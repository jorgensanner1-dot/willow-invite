"""Build the opaque base raster for the whole sheet (bleed included).

Layers, bottom to top:
  1. background beige
  2. floodplain tint from a relative elevation model (height above the river)
  3. land fills (refuge units, parks, etc.), painted so the relief shows through
  4. multi-directional hillshade, applied as a coloured multiply
"""
from __future__ import annotations

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from scipy import ndimage
from PIL import Image
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge

from terrain import relative_shade, apply_shade, blend_mask, hex_rgb

Image.MAX_IMAGE_PIXELS = None


def grid_for(frame, ppi):
    W = int(round(frame.page_w * ppi))
    H = int(round(frame.page_h * ppi))
    cell = frame.m_per_in / ppi
    return W, H, cell, from_origin(frame.x0, frame.y1, cell, cell)


def warp_dem(dem_path, W, H, transform, crs="EPSG:26915", resampling=Resampling.cubic_spline):
    dst = np.full((H, W), np.nan, np.float32)
    with rasterio.open(dem_path) as r:
        reproject(rasterio.band(r, 1), dst, src_transform=r.transform, src_crs=r.crs, src_nodata=r.nodata,
                  dst_transform=transform, dst_crs=crs, dst_nodata=np.nan, resampling=resampling,
                  num_threads=4)
    return dst


def _fill_nan(a):
    m = np.isnan(a)
    if not m.any():
        return a
    idx = ndimage.distance_transform_edt(m, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def river_profile(lines, dem_path, step=40.0, radius=45.0, upstream_first=True):
    """Sample water-surface elevation along river centerlines.

    Returns list of (x, y, z) points.  Elevation at each station is the minimum
    DEM value within `radius` (the water surface is the low point across the
    channel); the profile is then forced to be non-increasing downstream and
    lightly smoothed.
    """
    pts = []
    with rasterio.open(dem_path) as r:
        dem = r.read(1, masked=True).filled(np.nan)
        inv = ~r.transform
        res = r.res[0]
        k = int(np.ceil(radius / res))
        for line in lines:
            L = line.length
            n = max(2, int(L / step))
            xs, ys = [], []
            for i in range(n + 1):
                p = line.interpolate(i / n, normalized=True)
                xs.append(p.x)
                ys.append(p.y)
            zs = []
            for x, y in zip(xs, ys):
                c, rr = inv * (x, y)
                c, rr = int(c), int(rr)
                win = dem[max(0, rr - k):rr + k + 1, max(0, c - k):c + k + 1]
                zs.append(np.nanmin(win) if win.size and np.isfinite(win).any() else np.nan)
            z = np.array(zs, float)
            ok = np.isfinite(z)
            if ok.sum() < 2:
                continue
            z = np.interp(np.arange(len(z)), np.flatnonzero(ok), z[ok])
            # suppress bumps (bridges, embankments, DEM noise) without needing flow direction
            z = ndimage.minimum_filter1d(z, size=31, mode="nearest")
            z = ndimage.uniform_filter1d(z, size=31, mode="nearest")
            pts.extend(zip(xs, ys, z))
    return pts


def rem_grid(dem, transform, cell, profile_pts, coarse=4):
    """Height above nearest river station, computed on a coarser grid then upsampled."""
    H, W = dem.shape
    h, w = H // coarse, W // coarse
    small = dem[: h * coarse, : w * coarse].reshape(h, coarse, w, coarse).mean(axis=(1, 3))
    zr = np.full((h, w), np.nan, np.float32)
    inv = ~transform
    for x, y, z in profile_pts:
        c, r = inv * (x, y)
        c, r = int(c // coarse), int(r // coarse)
        if 0 <= r < h and 0 <= c < w:
            if np.isnan(zr[r, c]) or z < zr[r, c]:
                zr[r, c] = z
    mask = np.isnan(zr)
    idx = ndimage.distance_transform_edt(mask, return_distances=False, return_indices=True)
    near = zr[tuple(idx)]
    near = ndimage.gaussian_filter(near, 6)
    rem_small = small - near
    rem = np.kron(rem_small, np.ones((coarse, coarse), np.float32))
    out = np.full((H, W), np.nan, np.float32)
    out[: rem.shape[0], : rem.shape[1]] = rem
    return _fill_nan(out)


def build_base(frame, ppi, dem_path, out_jpg, *, river_lines=(), fills=(), bg="#F2EAD8",
               floodplain_color="#E2E5CC", floodplain_full=2.5, floodplain_zero=9.0, floodplain_opacity=1.0,
               zf=2.0, alt=42.0, k_shadow=0.9, k_high=0.6, shadow_tint="#6F6252", highlight="#FBF6EA",
               smooth_m=9.0, quality=92, rem_dem_path=None, strip=1024, pad=96):
    """Render the base raster in horizontal strips so memory stays modest at 200+ ppi."""
    from rasterio.transform import Affine
    W, H, cell, tr = grid_for(frame, ppi)
    print(f"base raster {W} x {H} px, cell {cell:.2f} m")
    out = np.empty((H, W, 3), np.uint8)

    # floodplain weight on a coarse (about 20 m) grid for the whole sheet
    wc = None
    if river_lines:
        cc = max(1, int(round(20.0 / cell)))
        Wc, Hc = int(np.ceil(W / cc)), int(np.ceil(H / cc))
        trc = from_origin(frame.x0, frame.y1, cell * cc, cell * cc)
        demc = _fill_nan(warp_dem(dem_path, Wc, Hc, trc, resampling=Resampling.average))
        demc = ndimage.gaussian_filter(demc, max(0.0, smooth_m / (cell * cc)))
        prof = river_profile(river_lines, rem_dem_path or dem_path)
        remc = rem_grid(demc, trc, cell * cc, prof, coarse=1)
        wc = np.clip((floodplain_zero - remc) / (floodplain_zero - floodplain_full), 0, 1)
        wc = ndimage.gaussian_filter(wc, 25.0 / (cell * cc)).astype(np.float32)

    fills = [([g for g in geoms if g is not None and not g.is_empty], color, op) for geoms, color, op in fills]
    bgc = hex_rgb(bg)
    sig = max(0.0, smooth_m / cell)
    for r0 in range(0, H, strip):
        r1 = min(H, r0 + strip)
        a0, a1 = max(0, r0 - pad), min(H, r1 + pad)
        hs = a1 - a0
        trs = tr * Affine.translation(0, a0)
        dem = _fill_nan(warp_dem(dem_path, W, hs, trs))
        z = ndimage.gaussian_filter(dem, sig) if sig > 0.3 else dem
        del dem
        rgb = np.empty((hs, W, 3), np.float32)
        rgb[:] = bgc
        if wc is not None:
            rows = (np.arange(a0, a1, dtype=np.float32) + 0.5) / cc - 0.5
            cols = (np.arange(W, dtype=np.float32) + 0.5) / cc - 0.5
            rr, cc_ = np.meshgrid(rows, cols, indexing="ij")
            wgt = ndimage.map_coordinates(wc, [rr, cc_], order=1, mode="nearest").astype(np.float32)
            del rr, cc_
            rgb = blend_mask(rgb, wgt, floodplain_color, floodplain_opacity)
            del wgt
        for geoms, color, opacity in fills:
            if not geoms:
                continue
            m = rasterize(((g, 1) for g in geoms), out_shape=(hs, W), transform=trs, fill=0, dtype="uint8")
            if m.any():
                rgb = blend_mask(rgb, m, color, opacity)
        sh = relative_shade(z, cell, zf=zf, alt_deg=alt)
        del z
        rgb = apply_shade(rgb, sh, shadow_tint=shadow_tint, k_shadow=k_shadow, highlight=highlight, k_high=k_high)
        out[r0:r1] = (rgb[r0 - a0: r0 - a0 + (r1 - r0)] * 255.0 + 0.5).astype(np.uint8)
        del rgb, sh
        print(f"  rows {r0}-{r1} done", flush=True)
    Image.fromarray(out, "RGB").save(out_jpg, quality=quality, subsampling=0, optimize=True, dpi=(ppi, ppi))
    return None


def oriented_river(lines_gdf, start_xy):
    """Merge river flowlines and orient the result to start nearest `start_xy` (upstream end)."""
    geoms = []
    for g in lines_gdf.geometry:
        if isinstance(g, MultiLineString):
            geoms.extend(g.geoms)
        elif isinstance(g, LineString):
            geoms.append(g)
    merged = linemerge(geoms)
    parts = list(merged.geoms) if isinstance(merged, MultiLineString) else [merged]
    out = []
    from shapely.geometry import Point
    sp = Point(start_xy)
    for p in parts:
        a, b = Point(p.coords[0]), Point(p.coords[-1])
        out.append(p if a.distance(sp) <= b.distance(sp) else LineString(list(p.coords)[::-1]))
    return out

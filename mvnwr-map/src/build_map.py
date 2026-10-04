"""Minnesota Valley National Wildlife Refuge wall map: build script.

usage:
  python build_map.py --ppi 200 --out ../output/MVNWR_wall_map_84x42in_with-bleed.pdf   (full print file)
  python build_map.py --ppi 40 --preview                                       (quick look)
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from shapely.geometry import box, Point, LineString
from shapely.ops import unary_union, linemerge

import style as S
from frame import Frame
from layers import load_all, DATA
from base import build_base
from cartolib import Fonts
import draw as D
import labels as LB
import panels as PN

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("MVNWR_FONTS", os.path.join(os.path.dirname(DATA), "fonts"))

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["pdf.compression"] = 9
plt.rcParams["path.simplify"] = True
plt.rcParams["path.simplify_threshold"] = 0.25
plt.rcParams["hatch.linewidth"] = 0.35


# ---------------------------------------------------------------------------
# feature selection
# ---------------------------------------------------------------------------
def refuge_parts(L):
    u = L["units"]
    fee = u[u["DIV"] == "Fee"].geometry
    other = u[u["DIV"] != "Fee"].geometry
    return fee, other


def open_regional_parks(L):
    r = L["regional_parks"]
    r = r[r["Category"].isin(["Regional Park", "Park Reserve", "Special Feature"]) & (r["OpenPublic"] == "Yes")]
    return r


def water_polys(L, prefix=""):
    import geopandas as gpd
    wb = L["inset_wb"] if prefix else L["nhd_wb"]
    dnr = L["inset_dnr"] if prefix else L["dnr_basins"]
    lakes = list(wb[wb["FTYPE"].isin([390, 436])].geometry)
    lakes += list(dnr[dnr["wb_class"].isin(["Lake or Pond", "Riverine polygon", "Innundation Area"])].geometry)
    marsh = list(wb[wb["FTYPE"] == 466].geometry) + list(dnr[dnr["wb_class"] == "Wetland"].geometry)
    if not prefix:
        from shapely.ops import unary_union
        keep_zone = unary_union(list(L["units"].geometry) + list(L["approved"].geometry)).buffer(200)
        lakes = [g for g in lakes if g.area >= 10000 or g.intersects(keep_zone)]
        marsh = [g for g in marsh if g.area >= 20000 or g.intersects(keep_zone)]
    rivers = []
    if not prefix:
        a = L["nhd_area"]
        tw = L["tiger_water"]
        rivers = list(a[a["FTYPE"] == 460].geometry) + list(tw[tw["MTFCC"] == "H3010"].geometry)
    crs = wb.crs
    return (gpd.GeoDataFrame(geometry=rivers, crs=crs), gpd.GeoDataFrame(geometry=lakes, crs=crs),
            gpd.GeoDataFrame(geometry=marsh, crs=crs))


def stream_sets(L):
    fl = L["flowlines"]
    st = fl[fl["ftype"].isin([460, 336, 334])]
    named = st[st["gnis_name"].notna() & ~st["gnis_name"].fillna("").str.contains("Ditch")]
    minor = st[~st.index.isin(named.index)]
    # keep minor streams that are not tiny fragments
    minor = minor[minor.length > 400]
    return named, minor


def river_centerlines(L, names=("Minnesota River", "Mississippi River")):
    fl = L["flowlines"]
    r = fl[fl["gnis_name"].isin(names)]
    out = []
    for g in r.geometry:
        out.extend(list(g.geoms) if g.geom_type == "MultiLineString" else [g])
    return out


# ---------------------------------------------------------------------------
# base raster
# ---------------------------------------------------------------------------
def make_base(F, L, ppi, out_jpg):
    rivers, lakes, marsh = water_polys(L)
    fee, other = refuge_parts(L)
    fills = []
    # lowest priority first
    ap = L["arealm"]
    airports = list(ap[ap["MTFCC"] == "K2451"].geometry) + list(L["airport_bdry"].geometry)
    fills.append((airports, S.AIRPORT_FILL, 1.0))
    fills.append((list(open_regional_parks(L).geometry), S.REGIONAL_FILL, 1.0))
    fills.append((list(L["wma"].geometry), S.WMA_FILL, 1.0))
    fills.append((list(L["state_park_lands"].geometry), S.STATE_FILL, 1.0))
    fills.append((list(L["sna"].geometry), S.SNA_FILL, 1.0))
    fills.append((list(other), S.REFUGE_EASE_FILL, 1.0))
    fills.append((list(fee), S.REFUGE_FILL, 1.0))
    t = time.time()
    build_base(F, ppi, os.path.join(DATA, "extra", "dem10_wide_utm15.tif"), out_jpg,
               river_lines=river_centerlines(L), fills=fills, bg=S.BG,
               floodplain_color=S.FLOODPLAIN_TINT, smooth_m=20.0, zf=1.55, k_shadow=0.72, k_high=0.46,
               shadow_tint=S.SHADOW_TINT, highlight=S.HIGHLIGHT)
    print(f"base raster done in {time.time() - t:.1f}s")


# ---------------------------------------------------------------------------
# vector map layers
# ---------------------------------------------------------------------------
def road_classes(L):
    e = L.get("road_edges")
    if e is None or e.empty:
        raise RuntimeError("road edges layer missing")
    e = e[e.geometry.notna()]
    # TIGER tagging fixes found in review: US 52 carriageways mis-coded as S1200 at the MN 55
    # interchange; dead-end stubs tagged MN 121 / MN 300 / MN 25 (S Meridian St, Belle Plaine);
    # untagged MN 41 (N Chestnut St, Chaska) and MN 284 (Benton St W, Cologne) edges.
    m = e["MTFCC"].mask(e["TLID"].isin([649690710, 37970791, 649615214, 649615215, 649690709, 37972004,
                                        37926454]), "S1100")
    rt = e["TOP_ROUTE_TYPE"].fillna("")
    rt = rt.mask(e["TLID"].isin([38142561, 38142558, 38142444, 38142445])
                 | e["TOP_ROUTE"].isin(["MN 121", "MN 300"]), "")
    rt = rt.mask(e["TLID"].isin([43507282, 43493742, 43493638, 43493636, 43493634, 43508324, 655160965,
                                 43509201, 43510542]), "MN")
    cls = {}
    cls["local"] = e[m.isin(["S1400", "S1740"]) & (rt == "")]
    cls["county"] = e[m.isin(["S1400", "S1200", "S1640"]) & (rt == "CO")]
    cls["other_sec"] = e[(m == "S1200") & (rt == "")]
    cls["ramp"] = e[m == "S1630"]
    cls["freeway_i"] = e[(m == "S1100") & (rt == "I")]
    cls["freeway_o"] = e[(m == "S1100") & (rt != "I")]
    cls["highway"] = e[m.isin(["S1200", "S1400"]) & rt.isin(["US", "MN"])]
    return cls


def draw_vectors(ax, F, L):
    z = 10
    # county lines under everything else
    cty = L["counties"]
    D.lines(ax, list(cty.boundary), color=S.COUNTY_LINE, lw=1.1, zorder=z, dashes=(6, 2.2, 1.2, 2.2),
            capstyle="butt")

    # roads, thin classes first
    rc = road_classes(L)
    D.lines(ax, rc["local"].geometry, color=S.ROAD_LOCAL, lw=0.4, zorder=z + 1)
    D.lines(ax, rc["other_sec"].geometry, color=S.ROAD_MINOR, lw=0.6, zorder=z + 2)
    D.lines(ax, rc["county"].geometry, color=S.ROAD_MINOR, lw=0.85, zorder=z + 2)

    # streams and water
    named, minor = stream_sets(L)
    D.lines(ax, minor.geometry, color=S.STREAM, lw=0.35, zorder=z + 3)
    D.lines(ax, named.geometry, color=S.STREAM, lw=0.8, zorder=z + 3)
    rivers, lakes, marsh = water_polys(L)
    D.polys(ax, marsh.geometry, fc=S.MARSH_FILL, ec="none", zorder=z + 4, hatch=None)
    D.lines(ax, river_centerlines(L), color=S.WATER, lw=2.4, zorder=z + 4.5)
    D.polys(ax, rivers.geometry, fc=S.WATER, ec="none", zorder=z + 5)
    D.polys(ax, lakes.geometry, fc=S.WATER, ec=S.WATER_LINE, lw=0.35, zorder=z + 5)
    D.polys(ax, rivers.geometry, fc="none", ec=S.WATER_LINE, lw=0.35, zorder=z + 5.1)

    # protected-area outlines
    D.polys(ax, open_regional_parks(L).geometry, fc="none", ec=S.REGIONAL_LINE, lw=0.5, zorder=z + 6)
    D.polys(ax, L["wma"].geometry, fc="none", ec=S.WMA_LINE, lw=0.45, zorder=z + 6)
    D.polys(ax, L["sna"].geometry, fc="none", ec=S.WMA_LINE, lw=0.45, zorder=z + 6)
    D.polys(ax, L["state_parks"].geometry, fc="none", ec=S.STATE_LINE, lw=0.9, zorder=z + 6,
            dashes=(5, 2))
    ai = L["aiannh"]
    D.polys(ax, ai.geometry, fc="none", ec=S.TRIBAL_LINE, lw=1.0, zorder=z + 6, dashes=(1.5, 2.5))
    D.lines(ax, list(L["approved"].boundary), color=S.APPROVED_LINE, lw=1.0, zorder=z + 7,
            dashes=(4, 2.5), capstyle="butt")
    u = L["units"]
    D.polys(ax, u.geometry, fc="none", ec=S.REFUGE_LINE, lw=1.5, zorder=z + 8)

    # airports: runways
    rw = L["runways"]
    rw = rw[rw["FAAIDENTIFIER"].isin(["MSP", "FCM", "SGS", "LVN"])]
    D.lines(ax, rw.geometry, color=S.AIRPORT_LINE, lw=3.2, zorder=z + 9, capstyle="butt")

    # rails: thin line + tick marks
    rails = L["rails"].geometry
    D.lines(ax, rails, color=S.RAIL, lw=0.55, zorder=z + 10)
    D.lines(ax, rails, color=S.RAIL, lw=2.6, zorder=z + 10, dashes=(0.35, 7.0), capstyle="butt")

    # major roads: casings then fills
    zc, zf = z + 12, z + 13
    D.lines(ax, rc["ramp"].geometry, color=S.ROAD_CASING, lw=1.3, zorder=zc)
    D.lines(ax, rc["highway"].geometry, color=S.STATE_CASE, lw=3.2, zorder=zc)
    D.lines(ax, rc["freeway_o"].geometry, color=S.US_CASE, lw=3.6, zorder=zc)
    D.lines(ax, rc["freeway_i"].geometry, color=S.INTERSTATE_CASE, lw=4.4, zorder=zc)
    D.lines(ax, rc["ramp"].geometry, color=S.STATE_HWY, lw=0.6, zorder=zf)
    D.lines(ax, rc["highway"].geometry, color=S.STATE_HWY, lw=2.1, zorder=zf)
    D.lines(ax, rc["freeway_o"].geometry, color=S.US_HWY, lw=2.5, zorder=zf)
    D.lines(ax, rc["freeway_i"].geometry, color=S.INTERSTATE, lw=3.2, zorder=zf)

    # trails
    rt = L["regional_trails"]
    rt = rt[rt["OpenPublic"] == "Yes"]
    D.lines(ax, rt.geometry, color=S.TRAIL_REGIONAL, lw=1.0, zorder=z + 15, dashes=(0.1, 2.4))
    stt = L["state_trails"]
    stt = stt[~stt["trail_name"].fillna("").str.startswith("Dakota Rail")]
    D.lines(ax, stt.geometry, color=S.TRAIL_STATE, lw=1.3, zorder=z + 16, dashes=(7.0, 2.5))
    ft = L["fws_trails"]
    D.lines(ax, ft.geometry, color=S.TRAIL_REFUGE, lw=1.3, zorder=z + 17, dashes=(2.4, 1.6))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ppi", type=float, default=200)
    ap.add_argument("--out", default=None)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--skip-base", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()

    F = Frame()
    fonts = Fonts(FONT_DIR)
    L = load_all(F, refresh=a.refresh)
    outdir = os.path.join(os.path.dirname(HERE), "output")
    os.makedirs(outdir, exist_ok=True)
    tag = f"p{int(a.ppi)}"
    out_pdf = a.out or os.path.join(DATA, "_work", f"MVNWR_map_{tag}_preview.pdf")
    work = os.path.join(DATA, "_work")
    os.makedirs(work, exist_ok=True)
    base_jpg = os.path.join(work, f"base_{tag}.jpg")
    if not (a.skip_base and os.path.exists(base_jpg)):
        make_base(F, L, a.ppi, base_jpg)

    t = time.time()
    fig = plt.figure(figsize=(F.page_w, F.page_h))
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(F.x0, F.x1)
    ax.set_ylim(F.y0, F.y1)
    ax.set_axis_off()
    ax.patch.set_alpha(0)
    pax = fig.add_axes([0, 0, 1, 1], zorder=5)
    pax.set_xlim(0, F.page_w)
    pax.set_ylim(0, F.page_h)
    pax.set_axis_off()
    pax.patch.set_alpha(0)

    draw_vectors(ax, F, L)
    LB.draw_labels(ax, F, L, fonts)
    PN.draw_panels(pax, F, L, fonts)

    over_pdf = os.path.join(work, f"overlay_{tag}.pdf")
    fig.savefig(over_pdf, transparent=True)
    plt.close(fig)
    print(f"overlay done in {time.time() - t:.1f}s")

    from pdfcompose import compose
    compose(base_jpg, over_pdf, out_pdf, F.page_w, F.page_h, F.bleed,
            title="Minnesota Valley National Wildlife Refuge — The Lower Minnesota River",
            subject="Wall map, 84 x 42 in trim, 1:42,000",
            keywords="Minnesota Valley National Wildlife Refuge, Minnesota River, map")
    print("wrote", out_pdf, f"{os.path.getsize(out_pdf) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()

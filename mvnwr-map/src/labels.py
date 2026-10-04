"""Point symbols and all map type.

Positions come from the data (place internal points, unit label points, lake
polygons, stream lines) and can be overridden in the tables below, which is
where hand placement happens.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Rectangle, Polygon as MplPolygon, FancyBboxPatch
from pyproj import Transformer
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import linemerge, unary_union

import style as S
import draw as D
from cartolib import spaced_text, text_on_path, draw_shield, text_width_pt, halo
from layers import P

_tr = Transformer.from_crs(4326, 26915, always_xy=True)


def ll(lon, lat):
    return _tr.transform(lon, lat)


HALO = S.BG


def where(F, spec, default=None):
    """spec dict may hold page=(x_in, y_in), lonlat=(lon, lat) or xy=(x, y) map metres"""
    if spec.get("page") is not None:
        return F.to_map(*spec["page"])
    if spec.get("lonlat") is not None:
        return ll(*spec["lonlat"])
    if spec.get("xy") is not None:
        return spec["xy"]
    return default

# -------------------------------------------------------------------------
# point symbols  (u = axis units per point)
# -------------------------------------------------------------------------
def sym_visitor(ax, x, y, u, z=60):
    r = 8.5 * u
    ax.add_patch(Circle((x, y), r * 1.18, fc=HALO, ec="none", zorder=z))
    ax.add_patch(Circle((x, y), r, fc=S.REFUGE_LINE, ec="#24331D", lw=0.6, zorder=z + 0.1))
    # stylised flying goose (refuge emblem motif): simple chevron
    ax.add_patch(MplPolygon([(x - 0.55 * r, y - 0.05 * r), (x, y + 0.42 * r), (x + 0.55 * r, y - 0.05 * r),
                             (x + 0.36 * r, y - 0.05 * r), (x, y + 0.18 * r), (x - 0.36 * r, y - 0.05 * r)],
                            closed=True, fc="white", ec="none", zorder=z + 0.2))
    ax.add_patch(Rectangle((x - 0.42 * r, y - 0.5 * r), 0.84 * r, 0.22 * r, fc="white", ec="none", zorder=z + 0.2))


def sym_trailhead(ax, x, y, u, z=60):
    s = 8.0 * u
    ax.add_patch(Rectangle((x - s / 2 - 1.2 * u, y - s / 2 - 1.2 * u), s + 2.4 * u, s + 2.4 * u, fc=HALO,
                           ec="none", zorder=z))
    ax.add_patch(Rectangle((x - s / 2, y - s / 2), s, s, fc=S.TRAIL_REFUGE, ec="none", zorder=z + 0.1))
    ax.text(x, y - 0.02 * s, "P", fontsize=6.5, color="white", ha="center", va="center", zorder=z + 0.2,
            fontweight="bold", family="DejaVu Sans")


def sym_boat(ax, x, y, u, z=60):
    r = 4.6 * u
    ax.add_patch(Circle((x, y), r + 1.2 * u, fc=HALO, ec="none", zorder=z))
    ax.add_patch(Circle((x, y), r, fc=S.WATER_LABEL, ec="none", zorder=z + 0.1))
    ax.add_patch(MplPolygon([(x - 0.15 * r, y + 0.62 * r), (x - 0.15 * r, y - 0.2 * r), (x + 0.5 * r, y - 0.2 * r)],
                            closed=True, fc="white", ec="none", zorder=z + 0.2))
    ax.add_patch(MplPolygon([(x - 0.62 * r, y - 0.32 * r), (x + 0.62 * r, y - 0.32 * r), (x + 0.4 * r, y - 0.58 * r),
                             (x - 0.4 * r, y - 0.58 * r)], closed=True, fc="white", ec="none", zorder=z + 0.2))


def sym_poi(ax, x, y, u, z=60):
    r = 3.6 * u
    ax.add_patch(Circle((x, y), r + 1.4 * u, fc=HALO, ec="none", zorder=z))
    ax.add_patch(Circle((x, y), r, fc=S.LANDMARK, ec="none", zorder=z + 0.1))


def sym_historic(ax, x, y, u, z=60):
    s = 7.0 * u
    pts = [(x, y + s * 0.62), (x + s * 0.55, y - s * 0.38), (x - s * 0.55, y - s * 0.38)]
    big = [(x, y + s * 0.92), (x + s * 0.85, y - s * 0.58), (x - s * 0.85, y - s * 0.58)]
    ax.add_patch(MplPolygon(big, closed=True, fc=HALO, ec="none", zorder=z))
    ax.add_patch(MplPolygon(pts, closed=True, fc="#7A3E2C", ec="none", zorder=z + 0.1))


def sym_airport(ax, x, y, u, z=60):
    s = 9.0 * u
    ax.add_patch(Circle((x, y), s * 0.72, fc=HALO, ec="none", zorder=z))
    ax.add_patch(Circle((x, y), s * 0.6, fc=S.INK_SOFT, ec="none", zorder=z + 0.1))
    # plane: fuselage + wings + tail
    ax.add_patch(Rectangle((x - 0.06 * s, y - 0.42 * s), 0.12 * s, 0.84 * s, fc="white", ec="none", zorder=z + 0.2))
    ax.add_patch(MplPolygon([(x - 0.42 * s, y - 0.02 * s), (x + 0.42 * s, y - 0.02 * s), (x + 0.06 * s, y + 0.16 * s),
                             (x - 0.06 * s, y + 0.16 * s)], closed=True, fc="white", ec="none", zorder=z + 0.2))
    ax.add_patch(MplPolygon([(x - 0.18 * s, y - 0.4 * s), (x + 0.18 * s, y - 0.4 * s), (x + 0.04 * s, y - 0.3 * s),
                             (x - 0.04 * s, y - 0.3 * s)], closed=True, fc="white", ec="none", zorder=z + 0.2))


def sym_town(ax, x, y, u, z=60, r=3.4):
    ax.add_patch(Circle((x, y), (r + 1.3) * u, fc=HALO, ec="none", zorder=z))
    ax.add_patch(Circle((x, y), r * u, fc="white", ec=S.INK, lw=1.0, zorder=z + 0.1))


# -------------------------------------------------------------------------
# generic text helpers
# -------------------------------------------------------------------------
def multiline(ax, x, y, text, fp, size, *, upp, tracking=0.0, color=S.INK, leading=1.15, halo_w=3.0,
              rotation=0.0, ha="center", zorder=55, caps=False):
    lines = text.split("\n")
    lh = size * leading * upp
    n = len(lines)
    ang = math.radians(rotation)
    for i, ln in enumerate(lines):
        off = ((n - 1) / 2 - i) * lh
        xx = x - math.sin(ang) * off
        yy = y + math.cos(ang) * off
        spaced_text(ax, xx, yy, ln.upper() if caps else ln, fp, size, tracking=tracking, color=color, ha=ha,
                    va="center", rotation=rotation, units_per_pt=upp, halo_w=halo_w, halo_color=HALO,
                    zorder=zorder)


# -------------------------------------------------------------------------
# cities and towns
# -------------------------------------------------------------------------
# name -> dict(dx, dy in points | lonlat, size, text, rot, hide)
CITY_OVR = {}
CITY_EXTRA = []   # (text, lon, lat, size, kind)


def _population():
    df = pd.read_csv(P("gnis", "raw", "sub-est2025_27.csv"), dtype=str, encoding="latin-1")
    df = df[df["SUMLEV"] == "162"]
    df["pop"] = df["POPESTIMATE2025"].astype(int)
    return dict(zip(df["PLACE"], df["pop"]))


def city_size(pop):
    if pop >= 80000:
        return 26, 0.26
    if pop >= 40000:
        return 22, 0.24
    if pop >= 15000:
        return 19.5, 0.22
    if pop >= 5000:
        return 17, 0.20
    if pop >= 1500:
        return 16, 0.18
    return 13, 0.15


def draw_cities(ax, F, L, fonts):
    pops = _population()
    pl = L["places"]
    pl = pl[pl["CLASSFP"].isin(["C1", "C5", "C7", "C8"])]   # incorporated places
    fp_big = fonts.sans(600)
    fp_small = fonts.sans(600)
    for _, r in pl.iterrows():
        name = r["NAME"]
        o = CITY_OVR.get(name, {})
        if o.get("hide"):
            continue
        pop = pops.get(r["PLACEFP"], 0)
        size, track = city_size(pop)
        size = o.get("size", size)
        ip = r.geometry.representative_point()
        x, y = ip.x, ip.y
        if pd.notna(r.get("INTPTLON", None)):
            x, y = ll(float(r["INTPTLON"]), float(r["INTPTLAT"]))
        x, y = where(F, o, (x, y))
        x += o.get("dx", 0) * F.upp
        y += o.get("dy", 0) * F.upp
        if not (F.x0 < x < F.x1 and F.y0 < y < F.y1):
            continue
        text = o.get("text", name.upper())
        small_town = pop < 5000
        if small_town and not o.get("nodot"):
            if o.get("dot") is not None:
                dxm, dym = F.to_map(*o["dot"])
            else:
                dxm = x + o.get("dotdx", 0) * F.upp
                dym = y + o.get("dotdy", 0) * F.upp
            sym_town(ax, dxm, dym, F.upp)
        multiline(ax, x, y, text, fp_big if size >= 19 else fp_small, size, upp=F.upp, tracking=track,
                  color=S.CITY_LABEL, halo_w=max(2.5, size * 0.16), rotation=o.get("rot", 0.0), zorder=58)


# -------------------------------------------------------------------------
# refuge units
# -------------------------------------------------------------------------
UNIT_OVR = {}


def draw_units(ax, F, L, fonts):
    pts = L["unit_pts"]
    fp = fonts.serif(700)
    for _, r in pts.iterrows():
        name = r["unit_name"]
        o = UNIT_OVR.get(name, {})
        if o.get("hide"):
            continue
        x, y = where(F, o, (r.geometry.x, r.geometry.y))
        if not (F.x0 < x < F.x1 and F.y0 < y < F.y1):
            continue
        text = o.get("text", name.upper().replace(" UNIT", "\nUNIT"))
        multiline(ax, x, y, text, fp, o.get("size", 25.5), upp=F.upp, tracking=0.16, color=S.REFUGE_LABEL,
                  halo_w=4.5, rotation=o.get("rot", 0.0), zorder=62, leading=1.08)
        for ex in o.get("extra", []):
            ex_x, ex_y = F.to_map(*ex[:2])
            multiline(ax, ex_x, ex_y, ex[2], fp, ex[3], upp=F.upp, tracking=0.16, color=S.REFUGE_LABEL,
                      halo_w=4.0, rotation=ex[4] if len(ex) > 4 else 0.0, zorder=62, leading=1.08)


# -------------------------------------------------------------------------
# water
# -------------------------------------------------------------------------
RIVER_LABELS = []      # (name, at fraction, size, offset_pt) along the Minnesota River centerline
LAKE_OVR = {}
LAKE_EXTRA = []        # (text, (page x, page y), size, rotation)
LAKE_MIN_HA = 45.0
STREAM_LABELS = []     # (gnis_name, near lon, near lat, size, text)


def river_line(L, name):
    fl = L["flowlines"]
    r = fl[(fl["gnis_name"] == name) & (fl["ftype"] == 558)]
    if r.empty:
        r = fl[fl["gnis_name"] == name]
    geoms = []
    for g in r.geometry:
        geoms.extend(list(g.geoms) if g.geom_type == "MultiLineString" else [g])
    m = linemerge(geoms)
    if m.geom_type == "MultiLineString":
        m = max(m.geoms, key=lambda g: g.length)
    return m


def draw_water_labels(ax, F, L, fonts):
    fpi = fonts.serif(500, True)
    # rivers: (gnis name, text, page x, page y, size, offset_pt, tracking, span_in, italic weight)
    cache = {}
    for item in RIVER_LABELS:
        name, text, px, py, size, off, track, span = item[:8]
        color = item[8] if len(item) > 8 else S.WATER_LABEL
        if name not in cache:
            cache[name] = river_line(L, name)
        line = cache[name]
        if line is None:
            continue
        cx, cy = F.to_map(px, py)
        d = line.project(Point(cx, cy))
        half = span * F.m_per_in / 2
        a, b = max(0, d - half), min(line.length, d + half)
        seg = np.array([line.interpolate(t).coords[0] for t in np.linspace(a, b, 200)])
        text_on_path(ax, seg, text, fpi, size, units_per_pt=F.upp, tracking=track, color=color, at=0.5,
                     offset_pt=off, halo_w=0, zorder=57, smooth_pt=span * 72 * 0.35)
    # lakes
    wb = L["nhd_wb"]
    lakes = wb[wb["FTYPE"].isin([390, 436]) & wb["GNIS_NAME"].notna()].copy()
    lakes["ha"] = lakes.area / 1e4
    fpl = fonts.serif(500, True)
    done = set()
    placed_lakes = []
    for _, r in lakes.sort_values("ha", ascending=False).iterrows():
        nm = r["GNIS_NAME"]
        o = LAKE_OVR.get(nm, {})
        key = (nm, round(r.geometry.centroid.x, -3), round(r.geometry.centroid.y, -3))
        if o.get("hide") or key in done:
            continue
        if r["ha"] < o.get("min_ha", LAKE_MIN_HA):
            continue
        done.add(key)
        p = r.geometry.representative_point()
        if any(nm == n2 and p.distance(q) < 4000 for n2, q in placed_lakes):
            continue
        placed_lakes.append((nm, p))
        x, y = where(F, o, (p.x, p.y))
        if not (F.x0 < x < F.x1 and F.y0 < y < F.y1):
            continue
        px_, py_ = F.to_page(x, y)
        sx0, sy0, sx1, sy1 = F.safe_box()
        if o.get("page") is None and not (sx0 + 0.6 < px_ < sx1 - 0.6 and sy0 + 0.3 < py_ < sy1 - 0.3):
            continue
        size = o.get("size", float(np.clip(9.5 + 2.2 * math.log10(max(r["ha"], 1)), 11, 22)))
        multiline(ax, x, y, o.get("text", nm.replace(" Lake", "\nLake") if r["ha"] < 150 else nm), fpl, size,
                  upp=F.upp, tracking=0.06, color=S.WATER_LABEL, halo_w=0, rotation=o.get("rot", 0.0),
                  zorder=56)
    for text, (px, py), size, rot in LAKE_EXTRA:
        x, y = F.to_map(px, py)
        multiline(ax, x, y, text, fpl, size, upp=F.upp, tracking=0.06, color=S.WATER_LABEL, halo_w=0,
                  rotation=rot, zorder=56)
    # streams
    fl = L["flowlines"]
    fps = fonts.serif(500, True)
    for gname, lon, lat, size, text, span in STREAM_LABELS:
        s = fl[fl["gnis_name"] == gname]
        if s.empty:
            continue
        geoms = []
        for g in s.geometry:
            geoms.extend(list(g.geoms) if g.geom_type == "MultiLineString" else [g])
        m = linemerge(geoms)
        parts = list(m.geoms) if m.geom_type == "MultiLineString" else [m]
        px, py = F.to_map(lon, lat) if lon > 0 else ll(lon, lat)
        pt = Point(px, py)
        part = min(parts, key=lambda g: g.distance(pt))
        d = part.project(pt)
        half = span / 2
        a, b = max(0, d - half), min(part.length, d + half)
        seg = LineString([part.interpolate(t) for t in np.linspace(a, b, 60)])
        text_on_path(ax, np.asarray(seg.coords), text, fps, size, units_per_pt=F.upp, tracking=0.08,
                     color=S.WATER_LABEL, at=0.5, offset_pt=size * 0.55, halo_w=2.2, zorder=56,
                     smooth_pt=min(100.0, 0.4 * span / F.upp))


# -------------------------------------------------------------------------
# trails
# -------------------------------------------------------------------------
TRAIL_LABELS = []   # (layer key, name field, name, page x, page y, size, text, span_in, color)


def draw_trail_labels(ax, F, L, fonts):
    fp = fonts.sans(600, True)
    for key, field, name, px, py, size, text, span, color in TRAIL_LABELS:
        lay = L[key]
        sel = lay[lay[field].fillna("").str.startswith(name)]
        if sel.empty:
            continue
        geoms = []
        for g in sel.geometry:
            geoms.extend(list(g.geoms) if g.geom_type == "MultiLineString" else [g])
        m = linemerge(geoms)
        parts = list(m.geoms) if m.geom_type == "MultiLineString" else [m]
        cx, cy = F.to_map(px, py)
        pt = Point(cx, cy)
        part = min(parts, key=lambda g: g.distance(pt))
        d = part.project(pt)
        half = span * F.m_per_in / 2
        a, b = max(0, d - half), min(part.length, d + half)
        seg = np.array([part.interpolate(t).coords[0] for t in np.linspace(a, b, 120)])
        text_on_path(ax, seg, text, fp, size, units_per_pt=F.upp, tracking=0.06, color=color, at=0.5,
                     offset_pt=size * 0.75, halo_w=2.4, zorder=55, smooth_pt=span * 72 * 0.3)


# -------------------------------------------------------------------------
# parks and natural areas
# -------------------------------------------------------------------------
PARK_LABELS = []   # dict(text, page|lonlat, size, rot, color)


def draw_park_labels(ax, F, L, fonts):
    fp = fonts.sans(600, True)
    for d in PARK_LABELS:
        x, y = where(F, d)
        multiline(ax, x, y, d["text"], fp, d.get("size", 15), upp=F.upp, tracking=d.get("track", 0.04),
                  color=d.get("color", S.PARK_LABEL), halo_w=2.8, rotation=d.get("rot", 0.0), zorder=54,
                  leading=1.12)


# -------------------------------------------------------------------------
# points of interest
# -------------------------------------------------------------------------
POI_LABELS = []   # dict(text, lonlat|page, sym, dx, dy (points), ha, size, bold, color)


def draw_pois(ax, F, L, fonts):
    syms = dict(visitor=sym_visitor, trailhead=sym_trailhead, boat=sym_boat, poi=sym_poi, historic=sym_historic,
                airport=sym_airport, none=None)
    for d in POI_LABELS:
        x, y = where(F, d)
        sym = d.get("sym", "poi")
        if syms.get(sym):
            syms[sym](ax, x, y, F.upp)
        text = d.get("text")
        if not text:
            continue
        size = d.get("size", 12)
        if sym == "visitor":
            f, col = fonts.sans(700), S.REFUGE_LABEL
        elif d.get("bold"):
            f, col = fonts.sans(600), S.INK
        elif d.get("italic"):
            f, col = fonts.serif(500, True), S.INK
        else:
            f, col = fonts.sans(400), S.INK
        col = d.get("color", col)
        ha = d.get("ha", "left")
        dx, dy = d.get("dx", 9 if ha == "left" else (-9 if ha == "right" else 0)), d.get("dy", 0)
        lines = text.split("\n")
        n = len(lines)
        for i, ln in enumerate(lines):
            yy = y + (dy + ((n - 1) / 2 - i) * size * 1.12) * F.upp
            ax.text(x + dx * F.upp, yy, ln, fontproperties=f, fontsize=size, color=col, ha=ha, va="center_baseline",
                    zorder=59, path_effects=halo(2.8, HALO))


# -------------------------------------------------------------------------
# highway shields
# -------------------------------------------------------------------------
SHIELDS = []   # (kind, number, lon, lat)


def draw_shields(ax, F, L, fonts):
    for kind, num, lon, lat in SHIELDS:
        x, y = ll(lon, lat)
        draw_shield(ax, x, y, kind, num, fonts, units_per_pt=F.upp, size_pt=19)


# -------------------------------------------------------------------------
# counties
# -------------------------------------------------------------------------
COUNTY_LABELS = []  # (text, lon, lat, rot)


def draw_county_labels(ax, F, L, fonts):
    fp = fonts.sans(600)
    for text, px, py, rot in COUNTY_LABELS:
        x, y = F.to_map(px, py)
        spaced_text(ax, x, y, text, fp, 17, tracking=0.5, units_per_pt=F.upp, color=S.TOWNSHIP_LABEL,
                    rotation=rot, halo_w=2.5, halo_color=HALO, zorder=52, va="center")


EDGE_LABELS = []


def draw_edge_labels(ax, F, L, fonts):
    fp = fonts.sans(600)
    for text, (px, py) in EDGE_LABELS:
        x, y = F.to_map(px, py)
        w = spaced_text(ax, x, y, text, fp, 22, tracking=0.3, units_per_pt=F.upp, color=S.CITY_LABEL,
                        va="center", halo_w=3.5, halo_color=HALO, zorder=58)
        # small upward chevron after the name
        cx = x + w / 2 + 14 * F.upp
        u = F.upp
        ax.add_patch(MplPolygon([(cx - 5 * u, y - 3 * u), (cx, y + 5 * u), (cx + 5 * u, y - 3 * u),
                                 (cx + 3 * u, y - 3 * u), (cx, y + 1.5 * u), (cx - 3 * u, y - 3 * u)],
                                closed=True, fc=S.CITY_LABEL, ec=HALO, lw=0.8, zorder=58))


def draw_labels(ax, F, L, fonts):
    from label_table import apply
    apply(globals(), F, L)
    draw_county_labels(ax, F, L, fonts)
    draw_park_labels(ax, F, L, fonts)
    draw_trail_labels(ax, F, L, fonts)
    draw_water_labels(ax, F, L, fonts)
    draw_units(ax, F, L, fonts)
    draw_cities(ax, F, L, fonts)
    draw_edge_labels(ax, F, L, fonts)
    draw_pois(ax, F, L, fonts)
    draw_shields(ax, F, L, fonts)

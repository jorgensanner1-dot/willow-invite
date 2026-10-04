"""Page furniture: title block, legend, scale bar, north arrow, insets and credits.

All coordinates here are sheet inches (origin at the lower-left corner of the
sheet, bleed included).  Type sizes are in points.
"""
from __future__ import annotations

import math

import numpy as np
import geopandas as gpd
from matplotlib.patches import Rectangle, Polygon as MplPolygon, Circle
from matplotlib.lines import Line2D
from shapely.geometry import box

import style as S
import draw as D
from cartolib import spaced_text, draw_shield, text_width_pt, halo

PANEL_FILL = "#F6F0E2"
PANEL_EDGE = "#8F8370"
RULE = "#A89B85"
HEAD = "#2B3A26"

# -------------------------------------------------------------------------
# layout (sheet inches).  Safe area is 1.125 .. page-1.125 on every side.
# -------------------------------------------------------------------------
TITLE = dict(x=1.6, y=31.5, w=20.7, h=9.1)
INFO = dict(x=1.6, y=1.6, w=10.9, h=8.5)
LEGEND = dict(x=44.0, y=1.6, w=38.6, h=13.2)

U = 1 / 72.0   # inches per point


def panel(pax, x, y, w, h, z=100, fill=PANEL_FILL, edge=PANEL_EDGE, double=True):
    pax.add_patch(Rectangle((x, y), w, h, fc=fill, ec="none", zorder=z))
    pax.add_patch(Rectangle((x, y), w, h, fc="none", ec=edge, lw=1.1, zorder=z + 0.5))
    if double:
        o = 0.09
        pax.add_patch(Rectangle((x + o, y + o), w - 2 * o, h - 2 * o, fc="none", ec=edge, lw=0.4,
                                zorder=z + 0.5))


def T(pax, x, y, s, fp, size, color=S.INK, ha="left", va="baseline", z=110, **kw):
    return pax.text(x, y, s, fontproperties=fp, fontsize=size, color=color, ha=ha, va=va, zorder=z, **kw)


def header(pax, x, y, s, fonts, size=17, color=HEAD, ha="left", tracking=0.3):
    spaced_text(pax, x, y, s, fonts.sans(700), size, tracking=tracking, units_per_pt=U, ha=ha, color=color,
                zorder=112)


def hrule(pax, x0, x1, y, lw=0.6, color=RULE):
    pax.add_line(Line2D([x0, x1], [y, y], color=color, lw=lw, zorder=111))


def vrule(pax, x, y0, y1, lw=0.6, color=RULE):
    pax.add_line(Line2D([x, x], [y0, y1], color=color, lw=lw, zorder=111))


def wrap(text, fp, size, width_in):
    words, lines, cur = [w for w in text.split(" ") if w], [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width_pt(trial, fp, size) / 72.0 <= width_in or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def paragraph(pax, x, y, text, fp, size, width_in, leading=1.32, color=S.INK, z=110, justify=False):
    lh = size * leading / 72.0
    yy = y
    for para in text.split("\n"):
        lines = wrap(para, fp, size, width_in)
        for i, ln in enumerate(lines):
            last = i == len(lines) - 1
            if justify and not last and " " in ln:
                words = ln.split(" ")
                wsum = sum(text_width_pt(w, fp, size) for w in words) / 72.0
                gap = (width_in - wsum) / (len(words) - 1)
                xx = x
                for w in words:
                    T(pax, xx, yy, w, fp, size, color=color, z=z)
                    xx += text_width_pt(w, fp, size) / 72.0 + gap
            else:
                T(pax, x, yy, ln, fp, size, color=color, z=z)
            yy -= lh
    return yy


# -------------------------------------------------------------------------
# title block
# -------------------------------------------------------------------------
INTRO = ("Established by Congress on October 8, 1976, Minnesota Valley National Wildlife Refuge is part of a "
         "corridor of land and water stretching nearly 70 miles along the Minnesota River (Mni Sota Wakpa), from "
         "Bloomington to Henderson. Its more than 15,000 acres of marsh, floodplain lake, bottomland forest, oak savanna and "
         "prairie give migrating waterfowl, bald eagles and songbirds a haven at the edge of the Twin Cities. "
         "The valley is Dakota homeland; Bdote, where the Minnesota and Mississippi rivers meet, is a place of "
         "deep significance to the Dakota Oyate.")


def title_block(pax, F, fonts):
    x, y, w, h = TITLE["x"], TITLE["y"], TITLE["w"], TITLE["h"]
    panel(pax, x, y, w, h)
    cx = x + w / 2
    top = y + h
    spaced_text(pax, cx, top - 1.0, "THE LOWER MINNESOTA RIVER VALLEY  ·  FIFTY YEARS, 1976–2026", fonts.sans(600), 21,
                tracking=0.32, units_per_pt=U, color=S.INK_SOFT, zorder=110)
    T(pax, cx, top - 3.15, "Minnesota Valley", fonts.serif(500), 148, ha="center", color=HEAD)
    T(pax, cx, top - 4.55, "National Wildlife Refuge", fonts.serif(400, True), 82, ha="center", color=HEAD)
    ry = top - 5.25
    hrule(pax, x + 1.6, cx - 0.55, ry, lw=1.0)
    hrule(pax, cx + 0.55, x + w - 1.6, ry, lw=1.0)
    pax.add_patch(MplPolygon([(cx - 0.32, ry), (cx, ry + 0.13), (cx + 0.32, ry), (cx, ry - 0.13)],
                             closed=True, fc=S.REFUGE_LINE, ec="none", zorder=110))
    spaced_text(pax, cx, top - 5.95, "FORT SNELLING TO HENDERSON  ·  MNI SOTA WAKPA", fonts.sans(600), 19,
                tracking=0.25, units_per_pt=U, color=S.WATER_LABEL, zorder=110)
    paragraph(pax, cx - 7.2, top - 6.85, INTRO, fonts.serif(400), 21.5, 14.4, leading=1.36, color=S.INK,
              justify=False)


# -------------------------------------------------------------------------
# lower-left: refuge units and visitor information
# -------------------------------------------------------------------------
UNIT_ROWS = [  # downstream (Fort Snelling) to upstream (Henderson); acres from USFWS unit data
    ("Long Meadow Lake", "Bloomington"),
    ("Black Dog Lake", "Burnsville"),
    ("Bloomington Ferry", "Bloomington"),
    ("Wilkie", "Shakopee, Savage"),
    ("Upgrala", "Eden Prairie, Chanhassen"),
    ("Chaska", "Carver, Chaska"),
    ("Rapids Lake", "Carver"),
    ("Louisville Swamp", "Jordan, Shakopee"),
    ("San Francisco", "Jordan, Carver"),
    ("St. Lawrence", "Jordan, Belle Plaine"),
    ("Jessenland", "Belle Plaine, Henderson"),
    ("Blakeley", "Henderson"),
    ("Round Lake", "Arden Hills (inset)"),
]


def info_block(pax, F, L, fonts):
    x, y, w, h = INFO["x"], INFO["y"], INFO["w"], INFO["h"]
    panel(pax, x, y, w, h)
    top = y + h
    header(pax, x + 0.55, top - 0.75, "REFUGE UNITS", fonts, size=16)
    T(pax, x + w - 0.55, top - 0.75, "acres", fonts.sans(400, True), 13, ha="right", color=S.INK_SOFT)
    d = L["units_dissolved"].set_index("unit")
    fp = fonts.serif(500)
    fps = fonts.sans(400, True)
    fpn = fonts.sans(400)
    yy = top - 1.2
    rh = 0.32
    total = 0.0
    for i, (u, where) in enumerate(UNIT_ROWS):
        ac = round(float(d.loc[u, "fee_acres"] + d.loc[u, "mou_acres"] + d.loc[u, "easement_acres"]))
        total += ac
        if i % 2 == 0:
            pax.add_patch(Rectangle((x + 0.4, yy - 0.105), w - 0.8, rh, fc="#ECE4D0", ec="none", zorder=105))
        T(pax, x + 0.55, yy, u, fp, 15, z=110)
        T(pax, x + 0.55 + text_width_pt(u, fp, 15) / 72 + 0.12, yy, where, fps, 11.5, color=S.INK_SOFT, z=110)
        T(pax, x + w - 0.55, yy, f"{ac:,.0f}", fpn, 14, ha="right", z=110)
        yy -= rh
    hrule(pax, x + 0.5, x + w - 0.5, yy + 0.18, lw=0.6)
    T(pax, x + 0.55, yy - 0.1, "Total", fonts.serif(600), 15, z=110)
    T(pax, x + w - 0.55, yy - 0.1, f"{total:,.0f}", fonts.sans(600), 14, ha="right", z=110)
    yy -= 0.42
    T(pax, x + 0.55, yy, "Includes fee-title, easement and cooperatively managed lands; acreages computed from "
      "USFWS unit data.", fps, 10.5, color=S.INK_SOFT)
    yy -= 0.5
    header(pax, x + 0.55, yy, "VISITOR CENTERS", fonts, size=16)
    yy -= 0.4
    lines = [
        ("Bloomington Education and Visitor Center", fonts.serif(600), 14.5),
        ("3815 American Blvd. East, Bloomington  ·  952-854-5900", fpn, 12.5),
        ("Rapids Lake Education and Visitor Center", fonts.serif(600), 14.5),
        ("15865 Rapids Lake Road, Carver  ·  952-361-4500", fpn, 12.5),
        ("www.fws.gov/refuge/minnesota-valley", fonts.sans(600), 12.5),
    ]
    gaps = [0.25, 0.40, 0.25, 0.36, 0.0]
    for (s_, f, sz), g in zip(lines, gaps):
        T(pax, x + 0.55, yy, s_, f, sz)
        yy -= g


# -------------------------------------------------------------------------
# legend
# -------------------------------------------------------------------------
def _swatch(pax, x, y, fc, ec="none", lw=0.0, w=0.66, h=0.36, z=112, dashes=None):
    r = Rectangle((x, y - h / 2), w, h, fc=fc, ec=ec, lw=lw, zorder=z)
    if dashes is not None:
        r.set_linestyle((0, dashes))
    pax.add_patch(r)


def _line(pax, x, y, color, lw, w=0.66, dashes=None, z=112, cap="butt"):
    ln = Line2D([x, x + w], [y, y], color=color, lw=lw, zorder=z, solid_capstyle=cap, dash_capstyle=cap)
    if dashes is not None:
        ln.set_linestyle((0, dashes))
    pax.add_line(ln)


def legend_block(pax, F, L, fonts):
    x, y, w, h = LEGEND["x"], LEGEND["y"], LEGEND["w"], LEGEND["h"]
    panel(pax, x, y, w, h)
    top = y + h
    lab = fonts.sans(400)
    sz = 16.0
    import labels as LB

    # ---- left column: locator + Round Lake inset ----
    lx0, lx1 = x + 0.55, x + 8.75
    locator(pax, F, L, fonts, lx0, top - 5.95, lx1 - lx0, 4.95)
    round_lake_inset(pax, F, L, fonts, lx0, y + 0.55, lx1 - lx0, 6.15)
    vrule(pax, lx1 + 0.4, y + 0.5, top - 0.5)

    # ---- legend columns ----
    gx = lx1 + 0.95
    header(pax, gx, top - 0.83, "LEGEND", fonts, size=16, tracking=0.28)
    colw = [8.35, 7.25, 6.55, 6.4]
    cols_x = [gx]
    for cw in colw[:-1]:
        cols_x.append(cols_x[-1] + cw)
    r0 = top - 1.6
    rows = 0.56

    def item(cx, cy, kind, text):
        sx, tx = cx, cx + 0.82
        k = kind[0]
        if k == "fill":
            _swatch(pax, sx, cy + 0.06, kind[1], kind[2], kind[3])
        elif k == "fill_dash":
            _swatch(pax, sx, cy + 0.06, kind[1], kind[2], kind[3], dashes=kind[4])
        elif k == "line":
            _line(pax, sx, cy + 0.06, kind[1], kind[2], dashes=kind[3])
        elif k == "line_bg":
            _swatch(pax, sx, cy + 0.06, S.BG)
            _line(pax, sx, cy + 0.06, kind[1], kind[2], dashes=kind[3], z=112.2)
        elif k == "road":
            _swatch(pax, sx, cy + 0.06, S.BG)
            _line(pax, sx, cy + 0.06, kind[1], kind[3], z=112.1)
            _line(pax, sx, cy + 0.06, kind[2], kind[4], z=112.2)
        elif k == "rail":
            _swatch(pax, sx, cy + 0.06, S.BG)
            _line(pax, sx, cy + 0.06, S.RAIL, 0.55, z=112.1)
            _line(pax, sx, cy + 0.06, S.RAIL, 2.6, dashes=(0.35, 7.0), z=112.1)
        elif k == "marker":
            kind[1](pax, sx + 0.31, cy + 0.06, U, z=114)
        if text:
            T(pax, tx, cy, text, lab, sz, color=S.INK, z=113)

    cols = [
        [
            (("fill", S.REFUGE_FILL, S.REFUGE_LINE, 1.3), "Refuge land owned by USFWS (fee title)"),
            (("fill", S.REFUGE_EASE_FILL, S.REFUGE_LINE, 1.3), "Refuge easement or cooperative agreement"),
            (("line", S.APPROVED_LINE, 1.0, (4, 2.5)), "Approved refuge acquisition boundary"),
            (("fill", S.FLOODPLAIN_TINT, "none", 0), "Valley floor, up to about 30 ft above the river"),
            (("fill", S.WATER, S.WATER_LINE, 0.35), "River or lake"),
            (("fill", S.MARSH_FILL, "none", 0), "Marsh or swamp"),
            (("line_bg", S.STREAM, 0.8, None), "Stream"),
        ],
        [
            (("fill_dash", S.STATE_FILL, S.STATE_LINE, 0.9, (5, 2)), "State park or recreation area"),
            (("fill", S.WMA_FILL, S.WMA_LINE, 0.45), "Scientific and Natural Area or Wildlife Mgmt. Area"),
            (("fill", S.REGIONAL_FILL, S.REGIONAL_LINE, 0.5), "Regional or county park"),
            (("fill_dash", "none", S.TRIBAL_LINE, 1.0, (1.5, 2.5)), "Tribal land"),
            (("fill", S.AIRPORT_FILL, "none", 0), "Airport grounds"),
            (("line_bg", S.COUNTY_LINE, 1.1, (6, 2.2, 1.2, 2.2)), "County boundary"),
        ],
        [
            (("line_bg", S.TRAIL_REFUGE, 1.3, (2.4, 1.6)), "Refuge trail"),
            (("line_bg", S.TRAIL_STATE, 1.3, (7.0, 2.5)), "State trail"),
            (("line_bg", S.TRAIL_REGIONAL, 1.0, (0.1, 2.4)), "Regional trail"),
            (("road", S.INTERSTATE_CASE, S.INTERSTATE, 4.4, 3.2), "Interstate"),
            (("road", S.US_CASE, S.US_HWY, 3.6, 2.5), "U.S. or state freeway"),
            (("road", S.STATE_CASE, S.STATE_HWY, 3.2, 2.1), "U.S. or state highway"),
            (("line_bg", S.ROAD_MINOR, 0.85, None), "County road"),
            (("line_bg", S.ROAD_LOCAL, 0.45, None), "Local road"),
            (("rail",), "Railroad"),
        ],
        [
            (("marker", LB.sym_visitor), "Visitor center"),
            (("marker", LB.sym_trailhead), "Trailhead or parking"),
            (("marker", LB.sym_boat), "Boat launch"),
            (("marker", LB.sym_historic), "Historic site"),
            (("marker", LB.sym_poi), "Point of interest"),
            (("marker", LB.sym_airport), "Airport"),
            (("marker", LB.sym_town), "City or town under 5,000 people"),
        ],
    ]
    for cx, col in zip(cols_x, cols):
        for i, (k, t) in enumerate(col):
            item(cx, r0 - i * rows, k, t)
    sx = cols_x[3]
    sy = r0 - 7.45 * rows
    draw_shield(pax, sx + 0.3, sy + 0.06, "I", "35W", fonts, units_per_pt=U, size_pt=18, zorder=114)
    draw_shield(pax, sx + 0.95, sy + 0.06, "US", "169", fonts, units_per_pt=U, size_pt=18, zorder=114)
    draw_shield(pax, sx + 1.62, sy + 0.06, "MN", "13", fonts, units_per_pt=U, size_pt=18, zorder=114)
    T(pax, sx + 2.05, sy + 0.1, "Interstate, U.S. and", lab, sz, z=113)
    T(pax, sx + 2.05, sy + 0.1 - 0.28, "state routes", lab, sz, z=113)

    # ---- middle band: scale, north arrow, projection, credits ----
    by = r0 - 9 * rows + 0.1
    hrule(pax, gx, x + w - 0.55, by)
    scale_bar(pax, F, fonts, gx + 0.1, by - 1.45)
    north_arrow(pax, fonts, gx + 10.05, by - 2.15, size=0.95)
    for i, ln in enumerate(["Shaded relief from USGS 3DEP 10-meter",
                            "elevation. The north arrow points to grid",
                            "north, within 1 degree of true north on",
                            "this map. UTM projection, zone 15 north,",
                            "North American Datum of 1983."]):
        T(pax, gx + 10.75, by - 0.62 - i * 0.235, ln, fonts.sans(400), 12, color=S.INK_SOFT)
    cxp = gx + 15.55
    credits(pax, fonts, cxp, by - 0.45, x + w - 0.6 - cxp)

    # ---- timeline band ----
    ty = y + 3.0
    hrule(pax, gx, x + w - 0.55, ty)
    header(pax, gx, ty - 0.5, "FIFTY YEARS ON THE RIVER  ·  1976–2026", fonts, size=16, tracking=0.28)
    span = (x + w - 0.55) - gx
    cw = span / len(TIMELINE)
    for i, (yr, txt) in enumerate(TIMELINE):
        ex = gx + i * cw
        T(pax, ex, ty - 1.15, yr, fonts.serif(600), 34, color=HEAD)
        paragraph(pax, ex, ty - 1.55, txt, fonts.sans(400), 14.5, cw - 0.45, leading=1.3, color=S.INK)


TIMELINE = [  # from the USFWS refuge "About Us" and home pages (fws.gov/refuge/minnesota-valley)
    ("1976", "Congress establishes the refuge on October 8 (Public Law 94-466), authorizing an initial "
             "purchase of 9,500 acres."),
    ("1984", "A conservation plan is completed with the State of Minnesota and local partners; the Act is "
             "amended to allow 2,000 more acres."),
    ("1995", "The Mittelstad tract, today's Rapids Lake Unit, is added, bringing the refuge to nearly "
             "14,000 acres."),
    ("2020", "The refuge is designated an urban wildlife refuge and awarded $1 million to strengthen urban "
             "programs."),
    ("2026", "The refuge marks 50 years with anniversary events. More than 45 miles of trails are open "
             "daily, 5\u00a0a.m. to 10\u00a0p.m., free of charge."),
]


# -------------------------------------------------------------------------
def scale_bar(pax, F, fonts, x, y, miles=5, km=8):
    lab = fonts.sans(400)
    in_per_mi = 1609.344 / F.m_per_in
    in_per_km = 1000.0 / F.m_per_in
    h = 0.1
    for i in range(miles):
        fc = S.INK if i % 2 == 0 else PANEL_FILL
        pax.add_patch(Rectangle((x + i * in_per_mi, y), in_per_mi, h, fc=fc, ec=S.INK, lw=0.6, zorder=112))
    for i in range(miles + 1):
        T(pax, x + i * in_per_mi, y + h + 0.09, f"{i}", lab, 12.5, ha="center", z=113)
    T(pax, x + miles * in_per_mi + 0.22, y + h + 0.09, "miles", lab, 12.5, z=113)
    yk = y - 0.17
    for i in range(km):
        fc = S.INK if i % 2 == 1 else PANEL_FILL
        pax.add_patch(Rectangle((x + i * in_per_km, yk), in_per_km, h, fc=fc, ec=S.INK, lw=0.6, zorder=112))
    for i in range(0, km + 1, 2):
        T(pax, x + i * in_per_km, yk - 0.26, f"{i}", lab, 12.5, ha="center", z=113)
    T(pax, x + km * in_per_km + 0.22, yk - 0.26, "kilometers", lab, 12.5, z=113)
    T(pax, x, y + h + 0.42, f"Scale 1:{int(F.scale):,} at 84 × 42 in  ·  1 inch = about "
      f"{F.m_per_in / 1609.344:.2f} mile (use the bars at other sizes)", fonts.sans(400, True), 12.5,
      color=S.INK_SOFT, z=113)


def north_arrow(pax, fonts, x, y, size=1.05):
    s = size
    left = [(x, y + s * 0.6), (x - s * 0.2, y - s * 0.4), (x, y - s * 0.2)]
    right = [(x, y + s * 0.6), (x + s * 0.2, y - s * 0.4), (x, y - s * 0.2)]
    pax.add_patch(MplPolygon(left, closed=True, fc=S.INK, ec=S.INK, lw=0.6, zorder=112))
    pax.add_patch(MplPolygon(right, closed=True, fc=PANEL_FILL, ec=S.INK, lw=0.6, zorder=112))
    T(pax, x, y + s * 0.7, "N", fonts.serif(600), 24, ha="center", z=113)


CREDITS = (
    "Data sources. U.S. Fish and Wildlife Service: refuge units and land status, approved acquisition boundary, "
    "trails and facilities (FWS cadastral and refuge facilities data, 2020–2026); unit acreages are computed "
    "from these data. U.S. Geological Survey: 3D Elevation Program 1/3 arc-second elevation (relief shading "
    "and valley-floor tint), National Hydrography Dataset, Geographic Names Information System. U.S. Census "
    "Bureau: TIGER/Line Shapefiles 2025 (roads, rail, boundaries, cities, tribal lands, river surfaces), 2025 "
    "cartographic boundary files, Vintage 2025 population estimates. Minnesota Department of Natural Resources "
    "via the Minnesota Geospatial Commons: state parks, Scientific and Natural Areas, Wildlife Management "
    "Areas, state trails, lakes and wetlands. Metropolitan Council: regional parks, regional trails, airport "
    "boundaries. Minnesota Department of Transportation: airport runways. Dakota place names (Bdote, Mni "
    "Sota Wakpa, Wakpa Tanka, Oheyawahi): Minnesota Historical Society and National Park Service.\n"
    "Boundaries are approximate and for general reference only. This is not an official U.S. Fish and "
    "Wildlife Service publication; check with the refuge for current regulations, trail conditions and "
    "seasonal closures. Map compiled October 2026."
)


def credits(pax, fonts, x, ytop, width):
    yy = ytop
    for i, para in enumerate(CREDITS.split("\n")):
        yy = paragraph(pax, x, yy, para, fonts.sans(400), 11.5, width, leading=1.32, color=S.INK_SOFT) - 0.08


# -------------------------------------------------------------------------
# locator map
# -------------------------------------------------------------------------
def locator(pax, F, L, fonts, x, y, w, h):
    fig = pax.figure
    from layers import P as _P
    st = gpd.read_file("zip://" + _P("extra", "cb_2025_us_state_500k.zip"))
    st = st[st["STUSPS"].isin(["MN", "WI", "IA", "ND", "SD", "MI"])].to_crs(26915)
    mn = st[st["STUSPS"] == "MN"]
    ax = fig.add_axes([x / F.page_w, y / F.page_h, w / F.page_w, h / F.page_h], zorder=6)
    ax.set_axis_off()
    b = mn.total_bounds
    pad = 40000
    cx, cy = (b[0] + b[2]) / 2 + 60000, (b[1] + b[3]) / 2
    # fit MN height into the box
    span_y = (b[3] - b[1]) + 2 * pad
    span_x = span_y * w / h
    ax.set_xlim(cx - span_x / 2, cx + span_x / 2)
    ax.set_ylim(cy - span_y / 2, cy + span_y / 2)
    ax.patch.set_alpha(0)
    others = st[st["STUSPS"] != "MN"]
    D.polys(ax, others.geometry, fc="#EEE7D6", ec="#B9AD98", lw=0.5, zorder=1)
    D.polys(ax, mn.geometry, fc="#E4E3C9", ec="#7D7262", lw=0.9, zorder=2)
    cb = L["mn_counties_cb"].to_crs(26915)
    metro = cb[cb["NAME"].isin(["Hennepin", "Ramsey", "Dakota", "Scott", "Carver", "Anoka", "Washington"])]
    D.polys(ax, metro.geometry, fc="#D9D2BC", ec="#A79C88", lw=0.3, zorder=3)
    ax.add_patch(Rectangle((F.x0, F.y0), F.x1 - F.x0, F.y1 - F.y0, fc="none", ec=S.REFUGE_LINE, lw=1.6,
                           zorder=5))
    upp_l = span_y / (h * 72)
    for txt, lon, lat, sz in [("MINNESOTA", -94.6, 46.35, 14), ("WIS.", -90.6, 45.0, 10), ("IOWA", -94.0, 43.33, 10),
                              ("S.D.", -97.2, 44.3, 10), ("N.D.", -97.6, 47.6, 10), ("MICH.", -87.6, 46.35, 10),
                              ("CANADA", -94.2, 49.6, 10)]:
        from labels import ll
        px, py = ll(lon, lat)
        spaced_text(ax, px, py, txt, fonts.sans(600), sz, tracking=0.25, units_per_pt=upp_l,
                    color=S.INK_SOFT, zorder=8, va="center")
    ax.add_patch(Rectangle((cx - span_x / 2, cy - span_y / 2), span_x, span_y, fc="none", ec=PANEL_EDGE, lw=1.0,
                           zorder=30, clip_on=False))
    header(pax, x, y + h + 0.17, "LOCATION", fonts, size=16, tracking=0.28)


# -------------------------------------------------------------------------
# Round Lake Unit inset
# -------------------------------------------------------------------------
RL_SCALE = 21000.0


def round_lake_inset(pax, F, L, fonts, x, y, w, h):
    import labels as LB
    from build_map import road_classes, water_polys
    fig = pax.figure
    cap_h = 0.62
    mh = h - cap_h
    m_per_in = RL_SCALE * 0.0254
    cx, cy = 486050.0, 4991600.0
    x0, x1 = cx - w / 2 * m_per_in, cx + w / 2 * m_per_in
    y0, y1 = cy - mh / 2 * m_per_in, cy + mh / 2 * m_per_in
    ax = fig.add_axes([x / F.page_w, y / F.page_h, w / F.page_w, mh / F.page_h], zorder=6)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_axis_off()
    ax.patch.set_facecolor(S.BG)
    ax.patch.set_alpha(1)
    clip = box(x0, y0, x1, y1)
    upp = m_per_in / 72.0

    def clipg(g):
        g = g[g.intersects(clip)]
        return [geom.intersection(clip) for geom in g.geometry]

    mil = L["military"]
    D.polys(ax, clipg(mil[mil["FULLNAME"].str.contains("Ammunition", na=False)]), fc="#EAE2CF", ec="#B3A790",
            lw=0.6, zorder=2, dashes=(3, 2))
    u = L["units"]
    rl = u[u["unit_name"] == "Round Lake Unit"]
    D.polys(ax, clipg(rl[rl["DIV"] == "Fee"]), fc=S.REFUGE_FILL, ec="none", zorder=3)
    D.polys(ax, clipg(rl[rl["DIV"] != "Fee"]), fc=S.REFUGE_EASE_FILL, ec="none", zorder=3)
    rc = road_classes({"road_edges": L["inset_roads"]})
    D.lines(ax, clipg(rc["local"]), color=S.ROAD_LOCAL, lw=0.45, zorder=4)
    D.lines(ax, clipg(rc["county"]), color=S.ROAD_MINOR, lw=1.0, zorder=4)
    rivers, lakes, marsh = water_polys(L, prefix="inset_")
    D.polys(ax, clipg(marsh), fc=S.MARSH_FILL, ec="none", zorder=5)
    D.polys(ax, clipg(lakes), fc=S.WATER, ec=S.WATER_LINE, lw=0.4, zorder=5)
    D.lines(ax, clipg(rc["ramp"]), color=S.ROAD_CASING, lw=1.3, zorder=6)
    D.lines(ax, clipg(rc["highway"]), color=S.STATE_CASE, lw=3.2, zorder=6)
    D.lines(ax, clipg(rc["freeway_o"]), color=S.US_CASE, lw=3.6, zorder=6)
    D.lines(ax, clipg(rc["freeway_i"]), color=S.INTERSTATE_CASE, lw=4.6, zorder=6)
    D.lines(ax, clipg(rc["ramp"]), color=S.STATE_HWY, lw=0.6, zorder=7)
    D.lines(ax, clipg(rc["highway"]), color=S.STATE_HWY, lw=2.1, zorder=7)
    D.lines(ax, clipg(rc["freeway_o"]), color=S.US_HWY, lw=2.5, zorder=7)
    D.lines(ax, clipg(rc["freeway_i"]), color=S.INTERSTATE, lw=3.4, zorder=7)
    D.polys(ax, clipg(rl), fc="none", ec=S.REFUGE_LINE, lw=1.6, zorder=8)
    for kind, num, sx_, sy_ in [("I", "35W", 485253, 4992557), ("I", "694", 484504, 4990336),
                                ("US", "10", 485790, 4992190)]:
        if x0 < sx_ < x1 and y0 < sy_ < y1:
            draw_shield(ax, sx_, sy_, kind, num, fonts, units_per_pt=upp, size_pt=15, zorder=25)
    labs = []
    unit_geom = rl.unary_union
    up = unit_geom.representative_point()
    labs.append(("ROUND LAKE\nUNIT", up.x + 1300, up.y - 450, 15, fonts.serif(700), S.REFUGE_LABEL))
    wb = L["inset_wb"]
    rlake = wb[(wb["GNIS_NAME"] == "Round Lake")]
    rlake = rlake[rlake.intersects(clip)]
    if len(rlake):
        g = max(rlake.geometry, key=lambda q: q.area)
        p = g.representative_point()
        labs.append(("Round\nLake", p.x, p.y, 12.5, fonts.serif(500, True), S.WATER_LABEL))
    tc = mil[mil["FULLNAME"].str.contains("Ammunition", na=False)]
    if len(tc):
        g = tc.geometry.iloc[0].intersection(clip)
        if not g.is_empty:
            p = g.representative_point()
            labs.append(("ARDEN HILLS ARMY\nTRAINING SITE", p.x, p.y, 11, fonts.sans(600), S.TOWNSHIP_LABEL))
    for txt, px, py, size, fp, col in labs:
        LB.multiline(ax, px, py, txt, fp, size, upp=upp, tracking=0.12, color=col, halo_w=2.6, zorder=20)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none", ec=PANEL_EDGE, lw=1.0, zorder=30))
    # caption above the inset
    header(pax, x, y + h - 0.3, "ROUND LAKE UNIT, ARDEN HILLS", fonts, size=16, tracking=0.28)
    T(pax, x, y + h - 0.55, f"About 13 miles north of Historic Fort Snelling  ·  scale 1:{int(RL_SCALE):,}",
      fonts.sans(400, True), 11, color=S.INK_SOFT)


# -------------------------------------------------------------------------
def draw_panels(pax, F, L, fonts):
    title_block(pax, F, fonts)
    info_block(pax, F, L, fonts)
    legend_block(pax, F, L, fonts)

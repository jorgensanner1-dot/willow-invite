"""Hand-placement tables for map type.  Edited between preview rounds.

Positions: page=(x, y) are sheet inches from the lower-left corner of the sheet;
lonlat=(lon, lat) are WGS84.  Offsets dx, dy are points at print size.
"""
from __future__ import annotations

from shapely.geometry import box
from shapely.ops import linemerge

import style as S

# -------------------------------------------------------------------------
# cities and towns
# -------------------------------------------------------------------------
CITY_OVR = {
    "Bloomington": dict(page=(56.6, 33.4)),
    "Minneapolis": dict(page=(62.0, 40.5), size=24),
    "St. Paul": dict(page=(81.3, 40.55), size=24, text="SAINT PAUL"),
    "Edina": dict(page=(56.0, 39.2)),
    "Richfield": dict(page=(62.3, 38.3)),
    "Eagan": dict(page=(70.6, 31.6)),
    "Burnsville": dict(page=(60.15, 24.65)),
    "Savage": dict(page=(55.0, 26.0)),
    "Shakopee": dict(page=(47.6, 28.0)),
    "Eden Prairie": dict(page=(48.6, 36.6)),
    "Chanhassen": dict(page=(41.6, 36.9)),
    "Chaska": dict(page=(38.6, 31.6)),
    "Carver": dict(page=(34.6, 27.9), dot=(35.6, 27.35)),
    "Jordan": dict(page=(37.0, 16.35), dot=(35.7, 16.2)),
    "Belle Plaine": dict(page=(26.0, 11.3), dot=(26.0, 12.0)),
    "Henderson": dict(page=(14.1, 2.65), dot=(15.3, 2.62), size=17),
    "Prior Lake": dict(page=(52.95, 21.95)),
    "Mendota Heights": dict(page=(74.0, 37.9)),
    "Mendota": dict(page=(71.58, 39.88), dot=(70.95, 39.88), size=13),
    "West St. Paul": dict(page=(77.0, 40.05)),
    "South St. Paul": dict(page=(79.2, 39.3)),
    "Inver Grove Heights": dict(page=(78.6, 33.4)),
    "Apple Valley": dict(page=(68.2, 24.8)),
    "Lakeville": dict(page=(64.0, 18.4)),
    "Rosemount": dict(page=(78.0, 24.4)),
    "Farmington": dict(page=(71.0, 16.6)),
    "Credit River": dict(page=(56.4, 17.5)),
    "Victoria": dict(page=(33.4, 38.2)),
    "Waconia": dict(page=(25.4, 34.2)),
    "Cologne": dict(page=(24.2, 27.2), dot=(24.2, 27.8)),
    "Norwood Young America": dict(page=(15.0, 27.4), dot=(15.0, 28.0)),
    "Hamburg": dict(page=(11.4, 23.3), dot=(11.4, 23.9)),
    "Green Isle": dict(page=(8.2, 17.9), dot=(8.2, 18.5)),
    "Arlington": dict(page=(2.9, 10.55), dot=(2.9, 11.15)),
    "New Prague": dict(page=(40.0, 3.35), dot=(40.0, 4.2)),
    "Elko New Market": dict(hide=True),
    "Newport": dict(hide=True),
    "St. Paul Park": dict(hide=True),
    "Empire": dict(page=(76.0, 17.4), dot=(76.0, 18.0)),
    "Coates": dict(page=(81.1, 21.85), dot=(80.5, 21.7)),
    "Hampton": dict(hide=True),
    "Randolph": dict(hide=True),
    "Mayer": dict(hide=True),
    "Lester Prairie": dict(hide=True),
    "New Germany": dict(hide=True),
    "Plato": dict(page=(5.8, 27.5), dot=(5.8, 28.1)),
    "Lilydale": dict(hide=True),
    "Sunfish Lake": dict(hide=True),
    "St. Bonifacius": dict(hide=True),
    "Shorewood": dict(hide=True),
    "Excelsior": dict(hide=True),
}
# Minneapolis and Saint Paul sit just beyond the top edge: directional labels
EDGE_LABELS = []

# -------------------------------------------------------------------------
# refuge units
# -------------------------------------------------------------------------
UNIT_OVR = {
    "Long Meadow Lake Unit": dict(page=(63.35, 34.45), rot=48.0, text="LONG MEADOW\nLAKE UNIT", size=23),
    "Black Dog Lake Unit": dict(page=(63.75, 30.55), rot=35.0, text="BLACK DOG LAKE UNIT", size=23),
    "Bloomington Ferry Unit": dict(page=(55.6, 31.35), text="BLOOMINGTON\nFERRY UNIT", size=22),
    "Wilkie Unit": dict(page=(51.1, 29.4)),
    "Upgrala Unit": dict(page=(47.0, 32.95), text="UPGRALA UNIT"),
    "Chaska Unit": dict(page=(38.0, 28.1), rot=40.0, text="CHASKA UNIT", size=17),
    "Rapids Lake Unit": dict(page=(32.6, 24.5)),
    "Louisville Swamp Unit": dict(page=(37.65, 21.3), text="LOUISVILLE\nSWAMP UNIT", size=23),
    "San Francisco Unit": dict(page=(33.1, 20.25)),
    "St. Lawrence Unit": dict(page=(30.6, 15.25), rot=25.0, text="ST. LAWRENCE\nUNIT", size=16),
    "Jessenland Unit": dict(page=(19.35, 10.85)),
    "Blakeley Unit": dict(page=(15.8, 5.3), size=21),
    "Round Lake Unit": dict(hide=True),   # shown in its own inset
}

# -------------------------------------------------------------------------
# rivers: (gnis name, text, page x, page y, size, offset_pt, tracking, span_in[, color])
# -------------------------------------------------------------------------
RIVER_LABELS = [
    ("Minnesota River", "Minnesota River", 22.9, 12.9, 32, -28, 0.24, 6.0),
    ("Minnesota River", "Minnesota River", 40.9, 29.9, 32, 24, 0.20, 7.5),
    ("Minnesota River", "Minnesota River", 58.6, 29.6, 32, -30, 0.24, 7.5),
    ("Minnesota River", "Mni Sota Wakpa", 58.6, 29.6, 19, -62, 0.18, 7.5),
    ("Mississippi River", "Mississippi River", 81.5, 31.9, 30, 6, 0.24, 6.5),
    ("Mississippi River", "Wakpa Tanka", 81.5, 31.9, 18, -40, 0.18, 6.5),
]

LAKE_OVR = {
    "Long Meadow Lake": dict(page=(66.2, 35.0), size=14, rot=48),
    "Black Dog Lake": dict(page=(62.9, 30.85), size=14),
    "Gun Club Lake": dict(page=(68.6, 36.3), size=12),
    "Lake Minnetonka": dict(page=(35.0, 40.45), size=15),
    "Cedar Lake": dict(page=(43.64, 9.45), size=11.5, text="Cedar\nLake"),
    "Saint Albans Bay": dict(hide=True),
    "Lake Nokomis": dict(hide=True),
    "Renneberg Lake": dict(hide=True),
    "River Lake": dict(hide=True),
    "Baldwin Lake": dict(page=(82.3, 28.75), size=14),
    "Mooers Lake": dict(page=(82.55, 30.05), size=12),
    "Lower Prior Lake": dict(page=(53.0, 24.05), size=14),
    "Lake Waconia": dict(size=17),
    "Rapids Lake": dict(min_ha=0.5, page=(35.6, 23.6), size=13),
    "Fisher Lake": dict(size=12),
    "Rice Lake": dict(size=12),
    "Blue Lake": dict(size=12),
    "Snelling Lake": dict(size=12, min_ha=30),
    "Louisville Swamp": dict(page=(37.55, 22.75), size=13),
}

LAKE_EXTRA = [  # (text, page xy, size, rotation): lakes whose automatic anchor falls off the sheet
    ("Spring Lake", (82.3, 27.1), 14, 0),
    ("Tiger Lake", (12.08, 28.78), 13, 0),
]

# (gnis_name, near lon|page x, near lat|page y, size, text, span_m)
STREAM_LABELS = [
    ("Credit River", 56.55, 23.2, 14, "Credit River", 3500),
    ("Sand Creek", -93.58, 44.69, 14, "Sand  Creek", 3500),
    ("Carver Creek", -93.66, 44.775, 13, "Carver Creek", 2600),
    ("Bevens Creek", -93.73, 44.70, 14, "Bevens Creek", 3500),
    ("Purgatory Creek", -93.43, 44.83, 13, "Purgatory Creek", 2800),
    ("Riley Creek", -93.5146, 44.8284, 13, "Riley Creek", 2500),
    ("Ninemile Creek", 58.65, 34.35, 12, "Nine Mile Creek", 2600),
    ("High Island Creek", 13.85, 6.9, 12, "High Island Creek", 2400),
    ("Eagle Creek", 53.9, 27.85, 12, "Eagle Creek", 2600),
    ("Robert Creek", 24.1, 9.3, 13, "Robert Creek", 1700),
]

# -------------------------------------------------------------------------
# parks and natural areas
# -------------------------------------------------------------------------
PARK_LABELS = [
    dict(text="Fort Snelling\nState Park", page=(67.75, 34.95), size=15, rot=50),
    dict(text="Minnesota Valley State Recreation Area", lonlat=(-93.715, 44.672), size=14, rot=36),
    dict(text="Minnesota Valley\nState Recreation Area", page=(41.2, 29.25), size=12),
    dict(text="Murphy-Hanrehan\nPark Reserve", page=(58.1, 21.3), size=15),
    dict(text="Cleary Lake\nRegional Park", page=(53.55, 18.35), size=14),
    dict(text="Spring Lake\nRegional Park", page=(47.7, 21.3), size=13),
    dict(text="Hyland-Bush-Anderson\nLakes Park Reserve", page=(54.85, 35.6), size=14),
    dict(text="Lebanon Hills\nRegional Park", page=(72.0, 28.4), size=15),
    dict(text="Cedar Lake Farm\nRegional Park", page=(43.1, 7.4), size=13),
    dict(text="Carver Park\nReserve", page=(31.0, 39.5), size=15),
    dict(text="Lake Minnewashta\nRegional Park", page=(38.4, 39.9), size=13),
    dict(text="Whitetail Woods\nRegional Park", page=(76.2, 20.4), size=13),
    dict(text="Vermillion Highlands\nResearch, Recreation and WMA", page=(78.6, 18.4), size=13),
    dict(text="Savage Fen\nScientific and Natural Area", page=(57.4, 27.15), size=12),
    dict(text="Seminary Fen SNA", page=(41.0, 32.2), size=12),
    dict(text="Pine Bend\nBluffs SNA", page=(80.63, 29.62), size=11),
    dict(text="Ney WMA", page=(18.0, 6.0), size=12),
    dict(text="SHAKOPEE MDEWAKANTON\nSIOUX COMMUNITY", page=(49.55, 25.25), size=13, color=S.TRIBAL_LABEL,
         track=0.12),
]

# -------------------------------------------------------------------------
# points: refuge facilities and landmarks
# -------------------------------------------------------------------------
POI_LABELS = [
    # visitor centers
    dict(text="Bloomington Education\nand Visitor Center", lonlat=(-93.216298, 44.859841), sym="visitor",
         size=14, ha="left", dx=13, dy=-5),
    dict(text="Rapids Lake Education\nand Visitor Center", lonlat=(-93.628795, 44.718348), sym="visitor",
         size=14, ha="right", dx=-13, dy=-12),
    # refuge trailheads and parking (USFWS facility points)
    dict(text="Bass Ponds", lonlat=(-93.235759, 44.847805), sym="trailhead", size=11, ha="left"),
    dict(text="Old Cedar Ave.", lonlat=(-93.244938, 44.830658), sym="trailhead", size=11, ha="right"),
    dict(text="Lyndale Ave.", lonlat=(-93.288998, 44.801748), sym="trailhead", size=11, ha="right", dy=4),
    dict(text="Bloomington Ferry", lonlat=(-93.386888, 44.799668), sym="trailhead", size=11, ha="left", dy=6),
    dict(text="Wilkie", lonlat=(-93.419608, 44.795388), sym="trailhead", size=11, ha="right"),
    dict(text=None, lonlat=(-93.403088, 44.792188), sym="trailhead"),
    dict(text=None, lonlat=(-93.526208, 44.802108), sym="trailhead"),
    dict(text="North Hunter Lot", lonlat=(-93.647818, 44.734608), sym="trailhead", size=11, ha="right"),
    dict(text="Louisville\nSwamp", lonlat=(-93.597698, 44.739718), sym="trailhead", size=11, ha="left"),
    dict(text=None, lonlat=(-93.595079, 44.715777), sym="trailhead"),
    dict(text=None, lonlat=(-93.627838, 44.693108), sym="trailhead"),
    dict(text=None, lonlat=(-93.641118, 44.692109), sym="trailhead"),
    dict(text=None, lonlat=(-93.876818, 44.611148), sym="trailhead"),
    dict(text=None, lonlat=(-93.888948, 44.604488), sym="trailhead"),
    dict(text=None, lonlat=(-93.890878, 44.531718), sym="trailhead"),
    dict(text=None, lonlat=(-93.899558, 44.529798), sym="trailhead"),
    # boat launches
    dict(text=None, lonlat=(-93.288808, 44.801118), sym="boat"),
    dict(text="Jens Caspersen Landing", lonlat=(-93.230228, 44.827123), sym="boat", size=11, ha="left"),
    dict(text=None, lonlat=(-93.616561, 44.766706), sym="boat"),
    # refuge historic and natural points
    dict(text="Jabs Farm", lonlat=(-93.619752, 44.734419), sym="historic", size=11, ha="left"),
    dict(text="Carver Rapids", lonlat=(-93.632668, 44.725303), sym="poi", size=11, ha="right", italic=True),
    # landmarks (coordinates: Met Council address points, FAA, USGS GNIS; see README)
    dict(text="Historic\nFort Snelling", lonlat=(-93.185671, 44.893067), sym="historic", size=13, ha="right",
         bold=True),
    dict(text="Bdote", lonlat=(-93.150698, 44.896753), sym="none", size=20, ha="left", dx=6, dy=8,
         italic=True, color="#4A3A5A"),
    dict(text="where two waters\ncome together", lonlat=(-93.150698, 44.896753), sym="none", size=10.5,
         ha="left", dx=6, dy=-14, italic=True, color="#4A3A5A"),
    dict(text="Mississippi River", page=(70.25, 40.72), sym="none", size=14, ha="center", italic=True,
         color=S.WATER_LABEL),
    dict(text="Vermillion River", page=(81.05, 16.36), sym="none", size=14, ha="center", italic=True,
         color=S.WATER_LABEL),
    dict(text="Pike Island", lonlat=(-93.165498, 44.892188), sym="none", size=11.5, ha="center", italic=True),
    dict(text="Sibley Historic Site", lonlat=(-93.164568, 44.887624), sym="historic", size=11, ha="left", dy=-6),
    dict(text="Oheyawahi\n(Pilot Knob)", lonlat=(-93.167327, 44.88073), sym="poi", size=11, ha="left"),
    dict(text="Minneapolis–St. Paul\nInternational Airport", lonlat=(-93.221778, 44.881972), sym="airport",
         size=13, ha="left", dx=12, bold=True),
    dict(text="Fort Snelling\nNational Cemetery", lonlat=(-93.2150, 44.8700), sym="none", size=11, ha="center",
         italic=True),
    dict(text="Mall of America", lonlat=(-93.241953, 44.856332), sym="poi", size=12, ha="right"),
    dict(text="Flying Cloud\nAirport", lonlat=(-93.458572, 44.827507), sym="airport", size=12, ha="left", dx=12),
    dict(text="Valleyfair", lonlat=(-93.450556, 44.798611), sym="poi", size=11, ha="left"),
    dict(text="Canterbury Park", lonlat=(-93.482944, 44.790554), sym="poi", size=11, ha="right"),
    dict(text="The Landing", lonlat=(-93.488120, 44.803608), sym="historic", size=11, ha="right"),
    dict(text="Mystic Lake\nCasino", lonlat=(-93.475554, 44.730759), sym="poi", size=11, ha="left"),
    dict(text="Renaissance\nFestival", lonlat=(-93.597247, 44.743389), sym="poi", size=11, ha="right"),
    dict(text="Minnesota Landscape\nArboretum", lonlat=(-93.615548, 44.862269), sym="poi", size=12, ha="left"),
    dict(text="Minnesota Zoo", lonlat=(-93.196048, 44.767613), sym="poi", size=12, ha="left"),
    dict(text="Little Rapids\nhistorical marker", lonlat=(-93.622222, 44.776389), sym="historic", size=11,
         ha="right"),
    dict(text="Ney Nature Center", lonlat=(-93.884561, 44.541103), sym="poi", size=11, ha="left"),
    dict(text="Fleming Field", lonlat=(-93.03291, 44.85711), sym="airport", size=11, ha="left", dx=11),
]

SHIELDS = []   # empty -> automatic placement along routes
SHIELD_DROP = [("MN", "77", 65.69, 33.42), ("US", "52", 80.35, 21.62), ("MN", "5", 61.28, 37.00),
               ("US", "212", 25.65, 27.51)]
SHIELD_ADD = [("MN", "77", -93.2222, 44.7995), ("US", "52", -93.0287, 44.7046), ("I", "494", -93.3187, 44.8613),
              ("US", "169", -93.3986, 44.8365), ("I", "35W", -93.2962, 44.8814), ("MN", "62", -93.3285, 44.8870),
              ("MN", "101", -93.538942, 44.821997),
              ("MN", "55", -93.1285, 44.8509), ("MN", "55", -93.0120, 44.7560), ("I", "35E", -93.1406, 44.8806),
              ("I", "35E", -93.2519, 44.7574), ("MN", "13", -93.1880, 44.8387), ("MN", "3", -93.0853, 44.8371),
              ("US", "52", -93.0594, 44.8621), ("MN", "77", -93.2474, 44.8705), ("MN", "13", -93.39280, 44.73045),
              ("MN", "5", -94.04863, 44.63115)]

# (layer key, name field, name prefix, page x, page y, size, text, span_in, colour)
TRAIL_LABELS = [
    ("state_trails", "trail_name", "Minnesota Valley State Trail", 33.2, 18.6, 13,
     "Minnesota Valley State Trail", 4.2, S.TRAIL_STATE),
    ("regional_trails", "TrailName", "Minnesota River Greenway", 63.2, 31.35, 12,
     "Minnesota River Greenway", 3.2, S.TRAIL_REGIONAL),
    ("regional_trails", "TrailName", "Big Rivers", 70.1, 38.4, 11, "Big Rivers Trail", 1.5, S.TRAIL_REGIONAL),
    ("fws_trails", "TRNAME", "River Bottoms Trail", 60.0, 30.0, 12, "River Bottoms Trail", 3.0, S.TRAIL_REFUGE),
]

COUNTY_LABELS = [  # (text, page x, page y, rotation)
    ("HENNEPIN COUNTY", 46.6, 38.0, 0),
    ("CARVER COUNTY", 28.8, 30.0, 0),
    ("SCOTT COUNTY", 43.9, 17.15, 0),
    ("DAKOTA COUNTY", 72.6, 22.5, 0),
    ("SIBLEY COUNTY", 9.0, 13.6, 0),
    ("LE SUEUR COUNTY", 29.8, 2.2, 0),
    ("McLEOD COUNTY", 6.0, 30.0, 0),
]


# -------------------------------------------------------------------------
def auto_shields(F, L, panels, spacing_in=12.0, edge_in=1.6):
    from pyproj import Transformer
    inv = Transformer.from_crs(26915, 4326, always_xy=True)
    r = L["routes"]
    r = r[r["ROUTE_TYPE"].isin(["I", "US", "MN"])]
    inner = box(F.x0 + edge_in * F.m_per_in, F.y0 + edge_in * F.m_per_in,
                F.x1 - edge_in * F.m_per_in, F.y1 - edge_in * F.m_per_in)
    for p in panels:
        inner = inner.difference(p)
    out = []
    spacing = spacing_in * F.m_per_in
    placed = []
    order = {"I": 0, "US": 1, "MN": 2}
    for _, row in sorted(r.iterrows(), key=lambda t: order[t[1]["ROUTE_TYPE"]]):
        g = row.geometry.intersection(inner)
        if g.is_empty:
            continue
        parts = list(g.geoms) if hasattr(g, "geoms") else [g]
        parts = [p for p in parts if p.geom_type == "LineString"]
        try:
            m = linemerge(parts)
            parts = list(m.geoms) if m.geom_type == "MultiLineString" else [m]
        except Exception:
            pass
        for part in parts:
            if part.length < spacing * 0.35:
                continue
            n = max(1, int(part.length // spacing))
            for i in range(n):
                d = (i + 0.5) * part.length / n
                p = part.interpolate(d)
                if any(p.distance(q) < 2.4 * F.m_per_in for q in placed):
                    continue
                placed.append(p)
                lon, lat = inv.transform(p.x, p.y)
                out.append((row["ROUTE_TYPE"], str(row["ROUTE_NUM"]), lon, lat))
    return out


def apply(ns, F=None, L=None):
    for k in ["CITY_OVR", "UNIT_OVR", "RIVER_LABELS", "LAKE_OVR", "LAKE_EXTRA", "STREAM_LABELS", "PARK_LABELS",
              "POI_LABELS", "COUNTY_LABELS", "EDGE_LABELS", "TRAIL_LABELS"]:
        ns[k] = globals()[k]
    if F is not None and L is not None:
        import panels as PN
        pb = []
        for d in (PN.TITLE, PN.LEGEND, PN.INFO):
            x0, y0 = F.to_map(d["x"], d["y"])
            x1, y1 = F.to_map(d["x"] + d["w"], d["y"] + d["h"])
            pb.append(box(x0, y0, x1, y1).buffer(0.6 * F.m_per_in))
        from pyproj import Transformer
        fwd = Transformer.from_crs(4326, 26915, always_xy=True)

        def keep(sh):
            px, py = F.to_page(*fwd.transform(sh[2], sh[3]))
            return not any(sh[0] == k and sh[1] == n and abs(px - x) < 0.3 and abs(py - y) < 0.3
                           for k, n, x, y in SHIELD_DROP)
        ns["SHIELDS"] = SHIELDS or ([s_ for s_ in auto_shields(F, L, pb) if keep(s_)] + SHIELD_ADD)

"""Load every source layer, reproject to UTM 15N and clip to the sheet (plus a margin).

Paths point at the downloads gathered for this map (see README for sources).
Results are cached as pickles so layout iterations are fast.
"""
from __future__ import annotations

import os
import pickle
import warnings

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from frame import CRS

warnings.filterwarnings("ignore")

DATA = os.environ.get(
    "MVNWR_DATA",
    "/tmp/claude-0/-home-user-willow-invite/e209d3f7-1d32-5856-8863-d3584c3cde89/scratchpad/data")
CACHE = os.environ.get("MVNWR_CACHE", os.path.join(DATA, "_cache"))


def P(*parts):
    return os.path.join(DATA, *parts)


def read(path, layer=None, clip=None, columns=None, where=None):
    kw = {}
    if layer:
        kw["layer"] = layer
    if where:
        kw["where"] = where
    g = gpd.read_file(path, **kw)
    if g.crs is None:
        g = g.set_crs(4326)
    g = g.to_crs(CRS)
    if clip is not None:
        g = g[g.intersects(clip)].copy()
        g["geometry"] = g.geometry.intersection(clip)
        g = g[~g.geometry.is_empty]
    if columns:
        keep = [c for c in columns if c in g.columns] + ["geometry"]
        g = g[keep]
    return g


def load_all(frame, margin=3000.0, refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    key = os.path.join(CACHE, f"layers_{int(frame.x0)}_{int(frame.y0)}_{int(frame.scale)}.pkl")
    if os.path.exists(key) and not refresh:
        with open(key, "rb") as fh:
            return pickle.load(fh)
    x0, y0, x1, y1 = frame.bounds
    clip = box(x0 - margin, y0 - margin, x1 + margin, y1 + margin)
    L = {}

    # ---------------- refuge (USFWS) ----------------
    L["units"] = read(P("audit", "mvnwr_units_mapready_r2.gpkg"), "units_by_interest")
    L["units_dissolved"] = read(P("audit", "mvnwr_units_mapready_r2.gpkg"), "units_dissolved")
    L["unit_pts"] = read(P("audit", "mvnwr_units_mapready_r2.gpkg"), "unit_label_points")
    L["approved"] = read(P("fws", "mvnwr_fws_approved_boundary.gpkg"), "mvnwr_approved_boundary")
    L["fws_interest"] = read(P("fws", "mvnwr_fws_interest_simplified.gpkg"), "mvnwr_interest_simplified")
    L["fws_trails"] = read(P("fws", "mvnwr_trails_fws_inventory.gpkg"), "mvnwr_trail_segments")
    L["fws_poi"] = read(P("fws", "mvnwr_points_of_interest.gpkg"), "poi")
    pk = read(P("fws", "mvnwr_fws_facilities.gpkg"), "parking_lots_poly")
    L["fws_parking"] = pk[pk["ORGCODE"].astype(str) == "32590"]

    # ---------------- hydrography (USGS NHD High Resolution) ----------------
    fl = read(P("audit", "nhd_flowline.geojson"), clip=clip)
    L["flowlines"] = fl
    L["nhd_area"] = read(P("audit", "nhd_area.geojson"), clip=clip)
    L["nhd_wb"] = read(P("audit", "nhd_waterbody.geojson"), clip=clip)
    L["dnr_basins"] = read(P("audit", "dnr_hydro_features_all.geojson"), clip=clip,
                           columns=["pw_basin_name", "map_label", "wb_class", "acres", "dowlknum"])

    # ---------------- Census TIGER/Line 2025 ----------------
    T = lambda f: P("tiger", f)
    L["counties"] = read(T("tiger2025_mn_counties.gpkg"))
    L["places"] = read(T("tiger2025_mn_places.gpkg"))
    L["cousub"] = read(T("tiger2025_mn_cousub.gpkg"))
    L["roads"] = read(T("tiger2025_mn_roads_all.gpkg"), clip=clip)
    L["routes"] = read(T("tiger2025_highway_routes.gpkg"), clip=clip)
    L["prisec"] = read(T("tiger2025_mn_prisecroads.gpkg"), clip=clip)
    L["rails"] = read(T("tiger2025_rails.gpkg"), clip=clip)
    L["arealm"] = read(T("tiger2025_mn_arealm.gpkg"))
    L["pointlm"] = read(T("tiger2025_mn_pointlm.gpkg"), clip=clip)
    L["aiannh"] = read(T("tiger2025_aiannh.gpkg"))
    L["military"] = read(T("tiger2025_military.gpkg"))
    L["tiger_water"] = read(T("tiger2025_mn_areawater.gpkg"), clip=clip)
    try:
        L["road_edges"] = read(T("tiger2025_mn_road_edges_routes.gpkg"), "road_edges", clip=clip)
    except Exception:
        L["road_edges"] = None

    # ---------------- Minnesota DNR ----------------
    D = lambda f: P("mndnr", f)
    L["state_parks"] = read(P("audit", "mndnr_state_parks_statutory_bdry.gpkg"))
    L["state_park_lands"] = read(P("audit", "mndnr_state_parks_managed_lands.gpkg"))
    L["sna"] = read(P("audit", "mndnr_sna_boundaries.gpkg"))
    L["wma"] = read(P("audit", "mndnr_wma_boundaries.gpkg"))
    L["ama"] = read(P("audit", "mndnr_ama_fisheries_acquisitions.gpkg"))
    L["dnr_units"] = read(P("audit", "mndnr_management_units_all.gpkg"))
    L["state_trails"] = read(P("audit", "mndnr_state_trails.gpkg"), clip=clip)
    L["water_trails"] = read(P("audit", "mndnr_state_water_trails.gpkg"), clip=clip)
    L["water_access"] = read(P("audit", "mndnr_water_access_sites.gpkg"), clip=clip)

    # ---------------- Metropolitan Council / MnDOT ----------------
    M = lambda f: P("metro", f)
    L["regional_parks"] = read(P("audit", "metc_regional_park_admin_boundaries.gpkg"))
    L["regional_trails"] = read(P("audit", "metc_regional_trails.gpkg"), clip=clip)
    L["runways"] = read(P("audit", "mndot_airport_runways.gpkg"))
    L["airports"] = read(P("audit", "mndot_airports.gpkg"))
    ab = read(M("metc_airport_boundaries_2025.gpkg"))
    L["airport_bdry"] = ab[ab["PRIVATEUSE"] == 0]

    # ---------------- Round Lake inset (Arden Hills) ----------------
    ib = box(482000, 4988000, 490500, 4995500)
    L["inset_roads"] = read(T("tiger2025_mn_road_edges_routes.gpkg"), "road_edges", clip=ib)
    L["inset_wb"] = read(P("audit", "nhd_waterbody.geojson"), clip=ib)
    L["inset_dnr"] = read(P("audit", "dnr_hydro_features_all.geojson"), clip=ib,
                          columns=["pw_basin_name", "map_label", "wb_class", "acres"])

    # ---------------- context ----------------
    L["states"] = gpd.read_file(P("extra", "states_region.gpkg"))
    L["mn_counties_cb"] = gpd.read_file(P("extra", "mn_counties_cb.gpkg"))

    with open(key, "wb") as fh:
        pickle.dump(L, fh)
    return L

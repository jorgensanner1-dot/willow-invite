# Minnesota Valley National Wildlife Refuge — wall map

A print-ready wall map of Minnesota Valley National Wildlife Refuge and the lower
Minnesota River from Fort Snelling to Henderson, built from official public GIS data.
It marks the refuge's 50th anniversary (established October 8, 1976).

## Files in `output/`

| File | What it is | Use it for |
|---|---|---|
| `MVNWR_wall_map_84x42in.pdf` | exactly 84 × 42 in, no bleed | **FedEx Office** and any shop printing on a 42-inch roll |
| `MVNWR_wall_map_84x42in_with-bleed.pdf` | 84.25 × 42.25 in, 0.125 in bleed on every side, trim box set to 84 × 42 | shops with 44-inch or wider media that trim to size |
| `MVNWR_wall_map_preview.jpg` | small preview image | looking at it on screen; not for printing |

Both PDFs: scale 1:42,000 (1 inch ≈ 0.66 mile at full size), UTM zone 15 north / NAD 1983,
warm beige `#F2EAD8` background edge to edge, all type and line work vector, one embedded
200 ppi terrain image, sRGB color profile embedded, fonts embedded, about 16 MB
(FedEx's online upload limit is 150 MB).

## How to print it at FedEx Office

FedEx Office prints custom poster sizes as a quote, on a 42-inch roll, with the 84-inch
side running along the roll.

1. Go to office.fedex.com → **Poster Prints** → upload `MVNWR_wall_map_84x42in.pdf`.
2. Choose **"Don't convert – keep this size."** The site will say a custom size needs a quote.
3. Paste this into the print instructions:

   > Custom poster, 84 in wide × 42 in tall, landscape, quantity 1. Heavyweight coated
   > MATTE paper (optional matte lamination). Print at 100%, do not scale or fit to page;
   > 42 in across the roll, 84 in along it. Print borderless if your printer supports it on
   > this paper; otherwise print centered at 100% and trim about 1/4 in off each 84-inch
   > edge so no white edge remains. Color: sRGB file with embedded profile; color-managed,
   > relative colorimetric, no auto-enhance, best quality mode. The background should be a
   > warm light beige, not white or yellow. Roll image side out in a tube; do not fold.

4. Submit the quote request, approve the emailed quote, and pay. Or bring the PDF on a USB
   drive to a FedEx Office with large-format printing (for example 80 S. 8th St.,
   Minneapolis) and read them the same instructions.
5. If the store has 44-inch or wider media, give them `MVNWR_wall_map_84x42in_with-bleed.pdf`
   instead and ask them to trim to exactly 84 × 42 in.

Nothing important sits within 1 inch of any edge, so a 1/4-inch trim loses only background.

Optional but worth it: ask for a small test strip first (for example a 24 × 12 inch piece at
100%) to check that the beige prints warm on their paper.

Backup vendor: Bay Photo Lab prints up to 48 × 96 inches (including deep matte paper), so the
bleed file fits with room to trim. The map is exactly 2:1, so a 96 × 48 inch print also works;
the scale bars stay correct at any size (the "1:42,000" statement applies only at 84 × 42).

## What is on the map

- all 13 refuge units outlined and labeled; land owned by USFWS (fee title) shown darker than
  easement or cooperatively managed land; the refuge's approved acquisition boundary
- the Round Lake Unit (Arden Hills) in its own inset
- both refuge visitor centers, trailheads and parking, boat launches, and refuge trails
- the Minnesota River from the Mississippi confluence (Bdote) past Henderson, with lakes,
  marshes and named creeks
- terrain shading from USGS elevation data, and a soft tint on the valley floor (land up to
  about 30 ft above the river, computed from the elevation data)
- Fort Snelling State Park, the Minnesota Valley State Recreation Area, Scientific and Natural
  Areas, Wildlife Management Areas, regional and county parks, and tribal land
- cities and towns, counties, interstates and highways with route markers, county and local
  roads, railroads, airports, and the state and regional trails
- landmarks such as Historic Fort Snelling, Pike Island, Sibley Historic Site, Oheyawahi
  (Pilot Knob), Mall of America, the airports and the Minnesota Landscape Arboretum
- title, introduction, unit acreage table, visitor information, legend, Minnesota locator,
  scale bars, north arrow, a 1976–2026 timeline, and data credits

## Data sources

| Theme | Source |
|---|---|
| Refuge units, land status, approved boundary, trails, facilities | U.S. Fish and Wildlife Service: FWS Cadastral data (approved boundaries and realty interests), refuge facility and trail layers, 2025–26 hunt units, and the refuge StoryMap unit layer supplied by the user |
| Elevation | U.S. Geological Survey, 3D Elevation Program, 1/3 arc-second seamless DEM |
| Rivers, lakes, streams, wetlands | USGS National Hydrography Dataset (High Resolution); Minnesota DNR Hydrography; Census TIGER/Line area water |
| Roads, rail, boundaries, cities, tribal land | U.S. Census Bureau, TIGER/Line Shapefiles 2025; 2025 cartographic boundary files |
| City population (label size) | U.S. Census Bureau, Vintage 2025 population estimates |
| State parks, SNAs, WMAs, state trails | Minnesota DNR via the Minnesota Geospatial Commons |
| Regional parks and trails, airport boundaries | Metropolitan Council |
| Airports and runways | Minnesota Department of Transportation |
| Landmark coordinates | Metropolitan Council address points, FAA airport reference points, USGS GNIS |
| Refuge facts and timeline | fws.gov/refuge/minnesota-valley (About Us, Visit Us, home page) |
| Dakota place names | Minnesota Historical Society (Historic Fort Snelling "Bdote" page; MNopedia) and National Park Service |

Note on unit land status: the refuge unit polygons come from the user's StoryMap layer, with
their fee / easement / agreement status corrected against the current FWS realty layer and
FWS hunt units (for example, the Jessenland and Blakeley units are agreement land, not fee
title). Total shown: 15,135 acres (sum of the rounded unit figures), consistent with FWS's "more than 15,000 acres."

This is not an official U.S. Fish and Wildlife Service publication. Boundaries are approximate.

## Rebuilding

The code is in `src/`. Python 3.11 with geopandas, shapely, pyproj, pyogrio, rasterio, numpy,
scipy, matplotlib, pillow, fonttools and pikepdf; `pdftoppm` (poppler) for previews.

```
cd src
python build_map.py --ppi 40                      # quick preview (written to the work folder)
python build_map.py --ppi 200 --out ../output/MVNWR_wall_map_84x42in_with-bleed.pdf
python make_variants.py ../output/MVNWR_wall_map_84x42in_with-bleed.pdf
```

`make_variants.py` writes the trim-size copy and the preview next to the input; rename them to
the names in the table above. `MVNWR_DATA` points at the downloaded data folder and
`MVNWR_FONTS` at the fonts (EB Garamond and Source Sans 3, SIL Open Font License, static
instances). Hand-set label positions are in `src/label_table.py`; panel layout and text are in
`src/panels.py`; colors in `src/style.py`.

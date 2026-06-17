# STAC Catalog — Belvedere Glacier Monitoring Dataset

This document explains what the STAC catalog is, how it is structured for this dataset, how to regenerate it, how to publish it, and how end users can consume it.

---

## What is STAC?

**STAC** (SpatioTemporal Asset Catalog) is an open standard for describing geospatial datasets in a way that is discoverable, filterable, and interoperable across tools. It organises data into three nested levels:

```
Catalog          ← single entry point (catalog.json)
 └── Collection  ← a coherent set of items sharing a common theme
      └── Item   ← one atomic observation (here: one survey epoch)
           └── Assets  ← the actual files (DSM, orthophoto, point cloud)
```

Each **Item** is a GeoJSON Feature, meaning any GIS tool that reads GeoJSON can parse it. It carries:

| Field | Content |
|---|---|
| `geometry` / `bbox` | Spatial footprint in WGS84 |
| `properties.datetime` | Survey date — enables temporal filtering |
| `properties.*` | Any metadata: platform, RMSE, camera, CRS… |
| `assets` | Named references to the data files, with URL, media type, and roles |

Because STAC is a plain JSON standard, no server is required. A folder of JSON files on disk (or on any static file host) is a fully valid catalog.

---

## Catalog structure for this dataset

```
stac_catalog/
├── catalog.json                          ← root entry point
└── belvedere-monitoring/
     ├── collection.json                  ← collection metadata + full extent
     ├── belv_1977_histo-aerial/
     │    └── belv_1977_histo-aerial.json ← Item: 1977 historical aerial survey
     ├── belv_1991_histo-aerial/
     │    └── belv_1991_histo-aerial.json
     ├── ...
     └── belv_2024_uav/
          └── belv_2024_uav.json          ← Item: 2024 UAV survey
```

Each item JSON contains three assets:

| Asset key | File type | Content |
|---|---|---|
| `dsm` | COG GeoTIFF | Digital Surface Model (elevation, orthometric) |
| `orthophoto` | COG GeoTIFF | True-colour orthorectified image |
| `pointcloud` | COPC LAZ | Dense 3-D point cloud with RGB colours |

For the 2020 survey (split into lower/upper due to field conditions) two orthophoto assets are present: `orthophoto` and `orthophoto_2`.

The asset `href` values point directly to the Zenodo file download URLs, so users never need to parse the catalog structure to find where to download a file.

---

## Why Cloud-Optimized formats matter

The dataset uses **COG** (Cloud-Optimized GeoTIFF) for rasters and **COPC** (Cloud-Optimized Point Cloud) for point clouds. Both formats store an internal spatial index that allows HTTP servers to serve arbitrary byte ranges. This means:

- A user can open a DSM at any zoom level or bounding box **without downloading the full file** — the client fetches only the bytes it needs.
- Visualisation tools (QGIS, web viewers) load overviews instantly.
- Python code using `rasterio` streams data on demand from the Zenodo URL.

---

## How to build (or rebuild) the catalog

### Requirements

```
pixi install   # installs pystac, pyproj, shapely — see pyproject.toml
```

### Run

```bash
pixi run python stac_build_catalog.py
```

This script:
1. Reads every `open-data/*_meta.json` file.
2. Reprojects the orthophoto footprint from EPSG:7791 → WGS84.
3. Creates a STAC Item with all survey properties.
4. Attaches the DSM, orthophoto, and point cloud as assets with Zenodo URLs.
5. Writes the full catalog tree to `stac_catalog/`.

Re-run this script whenever you add a new survey year or update metadata.

> **Important:** The `ZENODO_FILES_URL` and `CATALOG_BASE_URL` constants at the top of `stac_build_catalog.py` must match the Zenodo record ID and the GitHub Pages URL. Update them before publishing a new record version.

---

## How to publish the catalog

### Option A — Zenodo only (simplest)

Upload the entire `stac_catalog/` folder to the Zenodo record alongside the data files. Users can then open the catalog by URL:

```
https://zenodo.org/records/<RECORD_ID>/files/catalog.json
```

No extra hosting is needed. The relative links between item JSONs work correctly as long as Zenodo preserves the folder structure (which it does when you upload a ZIP of the catalog folder or individual files maintaining paths).

### Option B — GitHub Pages (deployed for this dataset)

The `stac_catalog/` folder is deployed automatically via GitHub Actions on every push to `main`. The catalog is live at:

```
https://franioli.github.io/belvedere-open-data/catalog.json
```

The workflow (`.github/workflows/deploy-stac.yml`) deploys only the contents of `stac_catalog/` — not the whole repository. This URL is registered with [STAC Index](https://stacindex.org/) for community discovery.

### Option C — STAC API server (for large/growing catalogs)

For datasets with hundreds of items or that need server-side spatial/temporal filtering, deploy a STAC API such as [stac-fastapi](https://github.com/stac-utils/stac-fastapi) or [pygeoapi](https://pygeoapi.io/). This is not needed for the current dataset size.

---

## How to use the catalog

### Python — pystac + rasterio

Install once:
```bash
pip install pystac rasterio
# or: pixi install  (already in the environment)
```

#### Open the catalog
```python
import pystac

# Remote catalog — GitHub Pages (recommended)
catalog = pystac.Catalog.from_file(
    "https://franioli.github.io/belvedere-open-data/catalog.json"
)

# Local catalog (after running stac_build_catalog.py)
catalog = pystac.Catalog.from_file("./stac_catalog/catalog.json")
```

#### List all surveys
```python
collection = catalog.get_child("belvedere-monitoring")
items = sorted(collection.get_items(), key=lambda i: i.datetime)

for item in items:
    print(item.id, item.datetime.year, item.properties.get("platform"))
```

#### Filter by year, platform, or accuracy
```python
# UAV surveys only
uav = [i for i in items if i.properties["platform"] == "uav"]

# Surveys from 2019 onward
recent = [i for i in items if i.datetime.year >= 2019]

# High-accuracy surveys (RMSE < 0.15 m)
accurate = [
    i for i in items
    if isinstance(i.properties.get("rmse_global_m"), float)
    and i.properties["rmse_global_m"] < 0.15
]
```

#### Stream a DSM from Zenodo (no full download)
```python
import rasterio
import numpy as np

item = collection.get_item("belv_2022_uav")
dsm_url = item.assets["dsm"].href

with rasterio.open(dsm_url) as src:
    # Read a coarse overview for a quick plot (fetches ~1 MB instead of ~270 MB)
    data = src.read(1, out_shape=(src.height // 16, src.width // 16))
```

#### Download a file when you need the full resolution
```python
import urllib.request
from pathlib import Path

asset = item.assets["pointcloud"]
dest = Path(Path(asset.href).name)
urllib.request.urlretrieve(asset.href, dest)
```

A complete worked example with visualisations and a DSM-of-Difference workflow is in [usage_example.ipynb](usage_example.ipynb).

---

### QGIS

1. Install the **STAC Browser** plugin from the QGIS Plugin Manager.
2. Add a new connection and paste the catalog URL.
3. Browse the collection, filter by date, and load any COG layer directly into the canvas — no download required.

---

### Command line (stac-client)

```bash
pip install pystac-client

# List all items
stac-client items ./stac_catalog/catalog.json belvedere-monitoring

# Filter by date range
stac-client search ./stac_catalog/catalog.json \
    --collections belvedere-monitoring \
    --datetime 2019-01-01/2024-12-31
```

---

## Metadata fields reference

Each STAC Item carries the following properties extracted from the `*_meta.json` files:

| Property | Type | Description |
|---|---|---|
| `datetime` | ISO 8601 | Survey date |
| `year` | int | Survey year |
| `platform` | string | `uav`, `histo-aerial`, or `digital-aerial` |
| `original_crs` | string | Native CRS of the data (e.g. `EPSG:7791`) |
| `rmse_global_m` | float | Global RMSE of the photogrammetric block (m) |
| `drone_model` | string | UAV platform name |
| `camera_model` | string | Camera name(s) |
| `point_density_pt_m2` | float | Average point cloud density (pts/m²) |

---

## Citation

If you use this dataset, please cite:

- **Open data description**: Gaspari et al. (2025). *Strategies for Glacier Retreat Communication with 3D Geovisualization and Open Data Sharing*. ISPRS IJGI, 14(2), 75. https://doi.org/10.3390/ijgi14020075
- **UAV datasets**: Ioli et al. (2022). *Mid-Term Monitoring of Glacier's Variations with UAVs*. Remote Sensing, 14, 28. https://doi.org/10.3390/rs14010028
- **Historical aerial datasets**: De Gaetani et al. (2021). *Aerial and UAV Images for Photogrammetric Analysis of Belvedere Glacier Evolution 1977–2019*. Remote Sensing, 13, 3787. https://doi.org/10.3390/rs13183787

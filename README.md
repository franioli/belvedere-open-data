# Belvedere Glacier — Long-Term Monitoring Open Dataset

Scripts and catalog for the Belvedere Glacier open dataset published on Zenodo.  
The dataset covers photogrammetric surveys of the glacier from **1977 to present**, acquired with historical aerial platforms, digital aerial cameras, and UAVs.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7842347.svg)](https://doi.org/10.5281/zenodo.7842347)

---

## Repository structure

```
belvedere_zenodo/
│
├── open-data/                  Final files published on Zenodo (not tracked by git)
│   ├── belv_YYYY_*_meta.json   Survey metadata (CRS, accuracy, sensor info)
│   ├── belv_YYYY_*_dsm_*_cog.tif        DSM — Cloud-Optimized GeoTIFF
│   ├── belv_YYYY_*_orthophoto_*_cog.tif  Orthophoto — Cloud-Optimized GeoTIFF
│   └── belv_YYYY_*_pcd_copc.laz          Point cloud — COPC LAZ
│
├── proc/                       Processing intermediates (not tracked by git)
│   ├── YYYY/                   Per-year workspace (raw exports, intermediate files)
│   ├── dod/                    DSM-of-Difference outputs
│   ├── ITALGEO05_E00_32632_0.2m_clipped.tif   Geoid undulation grid (EPSG:32632)
│   └── masks_all_years.geojson Study-area mask with one polygon per survey year
│
├── scripts/                    Data preparation utilities
│   ├── convert_to_cog.sh           Single GeoTIFF → COG
│   ├── convert_to_cog_batch.sh     Batch GeoTIFF → COG
│   ├── convert_to_copc.sh          Single point cloud → COPC LAZ
│   ├── convert_to_copc_batch.sh    Batch point cloud → COPC LAZ
│   ├── apply_geoid_correction.sh   Ellipsoidal → orthometric heights (ITALGEO05)
│   ├── apply_geoid_correction.py   Python version of the geoid correction
│   ├── compute_dem_of_difference_gdal.sh   DSM subtraction with GDAL
│   └── generate_dsm_previews.py    Quick PNG previews of all DSMs
│
├── stac_catalog/               STAC catalog (generated, committed for GitHub Pages)
│   ├── catalog.json
│   └── belvedere-monitoring/
│       ├── collection.json
│       └── belv_YYYY_*/belv_YYYY_*.json   One item JSON per survey epoch
│
├── stac_build_catalog.py       Script to regenerate the STAC catalog from open-data/
├── stac_usage_example.ipynb    End-user notebook: load, filter, and analyse the data
│
├── DATA_PREPARATION.md         Step-by-step guide for adding a new survey year
├── README_stac.md              How the STAC catalog works and how to use it
├── README_zenodo.md            Dataset description published on the Zenodo record
└── pyproject.toml              Python environment (managed with pixi)
```

---

## Quick start for data users

The easiest way to explore the dataset is through the STAC catalog. Open [`stac_usage_example.ipynb`](stac_usage_example.ipynb) in Jupyter or read [`README_stac.md`](README_stac.md) for a full explanation.

**One-liner to stream a DSM without downloading the full file:**

```python
import pystac, rasterio

catalog = pystac.Catalog.from_file("stac_catalog/catalog.json")
item = catalog.get_child("belvedere-monitoring").get_item("belv_2022_uav")
with rasterio.open(item.assets["dsm"].href) as src:
    data = src.read(1, out_shape=(src.height // 8, src.width // 8))
```

---

## Adding a new survey year

See [`DATA_PREPARATION.md`](DATA_PREPARATION.md) for the full step-by-step procedure.

The short version:

```bash
# 1. Copy and edit metadata
cp open-data/belv_2024_uav_meta.json open-data/belv_YYYY_uav_meta.json

# 2. Process orthophoto, DSM, and point cloud into open-data/
#    (see DATA_PREPARATION.md for the full commands)

# 3. Regenerate the STAC catalog
pixi run python stac_build_catalog.py
```

---

## Environment

The Python environment is managed with [pixi](https://pixi.sh). To install all dependencies:

```bash
pixi install
pixi run jupyter lab   # open the usage notebook
```

Key packages: `pystac`, `rasterio`, `xdem`, `geoutils`, `gdal`, `pdal`.

---

## Citation

If you use this dataset, please cite:

- **Open data description**: Gaspari et al. (2025). *Strategies for Glacier Retreat Communication with 3D Geovisualization and Open Data Sharing*. ISPRS IJGI, 14(2), 75. https://doi.org/10.3390/ijgi14020075
- **UAV datasets**: Ioli et al. (2022). *Mid-Term Monitoring of Glacier's Variations with UAVs: The Example of the Belvedere Glacier*. Remote Sensing, 14, 28. https://doi.org/10.3390/rs14010028
- **Historical aerial datasets**: De Gaetani et al. (2021). *Aerial and UAV Images for Photogrammetric Analysis of Belvedere Glacier Evolution in the Period 1977–2019*. Remote Sensing, 13, 3787. https://doi.org/10.3390/rs13183787

---

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
Scripts: [MIT](https://opensource.org/licenses/MIT)

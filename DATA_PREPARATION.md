# Belvedere Dataset — Yearly Preparation Procedure

Internal reference for preparing the final data for each survey year before upload to Zenodo.

**Tools required:** GDAL ≥ 3.1, PDAL ≥ 2.6, CloudCompare (or equivalent) for point cloud cleaning.  
All shell scripts are in `scripts/` and must be executable (`chmod +x scripts/*.sh`).

---

## Naming Convention

All files follow the schema defined in `readme_v3.1.md`:

```
belv_YYYY_<platform>_<datatype>[_<resolution>][_<vdatum>][_<other>].<ext>
```

| Token | Values |
|---|---|
| `YYYY` | Survey year, e.g. `2024` |
| `platform` | `uav`, `histo-aerial`, `digital-aerial` |
| `datatype` | `orthophoto`, `dsm`, `pcd`, `meta` |
| `resolution` | `20cm`, `40cm`, `50cm` (rasters only) |
| `vdatum` | `ortho` when heights are orthometric (DSM only) |
| `other` | `cog` for COG rasters, `copc` for point clouds |

**Final file names for a standard UAV year:**

| File | Name |
|---|---|
| Metadata | `belv_YYYY_uav_meta.json` |
| Orthophoto | `belv_YYYY_uav_orthophoto_20cm_cog.tif` |
| DSM | `belv_YYYY_uav_dsm_20cm_ortho_cog.tif` |
| Point cloud | `belv_YYYY_uav_pcd_copc.laz` |


Intermediate files generated during processing (e.g. resampled but not yet geoid-corrected DSM) are stored in `proc/<YYYY>/` and can be deleted after verifying the final outputs.

**All finalized files are placed in `open-data/`.**

---

## Set Year Variables

Set these at the start of every session to keep commands copy-pasteable:

```bash
YYYY=2024
PLATFORM=uav      # uav | histo-aerial | digital-aerial
RES=20cm          # resolution label used in the filename
RES_M=0.2         # resolution in metres for gdalwarp
EPSG=7791         # RDN2008 / UTM zone 32N

GEOID="proc/ITALGEO05_E00_32632_0.2m_clipped.tif"
MASK="proc/masks_all_years.geojson"
```

---

## Step 1 — Metadata JSON

Copy the JSON from the most recent completed year and update every field.

```bash
cp open-data/belv_2023_uav_meta.json open-data/belv_${YYYY}_${PLATFORM}_meta.json
```

Fields that must be updated for the new year:

- `year`, `survey.date`
- `survey.drone`, `survey.camera`, `survey.flight` — drone model, GSD, flight height
- `survey.photogrammetric_block` — image count, GCP/checkpoint counts, RMSE
- `data.pcd.file_name`, `data.pcd.points`, `data.pcd.average_point_density_pt/m2`, `data.pcd.average_point_spacing_m`, `data.pcd.bounding_box`
- `data.orthophoto.file_name`, `data.orthophoto.file_size__MB`, `data.orthophoto.width_px`, `data.orthophoto.heigth_px`, `data.orthophoto.extent`
- `data.dsm.file_name`, `data.dsm.file_size__MB`, `data.dsm.width_px`, `data.dsm.heigth_px`, `data.dsm.extent`
- `contributors` — add or remove contributors for the specific year
- `notes`, `related_pubblications`, `Acknowledgments`

Leave `bounding_box` and raster `extent` for last — fill these in once the processed files exist (`gdalinfo` is the quickest way).

---

## Step 2 — Orthophoto

### 2a. Resample, reproject, and clip

The raw photogrammetric orthophoto (typically exported from Agisoft Metashape in EPSG:32632 at the native GSD) is resampled to 20 cm, reprojected to EPSG:7791, and clipped to the study-area mask for the relevant year.

```bash
gdalwarp \
  -t_srs EPSG:${EPSG} \
  -tr ${RES_M} ${RES_M} \
  -r bilinear \
  -cutline ${MASK} \
  -cwhere "survey = '${YYYY}'" \
  -crop_to_cutline \
  -dstalpha \
  -overwrite \
  input_orthophoto_raw.tif \
  proc/${YYYY}/belv_${YYYY}_${PLATFORM}_orthophoto_${RES}.tif
```

> `-dstalpha` adds an alpha band so areas outside the mask are transparent rather than black, consistent with all other years.
> `-r bilinear` is appropriate for the RGB imagery; use `near` only if resampling at exactly the native GSD.

### 2b. Convert to COG

```bash
scripts/convert_to_cog.sh \
  -o open-data/belv_${YYYY}_${PLATFORM}_orthophoto_${RES}_cog.tif \
  proc/${YYYY}/belv_${YYYY}_${PLATFORM}_orthophoto_${RES}.tif
```

The script auto-detects `PREDICTOR=2` (horizontal, appropriate for 8-bit RGB). The intermediate file can be deleted after verifying the COG.

For batch conversion of multiple orthophotos at once:

```bash
scripts/convert_to_cog_batch.sh -s proc/${YYYY} -d open-data -g "belv_*_orthophoto_*.tif"
```

---

## Step 3 — DSM

### 3a. Resample, reproject, and clip

Same spatial processing as the orthophoto. The raw DSM is in ellipsoidal heights at this stage — do **not** apply the geoid correction yet.

```bash
gdalwarp \
  -t_srs EPSG:${EPSG} \
  -tr ${RES_M} ${RES_M} \
  -r bilinear \
  -cutline ${MASK} \
  -cwhere "survey = '${YYYY}'" \
  -crop_to_cutline \
  -dstnodata -9999 \
  -overwrite \
  input_dsm_raw.tif \
  proc/${YYYY}/belv_${YYYY}_${PLATFORM}_dsm_${RES}.tif
```

### 3b. Apply geoid undulation (ellipsoidal → orthometric)

Convert from ellipsoidal heights *h* to orthometric heights *H* using the ITALGEO05 undulation grid:

```
H = h - N
```

```bash
scripts/apply_geoid_correction.sh \
  -s sub \
  -o proc/${YYYY}/belv_${YYYY}_${PLATFORM}_dsm_${RES}_ortho.tif \
  proc/${YYYY}/belv_${YYYY}_${PLATFORM}_dsm_${RES}.tif \
  ${GEOID}
```

The script reprojects the geoid grid onto the DSM grid automatically. The intermediate ellipsoidal DSM (`proc/${YYYY}/belv_YYYY_..._dsm_20cm.tif`) can be kept for reference or discarded.

> The geoid file `ITALGEO05_E00_32632_0.2m_clipped.tif` is in `proc/`. It covers the Belvedere study area and is already at 0.2 m resolution in EPSG:32632.

### 3c. Convert to COG

```bash
scripts/convert_to_cog.sh \
  -o open-data/belv_${YYYY}_${PLATFORM}_dsm_${RES}_ortho_cog.tif \
  proc/${YYYY}/belv_${YYYY}_${PLATFORM}_dsm_${RES}_ortho.tif
```

The script auto-detects `PREDICTOR=3` (floating-point, appropriate for Float32 elevation data).

---

## Step 4 — Point Cloud

### 4a. Clean and restrict to the area of interest

Open the raw dense point cloud (exported from Agisoft Metashape) in **CloudCompare**:

1. Remove outliers: e.g., `Edit → Clean → SOR filter`.
2. Crop to the study area: `Edit → Segment` using the study-area boundary, or apply a bounding-box crop to remove photogrammetric extrapolation artefacts at the margins.
3. Ensure the point cloud is in EPSG:7791. If exported in EPSG:32632, reproject with PDAL:

```bash
pdal translate \
  input_pcd.las \
  belv_${YYYY}_${PLATFORM}_pcd.laz \
  --filters.reprojection.in_srs="EPSG:32632" \
  --filters.reprojection.out_srs="EPSG:7791"
```

Alternatively, cleaning and cropping can be done fully with PDAL pipelines if a reproducible workflow is needed.

### 4b. Save to LAZ

From CloudCompare: `File → Save as` → select **LAS 1.3 or 1.4 / LAZ** format.  
Name the file `proc/${YYYY}/belv_${YYYY}_${PLATFORM}_pcd.laz`.

Keep RGB colours and the `Confidence` scalar field if present (exported from Metashape dense point cloud confidence levels).

### 4c. Convert to COPC

```bash
scripts/convert_to_copc.sh \
  -o open-data/belv_${YYYY}_${PLATFORM}_pcd_copc.laz \
  proc/${YYYY}/belv_${YYYY}_${PLATFORM}_pcd.laz
```

For batch conversion of multiple point clouds:

```bash
scripts/convert_to_copc_batch.sh -s proc/${YYYY} -d open-data -g "belv_*_pcd.laz"
```

> COPC is fully backward-compatible with LAZ 1.4. The output can be opened in CloudCompare, QGIS, or any LAS reader without modification.

---

## Step 5 — Final Checks

Before uploading:

1. **Naming** — confirm all four files match the convention exactly (no typos, correct platform token).
2. **Spatial consistency** — load orthophoto, DSM, and point cloud together in QGIS and verify they align and cover the same area.
3. **CRS** — run `gdalinfo open-data/belv_${YYYY}_...` and confirm `EPSG:7791` on all rasters.
4. **Nodata** — DSM nodata should be `-9999`; orthophoto areas outside the mask should use the alpha channel.
5. **Heights** — spot-check DSM values at a known benchmark. Orthometric elevations at the glacier tongue should be ~1800–1900 m, at the upper glacier ~2300–2400 m.
6. **COPC validity** — run `pdal info open-data/belv_${YYYY}_${PLATFORM}_pcd_copc.laz` and check `count`, `bounds`, and `srs`.
7. **Update meta.json** — fill in `file_size__MB`, `width_px`, `heigth_px`, `extent`, `bounding_box` from the processed files:
   ```bash
   gdalinfo open-data/belv_${YYYY}_${PLATFORM}_orthophoto_${RES}_cog.tif
   gdalinfo open-data/belv_${YYYY}_${PLATFORM}_dsm_${RES}_ortho_cog.tif
   pdal info open-data/belv_${YYYY}_${PLATFORM}_pcd_copc.laz | python3 -m json.tool
   ```

import glob
import json
import os
from datetime import datetime

import pystac
from pyproj import Transformer
from shapely.geometry import box, mapping

ZENODO_FILES_URL = "https://zenodo.org/records/10817029/files"
DATA_DIR = "./data"


def parse_date(date_str, year):
    """Parses dates like '24-26 Jul 2023' or '15 Aug 2021' into a datetime object."""
    try:
        parts = date_str.split()
        if len(parts) >= 3:
            day = parts[0].split("-")[0]
            clean_date_str = f"{day} {parts[1]} {parts[2]}"
            return datetime.strptime(clean_date_str, "%d %b %Y")
        return datetime(int(year), 8, 1)
    except Exception:
        return datetime(int(year), 8, 1)


def build_catalog():
    catalog = pystac.Catalog(
        id="belvedere-glacier",
        description="Belvedere Glacier long-term monitoring Open Data",
    )

    all_datetimes = []
    meta_files = sorted(glob.glob(f"{DATA_DIR}/*_meta.json"))

    # First pass: collect all survey dates to build a dynamic temporal extent
    for meta_file in meta_files:
        with open(meta_file) as f:
            meta = json.load(f)
        all_datetimes.append(parse_date(meta["survey"]["date"], meta["year"]))

    collection = pystac.Collection(
        id="belvedere-monitoring",
        description="UAV and historical photogrammetric surveys of Belvedere Glacier (1977–2023). "
        "Each item contains a DSM (Cloud-Optimized GeoTIFF), an orthophoto (COG), "
        "and a point cloud (COPC .laz).",
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent(bboxes=[[7.93, 45.87, 7.97, 45.91]]),
            temporal=pystac.TemporalExtent(
                intervals=[[min(all_datetimes), max(all_datetimes)]]
            ),
        ),
        license="CC-BY-4.0",
    )
    catalog.add_child(collection)

    for meta_file in meta_files:
        with open(meta_file) as f:
            meta = json.load(f)

        year = meta["year"]
        # base_prefix is the filename stem shared by all files for this survey
        # e.g. "./data/belv_2022_uav"
        base_prefix = meta_file.replace("_meta.json", "")
        item_id = os.path.basename(base_prefix)  # e.g. "belv_2022_uav"
        platform = item_id.split("_")[2]          # "uav" or "histo-aerial"

        # Reproject orthophoto extent(s) from native CRS to WGS84 (EPSG:4326).
        # orthophoto can be a single dict or a list (e.g. 2020: lower + upper).
        ortho_raw = meta["data"]["orthophoto"]
        orthos = ortho_raw if isinstance(ortho_raw, list) else [ortho_raw]
        epsg_code = orthos[0]["epsg"]
        transformer = Transformer.from_crs(
            f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True
        )
        # Union of all orthophoto extents
        all_min_x = min(o["extent"]["min"][0] for o in orthos)
        all_min_y = min(o["extent"]["min"][1] for o in orthos)
        all_max_x = max(o["extent"]["max"][0] for o in orthos)
        all_max_y = max(o["extent"]["max"][1] for o in orthos)
        min_lon, min_lat = transformer.transform(all_min_x, all_min_y)
        max_lon, max_lat = transformer.transform(all_max_x, all_max_y)

        item_bbox = [min_lon, min_lat, max_lon, max_lat]
        item_geometry = mapping(box(*item_bbox))
        survey_date = parse_date(meta["survey"]["date"], year)

        properties = {
            "year": year,
            "platform": platform,
            "license": meta.get("license", "CC BY 4.0"),
            "original_crs": f"EPSG:{epsg_code}",
        }
        if "drone" in meta["survey"]:
            properties["drone_model"] = meta["survey"]["drone"]["name"]
        if "camera" in meta["survey"]:
            cam = meta["survey"]["camera"]
            if isinstance(cam, list):
                properties["camera_model"] = ", ".join(c["name"] for c in cam)
            else:
                properties["camera_model"] = cam["name"]
        if "photogrammetric_block" in meta["survey"]:
            properties["rmse_global_m"] = meta["survey"]["photogrammetric_block"][
                "on_ground_accuracy"
            ]["rmse_m"]["global"]
        if "pcd" in meta["data"]:
            properties["point_density_pt_m2"] = meta["data"]["pcd"].get(
                "average_point_density_pt/m2"
            )

        item = pystac.Item(
            id=item_id,
            geometry=item_geometry,
            bbox=item_bbox,
            datetime=survey_date,
            properties=properties,
        )

        # Attach all data files for this survey as assets.
        # base_prefix already includes DATA_DIR, so glob directly on it.
        survey_files = sorted(glob.glob(f"{base_prefix}*"))
        asset_counters = {"dsm": 0, "orthophoto": 0, "pcd": 0}
        for filepath in survey_files:
            if filepath.endswith("_meta.json"):
                continue

            filename = os.path.basename(filepath)
            asset_url = f"{ZENODO_FILES_URL}/{filename}"

            if "dsm" in filename:
                asset_counters["dsm"] += 1
                suffix = f"_{asset_counters['dsm']}" if asset_counters["dsm"] > 1 else ""
                item.add_asset(
                    f"dsm{suffix}",
                    pystac.Asset(
                        href=asset_url,
                        title=filename,
                        media_type=pystac.MediaType.COG,
                        roles=["data", "elevation"],
                    ),
                )
            elif "orthophoto" in filename:
                asset_counters["orthophoto"] += 1
                suffix = f"_{asset_counters['orthophoto']}" if asset_counters["orthophoto"] > 1 else ""
                item.add_asset(
                    f"orthophoto{suffix}",
                    pystac.Asset(
                        href=asset_url,
                        title=filename,
                        media_type=pystac.MediaType.COG,
                        roles=["data", "visual"],
                    ),
                )
            elif "pcd" in filename:
                item.add_asset(
                    "pointcloud",
                    pystac.Asset(
                        href=asset_url,
                        title=filename,
                        media_type="application/vnd.laszip+copc",
                        roles=["data", "pointcloud"],
                    ),
                )

        collection.add_item(item)

    catalog.normalize_hrefs("./stac_catalog")
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print(f"STAC catalog saved to ./stac_catalog/ ({len(meta_files)} items)")


if __name__ == "__main__":
    build_catalog()

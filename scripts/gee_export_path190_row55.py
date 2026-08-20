"""
GEE Export Script — Second Landsat Scene for Lagos Coverage
=============================================================

Run this in the GEE Code Editor (https://code.earthengine.google.com/).

This exports Landsat 9 Surface Reflectance + Surface Temperature for
Path 190, Row 55 — the scene that overlaps the western gap of the
Lagos State boundary.

After export finishes (~15-30 min), download the 7 COG files from
Google Drive into:
    data/raw/imagery/LC09_190055_YYYYMMDD/
"""

# ---------- CONFIGURATION ----------

# Lagos State boundary (WGS84) with a 30 km buffer to guarantee overlap.
LAGOS_BUFFERED = ee.Geometry.Polygon([[
    [2.40, 6.10],   # SW corner (buffered ~30 km west/south of boundary)
    [4.65, 6.10],   # SE corner
    [4.65, 6.95],   # NE corner
    [2.40, 6.95],   # NW corner
]])

WRS_PATH = 190
WRS_ROW = 55

# Date range — match the dry-season scene (Dec 2022) for consistency.
# Also check wet-season (Oct 2023) as fallback.
DATE_RANGES = [
    ("2022-11-01", "2023-01-31", "dry"),
    ("2023-09-01", "2023-11-30", "wet"),
]

MAX_CLOUD_PCT = 20  # percent

# Band mapping for Landsat 9 Collection 2 Level 2.
SR_BANDS = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
ST_BAND = "ST_B10"
QA_BAND = "QA_PIXEL"
ALL_BANDS = SR_BANDS + [ST_BAND, QA_BAND]

DRIVE_FOLDER = "urban_heat_intelligence"

# ---------- HELPER FUNCTIONS ----------

def mask_clouds(img):
    """Apply cloud/shadow/fill mask using QA_PIXEL bit flags."""
    qa = img.select(QA_PIXEL)
    # Bit 0: Fill, Bit 1: Dilated cloud, Bit 2: Cirrus,
    # Bit 3: Cloud, Bit 4: Cloud shadow
    mask_bits = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4)
    return img.updateMask(qa.bitwiseAnd(mask_bits).eq(0))


def find_best_scene(date_start, date_end, season_label):
    """Find the least cloudy scene for the given path/row and date range."""
    collection = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(LAGOS_BUFFERED)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.eq("WRS_PATH", WRS_PATH))
        .filter(ee.Filter.eq("WRS_ROW", WRS_ROW))
    )

    count = collection.size().getInfo()
    print(f"[{season_label}] Found {count} scenes for Path {WRS_PATH}/Row {WRS_ROW} "
          f"({date_start} to {date_end})")

    if count == 0:
        return None

    # Sort by cloud cover and pick the least cloudy.
    collection = collection.sort("CLOUD_COVER")
    best = ee.Image(collection.first())

    # Get metadata.
    info = best.getInfo()
    props = info["properties"]
    scene_id = props.get("LANDSAT_SCENE_ID", "unknown")
    cloud_pct = props.get("CLOUD_COVER", -1)
    date_acquired = props.get("DATE_ACQUIRED", "unknown")

    print(f"  Best scene: {scene_id}")
    print(f"  Date: {date_acquired}")
    print(f"  Cloud cover: {cloud_pct}%")

    return best, scene_id, date_acquired, cloud_pct


def export_scene(image, scene_id, date_acquired, cloud_pct, season_label):
    """Export a single scene as COGs to Google Drive."""
    # Apply cloud mask.
    masked = mask_clouds(image)

    # Select the bands we need.
    selected = masked.select(ALL_BANDS)

    # Clip to buffered extent.
    clipped = selected.clip(LAGOS_BUFFERED)

    # Export parameters.
    description = f"LC09_{WRS_PATH:03d}{WRS_ROW:03d}_{date_acquired.replace('-', '')}"

    task = ee.batch.Export.image.toDrive(
        image=clipped,
        description=description,
        folder=DRIVE_FOLDER,
        fileNamePrefix=description,
        region=LAGOS_BUFFERED,
        scale=30,
        crs="EPSG:32631",
        maxPixels=1e10,
        fileFormat="GeoTIFF",
        formatOptions={"cloudOptimized": True},
    )

    task.start()
    print(f"\n[{season_label}] Export started: {description}")
    print(f"  Task ID: {task.id}")
    print(f"  Scene ID: {scene_id}")
    print(f"  Date: {date_acquired}")
    print(f"  Cloud cover: {cloud_pct}%")
    print(f"  Output: Drive/{DRIVE_FOLDER}/{description}/*.tif")
    print(f"\n  Monitor at: https://code.earthengine.google.com/tasks")

    return task


# ---------- MAIN ----------

print("=" * 60)
print("LANDSAT 9 EXPORT — Path 190 / Row 55")
print("Purpose: fill the western gap of Lagos State boundary")
print("=" * 60)

# Try dry season first, then wet season.
for date_start, date_end, season in DATE_RANGES:
    result = find_best_scene(date_start, date_end, season)
    if result is not None:
        image, scene_id, date_acquired, cloud_pct = result
        task = export_scene(image, scene_id, date_acquired, cloud_pct, season)
        break
    print(f"  No scenes found for {season} season, trying next range...")
else:
    print("\nWARNING: No suitable scenes found for any date range!")
    print("Try adjusting DATE_RANGES in the script.")

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("1. Wait for export to finish (~15-30 min)")
print("2. Monitor at https://code.earthengine.google.com/tasks")
print("3. Download from Google Drive/urban_heat_intelligence/")
print(f"4. Place files in: data/raw/imagery/LC09_{WRS_PATH:03d}{WRS_ROW:03d}_YYYYMMDD/")
print("5. Tell me when ready — I'll mosaic the two scenes")
print("=" * 60)

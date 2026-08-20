/*
 * GEE Export Script — Second Landsat Scene for Lagos Coverage
 * ============================================================
 *
 * Paste this into https://code.earthengine.google.com/ and click Run.
 *
 * Exports Landsat 9 Surface Reflectance + Surface Temperature for
 * Path 190, Row 55 — the scene that overlaps the western gap of the
 * Lagos State boundary.
 *
 * After export finishes (~15-30 min), download the 7 COG files from
 * Google Drive folder "urban_heat_intelligence" into:
 *     data/raw/imagery/LC09_190055_YYYYMMDD/
 */

// ---------- CONFIGURATION ----------

// Lagos State boundary (WGS84) with a 30 km buffer to guarantee overlap.
var LAGOS_BUFFERED = ee.Geometry.Polygon([[
  [2.40, 6.10],   // SW corner (buffered ~30 km west/south)
  [4.65, 6.10],   // SE corner
  [4.65, 6.95],   // NE corner
  [2.40, 6.95],   // NW corner
]]);

var WRS_PATH = 190;
var WRS_ROW = 55;

var MAX_CLOUD_PCT = 20;

// Band mapping for Landsat 9 Collection 2 Level 2.
var SR_BANDS = ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'];
var ST_BAND = 'ST_B10';
var QA_BAND = 'QA_PIXEL';
var ALL_BANDS = SR_BANDS.concat([ST_BAND, QA_BAND]);

var DRIVE_FOLDER = 'urban_heat_intelligence';

// ---------- HELPER FUNCTIONS ----------

function maskClouds(img) {
  var qa = img.select(QA_BAND);
  // Bit 0: Fill, Bit 1: Dilated cloud, Bit 2: Cirrus,
  // Bit 3: Cloud, Bit 4: Cloud shadow
  var maskBits = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4);
  return img.updateMask(qa.bitwiseAnd(maskBits).eq(0));
}

// ---------- FIND BEST SCENE ----------

// Try dry season first (Nov 2022 – Jan 2023), then wet season.
var dateRanges = [
  {start: '2022-11-01', end: '2023-01-31', label: 'dry'},
  {start: '2023-09-01', end: '2023-11-30', label: 'wet'}
];

var bestImage = null;
var bestInfo = null;

for (var i = 0; i < dateRanges.length; i++) {
  var dr = dateRanges[i];
  print('Searching ' + dr.label + ' season (' + dr.start + ' to ' + dr.end + ')...');

  var collection = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
    .filterBounds(LAGOS_BUFFERED)
    .filterDate(dr.start, dr.end)
    .filter(ee.Filter.eq('WRS_PATH', WRS_PATH))
    .filter(ee.Filter.eq('WRS_ROW', WRS_ROW))
    .filter(ee.Filter.lt('CLOUD_COVER', MAX_CLOUD_PCT));

  var count = collection.size();
  print('  Found ' + count.getInfo() + ' scenes');

  if (count.getInfo() > 0) {
    // Sort by cloud cover, pick the least cloudy.
    collection = collection.sort('CLOUD_COVER');
    bestImage = ee.Image(collection.first());
    bestInfo = bestImage.getInfo().properties;
    print('  Best scene: ' + bestInfo.LANDSAT_SCENE_ID);
    print('  Date: ' + bestInfo.DATE_ACQUIRED);
    print('  Cloud cover: ' + bestInfo.CLOUD_COVER + '%');
    break;
  }
  print('  No scenes found, trying next range...');
}

if (bestImage === null) {
  print('WARNING: No suitable scenes found! Try adjusting date ranges.');
} else {

  // ---------- APPLY MASK AND EXPORT ----------

  var masked = maskClouds(bestImage);
  var selected = masked.select(ALL_BANDS);
  var clipped = selected.clip(LAGOS_BUFFERED);

  var dateStr = bestInfo.DATE_ACQUIRED.replace(/-/g, '');
  var description = 'LC09_' +
    ('000' + WRS_PATH).slice(-3) +
    ('000' + WRS_ROW).slice(-3) +
    '_' + dateStr;

  print('');
  print('=== EXPORT ===');
  print('Description: ' + description);
  print('Scene ID: ' + bestInfo.LANDSAT_SCENE_ID);
  print('Date: ' + bestInfo.DATE_ACQUIRED);
  print('Cloud: ' + bestInfo.CLOUD_COVER + '%');
  print('Path/Row: ' + WRS_PATH + '/' + WRS_ROW);
  print('CRS: EPSG:32631, Scale: 30m');

  // Visualize to confirm coverage.
  Map.centerObject(LAGOS_BUFFERED, 9);
  Map.addLayer(clipped.select(['SR_B4', 'SR_B3', 'SR_B2']),
    {min: 7000, max: 12000}, 'RGB preview');
  Map.addLayer(LAGOS_BUFFERED, {color: 'yellow'}, 'Lagos buffer');

  // Run export.
  var task = ee.batch.Export.image.toDrive({
    image: clipped,
    description: description,
    folder: DRIVE_FOLDER,
    fileNamePrefix: description,
    region: LAGOS_BUFFERED,
    scale: 30,
    crs: 'EPSG:32631',
    maxPixels: 1e10,
    fileFormat: 'GeoTIFF',
    formatOptions: {cloudOptimized: true}
  });

  task.start();
  print('');
  print('Export started!');
  print('Monitor at: https://code.earthengine.google.com/tasks');
  print('');
  print('NEXT STEPS:');
  print('1. Wait for export to finish (~15-30 min)');
  print('2. Download from Google Drive/urban_heat_intelligence/');
  print('3. Place files in: data/raw/imagery/' + description + '/');
  print('4. Tell me when ready — I will mosaic the two scenes');
}

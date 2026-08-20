/*
 * GEE Scene Finder — Find available Landsat scenes covering Lagos
 * ================================================================
 *
 * Paste this into https://code.earthengine.google.com/ and click Run.
 * It searches ALL available Landsat 8 + 9 scenes that cover Lagos
 * and breaks them down by path/row so we know what's available.
 */

// Lagos buffered bounding box.
var LAGOS_BUFFERED = ee.Geometry.Polygon([[
  [2.40, 6.10],
  [4.65, 6.10],
  [4.65, 6.95],
  [2.40, 6.95],
]]);

var DATE_START = '2022-06-01';
var DATE_END = '2024-01-31';
var MAX_CLOUD = 40;

print('========================================');
print('  LANDSAT SCENE SEARCH FOR LAGOS');
print('========================================');
print('Date range: ' + DATE_START + ' to ' + DATE_END);
print('Max cloud: ' + MAX_CLOUD + '%');
print('');

// Collect all scenes.
var lc09 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
  .filterBounds(LAGOS_BUFFERED)
  .filterDate(DATE_START, DATE_END)
  .filter(ee.Filter.lt('CLOUD_COVER', MAX_CLOUD));

var lc08 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(LAGOS_BUFFERED)
  .filterDate(DATE_START, DATE_END)
  .filter(ee.Filter.lt('CLOUD_COVER', MAX_CLOUD));

var allScenes = lc09.merge(lc08);
print('Total scenes (LC08 + LC09): ' + allScenes.size().getInfo());

// Print each scene.
allScenes.evaluate(function(collection) {
  if (!collection.features || collection.features.length === 0) {
    print('NO SCENES FOUND!');
    print('Try widening the date range or increasing MAX_CLOUD.');
    return;
  }
  
  print('');
  print('--- ALL SCENES ---');
  
  collection.features.forEach(function(feature, idx) {
    var p = feature.properties;
    print((idx + 1) + '. ' + 
      (p.SPACECRAFT_ID || 'unknown') + ' | ' +
      'Path ' + p.WRS_PATH + '/Row ' + p.WRS_ROW + ' | ' +
      (p.DATE_ACQUIRED || 'unknown') + ' | ' +
      'Cloud: ' + p.CLOUD_COVER + '%');
  });
  
  // Breakdown by path/row.
  print('');
  print('--- BY PATH/ROW ---');
  
  var pathRows = {};
  collection.features.forEach(function(feature) {
    var p = feature.properties;
    var key = p.WRS_PATH + '/' + p.WRS_ROW;
    if (!pathRows[key]) {
      pathRows[key] = {count: 0, bestCloud: 100, bestDate: '', bestSat: ''};
    }
    pathRows[key].count++;
    if (p.CLOUD_COVER < pathRows[key].bestCloud) {
      pathRows[key].bestCloud = p.CLOUD_COVER;
      pathRows[key].bestDate = p.DATE_ACQUIRED;
      pathRows[key].bestSat = p.SPACECRAFT_ID;
    }
  });
  
  for (var key in pathRows) {
    var info = pathRows[key];
    print(key + ': ' + info.count + ' scenes' +
      ' (best: ' + info.bestDate + ', ' + info.bestCloud + '% cloud, ' + info.bestSat + ')');
  }
  
  // Show map preview.
  Map.centerObject(LAGOS_BUFFERED, 9);
  Map.addLayer(LAGOS_BUFFERED, {color: 'yellow'}, 'Lagos buffer');
  
  // Preview the least cloudy scene overall.
  var sorted = allScenes.sort('CLOUD_COVER');
  var best = ee.Image(sorted.first());
  var bestProps = collection.features[0].properties;
  
  print('');
  print('--- BEST OVERALL SCENE ---');
  print('Path/Row: ' + bestProps.WRS_PATH + '/' + bestProps.WRS_ROW);
  print('Date: ' + bestProps.DATE_ACQUIRED);
  print('Cloud: ' + bestProps.CLOUD_COVER + '%');
  print('Satellite: ' + bestProps.SPACECRAFT_ID);
  print('');
  print('Check the map — yellow polygon is the Lagos buffer.');
  print('The RGB layer shows the best scene coverage.');
});

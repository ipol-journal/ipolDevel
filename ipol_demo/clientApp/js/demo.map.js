function printMapPanel(center) {
   $('#map-container').removeClass('di-none');
    $('#map-container').addClass('map-container');
    const style = {
        "version": 8,
          "sources": {
          "osm": {
                  "type": "raster",
                  "tiles": ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                  "tileSize": 256,
            "attribution": "&copy; OpenStreetMap Contributors",
            "maxzoom": 19
          }
        },
        "layers": [
          {
            "id": "osm",
            "type": "raster",
            "source": "osm" // This must match the source key above
          }
        ]
      };

    const map = new maplibregl.Map({
        container: 'map', // container ID
        style: style,
        zoom: 14 // starting zoom
    });
    map.jumpTo({center:center});

    document.querySelector('#map').style.height = '100%';
    document.querySelector('#map').style.width = '100%';
    window.setTimeout(()=>map.resize(), 100);
    const colors = {
      'darkGray': '#404040',
      'yellow': '#fbb03b',
      'blue': '#3bb2d0',
      'white': '#fff'
    }
    const draw = new MapboxDraw({
        displayControlsDefault: false,
        // Select which mapbox-gl-draw control buttons to add to the map.
        controls: {
            polygon: true,
            trash: true
        },
        // Set mapbox-gl-draw to draw by default.
        // The user does not have to click the polygon control button first.
        defaultMode: 'draw_polygon',
        styles: [
          {
            'id': 'gl-draw-polygon-fill-inactive',
            'type': 'fill',
            'filter': ['all', ['==', 'active', 'false'],
                ['==', '$type', 'Polygon'],
                ['!=', 'mode', 'static']
            ],
            'paint': {
                'fill-color': colors.yellow,
                'fill-outline-color': colors.yellow,
                'fill-opacity': 0.5
            }
          },
          {
              'id': 'gl-draw-polygon-fill-active',
              'type': 'fill',
              'filter': ['all', ['==', 'active', 'true'],
                  ['==', '$type', 'Polygon']
              ],
              'paint': {
                  'fill-color': colors.yellow,
                  'fill-outline-color': colors.yellow,
                  'fill-opacity': 0.5
              }
          },
          {
              'id': 'gl-draw-polygon-midpoint',
              'type': 'circle',
              'filter': ['all', ['==', '$type', 'Point'],
                  ['==', 'meta', 'midpoint']
              ],
              'paint': {
                  'circle-radius': 3,
                  'circle-color': colors.yellow
              }
          },
          {
              'id': 'gl-draw-polygon-stroke-inactive',
              'type': 'line',
              'filter': ['all', ['==', 'active', 'false'],
                  ['==', '$type', 'Polygon'],
                  ['!=', 'mode', 'static']
              ],
              'layout': {
                  'line-cap': 'round',
                  'line-join': 'round'
              },
              'paint': {
                  'line-color': colors.blue,
                  'line-width': 2
              }
          },
          {
              'id': 'gl-draw-polygon-stroke-active',
              'type': 'line',
              'filter': ['all', ['==', 'active', 'true'],
                  ['==', '$type', 'Polygon']
              ],
              'layout': {
                  'line-cap': 'round',
                  'line-join': 'round'
              },
              'paint': {
                  'line-color': colors.yellow,
                  'line-dasharray': [0.2, 2],
                  'line-width': 2
              }
          },
          {
              'id': 'gl-draw-line-inactive',
              'type': 'line',
              'filter': ['all', ['==', 'active', 'false'],
                  ['==', '$type', 'LineString'],
                  ['!=', 'mode', 'static']
              ],
              'layout': {
                  'line-cap': 'round',
                  'line-join': 'round'
              },
              'paint': {
                  'line-color': colors.blue,
                  'line-width': 2
              }
          },
          {
              'id': 'gl-draw-line-active',
              'type': 'line',
              'filter': ['all', ['==', '$type', 'LineString'],
                  ['==', 'active', 'true']
              ],
              'layout': {
                  'line-cap': 'round',
                  'line-join': 'round'
              },
              'paint': {
                  'line-color': colors.yellow,
                  'line-dasharray': [0.2, 2],
                  'line-width': 2
              }
          },
          {
              'id': 'gl-draw-polygon-and-line-vertex-stroke-inactive',
              'type': 'circle',
              'filter': ['all', ['==', 'meta', 'vertex'],
                  ['==', '$type', 'Point'],
                  ['!=', 'mode', 'static']
              ],
              'paint': {
                  'circle-radius': 5,
                  'circle-color': colors.white
              }
          },
          {
              'id': 'gl-draw-polygon-and-line-vertex-inactive',
              'type': 'circle',
              'filter': ['all', ['==', 'meta', 'vertex'],
                  ['==', '$type', 'Point'],
                  ['!=', 'mode', 'static']
              ],
              'paint': {
                  'circle-radius': 3,
                  'circle-color': colors.yellow
              }
          },
          {
              'id': 'gl-draw-point-point-stroke-inactive',
              'type': 'circle',
              'filter': ['all', ['==', 'active', 'false'],
                  ['==', '$type', 'Point'],
                  ['==', 'meta', 'feature'],
                  ['!=', 'mode', 'static']
              ],
              'paint': {
                  'circle-radius': 5,
                  'circle-opacity': 1,
                  'circle-color': colors.white
              }
          },
          {
              'id': 'gl-draw-point-inactive',
              'type': 'circle',
              'filter': ['all', ['==', 'active', 'false'],
                  ['==', '$type', 'Point'],
                  ['==', 'meta', 'feature'],
                  ['!=', 'mode', 'static']
              ],
              'paint': {
                  'circle-radius': 3,
                  'circle-color': colors.blue
              }
          },
          {
              'id': 'gl-draw-point-stroke-active',
              'type': 'circle',
              'filter': ['all', ['==', '$type', 'Point'],
                  ['==', 'active', 'true'],
                  ['!=', 'meta', 'midpoint']
              ],
              'paint': {
                  'circle-radius': 7,
                  'circle-color': colors.white
              }
          },
          {
              'id': 'gl-draw-point-active',
              'type': 'circle',
              'filter': ['all', ['==', '$type', 'Point'],
                  ['!=', 'meta', 'midpoint'],
                  ['==', 'active', 'true']
              ],
              'paint': {
                  'circle-radius': 5,
                  'circle-color': colors.yellow
              }
          },
          {
              'id': 'gl-draw-polygon-fill-static',
              'type': 'fill',
              'filter': ['all', ['==', 'mode', 'static'],
                  ['==', '$type', 'Polygon']
              ],
              'paint': {
                  'fill-color': colors.darkGray,
                  'fill-outline-color': colors.darkGray,
                  'fill-opacity': 0.1
              }
          },
          {
              'id': 'gl-draw-polygon-stroke-static',
              'type': 'line',
              'filter': ['all', ['==', 'mode', 'static'],
                  ['==', '$type', 'Polygon']
              ],
              'layout': {
                  'line-cap': 'round',
                  'line-join': 'round'
              },
              'paint': {
                  'line-color': colors.darkGray,
                  'line-width': 2
              }
          },
          {
              'id': 'gl-draw-line-static',
              'type': 'line',
              'filter': ['all', ['==', 'mode', 'static'],
                  ['==', '$type', 'LineString']
              ],
              'layout': {
                  'line-cap': 'round',
                  'line-join': 'round'
              },
              'paint': {
                  'line-color': colors.darkGray,
                  'line-width': 2
              }
          },
          {
              'id': 'gl-draw-point-static',
              'type': 'circle',
              'filter': ['all', ['==', 'mode', 'static'],
                  ['==', '$type', 'Point']
              ],
              'paint': {
                  'circle-radius': 5,
                  'circle-color': colors.darkGray
              }
          }
        ]
    });
    map.addControl(draw);
    
    map.on('draw.create', updateArea);
    map.on('draw.delete', updateArea);
    map.on('draw.update', updateArea);
    
    function updateArea(e) {
        const data = draw.getAll();
        const answer = document.getElementById('calculated-area');
        const stores = map.querySourceFeatures("geo_data")
        console.log(stores)
        if (data.features.length > 0) {
            console.info(data);
            let geoJSON = data;
            helpers.addToStorage('map', geoJSON);
            const area = turf.area(data);
            // Restrict the area to 2 decimal points.
            const rounded_area = Math.round(area * 100) / 100;
            answer.innerHTML = `<p><strong>${rounded_area}</strong></p><p>square meters</p>`;
        } else {
            helpers.removeItem('map');
            answer.innerHTML = '';
            if (e.type !== 'draw.delete')
                alert('Click the map to draw a polygon.');
        }
    }
}

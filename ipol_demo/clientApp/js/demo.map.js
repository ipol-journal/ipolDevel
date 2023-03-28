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
    
    const draw = new MapboxDraw({
        displayControlsDefault: false,
        // Select which mapbox-gl-draw control buttons to add to the map.
        controls: {
            polygon: true,
            trash: true
        },
        // Set mapbox-gl-draw to draw by default.
        // The user does not have to click the polygon control button first.
        defaultMode: 'draw_polygon'
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
            files[0] = geoJSON
            const area = turf.area(data);
            // Restrict the area to 2 decimal points.
            const rounded_area = Math.round(area * 100) / 100;
            answer.innerHTML = `<p><strong>${rounded_area}</strong></p><p>square meters</p>`;
        } else {
            answer.innerHTML = '';
            if (e.type !== 'draw.delete')
            alert('Click the map to draw a polygon.');
        }
    }
}

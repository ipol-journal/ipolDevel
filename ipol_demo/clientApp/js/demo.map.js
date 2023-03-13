function printMapPanel() {
    const token = document.createElement('script');
    token.setAttribute('src', 'js/demo.token.js');
    document.head.appendChild(token);
    token.addEventListener('load', function() {
        setupMapbox();
      });
}

function setupMapbox() {
    $('#map-container').removeClass('di-none');
    $('#map-container').addClass('map-container');
    mapboxgl.accessToken = MAPBOX_TOKEN;
    const map = new mapboxgl.Map({
        container: 'map', // container ID
        // Choose from Mapbox's core styles, or make your own style with Mapbox Studio
        style: 'mapbox://styles/mapbox/satellite-v9', // style URL
        center: [2.294226116367639, 48.85813310909694], // starting position [lng, lat]
        zoom: 14 // starting zoom
    });
    
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
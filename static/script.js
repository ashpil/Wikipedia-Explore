mapboxgl.accessToken = 'pk.eyJ1IjoiYXNocGlsIiwiYSI6ImNrNGRjbXdpOTAwbHQza21vbWE2aGlkZTYifQ.7QOHc9uZDLDF2FT95M76Ig';

var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/ashpil/ck4dcpj9t0avf1dn0nn3ffoid',
    zoom: 1
});

map.on('load', function() {
	$('button').click(function() {
	    var bounds = map.getBounds()
		var data = {
			"latitude": map.getCenter().lat,
			"longitude": map.getCenter().lng,
			"zoom": map.getZoom(),
			"sw": bounds.getSouthWest().toArray(),
			"ne": bounds.getNorthEast().toArray()
		};

		$.ajax({
			url: "/",
			type: "POST",
			data: JSON.stringify(data),
			contentType: "application/json",
			dataType: "json",
			success: function(response) {
			    console.log(response)
			    if (response == "NoArticles123Error"){
			        document.getElementById("button").innerHTML="No Articles in Area";
			    } else {
				document.getElementById("button").innerHTML="Get Articles in Area";
				map.getSource('locations').setData('/static/locations.geojson?r=' + (new Date()).getTime());
				console.log('updated!')
			    }
			},
			error: function() {
				console.log("error!")
				document.getElementById("button").innerHTML="No Articles in Area";
			}
		});
    });
    map.loadImage(
        '/static/icon.png',
        function(error, image) {
            if (error) throw error;
            map.addImage('icon', image);
            map.addSource('locations', {
                type: 'geojson',
                data: '/static/initialLocations.geojson?r=' + (new Date()).getTime()
            });
            map.addLayer({
                'id': 'points',
                'type': 'symbol',
                'source': 'locations',
                'layout': {
                    'icon-image': 'icon',
                    'icon-size': 0.05,
                }
            });
        }
    );

    map.on('click', 'points', function(e) {
		var coordinates = e.features[0].geometry.coordinates.slice();
        var title = e.features[0].properties.title;
		var id = e.features[0].properties.id;
		$.ajax({
			type: 'POST',
			url: "/_get_description",
			data: {"article_id" : id},
			dataType: "html",
			success: function(response) {
				document.getElementById("content").innerHTML=response;
			},
			error: function() {
				console.log("error!")
			}
		});
		document.getElementById("content").innerHTML="Loading description...";
		document.getElementById("title").innerHTML=title;
		var titleurl = title.replace(" ", "_");
		document.getElementById('titlelink').href = "//en.wikipedia.org/wiki/" + titleurl;

		while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
			coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
		}

		new mapboxgl.Popup({closeButton: false})
			.setLngLat(coordinates)
			.setHTML("")
			.addTo(map);
    });

    map.on('mouseenter', 'points', function() {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'points', function() {
        map.getCanvas().style.cursor = '';
    });
});
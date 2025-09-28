document.addEventListener("DOMContentLoaded", function () {
    const defaultLocation = [6.1164, 125.1716]; // General Santos City coordinates

    // Get the necessary fields
    const addressField = document.getElementById('location-input');
    const latitudeField = document.getElementById('latitude-input');
    const longitudeField = document.getElementById('longitude-input');

    // Create and insert the map container
    let mapContainer = document.getElementById('map');
    if (!mapContainer) {
        mapContainer = document.createElement('div');
        mapContainer.id = 'map';
        mapContainer.style.width = '100%';
        mapContainer.style.height = '400px';
        mapContainer.style.marginBottom = '20px';
        addressField.parentNode.insertBefore(mapContainer, addressField.nextSibling);
    }

    const map = L.map('map').setView(defaultLocation, 13);

    // Add OpenStreetMap tiles:
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // Add a draggable marker:
    const marker = L.marker(defaultLocation, { draggable: true }).addTo(map);

    // Update address and coordinates when marker is dragged:
    marker.on('dragend', function (event) {
        const latLng = marker.getLatLng();
        updateAddressAndCoordinates(latLng.lat, latLng.lng);
    });

    // Update address and coordinates when map is clicked:
    map.on('click', function (event) {
        const latLng = event.latlng;
        marker.setLatLng(latLng);
        updateAddressAndCoordinates(latLng.lat, latLng.lng);
    });

    function updateAddressAndCoordinates(lat, lng) {
        latitudeField.value = lat;
        longitudeField.value = lng;

        const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data && data.display_name) {
                    addressField.value = data.display_name;
                }
            })
            .catch(error => {
                console.error('Error fetching address:', error);
            });
    }

    // If latitude and longitude are provided, set the marker to that position
    if (latitudeField.value && longitudeField.value) {
        const latLng = [parseFloat(latitudeField.value), parseFloat(longitudeField.value)];
        marker.setLatLng(latLng);
        map.setView(latLng, 13);
        updateAddressAndCoordinates(latLng[0], latLng[1]);
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const defaultLocation = [6.1164, 125.1716]; // General Santos City coordinates

    const addressField = document.getElementById('address-input');

    // Add map container dynamically:
    const mapContainer = document.createElement('div');
    mapContainer.id = 'map';
    mapContainer.style.width = '100%';
    mapContainer.style.height = '400px';
    mapContainer.style.marginBottom = '20px';
    mapContainer.style.display = 'none'; // Initially hidden
    addressField.parentNode.insertBefore(mapContainer, addressField.nextSibling);

    // Create the checkbox to enable/disable map:
    const checkboxContainer = document.createElement('div');
    checkboxContainer.style.marginBottom = '10px';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = 'enable-map';

    const label = document.createElement('label');
    label.htmlFor = 'enable-map';
    label.textContent = ' Enable Map Drop Pin';

    checkboxContainer.appendChild(checkbox);
    checkboxContainer.appendChild(label);

    // Insert checkbox container before the map container (below the input field)
    addressField.parentNode.insertBefore(checkboxContainer, mapContainer);

    // Initialize the map:
    const map = L.map('map').setView(defaultLocation, 13);

    // Add OpenStreetMap tiles:
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // Add a draggable marker:
    const marker = L.marker(defaultLocation, { draggable: true }).addTo(map);

    // Check if the address input is not empty:
    if (addressField.value.trim() !== '') {
        checkbox.checked = true;
        mapContainer.style.display = 'block';
        map.dragging.enable();
        marker.dragging.enable();
    } else {
        // Disable map dragging initially:
        map.dragging.disable();
        marker.dragging.disable();
    }

    // Checkbox change event listener:
    checkbox.addEventListener('change', function () {
        if (checkbox.checked) {
            mapContainer.style.display = 'block';
            map.dragging.enable();
            marker.dragging.enable();
        } else {
            mapContainer.style.display = 'none';
            map.dragging.disable();
            marker.dragging.disable();
        }
    });

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
        document.getElementById('latitude-input').value = lat;
        document.getElementById('longitude-input').value = lng;

        // Use Nominatim to get the address from lat/lng:
        const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data && data.display_name) {
                    document.getElementById('address-input').value = data.display_name;
                }
            })
            .catch(error => {
                console.error('Error fetching address:', error);
            });
    }
});

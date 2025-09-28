document.addEventListener("DOMContentLoaded", function () {
    // Get the location type field by selecting the original <select> element:
    const locationTypeField = document.getElementById('id_location_type');
    const addressField = document.getElementById('id_location');
    const latitudeField = document.getElementById('latitude-input');  // Hidden input
    const longitudeField = document.getElementById('longitude-input'); // Hidden input
    const virtualUrlField = document.getElementById('id_virtual_url');
    const virtualPlatformField = document.getElementById('id_virtual_platform');
    const virtualDetailsField = document.getElementById('id_virtual_details');

    // Create and insert physical location message
    let physicalMessage = document.getElementById('physical-location-message');
    if (!physicalMessage) {
        physicalMessage = document.createElement('div');
        physicalMessage.id = 'physical-location-message';
        physicalMessage.style.display = 'none';
        physicalMessage.style.color = 'red';
        physicalMessage.style.marginTop = '10px';
        physicalMessage.style.fontSize = '16px';
        physicalMessage.innerHTML = '<p>Note: Physical location details are not required for virtual events.</p>';
        
        addressField.parentNode.parentNode.insertBefore(physicalMessage, addressField.parentNode.nextSibling);
    }

    // Create and insert virtual location message
    let virtualMessage = document.getElementById('virtual-location-message');
    if (!virtualMessage) {
        virtualMessage = document.createElement('div');
        virtualMessage.id = 'virtual-location-message';
        virtualMessage.style.display = 'none';
        virtualMessage.style.color = 'red';
        virtualMessage.style.marginTop = '10px';
        virtualMessage.style.fontSize = '16px';
        virtualMessage.innerHTML = '<p>Note: Virtual location details are not required for physical events.</p>';
        
        virtualUrlField.parentNode.parentNode.insertBefore(virtualMessage, virtualUrlField.parentNode.nextSibling);
    }

    // Toggle visibility of location fields and labels based on location type
    function toggleLocationFields() {
        const locationType = locationTypeField.value;

        const isPhysical = locationType === 'physical';
        const isVirtual = locationType === 'virtual';
        const isBoth = locationType === 'both';

        // Show/hide physical location fields (input)
        if (isPhysical || isBoth) {
            if (addressField) {
                addressField.parentElement.style.display = 'block';
            }
            if (physicalMessage) {
                physicalMessage.style.display = 'none';
            }
        } else if (isVirtual) {
            if (addressField) {
                addressField.parentElement.style.display = 'none';
            }
            if (physicalMessage) {
                physicalMessage.style.display = 'block';
            }
        }

        // Show/hide virtual location fields
        const virtualUrlLabel = document.querySelector("label[for='id_virtual_url']");
        const virtualPlatformLabel = document.querySelector("label[for='id_virtual_platform']");
        const virtualDetailsLabel = document.querySelector("label[for='id_details']");

        if (virtualUrlLabel && virtualPlatformLabel && virtualDetailsField && virtualDetailsLabel) {
            if (isVirtual || isBoth) {
                virtualUrlLabel.style.display = 'block';
                virtualPlatformLabel.style.display = 'block';
                virtualDetailsLabel.style.display = 'block';
                virtualUrlField.parentElement.style.display = 'block';
                virtualPlatformField.parentElement.style.display = 'block';
                virtualDetailsField.parentElement.style.display = 'block';
                virtualMessage.style.display = 'none';
            } else {
                virtualUrlLabel.style.display = 'none';
                virtualPlatformLabel.style.display = 'none';
                virtualDetailsLabel.style.display = 'none';
                virtualUrlField.parentElement.style.display = 'none';
                virtualPlatformField.parentElement.style.display = 'none';
                virtualDetailsField.parentElement.style.display = 'none';
                virtualMessage.style.display = 'block';
            }
        } else {
            console.error("One or more virtual location elements not found.");
        }
    }

    // Attach event listener to the original <select> element using Select2's event
    if (locationTypeField) {
        $(locationTypeField).on('select2:select', toggleLocationFields);
    } else {
        console.error("Location type field not found!"); // Error log
    }

    // Initial toggle based on the current value
    toggleLocationFields();
});

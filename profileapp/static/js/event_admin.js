document.addEventListener("DOMContentLoaded", function () {
    const isCancelledField = document.getElementById('id_is_cancelled');
    const remarksField = document.getElementById('id_remarks');

    // Ensure both elements are found before proceeding
    if (!isCancelledField || !remarksField) {
        console.error('isCancelledField or remarksField not found!');
        return;  // Exit if either element is not found
    }

    // Access the parent div of the remarks field directly
    const remarksContainer = remarksField.closest('.field-remarks');
    const remarksLabel = document.querySelector('label[for="id_remarks"]'); // Find the associated label

    if (remarksContainer && remarksLabel) {
        remarksContainer.style.display = 'none'; // Initially hide the remarks field
        remarksLabel.style.display = 'none'; // Initially hide the label as well
    } else {
        console.error('Remarks field container or label not found!');
        return;
    }

    function toggleRemarksField() {
        if (isCancelledField.checked) {
            remarksContainer.style.display = 'block';
            remarksLabel.style.display = 'block';
        } else {
            remarksContainer.style.display = 'none';
            remarksLabel.style.display = 'none';
            remarksField.value = '';  // Clear the remarks field if unchecked
        }
    }

    // Add event listener to toggle remarks field when is_cancelled changes
    isCancelledField.addEventListener('change', toggleRemarksField);

    // Initial check on page load
    toggleRemarksField();
});

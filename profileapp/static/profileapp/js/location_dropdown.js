async function fetchJSON(url) {
    const res = await fetch(url);
    return await res.json();
}

// Load Regions
async function loadRegions() {
    const regions = await fetchJSON('https://psgc.gitlab.io/api/regions');
    const regionSelect = document.getElementById('region');
    regionSelect.innerHTML = '<option value="">Select Region</option>';
    regions.forEach(r => {
        regionSelect.innerHTML += `<option value="${r.code}">${r.name}</option>`;
    });
}

document.addEventListener('DOMContentLoaded', function() {
    loadRegions();

    document.getElementById('region').addEventListener('change', async function() {
        const regionId = this.value;
        const provinces = await fetchJSON(`https://psgc.gitlab.io/api/provinces?region_id=${regionId}`);
        const provinceSelect = document.getElementById('province');
        provinceSelect.innerHTML = '<option value="">Select Province</option>';
        provinces.forEach(p => {
            provinceSelect.innerHTML += `<option value="${p.code}">${p.name}</option>`;
        });

        // Reset lower selects
        document.getElementById('city').innerHTML = '<option value="">Select City</option>';
        document.getElementById('barangay').innerHTML = '<option value="">Select Barangay</option>';
    });

    document.getElementById('province').addEventListener('change', async function() {
        const provinceId = this.value;
        const cities = await fetchJSON(`https://psgc.gitlab.io/api/cities?province_id=${provinceId}`);
        const citySelect = document.getElementById('city');
        citySelect.innerHTML = '<option value="">Select City</option>';
        cities.forEach(c => {
            citySelect.innerHTML += `<option value="${c.code}">${c.name}</option>`;
        });

        // Reset barangay
        document.getElementById('barangay').innerHTML = '<option value="">Select Barangay</option>';
    });

    document.getElementById('city').addEventListener('change', async function() {
        const cityId = this.value;
        const barangays = await fetchJSON(`https://psgc.gitlab.io/api/barangays?city_id=${cityId}`);
        const barangaySelect = document.getElementById('barangay');
        barangaySelect.innerHTML = '<option value="">Select Barangay</option>';
        barangays.forEach(b => {
            barangaySelect.innerHTML += `<option value="${b.code}">${b.name}</option>`;
        });
    });
});

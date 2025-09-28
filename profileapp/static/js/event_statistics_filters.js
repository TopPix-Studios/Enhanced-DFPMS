document.addEventListener('DOMContentLoaded', function() {
    const tagFilter = document.getElementById('tagFilter');
    const eventFilter = document.getElementById('eventFilter');
    const filterButton = document.getElementById('filterButton');

    let allData = []; // Store all event data fetched
    window.attendanceChart = null; // ✅ Initialize first!

    function fetchEventStatistics() {
        fetch(eventStatisticsUrl)
            .then(response => response.json())
            .then(data => {
                allData = data.attendance_by_event;
                renderAttendanceChart(allData);
                populateTagOptions(data.tags);
                populateEventOptions(allData); // 👈 populate events initially
            })
            .catch(error => console.error('Error fetching event statistics:', error));
    }

    function populateTagOptions(tags) {
        tags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag.skill_id;
            option.textContent = tag.skill;
            tagFilter.appendChild(option);
        });
    }

    function populateEventOptions(events, selectedTag = "") {
        // Clear current options
        eventFilter.innerHTML = '<option value="">All Events</option>';

        // Filter events if a tag is selected
        let filteredEvents = events;
        if (selectedTag) {
            const selectedTagNumber = parseInt(selectedTag, 10);
            filteredEvents = events.filter(event => event.tags.includes(selectedTagNumber));
        }

        // Only add unique event names
        const uniqueEventNames = new Set(filteredEvents.map(event => event.event));
        uniqueEventNames.forEach(eventName => {
            const option = document.createElement('option');
            option.value = eventName;
            option.textContent = eventName;
            eventFilter.appendChild(option);
        });
    }

    function renderAttendanceChart(data) {
        const ctx = document.getElementById('attendanceChart').getContext('2d');
        const titles = data.map(item => item.event);
        const counts = data.map(item => item.count);
    
        // ✅ Only destroy if it exists and is a Chart
        if (window.attendanceChart instanceof Chart) {
            window.attendanceChart.destroy();
        }
    
        window.attendanceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: titles,
                datasets: [{
                    label: 'Attendance',
                    data: counts,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // important for responsive containers
                layout: {
                    padding: 10
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: function (tooltipItems) {
                                const index = tooltipItems[0].dataIndex;
                                return titles[index]; // full title on hover
                            }
                        }
                    },
                    datalabels: {
                        anchor: 'end',
                        align: 'top',
                        color: '#777',
                        font: {
                            weight: 'bold',
                            size: 10
                        },
                        formatter: Math.round
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Event Name' },
                        ticks: {
                            autoSkip: false,
                            maxRotation: 45,
                            minRotation: 30,
                            callback: function (value) {
                                const label = this.getLabelForValue(value);
                                return label.length > 15 ? label.slice(0, 12) + '...' : label;
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Attendance Count' }
                    }
                }
            },
            plugins: [ChartDataLabels] // ✅ Register datalabels plugin
        });
    
        updateStatisticsCards(data);
    }
    

    function applyFilters() {
        const selectedTag = tagFilter.value;
        const selectedEvent = eventFilter.value;

        let filteredData = allData;

        if (selectedTag) {
            const selectedTagNumber = parseInt(selectedTag, 10);
            filteredData = filteredData.filter(item => item.tags.includes(selectedTagNumber));
        }

        if (selectedEvent) {
            filteredData = filteredData.filter(item => item.event === selectedEvent);
        }

        renderAttendanceChart(filteredData);
        renderFilteredStackedChart(filteredData);
    }

    tagFilter.addEventListener('change', function() {
        // Repopulate Event dropdown based on Tag selection
        populateEventOptions(allData, tagFilter.value);
    });

    filterButton.addEventListener('click', applyFilters);


    fetchEventStatistics();

    function renderFilteredStackedChart(filteredData) {
        const ctx = document.getElementById('filteredStackedChart').getContext('2d');
    
        const ageLabels = { 'A': '20 below', 'B': '20-29', 'C': '30-39', 'D': '40-49', 'E': '50+' };
        const genderLabels = { 'M': 'Male', 'F': 'Female', 'O': 'Other' };
    
        // Initialize counters
        const maleByAge = { 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0 };
        const femaleByAge = { 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0 };
        const otherByAge = { 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0 };
    
        const ageCounts = { 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0 };
        const genderCounts = { 'M': 0, 'F': 0, 'O': 0 };
    
        const pwdByAge = { 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0 };
        const fourPsByAge = { 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0 };
    
        const pwdByGender = { 'M': 0, 'F': 0, 'O': 0 };
        const fourPsByGender = { 'M': 0, 'F': 0, 'O': 0 };
    
        let totalPWD = 0;
        let total4Ps = 0;
    
        filteredData.forEach(event => {
            if (event.age_distribution && event.gender_distribution) {
                const totalEventAttendees = Object.values(event.age_distribution).reduce((sum, v) => sum + v, 0);
    
                Object.keys(ageLabels).forEach(age => {
                    const ageCount = event.age_distribution[age] || 0;
                    ageCounts[age] += ageCount;
    
                    const genderTotal = (event.gender_distribution['M'] || 0) + (event.gender_distribution['F'] || 0) + (event.gender_distribution['O'] || 0);
    
                    if (genderTotal > 0) {
                        maleByAge[age] += Math.round((event.gender_distribution['M'] || 0) * (ageCount / genderTotal));
                        femaleByAge[age] += Math.round((event.gender_distribution['F'] || 0) * (ageCount / genderTotal));
                        otherByAge[age] += Math.round((event.gender_distribution['O'] || 0) * (ageCount / genderTotal));
                    }
                });
    
                genderCounts['M'] += event.gender_distribution['M'] || 0;
                genderCounts['F'] += event.gender_distribution['F'] || 0;
                genderCounts['O'] += event.gender_distribution['O'] || 0;
            }
    
            if (event.pwd_distribution_by_age) {
                for (let age in event.pwd_distribution_by_age) {
                    pwdByAge[age] += event.pwd_distribution_by_age[age] || 0;
                }
            }
            if (event.four_ps_distribution_by_age) {
                for (let age in event.four_ps_distribution_by_age) {
                    fourPsByAge[age] += event.four_ps_distribution_by_age[age] || 0;
                }
            }
            if (event.pwd_distribution_by_gender) {
                for (let gender in event.pwd_distribution_by_gender) {
                    pwdByGender[gender] += event.pwd_distribution_by_gender[gender] || 0;
                }
            }
            if (event.four_ps_distribution_by_gender) {
                for (let gender in event.four_ps_distribution_by_gender) {
                    fourPsByGender[gender] += event.four_ps_distribution_by_gender[gender] || 0;
                }
            }
    
            totalPWD += event.pwd_count || 0;
            total4Ps += event.four_ps_count || 0;
        });
    
        // 🛑 Destroy old chart if exists
        if (window.filteredStackedChart instanceof Chart) {
            window.filteredStackedChart.destroy();
        }
    
        window.filteredStackedChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.values(ageLabels),
                datasets: [
                    {
                        label: 'Male',
                        data: Object.keys(ageLabels).map(key => maleByAge[key]),
                        backgroundColor: 'rgba(54, 162, 235, 0.7)',
                        stack: 'gender'
                    },
                    {
                        label: 'Female',
                        data: Object.keys(ageLabels).map(key => femaleByAge[key]),
                        backgroundColor: 'rgba(255, 99, 132, 0.7)',
                        stack: 'gender'
                    },
                    {
                        label: 'Other',
                        data: Object.keys(ageLabels).map(key => otherByAge[key]),
                        backgroundColor: 'rgba(255, 206, 86, 0.7)',
                        stack: 'gender'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Gender Distribution by Age Bracket (Filtered Events)' },
                    datalabels: {
                        color: '#777', // 🎨 grey color
                        anchor: 'center',
                        align: 'center',
                        font: {
                            weight: 'bold',
                            size: 10
                        },
                        formatter: Math.round
                    }
                },
                
                scales: {
                    x: { stacked: true },
                    y: { stacked: true }
                }
            },
            plugins: [ChartDataLabels]

        });
    
        // ✅ Update Cards:
    
        // 🔥 Gender Distribution
        document.getElementById('filtered-male-count').textContent = genderCounts['M'];
        document.getElementById('filtered-female-count').textContent = genderCounts['F'];
        document.getElementById('filtered-other-count').textContent = genderCounts['O'];
    
        // 🔥 Age Distribution
        document.getElementById('filtered-age-a-count').textContent = ageCounts['A'];
        document.getElementById('filtered-age-b-count').textContent = ageCounts['B'];
        document.getElementById('filtered-age-c-count').textContent = ageCounts['C'];
        document.getElementById('filtered-age-d-count').textContent = ageCounts['D'];
        document.getElementById('filtered-age-e-count').textContent = ageCounts['E'];
    
        // 🔥 PWDs by Gender
        Object.keys(pwdByGender).forEach(gender => {
            const el = document.getElementById(`filtered-pwd-${gender.toLowerCase()}-count`);
            if (el) el.textContent = pwdByGender[gender];
        });
    
        // 🔥 4Ps by Gender
        Object.keys(fourPsByGender).forEach(gender => {
            const el = document.getElementById(`filtered-fourps-${gender.toLowerCase()}-count`);
            if (el) el.textContent = fourPsByGender[gender];
        });
    
        // 🔥 PWDs by Age
        Object.keys(pwdByAge).forEach(age => {
            const el = document.getElementById(`filtered-pwd-${age.toLowerCase()}-count`);
            if (el) el.textContent = pwdByAge[age];
        });
    
        // 🔥 4Ps by Age
        Object.keys(fourPsByAge).forEach(age => {
            const el = document.getElementById(`filtered-fourps-${age.toLowerCase()}-count`);
            if (el) el.textContent = fourPsByAge[age];
        });
    }
    
    
    
    
    
    
});

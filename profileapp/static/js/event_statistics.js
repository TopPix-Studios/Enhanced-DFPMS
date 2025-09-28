document.addEventListener('DOMContentLoaded', function() {
    fetchEventStatistics();
});

// Fetch Overall Event Statistics
function fetchEventStatistics() {
    fetch('/api/overall_event_statistics/')
        .then(response => response.json())
        .then(data => {
            displayEventSummary(data);
            renderAttendanceChart(data.attendance_by_event);
            renderRSVPComparisonChart(data);
            renderGenderRatioChart(data.gender_ratio);
            renderAgeRangeChart(data.age_distribution);
            renderFilteredStackedChart(data.attendance_by_event); // 🔥 Add this!
        })
        .catch(error => console.error('Error fetching event statistics:', error));
}

function renderFilteredStackedChart(filteredData) {
    const ctx = document.getElementById('filteredStackedChart').getContext('2d');

    const ageLabels = {
        'A': '20 below',
        'B': '20-29',
        'C': '30-39',
        'D': '40-49',
        'E': '50+'
    };

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

    // ✅ Update Distribution Cards

    // 1. Gender Distribution
    document.getElementById('filtered-male-count').textContent = genderCounts['M'];
    document.getElementById('filtered-female-count').textContent = genderCounts['F'];
    document.getElementById('filtered-other-count').textContent = genderCounts['O'];

    // 2. Age Distribution
    document.getElementById('filtered-age-a-count').textContent = ageCounts['A'];
    document.getElementById('filtered-age-b-count').textContent = ageCounts['B'];
    document.getElementById('filtered-age-c-count').textContent = ageCounts['C'];
    document.getElementById('filtered-age-d-count').textContent = ageCounts['D'];
    document.getElementById('filtered-age-e-count').textContent = ageCounts['E'];

    // 3. PWD Distribution
    Object.keys(pwdByAge).forEach(age => {
        const el = document.getElementById(`filtered-pwd-${age.toLowerCase()}-count`);
        if (el) el.textContent = pwdByAge[age];
    });
    Object.keys(pwdByGender).forEach(gender => {
        const el = document.getElementById(`filtered-pwd-${gender.toLowerCase()}-count`);
        if (el) el.textContent = pwdByGender[gender];
    });

    // 4. 4Ps Distribution
    Object.keys(fourPsByAge).forEach(age => {
        const el = document.getElementById(`filtered-fourps-${age.toLowerCase()}-count`);
        if (el) el.textContent = fourPsByAge[age];
    });
    Object.keys(fourPsByGender).forEach(gender => {
        const el = document.getElementById(`filtered-fourps-${gender.toLowerCase()}-count`);
        if (el) el.textContent = fourPsByGender[gender];
    });
}


// Display Summary Values and Counters
function displayEventSummary(data) {

    setText('total-attendees', data.total_attendees);
    setText('pwd-count', data.pwd_count);
    setText('pwd-percentage', data.pwd_percentage.toFixed(2));
    setText('four-ps-count', data.four_ps_count);
    setText('four-ps-percentage', data.four_ps_percentage.toFixed(2));
    setText('total-rsvps', data.total_rsvp_count);
    setText('total-events', data.total_event_count);
    setText('average-rsvps-per-event', data.average_rsvp_per_event.toFixed(0));
    setText('average-attendance-per-event', data.average_attendance_per_event.toFixed(0));
    setText('interested-count', data.interested_count);
    setText('interested-percentage', data.interested_percentage.toFixed(2));
    setText('attending-count', data.attending_count);
    setText('attending-percentage', data.attending_percentage.toFixed(2));
    setText('not-attending-count', data.not_attending_count);
    setText('not-attending-percentage', data.not_attending_percentage.toFixed(2));
    setText('converted-attendance-count', data.rsvp_to_attendance_count);
    setText('converted-attendance-percentage', data.rsvp_to_attendance_percentage.toFixed(2));

    // Gender Counts
    const totalGenderCount = data.gender_ratio.reduce((acc, item) => acc + item.count, 0);

    setText('male-count', getGenderCount(data.gender_ratio, 'Male'));
    setText('female-count', getGenderCount(data.gender_ratio, 'Female'));
    setText('other-count', getGenderCount(data.gender_ratio, 'Other'));
    setText('total-gender-count', totalGenderCount);

    // Age Distribution
    const ageMapping = { 'A': '20 below', 'B': '20-29', 'C': '30-39', 'D': '40-49', 'E': '50+' };
    const ageRanges = ['20 below', '20-29', '30-39', '40-49', '50+'];
    const ageCounts = ageRanges.map(label => {
        const code = Object.keys(ageMapping).find(key => ageMapping[key] === label);
        const item = data.age_distribution.find(a => a.age_range === code);
        return item ? item.count : 0;
    });
    setText('age-20-below-count', ageCounts[0]);
    setText('age-20-29-count', ageCounts[1]);
    setText('age-30-39-count', ageCounts[2]);
    setText('age-40-49-count', ageCounts[3]);
    setText('age-50-plus-count', ageCounts[4]);
}

// Helper: Set Text
function setText(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
    }
}

// Helper: Get Gender Count
function getGenderCount(genderData, gender) {
    const genderMap = {
        'male': 'M',
        'female': 'F',
        'other': 'O'
    };
    const code = genderMap[gender.toLowerCase()];
    const item = genderData.find(g => g.gender === code);
    return item ? item.count : 0;
}

function renderAttendanceChart(attendanceByEvent) {
    const ctx = document.getElementById('attendanceChart').getContext('2d');

    const eventTitles = attendanceByEvent.map(item => item.event);
    const attendanceCounts = attendanceByEvent.map(item => item.count);

    if (window.attendanceChart) {
        window.attendanceChart.destroy();
    }

    window.attendanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: eventTitles,
            datasets: [{
                label: 'Attendance',
                data: attendanceCounts,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true, // ✅ enable responsiveness
            maintainAspectRatio: false, // ✅ allow container to control height
            layout: {
                padding: 10
            },
            plugins: {
                legend: { display: false },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    color: '#c3c3c3',
                    font: {
                        weight: 'bold'
                    },
                    formatter: Math.round
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Event Name'
                    },
                    ticks: {
                        autoSkip: false,
                        maxRotation: 45,
                        minRotation: 30,
                        callback: function (value, index) {
                            const label = this.getLabelForValue(value);
                            return label.length > 15 ? label.slice(0, 12) + '...' : label;
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Attendance Count'
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}


function updateStatisticsCards(data) {
    const totalAttendees = data.reduce((sum, event) => sum + event.count, 0);
    const totalEvents = data.length;
    const totalPWD = data.reduce((sum, event) => sum + (event.pwd_count || 0), 0);
    const total4Ps = data.reduce((sum, event) => sum + (event.four_ps_count || 0), 0);
    const averageAttendance = totalEvents > 0 ? (totalAttendees / totalEvents).toFixed(0) : 0;
    const pwdPercentage = totalAttendees > 0 ? (totalPWD / totalAttendees * 100).toFixed(2) : 0;
    const fourPsPercentage = totalAttendees > 0 ? (total4Ps / totalAttendees * 100).toFixed(2) : 0;

    document.getElementById('total-attendees').textContent = totalAttendees;
    document.getElementById('average-attendance-per-event').textContent = averageAttendance;
    document.getElementById('pwd-count').textContent = totalPWD;
    document.getElementById('pwd-percentage').textContent = `${pwdPercentage}%`;
    document.getElementById('four-ps-count').textContent = total4Ps;
    document.getElementById('four-ps-percentage').textContent = `${fourPsPercentage}%`;
}

function renderRSVPComparisonChart(data) {
    const ctx = document.getElementById('rsvpAttendanceChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Interested', 'Attending', 'Not Attending', 'Converted Attendance'],
            datasets: [
                {
                    label: 'RSVP Count',
                    data: [
                        data.interested_count,
                        data.attending_count,
                        data.not_attending_count,
                        data.rsvp_to_attendance_count
                    ],
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Percentage (%)',
                    data: [
                        data.interested_percentage,
                        data.attending_percentage,
                        data.not_attending_percentage,
                        data.rsvp_to_attendance_percentage
                    ],
                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                    borderColor: 'rgba(255, 159, 64, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            ...getChartOptions('RSVP and Attendance Comparison', 'RSVP Status', 'Count / Percentage'),
            plugins: {
                ...getChartOptions().plugins,
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.raw;
                            return context.dataset.label.includes('%')
                                ? `${context.label}: ${Math.round(value)}%`
                                : `${context.label}: ${Math.round(value)}`;
                        }
                    }
                },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    offset: 8,
                    color: '#777',
                    font: {
                        weight: 'bold',
                        size: 10
                    },
                    formatter: function (value, context) {
                        return context.dataset.label.includes('%')
                            ? `${Math.round(value)}%`
                            : Math.round(value);
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}


// Render Gender Ratio Chart
function renderGenderRatioChart(genderData) {
    const ctx = document.getElementById('genderRatioChart').getContext('2d');
    const labels = genderData.map(item => item.gender);
    const counts = genderData.map(item => item.count);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Gender Ratio',
                data: counts,
                backgroundColor: [
                    'rgba(54, 162, 235, 0.2)', 
                    'rgba(255, 99, 132, 0.2)', 
                    'rgba(255, 206, 86, 0.2)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)', 
                    'rgba(255, 99, 132, 1)', 
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            ...getChartOptions('Gender Ratio Distribution', 'Gender', 'Count'),
            plugins: {
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
                y: {
                    beginAtZero: true,
                    suggestedMax: Math.max(...counts) + 20,  // 🔼 adds space above top bar
                    title: {
                        display: true,
                        text: 'Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Gender'
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
    
    
}

// Render Age Range Distribution Chart
function renderAgeRangeChart(ageDistribution) {
    const ctx = document.getElementById('ageRangeChart').getContext('2d');
    const ageMapping = { 'A': '20 below', 'B': '20-29', 'C': '30-39', 'D': '40-49', 'E': '50+' };
    const ageLabels = ['20 below', '20-29', '30-39', '40-49', '50+'];

    const ageCounts = ageLabels.map(label => {
        const code = Object.keys(ageMapping).find(key => ageMapping[key] === label);
        const item = ageDistribution.find(a => a.age_range === code);
        return item ? item.count : 0;
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ageLabels,
            datasets: [{
                label: 'Age Range Distribution',
                data: ageCounts,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            ...getChartOptions('Age Range Distribution', 'Age Range', 'Count'),
            plugins: {
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    offset: 8,
                    color: '#777',
                    font: {
                        weight: 'bold',
                        size: 10
                    },
                    formatter: Math.round
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grace: '10%',  // optional: adds space above tallest bar
                    title: {
                        display: true,
                        text: 'Count'
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}

// Helper: Common Chart Options
function getChartOptions(title = '', xTitle = '', yTitle = '') {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: true, position: 'top' },
            title: { display: true, text: title },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `${context.label}: ${context.raw}`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: yTitle }
            },
            x: {
                title: { display: true, text: xTitle }
            }
        }
    };
}

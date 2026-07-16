// Dashboard Charts rendering using Chart.js - Student Course Management Portal

document.addEventListener("DOMContentLoaded", function() {
    const regCtx = document.getElementById('registrationsChart');
    const enrollCtx = document.getElementById('enrollmentsChart');
    
    if (regCtx || enrollCtx) {
        // Fetch stats from the API
        fetch('/admin/chart-data')
            .then(response => response.json())
            .then(data => {
                
                // 1. Registrations Line Chart
                if (regCtx) {
                    new Chart(regCtx, {
                        type: 'line',
                        data: {
                            labels: data.registrations.labels,
                            datasets: [{
                                label: 'New Students',
                                data: data.registrations.data,
                                borderColor: '#4f46e5', // Primary
                                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                                fill: true,
                                tension: 0.4,
                                borderWidth: 3,
                                pointBackgroundColor: '#4f46e5',
                                pointRadius: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        stepSize: 1,
                                        color: '#64748b'
                                    },
                                    grid: {
                                        color: '#f1f5f9'
                                    }
                                },
                                x: {
                                    ticks: {
                                        color: '#64748b'
                                    },
                                    grid: {
                                        display: false
                                    }
                                }
                            }
                        }
                    });
                }
                
                // 2. Enrollments Bar Chart
                if (enrollCtx) {
                    new Chart(enrollCtx, {
                        type: 'bar',
                        data: {
                            labels: data.enrollments.labels,
                            datasets: [{
                                label: 'Enrolled Students',
                                data: data.enrollments.data,
                                backgroundColor: [
                                    'rgba(79, 70, 229, 0.85)', // Indigo
                                    'rgba(14, 165, 233, 0.85)', // Sky
                                    'rgba(244, 63, 94, 0.85)',  // Rose
                                    'rgba(16, 185, 129, 0.85)',  // Emerald
                                    'rgba(245, 158, 11, 0.85)'   // Amber
                                ],
                                borderRadius: 8,
                                borderSkipped: false
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        stepSize: 1,
                                        color: '#64748b'
                                    },
                                    grid: {
                                        color: '#f1f5f9'
                                    }
                                },
                                x: {
                                    ticks: {
                                        color: '#64748b',
                                        maxRotation: 45,
                                        minRotation: 0
                                    },
                                    grid: {
                                        display: false
                                    }
                                }
                            }
                        }
                    });
                }
            })
            .catch(err => {
                console.error("Error loading dashboard chart data: ", err);
            });
    }
});

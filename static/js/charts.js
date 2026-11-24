// Chart.js helper utilities for Academic Analytics

const MITSCharts = {
    // Colors matching Midnight Navy theme
    colors: {
        primaryNavy: '#172554',
        secondaryBlue: '#2563EB',
        accentSky: '#38BDF8',
        successGreen: '#16A34A',
        warningAmber: '#D97706',
        dangerRed: '#DC2626',
        purple: '#8B5CF6',
        grayGrid: '#E2E8F0',
        textDark: '#1E293B',
        textMuted: '#64748B'
    },

    // 1. Grade Distribution Bar Chart
    createGradeDistributionChart: function (canvasId, labels, counts) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Students Count',
                    data: counts,
                    backgroundColor: [
                        '#16A34A', // Grade A - Green
                        '#2563EB', // Grade B - Blue
                        '#D97706', // Grade C - Amber
                        '#DC2626'  // Grade F - Red
                    ],
                    borderRadius: 6,
                    maxBarThickness: 45
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` ${context.raw} records`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: '#64748B' },
                        grid: { color: '#F1F5F9' }
                    },
                    x: {
                        ticks: { color: '#64748B' },
                        grid: { display: false }
                    }
                }
            }
        });
    },

    // 2. Subject Averages Horizontal / Vertical Bar Chart
    createSubjectAveragesChart: function (canvasId, labels, averages) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Score (%)',
                    data: averages,
                    backgroundColor: '#2563EB',
                    borderRadius: 6,
                    maxBarThickness: 40
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` Average: ${context.raw}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function (val) { return val + '%'; },
                            color: '#64748B'
                        },
                        grid: { color: '#F1F5F9' }
                    },
                    x: {
                        ticks: { color: '#64748B' },
                        grid: { display: false }
                    }
                }
            }
        });
    },

    // 3. Pass / Fail Donut Chart
    createPassFailChart: function (canvasId, passedCount, failedCount) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Passed', 'Failed'],
                datasets: [{
                    data: [passedCount, failedCount],
                    backgroundColor: ['#16A34A', '#DC2626'],
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 14, font: { size: 12 }, color: '#1E293B' }
                    }
                }
            }
        });
    },

    // 4. Performance Trend Line Chart
    createPerformanceTrendChart: function (canvasId, labels, datasets) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { boxWidth: 12, color: '#1E293B' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function (val) { return val + '%'; },
                            color: '#64748B'
                        },
                        grid: { color: '#F1F5F9' }
                    },
                    x: {
                        ticks: { color: '#64748B' },
                        grid: { display: false }
                    }
                }
            }
        });
    }
};

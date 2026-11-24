// Academic Analytics — Modern Chart.js Design System

// Global Chart.js Defaults
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748B';

const MITSCharts = {
    // 1. Grade Distribution Bar Chart
    createGradeDistributionChart: function (canvasId, labels, counts) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        '#10B981', // Grade A - Emerald
                        '#2563EB', // Grade B - Royal Blue
                        '#F59E0B', // Grade C - Amber
                        '#EF4444'  // Grade F - Soft Red
                    ],
                    borderRadius: 6,
                    maxBarThickness: 42
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        titleFont: { weight: '600', size: 12 },
                        bodyFont: { size: 12 },
                        padding: 10,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function (ctx) {
                                return `${ctx.raw} student records`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 2, color: '#94A3B8' },
                        grid: { color: '#F1F5F9', drawBorder: false },
                        border: { display: false }
                    },
                    x: {
                        ticks: { color: '#64748B', font: { weight: '500' } },
                        grid: { display: false },
                        border: { display: false }
                    }
                }
            }
        });
    },

    // 2. Subject Averages Bar Chart
    createSubjectAveragesChart: function (canvasId, labels, averages) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: averages,
                    backgroundColor: '#2563EB',
                    borderRadius: 6,
                    maxBarThickness: 36
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        padding: 10,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function (ctx) {
                                return `Average: ${ctx.raw}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            callback: function (v) { return v + '%'; },
                            color: '#94A3B8'
                        },
                        grid: { color: '#F1F5F9' },
                        border: { display: false }
                    },
                    x: {
                        ticks: { color: '#64748B', font: { weight: '500' } },
                        grid: { display: false },
                        border: { display: false }
                    }
                }
            }
        });
    },

    // 3. Pass / Fail Clean Donut Chart
    createPassFailChart: function (canvasId, passedCount, failedCount) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Passed', 'Failed'],
                datasets: [{
                    data: [passedCount, failedCount],
                    backgroundColor: ['#10B981', '#EF4444'],
                    borderWidth: 3,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '74%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 8,
                            boxHeight: 8,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 14,
                            font: { size: 12, weight: '500' },
                            color: '#475569'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        padding: 10,
                        cornerRadius: 8
                    }
                }
            }
        });
    },

    // 4. Performance Trend Line Chart
    createPerformanceTrendChart: function (canvasId, labels, datasets) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        // Apply smooth line styles
        const styledDatasets = datasets.map(d => ({
            ...d,
            pointRadius: 3,
            pointHoverRadius: 6,
            borderWidth: 2
        }));

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: styledDatasets
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
                        align: 'end',
                        labels: {
                            boxWidth: 8,
                            boxHeight: 8,
                            usePointStyle: true,
                            font: { size: 11, weight: '500' },
                            color: '#475569'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        padding: 10,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function (v) { return v + '%'; },
                            color: '#94A3B8'
                        },
                        grid: { color: '#F1F5F9' },
                        border: { display: false }
                    },
                    x: {
                        ticks: { color: '#64748B' },
                        grid: { display: false },
                        border: { display: false }
                    }
                }
            }
        });
    }
};

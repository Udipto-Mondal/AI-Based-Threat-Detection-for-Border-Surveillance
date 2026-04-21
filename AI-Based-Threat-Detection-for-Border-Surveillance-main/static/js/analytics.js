document.addEventListener('DOMContentLoaded', function() {
    // Daily Chart
    const dailyCtx = document.getElementById('daily-chart');
    let dailyChart;
    
    // Types Chart
    const typesCtx = document.getElementById('types-chart');
    let typesChart;
    
    // Heatmap Chart
    const heatmapCtx = document.getElementById('heatmap-chart');
    let heatmapChart;
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#00ff00',
                    font: { family: 'Share Tech Mono' }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(0, 255, 0, 0.2)' },
                ticks: { color: '#00ff00', font: { family: 'Share Tech Mono' } }
            },
            x: {
                grid: { color: 'rgba(0, 255, 0, 0.2)' },
                ticks: { color: '#00ff00', font: { family: 'Share Tech Mono' } }
            }
        }
    };
    
    // Fetch and render Daily Chart
    async function loadDailyChart() {
        try {
            const response = await fetch('/analytics/api/daily');
            const data = await response.json();
            
            if (dailyCtx) {
                dailyChart = new Chart(dailyCtx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Alerts',
                            data: data.data,
                            backgroundColor: 'rgba(0, 255, 0, 0.5)',
                            borderColor: '#00ff00',
                            borderWidth: 1
                        }]
                    },
                    options: chartOptions
                });
            }
        } catch (error) {
            console.error('Error loading daily chart:', error);
        }
    }
    
    // Fetch and render Types Chart
    async function loadTypesChart() {
        try {
            const response = await fetch('/analytics/api/types');
            const data = await response.json();
            
            if (typesCtx) {
                typesChart = new Chart(typesCtx, {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.data,
                            backgroundColor: [
                                'rgba(255, 0, 64, 0.7)',  // Red for PUSH-IN
                                'rgba(0, 255, 0, 0.7)',   // Green for PUSH-OUT
                                'rgba(76, 201, 240, 0.7)' // Cyan for others
                            ],
                            borderColor: [
                                '#ff0040',
                                '#00ff00',
                                '#4cc9f0'
                            ],
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: {
                                    color: '#00ff00',
                                    font: { family: 'Share Tech Mono' }
                                }
                            }
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Error loading types chart:', error);
        }
    }
    
    // Fetch and render Heatmap Chart
    async function loadHeatmapChart() {
        try {
            const response = await fetch('/analytics/api/heatmap');
            const data = await response.json();
            
            if (heatmapCtx) {
                heatmapChart = new Chart(heatmapCtx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Activity',
                            data: data.data,
                            borderColor: '#00ff00',
                            backgroundColor: 'rgba(0, 255, 0, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: chartOptions
                });
            }
        } catch (error) {
            console.error('Error loading heatmap chart:', error);
        }
    }
    
    // Export CSV
    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            window.location.href = '/analytics/api/export';
        });
    }
    
    // Load all charts
    loadDailyChart();
    loadTypesChart();
    loadHeatmapChart();
});


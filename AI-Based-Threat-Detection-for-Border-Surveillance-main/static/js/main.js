document.addEventListener('DOMContentLoaded', function() {
    // --- Chart Setup ---
    const ctx = document.getElementById('border-chart').getContext('2d');
    let borderChart;

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(0, 255, 0, 0.2)' },
                ticks: { color: '#00ff00' }
            },
            x: {
                grid: { color: 'rgba(0, 255, 0, 0.2)' },
                ticks: { color: '#00ff00' }
            }
        },
        plugins: {
            legend: { display: false }
        }
    };

    function setupChart(chartData) {
        borderChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Incidents',
                    data: chartData.data,
                    backgroundColor: 'rgba(0, 255, 0, 0.5)',
                    borderColor: '#00ff00',
                    borderWidth: 1
                }]
            },
            options: chartOptions
        });
    }

    // --- API Calls ---
    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            updateUI(data);
        } catch (error) {
            console.error("Failed to fetch status:", error);
        }
    }

    async function fetchChartData() {
        try {
            const response = await fetch('/api/chart_data');
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            setupChart(data);
        } catch (error) {
            console.error("Failed to fetch chart data:", error);
        }
    }

    // --- UI Updates ---
    function updateUI(data) {
        // Status Panel
        document.getElementById('analysis-status').textContent = data.stats.system_status || 'N/A';
        document.getElementById('status-text').textContent = data.stats.system_status || 'N/A';
        document.getElementById('total-alerts').textContent = data.stats.total_alerts || 0;
        document.getElementById('critical-alerts').textContent = data.stats.critical_alerts || 0;

        // Threat Log
        const logBody = document.getElementById('threat-log-body');
        logBody.innerHTML = ''; // Clear existing logs
        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach(alert => {
                const row = document.createElement('tr');
                if (alert.alert === "PUSH-IN") {
                    row.classList.add('critical');
                }
                row.innerHTML = `
                    <td>${alert.time}</td>
                    <td>${alert.frame}</td>
                    <td>${alert.track_id}</td>
                    <td>${alert.alert}</td>
                    <td>${alert.message}</td>
                `;
                logBody.appendChild(row);
            });
        } else {
            logBody.innerHTML = '<tr><td colspan="5">No threats detected. System clear.</td></tr>';
        }
    }

    // --- Event Listeners ---
    const videoPlaceholder = document.getElementById('placeholder');
    const videoStream = document.getElementById('video-stream');
    const uploadInput = document.getElementById('videoUpload');

    function startAnalysis(sourceType, file = null) {
        videoPlaceholder.classList.add('hidden');
        videoStream.src = `/video_feed?t=${new Date().getTime()}`; // bust cache

        let body;
        let headers = {};

        if (sourceType === 'file' && file) {
            body = new FormData();
            body.append('file', file);
        } else {
            body = JSON.stringify({ source: sourceType });
            headers['Content-Type'] = 'application/json';
        }

        fetch('/api/initiate_analysis', {
            method: 'POST',
            headers: headers,
            body: body
        })
        .then(res => res.json())
        .then(data => console.log(data.message))
        .catch(error => console.error("Error initiating analysis:", error));
    }

    document.getElementById('uploadBtn').addEventListener('click', () => uploadInput.click());
    uploadInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            startAnalysis('file', event.target.files[0]);
        }
    });

    document.getElementById('webcamBtn').addEventListener('click', () => startAnalysis('webcam'));
    document.getElementById('resetBtn').addEventListener('click', () => startAnalysis('default'));
    videoPlaceholder.addEventListener('click', () => startAnalysis('default'));

    // CSV Download
    document.getElementById('download-csv-btn').addEventListener('click', async () => {
         const response = await fetch('/api/status');
         const data = await response.json();
         const alerts = data.alerts;

         if (alerts.length === 0) {
             alert("No alerts to download.");
             return;
         }

         let csvContent = "data:text/csv;charset=utf-8,";
         csvContent += "Time,Frame,TrackID,Alert,Message\r\n"; // Header

         alerts.forEach(alert => {
             const row = [
                 alert.time,
                 alert.frame,
                 alert.track_id,
                 alert.alert,
                 `"${alert.message}"` // Quote message to handle commas
             ].join(",");
             csvContent += row + "\r\n";
         });

         const encodedUri = encodeURI(csvContent);
         const link = document.createElement("a");
         link.setAttribute("href", encodedUri);
         link.setAttribute("download", `falcon_ai_report_${new Date().toISOString()}.csv`);
         document.body.appendChild(link);
         link.click();
         document.body.removeChild(link);
    });


    // --- Initialization ---
    fetchChartData();
    setInterval(fetchStatus, 2000); // Refresh status and alerts every 2 seconds
});

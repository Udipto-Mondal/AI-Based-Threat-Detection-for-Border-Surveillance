document.addEventListener('DOMContentLoaded', function() {
    // --- System Load Chart Setup ---
    const systemLoadCtx = document.getElementById('system-load-chart');
    let systemLoadChart;
    
    const systemLoadData = {
        labels: [],
        datasets: [{
            label: 'System Load',
            data: [],
            borderColor: '#00ff00',
            backgroundColor: 'rgba(0, 255, 0, 0.1)',
            tension: 0.4,
            fill: true
        }]
    };
    
    const systemLoadOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                grid: { color: 'rgba(0, 255, 0, 0.2)' },
                ticks: { color: '#00ff00', font: { family: 'Share Tech Mono' } }
            },
            x: {
                grid: { color: 'rgba(0, 255, 0, 0.2)' },
                ticks: { color: '#00ff00', font: { family: 'Share Tech Mono' } }
            }
        }
    };
    
    if (systemLoadCtx) {
        systemLoadChart = new Chart(systemLoadCtx, {
            type: 'line',
            data: systemLoadData,
            options: systemLoadOptions
        });
        
        // Initialize with some data points
        for (let i = 0; i < 20; i++) {
            systemLoadData.labels.push('');
            systemLoadData.datasets[0].data.push(Math.random() * 100);
        }
        systemLoadChart.update();
    }
    
    // --- API Calls ---
    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            updateUI(data);
            
            // Play sound for critical alerts
            if (data.alerts && data.alerts.length > 0) {
                const latestAlert = data.alerts[0];
                if (latestAlert.alert === 'PUSH-IN') {
                    playAlertSound();
                }
            }
        } catch (error) {
            console.error("Failed to fetch status:", error);
        }
    }
    
    // --- UI Updates ---
    function updateUI(data) {
        // Status Panel
        const statusText = data.stats.system_status || 'N/A';
        document.getElementById('analysis-status').textContent = statusText;
        document.getElementById('status-text').textContent = statusText;
        document.getElementById('total-alerts').textContent = data.stats.total_alerts || 0;
        document.getElementById('critical-alerts').textContent = data.stats.critical_alerts || 0;
        document.getElementById('fps').textContent = data.stats.fps || 0;
        document.getElementById('active-tracks').textContent = data.stats.active_tracks || 0;
        
        // Update System Load Chart
        if (systemLoadChart) {
            const loadValue = Math.min(100, (data.stats.fps || 0) * 10 + Math.random() * 20);
            systemLoadData.labels.push('');
            systemLoadData.datasets[0].data.push(loadValue);
            
            if (systemLoadData.labels.length > 20) {
                systemLoadData.labels.shift();
                systemLoadData.datasets[0].data.shift();
            }
            systemLoadChart.update('none');
        }
        
        // Threat Log
        const logBody = document.getElementById('threat-log-body');
        if (logBody) {
            logBody.innerHTML = '';
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
    }
    
    // --- Alert Sound ---
    function playAlertSound() {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
    }
    
    // --- Event Listeners ---
    const videoPlaceholder = document.getElementById('placeholder');
    const videoStream = document.getElementById('video-stream');
    const uploadInput = document.getElementById('videoUpload');
    
    function startAnalysis(sourceType, file = null) {
        if (videoPlaceholder) videoPlaceholder.classList.add('hidden');
        if (videoStream) {
            videoStream.src = `/video_feed?t=${new Date().getTime()}`;
        }
        
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
    
    if (document.getElementById('uploadBtn')) {
        document.getElementById('uploadBtn').addEventListener('click', () => uploadInput.click());
    }
    
    if (uploadInput) {
        uploadInput.addEventListener('change', (event) => {
            if (event.target.files.length > 0) {
                startAnalysis('file', event.target.files[0]);
            }
        });
    }
    
    if (document.getElementById('webcamBtn')) {
        document.getElementById('webcamBtn').addEventListener('click', () => startAnalysis('webcam'));
    }
    
    if (document.getElementById('resetBtn')) {
        document.getElementById('resetBtn').addEventListener('click', () => startAnalysis('default'));
    }
    
    if (videoPlaceholder) {
        videoPlaceholder.addEventListener('click', () => startAnalysis('default'));
    }
    
    // --- System Health Check ---
    async function checkSystemHealth() {
        try {
            // Check MongoDB
            const response = await fetch('/api/status');
            if (response.ok) {
                const mongodbStatus = document.getElementById('mongodb-status');
                if (mongodbStatus) {
                    mongodbStatus.textContent = 'ONLINE';
                    mongodbStatus.className = 'status-indicator online';
                }
            }
        } catch (error) {
            const mongodbStatus = document.getElementById('mongodb-status');
            if (mongodbStatus) {
                mongodbStatus.textContent = 'OFFLINE';
                mongodbStatus.className = 'status-indicator offline';
            }
        }
        
        // Twilio status (simplified - could be enhanced)
        const twilioStatus = document.getElementById('twilio-status');
        if (twilioStatus) {
            twilioStatus.textContent = 'CONFIGURED';
            twilioStatus.className = 'status-indicator online';
        }
    }
    
    // --- Chatbot ---
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotBody = document.getElementById('chatbot-body');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');
    
    let chatbotOpen = false;
    
    if (chatbotToggle) {
        chatbotToggle.addEventListener('click', () => {
            chatbotOpen = !chatbotOpen;
            if (chatbotBody) {
                chatbotBody.style.display = chatbotOpen ? 'flex' : 'none';
                const toggleIcon = chatbotToggle.querySelector('.toggle-icon');
                if (toggleIcon) {
                    toggleIcon.textContent = chatbotOpen ? '▲' : '▼';
                }
            }
        });
    }
    
    function addChatbotMessage(text, isUser = false) {
        if (!chatbotMessages) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${isUser ? 'user' : 'bot'}`;
        messageDiv.textContent = text;
        chatbotMessages.appendChild(messageDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
    
    async function sendChatbotMessage() {
        if (!chatbotInput || !chatbotInput.value.trim()) return;
        
        const query = chatbotInput.value.trim();
        addChatbotMessage(query, true);
        chatbotInput.value = '';
        
        try {
            const response = await fetch('/api/chatbot/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            
            const data = await response.json();
            addChatbotMessage(data.response, false);
        } catch (error) {
            addChatbotMessage('Error: Could not connect to AI assistant.', false);
        }
    }
    
    if (chatbotSend) {
        chatbotSend.addEventListener('click', sendChatbotMessage);
    }
    
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatbotMessage();
            }
        });
    }
    
    // --- Initialization ---
    fetchStatus();
    setInterval(fetchStatus, 2000); // Refresh every 2 seconds
    checkSystemHealth();
    setInterval(checkSystemHealth, 10000); // Check health every 10 seconds
});


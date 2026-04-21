---
title: Falcon Ai Border Defence
emoji: 🦅
colorFrom: blue
colorTo: red
sdk: docker
app_file: app.py
pinned: false
---

# 🦅 Falcon AI: Autonomous Border Surveillance System

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![AI Model](https://img.shields.io/badge/AI-YOLOv11-red.svg)](https://github.com/ultralytics/ultralytics)

**Falcon AI** is a state-of-the-art autonomous surveillance solution designed for critical border monitoring. By leveraging real-time computer vision and tactical data analysis, Falcon AI aims to prevent civilian casualties and provide frontier forces with actionable intelligence.

---

## 🔭 Project Mission
The project was inspired by the tragic cases at the Bangladesh-India border (e.g., Felani Khatun). Our mission is to replace high-risk human patrolling with autonomous AI-driven monitoring, ensuring safety through technology.

---

## 🚀 Core Features

### 📡 Live Monitor & Virtual Fence
- **Real-time Detection**: Powered by **YOLOv11** for highly accurate person and object tracking.
- **Push-In/Push-Out Logic**: Intelligent virtual fence that distinguishes between border entry and exit.
- **NVIDIA Jetson Optimized**: Designed for high-performance edge computing.

### 📊 Intelligence Reports
- **Interactive Analytics**: Deep insights into threat trends using Chart.js.
- **Heatmaps**: Visualizing hourly activity intensity to identify peak threat times.
- **Exportable Data**: One-click tactical report generation in CSV format.

### 🤖 Tactical AI Assistant
- **Gemini Powered**: Intelligent chatbot providing real-time system diagnostics and strategic answers.
- **Context Aware**: Knows the current active tracks, system status, and recent threat events.

### 🔔 Smart Alerting
- **Twilio Integration**: Autonomous WhatsApp and SMS alerts sent to field commanders the moment a threat is verified.

---

## 🛠 Tech Stack
- **Vision**: YOLOv11 (Ultralytics)
- **Backend**: Python, Flask, Flask-SocketIO
- **Database**: MongoDB (Real-time alert storage)
- **AI/LLM**: Google Gemini 2.0 Flash
- **Alerts**: Twilio WhatsApp API
- **Frontend**: Glassmorphic UI (Vanilla CSS, JS)

---

## 📥 Installation

### 1. Prerequisites
- Python 3.10+
- MongoDB (running locally or via Atlas)
- Webcam (optional, defaults to video file)

### 2. Setup Workspace
```bash
# Clone the repository
git clone https://github.com/ShihabXSarar/AI-Based-Threat_Detection_for_Border_Surveillance.git
cd AI-Based-Threat-Detection-for-Border_Surveillance

# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and populate it with your credentials:
```env
SECRET_KEY=your_secret_key
GOOGLE_API_KEY=your_gemini_api_key
MONGO_URI=mongodb://localhost:27017/falcon_ai
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
FROM_NUMBER=whatsapp:+14155238886
TO_NUMBER=whatsapp:+YourPhoneNumber
GEMINI_MODEL=gemini-2.0-flash
```

---

## 🎮 Usage

### Launch System
```bash
python app.py
```
Visit `http://127.0.0.1:5000` to access the terminal.

### Operation Guide
1. **Live Monitor**: Watch real-time AI analysis. The system automatically detects intrusions across the virtual fence.
2. **Intel Reports**: View tactical charts and export historical alert logs.
3. **Tactical Assistant**: Use the bottom-right FAB to ask questions like *"What is the current threat level?"* or *"List today's alerts."*

---

## 📂 Project Organization
```text
/falcon_ai
  /app           # Flask Blueprints & Logic
  /config.py     # Environment & System Config
/static          # CSS, JS, and Asset files
/templates       # Professional UI Layouts
/uploads         # Video storage & Screenshots
app.py           # Application Entry Point
requirements.txt # Dependencies
.env             # Private Credentials (ignored by git)
```
New_Model: https://drive.google.com/drive/folders/1V9yxQIh9rRLbxMk2BJ4SOECFBkOMckXv?usp=sharing
---

## 🤝 Tactical Team
- **Shihab**: AI & System Architecture
- **Joynal**: Edge Computing & Hardware
- **Aditta**: Strategic Research

---

## ⚖️ License & Disclaimer
This project is for educational and humanitarian purposes. Ensure compliance with local border laws and data privacy regulations before deployment.

---
**Falcon AI — Secure the Frontier.**

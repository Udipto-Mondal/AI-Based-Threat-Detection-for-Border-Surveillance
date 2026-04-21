# Falcon AI - Border Defense System

A modular Flask application for AI-based threat detection using YOLOv11 and MongoDB.

## Architecture

```
falcon_ai/
├── app/
│   ├── __init__.py          # Flask app factory & DB connection
│   ├── auth.py              # Login/Register routes
│   ├── main.py              # Dashboard & Video routes
│   ├── analytics.py         # Data analysis & Graph routes
│   ├── chatbot.py           # Tactical Chatbot logic
│   ├── core.py              # The YOLO/OpenCV logic (Refactored)
│   ├── templates/
│   │   ├── base.html        # Master layout
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html   # The main view
│   │   └── analytics.html   # Deep dive graphs
│   └── static/
│       ├── css/             # Custom Sci-Fi styles
│       ├── js/              # Chart.js & dynamic logic
│       └── uploads/          # Video storage
├── config.py
├── run.py                   # Entry point
└── requirements.txt
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. MongoDB Setup

Make sure MongoDB is running on your system:

```bash
# Windows (if installed as service, it should auto-start)
# Or start manually:
mongod

# Linux/Mac
sudo systemctl start mongod
# or
mongod
```

The default connection string is: `mongodb://localhost:27017/falcon_ai`

You can override this by setting the `MONGODB_URI` environment variable.

### 3. Configuration

Edit `config.py` to update:
- Model path (`MODEL_PATH`)
- Default video source (`DEFAULT_SOURCE`)
- Twilio credentials (or set via environment variables)

### 4. Run the Application

```bash
python run.py
```

The application will be available at `http://127.0.0.1:5000`

## Features

### Phase 1: Foundation & Database
- ✅ Modular Flask application structure
- ✅ MongoDB integration with PyMongo
- ✅ Configuration management

### Phase 2: Authentication System
- ✅ User registration and login
- ✅ Password hashing with bcrypt
- ✅ Session management with Flask-Login
- ✅ Protected routes with `@login_required`

### Phase 3: Core Logic Integration
- ✅ YOLO surveillance logic in `app/core.py`
- ✅ MongoDB alerts collection
- ✅ Background video processing
- ✅ Twilio integration

### Phase 4: Tactical Dashboard
- ✅ 3-column grid layout (Navigation | Video | Stats)
- ✅ Live video feed with scanlines overlay
- ✅ REC indicator
- ✅ Real-time system load chart
- ✅ Threat alert log with auto-refresh
- ✅ Sci-Fi/Tactical aesthetic

### Phase 5: Data Analysis & Analytics
- ✅ Daily alert counts (last 7 days)
- ✅ Threat type distribution (doughnut chart)
- ✅ Activity heatmap (hourly)
- ✅ CSV export functionality

### Phase 6: Tactical AI Assistant
- ✅ Floating chat widget
- ✅ Rule-based intent parser
- ✅ Database query integration
- ✅ Terminal-style UI

### Phase 7: Polish & Impact
- ✅ Scanlines animation on video feed
- ✅ Alert sound effects (beep on critical alerts)
- ✅ Responsive design
- ✅ System health footer (MongoDB & Twilio status)

## Usage

1. **First Time Setup:**
   - Navigate to the application
   - Register a new user account
   - Log in with your credentials

2. **Dashboard:**
   - Click on the video feed or use controls to start analysis
   - Upload a video file, use webcam, or use default source
   - Monitor real-time alerts and system stats

3. **Analytics:**
   - Navigate to Analytics from the dashboard
   - View charts and data visualizations
   - Export reports as CSV

4. **Chatbot:**
   - Click the chatbot widget in the bottom right
   - Ask questions like:
     - "How many alerts today?"
     - "Show critical threats"
     - "System status?"

## Environment Variables

You can set these environment variables to override defaults:

- `SECRET_KEY` - Flask secret key
- `MONGODB_URI` - MongoDB connection string
- `MODEL_PATH` - Path to YOLO model file
- `DEFAULT_SOURCE` - Default video source path
- `TWILIO_SID` - Twilio Account SID
- `TWILIO_TOKEN` - Twilio Auth Token
- `FROM_NUMBER` - Twilio sender number
- `TO_NUMBER` - Twilio recipient number

## MongoDB Collections

The application uses the following collections:

- `users` - User accounts (username, email, password_hash, role)
- `alerts` - Threat alerts (timestamp, frame_id, track_id, type, message)

## Notes

- The model file path in `config.py` should point to your trained YOLO model
- Video uploads are stored in `app/static/uploads/`
- Make sure MongoDB is running before starting the application
- The application uses ByteTrack for object tracking

## Troubleshooting

1. **MongoDB Connection Error:**
   - Ensure MongoDB is running
   - Check the connection string in `config.py`
   - Verify MongoDB is accessible on port 27017

2. **Model Not Found:**
   - Update `MODEL_PATH` in `config.py`
   - Ensure the model file exists at the specified path

3. **Twilio Not Working:**
   - Check your Twilio credentials
   - Verify phone numbers are in correct format
   - Check Twilio account status

## License

This project is part of the AI-Based Threat Detection for Border Surveillance system.


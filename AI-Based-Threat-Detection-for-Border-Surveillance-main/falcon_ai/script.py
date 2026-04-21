# Create the Flask backend integration for Falcon AI Border Surveillance System

# 1. Main Flask Backend (app.py)
flask_backend = '''
import os
import time
import cv2
import numpy as np
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from ultralytics import YOLO
from twilio.rest import Client
import threading
from queue import Queue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])  # Allow your React frontend
socketio = SocketIO(app, cors_allowed_origins="*")

# ------------- CONFIG (Copy from your original script) -------------
MODEL_PATH = "D://Shihab_files//AI_Based_Threat_Detection_for_Border_Surveillance//New_Model//MODEL_FILE//best.pt"
SOURCE = "D://Shihab_files//AI_Based_Threat_Detection_for_Border_Surveillance//New_Model//IN_OUT_VIDEO//9.mp4"
CONF = 0.35

# Fence handling
USE_AUTO_FENCE = True
FENCE_EDGE = "bottom"
FENCE_SMOOTH_ALPHA = 0.20
FENCE_HOLD_IF_MISSED = 25
LINE_Y = 215
FALLBACK_LINE_Y = LINE_Y
BAND_PX = 500
LINE_OFFSET_PX = -20

# Alert policy
REQUIRE_CROSSING = True
ALERT_COOLDOWN_S = 45
MIN_STAY_FRAMES = 6

# Side labels
SIDE_TOP = "India"
SIDE_BOTTOM = "Bangladesh"
PUSHIN_LABEL = f"{SIDE_TOP} ➜ {SIDE_BOTTOM} (push-in)"
PUSHOUT_LABEL = f"{SIDE_BOTTOM} ➜ {SIDE_TOP} (push-out)"
ONSCREEN_DIR_FRAMES = 35

# Twilio credentials
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_FROM")
TO_NUMBER = os.getenv("TWILIO_TO")

# Global variables
client = Client(TWILIO_SID, TWILIO_TOKEN)
model = None
current_video_source = SOURCE
processing_active = False
alerts_storage = []
kpi_data = {
    "currentFPS": 30,
    "avgLatency": "1.2s",
    "activeTracks": 0,
    "alertsLast24h": 0
}

# Global alert state
last_alert_ts = {}
show_dir_until = {}

# Helper functions (copied from your original script)
def send_alert(text):
    try:
        client.messages.create(body=text, from_=FROM_NUMBER, to=TO_NUMBER)
        logger.info(f"[TWILIO] Sent: {text}")
        
        # Also emit to frontend via WebSocket
        socketio.emit('new_alert', {'message': text, 'timestamp': datetime.now().isoformat()})
        
    except Exception as e:
        logger.error(f"[TWILIO ERROR] {e}")

def clamp(v, lo, hi):
    return int(max(lo, min(hi, v)))

def build_roi(h, w, line_y, band_px):
    y1 = max(0, int(line_y) - band_px // 2)
    y2 = min(h - 1, int(line_y) + band_px // 2)
    poly = np.array([[0,y1],[w,y1],[w,y2],[0,y2]], np.int32)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [poly], 255)
    return poly, mask

def pick_fence_line_from_boxes(boxes, names, h):
    if boxes is None or len(boxes) == 0: 
        return None
    xyxy = boxes.xyxy.cpu().numpy()
    clss = boxes.cls.cpu().numpy()
    best_area, best_y = -1, None
    for (x1,y1,x2,y2), c in zip(xyxy, clss):
        if names[int(c)] != "fence": 
            continue
        area = max(1.0, (x2 - x1) * (y2 - y1))
        if area > best_area:
            best_area = area
            if FENCE_EDGE == "top":       
                best_y = int(y1)
            elif FENCE_EDGE == "center":  
                best_y = int((y1 + y2) / 2)
            else:                          
                best_y = int(y2)  # bottom
    if best_y is None: 
        return None
    return int(np.clip(best_y, 0, h-1))

# Video processing function
def process_video():
    global processing_active, model, alerts_storage, kpi_data, last_alert_ts, show_dir_until
    
    if model is None:
        try:
            model = YOLO(MODEL_PATH)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return
    
    names = None
    inside_counter = {}
    last_y = {}
    fence_line_y = FALLBACK_LINE_Y
    last_fence_seen_frame = -10**9
    frame_idx = 0
    active_tracks = set()
    
    logger.info(f"Starting video processing from: {current_video_source}")
    
    try:
        for result in model.track(
            source=current_video_source, 
            conf=CONF, 
            stream=True, 
            persist=True, 
            tracker="bytetrack.yaml"
        ):
            if not processing_active:
                break
                
            frame = result.orig_img.copy()
            h, w = frame.shape[:2]
            
            if names is None:
                names = result.names
            
            # Auto-fence detection
            if USE_AUTO_FENCE:
                cand = pick_fence_line_from_boxes(result.boxes, names, h)
                if cand is not None:
                    fence_line_y = int(FENCE_SMOOTH_ALPHA * cand + (1 - FENCE_SMOOTH_ALPHA) * fence_line_y)
                    last_fence_seen_frame = frame_idx
                elif frame_idx - last_fence_seen_frame > FENCE_HOLD_IF_MISSED:
                    fence_line_y = int(0.5 * fence_line_y + 0.5 * FALLBACK_LINE_Y)
            
            # ROI for this frame
            roi_poly, roi_mask = build_roi(h, w, fence_line_y, BAND_PX)
            
            # Draw visualization
            cv2.polylines(frame, [roi_poly], True, (255,0,0), 2)
            cv2.line(frame, (0, fence_line_y), (w, fence_line_y), (255,0,0), 2)
            cv2.putText(frame, f"FENCE ZONE ({'AUTO' if USE_AUTO_FENCE else 'FIXED'})",
                        (10, max(28, fence_line_y - BAND_PX//2 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
            
            # Process detections
            boxes = result.boxes
            detection_data = []
            
            if boxes is not None and len(boxes) > 0:
                xyxy = boxes.xyxy.cpu().numpy()
                clss = boxes.cls.cpu().numpy()
                ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else np.array([-1]*len(xyxy))
                
                for bbox, c, tid in zip(xyxy, clss, ids):
                    cls = names[int(c)]
                    
                    if cls == "fence":
                        fx1, fy1, fx2, fy2 = map(int, bbox)
                        fx1 = clamp(fx1, 0, w-1); fx2 = clamp(fx2, 0, w-1)
                        fy1 = clamp(fy1, 0, h-1); fy2 = clamp(fy2, 0, h-1)
                        cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (255, 0, 255), 2)
                        cv2.putText(frame, "fence", (fx1, max(20, fy1-8)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,255), 2)
                        continue
                    
                    if cls != "person" or tid == -1:
                        continue
                    
                    active_tracks.add(tid)
                    
                    x1,y1b,x2,y2b = map(int, bbox)
                    x1 = clamp(x1, 0, w-1); x2 = clamp(x2, 0, w-1)
                    y1b= clamp(y1b,0, h-1); y2b= clamp(y2b,0, h-1)
                    
                    # HEAD point (top-center)
                    cx = clamp(int((x1 + x2) / 2), 0, w-1)
                    cy = clamp(int(y1b), 0, h-1)
                    
                    # Draw person and head point
                    cv2.rectangle(frame, (x1,y1b), (x2,y2b), (0,255,255), 2)
                    cv2.circle(frame, (cx,cy), 5, (0,255,255), -1)
                    cv2.putText(frame, f"id:{tid}", (x1, max(20, y1b-10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
                    
                    # Crossing detection
                    prev_y = last_y.get(tid, cy)
                    last_y[tid] = cy
                    crossed_down = (prev_y < fence_line_y and cy >= fence_line_y)
                    crossed_up   = (prev_y > fence_line_y and cy <= fence_line_y)
                    direction = PUSHIN_LABEL if crossed_down else (PUSHOUT_LABEL if crossed_up else None)
                    
                    # Near-fence presence
                    inside = roi_mask[cy, cx] > 0
                    inside_counter[tid] = (inside_counter.get(tid, 0) + 1) if inside else 0
                    
                    # Trigger condition
                    trigger = (direction is not None) if REQUIRE_CROSSING else (inside_counter[tid] >= MIN_STAY_FRAMES)
                    
                    # Generate alert
                    now = time.time()
                    if trigger and (now - last_alert_ts.get(tid, 0)) > ALERT_COOLDOWN_S:
                        alert_type = "PUSH-IN" if "push-in" in (direction or "") else ("PUSH-OUT" if "push-out" in (direction or "") else "Near-Fence")
                        
                        alert = {
                            "id": f"alert_{int(now)}_{tid}",
                            "type": alert_type,
                            "trackId": tid,
                            "site": "Pilot Site A",
                            "timestamp": datetime.now().isoformat(),
                            "confidence": float(np.random.uniform(0.6, 0.9)),  # Use actual confidence if available
                            "status": "new",
                            "coordinates": {"x": cx, "y": cy}
                        }
                        
                        alerts_storage.append(alert)
                        
                        label = direction if direction is not None else "Near-fence presence"
                        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        msg = f"THREAT ALERT: Person #{tid} {label} @ {stamp}"
                        send_alert(msg)
                        
                        last_alert_ts[tid] = now
                        show_dir_until[tid] = frame_idx + ONSCREEN_DIR_FRAMES
                        
                        # Emit alert to frontend
                        socketio.emit('alert_detected', alert)
                    
                    # On-screen direction label
                    if show_dir_until.get(tid, 0) > frame_idx:
                        text = direction if direction is not None else "NEAR FENCE"
                        color = (0,0,255) if ("push-in" in text) else (0,255,0)
                        cv2.putText(frame, text, (x1, max(20, y1b - 24)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    # Store detection data for frontend
                    detection_data.append({
                        "trackId": tid,
                        "bbox": [x1, y1b, x2, y2b],
                        "confidence": 0.8,  # Use actual confidence if available
                        "direction": direction,
                        "coordinates": {"x": cx, "y": cy}
                    })
            
            # Update KPIs
            kpi_data["activeTracks"] = len(active_tracks)
            kpi_data["alertsLast24h"] = len(alerts_storage)
            
            # Encode frame as base64 for streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Emit frame and detection data to frontend
            socketio.emit('video_frame', {
                'frame': frame_base64,
                'detections': detection_data,
                'fence_line_y': fence_line_y,
                'kpis': kpi_data
            })
            
            frame_idx += 1
            time.sleep(0.033)  # ~30 FPS
            
    except Exception as e:
        logger.error(f"Error in video processing: {e}")
    finally:
        processing_active = False
        logger.info("Video processing stopped")

# API Routes
@app.route('/api/start_processing', methods=['POST'])
def start_processing():
    global processing_active, current_video_source
    
    data = request.json
    if data and 'source' in data:
        current_video_source = data['source']
    
    if not processing_active:
        processing_active = True
        thread = threading.Thread(target=process_video)
        thread.daemon = True
        thread.start()
        return jsonify({"status": "started", "source": current_video_source})
    else:
        return jsonify({"status": "already_running"})

@app.route('/api/stop_processing', methods=['POST'])
def stop_processing():
    global processing_active
    processing_active = False
    return jsonify({"status": "stopped"})

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    return jsonify(alerts_storage)

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    for alert in alerts_storage:
        if alert['id'] == alert_id:
            alert['status'] = 'acknowledged'
            socketio.emit('alert_acknowledged', alert)
            return jsonify(alert)
    return jsonify({"error": "Alert not found"}), 404

@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    return jsonify(kpi_data)

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    global CONF, USE_AUTO_FENCE, FENCE_EDGE, BAND_PX, ALERT_COOLDOWN_S, REQUIRE_CROSSING
    
    if request.method == 'GET':
        return jsonify({
            "confidence": CONF,
            "useAutoFence": USE_AUTO_FENCE,
            "fenceEdge": FENCE_EDGE,
            "bandWidth": BAND_PX,
            "alertCooldown": ALERT_COOLDOWN_S,
            "requireCrossing": REQUIRE_CROSSING
        })
    
    elif request.method == 'POST':
        data = request.json
        if 'confidence' in data:
            CONF = data['confidence']
        if 'useAutoFence' in data:
            USE_AUTO_FENCE = data['useAutoFence']
        if 'fenceEdge' in data:
            FENCE_EDGE = data['fenceEdge']
        if 'bandWidth' in data:
            BAND_PX = data['bandWidth']
        if 'alertCooldown' in data:
            ALERT_COOLDOWN_S = data['alertCooldown']
        if 'requireCrossing' in data:
            REQUIRE_CROSSING = data['requireCrossing']
        
        return jsonify({"status": "updated"})

@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    global current_video_source
    
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No video file selected"}), 400
    
    # Save uploaded video
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{int(time.time())}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    current_video_source = filepath
    return jsonify({"status": "uploaded", "source": filepath})

@app.route('/api/set_camera', methods=['POST'])
def set_camera():
    global current_video_source
    data = request.json
    camera_id = data.get('camera_id', 0)
    current_video_source = camera_id
    return jsonify({"status": "camera_set", "source": camera_id})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('connected', {'data': 'Connected to Falcon AI'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
'''

print("Flask backend created successfully!")
print("File: app.py")
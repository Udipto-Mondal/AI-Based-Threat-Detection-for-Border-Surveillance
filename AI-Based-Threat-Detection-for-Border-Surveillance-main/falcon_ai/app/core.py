"""
Core YOLO surveillance logic - Refactored from original app.py
"""
import cv2
import numpy as np
import os
import time
import threading
from datetime import datetime
from ultralytics import YOLO
from twilio.rest import Client
from . import mongo
from falcon_ai.config import Config

# Global state
model = None
current_source = Config.DEFAULT_SOURCE
processing_active = threading.Event()
processing_active.set()
processing_thread = None
system_stats = {
    'total_alerts': 0,
    'critical_alerts': 0,
    'system_status': "INITIALIZING",
    'fps': 0,
    'frame_count': 0,
    'active_tracks': 0
}
last_alert_ts = {}
show_dir_until = {}
global_alert_cooldown_until = 0

# Twilio Client
twilio_client = None
try:
    twilio_client = Client(Config.TWILIO_SID, Config.TWILIO_TOKEN)
    print("✅ Twilio client initialized successfully.")
except Exception as e:
    print(f"❌ Twilio client failed to initialize: {e}")


def clamp(v, lo, hi):
    return int(max(lo, min(hi, v)))


def build_roi(h, w, line_y, band_px):
    y1 = max(0, int(line_y) - band_px // 2)
    y2 = min(h - 1, int(line_y) + band_px // 2)
    poly = np.array([[0, y1], [w, y1], [w, y2], [0, y2]], np.int32)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [poly], 255)
    return poly, mask


def pick_fence_line_from_boxes(boxes, names, h):
    if boxes is None or len(boxes) == 0:
        return None
    try:
        xyxy, clss = boxes.xyxy.cpu().numpy(), boxes.cls.cpu().numpy()
        best_area, best_y = -1, None
        for (x1, y1, x2, y2), c in zip(xyxy, clss):
            if names[int(c)] != "fence":
                continue
            area = (x2 - x1) * (y2 - y1)
            if area > best_area:
                best_area = area
                if Config.FENCE_EDGE == "top":
                    best_y = int(y1)
                elif Config.FENCE_EDGE == "center":
                    best_y = int((y1 + y2) / 2)
                else:
                    best_y = int(y2)
        return int(np.clip(best_y, 0, h - 1)) if best_y is not None else None
    except Exception:
        return None


def send_alert(frame_idx, track_id, alert_type, message, user_id=None, frame=None):
    """Send alert to MongoDB and Twilio"""
    global system_stats
    
    timestamp = datetime.utcnow()
    image_filename = None
    
    # Save Screenshot if frame is provided and it's an upload (user_id present)
    if frame is not None and user_id is not None:
        try:
            # Create screenshots directory if not exists
            screenshots_dir = os.path.join(Config.UPLOAD_FOLDER, 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate filename
            image_filename = f"{user_id}_{timestamp.strftime('%Y%m%d%H%M%S')}_{track_id}.jpg"
            image_path = os.path.join(screenshots_dir, image_filename)
            
            # Save image
            cv2.imwrite(image_path, frame)
        except Exception as e:
            print(f"❌ Failed to save screenshot: {e}")

    # Save to MongoDB
    alert_doc = {
        'timestamp': timestamp,
        'frame_id': int(frame_idx),
        'track_id': int(track_id),
        'type': alert_type,
        'message': message,
        'image_path': image_filename, # Store filename only
        'user_id': user_id
    }
    
    try:
        if user_id:
            mongo.db.upload_alerts.insert_one(alert_doc)
            print(f"🚨 UPLOAD ALERT SAVED: {message} (User: {user_id})")
        else:
            mongo.db.alerts.insert_one(alert_doc)
            print(f"🚨 SYSTEM ALERT SAVED: {message}")
    except Exception as e:
        print(f"❌ Failed to save alert to DB: {e}")
    
    # Update stats (Global stats only update for system-wide alerts or if we decide to aggregate all)
    # For now, we'll keep global stats for the "Live Monitor" (user_id=None)
    if user_id is None:
        system_stats['total_alerts'] += 1
        if "PUSH-IN" in alert_type:
            system_stats['critical_alerts'] += 1
    
    # Send Twilio notification (Only for System Alerts to avoid spamming from user uploads)
    if twilio_client and user_id is None:
        try:
            twilio_message = f"🚨 FALCONAI THREAT: {message}"
            twilio_client.messages.create(
                body=twilio_message,
                from_=Config.FROM_NUMBER,
                to=Config.TO_NUMBER
            )
            print(f"✅ Sent Twilio alert to {Config.TO_NUMBER}")
        except Exception as e:
            print(f"❌ Failed to send Twilio alert: {e}")


def load_model():
    """Load YOLO model"""
    global model
    if not os.path.exists(Config.MODEL_PATH):
        print(f"❌ MODEL NOT FOUND at {Config.MODEL_PATH}")
        return False
    try:
        print(f"🚀 Loading YOLO model from: {Config.MODEL_PATH}")
        model = YOLO(Config.MODEL_PATH)
        print("✅ YOLO model loaded successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False


def process_detection(frame, result, frame_idx, user_id=None, state=None):
    """
    Reusable detection logic for both live stream and uploads.
    Returns: Annotated frame
    """
    global last_alert_ts, show_dir_until, global_alert_cooldown_until
    
    if state is None:
        state = {
            'last_y': {},
            'inside_counter': {},
            'fence_line_y': Config.FALLBACK_LINE_Y,
            'last_fence_seen_frame': -10**9
        }

    h, w = frame.shape[:2]
    names = result.names
    
    # Fence Logic
    cand = pick_fence_line_from_boxes(result.boxes, names, h)
    if cand is not None:
        # Smooth fence line if live, or just take it if confident
        # For consistency, we'll use the smoothing logic if state persists
        state['fence_line_y'] = int(
            Config.FENCE_SMOOTH_ALPHA * cand +
            (1 - Config.FENCE_SMOOTH_ALPHA) * state['fence_line_y']
        )
        state['last_fence_seen_frame'] = frame_idx
    
    fence_line_y = state['fence_line_y']
    
    # Decide whether to draw fence
    draw_fence = False
    if user_id is None: # Live feed (webcam or video) logic
        is_webcam = (current_source == 'webcam' or current_source == 0)
        if is_webcam:
             if cand is not None: draw_fence = True
        else:
             if cand is not None or (frame_idx - state['last_fence_seen_frame'] <= Config.FENCE_HOLD_IF_MISSED):
                 draw_fence = True
    else: # Upload logic - always draw if we have a line
        draw_fence = True

    roi_mask = np.zeros((h, w), dtype=np.uint8)
    if draw_fence and Config.USE_AUTO_FENCE:
        roi_poly, roi_mask = build_roi(h, w, fence_line_y, Config.BAND_PX)
        cv2.polylines(frame, [roi_poly], True, (0, 255, 255), 2)
        cv2.line(frame, (0, fence_line_y), (w, fence_line_y), (0, 0, 255), 2)
        cv2.putText(
            frame, "FENCE ZONE",
            (10, max(28, fence_line_y - Config.BAND_PX // 2 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
        )
    
    active_tracks_this_frame = set()
    boxes = result.boxes
    if boxes is not None and len(boxes) > 0:
        xyxy, clss = boxes.xyxy.cpu().numpy(), boxes.cls.cpu().numpy()
        ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else []
        
        for bbox, cls_id, tid in zip(xyxy, clss, ids):
            cls_name = names[int(cls_id)]
            x1, y1, x2, y2 = map(int, bbox)
            
            if cls_name == "fence":
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
                continue
            
            if cls_name != "person":
                continue
            
            active_tracks_this_frame.add(tid)
            head_x = clamp((x1 + x2) // 2, 0, w - 1)
            head_y = clamp(y1, 0, h - 1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame, f"ID:{tid}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )
            
            # Logic for crossing (Push-In / Push-Out)
            if draw_fence and Config.USE_AUTO_FENCE:
                prev_y = state['last_y'].get(tid, head_y)
                state['last_y'][tid] = head_y
                
                crossed_down = (prev_y < fence_line_y and head_y >= fence_line_y)
                crossed_up = (prev_y > fence_line_y and head_y <= fence_line_y)
                
                direction = (
                    Config.PUSHIN_LABEL if crossed_down else
                    (Config.PUSHOUT_LABEL if crossed_up else None)
                )
                
                inside = roi_mask[head_y, head_x] > 0
                state['inside_counter'][tid] = (state['inside_counter'].get(tid, 0) + 1) if inside else 0
                
                # Trigger Logic
                # For Live: Respect Config.REQUIRE_CROSSING
                # For Uploads: Always trigger if inside zone (ignore crossing requirement) to show "Instant Insights"
                if user_id is not None:
                    trigger = (state['inside_counter'][tid] >= Config.MIN_STAY_FRAMES) or (direction is not None)
                else:
                    trigger = (
                        (direction is not None) if Config.REQUIRE_CROSSING else
                        (state['inside_counter'][tid] >= Config.MIN_STAY_FRAMES)
                    )
                
                # Cooldown Logic
                # For uploads (user_id is set), use frame-based cooldown from state
                # For live (user_id is None), use global time-based cooldown
                
                should_alert = False
                now = time.time()
                
                if user_id is not None:
                    # Upload Logic: Frame-based cooldown
                    last_alert_frame = state.get('last_alert_frame', {}).get(tid, -1000)
                    if frame_idx - last_alert_frame > Config.ONSCREEN_DIR_FRAMES: # Reuse this constant or define a new one
                        should_alert = True
                else:
                    # Live Logic: Time-based cooldown
                    if now >= global_alert_cooldown_until:
                        should_alert = True

                if trigger and should_alert:
                    alert_label = (
                        direction.split('(')[-1].replace(')', '').strip()
                        if direction else "NEAR-FENCE"
                    )
                    message = f"ID:{tid} triggered a {alert_label} event."
                    
                    # Pass frame for screenshot saving
                    send_alert(frame_idx, tid, alert_label, message, user_id, frame)
                    
                    if user_id is not None:
                         if 'last_alert_frame' not in state: state['last_alert_frame'] = {}
                         state['last_alert_frame'][tid] = frame_idx
                    else:
                        last_alert_ts[tid] = now
                        global_alert_cooldown_until = now + Config.ALERT_COOLDOWN_S
                    
                    show_dir_until[tid] = frame_idx + Config.ONSCREEN_DIR_FRAMES
                
                if show_dir_until.get(tid, 0) > frame_idx:
                    label_text = (
                        direction.split('(')[-1].replace(')', '').strip()
                        if direction else "NEAR FENCE"
                    )
                    # If direction is None (just lingering), fallback to last known or generic
                    # But here 'direction' is only set on crossing frame. 
                    # We need to persist the label? The original code re-calculated direction every frame?
                    # No, original code: `if show_dir_until...` used `direction` variable which might be None!
                    # Wait, original code had `direction` in scope. 
                    # We should probably store the last event label in state or use a simplified approach.
                    # For now, let's just show "ALERT" or re-use the label if we can.
                    # Actually, let's just show "INTRUSION" or "CROSSING" if we don't have the specific label persisted.
                    # Or better, let's trust the `alert_label` we just calculated if trigger happened.
                    
                    # Fix: The original code relied on `direction` being available in the loop.
                    # If we are just showing the label for N frames, we need to know WHAT label.
                    # Let's skip the specific label for the "lingering" display to avoid complex state,
                    # or just show "THREAT DETECTED".
                    
                    color = (50, 50, 255) 
                    cv2.putText(
                        frame, "THREAT DETECTED",
                        (x1, y1 - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
                    )

    return frame


def generate_frames(user_id=None):
    """Generator function for video frames with YOLO detection (Live System)"""
    global system_stats
    
    if model is None:
        return
    
    video_source = 0 if current_source == 'webcam' else current_source
    if video_source != 0 and not os.path.exists(video_source):
        print(f"❌ Video source not found: {video_source}")
        return
    
    print(f"🎬 Starting AI detection on: {video_source}")
    
    frame_idx, start_time = 0, time.time()
    system_stats['system_status'] = "ANALYSIS ACTIVE"
    
    # Initialize state for this stream
    state = {
        'last_y': {},
        'inside_counter': {},
        'fence_line_y': Config.FALLBACK_LINE_Y,
        'last_fence_seen_frame': -10**9
    }
    
    try:
        for result in model.track(
            source=video_source,
            conf=Config.CONF,
            stream=True,
            persist=True,
            tracker="bytetrack.yaml"
        ):
            if not processing_active.is_set():
                break
            
            frame = result.orig_img.copy()
            frame_idx += 1
            
            # Use the shared detection logic
            frame = process_detection(frame, result, frame_idx, user_id=None, state=state)
            
            # Update global stats
            system_stats.update({
                'frame_count': frame_idx,
                'fps': round(frame_idx / (time.time() - start_time), 1) if frame_idx > 0 else 0
            })
            
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    except Exception as e:
        print(f"❌ Error during frame generation: {e}")
    finally:
        system_stats['system_status'] = "ANALYSIS COMPLETE"
        print("🎥 Video stream finished.")


def generate_frames_for_upload(video_path, user_id):
    """Generator for uploaded videos - Isolated from system stats"""
    if model is None:
        return

    print(f"🎬 Starting Upload Analysis for User {user_id}: {video_path}")
    
    # Initialize state for this stream
    state = {
        'last_y': {},
        'inside_counter': {},
        'fence_line_y': Config.FALLBACK_LINE_Y,
        'last_fence_seen_frame': -10**9
    }
    
    try:
        # Use a separate tracker instance implicitly by calling model.track
        for i, result in enumerate(model.track(
            source=video_path,
            conf=Config.CONF,
            stream=True,
            persist=True,
            tracker="bytetrack.yaml"
        )):
            frame = result.orig_img.copy()
            
            # Process detection with user_id
            frame = process_detection(frame, result, i, user_id=user_id, state=state)
            
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                   
    except Exception as e:
        print(f"❌ Error during upload analysis: {e}")


def _run_analysis_loop(user_id=None):
    """Background loop that consumes the generator to trigger alerts."""
    for _ in generate_frames(user_id=user_id):
        if not processing_active.is_set():
            break


def start_processing_thread(source):
    """Start video processing in background thread"""
    global processing_thread, current_source
    current_source = source
    
    if processing_thread and processing_thread.is_alive():
        processing_active.clear()
        processing_thread.join()
    
    processing_active.set()
    # Live feed always runs as System (user_id=None)
    processing_thread = threading.Thread(target=_run_analysis_loop, kwargs={'user_id': None}, daemon=True)
    processing_thread.start()


def get_system_stats():
    """Get current system statistics"""
    return system_stats.copy()


def get_latest_alerts(limit=50):
    """Get latest alerts from MongoDB"""
    try:
        alerts = list(mongo.db.alerts.find().sort('timestamp', -1).limit(limit))
        # Convert ObjectId to string and format timestamp
        for alert in alerts:
            alert['_id'] = str(alert['_id'])
            alert['time'] = alert['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            alert['frame'] = alert['frame_id']
            alert['track_id'] = alert['track_id']
            alert['alert'] = alert['type']
        return alerts
    except Exception as e:
        print(f"❌ Error fetching alerts: {e}")
        return []


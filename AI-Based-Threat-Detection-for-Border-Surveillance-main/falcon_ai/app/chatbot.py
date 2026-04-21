"""
app/chatbot.py - Intelligent Tactical Assistant using Gemini Flash
"""
import os
import google.generativeai as genai
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from datetime import datetime, timedelta
from . import mongo
from .core import get_system_stats

bp = Blueprint('chatbot', __name__)

# --- Configuration ---
def configure_genai():
    api_key = current_app.config.get("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        print("⚠️ GOOGLE_API_KEY not found in config.")

# --- Project Knowledge Base ---
PROJECT_CONTEXT = """
You are the Tactical AI Assistant for Project Falcon AI.
MISSION: Autonomous border surveillance to prevent civilian deaths (e.g., Felani Khatun case) at the Bangladesh-India border.
TECH STACK: YOLOv11 (Vision), NVIDIA Jetson (Edge Compute), Twilio (Alerts), MongoDB (Data), Flask (Backend).
FEATURES: Virtual Fence (detects PUSH-IN vs PUSH-OUT), Autonomous Drone Fleet.
TEAM: Shihab (AI Lead), Joynal (Edge Systems), Aditta (Research), Sumaiya (Frontend).
TONE: Professional, Military/Tactical, Concise.
"""

# --- Helper Functions (The "Tools") ---
def get_live_data_context():
    """Fetches real-time DB stats to feed into the LLM"""
    try:
        # 1. Get Stats
        stats = get_system_stats()
        
        # 2. Get Today's Alerts Count
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        alert_count = mongo.db.alerts.count_documents({'timestamp': {'$gte': today_start}})
        push_in_count = mongo.db.alerts.count_documents({'timestamp': {'$gte': today_start}, 'type': 'PUSH-IN'})
        push_out_count = mongo.db.alerts.count_documents({'timestamp': {'$gte': today_start}, 'type': 'PUSH-OUT'})
        
        # 3. Get Latest Critical Threat
        latest_threat = mongo.db.alerts.find_one({'type': 'PUSH-IN'}, sort=[('timestamp', -1)])
        threat_msg = latest_threat['message'] if latest_threat else "None"
        
        return (
            f"[SYSTEM DATA]:\n"
            f"- System Status: {stats.get('system_status')}\n"
            f"- Active Tracks: {stats.get('active_tracks')}\n"
            f"- Alerts Today: {alert_count}\n"
            f"- Push-In Events: {push_in_count}\n"
            f"- Push-Out Events: {push_out_count}\n"
            f"- Last Critical Threat: {threat_msg}\n"
        )
    except Exception as e:
        return f"[SYSTEM DATA ERROR]: {str(e)}"

@bp.route('/query', methods=['POST'])
@login_required
def query():
    try:
        data = request.get_json()
        if not data:
             return jsonify({'response': 'Invalid request format.'}), 400
             
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'response': 'Awaiting orders, Commander.'})

        # Ensure GenAI is configured (lazy init to access current_app)
        configure_genai()

        # 1. Fetch live system data (RAG - Retrieval Augmented Generation)
        live_context = get_live_data_context()
        
        # 2. Construct the full prompt
        full_prompt = (
            f"{PROJECT_CONTEXT}\n\n"
            f"{live_context}\n\n"
            f"USER QUERY: {user_query}\n"
            f"RESPONSE:"
        )

        # 3. Call Gemini API
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(full_prompt)
        
        return jsonify({'response': response.text})

    except Exception as e:
        error_msg = str(e)
        print(f"Chatbot Error: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg.lower():
            return jsonify({'response': "⚠ API Quota Exceeded. Please try again later or switch to another model in .env (e.g., gemini-1.5-flash)."})
        
        return jsonify({'response': "⚠ Communication Link Failure. Check connectivity or API key."})

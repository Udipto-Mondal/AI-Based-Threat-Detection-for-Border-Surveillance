"""
Main blueprint for dashboard and video feed routes
"""
from flask import Blueprint, render_template, Response, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .core import (
    start_processing_thread, generate_frames,
    get_system_stats, get_latest_alerts,
    last_alert_ts, global_alert_cooldown_until, system_stats
)
from falcon_ai.config import Config

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Landing page"""
    return render_template('landing.html')


@bp.route('/live')
@login_required
def live_monitor():
    """Live surveillance monitor"""
    return render_template('live_monitor.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """Legacy dashboard route - redirect to live monitor"""
    return redirect(url_for('main.live_monitor'))


@bp.route('/video_feed')
@login_required
def video_feed():
    """Video feed stream route"""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@bp.route('/api/status')
@login_required
def api_status():
    """API endpoint for system status and alerts"""
    stats = get_system_stats()
    alerts = get_latest_alerts(limit=50)
    
    return jsonify({
        'stats': stats,
        'alerts': alerts
    })


@bp.route('/api/initiate_analysis', methods=['POST'])
@login_required
def initiate_analysis():
    """API endpoint to start video analysis"""
    # Reset alert tracking
    last_alert_ts.clear()
    global_alert_cooldown_until = 0
    system_stats.update({'total_alerts': 0, 'critical_alerts': 0})
    
    source_type = 'default'
    if request.is_json:
        source_type = request.get_json().get('source', 'default')
    
    source = Config.DEFAULT_SOURCE
    
    if 'file' in request.files:
        file = request.files['file']
        if file.filename:
            filename = secure_filename(file.filename)
            filepath = Config.get_upload_path(filename)
            file.save(filepath)
            source = filepath
            print(f"📁 Switched to uploaded file: {filename}")
    elif source_type == 'webcam':
        source = 'webcam'
        print("📹 Switching to webcam feed.")
    else:
        source = Config.DEFAULT_SOURCE
        print(f"🔄 Resetting to default video source.")
    
    start_processing_thread(source)
    return jsonify({
        'status': 'success',
        'message': f'Analysis started on {source}'
    })


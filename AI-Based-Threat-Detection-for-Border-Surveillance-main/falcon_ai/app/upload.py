"""
Blueprint for Video Uploads and Analysis
"""
import os
from flask import Blueprint, render_template, request, Response, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .core import generate_frames_for_upload

bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Upload page"""
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['video']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Save with user_id prefix to avoid collisions
            unique_filename = f"{current_user.id}_{filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            
            try:
                file.save(upload_path)
                flash('Video uploaded successfully. Starting analysis...', 'success')
                return render_template('upload_analytics.html', video_filename=unique_filename)
            except Exception as e:
                flash(f'Error saving file: {e}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Allowed: mp4, avi, mov, mkv', 'error')
            return redirect(request.url)

    return render_template('upload_analytics.html', video_filename=None)


@bp.route('/stream/<filename>')
@login_required
def stream_upload(filename):
    """Stream processed video for the specific upload"""
    # Security check: ensure user is accessing their own file
    if not filename.startswith(str(current_user.id) + "_"):
        return "Unauthorized", 403
        
    video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(video_path):
        return "Video not found", 404

    return Response(
        generate_frames_for_upload(video_path, current_user.id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@bp.route('/screenshots/<filename>')
@login_required
def get_screenshot(filename):
    """Serve screenshot image"""
    # Security: Ensure user can only access their own screenshots
    if not filename.startswith(str(current_user.id) + "_"):
        return "Unauthorized", 403
        
    from flask import send_from_directory
    screenshots_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'screenshots')
    return send_from_directory(screenshots_dir, filename)


@bp.route('/api/alerts')
@login_required
def get_upload_alerts():
    """Get latest alerts for the current user (Instant Insights)"""
    try:
        # Fetch last 20 alerts for this user from the dedicated upload_alerts collection
        from . import mongo
        alerts = list(mongo.db.upload_alerts.find(
            {'user_id': current_user.id}
        ).sort('timestamp', -1).limit(20))
        
        results = []
        for a in alerts:
            image_url = None
            if a.get('image_path'):
                image_url = url_for('upload.get_screenshot', filename=a['image_path'])
                
            results.append({
                'time': a['timestamp'].strftime('%H:%M:%S'),
                'message': a['message'],
                'type': a['type'],
                'image': image_url
            })
        
        return {'alerts': results}
    except Exception as e:
        print(f"Error fetching upload alerts: {e}")
        return {'alerts': []}

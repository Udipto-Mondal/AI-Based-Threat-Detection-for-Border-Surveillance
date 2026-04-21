"""
Analytics blueprint for data analysis and visualization
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from . import mongo
from bson import ObjectId

bp = Blueprint('analytics', __name__)


@bp.route('/')
@login_required
def analytics():
    """Analytics dashboard page"""
    return render_template('long_term_analytics.html')


@bp.route('/api/daily')
@login_required
def api_daily():
    """Get daily alert counts for last 7 days (User Specific)"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        pipeline = [
            {
                '$match': {
                    '$or': [
                        {'user_id': current_user.id},
                        {'user_id': None}
                    ],
                    'timestamp': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$timestamp'
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id': 1}
            }
        ]
        
        results = list(mongo.db.alerts.aggregate(pipeline))
        
        # Format for Chart.js
        labels = [r['_id'] for r in results]
        data = [r['count'] for r in results]
        
        return jsonify({
            'labels': labels,
            'data': data
        })
    except Exception as e:
        print(f"❌ Error in daily analytics: {e}")
        return jsonify({'labels': [], 'data': []}), 500


@bp.route('/api/types')
@login_required
def api_types():
    """Get alert type distribution (User Specific)"""
    try:
        pipeline = [
            {
                '$match': {
                    '$or': [
                        {'user_id': current_user.id},
                        {'user_id': None}
                    ]
                }
            },
            {
                '$group': {
                    '_id': '$type',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        results = list(mongo.db.alerts.aggregate(pipeline))
        
        labels = [r['_id'] for r in results]
        data = [r['count'] for r in results]
        
        return jsonify({
            'labels': labels,
            'data': data
        })
    except Exception as e:
        print(f"❌ Error in types analytics: {e}")
        return jsonify({'labels': [], 'data': []}), 500


@bp.route('/api/heatmap')
@login_required
def api_heatmap():
    """Get hourly activity heatmap (User Specific)"""
    try:
        pipeline = [
            {
                '$match': {
                    '$or': [
                        {'user_id': current_user.id},
                        {'user_id': None}
                    ]
                }
            },
            {
                '$group': {
                    '_id': {
                        '$hour': '$timestamp'
                    },
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id': 1}
            }
        ]
        
        results = list(mongo.db.alerts.aggregate(pipeline))
        
        # Create array for all 24 hours
        hours = [0] * 24
        for r in results:
            hours[r['_id']] = r['count']
        
        labels = [f"{h:02d}:00" for h in range(24)]
        
        return jsonify({
            'labels': labels,
            'data': hours
        })
    except Exception as e:
        print(f"❌ Error in heatmap analytics: {e}")
        return jsonify({'labels': [], 'data': []}), 500


@bp.route('/api/export')
@login_required
def api_export():
    """Export all alerts as CSV (User Specific)"""
    try:
        # Filter by current_user.id OR system-wide alerts (None)
        alerts = list(mongo.db.alerts.find({
            '$or': [
                {'user_id': current_user.id},
                {'user_id': None}
            ]
        }).sort('timestamp', -1))
        
        csv_lines = ["Time,Frame ID,Track ID,Type,Message\n"]
        
        for alert in alerts:
            timestamp = alert['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            frame_id = alert.get('frame_id', '')
            track_id = alert.get('track_id', '')
            alert_type = alert.get('type', '')
            message = alert.get('message', '').replace('"', '""')  # Escape quotes
            
            csv_lines.append(
                f'"{timestamp}",{frame_id},{track_id},"{alert_type}","{message}"\n'
            )
        
        from flask import Response
        return Response(
            ''.join(csv_lines),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=falcon_ai_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        return jsonify({'error': 'Export failed'}), 500


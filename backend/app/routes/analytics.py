"""
Analytics Routes

Provides privacy-safe mood analytics for campus wellness insights.

Endpoints:
- GET /api/analytics/daily    — Daily mood stats (by date, optional zone)
- GET /api/analytics/weekly   — Weekly mood stats (by week_start, optional zone)
- GET /api/analytics/campus   — Campus-wide mood overview for a date
"""

from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models.aggregate import DailyAggregate, WeeklyAggregate
from app.models.campus_zone import CampusZone
from app.services.aggregation_service import (
    compute_daily_aggregate,
    compute_weekly_aggregate,
    get_campus_mood_overview
)
from app.utils.i18n import get_message, get_bilingual_message

# Create blueprint
bp = Blueprint('analytics', __name__)


@bp.route('/daily', methods=['GET'])
@jwt_required()
def get_daily_analytics():
    """
    Get daily mood analytics.

    Query Params:
        date (str): Date in YYYY-MM-DD format (default: today)
        zone_id (int, optional): Campus zone ID (default: campus-wide)

    Returns:
        200: Daily aggregate (may show "insufficient data" if < 10 posts)
    """
    # Parse date parameter
    date_str = request.args.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': get_message('validation_error', 'en'),
                'message': 'Invalid date format. Use YYYY-MM-DD.'
            }), 400
    else:
        target_date = date.today()

    # Parse zone parameter
    zone_id = request.args.get('zone_id', type=int)
    if zone_id is not None:
        zone = CampusZone.get_by_id(zone_id)
        if not zone:
            return jsonify({
                'error': get_message('validation_error', 'en'),
                'message': get_bilingual_message('zone_not_found')
            }), 404

    # Compute/fetch aggregate
    aggregate = compute_daily_aggregate(target_date, zone_id=zone_id)

    return jsonify({
        'analytics': aggregate.to_dict(enforce_threshold=True),
        'type': 'daily',
        'disclaimer': 'Sentiment analysis is automated and approximate.'
    }), 200


@bp.route('/weekly', methods=['GET'])
@jwt_required()
def get_weekly_analytics():
    """
    Get weekly mood analytics.

    Query Params:
        week_start (str): Monday date in YYYY-MM-DD format
        zone_id (int, optional): Campus zone ID

    Returns:
        200: Weekly aggregate
    """
    # Parse week_start parameter
    week_start_str = request.args.get('week_start')
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': get_message('validation_error', 'en'),
                'message': 'Invalid date format. Use YYYY-MM-DD.'
            }), 400
    else:
        # Default to current week's Monday
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    # Parse zone parameter
    zone_id = request.args.get('zone_id', type=int)
    if zone_id is not None:
        zone = CampusZone.get_by_id(zone_id)
        if not zone:
            return jsonify({
                'error': get_message('validation_error', 'en'),
                'message': get_bilingual_message('zone_not_found')
            }), 404

    # Compute/fetch aggregate
    aggregate = compute_weekly_aggregate(week_start, zone_id=zone_id)

    return jsonify({
        'analytics': aggregate.to_dict(enforce_threshold=True),
        'type': 'weekly',
        'disclaimer': 'Sentiment analysis is automated and approximate.'
    }), 200


@bp.route('/campus', methods=['GET'])
@jwt_required()
def get_campus_overview():
    """
    Get campus-wide mood overview with per-zone breakdown.

    Query Params:
        date (str): Date in YYYY-MM-DD format (default: today)

    Returns:
        200: Campus overview with all zones
    """
    # Parse date parameter
    date_str = request.args.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': get_message('validation_error', 'en'),
                'message': 'Invalid date format. Use YYYY-MM-DD.'
            }), 400
    else:
        target_date = date.today()

    overview = get_campus_mood_overview(target_date)

    return jsonify(overview), 200

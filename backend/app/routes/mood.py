"""
Mood Check-In Routes

Lightweight mood capture — users share how they feel without posting.

Endpoints:
- POST /api/mood/checkin  — Record or update today's emotion
- GET  /api/mood/pulse    — Today's campus emotion distribution
"""

from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.mood_checkin import MoodCheckin

bp = Blueprint('mood', __name__)

VALID_EMOTIONS = {'joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise', 'neutral'}
COOLDOWN_HOURS = 12


@bp.route('/mood/checkin', methods=['POST'])
@jwt_required()
def checkin():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    emotion = str(data.get('emotion', '')).strip().lower()

    if emotion not in VALID_EMOTIONS:
        return jsonify({'error': 'Invalid emotion'}), 400

    # Enforce 12-hour cooldown
    last = MoodCheckin.get_last_checkin_for_user(user_id)
    if last:
        cooldown_ends = last.checked_at + timedelta(hours=COOLDOWN_HOURS)
        retry_after = int((cooldown_ends - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())
        return jsonify({
            'error': 'Cooldown active',
            'emotion': last.emotion,
            'retry_after': max(retry_after, 0),
        }), 429

    db.session.add(MoodCheckin(user_id=user_id, emotion=emotion))
    db.session.commit()
    return jsonify({'ok': True, 'emotion': emotion}), 200


@bp.route('/mood/pulse', methods=['GET'])
@jwt_required()
def pulse():
    user_id = int(get_jwt_identity())
    distribution = MoodCheckin.today_distribution()
    total = sum(distribution.values())

    dominant = max(distribution, key=distribution.get) if distribution else None

    last = MoodCheckin.get_last_checkin_for_user(user_id)
    user_emotion = last.emotion if last else None
    cooldown_seconds = 0
    if last:
        cooldown_ends = last.checked_at + timedelta(hours=COOLDOWN_HOURS)
        remaining = (cooldown_ends - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds()
        cooldown_seconds = max(int(remaining), 0)

    return jsonify({
        'dominant': dominant,
        'distribution': distribution,
        'total': total,
        'user_emotion': user_emotion,
        'cooldown_seconds': cooldown_seconds,
    }), 200

"""Push notification subscription routes."""

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models.push_subscription import PushSubscription
from app.services.push_service import send_push_notification
from app.utils.i18n import get_localized_message

bp = Blueprint('push', __name__)


@bp.route('/push/subscribe', methods=['POST'])
@jwt_required()
def subscribe_push():
    """Register or reactivate a push subscription for the current user."""
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    platform = (data.get('platform') or '').strip().lower()
    token = (data.get('token') or '').strip()
    device_label = (data.get('device_label') or '').strip() or None

    if platform not in {'web', 'ios', 'android'} or not token:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': 'platform and token are required'
        }), 400

    existing = PushSubscription.query.filter_by(user_id=current_user_id, token=token).first()
    if existing:
        existing.platform = platform
        existing.device_label = device_label
        existing.is_active = True
        db.session.commit()
        return jsonify({'subscription_id': existing.id}), 200

    subscription = PushSubscription(
        user_id=current_user_id,
        platform=platform,
        token=token,
        device_label=device_label,
    )
    db.session.add(subscription)
    db.session.commit()
    return jsonify({'subscription_id': subscription.id}), 201


@bp.route('/push/subscribe/<int:subscription_id>', methods=['DELETE'])
@jwt_required()
def unsubscribe_push(subscription_id):
    """Deactivate a push subscription owned by the current user."""
    current_user_id = int(get_jwt_identity())
    subscription = PushSubscription.query.filter_by(id=subscription_id, user_id=current_user_id).first()
    if not subscription:
        return jsonify({'error': get_localized_message(request, 'not_found'), 'message': 'Subscription not found'}), 404

    subscription.is_active = False
    db.session.commit()
    return jsonify({'deleted': True}), 200


@bp.route('/push/test', methods=['POST'])
@jwt_required()
def test_push():
    """Send a test push notification in debug/test environments only."""
    if not (current_app.debug or current_app.testing):
        return jsonify({'error': get_localized_message(request, 'forbidden'), 'message': 'Push testing is only available in development'}), 403

    current_user_id = int(get_jwt_identity())
    result = send_push_notification(
        user_id=current_user_id,
        title='Pulse test notification',
        body='This is a test push notification.',
        data={'type': 'push_test'},
    )
    return jsonify({
        'message': 'Test push attempted',
        'result': result,
    }), 200

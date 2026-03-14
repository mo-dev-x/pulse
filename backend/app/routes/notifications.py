"""Notification routes."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.notification import Notification
from app.utils.i18n import get_localized_message

bp = Blueprint('notifications', __name__)


@bp.route('/notifications', methods=['GET'])
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'unread_count': unread_count,
    }), 200


@bp.route('/notifications/<int:notification_id>/read', methods=['PATCH'])
@jwt_required()
def mark_notification_read(notification_id):
    user_id = int(get_jwt_identity())
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        return jsonify({
            'error': get_localized_message(request, 'not_found'),
            'message': get_localized_message(request, 'not_found')
        }), 404

    notification.is_read = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as read', 'notification': notification.to_dict()}), 200


@bp.route('/notifications/read-all', methods=['PATCH'])
@jwt_required()
def mark_all_notifications_read():
    user_id = int(get_jwt_identity())
    updated = Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read', 'updated': updated}), 200


@bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    user_id = int(get_jwt_identity())
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        return jsonify({
            'error': get_localized_message(request, 'not_found'),
            'message': get_localized_message(request, 'not_found')
        }), 404

    db.session.delete(notification)
    db.session.commit()
    return jsonify({'message': 'Notification deleted'}), 200

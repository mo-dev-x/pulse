"""Comment routes for posts and threaded replies."""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app import db, limiter, rate_limit_key_user, rate_limit_value
from app.middleware import require_verification
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.services.notification_service import create_notification, create_mention_notifications
from app.utils.i18n import get_localized_message

bp = Blueprint('comments', __name__)


def _get_optional_user_id():
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        return int(identity) if identity else None
    except Exception:
        return None


@bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
@limiter.limit(rate_limit_value('COMMENT_CREATE_RATE_LIMIT', '20 per hour'), key_func=rate_limit_key_user)
@require_verification
def create_comment(post_id):
    """Create a comment on a post (or reply to another comment)."""
    user_id = int(get_jwt_identity())
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'post_not_found')
        }), 404

    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    is_anonymous = bool(data.get('is_anonymous', False))
    parent_id = data.get('parent_id')

    if not Comment.validate_content(content):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'comment_length_invalid')
        }), 400

    if parent_id is not None:
        parent = db.session.get(Comment, parent_id)
        if not parent or parent.post_id != post_id:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'comment_parent_invalid')
            }), 400
        if parent.parent_id is not None:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'comment_reply_depth')
            }), 400

    comment = Comment(
        content=content,
        post_id=post_id,
        user_id=user_id,
        parent_id=parent_id,
        is_anonymous=is_anonymous
    )
    db.session.add(comment)
    db.session.flush()

    actor = db.session.get(User, user_id)
    if parent_id is not None and parent.user_id != user_id:
        create_notification(
            user_id=parent.user_id,
            notification_type='comment_reply',
            title='New reply',
            message=f"{actor.display_name if actor else 'Someone'} replied to your comment.",
            related_type='comment',
            related_id=comment.id,
            actor_id=user_id,
        )
    elif post.user_id != user_id:
        create_notification(
            user_id=post.user_id,
            notification_type='new_comment',
            title='New comment',
            message=f"{actor.display_name if actor else 'Someone'} commented on your post.",
            related_type='post',
            related_id=post_id,
            actor_id=user_id,
        )

    create_mention_notifications(
        content=content,
        actor_id=user_id,
        related_type='comment',
        related_id=comment.id
    )
    db.session.commit()

    return jsonify({
        'message': get_localized_message(request, 'comment_added'),
        'comment': comment.to_dict(current_user_id=user_id)
    }), 201


@bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """List top-level comments for a post with pagination."""
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'post_not_found')
        }), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    current_user_id = _get_optional_user_id()

    pagination = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'comments': [comment.to_dict(current_user_id=current_user_id) for comment in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_next': pagination.has_next
    }), 200


@bp.route('/comments/<int:comment_id>/replies', methods=['GET'])
def get_comment_replies(comment_id):
    """List replies for a given comment (one level)."""
    parent_comment = db.session.get(Comment, comment_id)
    if not parent_comment:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'comment_not_found')
        }), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    current_user_id = _get_optional_user_id()

    pagination = Comment.query.filter_by(parent_id=comment_id).order_by(
        Comment.created_at.asc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'replies': [comment.to_dict(current_user_id=current_user_id) for comment in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_next': pagination.has_next
    }), 200


@bp.route('/comments/<int:comment_id>', methods=['PATCH'])
@jwt_required()
def edit_comment(comment_id):
    """Edit a comment inside a 5-minute edit window."""
    user_id = int(get_jwt_identity())
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'comment_not_found')
        }), 404

    if comment.user_id != user_id:
        return jsonify({
            'error': get_localized_message(request, 'forbidden'),
            'message': get_localized_message(request, 'comment_edit_own_only')
        }), 403

    if datetime.now(timezone.utc).replace(tzinfo=None) - comment.created_at > timedelta(minutes=5):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'comment_edit_expired')
        }), 400

    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not Comment.validate_content(content):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'comment_length_invalid')
        }), 400

    comment.content = content
    db.session.commit()
    return jsonify({
        'message': get_localized_message(request, 'comment_updated'),
        'comment': comment.to_dict(current_user_id=user_id)
    }), 200


@bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete a comment owned by the current user."""
    user_id = int(get_jwt_identity())
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'comment_not_found')
        }), 404

    if comment.user_id != user_id:
        return jsonify({
            'error': get_localized_message(request, 'forbidden'),
            'message': get_localized_message(request, 'comment_delete_own_only')
        }), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': get_localized_message(request, 'comment_deleted')}), 200

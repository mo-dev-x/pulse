"""
Direct Messaging Routes

Handles private conversations and message delivery between users.

Endpoints:
- GET    /api/messages/conversations                    — List user's conversations
- POST   /api/messages/conversations                    — Create or reuse a conversation
- GET    /api/messages/conversations/<id>               — Fetch messages in a thread
- POST   /api/messages/conversations/<id>               — Send a text message
- PATCH  /api/messages/conversations/<id>/read          — Mark conversation as read
- GET    /api/messages/unread-count                     — Unread conversation count
- POST   /api/messages/conversations/<id>/audio         — Send a voice/audio message
- POST   /api/messages/conversations/<id>/media         — Send an image or video

Media content convention:
  Audio messages are stored as   [audio]/api/uploads/<filename>
  Image messages are stored as   [image]/api/uploads/<filename>
  Video messages are stored as   [video]/api/uploads/<filename>
  Plain text messages are stored verbatim (no prefix).
"""

import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from app import db, limiter, rate_limit_key_user, rate_limit_value
from app.models import Conversation, Message, User
from app.utils.i18n import get_localized_message

_ALLOWED_AUDIO_EXTS = {'webm', 'ogg', 'mp4', 'm4a', 'wav', 'opus'}
_ALLOWED_MEDIA_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'webm'}

bp = Blueprint('messages', __name__)


def _get_conversation_or_403(conversation_id, current_user_id):
    conversation = db.session.get(Conversation, conversation_id)
    if not conversation:
        return None, (jsonify({'error': get_localized_message(request, 'not_found'), 'message': 'Conversation not found'}), 404)
    if not conversation.has_participant(current_user_id):
        return None, (jsonify({'error': get_localized_message(request, 'forbidden'), 'message': get_localized_message(request, 'forbidden')}), 403)
    return conversation, None


def _other_user_payload(conversation, current_user_id):
    other_user = db.session.get(User, conversation.other_user_id(current_user_id))
    return {
        'id': other_user.id,
        'username': other_user.username,
        'display_name': other_user.display_name,
        'profile_picture': other_user.profile_picture,
        'is_admin': other_user.is_admin,
    } if other_user else None


def _conversation_payload(conversation, current_user_id):
    last_message = conversation.messages.order_by(Message.created_at.desc()).first()
    unread_count = conversation.messages.filter(
        Message.sender_id != current_user_id,
        Message.is_read == False  # noqa: E712
    ).count()

    return {
        'id': conversation.id,
        'other_user': _other_user_payload(conversation, current_user_id),
        'last_message': last_message.to_dict(current_user_id=current_user_id) if last_message else None,
        'unread_count': unread_count,
        'last_message_at': conversation.last_message_at.isoformat() + 'Z' if conversation.last_message_at else None,
        'created_at': conversation.created_at.isoformat() + 'Z' if conversation.created_at else None,
    }


@bp.route('/messages/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    """List current user's conversations with unread counts."""
    current_user_id = int(get_jwt_identity())
    conversations = Conversation.query.filter(
        (Conversation.participant_a == current_user_id) | (Conversation.participant_b == current_user_id)
    ).order_by(Conversation.last_message_at.desc(), Conversation.created_at.desc()).all()

    return jsonify({
        'conversations': [_conversation_payload(conversation, current_user_id) for conversation in conversations],
        'total': len(conversations),
    }), 200


@bp.route('/messages/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    """Start or retrieve a one-to-one conversation by username."""
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    username = (data.get('username') or '').strip().lower()
    target_user = User.query.filter_by(username=username).first()

    if not target_user:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': get_localized_message(request, 'user_not_found')}), 404
    if target_user.is_deactivated:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': get_localized_message(request, 'user_not_found')}), 404
    if target_user.id == current_user_id:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'You cannot message yourself'}), 400

    existing = Conversation.find_between(current_user_id, target_user.id)
    if existing:
        return jsonify({'conversation': _conversation_payload(existing, current_user_id)}), 200

    participant_a, participant_b = Conversation.normalize_pair(current_user_id, target_user.id)
    conversation = Conversation(participant_a=participant_a, participant_b=participant_b)
    db.session.add(conversation)
    db.session.commit()

    return jsonify({'conversation': _conversation_payload(conversation, current_user_id)}), 201


@bp.route('/messages/conversations/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation_messages(conversation_id):
    """Get paginated messages in a conversation."""
    current_user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)

    conversation, error_response = _get_conversation_or_403(conversation_id, current_user_id)
    if error_response:
        return error_response

    pagination = conversation.messages.order_by(Message.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )
    messages = [message.to_dict(current_user_id=current_user_id) for message in reversed(pagination.items)]

    return jsonify({
        'conversation': _conversation_payload(conversation, current_user_id),
        'messages': messages,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_more': pagination.has_next,
    }), 200


@bp.route('/messages/conversations/<int:conversation_id>', methods=['POST'])
@jwt_required()
@limiter.limit(rate_limit_value('MESSAGE_SEND_RATE_LIMIT', '60 per hour'), key_func=rate_limit_key_user)
def send_message(conversation_id):
    """Send a message in a conversation."""
    current_user_id = int(get_jwt_identity())
    conversation, error_response = _get_conversation_or_403(conversation_id, current_user_id)
    if error_response:
        return error_response

    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not Message.validate_content(content):
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'Message must be between 1 and 1000 characters'}), 400

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user_id,
        content=content,
    )
    db.session.add(message)
    conversation.last_message_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()

    return jsonify({'message': message.to_dict(current_user_id=current_user_id)}), 201


@bp.route('/messages/conversations/<int:conversation_id>/audio', methods=['POST'])
@jwt_required()
@limiter.limit(rate_limit_value('MESSAGE_SEND_RATE_LIMIT', '60 per hour'), key_func=rate_limit_key_user)
def send_audio_message(conversation_id):
    """Upload an audio blob and send it as a voice message."""
    current_user_id = int(get_jwt_identity())
    conversation, error_response = _get_conversation_or_403(conversation_id, current_user_id)
    if error_response:
        return error_response

    audio_file = request.files.get('audio')
    if not audio_file or not audio_file.filename:
        return jsonify({'error': 'No audio file provided'}), 400

    raw_ext = audio_file.filename.rsplit('.', 1)[-1].lower() if '.' in audio_file.filename else 'webm'
    ext = raw_ext if raw_ext in _ALLOWED_AUDIO_EXTS else 'webm'
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/')
    os.makedirs(upload_folder, exist_ok=True)
    audio_file.save(os.path.join(upload_folder, filename))

    content = f"[audio]/api/uploads/{filename}"
    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user_id,
        content=content,
    )
    db.session.add(message)
    conversation.last_message_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()

    return jsonify({'message': message.to_dict(current_user_id=current_user_id)}), 201


@bp.route('/messages/conversations/<int:conversation_id>/media', methods=['POST'])
@jwt_required()
@limiter.limit(rate_limit_value('MESSAGE_SEND_RATE_LIMIT', '60 per hour'), key_func=rate_limit_key_user)
def send_media_message(conversation_id):
    """Upload an image/video and send it as a media message."""
    current_user_id = int(get_jwt_identity())
    conversation, error_response = _get_conversation_or_403(conversation_id, current_user_id)
    if error_response:
        return error_response

    media_file = request.files.get('media')
    if not media_file or not media_file.filename:
        return jsonify({'error': 'No media file provided'}), 400

    raw_ext = media_file.filename.rsplit('.', 1)[-1].lower() if '.' in media_file.filename else ''
    if raw_ext not in _ALLOWED_MEDIA_EXTS:
        return jsonify({'error': 'Unsupported file type'}), 400

    filename = f"{uuid.uuid4().hex}.{raw_ext}"
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/')
    os.makedirs(upload_folder, exist_ok=True)
    media_file.save(os.path.join(upload_folder, filename))

    is_video = raw_ext in {'mp4', 'mov', 'webm'}
    prefix   = '[video]' if is_video else '[image]'
    content  = f"{prefix}/api/uploads/{filename}"
    message  = Message(
        conversation_id=conversation.id,
        sender_id=current_user_id,
        content=content,
    )
    db.session.add(message)
    conversation.last_message_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()

    return jsonify({'message': message.to_dict(current_user_id=current_user_id)}), 201


@bp.route('/messages/conversations/<int:conversation_id>/messages/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(conversation_id, message_id):
    """Delete (unsend) a message — only the original sender can do this."""
    current_user_id = int(get_jwt_identity())
    conversation, error_response = _get_conversation_or_403(conversation_id, current_user_id)
    if error_response:
        return error_response

    message = db.session.get(Message, message_id)
    if not message or message.conversation_id != conversation_id:
        return jsonify({'error': 'Message not found'}), 404
    if message.sender_id != current_user_id:
        return jsonify({'error': 'You can only unsend your own messages'}), 403

    db.session.delete(message)
    db.session.commit()
    return jsonify({'deleted': True}), 200


@bp.route('/messages/conversations/<int:conversation_id>/read', methods=['PATCH'])
@jwt_required()
def mark_conversation_read(conversation_id):
    """Mark all received messages in a conversation as read."""
    current_user_id = int(get_jwt_identity())
    conversation, error_response = _get_conversation_or_403(conversation_id, current_user_id)
    if error_response:
        return error_response

    messages = conversation.messages.filter(
        Message.sender_id != current_user_id,
        Message.is_read == False  # noqa: E712
    ).all()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for message in messages:
        message.is_read = True
        message.read_at = now

    db.session.commit()
    return jsonify({'marked_read': len(messages)}), 200


@bp.route('/messages/unread-count', methods=['GET'])
@jwt_required()
def unread_count():
    """Return unread conversation and message totals for the current user."""
    current_user_id = int(get_jwt_identity())
    unread_counts = (
        db.session.query(
            Message.conversation_id,
            func.count(Message.id).label('unread_count'),
        )
        .join(Conversation, Conversation.id == Message.conversation_id)
        .filter(
            ((Conversation.participant_a == current_user_id) | (Conversation.participant_b == current_user_id)),
            Message.sender_id != current_user_id,
            Message.is_read == False,  # noqa: E712
        )
        .group_by(Message.conversation_id)
        .all()
    )

    unread_conversations = len(unread_counts)
    unread_messages = sum(row.unread_count for row in unread_counts)

    return jsonify({
        'unread_conversations': unread_conversations,
        'unread_messages': unread_messages,
    }), 200

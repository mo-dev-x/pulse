"""
Posts Routes

Handles post creation, retrieval, feed generation, and management.

Endpoints:
- POST   /api/posts                — Create new post (public or anonymous)
- GET    /api/posts/feed           — Feed (public posts from followed users)
- GET    /api/posts/me             — Current user's public posts
- GET    /api/posts/me/anonymous   — Current user's anonymous posts (private)
- GET    /api/posts/@{username}    — User's public posts
- GET    /api/posts/zone/{zone_id} — All posts in a zone
- DELETE /api/posts/{post_id}      — Delete own post
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app import db
from app.middleware import require_verification
from app.models import Post, CampusZone, User
from app.models.follower import Follower
from app.models.media import Media
from app.models.reaction import Reaction
from app.models.bookmark import Bookmark
from app.services import analyze_sentiment
from app.services.notification_service import create_mention_notifications
from app.utils.i18n import get_localized_message

# Create blueprint
bp = Blueprint('posts', __name__)


def _enrich_post_dict(post_dict, post, current_user_id):
    """Add reaction counts and media to a serialized post dict"""
    # Add reaction counts
    post_dict['reactions'] = Reaction.get_counts(post.id)
    post_dict['my_reaction'] = Reaction.get_user_reaction(current_user_id, post.id)
    post_dict['reaction_count'] = Reaction.get_total_count(post.id)

    # Add media
    if post.media:
        post_dict['media'] = [m.to_dict() for m in post.media]
    else:
        post_dict['media'] = []

    return post_dict


def _allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@bp.route('', methods=['POST'])
@jwt_required()
@require_verification
def create_post():
    """
    Create a new post with sentiment analysis.

    Supports JSON body or multipart form data (for image uploads).

    Request Body (JSON):
        {
            "content": "Post content here (10-500 chars)",
            "zone_id": 1,
            "is_anonymous": false
        }

    Returns:
        201: Post created successfully with sentiment analysis
        400: Validation error
        404: Zone not found
    """
    user_id = int(get_jwt_identity())

    # Handle both JSON and form data (for file uploads)
    if request.content_type and 'multipart/form-data' in request.content_type:
        content = request.form.get('content', '').strip()
        zone_id = request.form.get('zone_id', type=int)
        is_anonymous = request.form.get('is_anonymous', 'false').lower() == 'true'
        uploaded_file = request.files.get('image')
    else:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'post_content_required')
            }), 400
        content = data['content'].strip()
        zone_id = data.get('zone_id')
        is_anonymous = data.get('is_anonymous', False)
        uploaded_file = None

    # Validate content length
    if len(content) < 10:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'post_too_short')
        }), 400

    if len(content) > 500:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'post_too_long')
        }), 400

    # Validate zone if provided
    if zone_id:
        zone = CampusZone.get_by_id(zone_id)
        if not zone:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'zone_not_found')
            }), 404

    try:
        # Analyze sentiment (bilingual: FR + EN)
        sentiment_result = analyze_sentiment(content)

        # Create post
        new_post = Post(
            content=content,
            user_id=user_id,
            zone_id=zone_id,
            is_anonymous=is_anonymous,
            sentiment_score=sentiment_result['score'],
            sentiment_label=sentiment_result['label'],
            detected_language=sentiment_result['language']
        )

        db.session.add(new_post)
        db.session.flush()  # Get the post ID before committing
        create_mention_notifications(
            content=content,
            actor_id=user_id,
            related_type='post',
            related_id=new_post.id
        )

        # Handle file upload
        if uploaded_file and uploaded_file.filename:
            if not _allowed_file(uploaded_file.filename):
                db.session.rollback()
                return jsonify({
                    'error': get_localized_message(request, 'validation_error'),
                    'message': get_localized_message(request, 'file_type_invalid')
                }), 400

            # Generate unique filename
            ext = uploaded_file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{ext}"

            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)

            uploaded_file.save(file_path)
            file_size = os.path.getsize(file_path)

            media = Media(
                post_id=new_post.id,
                file_path=file_path,
                file_type='image',
                file_size=file_size,
                mime_type=uploaded_file.content_type
            )
            db.session.add(media)

        db.session.commit()

        # Return post (privacy-aware serialization)
        post_dict = new_post.to_dict(current_user_id=user_id)
        post_dict = _enrich_post_dict(post_dict, new_post, user_id)

        return jsonify({
            'message': get_localized_message(request, 'post_created'),
            'post': post_dict
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error creating post: {str(e)}")
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/<int:post_id>/bookmark', methods=['POST'])
@jwt_required()
def bookmark_post(post_id):
    """Bookmark a post for the authenticated user."""
    current_user_id = int(get_jwt_identity())
    post = Post.query.get(post_id)
    if not post:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'post_not_found')
        }), 404

    existing = Bookmark.query.filter_by(user_id=current_user_id, post_id=post_id).first()
    if existing:
        return jsonify({'message': 'Post already bookmarked', 'bookmark': existing.to_dict(current_user_id=current_user_id)}), 200

    bookmark = Bookmark(user_id=current_user_id, post_id=post_id)
    db.session.add(bookmark)
    db.session.commit()
    return jsonify({'message': 'Post bookmarked', 'bookmark': bookmark.to_dict(current_user_id=current_user_id)}), 201


@bp.route('/<int:post_id>/bookmark', methods=['DELETE'])
@jwt_required()
def remove_bookmark(post_id):
    """Remove bookmark for the authenticated user."""
    current_user_id = int(get_jwt_identity())
    bookmark = Bookmark.query.filter_by(user_id=current_user_id, post_id=post_id).first()
    if not bookmark:
        return jsonify({
            'error': get_localized_message(request, 'not_found'),
            'message': get_localized_message(request, 'not_found')
        }), 404

    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({'message': 'Bookmark removed'}), 200


@bp.route('/feed', methods=['GET'])
@jwt_required()
def get_feed():
    """
    Get user's personalized feed.

    Shows ONLY public posts from followed users (never anonymous).
    Ordered by newest first, paginated.

    Query Params:
        page (int): Page number (default 1)
        per_page (int): Items per page (default 20, max 50)
    """
    current_user_id = int(get_jwt_identity())

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    # Get IDs of users the current user follows
    following_ids = Follower.get_following_ids(current_user_id)

    if not following_ids:
        return jsonify({
            'posts': [],
            'total': 0,
            'page': 1,
            'pages': 0,
            'has_next': False,
            'message': get_localized_message(request, 'feed_empty')
        }), 200

    # CRITICAL: Only public posts from followed users
    feed_query = Post.query.filter(
        Post.user_id.in_(following_ids),
        Post.is_anonymous == False  # noqa: E712 — SQLAlchemy requires ==
    ).join(User, User.id == Post.user_id).filter(
        User.is_deactivated == False  # noqa: E712
    ).order_by(Post.created_at.desc())

    paginated = feed_query.paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for post in paginated.items:
        post_dict = post.to_dict(current_user_id=current_user_id)
        post_dict = _enrich_post_dict(post_dict, post, current_user_id)
        posts.append(post_dict)

    return jsonify({
        'posts': posts,
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'has_next': paginated.has_next
    }), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_posts():
    """
    Get current user's public posts (paginated).
    """
    current_user_id = int(get_jwt_identity())

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    query = Post.query.filter_by(
        user_id=current_user_id,
        is_anonymous=False
    ).order_by(Post.created_at.desc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for post in paginated.items:
        post_dict = post.to_dict(current_user_id=current_user_id)
        post_dict = _enrich_post_dict(post_dict, post, current_user_id)
        posts.append(post_dict)

    return jsonify({
        'posts': posts,
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'has_next': paginated.has_next
    }), 200


@bp.route('/me/anonymous', methods=['GET'])
@jwt_required()
def get_my_anonymous_posts():
    """
    Get current user's anonymous posts (private view).

    Privacy Note:
    - Only the post author can see their own anonymous posts.
    - This is the ONLY endpoint that links user_id to anonymous posts.
    """
    current_user_id = int(get_jwt_identity())

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    query = Post.query.filter_by(
        user_id=current_user_id,
        is_anonymous=True
    ).order_by(Post.created_at.desc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for post in paginated.items:
        post_dict = post.to_dict(current_user_id=current_user_id)
        post_dict = _enrich_post_dict(post_dict, post, current_user_id)
        posts.append(post_dict)

    return jsonify({
        'posts': posts,
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'has_next': paginated.has_next
    }), 200


@bp.route('/@<string:username>', methods=['GET'])
@jwt_required()
def get_user_posts(username):
    """
    Get a user's public posts (paginated).

    Privacy: Only shows public (non-anonymous) posts.
    """
    current_user_id = int(get_jwt_identity())

    user = User.query.filter_by(username=username.lower()).first()
    if not user:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_not_found')
        }), 404
    if user.is_deactivated:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_not_found')
        }), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    query = Post.query.filter_by(
        user_id=user.id,
        is_anonymous=False
    ).order_by(Post.created_at.desc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for post in paginated.items:
        post_dict = post.to_dict(current_user_id=current_user_id)
        post_dict = _enrich_post_dict(post_dict, post, current_user_id)
        posts.append(post_dict)

    return jsonify({
        'user': username,
        'posts': posts,
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'has_next': paginated.has_next
    }), 200


@bp.route('/zone/<int:zone_id>', methods=['GET'])
@jwt_required()
def get_zone_posts(zone_id):
    """
    Get all posts in a campus zone (paginated).

    Shows both public and anonymous posts (anonymous hide author info).
    """
    current_user_id = int(get_jwt_identity())

    zone = CampusZone.get_by_id(zone_id)
    if not zone:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'zone_not_found')
        }), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    query = Post.query.filter_by(
        zone_id=zone_id
    ).order_by(Post.created_at.desc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for post in paginated.items:
        post_dict = post.to_dict(current_user_id=current_user_id)
        post_dict = _enrich_post_dict(post_dict, post, current_user_id)
        posts.append(post_dict)

    return jsonify({
        'zone': zone.to_dict(),
        'posts': posts,
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'has_next': paginated.has_next
    }), 200


@bp.route('/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """
    Delete own post.

    Authorization:
    - Only the post author can delete their post
    - Posts can only be deleted within 24 hours of creation (AD-004)
    """
    current_user_id = int(get_jwt_identity())

    post = Post.query.get(post_id)
    if not post:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'post_not_found')
        }), 404

    # Authorization: only author can delete
    if post.user_id != current_user_id:
        return jsonify({
            'error': get_localized_message(request, 'forbidden'),
            'message': get_localized_message(request, 'forbidden')
        }), 403

    # Time restriction: within 24 hours
    if post.created_at:
        hours_since = (datetime.utcnow() - post.created_at).total_seconds() / 3600
        if hours_since > 24:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'post_delete_expired')
            }), 403

    try:
        db.session.delete(post)
        db.session.commit()

        return jsonify({
            'message': get_localized_message(request, 'post_deleted'),
            'deleted': True
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/<int:post_id>/pin', methods=['PATCH'])
@jwt_required()
def pin_post(post_id):
    """Pin one of the current user's own posts to profile."""
    current_user_id = int(get_jwt_identity())
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': get_localized_message(request, 'post_not_found')}), 404
    if post.user_id != current_user_id:
        return jsonify({'error': get_localized_message(request, 'forbidden'), 'message': get_localized_message(request, 'forbidden')}), 403

    user = User.query.get(current_user_id)
    user.pinned_post_id = post_id
    db.session.commit()
    return jsonify({'message': 'Post pinned', 'pinned_post_id': post_id}), 200


@bp.route('/pin', methods=['DELETE'])
@jwt_required()
def unpin_post():
    """Remove profile pinned post."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    user.pinned_post_id = None
    db.session.commit()
    return jsonify({'message': 'Pinned post removed'}), 200

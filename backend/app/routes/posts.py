"""
Posts Routes

Handles post creation, retrieval, feed generation, and management.

Endpoints:
- POST   /api/posts                       — Create new post (public or anonymous)
- GET    /api/posts/feed                  — Home feed (posts from followed users)
- GET    /api/posts/discover              — Discover feed (public posts from all users)
- GET    /api/posts/trending              — Trending posts
- GET    /api/posts/me                    — Current user's public posts
- GET    /api/posts/me/anonymous          — Current user's anonymous posts (private)
- GET    /api/posts/@<username>           — A specific user's public posts
- GET    /api/posts/zone/<zone_id>        — All posts in a campus zone
- DELETE /api/posts/<post_id>             — Delete own post
- POST   /api/posts/<post_id>/bookmark    — Bookmark a post
- DELETE /api/posts/<post_id>/bookmark    — Remove bookmark
- PATCH  /api/posts/<post_id>/pin         — Pin a post to own profile
- DELETE /api/posts/pin                   — Unpin the currently pinned post
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app import cache, db, limiter, rate_limit_key_user, rate_limit_value
from app.middleware import require_verification
from app.models import Post, CampusZone, User, Comment
from app.models.follower import Follower
from app.models.media import Media
from app.models.reaction import Reaction
from app.models.bookmark import Bookmark
from app.services import delete_document, upsert_documents
from app.services.job_queue_service import enqueue_task
from app.services.notification_service import create_mention_notifications
from app.utils.i18n import get_localized_message

# Create blueprint
bp = Blueprint('posts', __name__)

TRENDING_WINDOWS = {
    '1h': timedelta(hours=1),
    '6h': timedelta(hours=6),
    '24h': timedelta(hours=24),
    '7d': timedelta(days=7),
}


def _enrich_post_dict(post_dict, post, current_user_id):
    """Add reaction counts and media to a serialized post dict (single-post path)."""
    post_dict['reactions'] = Reaction.get_counts(post.id)
    post_dict['my_reaction'] = Reaction.get_user_reaction(current_user_id, post.id)
    post_dict['reaction_count'] = Reaction.get_total_count(post.id)
    post_dict['media'] = [m.to_dict() for m in post.media] if post.media else []
    return post_dict


def _bulk_enrich_posts(posts, current_user_id):
    """
    Enrich a list of posts with reaction/comment/media data using bulk queries.

    Replaces per-post calls to _enrich_post_dict: instead of 4 queries per post
    this runs 4 queries total regardless of how many posts are in the list.
    """
    if not posts:
        return []

    post_ids = [p.id for p in posts]

    # One query for all reaction counts across all posts
    reaction_rows = db.session.query(
        Reaction.post_id,
        Reaction.emoji,
        db.func.count('*').label('cnt')
    ).filter(Reaction.post_id.in_(post_ids)).group_by(
        Reaction.post_id, Reaction.emoji
    ).all()

    reaction_counts = {}  # {post_id: {emoji: count}}
    total_reactions = {}  # {post_id: int}
    for row in reaction_rows:
        reaction_counts.setdefault(row.post_id, {})[row.emoji] = row.cnt
        total_reactions[row.post_id] = total_reactions.get(row.post_id, 0) + row.cnt

    # One query for the current user's reactions across all posts
    user_reaction_rows = Reaction.query.filter(
        Reaction.post_id.in_(post_ids),
        Reaction.user_id == current_user_id
    ).all()
    user_reactions = {r.post_id: r.emoji for r in user_reaction_rows}

    # One query for comment counts across all posts
    comment_rows = db.session.query(
        Comment.post_id,
        db.func.count('*').label('cnt')
    ).filter(Comment.post_id.in_(post_ids)).group_by(Comment.post_id).all()
    comment_counts = {row.post_id: row.cnt for row in comment_rows}

    result = []
    for post in posts:
        post_dict = post.to_dict(current_user_id=current_user_id)
        post_dict['reactions'] = reaction_counts.get(post.id, {})
        post_dict['my_reaction'] = user_reactions.get(post.id)
        post_dict['reaction_count'] = total_reactions.get(post.id, 0)
        post_dict['comment_count'] = comment_counts.get(post.id, 0)
        post_dict['media'] = [m.to_dict() for m in post.media] if post.media else []
        result.append(post_dict)

    return result


def _allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def _paginate_list(items, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], len(items) > end


def _public_posts_query():
    return (
        Post.query
        .join(User, User.id == Post.user_id)
        .filter(Post.is_anonymous == False)  # noqa: E712
        .filter(Post.hidden_by_mod == False)  # noqa: E712
        .filter(User.is_verified == True)  # noqa: E712
        .filter(User.is_deactivated == False)  # noqa: E712
    )



def _sentiment_bucket(avg_score):
    if avg_score is None:
        return 'neutral'
    if avg_score > 0.15:
        return 'positive'
    if avg_score < -0.15:
        return 'negative'
    return 'neutral'


def _serialize_ranked_posts(posts, current_user_id):
    enriched = _bulk_enrich_posts(posts, current_user_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ranked = []
    for post_dict, post in zip(enriched, posts):
        reaction_count = post_dict.get('reaction_count', 0)
        comment_count = post_dict.get('comment_count', 0)
        hours_since = max((now - post.created_at).total_seconds() / 3600, 1 / 60)
        score = reaction_count * 2 + comment_count + (10 / hours_since)
        post_dict['engagement_score'] = round(score, 4)
        ranked.append((score, post.created_at, post_dict))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in ranked]


def _build_trending_zones(posts):
    zone_metrics = {}
    for post in posts:
        if not post.zone:
            continue

        entry = zone_metrics.setdefault(post.zone_id, {
            'zone': post.zone.to_dict(),
            'post_count': 0,
            'reaction_count': 0,
            'sentiment_scores': [],
        })
        entry['post_count'] += 1
        entry['reaction_count'] += Reaction.get_total_count(post.id)
        if post.sentiment_score is not None:
            entry['sentiment_scores'].append(post.sentiment_score)

    zone_results = []
    for entry in zone_metrics.values():
        scores = entry.pop('sentiment_scores')
        avg_score = (sum(scores) / len(scores)) if scores else None
        entry['avg_sentiment'] = _sentiment_bucket(avg_score)
        entry['mood'] = entry['avg_sentiment']
        zone_results.append(entry)

    zone_results.sort(key=lambda item: (item['post_count'], item['reaction_count']), reverse=True)
    return zone_results


def _filtered_public_posts(zone_id=None, sentiment=None, window=None):
    query = _public_posts_query()
    if zone_id:
        query = query.filter(Post.zone_id == zone_id)
    if sentiment:
        query = query.filter(Post.sentiment_label == sentiment)
    if window:
        query = query.filter(Post.created_at >= datetime.now(timezone.utc).replace(tzinfo=None) - window)
    return query.order_by(Post.created_at.desc()).all()


def _trending_cache_key():
    """Cache trending responses per user because payload includes my_reaction."""
    current_user_id = get_jwt_identity() or 'anonymous'
    query_items = sorted(request.args.items(multi=True))
    query_string = '&'.join(f'{key}={value}' for key, value in query_items)
    return f"trending_posts:{current_user_id}:{query_string}"


def _post_search_document(post):
    return {
        'id': post.id,
        'content': post.content,
        'is_anonymous': post.is_anonymous,
        'hidden_by_mod': post.hidden_by_mod,
        'zone_id': post.zone_id,
        'zone_name': post.zone.name if post.zone else None,
        'author_display_name': post.author.display_name if post.author else None,
        'author_is_deactivated': bool(post.author.is_deactivated) if post.author else False,
        'created_at': post.created_at.isoformat() if post.created_at else None,
    }


@bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit(rate_limit_value('POST_CREATE_RATE_LIMIT', '15 per hour'), key_func=rate_limit_key_user)
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
        # Create post — sentiment fields are populated asynchronously after commit
        new_post = Post(
            content=content,
            user_id=user_id,
            zone_id=zone_id,
            is_anonymous=is_anonymous,
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

        enqueue_task(
            'app.tasks.aggregation_tasks.refresh_post_aggregates',
            new_post.id,
            queue_name='analytics',
        )
        enqueue_task(
            'app.tasks.nlp_tasks.analyze_post_sentiment',
            new_post.id,
            queue_name='default',
        )
        try:
            upsert_documents('posts', [_post_search_document(new_post)])
        except Exception:
            current_app.logger.warning('Meilisearch post upsert failed for post_id=%s', new_post.id)

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
    post = db.session.get(Post, post_id)
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
        Post.is_anonymous == False,  # noqa: E712 — SQLAlchemy requires ==
        Post.hidden_by_mod == False  # noqa: E712
    ).join(User, User.id == Post.user_id).filter(
        User.is_deactivated == False  # noqa: E712
    ).order_by(Post.created_at.desc())

    paginated = feed_query.paginate(page=page, per_page=per_page, error_out=False)
    posts = _bulk_enrich_posts(paginated.items, current_user_id)

    return jsonify({
        'posts': posts,
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'has_next': paginated.has_next
    }), 200


@bp.route('/discover', methods=['GET'])
@jwt_required()
def discover_posts():
    """Return a ranked discovery feed from verified public posts."""
    current_user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    zone_id = request.args.get('zone_id', type=int)
    sentiment = (request.args.get('sentiment') or '').strip().lower() or None

    if page < 1 or per_page < 1:
        return jsonify({'error': 'Invalid pagination', 'message': 'page and per_page must be positive integers'}), 400

    if sentiment and sentiment not in {'positive', 'negative', 'neutral'}:
        return jsonify({'error': 'Invalid sentiment filter', 'message': 'sentiment must be positive, negative, or neutral'}), 400

    posts = _filtered_public_posts(zone_id=zone_id, sentiment=sentiment)
    ranked_posts = _serialize_ranked_posts(posts, current_user_id=current_user_id)
    paginated_posts, has_next = _paginate_list(ranked_posts, page, per_page)

    return jsonify({
        'posts': paginated_posts,
        'total': len(ranked_posts),
        'page': page,
        'has_next': has_next,
        'filters': {
            'zone_id': zone_id,
            'sentiment': sentiment,
        },
    }), 200


@bp.route('/trending', methods=['GET'])
@jwt_required()
@cache.cached(timeout=120, make_cache_key=_trending_cache_key)
def trending_posts():
    """Return trending public posts and zone activity for a time window."""
    current_user_id = int(get_jwt_identity())
    window_name = (request.args.get('window') or '24h').strip().lower()
    zone_id = request.args.get('zone_id', type=int)
    limit = min(request.args.get('limit', 10, type=int), 25)

    window = TRENDING_WINDOWS.get(window_name)
    if not window:
        return jsonify({'error': 'Invalid window', 'message': 'window must be one of 1h, 6h, 24h, or 7d'}), 400

    posts = _filtered_public_posts(zone_id=zone_id, window=window)
    ranked_posts = _serialize_ranked_posts(posts, current_user_id=current_user_id)[:limit]
    trending_zones = _build_trending_zones(posts)

    return jsonify({
        'window': window_name,
        'posts': ranked_posts,
        'trending_zones': [
            {
                'zone': item['zone'],
                'post_count': item['post_count'],
                'reaction_count': item['reaction_count'],
                'avg_sentiment': item['avg_sentiment'],
            }
            for item in trending_zones[:limit]
        ],
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
    posts = _bulk_enrich_posts(paginated.items, current_user_id)

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
    posts = _bulk_enrich_posts(paginated.items, current_user_id)

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

    posts = _bulk_enrich_posts(paginated.items, current_user_id)

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

    Shows only public posts from verified, active users.
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

    query = (
        Post.query
        .join(User, User.id == Post.user_id)
        .filter(Post.zone_id == zone_id)
        .filter(Post.is_anonymous == False)  # noqa: E712
        .filter(Post.hidden_by_mod == False)  # noqa: E712
        .filter(User.is_verified == True)  # noqa: E712
        .filter(User.is_deactivated == False)  # noqa: E712
        .order_by(Post.created_at.desc())
    )

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    posts = _bulk_enrich_posts(paginated.items, current_user_id)

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

    post = db.session.get(Post, post_id)
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
        hours_since = (datetime.now(timezone.utc).replace(tzinfo=None) - post.created_at).total_seconds() / 3600
        if hours_since > 24:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'post_delete_expired')
            }), 403

    try:
        post_id_to_remove = post.id
        db.session.delete(post)
        db.session.commit()
        try:
            delete_document('posts', post_id_to_remove)
        except Exception:
            current_app.logger.warning('Meilisearch post delete failed for post_id=%s', post_id_to_remove)

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
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': get_localized_message(request, 'post_not_found')}), 404
    if post.user_id != current_user_id:
        return jsonify({'error': get_localized_message(request, 'forbidden'), 'message': get_localized_message(request, 'forbidden')}), 403

    user = db.session.get(User, current_user_id)
    user.pinned_post_id = post_id
    db.session.commit()
    return jsonify({'message': 'Post pinned', 'pinned_post_id': post_id}), 200


@bp.route('/pin', methods=['DELETE'])
@jwt_required()
def unpin_post():
    """Remove profile pinned post."""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    user.pinned_post_id = None
    db.session.commit()
    return jsonify({'message': 'Pinned post removed'}), 200

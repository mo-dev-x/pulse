"""Unified search routes for posts, users, and campus zones."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import limiter, rate_limit_value
from app.models import CampusZone, Post, User

bp = Blueprint('search', __name__)


def _contains(value, query):
    return query.lower() in (value or '').lower()


def _score_text_match(query, *values):
    query_lower = query.lower()
    best = 0

    for raw_value in values:
        value = (raw_value or '').strip()
        if not value:
            continue

        lower_value = value.lower()
        if lower_value == query_lower:
            score = 100
        elif lower_value.startswith(query_lower):
            score = 90
        elif query_lower in lower_value:
            score = 75
        else:
            score = 0

        best = max(best, score)

    return best


def _paginate(items, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], len(items) > end


def _search_posts(query, zone_id=None):
    search_pattern = f"%{query}%"
    post_query = (
        Post.query
        .join(User, Post.user_id == User.id)
        .filter(Post.is_anonymous == False)  # noqa: E712
        .filter(Post.hidden_by_mod == False)  # noqa: E712
        .filter(User.is_deactivated == False)  # noqa: E712
        .filter(Post.content.ilike(search_pattern))
        .order_by(Post.created_at.desc())
    )

    if zone_id:
        post_query = post_query.filter(Post.zone_id == zone_id)

    posts = post_query.all()

    results = []
    for post in posts:
        post_dict = post.to_dict()
        post_dict['match_score'] = _score_text_match(
            query,
            post.content,
            post.zone.name if post.zone else None,
            post.author.display_name if post.author else None,
        )
        results.append(post_dict)

    results.sort(key=lambda item: (item['match_score'], item['created_at']), reverse=True)
    return results


def _search_users(query):
    users = (
        User.query
        .filter(User.profile_visibility != 'private')
        .filter(User.is_deactivated == False)  # noqa: E712
        .order_by(User.created_at.desc())
        .all()
    )

    results = []
    for user in users:
        if not any(
            _contains(value, query)
            for value in (user.username, user.display_name, user.bio)
        ):
            continue

        user_dict = user.to_dict()
        user_dict['match_score'] = _score_text_match(
            query,
            user.username,
            user.display_name,
            user.bio,
        )
        results.append(user_dict)

    results.sort(key=lambda item: (item['match_score'], item['username']), reverse=True)
    return results


def _search_zones(query):
    zones = CampusZone.query.order_by(CampusZone.name.asc()).all()
    results = []

    for zone in zones:
        if not any(_contains(value, query) for value in (zone.name, zone.description)):
            continue

        zone_dict = zone.to_dict()
        zone_dict['match_score'] = _score_text_match(query, zone.name, zone.description)
        results.append(zone_dict)

    results.sort(key=lambda item: (item['match_score'], item['name']), reverse=True)
    return results


@bp.route('/search', methods=['GET'])
@jwt_required()
@limiter.limit(rate_limit_value('SEARCH_RATE_LIMIT', '60 per minute'))
def search():
    """Search posts, users, and zones with privacy-aware filters."""
    query = (request.args.get('q') or '').strip()
    search_type = (request.args.get('type') or 'all').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    zone_id = request.args.get('zone_id', type=int)

    if not query:
        return jsonify({'error': 'Missing search query', 'message': 'Please provide ?q=...'}), 400

    if len(query) < 2:
        return jsonify({'error': 'Query too short', 'message': 'Please enter at least 2 characters'}), 400

    if search_type not in {'all', 'posts', 'users', 'zones'}:
        return jsonify({'error': 'Invalid type filter', 'message': 'type must be posts, users, zones, or all'}), 400

    if page < 1 or per_page < 1:
        return jsonify({'error': 'Invalid pagination', 'message': 'page and per_page must be positive integers'}), 400

    all_results = {'posts': [], 'users': [], 'zones': []}
    has_next = False

    if search_type in {'all', 'posts'}:
        all_results['posts'] = _search_posts(query, zone_id=zone_id)
    if search_type in {'all', 'users'}:
        all_results['users'] = _search_users(query)
    if search_type in {'all', 'zones'}:
        all_results['zones'] = _search_zones(query)

    paginated_results = {}
    counts = {}
    for key, items in all_results.items():
        counts[key] = len(items)
        sliced_items, sliced_has_next = _paginate(items, page, per_page)
        paginated_results[key] = sliced_items
        has_next = has_next or sliced_has_next

    return jsonify({
        'query': query,
        'results': paginated_results,
        'counts': counts,
        'page': page,
        'has_next': has_next,
    }), 200


@bp.route('/search/users', methods=['GET'])
@jwt_required()
def search_users():
    """Lightweight user search endpoint for mention autocomplete."""
    query = (request.args.get('q') or '').strip()
    limit = min(request.args.get('limit', 5, type=int), 20)

    if not query:
        return jsonify({'error': 'Missing search query', 'message': 'Please provide ?q=...'}), 400

    matches = _search_users(query)[:limit]
    users = [
        {
            'username': user['username'],
            'display_name': user['display_name'],
            'profile_picture': user['profile_picture'],
        }
        for user in matches
    ]
    return jsonify({'users': users, 'count': len(users)}), 200

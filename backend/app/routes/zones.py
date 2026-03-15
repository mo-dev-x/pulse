"""Campus zone discovery, search, and trending routes."""

from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_

from app import cache, db
from app.models import CampusZone, Post, Reaction, User

bp = Blueprint('zones', __name__)

TRENDING_WINDOWS = {
    '1h': timedelta(hours=1),
    '6h': timedelta(hours=6),
    '24h': timedelta(hours=24),
    '7d': timedelta(days=7),
}

ZONE_ALIASES = {
    'biblio': 'Bonenfant',
    'library': 'Bonenfant',
    'bibliotheque': 'Bonenfant',
    'bibliothèque': 'Bonenfant',
    'admin': 'Desjardins',
    'administration': 'Desjardins',
    'genie': 'Pouliot',
    'génie': 'Pouliot',
    'engineering': 'Pouliot',
    'math': 'Vachon',
    'maths': 'Vachon',
    'sport': 'PEPS',
    'sports': 'PEPS',
    'gym': 'PEPS',
    'pool': 'Piscine',
    'piscine': 'Piscine',
    'cafe': 'Café',
    'café': 'Café',
    'resto': 'Café',
    'food': 'Café',
    'residence': 'Résidences',
    'résidence': 'Résidences',
    'dorm': 'Résidences',
}


def _score_zone(zone, query):
    query_lower = query.lower()
    name_lower = zone.name.lower()
    desc_lower = (zone.description or '').lower()

    if query_lower == name_lower:
        score = 100
    elif name_lower.startswith(query_lower):
        score = 90
    elif query_lower in name_lower:
        score = 80
    elif query_lower in desc_lower:
        score = 70
    else:
        score = 50

    if len(query) <= 4 and query.upper() in zone.name.upper():
        score += 20

    return score


@bp.route('/zones/search', methods=['GET'])
def search_zones():
    """Search campus zones by partial name, code, or description."""
    query = (request.args.get('q') or '').strip()
    limit = min(request.args.get('limit', 10, type=int), 50)
    zone_type = (request.args.get('type') or '').strip()

    if not query:
        return jsonify({
            'error': 'Missing search query',
            'message': 'Please provide a search query using ?q=...'
        }), 400

    if len(query) < 2:
        return jsonify({
            'error': 'Query too short',
            'message': 'Please enter at least 2 characters'
        }), 400

    search_pattern = f"%{query}%"
    db_query = CampusZone.query.filter(
        or_(
            CampusZone.name.ilike(search_pattern),
            CampusZone.description.ilike(search_pattern)
        )
    )

    if zone_type:
        db_query = db_query.filter(CampusZone.zone_type == zone_type)

    zones = db_query.limit(limit).all()
    results = []
    for zone in zones:
        zone_data = zone.to_dict()
        zone_data['match_score'] = _score_zone(zone, query)
        results.append(zone_data)

    results.sort(key=lambda item: item['match_score'], reverse=True)

    return jsonify({
        'query': query,
        'zones': results,
        'count': len(results)
    }), 200


@bp.route('/zones/suggest', methods=['GET'])
def suggest_zones():
    """Suggest zones using direct match first, then common aliases."""
    query = (request.args.get('q') or '').strip()
    limit = min(request.args.get('limit', 5, type=int), 20)
    zone_type = (request.args.get('type') or '').strip()

    if not query:
        return jsonify({
            'error': 'Missing search query',
            'message': 'Please provide a search query using ?q=...'
        }), 400

    search_term = ZONE_ALIASES.get(query.lower(), query)
    search_pattern = f"%{search_term}%"
    db_query = CampusZone.query.filter(
        or_(
            CampusZone.name.ilike(search_pattern),
            CampusZone.description.ilike(search_pattern)
        )
    )

    if zone_type:
        db_query = db_query.filter(CampusZone.zone_type == zone_type)

    zones = db_query.limit(limit).all()
    results = []
    for zone in zones:
        zone_data = zone.to_dict()
        zone_data['match_score'] = _score_zone(zone, search_term)
        results.append(zone_data)

    results.sort(key=lambda item: item['match_score'], reverse=True)

    return jsonify({
        'query': query,
        'expanded_query': search_term,
        'zones': results,
        'count': len(results)
    }), 200


@bp.route('/zones', methods=['GET'])
@cache.cached(timeout=3600, query_string=True)
def get_all_zones():
    """List all zones, optionally filtered by type."""
    zone_type = (request.args.get('type') or '').strip()
    query = CampusZone.query
    if zone_type:
        query = query.filter(CampusZone.zone_type == zone_type)

    zones = query.order_by(CampusZone.name.asc()).all()
    return jsonify({
        'zones': [zone.to_dict() for zone in zones],
        'count': len(zones),
        'type_filter': zone_type or None
    }), 200


@bp.route('/zones/<int:zone_id>', methods=['GET'])
def get_zone(zone_id):
    """Return one zone by ID."""
    zone = CampusZone.query.get(zone_id)
    if not zone:
        return jsonify({
            'error': 'Zone not found',
            'message': f'No zone found with ID {zone_id}'
        }), 404

    return jsonify({'zone': zone.to_dict()}), 200


@bp.route('/zones/types', methods=['GET'])
def get_zone_types():
    """Return available zone types with counts."""
    results = db.session.query(
        CampusZone.zone_type,
        func.count(CampusZone.id).label('count')
    ).group_by(CampusZone.zone_type).order_by(CampusZone.zone_type.asc()).all()

    return jsonify({
        'types': [
            {'type': zone_type, 'count': count}
            for zone_type, count in results
        ]
    }), 200


@bp.route('/zones/trending', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_trending_zones():
    """Return the most active public zones for a given time window."""
    window_name = (request.args.get('window') or '24h').strip().lower()
    limit = min(request.args.get('limit', 10, type=int), 25)
    window = TRENDING_WINDOWS.get(window_name)

    if not window:
        return jsonify({'error': 'Invalid window', 'message': 'window must be one of 1h, 6h, 24h, or 7d'}), 400

    cutoff = datetime.utcnow() - window
    posts = (
        Post.query
        .join(User, User.id == Post.user_id)
        .filter(Post.is_anonymous == False)  # noqa: E712
        .filter(Post.hidden_by_mod == False)  # noqa: E712
        .filter(User.is_verified == True)  # noqa: E712
        .filter(User.is_deactivated == False)  # noqa: E712
        .filter(Post.zone_id.isnot(None))
        .filter(Post.created_at >= cutoff)
        .all()
    )

    zone_metrics = {}
    for post in posts:
        entry = zone_metrics.setdefault(post.zone_id, {
            'zone': post.zone.to_dict(),
            'post_count': 0,
            'reaction_count': 0,
            'scores': [],
        })
        entry['post_count'] += 1
        entry['reaction_count'] += Reaction.get_total_count(post.id)
        if post.sentiment_score is not None:
            entry['scores'].append(post.sentiment_score)

    zones = []
    for entry in zone_metrics.values():
        avg_score = (sum(entry['scores']) / len(entry['scores'])) if entry['scores'] else None
        if avg_score is None:
            mood = 'neutral'
        elif avg_score > 0.15:
            mood = 'positive'
        elif avg_score < -0.15:
            mood = 'negative'
        else:
            mood = 'neutral'

        zones.append({
            'zone': entry['zone'],
            'post_count': entry['post_count'],
            'reaction_count': entry['reaction_count'],
            'mood': mood,
        })

    zones.sort(key=lambda item: (item['post_count'], item['reaction_count']), reverse=True)
    return jsonify({
        'window': window_name,
        'zones': zones[:limit],
    }), 200


@bp.route('/zones/<int:zone_id>/activity', methods=['GET'])
def get_zone_activity(zone_id):
    """Return zone activity summary and recent public posts."""
    zone = CampusZone.query.get(zone_id)
    if not zone:
        return jsonify({
            'error': 'Zone not found',
            'message': f'No zone found with ID {zone_id}'
        }), 404

    cutoff = datetime.utcnow() - timedelta(hours=24)
    posts = (
        Post.query
        .join(User, User.id == Post.user_id)
        .filter(Post.zone_id == zone_id)
        .filter(Post.is_anonymous == False)  # noqa: E712
        .filter(Post.hidden_by_mod == False)  # noqa: E712
        .filter(User.is_verified == True)  # noqa: E712
        .filter(User.is_deactivated == False)  # noqa: E712
        .filter(Post.created_at >= cutoff)
        .order_by(Post.created_at.desc())
        .all()
    )

    reaction_count = sum(Reaction.get_total_count(post.id) for post in posts)
    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    for post in posts:
        label = post.sentiment_label or 'neutral'
        if label in sentiment_counts:
            sentiment_counts[label] += 1

    total_posts = len(posts)
    dominant_sentiment = 'neutral'
    if total_posts:
        dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)

    sentiment_breakdown = {
        key: round((count / total_posts), 2) if total_posts else 0.0
        for key, count in sentiment_counts.items()
    }

    recent_posts = []
    for post in posts[:5]:
        recent_posts.append({
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at.isoformat() + 'Z' if post.created_at else None,
            'author': {
                'id': post.author.id,
                'username': post.author.username,
                'display_name': post.author.display_name,
                'profile_picture': post.author.profile_picture,
            },
            'sentiment': post.sentiment_label,
            'reaction_count': Reaction.get_total_count(post.id),
        })

    return jsonify({
        'zone': zone.to_dict(),
        'last_24h': {
            'post_count': total_posts,
            'reaction_count': reaction_count,
            'dominant_sentiment': dominant_sentiment,
            'sentiment_breakdown': sentiment_breakdown,
        },
        'recent_posts': recent_posts,
    }), 200

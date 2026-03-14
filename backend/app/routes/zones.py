"""Campus zone discovery and search routes."""

from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_

from app import db
from app.models.campus_zone import CampusZone

bp = Blueprint('zones', __name__)

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

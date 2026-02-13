"""
Posts Routes

Handles post creation, retrieval, and management.

Endpoints:
- POST /api/posts - Create new post (public or anonymous)
- GET /api/posts/feed - Get user's feed (future)
- GET /api/posts/me - Get user's public posts (future)
- GET /api/posts/me/anonymous - Get user's anonymous posts (future)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Post, CampusZone, User
from app.services import analyze_sentiment
from app.utils.i18n import get_bilingual_message, get_message

# Create blueprint
bp = Blueprint('posts', __name__)


@bp.route('', methods=['POST'])
@jwt_required()
def create_post():
    """
    Create a new post with sentiment analysis
    
    Request Body:
        {
            "content": "Post content here (10-500 chars)",
            "zone_id": 1,  // Optional: Campus zone ID
            "is_anonymous": false  // Optional: Default false
        }
    
    Returns:
        201: Post created successfully with sentiment analysis
        400: Validation error
        404: Zone not found
    
    Features:
    - Automatic bilingual sentiment analysis (FR/EN)
    - Privacy-aware: Anonymous posts hide user_id in response
    - Zone validation
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Validate required fields
    if not data or 'content' not in data:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('post_content_required')
        }), 400
    
    content = data['content'].strip()
    zone_id = data.get('zone_id')
    is_anonymous = data.get('is_anonymous', False)
    
    # Validate content length
    if len(content) < 10:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('post_too_short')
        }), 400
    
    if len(content) > 500:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('post_too_long')
        }), 400
    
    # Validate zone if provided
    if zone_id:
        zone = CampusZone.get_by_id(zone_id)
        if not zone:
            return jsonify({
                'error': get_message('validation_error', 'en'),
                'message': get_bilingual_message('zone_not_found')
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
        db.session.commit()
        
        # Return post (privacy-aware serialization)
        return jsonify({
            'message': get_bilingual_message('post_created'),
            'post': new_post.to_dict(current_user_id=user_id)
        }), 201
        
    except ValueError as e:
        # NLP validation error (text too short)
        db.session.rollback()
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error creating post: {str(e)}")  # Log for debugging
        return jsonify({
            'error': get_message('server_error', 'en'),
            'message': 'Failed to create post'
        }), 500


@bp.route('/feed', methods=['GET'])
@jwt_required()
def get_feed():
    """
    Get user's personalized feed
    
    TODO: Phase 2 - Implement feed generation
    Shows public posts from followed users
    """
    return jsonify({
        'message': 'Feed endpoint - Coming in Phase 2!',
        'posts': []
    }), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_posts():
    """
    Get current user's public posts
    
    TODO: Phase 2 - Implement user posts retrieval
    """
    return jsonify({
        'message': 'My posts endpoint - Coming in Phase 2!',
        'posts': []
    }), 200


@bp.route('/me/anonymous', methods=['GET'])
@jwt_required()
def get_my_anonymous_posts():
    """
    Get current user's anonymous posts (private view)
    
    Privacy Note:
    - Only the post author can see their own anonymous posts
    - This endpoint is for "My Anonymous Posts" feature
    
    TODO: Phase 2 - Implement anonymous posts retrieval
    """
    return jsonify({
        'message': 'My anonymous posts endpoint - Coming in Phase 2!',
        'posts': []
    }), 200
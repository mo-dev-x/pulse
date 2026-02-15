"""
Reactions Routes

Handles emoji reactions on posts.

Endpoints:
- POST   /api/posts/{post_id}/react      — Add/update emoji reaction
- DELETE /api/posts/{post_id}/react      — Remove reaction
- GET    /api/posts/{post_id}/reactions  — Get reaction counts
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.post import Post
from app.models.reaction import Reaction
from app.utils.i18n import get_bilingual_message, get_message

# Create blueprint
bp = Blueprint('reactions', __name__)


@bp.route('/<int:post_id>/react', methods=['POST'])
@jwt_required()
def add_reaction(post_id):
    """
    Add or update emoji reaction on a post.

    Request Body:
        {"emoji": "❤️"}

    Rules:
    - One reaction per user per post
    - If user already reacted, emoji is updated
    - Only allowed emojis accepted

    Returns:
        201: Reaction added
        200: Reaction updated
        400: Invalid emoji
        404: Post not found
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    # Validate request
    if not data or 'emoji' not in data:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('emoji_required')
        }), 400

    emoji = data['emoji'].strip()

    # Validate emoji is allowed
    if emoji not in Reaction.ALLOWED_EMOJIS:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('emoji_invalid'),
            'allowed_emojis': list(Reaction.ALLOWED_EMOJIS)
        }), 400

    # Check post exists
    post = Post.query.get(post_id)
    if not post:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('post_not_found')
        }), 404

    try:
        # Check for existing reaction
        existing = Reaction.query.filter_by(
            user_id=current_user_id,
            post_id=post_id
        ).first()

        if existing:
            # Update existing reaction
            old_emoji = existing.emoji
            existing.emoji = emoji
            db.session.commit()

            # Remove session to force completely fresh queries
            db.session.remove()

            # Get counts - this will now query the database freshly
            counts = Reaction.get_counts(post_id)

            return jsonify({
                'message': get_bilingual_message('reaction_updated'),
                'reaction': {
                    'post_id': post_id,
                    'emoji': emoji,
                    'previous_emoji': old_emoji
                },
                'counts': Reaction.get_counts(post_id)
            }), 200
        else:
            # Create new reaction
            new_reaction = Reaction(
                post_id=post_id,
                user_id=current_user_id,
                emoji=emoji
            )
            db.session.add(new_reaction)
            db.session.commit()

            return jsonify({
                'message': get_bilingual_message('reaction_added'),
                'reaction': {
                    'post_id': post_id,
                    'emoji': emoji
                },
                'counts': Reaction.get_counts(post_id)
            }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_message('server_error', 'en'),
            'message': 'Failed to add reaction'
        }), 500


@bp.route('/<int:post_id>/react', methods=['DELETE'])
@jwt_required()
def remove_reaction(post_id):
    """
    Remove user's reaction from a post.

    Returns:
        200: Reaction removed
        404: No reaction found or post not found
    """
    current_user_id = int(get_jwt_identity())

    # Check post exists
    post = Post.query.get(post_id)
    if not post:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('post_not_found')
        }), 404

    # Find existing reaction
    reaction = Reaction.query.filter_by(
        user_id=current_user_id,
        post_id=post_id
    ).first()

    if not reaction:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('no_reaction')
        }), 404

    try:
        db.session.delete(reaction)
        db.session.commit()

        return jsonify({
            'message': get_bilingual_message('reaction_removed'),
            'counts': Reaction.get_counts(post_id)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_message('server_error', 'en'),
            'message': 'Failed to remove reaction'
        }), 500


@bp.route('/<int:post_id>/reactions', methods=['GET'])
@jwt_required()
def get_reactions(post_id):
    """
    Get reaction counts for a post.

    Privacy Note:
    - Only aggregate counts are returned
    - Never shows "who reacted"
    - Includes current user's own reaction

    Returns:
        200: Reaction counts
        404: Post not found
    """
    current_user_id = int(get_jwt_identity())

    # Check post exists
    post = Post.query.get(post_id)
    if not post:
        return jsonify({
            'error': get_message('validation_error', 'en'),
            'message': get_bilingual_message('post_not_found')
        }), 404

    counts = Reaction.get_counts(post_id)
    my_reaction = Reaction.get_user_reaction(current_user_id, post_id)
    total = Reaction.get_total_count(post_id)

    return jsonify({
        'post_id': post_id,
        'reactions': counts,
        'total_reactions': total,
        'my_reaction': my_reaction
    }), 200

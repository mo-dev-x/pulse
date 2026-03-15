"""
Social Routes

Handles follow/unfollow, followers/following lists, friends, and user profiles.

Endpoints:
- POST   /api/follow/@{username}          — Follow a user
- DELETE /api/unfollow/@{username}        — Unfollow a user
- GET    /api/users/@{username}/followers — List user's followers
- GET    /api/users/@{username}/following — List user's following
- GET    /api/users/me/friends           — Mutual follows
- GET    /api/users/@{username}          — Public user profile
"""

from copy import deepcopy

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import cache, db
from app.models.user import User
from app.models.follower import Follower
from app.models.post import Post
from app.services.notification_service import create_notification
from app.utils.i18n import get_localized_message

# Create blueprint
bp = Blueprint('social', __name__)


def _public_profile_cache_key(username):
    return f'public_profile:{username.lower()}'


def _build_public_profile_base(user, current_user_id):
    recent_posts = Post.query.filter_by(
        user_id=user.id,
        is_anonymous=False
    ).order_by(Post.created_at.desc()).limit(10).all()

    pinned_post = None
    if user.pinned_post_id:
        pinned = Post.query.filter_by(id=user.pinned_post_id, user_id=user.id, is_anonymous=False).first()
        if pinned:
            pinned_post = pinned.to_dict(current_user_id=current_user_id)

    return {
        'user': {
            'id': user.id,
            'username': user.username,
            'display_name': user.display_name,
            'bio': user.bio,
            'profile_picture': user.profile_picture,
            'website': user.website,
            'location': user.location,
            'email': None,
            'profile_visibility': user.profile_visibility,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'follower_count': Follower.get_follower_count(user.id),
            'following_count': Follower.get_following_count(user.id),
        },
        'pinned_post': pinned_post,
        'recent_posts': [post.to_dict(current_user_id=current_user_id) for post in recent_posts]
    }


@bp.route('/follow/@<string:username>', methods=['POST'])
@jwt_required()
def follow_user(username):
    """
    Follow a user

    Returns:
        201: Successfully followed
        400: Can't follow self or already following
        404: User not found
    """
    current_user_id = int(get_jwt_identity())

    # Find target user
    target_user = User.query.filter_by(username=username.lower()).first()
    if not target_user:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_not_found')
        }), 404

    # Can't follow self
    if target_user.id == current_user_id:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'cannot_follow_self')
        }), 400

    # Check if already following
    if Follower.is_following(current_user_id, target_user.id):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'already_following')
        }), 400

    try:
        actor = User.query.get(current_user_id)
        new_follow = Follower(
            follower_id=current_user_id,
            following_id=target_user.id
        )
        db.session.add(new_follow)
        create_notification(
            user_id=target_user.id,
            notification_type='new_follower',
            title='New follower',
            message=f"{actor.display_name if actor else 'Someone'} started following you.",
            related_type='user',
            related_id=current_user_id,
            actor_id=current_user_id,
        )
        db.session.commit()

        return jsonify({
            'message': get_localized_message(request, 'follow_success'),
            'following': {
                'username': target_user.username,
                'display_name': target_user.display_name
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/unfollow/@<string:username>', methods=['DELETE'])
@jwt_required()
def unfollow_user(username):
    """
    Unfollow a user

    Returns:
        200: Successfully unfollowed
        400: Not following this user
        404: User not found
    """
    current_user_id = int(get_jwt_identity())

    # Find target user
    target_user = User.query.filter_by(username=username.lower()).first()
    if not target_user:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_not_found')
        }), 404

    # Find the follow record
    follow = Follower.query.filter_by(
        follower_id=current_user_id,
        following_id=target_user.id
    ).first()

    if not follow:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'not_following')
        }), 400

    try:
        db.session.delete(follow)
        db.session.commit()

        return jsonify({
            'message': get_localized_message(request, 'unfollow_success'),
            'unfollowed': {
                'username': target_user.username,
                'display_name': target_user.display_name
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/users/@<string:username>/followers', methods=['GET'])
@jwt_required()
def get_followers(username):
    """
    Get a user's followers list (paginated)

    Query Params:
        page (int): Page number (default 1)
        per_page (int): Items per page (default 20, max 50)
    """
    target_user = User.query.filter_by(username=username.lower()).first()
    if not target_user:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_not_found')
        }), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    followers_query = Follower.query.filter_by(
        following_id=target_user.id
    ).order_by(Follower.created_at.desc())

    paginated = followers_query.paginate(page=page, per_page=per_page, error_out=False)

    followers_list = []
    for follow in paginated.items:
        user = User.query.get(follow.follower_id)
        if user:
            followers_list.append({
                'id': user.id,
                'username': user.username,
                'display_name': user.display_name,
                'profile_picture': user.profile_picture,
                'followed_at': follow.created_at.isoformat() + 'Z' if follow.created_at else None
            })

    return jsonify({
        'user': username,
        'followers': followers_list,
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'has_next': paginated.has_next
    }), 200


@bp.route('/users/@<string:username>/following', methods=['GET'])
@jwt_required()
def get_following(username):
    """
    Get list of users that a user follows (paginated)

    Query Params:
        page (int): Page number (default 1)
        per_page (int): Items per page (default 20, max 50)
    """
    target_user = User.query.filter_by(username=username.lower()).first()
    if not target_user:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_not_found')
        }), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    following_query = Follower.query.filter_by(
        follower_id=target_user.id
    ).order_by(Follower.created_at.desc())

    paginated = following_query.paginate(page=page, per_page=per_page, error_out=False)

    following_list = []
    for follow in paginated.items:
        user = User.query.get(follow.following_id)
        if user:
            following_list.append({
                'id': user.id,
                'username': user.username,
                'display_name': user.display_name,
                'profile_picture': user.profile_picture,
                'followed_at': follow.created_at.isoformat() + 'Z' if follow.created_at else None
            })

    return jsonify({
        'user': username,
        'following': following_list,
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'has_next': paginated.has_next
    }), 200


@bp.route('/users/me/friends', methods=['GET'])
@jwt_required()
def get_friends():
    """
    Get current user's friends (mutual follows)
    """
    current_user_id = int(get_jwt_identity())

    friends = Follower.get_friends(current_user_id)

    friends_list = []
    for friend in friends:
        friends_list.append({
            'id': friend.id,
            'username': friend.username,
            'display_name': friend.display_name,
            'profile_picture': friend.profile_picture
        })

    return jsonify({
        'friends': friends_list,
        'total': len(friends_list)
    }), 200


@bp.route('/users/@<string:username>', methods=['GET'])
@jwt_required()
def get_user_profile(username):
    """
    Get public user profile with follower/following counts

    Returns:
        200: User profile
        404: User not found
    """
    current_user_id = int(get_jwt_identity())

    user = User.query.filter_by(username=username.lower()).first()
    if not user:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_not_found')
        }), 404
    if user.is_deactivated and user.id != current_user_id:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_not_found')
        }), 404

    if user.profile_visibility == 'private' and user.id != current_user_id:
        return jsonify({
            'error': get_localized_message(request, 'forbidden'),
            'message': get_localized_message(request, 'forbidden')
        }), 403
    if user.profile_visibility == 'followers' and user.id != current_user_id:
        if not Follower.is_following(current_user_id, user.id):
            return jsonify({
                'error': get_localized_message(request, 'forbidden'),
                'message': get_localized_message(request, 'forbidden')
            }), 403

    is_following = Follower.is_following(current_user_id, user.id)
    is_friend = Follower.is_following(current_user_id, user.id) and Follower.is_following(user.id, current_user_id)
    if user.profile_visibility == 'public' and user.id != current_user_id:
        cache_key = _public_profile_cache_key(user.username)
        base_payload = cache.get(cache_key)
        if base_payload is None:
            base_payload = _build_public_profile_base(user, current_user_id)
            cache.set(cache_key, base_payload, timeout=120)
        payload = deepcopy(base_payload)
    else:
        payload = _build_public_profile_base(user, current_user_id)

    payload['user']['email'] = user.email if user.show_email or user.id == current_user_id else None
    payload['user']['is_following'] = is_following
    payload['user']['is_friend'] = is_friend
    payload['user']['is_you'] = (user.id == current_user_id)

    return jsonify(payload), 200

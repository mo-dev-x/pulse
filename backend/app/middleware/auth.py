"""Authentication middleware helpers."""

from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.models.user import User
from app.utils.i18n import get_localized_message


def require_verification(func):
    """Allow access only to users with verified university identity."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'error': get_localized_message(request, 'unauthorized'),
                'message': get_localized_message(request, 'unauthorized')
            }), 401

        user = User.query.get(int(current_user_id))
        if not user:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'user_not_found')
            }), 404

        if not user.is_verified:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'verification_required')
            }), 403

        return func(*args, **kwargs)

    return wrapper

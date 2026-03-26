"""
Authentication Routes

Handles user registration, login, and logout.

Endpoints:
- POST /api/auth/register - Create new user account
- POST /api/auth/login - Authenticate and get JWT token
- POST /api/auth/logout - Invalidate token (client-side only for now)
"""

import os
import re
import secrets
import base64
import io
from datetime import datetime, timezone
from urllib.parse import urlencode

import jwt as pyjwt
import requests
from flask import Blueprint, request, jsonify, current_app, redirect, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency for local dev
    Image = None
try:
    import qrcode
except ImportError:  # pragma: no cover
    qrcode = None

from app import db, limiter, rate_limit_value
from app.models.post import Post
from app.models.session import Session
from app.models.user import User
from app.services import upsert_documents
from app.services.email_service import send_verification_email, send_password_reset_email
from app.services.security_log_service import log_security_event
from app.services.session_service import track_session, revoke_session
from app.services.totp_service import generate_secret, verify_totp, build_provisioning_uri
from app.utils.i18n import get_localized_message

# Create blueprint
bp = Blueprint('auth', __name__)


def _should_log_email_warning(error_message):
    """Keep expected SMTP-disabled test runs quiet while logging real delivery issues."""
    if current_app.testing and error_message == 'SMTP is not configured':
        return False
    return True


def _is_oidc_enabled():
    """Feature flag guard to keep OIDC code available but disabled by default."""
    return bool(current_app.config.get('ENABLE_OIDC_AUTH', False))


def _user_search_document(user):
    return {
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'bio': user.bio,
        'profile_picture': user.profile_picture,
        'profile_visibility': user.profile_visibility,
        'is_deactivated': bool(user.is_deactivated),
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def _allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def _resize_and_save_image(file_obj, destination_path, max_size):
    if Image is None:
        # Fallback keeps uploads functional in environments missing Pillow.
        with open(destination_path, 'wb') as output_file:
            file_obj.seek(0)
            output_file.write(file_obj.read())
        return

    image = Image.open(file_obj)
    image = image.convert('RGB')
    image.thumbnail(max_size)
    image.save(destination_path, format='JPEG', optimize=True, quality=85)

#Faten did this
def _get_upload_root():
    upload_root = current_app.config.get('UPLOAD_FOLDER')
    if not upload_root:
        upload_root = os.path.join(current_app.root_path, '..', 'uploads')
    return os.path.abspath(upload_root)


@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account
    
    Request Body:
        {
            "email": "user@university.edu",
            "password": "SecurePass123!",
            "username": "johndoe",
            "display_name": "John Doe"  (optional)
        }
    
    Returns:
        201: User created successfully with JWT token
        400: Validation error or user already exists
    
    Security:
    - Password is hashed with bcrypt before storage
    - Email and username uniqueness enforced
    - Input validation on all fields
    """
    data = request.get_json() or {}
    
    # Validate required fields
    required_fields = ['email', 'password', 'username']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, f'{field}_required')
            }), 400
    
    email = data['email'].strip()
    password = data['password']
    username = data['username'].strip()
    display_name = data.get('display_name', username).strip()
    
    # Validate email format
    if not User.validate_email(email):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'email_domain_error')
        }), 400
    
    # Validate username format
    if not User.validate_username(username):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'username_invalid')
        }), 400
    
    # Validate password strength
    if not User.validate_password_strength(password):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'password_weak')
        }), 400
    
    # Check if user already exists
    if User.query.filter_by(email=email.lower()).first():
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_exists_email')
        }), 400
    
    if User.query.filter_by(username=username.lower()).first():
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'user_exists_username')
        }), 400
    
    try:
        # Create new user (password will be hashed in __init__)
        new_user = User(
            email=email,
            password=password,
            username=username,
            display_name=display_name,
            is_verified=False
        )
        
        db.session.add(new_user)
        db.session.commit()

        # Best effort: attempt to send verification email without blocking registration.
        verification_email_sent = False
        verification_email_error = None
        try:
            verification_email_sent, verification_email_error = send_verification_email(new_user)
        except Exception as exc:
            verification_email_error = str(exc)

        if not verification_email_sent and _should_log_email_warning(verification_email_error):
            current_app.logger.warning(
                "Verification email not sent for user_id=%s email=%s reason=%s",
                new_user.id,
                new_user.email,
                verification_email_error or "unknown error",
            )
        
        # Generate JWT token (identity must be a string)
        access_token = create_access_token(identity=str(new_user.id))
        track_session(
            user_id=new_user.id,
            jwt_token=access_token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        try:
            upsert_documents('users', [_user_search_document(new_user)])
        except Exception:
            current_app.logger.warning('Meilisearch user upsert failed for user_id=%s', new_user.id)
        db.session.commit()
        
        response = {
            'message': get_localized_message(request, 'user_created'),
            'user': new_user.to_dict(include_private=True),
            'token': access_token,
            'verification_email_sent': verification_email_sent
        }
        if current_app.debug and not verification_email_sent:
            response['verification_email_error'] = verification_email_error or 'email delivery failed'

        return jsonify(response), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/login', methods=['POST'])
@limiter.limit(rate_limit_value('LOGIN_RATE_LIMIT', '10 per minute'))
def login():
    """
    Authenticate user and return JWT token
    
    Request Body:
        {
            "email": "user@university.edu",
            "password": "SecurePass123!"
        }
    
    Returns:
        200: Login successful with JWT token
        401: Invalid credentials
        403: Account disabled or email not verified
        400: Missing required fields
    
    Security:
    - Password verified using bcrypt
    - JWT token expires in 24 hours (configurable)
    - Updates last_login timestamp
    """
    data = request.get_json() or {}
    
    # Validate required fields
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'email_password_required')
        }), 400
    
    email = data['email'].strip().lower()
    password = data['password']
    
    # Find user by email
    user = User.query.filter_by(email=email).first()
    
    # Check if user exists and password is correct
    if not user or not user.password_hash or not user.check_password(password):
        log_security_event(
            event_type='login_failed',
            user_id=user.id if user else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            metadata={'reason': 'invalid_credentials', 'email': email},
        )
        db.session.commit()
        return jsonify({
            'error': get_localized_message(request, 'auth_failed'),
            'message': get_localized_message(request, 'invalid_credentials')
        }), 401
    
    # Check if account is active
    if not user.is_active:
        return jsonify({
            'error': get_localized_message(request, 'account_disabled'),
            'message': get_localized_message(request, 'account_disabled')
        }), 403

    if user.is_deactivated:
        return jsonify({
            'error': get_localized_message(request, 'account_disabled'),
            'message': get_localized_message(request, 'account_disabled')
        }), 403

    # Only verified users (email link or institutional SSO) can log in.
    if not user.is_verified:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'verification_required_login')
        }), 403

    if user.totp_enabled:
        totp_code = (data.get('totp_code') or '').strip()
        backup_code = (data.get('backup_code') or '').strip()

        if not totp_code and not backup_code:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': '2FA code is required',
                'requires_2fa': True
            }), 401

        validated = False
        if totp_code and user.totp_secret:
            validated = verify_totp(user.totp_secret, totp_code, valid_window=1)

        if not validated and backup_code:
            backup_codes = user.backup_codes or []
            if backup_code in backup_codes:
                backup_codes.remove(backup_code)
                user.backup_codes = backup_codes
                validated = True

        if not validated:
            log_security_event(
                event_type='2fa_verify_failed',
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
            )
            db.session.commit()
            return jsonify({
                'error': get_localized_message(request, 'auth_failed'),
                'message': 'Invalid 2FA code'
            }), 401
    
    try:
        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        log_security_event(
            event_type='login_success',
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
        )
        
        # Generate JWT token (identity must be a string)
        access_token = create_access_token(identity=str(user.id))
        track_session(
            user_id=user.id,
            jwt_token=access_token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.commit()
        try:
            upsert_documents('users', [_user_search_document(user)])
        except Exception:
            current_app.logger.warning('Meilisearch user upsert failed for user_id=%s', user.id)
        
        return jsonify({
            'message': get_localized_message(request, 'login_successful'),
            'user': user.to_dict(include_private=True),
            'token': access_token
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (client-side token invalidation)
    
    Note:
    - JWTs are stateless, so we can't truly invalidate them server-side
    - Client should delete the token from storage
    - Future enhancement: Add token blacklist for immediate invalidation
    
    Returns:
        200: Logout acknowledged
    """
    # In a more advanced implementation, we would:
    # 1. Add token to blacklist in Redis/database
    # 2. Check blacklist on every @jwt_required() request
    # For now, client handles token deletion
    
    claims = get_jwt()
    revoke_session(claims.get('jti'))
    log_security_event(
        event_type='logout',
        user_id=int(get_jwt_identity()),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()

    return jsonify({
        'message': get_localized_message(request, 'logout_successful'),
        'note': get_localized_message(request, 'logout_successful')
    }), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user's profile
    
    Headers:
        Authorization: Bearer <JWT_TOKEN>
    
    Returns:
        200: User profile data
        401: Missing or invalid token
    """
    try:
        # Get user ID from JWT token (comes back as string)
        user_id = int(get_jwt_identity())
        
        # Fetch user from database
        user = db.session.get(User, user_id)
        
        if not user:
            return jsonify({
                'error': get_localized_message(request, 'validation_error'),
                'message': get_localized_message(request, 'user_not_found')
            }), 404
        
        return jsonify({
            'user': user.to_dict(include_private=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/update-profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    """
    Update user profile (display_name, bio, profile_picture)
    
    Request Body (all fields optional):
        {
            "display_name": "John Doe",
            "bio": "Computer Science student",
            "profile_picture": "https://example.com/pic.jpg"
        }
    
    Returns:
        200: Profile updated successfully
        400: Validation error
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404
    
    data = request.get_json()
    
    try:
        # Update allowed fields
        if 'display_name' in data:
            display_name = data['display_name'].strip()
            if 1 <= len(display_name) <= 100:
                user.display_name = display_name
            else:
                return jsonify({
                    'error': get_localized_message(request, 'validation_error'),
                    'message': get_localized_message(request, 'display_name_invalid')
                }), 400
        
        if 'bio' in data:
            bio = data['bio'].strip()
            if len(bio) <= 500:
                user.bio = bio
            else:
                return jsonify({
                    'error': get_localized_message(request, 'validation_error'),
                    'message': get_localized_message(request, 'bio_too_long')
                }), 400
        
        if 'profile_picture' in data:
            # In production, validate this is a safe URL or uploaded file
            user.profile_picture = data['profile_picture']
        
        db.session.commit()
        try:
            upsert_documents('users', [_user_search_document(user)])
        except Exception:
            current_app.logger.warning('Meilisearch user upsert failed for user_id=%s', user.id)
        
        return jsonify({
            'message': get_localized_message(request, 'profile_updated'),
            'user': user.to_dict(include_private=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/update-pseudonym', methods=['PATCH'])
@jwt_required()
def update_pseudonym():
    """
    Update anonymous pseudonym (90-day cooldown)
    
    Request Body:
        {
            "pseudonym": "stressed_engineer"
        }
    
    Returns:
        200: Pseudonym updated successfully
        400: Cooldown not met or validation error
    
    Privacy Note:
    - This updates ALL past anonymous posts to show new pseudonym
    - This is intentional to prevent building "alt identities"
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404
    
    data = request.get_json()
    
    if 'pseudonym' not in data:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'pseudonym_required')
        }), 400
    
    new_pseudonym = data['pseudonym'].strip()
    
    try:
        user.update_pseudonym(new_pseudonym)
        db.session.commit()
        
        return jsonify({
            'message': get_localized_message(request, 'pseudonym_updated'),
            'pseudonym': user.pseudonym,
            'can_change_again_at': (
                user.pseudonym_last_changed.isoformat() 
                if user.pseudonym_last_changed 
                else None
            )
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500


@bp.route('/send-verification', methods=['POST'])
@jwt_required()
@limiter.limit(rate_limit_value('SEND_VERIFICATION_RATE_LIMIT', '5 per hour'))
def send_verification():
    """Send or resend a verification email for the current user."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    if user.is_verified:
        return jsonify({
            'message': get_localized_message(request, 'account_already_verified')
        }), 200

    sent = False
    error = None
    try:
        sent, error = send_verification_email(user)
    except Exception as exc:
        error = str(exc)

    if not sent and _should_log_email_warning(error):
        current_app.logger.warning(
            "Resend verification failed for user_id=%s email=%s reason=%s",
            user.id,
            user.email,
            error or "unknown error",
        )

    response = {
        'message': get_localized_message(request, 'verification_sent_generic')
    }
    if current_app.debug:
        response['verification_email_sent'] = sent
        if not sent:
            response['verification_email_error'] = error or 'email delivery failed'

    return jsonify(response), 200


@bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify email token and activate verified status."""
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        return jsonify({'error': get_localized_message(request, 'invalid_verification_token')}), 400

    if not user.verification_expires or user.verification_expires < datetime.now(timezone.utc).replace(tzinfo=None):
        return jsonify({'error': get_localized_message(request, 'verification_token_expired')}), 400

    user.is_verified = True
    user.verification_token = None
    user.verification_expires = None
    db.session.commit()

    return jsonify({
        'message': get_localized_message(request, 'email_verified_success'),
        'user': user.to_dict(include_private=True)
    }), 200


@bp.route('/forgot-password', methods=['POST'])
@limiter.limit(rate_limit_value('FORGOT_PASSWORD_RATE_LIMIT', '5 per hour'))
def forgot_password():
    """Request password reset link without revealing account existence."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()

    if User.validate_email(email):
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                sent, error = send_password_reset_email(user)
                if not sent and _should_log_email_warning(error):
                    current_app.logger.warning(
                        "Password reset email not sent for user_id=%s email=%s reason=%s",
                        user.id,
                        user.email,
                        error or "unknown error",
                    )
            except Exception as exc:
                current_app.logger.warning(
                    "Password reset email exception for email=%s reason=%s",
                    user.email,
                    str(exc),
                )

    return jsonify({
        'message': get_localized_message(request, 'reset_link_sent_generic')
    }), 200


@bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using a one-time token."""
    data = request.get_json() or {}
    token = (data.get('token') or '').strip()
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'token_new_password_required')
        }), 400

    if not User.validate_password_strength(new_password):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'password_weak')
        }), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'error': get_localized_message(request, 'invalid_reset_token')}), 400

    if not user.reset_expires or user.reset_expires < datetime.now(timezone.utc).replace(tzinfo=None):
        return jsonify({'error': get_localized_message(request, 'reset_token_expired')}), 400

    try:
        user.set_password(new_password)
        user.reset_token = None
        user.reset_expires = None
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': str(exc)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'error': get_localized_message(request, 'server_error'), 'message': get_localized_message(request, 'server_error')}), 500

    return jsonify({'message': get_localized_message(request, 'password_reset_success')}), 200


@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change the current user's password using their existing password."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    data = request.get_json() or {}
    current_password = data.get('current_password') or ''
    new_password = data.get('new_password') or ''

    if not current_password or not new_password:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': 'Current password and new password are required'
        }), 400

    if not user.check_password(current_password):
        return jsonify({
            'error': get_localized_message(request, 'auth_failed'),
            'message': 'Current password is incorrect'
        }), 401

    if current_password == new_password:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': 'New password must be different from the current password'
        }), 400

    if not User.validate_password_strength(new_password):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'password_weak')
        }), 400

    try:
        user.set_password(new_password)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': str(exc)
        }), 400
    except Exception:
        db.session.rollback()
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500

    return jsonify({'message': 'Password changed successfully'}), 200


def _resolve_account_type(claims):
    """Map OIDC affiliation-like claims to local account_type enum."""
    affiliation = str(
        claims.get('eduPersonPrimaryAffiliation', '')
        or claims.get('affiliation', '')
        or claims.get('employeeType', '')
    ).lower()

    if 'staff' in affiliation:
        return 'staff'
    if 'faculty' in affiliation or 'prof' in affiliation:
        return 'faculty'
    if 'alumni' in affiliation:
        return 'alumni'
    return 'student'


def _extract_identity_from_claims(claims):
    """Extract stable identity id, email and display name from OIDC claims."""
    email = (
        claims.get('email')
        or claims.get('upn')
        or claims.get('preferred_username')
        or claims.get('userPrincipalName')
    )
    external_id = claims.get('oid') or claims.get('sub')
    display_name = claims.get('name') or claims.get('displayName')
    return external_id, email, display_name


def _upsert_user_from_oidc_claims(claims):
    """Create/update local user from validated institutional OIDC claims."""
    external_id, oidc_email, display_name = _extract_identity_from_claims(claims)
    if not oidc_email or not User.validate_email(oidc_email):
        return None, ({
            'error': get_localized_message(request, 'oidc_invalid_ulaval_email')
        }, 400)

    if not external_id:
        return None, ({
            'error': get_localized_message(request, 'oidc_missing_identity')
        }, 400)

    # Keep existing DB column for now. `cas_username` stores institutional unique id (OID/sub).
    db_user = User.query.filter_by(email=oidc_email.lower()).first()
    id_owner = User.query.filter_by(cas_username=external_id).first()
    if id_owner and (not db_user or id_owner.id != db_user.id):
        return None, ({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'cas_identity_conflict')
        }, 409)

    account_type = _resolve_account_type(claims)
    if not db_user:
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(external_id).lower())
        generated_username = f"u{sanitized}"[:50]
        if len(generated_username) < 3:
            generated_username = f"user_{secrets.token_hex(2)}"
        if User.query.filter_by(username=generated_username).first():
            generated_username = f"u{generated_username}_{secrets.token_hex(3)}"[:50]

        db_user = User(
            email=oidc_email,
            password=None,
            username=generated_username,
            display_name=display_name or str(external_id),
            is_verified=True,
            cas_username=str(external_id),
            account_type=account_type
        )
        db.session.add(db_user)
    else:
        db_user.cas_username = str(external_id)
        db_user.is_verified = True
        db_user.account_type = account_type
        if display_name:
            db_user.display_name = display_name

    db.session.commit()
    return db_user, None


@bp.route('/oidc/login', methods=['GET'])
def oidc_login():
    """Redirect user to OIDC provider authorize endpoint (Azure Entra)."""
    if not _is_oidc_enabled():
        return jsonify({
            'error': get_localized_message(request, 'oidc_unavailable'),
            'message': get_localized_message(request, 'oidc_disabled')
        }), 503

    authorize_url = current_app.config.get('OIDC_AUTHORIZE_URL')
    client_id = current_app.config.get('OIDC_CLIENT_ID')
    redirect_uri = current_app.config.get('OIDC_REDIRECT_URI')
    scope = current_app.config.get('OIDC_SCOPE', 'openid profile email')

    if not authorize_url or not client_id or not redirect_uri:
        return jsonify({
            'error': get_localized_message(request, 'oidc_unavailable'),
            'message': get_localized_message(request, 'oidc_missing_config')
        }), 503

    state = secrets.token_urlsafe(24)
    session['oidc_state'] = state
    query = urlencode({
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'response_mode': 'query',
        'scope': scope,
        'state': state,
    })
    return redirect(f'{authorize_url}?{query}')


@bp.route('/oidc/callback', methods=['GET'])
def oidc_callback():
    """Handle OIDC callback, validate code flow, then issue API JWT."""
    if not _is_oidc_enabled():
        return jsonify({
            'error': get_localized_message(request, 'oidc_unavailable'),
            'message': get_localized_message(request, 'oidc_disabled')
        }), 503

    error = request.args.get('error')
    if error:
        return jsonify({'error': get_localized_message(request, 'auth_failed')}), 401

    code = request.args.get('code')
    state = request.args.get('state')
    expected_state = session.pop('oidc_state', None)
    if not code or not state or state != expected_state:
        return jsonify({'error': get_localized_message(request, 'invalid_oidc_state')}), 400

    token_url = current_app.config.get('OIDC_TOKEN_URL')
    redirect_uri = current_app.config.get('OIDC_REDIRECT_URI')
    client_id = current_app.config.get('OIDC_CLIENT_ID')
    client_secret = current_app.config.get('OIDC_CLIENT_SECRET')
    userinfo_url = current_app.config.get('OIDC_USERINFO_URL')

    if not token_url or not redirect_uri or not client_id or not userinfo_url:
        return jsonify({
            'error': get_localized_message(request, 'oidc_unavailable'),
            'message': get_localized_message(request, 'oidc_missing_config')
        }), 503

    token_payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
    }
    if client_secret:
        token_payload['client_secret'] = client_secret

    try:
        token_resp = requests.post(token_url, data=token_payload, timeout=10)
        if token_resp.status_code >= 400:
            return jsonify({'error': get_localized_message(request, 'auth_failed')}), 401
        token_data = token_resp.json()
    except Exception:
        return jsonify({'error': get_localized_message(request, 'oidc_provider_error')}), 502

    access_token = token_data.get('access_token')
    id_token = token_data.get('id_token')
    if not access_token:
        return jsonify({'error': get_localized_message(request, 'auth_failed')}), 401

    claims = {}
    try:
        userinfo_resp = requests.get(
            userinfo_url,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        if userinfo_resp.status_code < 400:
            claims = userinfo_resp.json() or {}
    except Exception:
        claims = {}

    # Fallback if userinfo isn't available: parse ID token claims (without signature verify).
    if not claims and id_token:
        try:
            claims = pyjwt.decode(id_token, options={"verify_signature": False}) or {}
        except Exception:
            claims = {}

    if not claims:
        return jsonify({'error': get_localized_message(request, 'oidc_provider_error')}), 502

    db_user, err = _upsert_user_from_oidc_claims(claims)
    if err:
        body, status = err
        return jsonify(body), status

    token = create_access_token(identity=str(db_user.id))
    track_session(
        user_id=db_user.id,
        jwt_token=token,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    log_security_event(
        event_type='login_success',
        user_id=db_user.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        metadata={'provider': 'oidc'}
    )
    db.session.commit()
    return jsonify({
        'message': get_localized_message(request, 'oidc_auth_success'),
        'token': token,
        'user': db_user.to_dict(include_private=True)
    }), 200


# Legacy CAS routes kept temporarily for compatibility with older frontend links.
@bp.route('/cas/login', methods=['GET'])
def cas_login_legacy_redirect():
    if not _is_oidc_enabled():
        return jsonify({
            'error': get_localized_message(request, 'oidc_unavailable'),
            'message': get_localized_message(request, 'oidc_disabled')
        }), 503
    return redirect('/api/auth/oidc/login')


@bp.route('/cas/callback', methods=['GET'])
def cas_callback_legacy_redirect():
    if not _is_oidc_enabled():
        return jsonify({
            'error': get_localized_message(request, 'oidc_unavailable'),
            'message': get_localized_message(request, 'oidc_disabled')
        }), 503
    query = request.query_string.decode('utf-8')
    return redirect(f'/api/auth/oidc/callback?{query}' if query else '/api/auth/oidc/callback')


@bp.route('/update-bio', methods=['PATCH'])
@jwt_required()
def update_bio():
    """Update only the bio field (max 500 chars)."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    data = request.get_json() or {}
    bio = (data.get('bio') or '').strip()
    if len(bio) > 500:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'bio_too_long')
        }), 400

    user.bio = bio or None
    db.session.commit()
    try:
        upsert_documents('users', [_user_search_document(user)])
    except Exception:
        current_app.logger.warning('Meilisearch user upsert failed for user_id=%s', user.id)
    return jsonify({'message': get_localized_message(request, 'bio_updated_success'), 'user': user.to_dict(include_private=True)}), 200


def _handle_image_upload(user, request_key, upload_folder, filename_prefix, size):
    if request_key not in request.files:
        return None, ({'error': get_localized_message(request, 'validation_error'), 'message': get_localized_message(request, 'no_file_uploaded')}, 400)

    file = request.files[request_key]
    if not file or not file.filename:
        return None, ({'error': get_localized_message(request, 'validation_error'), 'message': get_localized_message(request, 'no_file_uploaded')}, 400)

    if not _allowed_file(file.filename):
        return None, ({'error': get_localized_message(request, 'validation_error'), 'message': get_localized_message(request, 'file_type_invalid')}, 400)

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > current_app.config.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024):
        return None, ({'error': get_localized_message(request, 'validation_error'), 'message': get_localized_message(request, 'file_too_large')}, 400)

    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(f"{filename_prefix}_{user.id}_{secrets.token_hex(8)}.jpg")
    destination = os.path.join(upload_folder, filename)

    try:
        _resize_and_save_image(file.stream, destination, size)
    except Exception as exc:
        return None, ({'error': get_localized_message(request, 'server_error'), 'message': str(exc)}, 500)

    return filename, None


@bp.route('/upload-profile-pic', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    """Upload and resize profile picture to 500x500 max."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    # upload_folder = current_app.config.get('PROFILE_UPLOAD_FOLDER', 'uploads/profiles') Faten did this
    upload_folder = os.path.join(_get_upload_root(), 'profiles')

    filename, error = _handle_image_upload(
        user=user,
        request_key='file',
        upload_folder=upload_folder,
        filename_prefix='profile',
        size=(500, 500)
    )
    if error:
        body, status = error
        return jsonify(body), status

    old_filename = user.profile_picture
    user.profile_picture = f'profiles/{filename}'
    db.session.commit()
    try:
        upsert_documents('users', [_user_search_document(user)])
    except Exception:
        current_app.logger.warning('Meilisearch user upsert failed for user_id=%s', user.id)

    # if old_filename:
    #     old_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads/'), old_filename)
    #     if os.path.exists(old_path):
    #         os.remove(old_path)
    #Faten did this 
    if old_filename:
        old_path = os.path.join(_get_upload_root(), old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    return jsonify({
        'message': get_localized_message(request, 'profile_picture_updated'),
        'profile_picture': user.profile_picture,
        'profile_picture_url': f"/uploads/{user.profile_picture}"
    }), 200


@bp.route('/upload-header', methods=['POST'])
@jwt_required()
def upload_header_image():
    """Upload and resize header image to 1500x500 max."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    # upload_folder = current_app.config.get('HEADER_UPLOAD_FOLDER', 'uploads/headers') Faten did this
    upload_folder = os.path.join(_get_upload_root(), 'headers')
    
    filename, error = _handle_image_upload(
        user=user,
        request_key='file',
        upload_folder=upload_folder,
        filename_prefix='header',
        size=(1500, 500)
    )
    if error:
        body, status = error
        return jsonify(body), status

    old_filename = user.header_image
    user.header_image = f'headers/{filename}'
    db.session.commit()
    try:
        upsert_documents('users', [_user_search_document(user)])
    except Exception:
        current_app.logger.warning('Meilisearch user upsert failed for user_id=%s', user.id)

    if old_filename:
        old_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads/'), old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    return jsonify({
        'message': get_localized_message(request, 'header_image_updated'),
        'header_image': user.header_image,
        'header_image_url': f"/uploads/{user.header_image}"
    }), 200


@bp.route('/sessions', methods=['GET'])
@jwt_required()
def list_sessions():
    """List active sessions for the authenticated user."""
    user_id = int(get_jwt_identity())
    sessions = Session.query.filter_by(user_id=user_id, is_active=True).order_by(Session.created_at.desc()).all()
    return jsonify({'sessions': [s.to_dict() for s in sessions], 'total': len(sessions)}), 200


@bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def revoke_one_session(session_id):
    """Revoke one of the authenticated user's sessions."""
    user_id = int(get_jwt_identity())
    current_jti = get_jwt().get('jti')
    session_row = Session.query.filter_by(id=session_id, user_id=user_id).first()
    if not session_row:
        return jsonify({'error': get_localized_message(request, 'not_found')}), 404
    if session_row.token_jti == current_jti:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'Cannot revoke current session here'}), 400

    session_row.is_active = False
    log_security_event(
        event_type='session_revoked',
        user_id=user_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        metadata={'session_id': session_id},
    )
    db.session.commit()
    return jsonify({'message': 'Session revoked'}), 200


@bp.route('/sessions/all', methods=['DELETE'])
@jwt_required()
def revoke_all_sessions():
    """Revoke all active sessions except the current session."""
    user_id = int(get_jwt_identity())
    current_jti = get_jwt().get('jti')
    sessions = Session.query.filter(
        Session.user_id == user_id,
        Session.is_active == True,  # noqa: E712
        Session.token_jti != current_jti
    ).all()
    for session_row in sessions:
        session_row.is_active = False

    log_security_event(
        event_type='session_revoked',
        user_id=user_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        metadata={'scope': 'all_except_current', 'count': len(sessions)},
    )
    db.session.commit()
    return jsonify({'message': 'Sessions revoked', 'revoked': len(sessions)}), 200


@bp.route('/privacy-settings', methods=['PATCH'])
@jwt_required()
def update_privacy_settings():
    """Update user profile privacy settings."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    data = request.get_json() or {}
    profile_visibility = data.get('profile_visibility')
    show_email = data.get('show_email')

    if profile_visibility is not None:
        if profile_visibility not in {'public', 'followers', 'private'}:
            return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'Invalid profile_visibility'}), 400
        user.profile_visibility = profile_visibility

    if show_email is not None:
        user.show_email = bool(show_email)

    db.session.commit()
    return jsonify({'message': 'Privacy settings updated', 'user': user.to_dict(include_private=True)}), 200


@bp.route('/preferences', methods=['PATCH'])
@jwt_required()
def update_preferences():
    """Update user UI/notification preferences."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    data = request.get_json() or {}
    theme = data.get('theme')
    if theme is not None:
        if theme not in {'light', 'dark', 'auto'}:
            return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'Invalid theme'}), 400
        user.theme = theme

    if 'email_notifications' in data:
        user.email_notifications = bool(data.get('email_notifications'))
    if 'push_notifications' in data:
        user.push_notifications = bool(data.get('push_notifications'))

    db.session.commit()
    return jsonify({'message': 'Preferences updated', 'user': user.to_dict(include_private=True)}), 200


def _generate_backup_codes():
    return [secrets.token_hex(4) for _ in range(10)]


def _build_qr_code_data_url(uri):
    if qrcode is None:
        return None
    image = qrcode.make(uri)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f'data:image/png;base64,{encoded}'


@bp.route('/2fa/enable', methods=['POST'])
@jwt_required()
def enable_2fa():
    """Initialize TOTP setup and return provisioning payload."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    if user.totp_enabled:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': '2FA already enabled'}), 400

    secret = generate_secret()
    user.totp_secret = secret
    user.backup_codes = _generate_backup_codes()
    provisioning_uri = build_provisioning_uri(secret, name=user.email, issuer_name='Pulse ULaval')
    db.session.commit()

    return jsonify({
        'message': '2FA setup initialized. Verify one code to complete enablement.',
        'totp_secret': secret,
        'provisioning_uri': provisioning_uri,
        'qr_code_data_url': _build_qr_code_data_url(provisioning_uri),
        'backup_codes': user.backup_codes,
    }), 200


@bp.route('/2fa/verify', methods=['POST'])
@jwt_required()
def verify_2fa():
    """Verify TOTP code and finalize 2FA enablement."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or not user.totp_secret:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': '2FA is not initialized'}), 400

    code = (request.get_json() or {}).get('code', '').strip()
    if not code:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'Code is required'}), 400

    valid = verify_totp(user.totp_secret, code, valid_window=1)
    if not valid:
        log_security_event(
            event_type='2fa_verify_failed',
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
        )
        db.session.commit()
        return jsonify({'error': get_localized_message(request, 'auth_failed'), 'message': 'Invalid 2FA code'}), 401

    user.totp_enabled = True
    log_security_event(
        event_type='2fa_enabled',
        user_id=user_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
    return jsonify({'message': '2FA enabled successfully'}), 200


@bp.route('/2fa/disable', methods=['POST'])
@jwt_required()
def disable_2fa():
    """Disable 2FA after verifying current TOTP or backup code."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or not user.totp_enabled or not user.totp_secret:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': '2FA is not enabled'}), 400

    payload = request.get_json() or {}
    code = (payload.get('code') or '').strip()
    backup_code = (payload.get('backup_code') or '').strip()

    valid = False
    if code:
        valid = verify_totp(user.totp_secret, code, valid_window=1)
    if not valid and backup_code:
        backup_codes = user.backup_codes or []
        if backup_code in backup_codes:
            backup_codes.remove(backup_code)
            user.backup_codes = backup_codes
            valid = True

    if not valid:
        return jsonify({'error': get_localized_message(request, 'auth_failed'), 'message': 'Invalid 2FA code'}), 401

    user.totp_enabled = False
    user.totp_secret = None
    user.backup_codes = None
    log_security_event(
        event_type='2fa_disabled',
        user_id=user_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
    return jsonify({'message': '2FA disabled'}), 200


@bp.route('/2fa/backup-codes', methods=['GET'])
@jwt_required()
def regenerate_backup_codes():
    """Regenerate 2FA backup codes."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or not user.totp_enabled:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': '2FA is not enabled'}), 400

    user.backup_codes = _generate_backup_codes()
    db.session.commit()
    return jsonify({'backup_codes': user.backup_codes}), 200


@bp.route('/deactivate', methods=['POST'])
@jwt_required()
def deactivate_account():
    """Deactivate account without deleting user data."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404
    if user.is_deactivated:
        return jsonify({'message': 'Account already deactivated'}), 200

    user.is_deactivated = True
    user.deactivated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    user.is_active = False
    log_security_event(
        event_type='account_deactivated',
        user_id=user_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
    return jsonify({'message': 'Account deactivated', 'deactivated_at': user.deactivated_at.isoformat() + 'Z'}), 200


@bp.route('/reactivate', methods=['POST'])
@jwt_required()
def reactivate_account():
    """Reactivate previously deactivated account."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    user.is_deactivated = False
    user.deactivated_at = None
    user.is_active = True
    log_security_event(
        event_type='account_reactivated',
        user_id=user_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
    return jsonify({'message': 'Account reactivated'}), 200

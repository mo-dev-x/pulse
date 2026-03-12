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
from datetime import datetime
from urllib.parse import urlencode

import jwt as pyjwt
import requests
from flask import Blueprint, request, jsonify, current_app, redirect, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency for local dev
    Image = None

from app import db
from app.models.user import User
from app.services.email_service import send_verification_email, send_password_reset_email
from app.utils.i18n import get_localized_message

# Create blueprint
bp = Blueprint('auth', __name__)


def _is_oidc_enabled():
    """Feature flag guard to keep OIDC code available but disabled by default."""
    return bool(current_app.config.get('ENABLE_OIDC_AUTH', False))


def _allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def _resize_and_save_image(file_obj, destination_path, max_size):
    if Image is None:
        raise ValueError('Image processing is unavailable (Pillow not installed)')

    image = Image.open(file_obj)
    image = image.convert('RGB')
    image.thumbnail(max_size)
    image.save(destination_path, format='JPEG', optimize=True, quality=85)


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

        if not verification_email_sent:
            current_app.logger.warning(
                "Verification email not sent for user_id=%s email=%s reason=%s",
                new_user.id,
                new_user.email,
                verification_email_error or "unknown error",
            )
        
        # Generate JWT token (identity must be a string)
        access_token = create_access_token(identity=str(new_user.id))
        
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

    # Only verified users (email link or institutional SSO) can log in.
    if not user.is_verified:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'verification_required_login')
        }), 403
    
    try:
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token (identity must be a string)
        access_token = create_access_token(identity=str(user.id))
        
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
        user = User.query.get(user_id)
        
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
    user = User.query.get(user_id)
    
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
    user = User.query.get(user_id)
    
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
def send_verification():
    """Send or resend a verification email for the current user."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

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

    if not sent:
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

    if not user.verification_expires or user.verification_expires < datetime.utcnow():
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
def forgot_password():
    """Request password reset link without revealing account existence."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()

    if User.validate_email(email):
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                sent, error = send_password_reset_email(user)
                if not sent:
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

    if not user.reset_expires or user.reset_expires < datetime.utcnow():
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
    user = User.query.get(user_id)
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
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    upload_folder = current_app.config.get('PROFILE_UPLOAD_FOLDER', 'uploads/profiles')
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

    if old_filename:
        old_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads/'), old_filename)
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
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': get_localized_message(request, 'user_not_found')}), 404

    upload_folder = current_app.config.get('HEADER_UPLOAD_FOLDER', 'uploads/headers')
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

    if old_filename:
        old_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads/'), old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    return jsonify({
        'message': get_localized_message(request, 'header_image_updated'),
        'header_image': user.header_image,
        'header_image_url': f"/uploads/{user.header_image}"
    }), 200

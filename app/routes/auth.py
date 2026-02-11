"""
Authentication Routes

Handles user registration, login, and logout.

Endpoints:
- POST /api/auth/register - Create new user account
- POST /api/auth/login - Authenticate and get JWT token
- POST /api/auth/logout - Invalidate token (client-side only for now)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime

from app import db
from app.models.user import User

# Create blueprint
bp = Blueprint('auth', __name__)


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
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'username']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'error': 'Validation error',
                'message': f'{field} is required'
            }), 400
    
    email = data['email'].strip()
    password = data['password']
    username = data['username'].strip()
    display_name = data.get('display_name', username).strip()
    
    # Validate email format
    if not User.validate_email(email):
        return jsonify({
            'error': 'Validation error',
            'message': 'Invalid email format'
        }), 400
    
    # Validate username format
    if not User.validate_username(username):
        return jsonify({
            'error': 'Validation error',
            'message': 'Username must be 3-50 characters, alphanumeric and underscores only, cannot start with number'
        }), 400
    
    # Validate password strength
    if not User.validate_password_strength(password):
        return jsonify({
            'error': 'Validation error',
            'message': 'Password must be at least 8 characters with uppercase, lowercase, and digit'
        }), 400
    
    # Check if user already exists
    if User.query.filter_by(email=email.lower()).first():
        return jsonify({
            'error': 'User already exists',
            'message': 'An account with this email already exists'
        }), 400
    
    if User.query.filter_by(username=username.lower()).first():
        return jsonify({
            'error': 'User already exists',
            'message': 'This username is already taken'
        }), 400
    
    try:
        # Create new user (password will be hashed in __init__)
        new_user = User(
            email=email,
            password=password,
            username=username,
            display_name=display_name
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT token (identity must be a string)
        access_token = create_access_token(identity=str(new_user.id))
        
        return jsonify({
            'message': 'User created successfully',
            'user': new_user.to_dict(include_private=True),
            'token': access_token
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'error': 'Validation error',
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server error',
            'message': 'Failed to create user'
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
        400: Missing required fields
    
    Security:
    - Password verified using bcrypt
    - JWT token expires in 24 hours (configurable)
    - Updates last_login timestamp
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'error': 'Validation error',
            'message': 'Email and password are required'
        }), 400
    
    email = data['email'].strip().lower()
    password = data['password']
    
    # Find user by email
    user = User.query.filter_by(email=email).first()
    
    # Check if user exists and password is correct
    if not user or not user.check_password(password):
        return jsonify({
            'error': 'Authentication failed',
            'message': 'Invalid email or password'
        }), 401
    
    # Check if account is active
    if not user.is_active:
        return jsonify({
            'error': 'Account disabled',
            'message': 'Your account has been deactivated'
        }), 403
    
    try:
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token (identity must be a string)
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(include_private=True),
            'token': access_token
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server error',
            'message': 'Login failed'
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
        'message': 'Logout successful',
        'note': 'Please delete your token from client storage'
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
        user_id = get_jwt_identity()
        
        # Fetch user from database
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'message': 'Your account no longer exists'
            }), 404
        
        return jsonify({
            'user': user.to_dict(include_private=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Server error',
            'message': 'Failed to fetch user data'
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
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update allowed fields
        if 'display_name' in data:
            display_name = data['display_name'].strip()
            if 1 <= len(display_name) <= 100:
                user.display_name = display_name
            else:
                return jsonify({
                    'error': 'Validation error',
                    'message': 'Display name must be 1-100 characters'
                }), 400
        
        if 'bio' in data:
            bio = data['bio'].strip()
            if len(bio) <= 500:
                user.bio = bio
            else:
                return jsonify({
                    'error': 'Validation error',
                    'message': 'Bio must be 500 characters or less'
                }), 400
        
        if 'profile_picture' in data:
            # In production, validate this is a safe URL or uploaded file
            user.profile_picture = data['profile_picture']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict(include_private=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server error',
            'message': 'Failed to update profile'
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
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'pseudonym' not in data:
        return jsonify({
            'error': 'Validation error',
            'message': 'Pseudonym is required'
        }), 400
    
    new_pseudonym = data['pseudonym'].strip()
    
    try:
        user.update_pseudonym(new_pseudonym)
        db.session.commit()
        
        return jsonify({
            'message': 'Pseudonym updated successfully',
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
            'error': 'Validation error',
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server error',
            'message': 'Failed to update pseudonym'
        }), 500
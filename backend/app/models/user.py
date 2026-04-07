"""
User Model

Represents a user account with public and anonymous identities.

Key Features:
- Password hashing (never stores plaintext)
- Persistent pseudonym for anonymous posts
- Methods for validation and authentication
"""

from datetime import datetime, timezone
from app import db
import bcrypt
import re


class User(db.Model):
    """
    User model for authentication and profile management
    
    Privacy Note:
    - user_id is stored in posts table even for anonymous posts
    - API layer ensures user_id is never exposed for anonymous posts
    """
    
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Authentication
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(255), nullable=True, index=True)
    verification_expires = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(255), nullable=True, index=True)
    reset_expires = db.Column(db.DateTime, nullable=True)
    cas_username = db.Column(db.String(50), nullable=True, unique=True, index=True)
    account_type = db.Column(
        db.Enum('student', 'staff', 'faculty', 'alumni', name='account_type_enum'),
        default='student',
        nullable=False
    )
    
    # Public identity
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(500))
    header_image = db.Column(db.String(500))
    website = db.Column(db.String(255))
    location = db.Column(db.String(100))

    # Privacy settings
    profile_visibility = db.Column(
        db.Enum('public', 'followers', 'private', name='profile_visibility_enum'),
        default='public',
        nullable=False
    )
    show_email = db.Column(db.Boolean, default=False, nullable=False)

    # Preferences
    theme = db.Column(
        db.Enum('light', 'dark', 'auto', name='theme_enum'),
        default='auto',
        nullable=False
    )
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    push_notifications = db.Column(db.Boolean, default=True, nullable=False)

    # Two-factor authentication
    totp_secret = db.Column(db.String(32), nullable=True)
    totp_enabled = db.Column(db.Boolean, default=False, nullable=False)
    backup_codes = db.Column(db.JSON, nullable=True)

    # Account status and profile pinning
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_deactivated = db.Column(db.Boolean, default=False, nullable=False)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    pinned_post_id = db.Column(
        db.Integer,
        db.ForeignKey('posts.id', use_alter=True, name='fk_user_pinned_post'),
        nullable=True
    )
    
    # Anonymous identity (persistent pseudonym)
    pseudonym = db.Column(db.String(50), nullable=False, default='anonymous')
    pseudonym_last_changed = db.Column(db.DateTime, nullable=True)
    
    # Language preference (Université Laval bilingual community)
    preferred_language = db.Column(
        db.Enum('en', 'fr'),
        default='fr',
        nullable=False
    )
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships (we'll define these when we create the other models)
    # posts = db.relationship('Post', backref='author', lazy='dynamic')
    # followers = db.relationship('Follower', foreign_keys='Follower.following_id', backref='following', lazy='dynamic')
    # following = db.relationship('Follower', foreign_keys='Follower.follower_id', backref='follower', lazy='dynamic')
    
    def __init__(self, email, password, username, display_name=None, is_verified=False, cas_username=None, account_type='student'):
        """
        Create a new user
        
        Args:
            email (str): User's email address
            password (str): Plain text password (will be hashed)
            username (str): Unique username (3-50 chars)
            display_name (str, optional): Display name for profile
        """
        self.email = email.lower().strip()
        self.username = username.lower().strip()
        self.display_name = display_name or username
        self.is_verified = is_verified
        self.cas_username = cas_username
        self.account_type = account_type

        if password:
            self.set_password(password)
        else:
            self.password_hash = None
    
    def set_password(self, password):
        """
        Hash and store password using bcrypt
        
        Args:
            password (str): Plain text password
        
        Security:
        - Uses bcrypt with automatic salt generation
        - Never stores plain text passwords
        - Password hash is 60 characters
        """
        # Validate password strength
        if not self.validate_password_strength(password):
            raise ValueError("Password does not meet requirements")
        
        # Hash password (bcrypt automatically handles salting)
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        self.password_hash = hashed.decode('utf-8')
    
    def check_password(self, password):
        """
        Verify password against stored hash
        
        Args:
            password (str): Plain text password to check
        
        Returns:
            bool: True if password matches, False otherwise
        """
        if not self.password_hash:
            return False

        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    
    @staticmethod
    def validate_email(email):
        """
        Validate email format and domain (Université Laval only)
        
        Args:
            email (str): Email address to validate
        
        Returns:
            bool: True if valid @ulaval.ca email, False otherwise
        """
        # Must be @ulaval.ca email
        if not email.lower().endswith('@ulaval.ca'):
            return False
        
        # Check basic email format
        pattern = r'^[a-zA-Z0-9._%+-]+@ulaval\.ca$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password):
        """
        Validate password meets security requirements
        
        Requirements:
        - At least 8 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        
        Args:
            password (str): Password to validate
        
        Returns:
            bool: True if meets requirements, False otherwise
        """
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit
    
    @staticmethod
    def validate_username(username):
        """
        Validate username format
        
        Requirements:
        - 3-50 characters
        - Alphanumeric and underscores only
        - Cannot start with number
        
        Args:
            username (str): Username to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if len(username) < 3 or len(username) > 50:
            return False
        
        if username[0].isdigit():
            return False
        
        pattern = r'^[a-zA-Z0-9_]+$'
        return re.match(pattern, username) is not None
    
    def update_pseudonym(self, new_pseudonym):
        """
        Update anonymous pseudonym (90-day cooldown enforced)
        
        Args:
            new_pseudonym (str): New pseudonym
        
        Raises:
            ValueError: If cooldown period not met or pseudonym invalid
        
        Note:
            This updates ALL past anonymous posts to show new pseudonym.
            This is intentional to prevent building "alt identities".
        """
        # Check cooldown
        if self.pseudonym_last_changed:
            days_since = (datetime.now(timezone.utc).replace(tzinfo=None) - self.pseudonym_last_changed).days
            if days_since < 90:
                raise ValueError(f"Can change pseudonym in {90 - days_since} days")
        
        # Validate new pseudonym
        if len(new_pseudonym) < 3 or len(new_pseudonym) > 50:
            raise ValueError("Pseudonym must be 3-50 characters")
        
        # Check for reserved names
        reserved = ['admin', 'administrator', 'system', 'pulse', 'anonymous', 'moderator']
        if new_pseudonym.lower() in reserved:
            raise ValueError("This pseudonym is reserved")
        
        # Update
        self.pseudonym = new_pseudonym
        self.pseudonym_last_changed = datetime.now(timezone.utc).replace(tzinfo=None)
    
    def to_dict(self, include_private=False):
        """
        Serialize user to dictionary
        
        Args:
            include_private (bool): Include private fields (email, etc.)
        
        Returns:
            dict: User data
        """
        data = {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'bio': self.bio,
            'profile_picture': self.profile_picture,
            'header_image': self.header_image,
            'website': self.website,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_admin': self.is_admin
        }

        if include_private:
            data['email'] = self.email
            data['pseudonym'] = self.pseudonym
            data['can_change_pseudonym'] = self.can_change_pseudonym()
            data['is_verified'] = self.is_verified
            data['cas_username'] = self.cas_username
            data['account_type'] = self.account_type
            data['profile_visibility'] = self.profile_visibility
            data['show_email'] = self.show_email
            data['theme'] = self.theme
            data['email_notifications'] = self.email_notifications
            data['push_notifications'] = self.push_notifications
            data['totp_enabled'] = self.totp_enabled
            data['is_admin'] = self.is_admin
            data['is_deactivated'] = self.is_deactivated
            data['deactivated_at'] = self.deactivated_at.isoformat() if self.deactivated_at else None
            data['pinned_post_id'] = self.pinned_post_id

        return data
    
    def can_change_pseudonym(self):
        """
        Check if user can change pseudonym (90-day cooldown)
        
        Returns:
            bool: True if can change, False otherwise
        """
        if not self.pseudonym_last_changed:
            return True
        
        days_since = (datetime.now(timezone.utc).replace(tzinfo=None) - self.pseudonym_last_changed).days
        return days_since >= 90
    
    def days_until_pseudonym_change(self):
        """
        Get number of days until pseudonym can be changed
        
        Returns:
            int: Days remaining (0 if can change now)
        """
        if self.can_change_pseudonym():
            return 0
        
        days_since = (datetime.now(timezone.utc).replace(tzinfo=None) - self.pseudonym_last_changed).days
        return 90 - days_since
    
    def __repr__(self):
        return f'<User {self.username}>'

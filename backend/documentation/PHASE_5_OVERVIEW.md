# 🚀 PHASE 5 OVERVIEW - ENHANCED AUTHENTICATION & USER FEATURES

**Pulse Backend - Production Authentication & User Experience**

**Status:** Planning Phase  
**Priority:** High - Security & User Engagement  
**Estimated Time:** 10-14 days

---

## 🎯 PHASE 5 GOALS

Phase 5 will transform Pulse into a production-ready platform with:
- **University SSO Integration** - Authentic @ulaval.ca verification
- **Email Verification** - Confirm valid university emails
- **Password Management** - Secure password reset flow
- **Enhanced Profiles** - Bio, profile pictures, customization
- **Comment System** - Post discussions and engagement
- **Account Security** - 2FA, session management, security logs
- **User Experience** - Notifications, preferences, onboarding

---

## 🔐 AUTHENTICATION ENHANCEMENTS

### **1. Université Laval SSO Integration**

**Problem:** Current system allows any @ulaval.ca email without verification  
**Risk:** Fake accounts, unauthorized access, security vulnerabilities

**Solution:** Integrate with Université Laval's authentication system

#### **Implementation Options:**

**Option A: CAS (Central Authentication Service)**
```
UniversitÃ© Laval's SSO: https://cas.ulaval.ca/
- Industry standard for universities
- Single sign-on across campus services
- Validates student/staff status
- Returns user attributes (name, student ID, email)
```

**Option B: SAML 2.0**
```
- Enterprise-grade authentication
- Works with university identity provider
- Supports multi-factor authentication
- Session management built-in
```

**Option C: OAuth 2.0 / OpenID Connect**
```
- Modern authentication standard
- Works with most university systems
- Mobile-friendly
- Token-based authentication
```

#### **Recommended: CAS Integration**

**Why CAS:**
- ✅ Standard at Canadian universities
- ✅ Well-documented
- ✅ Python libraries available (`python-cas`)
- ✅ Validates university affiliation
- ✅ No password storage needed

**Implementation:**
```python
# New route: /api/auth/cas/login
@bp.route('/cas/login', methods=['GET'])
def cas_login():
    """Redirect to Université Laval CAS for authentication"""
    cas_client = CASClient(
        version=3,
        service_url=f'{FRONTEND_URL}/auth/callback',
        server_url='https://cas.ulaval.ca/cas/'
    )
    return redirect(cas_client.get_login_url())

# New route: /api/auth/cas/callback
@bp.route('/cas/callback', methods=['GET'])
def cas_callback():
    """Handle CAS authentication response"""
    ticket = request.args.get('ticket')
    cas_client = CASClient(...)
    
    # Validate ticket with CAS server
    user, attributes, pgtiou = cas_client.verify_ticket(ticket)
    
    if user:
        # user = 'abc123' (student number or IDUL)
        # attributes = {'mail': 'abc123@ulaval.ca', 'displayName': '...'}
        
        # Create or update user in our database
        db_user = User.query.filter_by(email=attributes['mail']).first()
        if not db_user:
            db_user = User(
                email=attributes['mail'],
                username=user,  # IDUL or student number
                display_name=attributes.get('displayName'),
                is_verified=True  # CAS verification = verified
            )
            db.session.add(db_user)
            db.session.commit()
        
        # Create JWT token for our API
        token = create_access_token(identity=str(db_user.id))
        return jsonify({'token': token, 'user': db_user.to_dict()})
    
    return jsonify({'error': 'Authentication failed'}), 401
```

**Migration Strategy:**
```
Phase 1: Add CAS login alongside existing auth (parallel)
Phase 2: Encourage CAS usage with benefits (verified badge)
Phase 3: Require CAS for new accounts
Phase 4: Migrate existing accounts or deprecate
```

**New Database Fields:**
```python
User model additions:
- is_verified: Boolean (True if CAS or email verified)
- verification_token: String (for email verification)
- verification_expires: DateTime
- cas_username: String (IDUL from CAS)
- account_type: Enum ('student', 'staff', 'faculty', 'alumni')
```

---

### **2. Email Verification System**

**For users who don't use CAS (legacy or special cases)**

#### **Registration Flow:**
```
1. User registers with @ulaval.ca email
2. System sends verification email with token
3. User clicks link to verify
4. Account activated
```

#### **Implementation:**

**New Endpoints:**
```
POST   /api/auth/send-verification      # Resend verification email
GET    /api/auth/verify-email/{token}   # Verify email with token
```

**Email Service:**
```python
# app/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

def send_verification_email(user):
    """Send verification email to user"""
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Store token with expiration (24 hours)
    user.verification_token = token
    user.verification_expires = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()
    
    # Build verification link
    verify_link = f"{FRONTEND_URL}/verify-email?token={token}"
    
    # Email content (bilingual)
    html = f"""
    <html>
    <body>
        <h2>Bienvenue sur Pulse / Welcome to Pulse</h2>
        <p>Veuillez vérifier votre adresse courriel / Please verify your email:</p>
        <a href="{verify_link}">Vérifier / Verify</a>
        <p>Ce lien expire dans 24 heures / This link expires in 24 hours</p>
    </body>
    </html>
    """
    
    # Send email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Pulse - Vérification de courriel / Email Verification'
    msg['From'] = 'noreply@pulse.ulaval.ca'
    msg['To'] = user.email
    msg.attach(MIMEText(html, 'html'))
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
```

**Verification Endpoint:**
```python
@bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify user's email with token"""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        return jsonify({'error': 'Invalid verification token'}), 400
    
    if user.verification_expires < datetime.utcnow():
        return jsonify({'error': 'Verification token expired'}), 400
    
    # Mark as verified
    user.is_verified = True
    user.verification_token = None
    user.verification_expires = None
    db.session.commit()
    
    return jsonify({
        'message': 'Email verified successfully',
        'user': user.to_dict()
    }), 200
```

**Enforcement:**
```python
# Middleware: Require verification for certain actions
def require_verification(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user.is_verified:
            return jsonify({
                'error': 'Email verification required',
                'message': 'Please verify your email to perform this action'
            }), 403
        
        return f(*args, **kwargs)
    return decorated

# Apply to sensitive endpoints
@bp.route('/posts', methods=['POST'])
@jwt_required()
@require_verification  # Must be verified to post
def create_post():
    ...
```

---

### **3. Password Reset Flow**

**Backend Implementation** (Frontend will handle UI)

#### **Endpoints:**
```
POST   /api/auth/forgot-password        # Request password reset
POST   /api/auth/reset-password         # Reset with token
```

#### **Implementation:**

**Step 1: Request Reset**
```python
@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Initiate password reset flow"""
    data = request.get_json()
    email = data.get('email')
    
    user = User.query.filter_by(email=email).first()
    
    # Always return success (security - don't reveal if email exists)
    if user:
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Store token with expiration (1 hour)
        user.reset_token = reset_token
        user.reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        # Send reset email
        send_password_reset_email(user, reset_token)
    
    return jsonify({
        'message': 'If that email exists, a reset link has been sent'
    }), 200
```

**Step 2: Reset Password**
```python
@bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    # Validate password strength
    if not is_strong_password(new_password):
        return jsonify({'error': 'Password does not meet requirements'}), 400
    
    # Find user by token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user:
        return jsonify({'error': 'Invalid reset token'}), 400
    
    if user.reset_expires < datetime.utcnow():
        return jsonify({'error': 'Reset token expired'}), 400
    
    # Update password
    user.password_hash = bcrypt.hashpw(
        new_password.encode('utf-8'), 
        bcrypt.gensalt(12)
    ).decode('utf-8')
    
    # Clear reset token
    user.reset_token = None
    user.reset_expires = None
    db.session.commit()
    
    return jsonify({'message': 'Password reset successful'}), 200
```

**New Database Fields:**
```python
User model additions:
- reset_token: String(255)
- reset_expires: DateTime
```

---

## 👤 ENHANCED USER PROFILES

### **4. Profile Customization**

**New Features:**
- Bio/About section
- Profile picture upload
- Display name customization
- Privacy settings
- Theme preferences

#### **Extended User Model:**
```python
class User(db.Model):
    # Existing fields...
    
    # Profile customization
    bio = db.Column(db.Text, nullable=True)  # Up to 500 characters
    profile_picture = db.Column(db.String(255), nullable=True)  # File path
    header_image = db.Column(db.String(255), nullable=True)  # Cover photo
    website = db.Column(db.String(255), nullable=True)  # Personal link
    location = db.Column(db.String(100), nullable=True)  # "QuÃ©bec, QC"
    
    # Privacy settings
    profile_visibility = db.Column(
        db.Enum('public', 'followers', 'private'),
        default='public'
    )
    show_email = db.Column(db.Boolean, default=False)
    
    # Preferences
    theme = db.Column(db.Enum('light', 'dark', 'auto'), default='auto')
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
```

#### **New Endpoints:**

```
PATCH  /api/auth/update-bio             # Update bio
POST   /api/auth/upload-profile-pic     # Upload profile picture
POST   /api/auth/upload-header          # Upload header image
PATCH  /api/auth/privacy-settings       # Update privacy settings
PATCH  /api/auth/preferences            # Update preferences
```

#### **Profile Picture Upload:**
```python
@bp.route('/upload-profile-pic', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    """Upload and set profile picture"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    # Check for file in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Validate file type
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Validate file size (max 5MB)
    if len(file.read()) > 5 * 1024 * 1024:
        return jsonify({'error': 'File too large (max 5MB)'}), 400
    file.seek(0)  # Reset file pointer
    
    # Generate secure filename
    filename = f"profile_{user.id}_{secrets.token_hex(8)}.{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, 'profiles', filename)
    
    # Save file
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)
    
    # Resize and optimize image
    from PIL import Image
    img = Image.open(filepath)
    img.thumbnail((500, 500))  # Max 500x500
    img.save(filepath, optimize=True, quality=85)
    
    # Delete old profile picture
    if user.profile_picture:
        old_path = os.path.join(UPLOAD_DIR, user.profile_picture)
        if os.path.exists(old_path):
            os.remove(old_path)
    
    # Update user record
    user.profile_picture = f"profiles/{filename}"
    db.session.commit()
    
    return jsonify({
        'message': 'Profile picture updated',
        'profile_picture_url': f"/uploads/{user.profile_picture}"
    }), 200
```

#### **Bio Update:**
```python
@bp.route('/update-bio', methods=['PATCH'])
@jwt_required()
def update_bio():
    """Update user bio"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    data = request.get_json()
    bio = data.get('bio', '').strip()
    
    # Validate bio length
    if len(bio) > 500:
        return jsonify({
            'error': 'Bio too long (max 500 characters)'
        }), 400
    
    # Update bio
    user.bio = bio if bio else None
    db.session.commit()
    
    return jsonify({
        'message': 'Bio updated successfully',
        'user': user.to_dict()
    }), 200
```

---

## 💬 COMMENT SYSTEM

### **5. Post Comments**

**Enable threaded discussions on posts**

#### **Comment Model:**
```python
class Comment(db.Model):
    """Comments on posts"""
    __tablename__ = 'comments'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Content
    content = db.Column(db.Text, nullable=False)  # 1-500 characters
    
    # Relationships
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    
    # Threading (optional - for replies to comments)
    parent_id = db.Column(
        db.Integer, 
        db.ForeignKey('comments.id', ondelete='CASCADE'),
        nullable=True  # NULL = top-level comment
    )
    
    # Privacy
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    
    def to_dict(self, current_user_id=None):
        """Serialize to dict with privacy"""
        result = {
            'id': self.id,
            'content': self.content,
            'post_id': self.post_id,
            'created_at': self.created_at.isoformat(),
            'is_anonymous': self.is_anonymous,
            'reply_count': self.replies.count()
        }
        
        # Author info based on anonymity
        if self.is_anonymous:
            result['author'] = {
                'pseudonym': self.user.pseudonym,
                'is_you': (current_user_id == self.user_id)
            }
        else:
            result['author'] = {
                'username': self.user.username,
                'display_name': self.user.display_name,
                'profile_picture': self.user.profile_picture,
                'is_you': (current_user_id == self.user_id)
            }
        
        return result
```

#### **Comment Endpoints:**

```
POST   /api/posts/{post_id}/comments           # Add comment
GET    /api/posts/{post_id}/comments           # List comments (paginated)
GET    /api/comments/{comment_id}/replies      # Get replies to comment
PATCH  /api/comments/{comment_id}              # Edit comment (5 min window)
DELETE /api/comments/{comment_id}              # Delete comment
```

#### **Create Comment:**
```python
@bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
@require_verification
def create_comment(post_id):
    """Add a comment to a post"""
    current_user_id = int(get_jwt_identity())
    
    # Verify post exists
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    data = request.get_json()
    content = data.get('content', '').strip()
    is_anonymous = data.get('is_anonymous', False)
    parent_id = data.get('parent_id')  # For threading
    
    # Validate content
    if not content or len(content) < 1:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    if len(content) > 500:
        return jsonify({'error': 'Comment too long (max 500 characters)'}), 400
    
    # Create comment
    comment = Comment(
        content=content,
        post_id=post_id,
        user_id=current_user_id,
        is_anonymous=is_anonymous,
        parent_id=parent_id
    )
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'message': 'Comment added',
        'comment': comment.to_dict(current_user_id)
    }), 201
```

#### **List Comments:**
```python
@bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """Get comments for a post (paginated)"""
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Query top-level comments only (no parent)
    comments = Comment.query.filter_by(
        post_id=post_id,
        parent_id=None
    ).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    current_user_id = None
    if get_jwt_identity():
        current_user_id = int(get_jwt_identity())
    
    return jsonify({
        'comments': [c.to_dict(current_user_id) for c in comments.items],
        'total': comments.total,
        'pages': comments.pages,
        'current_page': page
    }), 200
```

---

## 🔔 NOTIFICATION SYSTEM

### **6. User Notifications**

**Real-time updates for user engagement**

#### **Notification Model:**
```python
class Notification(db.Model):
    """User notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Target user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    
    # Notification type
    type = db.Column(db.Enum(
        'new_follower',
        'new_comment',
        'comment_reply',
        'post_reaction',
        'mention',
        'system'
    ))
    
    # Content
    title = db.Column(db.String(255))
    message = db.Column(db.Text)
    
    # Reference to related object
    related_type = db.Column(db.Enum('post', 'comment', 'user'))
    related_id = db.Column(db.Integer)
    
    # Actor (who triggered the notification)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    actor = db.relationship('User', foreign_keys=[actor_id])
```

#### **Notification Endpoints:**

```
GET    /api/notifications                # List user's notifications
PATCH  /api/notifications/{id}/read      # Mark as read
PATCH  /api/notifications/read-all       # Mark all as read
DELETE /api/notifications/{id}           # Delete notification
```

#### **Notification Service:**
```python
# app/services/notification_service.py
def create_notification(user_id, notification_type, title, message, 
                       related_type=None, related_id=None, actor_id=None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        related_type=related_type,
        related_id=related_id,
        actor_id=actor_id
    )
    db.session.add(notification)
    db.session.commit()
    
    # Send push notification if enabled
    user = User.query.get(user_id)
    if user.push_notifications:
        send_push_notification(user, title, message)

# Usage examples:
# New follower
create_notification(
    user_id=target_user.id,
    notification_type='new_follower',
    title='New Follower',
    message=f'{actor.display_name} started following you',
    actor_id=actor.id
)

# New comment on your post
create_notification(
    user_id=post.user_id,
    notification_type='new_comment',
    title='New Comment',
    message=f'{actor.display_name} commented on your post',
    related_type='post',
    related_id=post.id,
    actor_id=actor.id
)
```

---

## 🔒 SECURITY ENHANCEMENTS

### **7. Two-Factor Authentication (2FA)**

**Optional 2FA for enhanced account security**

#### **Implementation:**
```python
# New fields in User model
totp_secret = db.Column(db.String(32), nullable=True)  # For TOTP
totp_enabled = db.Column(db.Boolean, default=False)
backup_codes = db.Column(db.JSON, nullable=True)  # List of recovery codes
```

#### **2FA Endpoints:**
```
POST   /api/auth/2fa/enable              # Enable 2FA
POST   /api/auth/2fa/verify              # Verify 2FA code
POST   /api/auth/2fa/disable             # Disable 2FA
GET    /api/auth/2fa/backup-codes        # Generate backup codes
```

#### **Enable 2FA:**
```python
import pyotp
import qrcode

@bp.route('/2fa/enable', methods=['POST'])
@jwt_required()
def enable_2fa():
    """Enable 2FA for user"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if user.totp_enabled:
        return jsonify({'error': '2FA already enabled'}), 400
    
    # Generate TOTP secret
    secret = pyotp.random_base32()
    user.totp_secret = secret
    
    # Generate QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name='Pulse - UniversitÃ© Laval'
    )
    
    # Create QR code image
    qr = qrcode.make(provisioning_uri)
    # ... save QR code and return URL
    
    # Generate backup codes
    backup_codes = [secrets.token_hex(4) for _ in range(10)]
    user.backup_codes = backup_codes
    
    db.session.commit()
    
    return jsonify({
        'secret': secret,
        'qr_code_url': qr_url,
        'backup_codes': backup_codes,
        'message': 'Scan QR code with authenticator app'
    }), 200
```

---

### **8. Session Management**

**Track active sessions and allow users to manage them**

#### **Session Model:**
```python
class Session(db.Model):
    """User sessions for security tracking"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    
    # Session info
    token_jti = db.Column(db.String(255), unique=True)  # JWT ID
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(255))
    device_type = db.Column(db.Enum('web', 'mobile', 'desktop', 'unknown'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
```

#### **Session Endpoints:**
```
GET    /api/auth/sessions               # List active sessions
DELETE /api/auth/sessions/{id}          # Revoke session
DELETE /api/auth/sessions/all           # Revoke all sessions (except current)
```

---

### **9. Security Logs**

**Track security-related events for audit trail**

#### **SecurityLog Model:**
```python
class SecurityLog(db.Model):
    """Security event logging"""
    __tablename__ = 'security_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    
    # Event details
    event_type = db.Column(db.Enum(
        'login_success',
        'login_failed',
        'password_change',
        'password_reset_request',
        'email_change',
        '2fa_enabled',
        '2fa_disabled',
        'suspicious_activity',
        'account_locked'
    ))
    
    # Context
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    details = db.Column(db.JSON)  # Additional context
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 📱 USER EXPERIENCE ENHANCEMENTS

### **10. Onboarding Flow**

**Guided setup for new users**

**Steps:**
1. Email verification
2. Complete profile (bio, picture)
3. Follow suggestions (friends from zones)
4. Privacy settings tour
5. First post tutorial

### **11. User Preferences**

**Customization options:**
- Language preference (FR/EN)
- Theme (light/dark/auto)
- Email notifications (on/off, frequency)
- Push notifications (on/off)
- Default post visibility (public/followers)
- Default anonymity setting

### **12. @Mentions System**

**Tag users in posts and comments**

```python
# In post/comment processing:
def extract_mentions(content):
    """Extract @username mentions from content"""
    import re
    pattern = r'@(\w+)'
    mentions = re.findall(pattern, content)
    return mentions

# When creating post/comment:
mentions = extract_mentions(content)
for username in mentions:
    user = User.query.filter_by(username=username).first()
    if user:
        create_notification(
            user_id=user.id,
            notification_type='mention',
            title='You were mentioned',
            message=f'{author.display_name} mentioned you',
            related_type='post',
            related_id=post.id,
            actor_id=author.id
        )
```

### **13. Bookmarks/Saved Posts**

**Save posts for later**

```python
class Bookmark(db.Model):
    """Saved posts"""
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_bookmark'),
    )
```

**Endpoints:**
```
POST   /api/posts/{post_id}/bookmark    # Bookmark post
DELETE /api/posts/{post_id}/bookmark    # Remove bookmark
GET    /api/bookmarks                   # List bookmarked posts
```

### **14. Post Pinning**

**Pin important posts to profile**

```python
# User model addition:
pinned_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
```

### **15. Account Deactivation**

**Temporary account deactivation (vs deletion)**

```python
# User model additions:
is_deactivated = db.Column(db.Boolean, default=False)
deactivated_at = db.Column(db.DateTime, nullable=True)
```

**Endpoint:**
```
POST   /api/auth/deactivate              # Deactivate account
POST   /api/auth/reactivate              # Reactivate account
```

---

## 🗄️ DATABASE SCHEMA UPDATES

### **New Tables:**
1. **comments** - Post comments with threading
2. **notifications** - User notifications
3. **sessions** - Active user sessions
4. **security_logs** - Security event audit trail
5. **bookmarks** - Saved posts

### **Updated Tables:**

**users:**
```sql
-- Email verification
ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
ADD COLUMN verification_token VARCHAR(255);
ADD COLUMN verification_expires DATETIME;

-- Password reset
ADD COLUMN reset_token VARCHAR(255);
ADD COLUMN reset_expires DATETIME;

-- CAS integration
ADD COLUMN cas_username VARCHAR(50);
ADD COLUMN account_type ENUM('student', 'staff', 'faculty', 'alumni');

-- Profile customization
ADD COLUMN bio TEXT;
ADD COLUMN header_image VARCHAR(255);
ADD COLUMN website VARCHAR(255);
ADD COLUMN location VARCHAR(100);

-- Privacy
ADD COLUMN profile_visibility ENUM('public', 'followers', 'private') DEFAULT 'public';
ADD COLUMN show_email BOOLEAN DEFAULT FALSE;

-- Preferences
ADD COLUMN theme ENUM('light', 'dark', 'auto') DEFAULT 'auto';
ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE;
ADD COLUMN push_notifications BOOLEAN DEFAULT TRUE;

-- 2FA
ADD COLUMN totp_secret VARCHAR(32);
ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE;
ADD COLUMN backup_codes JSON;

-- Account status
ADD COLUMN is_deactivated BOOLEAN DEFAULT FALSE;
ADD COLUMN deactivated_at DATETIME;

-- Pinned post
ADD COLUMN pinned_post_id INT;
```

---

## 📊 PHASE 5 METRICS

### **Estimated Deliverables:**

**Models:** 5 new (Comment, Notification, Session, SecurityLog, Bookmark)  
**Routes:** ~30 new endpoints  
**Services:** 3 new (Email, Notification, Session)  
**Tests:** ~50 test cases  
**Documentation:** Updated API docs, setup guides

### **Development Timeline:**

| Feature | Time | Priority |
|---------|------|----------|
| Email Verification | 2 days | High |
| CAS Integration | 3 days | High |
| Password Reset | 1 day | High |
| Profile Customization | 2 days | Medium |
| Comment System | 2 days | High |
| Notifications | 2 days | Medium |
| 2FA | 2 days | Low |
| Session Management | 1 day | Medium |
| UX Enhancements | 2 days | Low |

**Total:** 10-14 days

---

## 🎯 PRIORITY MATRIX

### **Must Have (Phase 5A):**
1. ✅ Email verification
2. ✅ CAS integration
3. ✅ Password reset
4. ✅ Basic profile customization (bio, picture)
5. ✅ Comment system

### **Should Have (Phase 5B):**
6. ✅ Notifications
7. ✅ Session management
8. ✅ @Mentions
9. ✅ Bookmarks

### **Nice to Have (Phase 5C):**
10. ⭐ 2FA
11. ⭐ Advanced privacy settings
12. ⭐ Theme customization
13. ⭐ Post pinning
14. ⭐ Account deactivation

---

## 🔐 SECURITY CONSIDERATIONS

### **Authentication:**
- ✅ CAS integration for university verification
- ✅ Email verification for non-CAS users
- ✅ Secure password reset with time-limited tokens
- ✅ Optional 2FA for enhanced security
- ✅ Session tracking and management

### **Privacy:**
- ✅ Profile visibility controls
- ✅ Anonymous commenting
- ✅ Email privacy setting
- ✅ Deactivation vs deletion

### **Audit:**
- ✅ Security logs for all sensitive actions
- ✅ Session tracking
- ✅ Failed login attempts monitoring

---

## 📚 DOCUMENTATION NEEDED

1. **CAS Integration Guide** - Setup instructions
2. **Email Service Setup** - SMTP configuration
3. **2FA User Guide** - How to enable/use
4. **API Documentation** - Updated endpoint reference
5. **Security Best Practices** - For developers
6. **Migration Guide** - Database updates
7. **Testing Guide** - New test cases

---

## 🚀 DEPLOYMENT CHECKLIST

### **Infrastructure:**
- [ ] SMTP server configured (email sending)
- [ ] CAS credentials obtained from UniversitÃ© Laval
- [ ] File upload directory configured
- [ ] Image processing library installed (Pillow)
- [ ] Redis for session management (optional)
- [ ] Push notification service (Firebase/OneSignal)

### **Security:**
- [ ] HTTPS enabled (required for CAS)
- [ ] Rate limiting configured
- [ ] CORS settings updated
- [ ] File upload restrictions enforced

### **Testing:**
- [ ] Email delivery working
- [ ] CAS callback working
- [ ] File uploads working
- [ ] 2FA tested
- [ ] All endpoints tested

---

## ✨ PHASE 5 DELIVERABLES

**Security & Authentication:**
- ✅ CAS integration with UniversitÃ© Laval
- ✅ Email verification system
- ✅ Secure password reset
- ✅ Two-factor authentication (optional)
- ✅ Session management
- ✅ Security audit logs

**User Experience:**
- ✅ Rich profile customization
- ✅ Comment system with threading
- ✅ Real-time notifications
- ✅ @Mentions functionality
- ✅ Bookmarks/saved posts
- ✅ Post pinning
- ✅ Account deactivation

**Infrastructure:**
- ✅ Email service integration
- ✅ File upload system
- ✅ Image processing
- ✅ Push notifications

**Testing & Docs:**
- ✅ Comprehensive test coverage
- ✅ Updated API documentation
- ✅ CAS integration guide
- ✅ Security best practices

---

## 📞 HANDOFF NOTES

### **For Backend Developer:**
1. Obtain CAS credentials from UniversitÃ© Laval IT
2. Configure SMTP server for email
3. Set up file upload directory structure
4. Install required packages (pyotp, qrcode, Pillow)
5. Review and implement priority features first

### **For Frontend Developer:**
1. Design CAS login flow UI
2. Build profile customization interface
3. Create comment component
4. Implement notification center
5. Design 2FA setup wizard

### **For DevOps:**
1. Configure SMTP relay
2. Set up file storage (S3 or local)
3. Configure CAS redirect URLs
4. Set up push notification service
5. Configure Redis for sessions

### **For University IT:**
1. Request CAS integration approval
2. Provide callback URLs
3. Obtain CAS credentials
4. Test authentication flow
5. Plan migration strategy

---

**Phase 5: READY TO START 🚀**  
**Priority: Production-Ready Authentication & User Engagement**  
**Timeline: 10-14 days**  
**Goal: Enterprise-Grade Platform** ✨

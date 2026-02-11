# 🏗️ PULSE BACKEND — ARCHITECTURE DECISIONS

**Last Updated:** 2026-02-10  
**Project:** Pulse Privacy-First Campus Wellness Platform  
**Maintainer:** Backend, Data & Intelligence Lead

---

## 🎯 CORE PRINCIPLES

### 1. Privacy-First Architecture

> **"Individual expression is private, collective insight is public."**

**What this means in code:**
- Anonymous posts store `user_id` in database BUT never expose it via API
- Aggregates require minimum threshold (≥10 posts) before revealing mood data
- No endpoint ever returns "user X's emotional history"
- Followers can NEVER see friends' anonymous posts

**Enforcement Layer:** Backend API (NOT frontend)

---

### 2. Ethical Data Handling

**We collect:**
- ✅ Post content (for sentiment analysis)
- ✅ User_id (for ownership, even on anonymous posts)
- ✅ Timestamps (for aggregation)
- ✅ Campus zones (for location-based insights)

**We DON'T collect:**
- ❌ IP addresses (beyond session management)
- ❌ Device fingerprints
- ❌ GPS coordinates (only user-selected zones)
- ❌ Individual emotional trends over time

**We DON'T expose:**
- ❌ "User X posted this anonymous post"
- ❌ "User Y seems to be getting sadder"
- ❌ Individual post histories (anonymous posts excluded from profile)

---

### 3. Defense in Depth

**Security layers:**
1. **Input validation** (sanitize all user input)
2. **Authentication** (JWT tokens, bcrypt hashing)
3. **Authorization** (can this user perform this action?)
4. **Rate limiting** (prevent abuse)
5. **Database constraints** (foreign keys, unique constraints)
6. **API design** (never expose sensitive data in endpoints)

---

## 📋 ARCHITECTURAL DECISIONS

### **AD-001: Database Storage of Anonymous Posts**

**Decision:** Store `user_id` even for anonymous posts

**Options Considered:**
1. **True Anonymous:** `user_id = NULL` (no link to author)
2. **Pseudo-Anonymous:** Store `user_id`, hide in API ✅ CHOSEN

**Rationale:**
- User needs to see their own anonymous posts ("My Anonymous Posts" view)
- User needs to delete their anonymous posts
- Backend can enforce privacy without losing ownership

**Implementation:**
```python
# Database: user_id is ALWAYS stored
post = Post(
    user_id=42,
    is_anonymous=True,
    content="..."
)

# API: user_id is NEVER exposed for anonymous posts
def serialize_post(post, requesting_user_id):
    if post.is_anonymous:
        return {
            'author': {
                'pseudonym': post.user.pseudonym,  # NOT user_id
                'is_you': (post.user_id == requesting_user_id)
            }
        }
```

**Security Guarantee:**
- No API endpoint returns `user_id` for anonymous posts
- Database queries never JOIN users table for anonymous posts in public feeds
- Only in "My Anonymous Posts" endpoint is the link used

---

### **AD-002: Pseudonym System**

**Decision:** Persistent pseudonym with 90-day change cooldown

**Options Considered:**
1. Always "anonymous" (boring, no personality)
2. Per-post custom username (inconsistent)
3. Persistent pseudonym ✅ CHOSEN

**Rationale:**
- Users can express personality without revealing identity
- Consistency helps readers recognize writing style (user's choice)
- 90-day cooldown prevents gaming the system

**Implementation:**
```python
# In users table:
pseudonym VARCHAR(50) NOT NULL DEFAULT 'anonymous'
pseudonym_last_changed TIMESTAMP NULL

# Validation:
def update_pseudonym(user_id, new_pseudonym):
    user = User.query.get(user_id)
    
    # Check cooldown
    if user.pseudonym_last_changed:
        days_since = (datetime.now() - user.pseudonym_last_changed).days
        if days_since < 90:
            raise ValidationError(f"Can change in {90 - days_since} days")
    
    # Reserved names
    if new_pseudonym.lower() in ['admin', 'system', 'pulse']:
        raise ValidationError("Reserved pseudonym")
    
    user.pseudonym = new_pseudonym
    user.pseudonym_last_changed = datetime.now()
```

**Ethical Consideration:**
- All past anonymous posts now show new pseudonym
- Users should be warned: "Changing pseudonym updates all your anonymous posts"
- This is intentional (prevents building "alt identities")

---

### **AD-003: Reactions on Anonymous Posts**

**Decision:** Allow emoji reactions on anonymous posts

**Rationale:**
- Anonymous posts should feel like public posts (equal engagement)
- Reactions are aggregate data (heart count), not individual tracking
- Users already know their own anonymous posts, so seeing reactions is fine

**Risk Mitigation:**
- We DON'T show "who reacted" on any post (public or anonymous)
- Only aggregate counts: {"❤️": 12, "👍": 8}
- Prevents stalking patterns

**Implementation:**
```python
# Reactions table:
CREATE TABLE reactions (
    user_id INT NOT NULL,  # Who reacted
    post_id INT NOT NULL,  # To which post
    emoji VARCHAR(10),
    UNIQUE (user_id, post_id)  # One reaction per user per post
)

# API returns only counts:
{
    "reactions": {
        "❤️": 12,
        "👍": 8,
        "😢": 3
    },
    "my_reaction": "❤️"  # User's own reaction
}
```

---

### **AD-004: Edit vs. Delete for Anonymous Posts**

**Decision:** Users can DELETE but NOT EDIT anonymous posts

**Rationale:**
- **Edit risk:** Multiple versions could reveal identity through writing style
- **Delete benefit:** User control over their data
- **Simplicity:** Clear UX ("Once posted anonymously, it's final")

**Implementation:**
```python
@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    
    # Authorization: Only author can delete
    if post.user_id != user_id:
        return {'error': 'Unauthorized'}, 403
    
    # Optional: Restrict deletion after 24 hours
    hours_since_post = (datetime.now() - post.created_at).total_seconds() / 3600
    if hours_since_post > 24:
        return {'error': 'Can only delete posts within 24 hours'}, 403
    
    db.session.delete(post)
    db.session.commit()
    return {'deleted': True}
```

**No EDIT endpoint exists for posts.**

---

### **AD-005: Social Graph Model**

**Decision:** Hybrid system — Followers (one-way) + Friends (computed)

**Database Design:**
```sql
CREATE TABLE followers (
    follower_id INT NOT NULL,   # User who clicks "follow"
    following_id INT NOT NULL,  # User being followed
    UNIQUE (follower_id, following_id)
)

-- Friends are NOT a separate table
-- Friends = users where mutual follow exists
```

**Friends Computation:**
```python
def get_friends(user_id):
    # Find users where:
    # 1. I follow them (follower_id = user_id, following_id = X)
    # 2. They follow me (follower_id = X, following_id = user_id)
    
    friends = db.session.query(User)\
        .join(Follower, Follower.following_id == User.id)\
        .filter(Follower.follower_id == user_id)\
        .filter(
            db.exists(
                db.session.query(Follower)\
                .filter(
                    Follower.follower_id == User.id,
                    Follower.following_id == user_id
                )
            )
        ).all()
    
    return friends
```

**Rationale:**
- Flexibility: Users can follow without reciprocity (like Twitter)
- Friends emerge naturally from mutual interest
- No "friend request" approval flow needed
- Simpler database schema

---

### **AD-006: Feed Generation Algorithm**

**Decision:** Feed shows ONLY public posts from followed users

**Critical Rule:**
```python
def get_feed(user_id):
    following_ids = get_following_ids(user_id)
    
    posts = Post.query\
        .filter(
            Post.user_id.in_(following_ids),
            Post.is_anonymous == False  # ← CRITICAL
        )\
        .order_by(Post.created_at.desc())\
        .limit(50)\
        .all()
    
    return posts
```

**What this prevents:**
- ❌ "I noticed my friend posts anonymously at 2am every night"
- ❌ Pattern matching based on writing style
- ❌ Social pressure ("Why did you post that anonymously?")

**User Experience:**
- User's profile shows only their public posts
- User's "My Posts" view shows public posts
- User's "My Anonymous Posts" is a SEPARATE, PRIVATE view

---

### **AD-007: Sentiment Analysis Approach**

**Decision:** Use VADER (not custom ML model)

**Options Considered:**
1. **Custom ML model** (requires training data, expertise)
2. **Cloud API** (OpenAI, Google NLP - costs money, privacy risk)
3. **VADER** ✅ CHOSEN

**Rationale:**
- Pre-trained for social media text
- Handles emojis, slang, punctuation
- No API costs
- No external data sharing
- Suitable for student project scope

**Implementation:**
```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def analyze(text):
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']  # -1 to +1
    
    # Classification:
    if compound > 0.05:
        return 'positive'
    elif compound < -0.05:
        return 'negative'
    else:
        return 'neutral'
```

**Thresholds Explanation:**
- `> 0.05` = Positive (clearly optimistic tone)
- `-0.05 to 0.05` = Neutral (matter-of-fact, informational)
- `< -0.05` = Negative (clearly stressed/sad/frustrated)

**Documented Limitations:**
- Not clinically validated
- English-only (breaks for French, Spanish, etc.)
- Struggles with sarcasm
- No context awareness ("Great, another exam 🙄" might be misclassified)

**Ethical Disclaimer (in UI):**
> "Sentiment analysis is automated and approximate. It's designed to show campus trends, not diagnose individuals. If you're struggling, contact [Campus Counseling: 555-0100]."

---

### **AD-008: Aggregation Threshold**

**Decision:** Minimum 10 posts required to show mood data

**Rationale:**
- **Privacy:** Fewer than 10 posts could reveal individual contributors
- **Statistical validity:** Small samples are noisy
- **Ethical:** Prevents targeting specific individuals

**Implementation:**
```python
def get_daily_mood(date, zone_id=None):
    aggregate = DailyAggregate.query\
        .filter_by(date=date, zone_id=zone_id)\
        .first()
    
    if not aggregate or aggregate.total_posts < 10:
        return {
            'mood': None,
            'message': 'Not enough data (minimum 10 posts required)'
        }
    
    return {
        'mood': aggregate.avg_sentiment,
        'distribution': {
            'positive': aggregate.positive_count,
            'neutral': aggregate.neutral_count,
            'negative': aggregate.negative_count
        },
        'total_posts': aggregate.total_posts
    }
```

**Edge Case:**
- What if a small zone never reaches 10 posts?
- Answer: Data not shown for that zone (privacy over completeness)

---

### **AD-009: Media Upload Security**

**Decision:** Strict validation, no user-provided filenames

**Security Measures:**

1. **File Type Whitelist:**
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_MIME_TYPES = {
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp'
}

def validate_upload(file):
    # Check extension
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError('Invalid file type')
    
    # Check MIME type (actual file content)
    mime = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # Reset pointer
    if mime not in ALLOWED_MIME_TYPES:
        raise ValidationError('File content does not match extension')
    
    # Check file size (max 5MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        raise ValidationError('File too large (max 5MB)')
```

2. **Filename Sanitization:**
```python
import uuid

def save_media(file, post_id):
    # Generate random filename (prevent path traversal)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    
    # Store in structured directory
    upload_dir = f"uploads/posts/{post_id}/"
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    return filepath
```

3. **No Direct File Access:**
```python
# ❌ NEVER DO THIS:
@app.route('/uploads/<path:filename>')
def serve_file(filename):
    return send_file(filename)  # Path traversal attack!

# ✅ CORRECT:
@app.route('/api/media/<int:media_id>')
def serve_media(media_id):
    media = Media.query.get_or_404(media_id)
    
    # Verify file exists and is safe
    if not os.path.exists(media.file_path):
        abort(404)
    
    return send_file(
        media.file_path,
        mimetype=media.mime_type,
        as_attachment=False
    )
```

---

## 🔐 SECURITY PATTERNS

### Pattern 1: JWT Authentication

```python
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Login endpoint:
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return {'error': 'Invalid credentials'}, 401
    
    # Create token (expires in 24 hours)
    token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(hours=24)
    )
    
    return {'token': token, 'user': serialize_user(user)}

# Protected endpoint:
@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    user_id = get_jwt_identity()  # Extract from token
    # ... create post
```

**Token Configuration:**
```python
# app/config.py
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')  # From .env file
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ALGORITHM = 'HS256'
```

---

### Pattern 2: Input Validation

```python
from marshmallow import Schema, fields, validate, ValidationError

class PostCreateSchema(Schema):
    content = fields.Str(
        required=True,
        validate=[
            validate.Length(min=10, max=500, error='Content must be 10-500 characters'),
            validate.Regexp(r'^[^<>]*$', error='No HTML tags allowed')
        ]
    )
    zone_id = fields.Int(required=False, allow_none=True)
    is_anonymous = fields.Bool(required=True)

# Usage:
@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    schema = PostCreateSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return {'errors': err.messages}, 400
    
    # Data is now validated and safe
```

---

### Pattern 3: Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

@app.route('/api/posts', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")  # Max 10 posts per hour
def create_post():
    # ...
```

---

## 🧪 TESTING STRATEGY

### Unit Tests (per component)
```python
# tests/test_nlp_service.py
def test_sentiment_positive():
    result = nlp_service.analyze("I love this campus! ❤️")
    assert result['label'] == 'positive'
    assert result['score'] > 0.05

def test_sentiment_negative():
    result = nlp_service.analyze("So stressed 😭")
    assert result['label'] == 'negative'
    assert result['score'] < -0.05
```

### Integration Tests (API endpoints)
```python
# tests/test_auth.py
def test_register_success():
    response = client.post('/api/auth/register', json={
        'email': 'test@uni.edu',
        'password': 'SecurePass123!',
        'username': 'testuser'
    })
    assert response.status_code == 201
    assert 'token' in response.json

def test_register_duplicate_email():
    # Register once
    client.post('/api/auth/register', json={...})
    
    # Try again with same email
    response = client.post('/api/auth/register', json={...})
    assert response.status_code == 400
    assert 'email already exists' in response.json['error'].lower()
```

### Privacy Tests (critical)
```python
# tests/test_privacy.py
def test_anonymous_post_hides_user_id():
    token = login_as('testuser')
    
    # Create anonymous post
    response = client.post('/api/posts', 
        headers={'Authorization': f'Bearer {token}'},
        json={
            'content': 'Anonymous test',
            'is_anonymous': True
        }
    )
    post_id = response.json['post']['id']
    
    # Fetch post as different user
    other_token = login_as('otheruser')
    response = client.get(f'/api/posts/{post_id}',
        headers={'Authorization': f'Bearer {other_token}'}
    )
    
    # Should NOT contain user_id
    assert 'user_id' not in response.json
    assert 'author' in response.json
    assert 'pseudonym' in response.json['author']
    assert 'username' not in response.json['author']
```

---

## 📊 PERFORMANCE CONSIDERATIONS

### Database Indexes

```sql
-- Critical indexes for performance:

-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Post queries
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at DESC);
CREATE INDEX idx_posts_zone_created ON posts(zone_id, created_at DESC);
CREATE INDEX idx_posts_public_created ON posts(is_anonymous, created_at DESC);

-- Feed generation (followers)
CREATE INDEX idx_followers_follower ON followers(follower_id);
CREATE INDEX idx_followers_following ON followers(following_id);

-- Reactions
CREATE INDEX idx_reactions_post ON reactions(post_id);
```

### Query Optimization

```python
# ❌ BAD: N+1 query problem
posts = Post.query.all()
for post in posts:
    author = post.user  # Extra query per post!

# ✅ GOOD: Eager loading
posts = Post.query.options(
    db.joinedload(Post.user),
    db.joinedload(Post.zone)
).all()
```

---

## 🚨 KNOWN LIMITATIONS & FUTURE WORK

### Current Limitations:

1. **VADER is English-only**
   - Problem: Campus might have multilingual users
   - Solution: Detect language, fall back to neutral for non-English
   - Future: Add multilingual sentiment models

2. **Pseudonym change affects all past posts**
   - Problem: User might want different pseudonyms for different contexts
   - Solution: This is intentional (prevents alt accounts)
   - Future: Could allow multiple pseudonyms with clear UX

3. **No content moderation**
   - Problem: Users could post harmful content
   - Solution: Manual reporting system + admin review
   - Future: Automated toxicity detection

4. **Media is images-only**
   - Problem: Users might want to share audio journals
   - Solution: Phase 3 will add audio support
   - Future: Video support with transcription

---

## 📚 CODE STYLE GUIDE

### Naming Conventions:
- **Variables:** `snake_case`
- **Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Files:** `snake_case.py`

### Comment Style:
```python
def analyze_sentiment(text):
    """
    Analyzes emotional tone of text using VADER.
    
    Args:
        text (str): User input text (10-500 chars)
    
    Returns:
        dict: {
            'score': float,  # -1.00 to 1.00
            'label': str,    # 'positive' | 'neutral' | 'negative'
            'confidence': float
        }
    
    Raises:
        ValidationError: If text is too short
    """
```

---

**📌 This document grows with the project. Every technical decision is recorded here.**

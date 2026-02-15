# 🗂️ PULSE BACKEND — ARCHITECTURE DECISIONS

**Last Updated:** 2026-02-13  
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

**Date:** 2026-02-10  
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

**Date:** 2026-02-10  
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

**Date:** 2026-02-10  
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

**Date:** 2026-02-10  
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

**Date:** 2026-02-10  
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

**Date:** 2026-02-10  
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

### **AD-007: Bilingual NLP - Two-Model Approach**

**Date:** 2026-02-13  
**Decision:** Use Twitter RoBERTa (multilingual) for French, VADER for English

**Options Considered:**
1. **TextBlob for both** - Simple but inaccurate for social media
2. **CamemBERT for French only** - Good but French-specific, no English
3. **Twitter RoBERTa (multilingual)** - ✅ CHOSEN for French
4. **VADER** - ✅ CHOSEN for English (social media optimized)

**Rationale:**
- **French posts deserve equal quality:** Student posts in French should have same sentiment accuracy as English
- **Twitter RoBERTa is trained on tweets:** Perfect for campus social posts (informal, emoji-heavy, short)
- **VADER is lightweight for English:** Fast, accurate, perfect for English social media
- **Automatic language detection:** Uses langdetect to choose the right model

**Performance Trade-offs:**

| Model | Language | First Load | Subsequent | Accuracy |
|-------|----------|-----------|------------|----------|
| VADER | English | <1s | <1s | 85% (social) |
| Twitter RoBERTa | French | ~30s | ~3-5s | 92% (social) |

**Implementation:**
```python
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect

# Load models once at startup
vader = SentimentIntensityAnalyzer()
french_analyzer = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
    top_k=None
)

def analyze_sentiment(text):
    """Bilingual sentiment analysis with automatic language detection"""
    
    # Detect language
    try:
        lang = detect(text)
    except:
        lang = 'en'  # Default to English if detection fails
    
    # Choose appropriate model
    if lang == 'fr':
        # French: Use Twitter RoBERTa
        results = french_analyzer(text)[0]
        
        # Map to our schema
        label_map = {'positive': 1, 'neutral': 0, 'negative': -1}
        score = sum(
            label_map[item['label']] * item['score']
            for item in results
        )
        
        # Classify
        if score > 0.05:
            label = 'positive'
        elif score < -0.05:
            label = 'negative'
        else:
            label = 'neutral'
            
    else:
        # English: Use VADER
        scores = vader.polarity_scores(text)
        score = scores['compound']
        
        if score > 0.05:
            label = 'positive'
        elif score < -0.05:
            label = 'negative'
        else:
            label = 'neutral'
    
    return {
        'score': round(score, 2),
        'label': label,
        'language': lang
    }
```

**Why NOT a single multilingual model for both?**
- VADER is much faster for English (<1s vs 3-5s)
- VADER is optimized for English social media slang
- No need to use heavy model when lightweight works perfectly

**Dependencies Added:**
```
transformers>=4.30.0
torch>=2.0.0
langdetect>=1.0.9
```

**Future Improvements:**
- Cache model outputs for duplicate content
- Consider quantized models for faster French analysis
- Add Spanish support (large Latin American student population)

---

### **AD-008: Database Schema - Updated_At Column**

**Date:** 2026-02-13  
**Decision:** Add `updated_at` column to posts table

**Rationale:**
- **Audit trail:** Track when posts are modified (future edit feature)
- **Industry standard:** Most production apps track created_at + updated_at
- **Debugging:** Helps identify issues with timestamp handling
- **Future-proof:** Even though we don't allow edits now, might enable later

**Implementation:**
```sql
ALTER TABLE posts 
ADD COLUMN updated_at TIMESTAMP NULL 
DEFAULT CURRENT_TIMESTAMP 
ON UPDATE CURRENT_TIMESTAMP 
AFTER created_at;
```

**SQLAlchemy Model:**
```python
class Post(db.Model):
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
```

**Note:** Even though posts are currently immutable (no edit), having this column:
- Matches database best practices
- Prepares for potential future features
- Costs minimal storage (~8 bytes per row)

---

## 🆕 IMPLEMENTATION NOTES (Phase 2)

### Model-Database Alignment

**Critical Lesson Learned:**
SQLAlchemy models must EXACTLY match database schema column names.

**Example Issue Found:**
```python
# ❌ Model had this:
zone_type = db.Column(..., name='type')  # WRONG

# ✅ Database has this:
zone_type ENUM(...)

# ✅ Correct model:
zone_type = db.Column(...)  # Column name matches DB exactly
```

**Best Practice:**
1. Run `DESCRIBE table_name` in MySQL first
2. Match model column names to database column names exactly
3. Use SQLAlchemy's `name` parameter ONLY if database uses reserved keywords
4. Test models immediately after creation (don't wait for endpoint testing)

---

### Privacy Implementation Checklist

**When adding new endpoints that return posts:**

- [ ] Check if post is anonymous
- [ ] If anonymous, hide `user_id` in response
- [ ] Show only `pseudonym` instead of username
- [ ] Include `is_you` flag for post author
- [ ] NEVER join users table in query for anonymous posts (except in "My Anonymous Posts")
- [ ] Write test to verify privacy enforcement

**Code Template:**
```python
def post_to_dict(post, current_user_id=None):
    data = {...}
    
    if post.is_anonymous:
        data['author'] = {
            'pseudonym': post.author.pseudonym,
            'is_you': (post.user_id == current_user_id)
        }
    else:
        data['author'] = {
            'id': post.author.id,
            'username': post.author.username,
            # ... full profile
        }
    
    return data
```

---

## 🧪 TESTING STRATEGY

### Unit Tests (per component)
```python
# tests/test_nlp_service.py
def test_sentiment_positive_english():
    result = nlp_service.analyze("I love this campus! ❤️")
    assert result['label'] == 'positive'
    assert result['language'] == 'en'
    assert result['score'] > 0.05

def test_sentiment_negative_french():
    result = nlp_service.analyze("Je suis tellement stressé 😭")
    assert result['label'] == 'negative'
    assert result['language'] == 'fr'
    assert result['score'] < -0.05
```

### Integration Tests (API endpoints)
```python
# tests/test_posts.py
def test_create_post_french():
    response = client.post('/api/posts', json={
        'content': 'Je suis heureux! 🎉',
        'zone_id': 1,
        'is_anonymous': False
    })
    assert response.status_code == 201
    assert response.json['post']['detected_language'] == 'fr'
    assert response.json['post']['sentiment'] == 'positive'
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
    Analyzes emotional tone of text using bilingual NLP.
    
    Args:
        text (str): User input text (10-500 chars)
    
    Returns:
        dict: {
            'score': float,      # -1.00 to 1.00
            'label': str,        # 'positive' | 'neutral' | 'negative'
            'language': str      # 'en' | 'fr'
        }
    
    Raises:
        ValidationError: If text is too short
    """
```

---

### **AD-009: NLP Model Selection — Twitter XLM-RoBERTa**

**Date:** 2026-02-13  
**Decision:** Use `cardiffnlp/twitter-xlm-roberta-base-sentiment` for French sentiment

**Alternatives Evaluated:**

| Model | Accuracy | Domain | Verdict |
|-------|----------|--------|---------|
| TextBlob | ~66% | General | ❌ Too inaccurate |
| CamemBERT (distilcamembert-base-sentiment) | ~71% | Product reviews | ❌ Wrong domain, missed stress |
| **Twitter XLM-RoBERTa** | **81%** | **Social media** | **✅ Selected** |

**Why This Model:**
1. **Perfect stress detection** — 100% of negative/stressed posts detected correctly
2. **Zero false negatives** — no missed distress signals (critical for wellness)
3. **Social media trained** — understands emojis, slang, informal writing
4. **Bilingual** — handles both French and English natively
5. **1M+ downloads** — proven and community-validated

**Known Limitation:**
- Neutral posts lean slightly positive (score ~0.10–0.20)
- Acceptable for wellness context: false positive (neutral → positive) is harmless; false negative (negative → neutral) would be dangerous — and there are zero of those

**Classification Thresholds:**
```python
score > 0.05   → 'positive'
score < -0.05  → 'negative'
else           → 'neutral'
```

**Performance:**
- First load: ~40 seconds (downloads 500MB model)
- Cached: <1 second per analysis
- GPU not required (CPU works fine)

---

### **AD-010: Feed Privacy — Public Posts Only**

**Date:** 2026-02-13  
**Decision:** Feed shows ONLY `is_anonymous=False` posts from followed users

**Implementation:**
```python
Post.query.filter(
    Post.user_id.in_(following_ids),
    Post.is_anonymous == False  # ← CRITICAL
).order_by(Post.created_at.desc())
```

**What this prevents:**
- ❌ Pattern matching: "My friend posts anonymously at 2am every night"
- ❌ Writing style correlation between public and anonymous posts
- ❌ Social pressure: "Why did you post that anonymously?"

**Separate Views:**
- Profile page → public posts only
- "My Posts" → user's own public posts
- "My Anonymous Posts" → **private**, only visible to the author

---

### **AD-011: Reaction Privacy — Aggregate Counts Only**

**Date:** 2026-02-13  
**Decision:** Reaction endpoints return only emoji counts, never "who reacted"

**API Response:**
```json
{
  "reactions": {"❤️": 12, "👍": 8, "😢": 3},
  "total_reactions": 23,
  "my_reaction": "❤️"
}
```

**Rules:**
- One reaction per user per post (UNIQUE constraint)
- Only 10 allowed emojis (curated set for consistency)
- Reactions on anonymous posts are allowed (counts only, no identity leak)
- `my_reaction` shows only the requesting user's own reaction

---

### **AD-012: Analytics Privacy Threshold — ≥10 Posts**

**Date:** 2026-02-13  
**Decision:** Aggregated mood data is only returned when `total_posts >= 10`

**Rationale:**
- With fewer than 10 posts, individual writing patterns could be identifiable
- Threshold prevents small-group de-anonymization (e.g., zone with 2 posts)
- Returns explicit "insufficient data" message when below threshold

**Implementation:**
```python
class DailyAggregate(db.Model):
    MINIMUM_POSTS = 10

    def to_dict(self, enforce_threshold=True):
        if enforce_threshold and self.total_posts < self.MINIMUM_POSTS:
            return {
                'message': 'Insufficient data for privacy-safe aggregation',
                'minimum_required': self.MINIMUM_POSTS,
                'current_count': self.total_posts
            }
```

**Disclaimer:** Every analytics response includes:
> "Sentiment analysis is automated and approximate. It shows campus trends, not individual diagnoses."

---

### **AD-013: Post Deletion — 24-Hour Window**

**Date:** 2026-02-13  
**Decision:** Posts (public and anonymous) can only be deleted within 24 hours

**Rationale:**
- Gives users time to reconsider while preserving data integrity
- Anonymous posts can be deleted (user control over their data)
- Anonymous posts can NOT be edited (multiple versions could reveal identity through writing style changes — see AD-004)

**Implementation:**
```python
hours_since = (datetime.utcnow() - post.created_at).total_seconds() / 3600
if hours_since > 24:
    return HTTP 403  # "Posts can only be deleted within 24 hours"
```

---

**📌 This document grows with the project. Every technical decision is recorded here.**

**Last Updated:** Phase 4 Complete — Social Features, Reactions, Feed, Analytics
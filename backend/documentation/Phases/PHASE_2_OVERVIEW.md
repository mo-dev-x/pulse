# 🚀 PHASE 2: POSTS & NLP SENTIMENT ANALYSIS

**Status:** Ready to start  
**Goal:** Enable users to create posts with automatic sentiment analysis

---

## 📋 WHAT WE'LL BUILD

### **1. Post Model** (`app/models/post.py`)
SQLAlchemy model with:
- Content (text, 10-500 characters)
- User ID (always stored, even for anonymous)
- Zone ID (campus location, optional)
- `is_anonymous` flag (boolean)
- Sentiment score (-1.00 to 1.00)
- Sentiment label (positive/neutral/negative)
- Timestamps

**Privacy Rule:** API never exposes `user_id` for anonymous posts!

---

### **2. Campus Zone Model** (`app/models/campus_zone.py`)
Simple model for campus locations:
- Name (e.g., "Library", "Student Center")
- Description
- Type (academic, residence, social, sports, dining)

**Already seeded in database!** We just need the Python model.

---

### **3. NLP Sentiment Service** (`app/services/nlp_service.py`)
VADER-based sentiment analyzer:
- Input: User's text
- Processing: Clean text, analyze emotion
- Output: Score + Label

**Classification:**
```python
score > 0.05   → "positive"  # Happy, optimistic
score < -0.05  → "negative"  # Stressed, sad
else           → "neutral"   # Informational
```

---

### **4. Create Post Endpoint** (`POST /api/posts`)

**Request:**
```json
{
  "content": "Studying for midterms is stressful 😭",
  "zone_id": 1,  // Optional: Library
  "is_anonymous": true
}
```

**Response:**
```json
{
  "post": {
    "id": 123,
    "content": "Studying for midterms is stressful 😭",
    "sentiment": "negative",
    "sentiment_score": -0.68,
    "zone": "Library",
    "is_anonymous": true,
    "author": {
      "pseudonym": "stressed_engineer"  // NOT username!
    },
    "created_at": "2026-02-11T08:00:00Z"
  }
}
```

---

## 🔐 PRIVACY ENFORCEMENT

### **Anonymous Posts:**
```python
# Database: user_id STORED (for deletion, "my posts" view)
post = Post(
    user_id=42,  # Stored in DB
    is_anonymous=True
)

# API Response: user_id HIDDEN
{
    "author": {
        "pseudonym": "calm_coder",  # User's persistent pseudonym
        "is_you": True  # Only for the author
    }
    # NO username, NO user_id exposed!
}
```

### **Public Posts:**
```python
# API Response: Full author info
{
    "author": {
        "username": "johndoe",
        "display_name": "John Doe",
        "profile_picture": "/media/profiles/42.jpg"
    }
}
```

---

## 🧪 TESTING PLAN

### **Test Cases:**
1. ✅ Create public post → Shows username
2. ✅ Create anonymous post → Shows pseudonym only
3. ✅ Sentiment analysis works (positive text → positive label)
4. ✅ Zone association works
5. ✅ Content validation (10-500 chars)
6. ✅ Rate limiting (max 10 posts/hour)
7. ✅ User can see own anonymous posts in private view

---

## 📚 LEARNING OBJECTIVES

By completing Phase 2, you'll learn:

1. **SQLAlchemy Relationships:**
   - Foreign keys (post → user, post → zone)
   - One-to-many relationships
   - Lazy vs eager loading

2. **Service Layer Pattern:**
   - Separate business logic from routes
   - Reusable NLP service
   - Clean code architecture

3. **NLP Basics:**
   - VADER sentiment analysis
   - Text preprocessing
   - Confidence scoring

4. **Privacy Implementation:**
   - Conditional data exposure
   - Serialization logic
   - API-level security

---

## 🎯 DELIVERABLES

By end of Phase 2:

- [ ] Post model with relationships
- [ ] CampusZone model
- [ ] NLP sentiment service (VADER)
- [ ] POST /api/posts endpoint
- [ ] GET /api/posts/feed endpoint
- [ ] GET /api/posts/me/anonymous endpoint
- [ ] Test suite for post creation
- [ ] Privacy verification tests

---

## 🚀 ESTIMATED TIME

- **Post & Zone Models:** 30 minutes
- **NLP Service:** 45 minutes
- **Create Post Endpoint:** 1 hour
- **Testing & Debugging:** 1 hour

**Total:** ~3-4 hours

---

## 📖 NEXT STEPS

Ready to start? I'll guide you through:

1. **First:** Create Post and CampusZone models
2. **Second:** Build NLP sentiment service
3. **Third:** Create POST endpoint with validation
4. **Fourth:** Test everything works
5. **Fifth:** Push to GitHub

---

**Let's build the core feature of Pulse!** 🫀

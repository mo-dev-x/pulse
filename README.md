# 🫀 PULSE BACKEND

**Privacy-First Campus Wellness Platform for Université Laval**

A Flask-based REST API that enables students to share their emotional states anonymously while providing aggregated campus mood insights.

**University:** Université Laval  
**Languages:** Bilingual (French/English)  
**Access:** @ulaval.ca email addresses only

---

## 🎯 PROJECT OVERVIEW

### What is Pulse?

Pulse is a campus wellness platform with three core features:

1. **Social Expression** 
   - Post publicly (linked to your profile) or anonymously (with pseudonym)
   - Follow friends and build connections
   - React with emojis to posts

2. **Privacy Protection**
   - Choose public or anonymous per post
   - Persistent pseudonym (changeable every 90 days)
   - Followers never see your anonymous posts

3. **Collective Insights**
   - Campus-wide mood trends
   - Zone-based sentiment analysis
   - Privacy-safe aggregation (≥10 posts required)

### Core Principle

> **"Individual expression is private, collective insight is public."**

---

## 🏗️ ARCHITECTURE

**Tech Stack:**
- **Backend:** Python 3.12.3 + Flask
- **Database:** MySQL 8.0
- **Authentication:** JWT tokens, bcrypt password hashing
- **NLP:** VADER sentiment analysis
- **API:** RESTful JSON endpoints

**Key Components:**
```
app/
├── models/          # SQLAlchemy database models
├── routes/          # API endpoint blueprints
├── services/        # Business logic (NLP, aggregation)
├── middleware/      # Auth, rate limiting, validation
└── utils/           # Helper functions
```

---

## 📊 DATABASE SCHEMA

**9 Core Tables:**
- `users` - User accounts with public and anonymous identities
- `followers` - Social graph (one-way follows)
- `posts` - Content with sentiment analysis
- `campus_zones` - Campus locations
- `media` - Uploaded images
- `reactions` - Emoji reactions
- `daily_aggregates` - Daily mood statistics
- `weekly_aggregates` - Weekly mood statistics
- `events` - Campus events

**Key Privacy Feature:**
Anonymous posts store `user_id` in database but API **never** exposes it.

---

## 🚀 QUICK START

### Prerequisites
- Python 3.12+
- MySQL 8.0+
- Virtual environment

### Installation

```bash
# 1. Clone/navigate to project
git clone https://github.com/mo-dev-x/pulse-backend.git
cd pulse-backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.template .env
# Edit .env with your MySQL credentials and secret keys

# 5. Initialize database
python setup_db.py

# 6. Run the app
python run.py
```

**See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.**

---

## 📡 API ENDPOINTS

### Authentication
```
POST   /api/auth/register    # Create account
POST   /api/auth/login       # Get JWT token
POST   /api/auth/logout      # Invalidate token
```

### Posts
```
POST   /api/posts                      # Create post (public or anonymous)
GET    /api/posts/feed                 # Timeline (friends' public posts)
GET    /api/posts/@{username}          # User's public posts
GET    /api/posts/me                   # My public posts
GET    /api/posts/me/anonymous         # My anonymous posts (private)
GET    /api/posts/zone/{zone_id}       # Zone feed (all posts)
DELETE /api/posts/{post_id}            # Delete my post
```

### Social
```
POST   /api/follow/@{username}         # Follow user
DELETE /api/unfollow/@{username}       # Unfollow
GET    /api/users/@{username}/followers
GET    /api/users/@{username}/following
GET    /api/users/me/friends           # Mutual follows
```

### Reactions
```
POST   /api/posts/{post_id}/react      # Add emoji reaction
DELETE /api/posts/{post_id}/react      # Remove reaction
GET    /api/posts/{post_id}/reactions  # Get reaction counts
```

### Analytics
```
GET    /api/analytics/daily?date=YYYY-MM-DD&zone_id=X
GET    /api/analytics/weekly?week_start=YYYY-MM-DD
GET    /api/analytics/campus?date=YYYY-MM-DD
```

---

## 🔐 SECURITY FEATURES

### Authentication
- bcrypt password hashing (never plaintext)
- JWT tokens with 24-hour expiration
- Secure secret key management via environment variables

### Privacy Protection
- Anonymous posts never expose `user_id` in API
- Followers can't see friends' anonymous posts
- Aggregation threshold (≥10 posts) prevents individual identification
- Rate limiting (10 posts/hour per user)

### Input Validation
- Content length limits (10-500 characters)
- Zone existence validation
- File type/size restrictions for media uploads
- SQL injection prevention (SQLAlchemy ORM)

---

## 🧪 NLP & SENTIMENT ANALYSIS

**Tool:** VADER (Valence Aware Dictionary and sEntiment Reasoner)

**Classification:**
- **Positive:** score > 0.05 (optimistic, happy)
- **Neutral:** -0.05 ≤ score ≤ 0.05 (informational)
- **Negative:** score < -0.05 (stressed, sad)

**Limitations:**
- May struggle with sarcasm
- Not clinically validated
- Should not be used for individual mental health assessment

**Ethical Disclaimer:**
> "Sentiment analysis is automated and approximate. It's designed to show campus trends, not diagnose individuals. If you're struggling, contact Campus Counseling."

---

## 📚 DOCUMENTATION

- **[QUICKSTART.md](documentation/QUICKSTART.md)** - Setup guide
- **[PROJECT_TRACKER.md](documentation/QUICKSTART.md)** - Development progress
- **[ARCHITECTURE_DECISIONS.md](documentation/QUICKSTART.md)** - Technical decisions
- **[schema.sql](schema.sql)** - Database schema

---

## 🛣️ DEVELOPMENT ROADMAP

### ✅ Phase 1: Foundation (Current)
- [x] Environment setup
- [x] Database schema
- [x] User authentication
- [x] Basic post creation

### ⏳ Phase 2: Privacy & Social
- [x] Anonymous posting
- [ ] Follow/unfollow system
- [ ] Feed generation
- [ ] Friends computation

### ⏳ Phase 3: Interactions
- [ ] Emoji reactions
- [ ] User profiles
- [ ] Media uploads

### ⏳ Phase 4: Analytics
- [ ] Aggregation service
- [ ] Daily/weekly mood calculation
- [ ] Analytics API

---

## 🤝 CONTRIBUTING

This is a university project. Key principles:

1. **Privacy First** - Never compromise user anonymity
2. **Security Always** - No shortcuts on authentication or data protection
3. **Ethical Design** - No individual tracking or emotional profiling
4. **Code Quality** - Documented, tested, maintainable

---

## 📄 LICENSE

Educational project for software engineering coursework.

---

## 🙏 ACKNOWLEDGMENTS

- **VADER Sentiment Analysis** - Hutto, C.J. & Gilbert, E.E. (2014)
- **Flask Framework** - Pallets Projects
- **SQLAlchemy ORM** - Michael Bayer
- **My Partner in crime** - Principessa 

---

## 📧 CONTACT

**Project Lead:** Backend, Data & Intelligence Lead  
**Course:** Software Engineering  
**Institution:** Université Laval

---

**Built with privacy, powered by Python.** 🐍

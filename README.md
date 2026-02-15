# 🫀 PULSE

**Privacy-First Campus Wellness Platform for Université Laval**

A full-stack application enabling students to share their emotional states anonymously while providing aggregated campus mood insights.

**Repository:** Monorepo (Frontend + Backend)  
**University:** Université Laval  
**Languages:** Bilingual (French/English)  
**Access:** @ulaval.ca email addresses only

---

## 📁 REPOSITORY STRUCTURE

This is a **monorepo** containing both frontend and backend:

```
pulse/
├── frontend/          
│   ├── css/
│   ├── images/
│   └── js/
│
├── backend/           # Flask REST API (this README focuses on backend)
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   ├── run.py
│   └── schema.sql
│
└── README.md          # This file
```

**This README primarily documents the backend API.** For frontend documentation, see `frontend/README.md`.

---

## 🎯 PROJECT OVERVIEW

### What is Pulse?

Pulse is a campus wellness platform with three core features:

1. **Social Expression** 
   - Post publicly (linked to your profile) or anonymously (with pseudonym)
   - Follow friends and build connections
   - React with emojis to posts
   - Comment on posts with threading support

2. **Privacy Protection**
   - Choose public or anonymous per post
   - Persistent pseudonym (changeable every 90 days)
   - Followers never see your anonymous posts
   - University-verified accounts (CAS integration)

3. **Collective Insights**
   - Campus-wide mood trends
   - Zone-based sentiment analysis
   - Privacy-safe aggregation (≥10 posts required)
   - Daily and weekly analytics

### Core Principle

> **"Individual expression is private, collective insight is public."**

---

## 🗂️ BACKEND ARCHITECTURE

**Tech Stack:**
- **Backend:** Python 3.12.3 + Flask
- **Database:** MySQL 8.0
- **Authentication:** JWT tokens + Université Laval CAS
- **Security:** bcrypt password hashing, optional 2FA
- **NLP:** VADER (English) + CamemBERT (French) sentiment analysis
- **API:** RESTful JSON endpoints

**Key Components:**
```
backend/app/
├── models/          # SQLAlchemy database models
├── routes/          # API endpoint blueprints
├── services/        # Business logic (NLP, aggregation, email)
├── middleware/      # Auth, rate limiting, validation
└── utils/           # Helper functions, i18n
```

---

## 📊 DATABASE SCHEMA

**14 Core Tables:**
- `users` - User accounts with public and anonymous identities
- `followers` - Social graph (one-way follows)
- `posts` - Content with sentiment analysis
- `comments` - Post comments with threading
- `campus_zones` - Campus locations
- `media` - Uploaded images
- `reactions` - Emoji reactions
- `notifications` - User notifications
- `sessions` - Active user sessions
- `bookmarks` - Saved posts
- `daily_aggregates` - Daily mood statistics
- `weekly_aggregates` - Weekly mood statistics
- `security_logs` - Security event audit trail
- `events` - Campus events (future)

**Key Privacy Feature:**
Anonymous posts store `user_id` in database but API **never** exposes it.

---

## 🚀 QUICK START

### Prerequisites
- Python 3.12+
- MySQL 8.0+
- Virtual environment
- SMTP server (for email verification)
- CAS credentials (for production)

### Backend Installation

```bash
# 1. Clone repository
git clone https://github.com/mo-dev-x/pulse.git
cd pulse/backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install PyTorch (CPU version)
# PyTorch is installed separately to avoid downloading GPU CUDA libraries (~4GB)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 4. Install remaining Python dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.template .env
# Edit .env with your MySQL credentials, secret keys, SMTP config

# 6. Initialize database
python setup_db.py

# 7. Run the backend
python run.py
```

**Backend runs on:** `http://localhost:5000`

### Frontend Installation

```bash
# From repository root
cd frontend

# Install dependencies
npm install

# Configure API endpoint
# Edit .env or config to point to http://localhost:5000

# Run development server
npm run dev
```

**See [backend/QUICKSTART.md](backend/QUICKSTART.md) for detailed backend setup.**  
**See [frontend/QUICKSTART.md](frontend/QUICKSTART.md) for detailed frontend setup.**

---

## 📡 API ENDPOINTS

### Authentication
```
POST   /api/auth/register              # Create account
POST   /api/auth/login                 # Get JWT token
POST   /api/auth/logout                # Invalidate token
GET    /api/auth/me                    # Get current user
PATCH  /api/auth/update-profile        # Update profile
PATCH  /api/auth/update-bio            # Update bio
POST   /api/auth/upload-profile-pic    # Upload profile picture
GET    /api/auth/cas/login             # CAS SSO login (production)
GET    /api/auth/cas/callback          # CAS callback
POST   /api/auth/send-verification     # Send verification email
GET    /api/auth/verify-email/{token}  # Verify email
POST   /api/auth/forgot-password       # Request password reset
POST   /api/auth/reset-password        # Reset password
```

### Posts
```
POST   /api/posts                      # Create post (public or anonymous)
GET    /api/posts/feed                 # Timeline (friends' public posts)
GET    /api/posts/@{username}          # User's public posts
GET    /api/posts/me                   # My public posts
GET    /api/posts/me/anonymous         # My anonymous posts (private)
GET    /api/posts/zone/{zone_id}       # Zone feed (all posts)
DELETE /api/posts/{post_id}            # Delete my post (24h window)
```

### Comments
```
POST   /api/posts/{post_id}/comments   # Add comment
GET    /api/posts/{post_id}/comments   # List comments (paginated)
GET    /api/comments/{id}/replies      # Get comment replies
PATCH  /api/comments/{id}              # Edit comment (5min window)
DELETE /api/comments/{id}              # Delete comment
```

### Social
```
POST   /api/follow/@{username}         # Follow user
DELETE /api/unfollow/@{username}       # Unfollow
GET    /api/users/@{username}/followers
GET    /api/users/@{username}/following
GET    /api/users/me/friends           # Mutual follows
GET    /api/users/@{username}          # User profile
```

### Reactions
```
POST   /api/posts/{post_id}/react      # Add emoji reaction
DELETE /api/posts/{post_id}/react      # Remove reaction
GET    /api/posts/{post_id}/reactions  # Get reaction counts
```

### Notifications
```
GET    /api/notifications              # List notifications
PATCH  /api/notifications/{id}/read    # Mark as read
PATCH  /api/notifications/read-all     # Mark all as read
DELETE /api/notifications/{id}         # Delete notification
```

### Bookmarks
```
POST   /api/posts/{post_id}/bookmark   # Bookmark post
DELETE /api/posts/{post_id}/bookmark   # Remove bookmark
GET    /api/bookmarks                  # List bookmarked posts
```

### Analytics
```
GET    /api/analytics/daily?date=YYYY-MM-DD&zone_id=X
GET    /api/analytics/weekly?week_start=YYYY-MM-DD&zone_id=X
GET    /api/analytics/campus?date=YYYY-MM-DD
```

**Total:** 55+ endpoints

---

## 🔐 SECURITY FEATURES

### Authentication & Authorization
- ✅ JWT tokens with 24-hour expiration
- ✅ bcrypt password hashing (cost factor 12)
- ✅ Université Laval CAS integration (SSO)
- ✅ Email verification for new accounts
- ✅ Secure password reset flow
- ✅ Optional 2FA (TOTP)
- ✅ Session management and tracking
- ✅ Security audit logs

### Privacy Protection
- ✅ Anonymous posting with persistent pseudonyms
- ✅ User ID never exposed for anonymous posts
- ✅ Reaction privacy (only aggregates shown)
- ✅ Profile visibility controls
- ✅ Privacy threshold (≥10 posts) for analytics
- ✅ Deactivation vs deletion options

### Data Protection
- ✅ @ulaval.ca email validation
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS protection (input sanitization)
- ✅ CORS configuration
- ✅ Rate limiting (planned)
- ✅ File upload restrictions

---

## 🌍 BILINGUAL SUPPORT

All user-facing messages support both French and English:

```python
# Example usage
from app.utils.i18n import get_message, get_bilingual_message

# Get message in specific language
error_msg = get_message('validation_error', 'fr')  # French
success_msg = get_message('post_created', 'en')    # English

# Get both languages
both = get_bilingual_message('welcome')
# Returns: {'fr': 'Bienvenue', 'en': 'Welcome'}
```

**Supported:**
- API response messages
- Email templates
- Error messages
- Success notifications

---

## 🧪 TESTING

### Test Suites

```bash
# Run all tests
cd backend
python -m pytest tests/

# Run specific test suites
python tests/test_auth.py          # Authentication (7 tests)
python tests/test_posts.py         # Posts & NLP (8 tests)
python tests/test_reactions.py     # Reactions (26 tests)
python tests/test_analytics.py     # Analytics (30 tests)
python tests/test_social.py        # Social features
```

**Current Status:** 71/71 tests passing ✅

**Phase 5 Target:** 120+ tests (adding comment, notification, auth tests)

---

## 📚 DOCUMENTATION

### Core Documentation
- **[README.md](README.md)** - This file (API overview)
- **[backend/QUICKSTART.md](backend/QUICKSTART.md)** - Detailed setup guide
- **[backend/ARCHITECTURE_DECISIONS.md](backend/documentation/ARCHITECTURE_DECISIONS.md)** - Technical decisions
- **[backend/PROJECT_TRACKER.md](backend/documentation/PROJECT_TRACKER.md)** - Current development (Phase 5)
- **[backend/INITIAL_PHASES_TRACKER.md](backend/documentation/Phases/INITIAL_PHASES_TRACKER.md)** - Phases 1-4 history

### Phase Documentation
- **[backend/PHASE_1_OVERVIEW.md](backend/documentation/Phases/PHASE_1_OVERVIEW.md)** - Foundation (Complete)
- **[backend/PHASE_2_OVERVIEW.md](backend/documentation/Phases/PHASE_2_OVERVIEW.md)** - Posts & NLP (Complete)
- **[backend/PHASE_3_OVERVIEW.md](backend/documentation/Phases/PHASE_3_OVERVIEW.md)** - Social Features (Complete)
- **[backend/PHASE_4_OVERVIEW.md](backend/documentation/Phases/PHASE_4_OVERVIEW.md)** - Analytics (Complete)
- **[backend/PHASE_5_OVERVIEW.md](backend/documentation/PHASE_5_OVERVIEW.md)** - Production Auth & UX (In Progress)

### Technical Guides
- **[backend/BILINGUAL_GUIDE.md](backend/documentation/Technical/BILINGUAL_GUIDE.md)** - Bilingual NLP implementation
- **[backend/EMOJI_COLLATION_BUG.md](backend/documentation/Technical/EMOJI_COLLATION_BUG.md)** - Critical bug fix documentation
- **[backend/CAS_INTEGRATION_GUIDE.md](backend/documentation/Technical/CAS_INTEGRATION_GUIDE.md)** - CAS setup (Phase 5)

---

## 🎯 PROJECT STATUS

### Completed Phases (100%)
- ✅ **Phase 1:** Foundation - Auth, Database, NLP (7/7 tests)
- ✅ **Phase 2:** Posts & NLP - Sentiment Analysis (8/8 tests)
- ✅ **Phase 3:** Social Features - Follows, Reactions, Feeds (26/26 tests)
- ✅ **Phase 4:** Analytics - Mood Insights, Privacy Thresholds (30/30 tests)

### Current Phase (Phase 5 - In Progress)
- 🚧 **Phase 5:** Production Auth & UX (0/50 tests)
  - Email verification system
  - Université Laval CAS integration
  - Password reset flow
  - Profile customization (bio, pictures)
  - Comment system with threading
  - Notification system
  - Session management
  - 2FA (optional)

**Timeline:** 10-14 days  
**Priority:** High - Production Readiness

---

## 🔧 DEVELOPMENT

### Project Structure

```
pulse/
├── frontend/                      # Frontend application
│
└── backend/                       # Backend API (Flask)
    ├── app/
    │   ├── __init__.py           # Flask app factory
    │   ├── models/               # Database models
    │   │   ├── user.py
    │   │   ├── post.py
    │   │   ├── comment.py
    │   │   ├── reaction.py
    │   │   ├── notification.py
    │   │   └── ...
    │   ├── routes/               # API endpoints
    │   │   ├── auth.py
    │   │   ├── posts.py
    │   │   ├── social.py
    │   │   ├── reactions.py
    │   │   ├── analytics.py
    │   │   └── ...
    │   ├── services/             # Business logic
    │   │   ├── nlp_service_camembert.py
    │   │   ├── aggregation_service.py
    │   │   ├── email_service.py
    │   │   └── notification_service.py
    │   └── utils/
    │       └── i18n.py           # Bilingual messages
    ├── tests/                    # Test suites
    ├── requirements.txt          # Python dependencies
    ├── run.py                    # Application entry point
    └── schema.sql                # Database schema
```

### Environment Variables

```bash
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=pulse_user
MYSQL_PASSWORD=***
MYSQL_DATABASE=pulse_db

# JWT
JWT_SECRET_KEY=***

# CAS (Production)
CAS_SERVER_URL=https://cas.ulaval.ca/cas/
CAS_SERVICE_URL=https://pulse.ulaval.ca/auth/callback

# Email (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@pulse.ulaval.ca
SMTP_PASSWORD=***

# File Uploads
UPLOAD_DIR=/var/www/pulse/uploads
MAX_FILE_SIZE=5242880  # 5MB

# Frontend
FRONTEND_URL=http://localhost:3000  # Development
```

---

## 🚀 DEPLOYMENT

### Production Checklist

**Backend:**
- [ ] HTTPS enabled
- [ ] Environment variables secured
- [ ] SMTP server configured
- [ ] CAS credentials obtained
- [ ] File upload directory configured
- [ ] Database backups scheduled
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] All tests passing (120+)

**Frontend:**
- [ ] API endpoint configured
- [ ] Build optimized
- [ ] CORS configured
- [ ] Analytics integrated
- [ ] Error tracking enabled

---

## 👥 TEAM

**Backend Developer:** Full-stack focus (Python, Flask, MySQL)  
**Frontend Developer:** UI/UX focus (HTML/CSS, JavaScript, API integration)  
**University IT:** CAS integration support

---

## 📝 LICENSE

Internal use - Université Laval

---

## 📞 CONTACT

For questions or issues, please contact the development team or open an issue in the repository.

---

**Last Updated:** February 14, 2026  
**Backend Status:** Phase 4 Complete, Phase 5 In Progress  
**Frontend Status:** Phase 1 Complete, Phase 2 In Progress  
**Repository:** [github.com/mo-dev-x/pulse](https://github.com/mo-dev-x/pulse)
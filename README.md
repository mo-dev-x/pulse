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
├── Frontend/              # Vanilla JS Frontend (Principessa)
│   ├── css/
│   │   └── login.css
│   ├── js/
│   │   ├── auth.js       # Token helpers + apiFetch
│   │   ├── login.js
│   │   └── register.js
│   ├── login.html
│   ├── register.html
│   ├── feed.html
│   └── QUICKSTART.md     # Frontend quickstart
│
├── backend/               # Flask REST API
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
└── README.md             # This file
```

**Frontend:** Vanilla JavaScript (HTML + CSS + ES Modules)  
**Backend:** Python Flask REST API with JWT authentication

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
   - University-verified accounts via email verification (OIDC/Entra ready but currently disabled)

3. **Collective Insights**
   - Campus-wide mood trends
   - Zone-based sentiment analysis
   - Privacy-safe aggregation (≥10 posts required)
   - Daily and weekly analytics

### Core Principle

> **"Individual expression is private, collective insight is public."**

---

## 🚀 QUICK START

### Prerequisites
- **Backend:** Python 3.12+, MySQL 8.0+, Virtual environment
- **Frontend:** Any modern browser, Python 3 (for HTTP server)
- **SMTP server** (for email verification - Phase 5)
- **OIDC (Azure Entra) app credentials** (optional for future re-enable)

---

## 🖥️ FRONTEND SETUP

### Installation & Running

```bash
# 1. Navigate to frontend directory
cd pulse/Frontend

# 2. Run HTTP server (required for ES modules)
python3 -m http.server 8000

# 3. Open in browser
# Login: http://127.0.0.1:8000/login.html
# Register: http://127.0.0.1:8000/register.html
# Feed: http://127.0.0.1:8000/feed.html
```

**Important:** Frontend MUST be served via HTTP server (not `file://`) for ES modules to work.

### Frontend Configuration

- **Backend API URL:** `http://127.0.0.1:5000`
- **Frontend URL:** `http://127.0.0.1:8000`
- **JWT Storage:** LocalStorage key `pulse_token`
- **Auth Method:** Bearer token in Authorization header

### Frontend Architecture

**Tech Stack:**
- Vanilla JavaScript (ES Modules)
- HTML5 + CSS3
- No framework dependencies
- `python3 -m http.server` for development

**Key Files:**
- `js/auth.js` - Token management, API fetch wrapper
- `js/login.js` - Login page logic
- `js/register.js` - Registration with @ulaval.ca validation
- `css/login.css` - Shared styles (glass UI, gradients)

### Frontend Status

| Phase | Status | Completion |
|-------|--------|------------|
| **Phase 1:** Foundation | ✅ Complete | 100% |
| **Phase 2:** Auth Integration | ✅ Complete | 90% |
| **Phase 3:** Feed UI | 🟡 In Progress | 60% |
| **Phase 4:** Feed API Integration | 🟠 Next | 0% |
| **Phase 5:** UX Polish | 🔵 Later | 0% |
| **Phase 6:** Analytics UI | 🔵 Later | 0% |

**Current:** Building feed page (sidebar ✅, navbar ✅, posts section in progress)

**See [Frontend/QUICKSTART.md](Frontend/QUICKSTART.md) for detailed frontend documentation.**

---

## ⚙️ BACKEND SETUP

### Installation

```bash
# 1. Navigate to backend directory
cd pulse/backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install PyTorch (CPU version)
# PyTorch installed separately to avoid GPU CUDA libraries (~4GB)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 4. Install remaining dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.template .env
# Edit .env with your MySQL credentials, secret keys, SMTP config

# 6. Initialize database
python setup_db.py

# 7. Run the backend
python run.py
```

**Backend runs on:** `http://127.0.0.1:5000`

**See [backend/QUICKSTART.md](backend/QUICKSTART.md) for detailed backend setup.**

---

## 🔗 FRONTEND ↔ BACKEND INTEGRATION

### Authentication Flow

1. **Register:** `POST /api/auth/register`
   - Frontend validates `@ulaval.ca` email
   - Backend creates user, returns JWT token
   - Frontend stores token in `localStorage.pulse_token`

2. **Login:** `POST /api/auth/login`
   - Backend validates credentials
   - Returns JWT token (24-hour expiration)
   - Frontend stores token, redirects to feed

3. **Protected Routes:** 
   - Frontend checks `localStorage.pulse_token` exists
   - Sends `Authorization: Bearer <token>` header
   - Backend validates JWT on protected endpoints

4. **Token Verification:** `GET /api/auth/me`
   - Frontend can verify token validity
   - Returns current user profile

### CORS Configuration

Backend allows requests from:
- `http://127.0.0.1:8000` (frontend dev server)
- Configured in backend CORS settings

### API Response Format

API responses use JSON (shape varies by endpoint):
```json
{
  "message": "Success message",
  "data": { /* response data */ },
  "error": "Error message (if any)"
}
```

---

## 🗂️ BACKEND ARCHITECTURE

**Tech Stack:**
- **Backend:** Python 3.12.3 + Flask
- **Database:** MySQL 8.0
- **Authentication:** JWT tokens + email verification (OIDC/Entra currently feature-flagged off)
- **Security:** bcrypt password hashing, optional 2FA (Phase 5)
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
- `comments` - Post comments with threading (Phase 5)
- `campus_zones` - Campus locations
- `media` - Uploaded images
- `reactions` - Emoji reactions
- `notifications` - User notifications (Phase 5)
- `sessions` - Active user sessions (Phase 5)
- `bookmarks` - Saved posts (Phase 5)
- `daily_aggregates` - Daily mood statistics
- `weekly_aggregates` - Weekly mood statistics
- `security_logs` - Security event audit trail (Phase 5)
- `events` - Campus events (future)

**Key Privacy Feature:**
Anonymous posts store `user_id` in database but API **never** exposes it.

---

## 📡 API ENDPOINTS

### Authentication (Phase 2 - Working)
```
POST   /api/auth/register              # Create account ✅
POST   /api/auth/login                 # Get JWT token ✅
POST   /api/auth/logout                # Invalidate token
GET    /api/auth/me                    # Get current user ✅
PATCH  /api/auth/update-profile        # Update profile
PATCH  /api/auth/update-pseudonym      # Change pseudonym
```

### Posts (Phase 3 - Backend Complete)
```
POST   /api/posts                      # Create post
GET    /api/posts/feed                 # Timeline (friends' posts) 🔜 Frontend next
GET    /api/posts/@{username}          # User's public posts
GET    /api/posts/me                   # My public posts
GET    /api/posts/me/anonymous         # My anonymous posts
GET    /api/posts/zone/{zone_id}       # Zone feed
DELETE /api/posts/{post_id}            # Delete post (24h window)
```

### Social (Phase 3 - Backend Complete)
```
POST   /api/follow/@{username}         # Follow user
DELETE /api/unfollow/@{username}       # Unfollow
GET    /api/users/@{username}/followers
GET    /api/users/@{username}/following
GET    /api/users/me/friends           # Mutual follows
GET    /api/users/@{username}          # User profile
```

### Reactions (Phase 3 - Backend Complete)
```
POST   /api/posts/{post_id}/react      # Add emoji reaction
DELETE /api/posts/{post_id}/react      # Remove reaction
GET    /api/posts/{post_id}/reactions  # Get reaction counts
```

### Analytics (Phase 4 - Backend Complete)
```
GET    /api/analytics/daily?date=YYYY-MM-DD&zone_id=X
GET    /api/analytics/weekly?week_start=YYYY-MM-DD&zone_id=X
GET    /api/analytics/campus?date=YYYY-MM-DD
```

### Phase 5 Endpoints (In Development)
```
POST   /api/auth/send-verification     # Send verification email
GET    /api/auth/verify-email/{token}  # Verify email
POST   /api/auth/forgot-password       # Request password reset
POST   /api/auth/reset-password        # Reset password
POST   /api/auth/upload-profile-pic    # Upload profile picture
POST   /api/posts/{post_id}/comments   # Add comment
GET    /api/posts/{post_id}/comments   # List comments
GET    /api/notifications              # List notifications
POST   /api/posts/{post_id}/bookmark   # Bookmark post
GET    /api/auth/oidc/login            # OIDC SSO login (disabled by default)
GET    /api/auth/oidc/callback         # OIDC callback (disabled by default)
```

**Total:** 55+ endpoints (25 complete, 30+ in Phase 5)

---

## 🔐 SECURITY FEATURES

### Authentication & Authorization
- ✅ JWT tokens with 24-hour expiration
- ✅ bcrypt password hashing (cost factor 12)
- ✅ @ulaval.ca email validation
- ✅ Email verification for new accounts (Phase 5)
- ⏸️ Université Laval OIDC / Entra integration (implemented, disabled pending university access)
- ✅ Secure password reset flow (Phase 5)
- 🚧 Optional 2FA (TOTP) (Phase 5)
- 🚧 Session management and tracking (Phase 5)

### Privacy Protection
- ✅ Anonymous posting with persistent pseudonyms
- ✅ User ID never exposed for anonymous posts
- ✅ Reaction privacy (only aggregates shown)
- ✅ Privacy threshold (≥10 posts) for analytics
- 🚧 Profile visibility controls (Phase 5)
- 🚧 Account deactivation (Phase 5)

### Data Protection
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS protection (input sanitization)
- ✅ CORS configuration
- ✅ File upload restrictions
- 🚧 Rate limiting (Phase 5)
- 🚧 Security audit logs (Phase 5)

---

## 🌍 BILINGUAL SUPPORT

All user-facing messages support both French and English:

```python
# Backend example
from app.utils.i18n import get_message, get_bilingual_message

error_msg = get_message('validation_error', 'fr')  # French
success_msg = get_message('post_created', 'en')    # English
```

**Supported:**
- API response messages
- Email templates
- Error messages
- Success notifications

---

## 🧪 TESTING

### Backend Test Suites

```bash
# Run all tests
cd backend
python -m pytest tests/

# Run specific test suites
python tests/test_auth.py          # Authentication (7 tests) ✅
python tests/test_posts.py         # Posts & NLP (8 tests) ✅
python tests/test_reactions.py     # Reactions (26 tests) ✅
python tests/test_analytics.py     # Analytics (30 tests) ✅
python tests/test_social.py        # Social features ✅
```

**Backend Status:** 71/71 tests passing ✅

**Phase 5 Target:** 120+ tests (adding email, OIDC-ready, comment tests)

### Frontend Testing

Currently manual testing via browser:
- Register flow with @ulaval.ca validation
- Login flow with token storage
- Protected route access
- Token verification via `/api/auth/me`

**Frontend automated tests:** Planned for Phase 5

---

## 📚 DOCUMENTATION

### Core Documentation
- **[README.md](README.md)** - This file (project overview)
- **[Frontend/QUICKSTART.md](Frontend/QUICKSTART.md)** - Frontend-specific guide (by Principessa)
- **[backend/QUICKSTART.md](backend/QUICKSTART.md)** - Backend setup guide
- **[backend/documentation/ARCHITECTURE_DECISIONS.md](backend/documentation/ARCHITECTURE_DECISIONS.md)** - Technical decisions
- **[backend/documentation/PROJECT_TRACKER.md](backend/documentation/PROJECT_TRACKER.md)** - Backend development (Phase 5)
- **[backend/documentation/Phases/INITIAL_PHASES_TRACKER.md](backend/documentation/Phases/INITIAL_PHASES_TRACKER.md)** - Phases 1-4 history

### Phase Documentation
- **[backend/documentation/Phases/PHASE_1_OVERVIEW.md](backend/documentation/Phases/PHASE_1_OVERVIEW.md)** - Foundation (Complete)
- **[backend/documentation/Phases/PHASE_2_OVERVIEW.md](backend/documentation/Phases/PHASE_2_OVERVIEW.md)** - Posts & NLP (Complete)
- **[backend/documentation/Phases/PHASE_3_OVERVIEW.md](backend/documentation/Phases/PHASE_3_OVERVIEW.md)** - Social Features (Complete)
- **[backend/documentation/Phases/PHASE_4_OVERVIEW.md](backend/documentation/Phases/PHASE_4_OVERVIEW.md)** - Analytics (Complete)
- **[backend/documentation/PHASE_5_OVERVIEW.md](backend/documentation/PHASE_5_OVERVIEW.md)** - Production Auth & UX (In Progress)

### Technical Guides
- **[backend/documentation/Technical/BILINGUAL_GUIDE.md](backend/documentation/Technical/BILINGUAL_GUIDE.md)** - Bilingual NLP implementation
- **[backend/documentation/Technical/EMOJI_COLLATION_BUG.md](backend/documentation/Technical/EMOJI_COLLATION_BUG.md)** - Critical bug fix documentation
- **[backend/documentation/Technical/MIGRATION_GUIDE.md](backend/documentation/Technical/MIGRATION_GUIDE.md)** - Migration runbook
- **[backend/documentation/Technical/OIDC_ENTRA_INTEGRATION_GUIDE.md](backend/documentation/Technical/OIDC_ENTRA_INTEGRATION_GUIDE.md)** - OIDC integration details
- **[backend/documentation/Technical/OIDC_REENABLE_PLAYBOOK.md](backend/documentation/Technical/OIDC_REENABLE_PLAYBOOK.md)** - Step-by-step re-enable checklist

---

## 🎯 PROJECT STATUS

### Backend Progress

**Completed Phases (100%):**
- ✅ **Phase 1:** Foundation - Auth, Database, NLP (7/7 tests)
- ✅ **Phase 2:** Posts & NLP - Sentiment Analysis (8/8 tests)
- ✅ **Phase 3:** Social Features - Follows, Reactions, Feeds (26/26 tests)
- ✅ **Phase 4:** Analytics - Mood Insights, Privacy Thresholds (30/30 tests)

**Current Phase:**
- 🚧 **Phase 5:** Production Auth & UX (In Progress)
  - Email verification system (active)
  - Université Laval OIDC / Entra integration (paused behind feature flag)
  - Password reset flow (active)
  - Profile customization (bio, pictures)
  - Comment system with threading
  - Notification system
  - Session management
  - 2FA (optional)

**Timeline:** 10-14 days for Phase 5  
**Priority:** High - Production Readiness

### Frontend Progress

| Component | Status | Notes |
|-----------|--------|-------|
| Login Page | ✅ Complete | JWT auth working |
| Register Page | ✅ Complete | Email validation working |
| Feed Layout | 🟡 In Progress | Sidebar + navbar done |
| Feed Posts | 🟠 Next | Will use `GET /api/posts/feed` |
| Post Creation | 🔵 Planned | Phase 4 |
| User Profiles | 🔵 Planned | Phase 4 |
| Analytics Dashboard | 🔵 Planned | Phase 6 |

**Overall Progress:** ~65%

---

## 🔧 DEVELOPMENT

### Running Both Frontend + Backend

**Terminal 1 (Backend):**
```bash
cd pulse/backend
source venv/bin/activate
python run.py
# Runs on http://127.0.0.1:5000
```

**Terminal 2 (Frontend):**
```bash
cd pulse/Frontend
python3 -m http.server 8000
# Serves on http://127.0.0.1:8000
```

**Open Browser:**
- Frontend: http://127.0.0.1:8000/login.html
- Backend API: http://127.0.0.1:5000/api/auth/me (requires token)

### Development Workflow

1. **Backend changes:** Edit Python files, Flask auto-reloads
2. **Frontend changes:** Edit HTML/CSS/JS, refresh browser
3. **API testing:** Use browser DevTools Network tab or Postman
4. **Token inspection:** `localStorage.getItem('pulse_token')` in console

### Environment Variables

```bash
# Backend (.env)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=pulse_user
MYSQL_PASSWORD=***
MYSQL_DATABASE=pulse_db
JWT_SECRET_KEY=***
FRONTEND_URL=http://127.0.0.1:8000

# Frontend (hardcoded in auth.js)
BACKEND_URL=http://127.0.0.1:5000
JWT_STORAGE_KEY=pulse_token
```

---

## 🚀 DEPLOYMENT

### Production Checklist

**Backend:**
- [ ] HTTPS enabled
- [ ] Environment variables secured
- [ ] SMTP server configured
- [ ] OIDC app credentials obtained (only needed when re-enabling institutional login)
- [ ] File upload directory configured
- [ ] Database backups scheduled
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] All tests passing (120+)

**Frontend:**
- [ ] Update API base URL to production backend
- [ ] Enable HTTPS
- [ ] Minify JavaScript/CSS
- [ ] Add error tracking (e.g., Sentry)
- [ ] Add analytics (e.g., Plausible)
- [ ] Configure CSP headers
- [ ] Test on multiple browsers

**Integration:**
- [ ] CORS configured for production domain
- [ ] JWT tokens use secure cookies (not localStorage)
- [ ] Session timeout implemented
- [ ] Rate limiting on auth endpoints

---

## 👥 TEAM

**Backend Developer:** Full-stack focus (Python, Flask, MySQL, NLP)  
**Frontend Developer (Principessa):** UI/UX focus (HTML, CSS, JavaScript, API integration)  
**University IT:** OIDC / Entra integration support (future re-enable)

---

## 🐛 KNOWN ISSUES

### Backend
- ✅ Emoji collation bug - FIXED (Feb 14, 2026)
- ✅ Analytics response structure - FIXED (Feb 14, 2026)
- 🚧 Phase 5 features in development

### Frontend
- ✅ ES modules working via HTTP server
- ✅ Token storage and retrieval working
- ⚠️ Logout button not implemented yet (manual removal works)
- ⚠️ Feed posts not loading yet (API integration pending)
- ⚠️ Empty states and loading spinners needed

### Integration
- ✅ CORS working between frontend and backend
- ✅ JWT authentication working end-to-end
- ⚠️ Token refresh not implemented (24h expiration)

---

## 📝 LICENSE

Internal use - Université Laval

---

## 📞 CONTACT

For questions or issues, please contact the development team or open an issue in the repository.

---

## 🔗 QUICK LINKS

**Frontend:**
- Login: http://127.0.0.1:8000/login.html
- Register: http://127.0.0.1:8000/register.html
- Feed: http://127.0.0.1:8000/feed.html

**Backend:**
- API Base: http://127.0.0.1:5000
- Health Check: http://127.0.0.1:5000/api/auth/me (with token)

**Documentation:**
- Frontend Guide: [Frontend/QUICKSTART.md](Frontend/QUICKSTART.md)
- Backend Guide: [backend/QUICKSTART.md](backend/QUICKSTART.md)
- Backend Tracker: [backend/documentation/PROJECT_TRACKER.md](backend/documentation/PROJECT_TRACKER.md)

---

**Last Updated:** February 14, 2026  
**Backend Status:** Phase 4 Complete (71/71 tests ✅), Phase 5 In Progress (90% planned)  
**Frontend Status:** Phase 2 Complete (90%), Phase 3 In Progress (60%)  
**Repository:** [github.com/mo-dev-x/pulse](https://github.com/mo-dev-x/pulse)

---

## 🎉 MILESTONE ACHIEVEMENTS

**February 2026:**
- ✅ Backend Phases 1-4 Complete (71/71 tests passing)
- ✅ Frontend Auth Integration Complete (login + register working)
- ✅ JWT authentication working end-to-end
- ✅ Emoji collation bug resolved
- ✅ Analytics endpoints operational
- 🚧 Backend Phase 5 in development
- 🚧 Frontend feed UI in progress

**Next Major Milestone:** Feed API integration + Backend Phase 5 completion 🚀

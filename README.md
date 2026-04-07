# 🫀 PULSE

**Privacy-First Campus Wellness Platform for Université Laval**

A full-stack application enabling students to share their emotional states publicly or anonymously while providing privacy-safe campus mood insights.

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
   - Manage your anonymous identity — custom pseudonym, changeable every 90 days, from Settings
   - Follow friends and build connections
   - React to posts via an emoji picker (tap + to reveal reactions)
   - Comment on posts with threading support

2. **Privacy Protection**
   - Choose public or anonymous per post
   - Persistent pseudonym (changeable every 90 days via Settings)
   - Followers never see your anonymous posts
   - University-verified accounts via email verification (OIDC/Entra ready but currently disabled)
   - Email notifications for reactions, comments, follows, and mentions (on by default)

3. **Collective Insights**
   - Campus-wide mood trends
   - Zone-based sentiment analysis
   - Personalised home feed: posts from followed accounts blended with interest-based suggestions from non-followed accounts (ranked by engagement + recency)
   - Discovery and trending feeds
   - Privacy-safe aggregation (≥10 posts required)
   - Daily and weekly analytics

4. **Platform Systems**
   - Unified search across posts, users, and zones
   - Moderation and reporting workflow
   - Direct messaging: text, images, videos, and voice messages
   - Instagram-style notification centre with grouping (Today / This week / Earlier)
   - Push-ready notification infrastructure
   - Mobile-friendly navigation via slide-in drawer (hamburger menu)
   - Caching and optional Redis/RQ background jobs

### Core Principle

> **"Individual expression is private, collective insight is public."**

---

## 🚀 QUICK START

### Prerequisites
- **Backend:** Python 3.12+, MySQL 8.0+, Virtual environment
- **Frontend:** Any modern browser, Python 3 (for HTTP server)
- **SMTP server** (for email verification / password reset)
- **Redis** (optional for production rate limiting + background jobs)
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
- **Deployed Backend API URL:** `https://pulse-backend.up.railway.app/`
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
| **Phase 2:** Auth Integration | ✅ Complete | 100% |
| **Phase 3:** Feed UI | ✅ Complete | 100% |
| **Phase 4:** Feed API Integration | 🟡 In Progress | ~60% |
| **Phase 5:** UX Polish | 🔵 Later | 0% |
| **Phase 6:** Advanced UI integrations | 🔵 Later | 0% |

**Current:** Feed API integration (reactions, comments, full wiring) is the active focus.

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

# 3. Install lightweight backend dependencies
pip install -r requirements.txt

# 4. Optional: install ML dependencies for advanced French sentiment
pip install -r requirements-ml.txt

# 5. Set up environment variables
cp .env.template .env
# Edit .env with your MySQL credentials, secret keys, SMTP config

# 6. Initialize database
python setup_db.py

# 7. Run the backend
python run.py
```

**Backend runs on:** `http://127.0.0.1:5000`

**Deployed backend:** `https://pulse-backend.up.railway.app/`

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
- **Backend:** Python 3.12 + Flask
- **Database:** MySQL 8.0
- **Authentication:** JWT tokens + email verification (OIDC/Entra currently feature-flagged off)
- **Security:** bcrypt, optional 2FA, session tracking, security logs, rate limiting
- **Search & Discovery:** unified search, trending, zone discovery
- **Infra:** Flask-Caching, optional Redis/RQ background jobs
- **NLP:** VADER (English) + CamemBERT (French) sentiment analysis
- **API:** RESTful JSON endpoints

**Key Components:**
```
backend/app/
├── models/          # SQLAlchemy database models
├── routes/          # API endpoint blueprints
├── services/        # Business logic (NLP, aggregation, email, jobs)
├── middleware/      # Auth, verification, admin checks
├── tasks/           # Background job entrypoints
└── utils/           # Helper functions, i18n
```

---

## 📊 DATABASE SCHEMA

**Current Major Tables:**
- `users` - User accounts with public and anonymous identities
- `followers` - Social graph (one-way follows)
- `posts` - Content with sentiment analysis
- `comments` - Post comments with threading
- `campus_zones` - Campus locations
- `media` - Uploaded images
- `reactions` - Emoji reactions
- `notifications` - In-app notifications
- `sessions` - Active user sessions
- `bookmarks` - Saved posts
- `reports` - Moderation reporting pipeline
- `conversations` - Direct message threads
- `messages` - Direct message content
- `push_subscriptions` - Push delivery registrations
- `daily_aggregates` - Daily mood statistics
- `weekly_aggregates` - Weekly mood statistics
- `security_logs` - Security and moderation audit trail

**Key Privacy Feature:**
Anonymous posts store `user_id` in database but API **never** exposes it.

---

## 📡 API ENDPOINTS

### Authentication & Account Security
```
POST   /api/auth/register              # Create account ✅
POST   /api/auth/login                 # Get JWT token ✅
POST   /api/auth/logout                # Logout / revoke session tracking
GET    /api/auth/me                    # Get current user ✅
PATCH  /api/auth/update-profile        # Update profile
PATCH  /api/auth/update-pseudonym      # Change pseudonym
POST   /api/auth/send-verification     # Send verification email
GET    /api/auth/verify-email/{token}  # Verify email
POST   /api/auth/forgot-password       # Request password reset
POST   /api/auth/reset-password        # Reset password
```

### Posts, Discovery & Search
```
POST   /api/posts                      # Create post
GET    /api/posts/feed                 # Personalised feed (followed + interest-based)
GET    /api/posts/discover             # Campus-wide discovery feed
GET    /api/posts/trending             # Trending posts
GET    /api/posts/@{username}          # User's public posts
GET    /api/posts/me                   # My public posts
GET    /api/posts/me/anonymous         # My anonymous posts
GET    /api/posts/zone/{zone_id}       # Zone feed
DELETE /api/posts/{post_id}            # Delete post (24h window)
GET    /api/search                     # Unified search
GET    /api/search/users               # Mention autocomplete
```

### Social, Messaging & Notifications
```
POST   /api/follow/@{username}         # Follow user
DELETE /api/unfollow/@{username}       # Unfollow
GET    /api/users/@{username}/followers
GET    /api/users/@{username}/following
GET    /api/users/me/friends           # Mutual follows
GET    /api/users/@{username}          # User profile
GET    /api/messages/conversations     # DM conversations
POST   /api/messages/conversations     # Create/reuse DM conversation
GET    /api/messages/conversations/{id}    # Fetch messages in thread
POST   /api/messages/conversations/{id}    # Send text message
POST   /api/messages/conversations/{id}/audio  # Send voice message
POST   /api/messages/conversations/{id}/media  # Send image or video
PATCH  /api/messages/conversations/{id}/read   # Mark conversation read
GET    /api/messages/unread-count      # Unread count
GET    /api/notifications              # List notifications
PATCH  /api/notifications/{id}         # Mark notification read
DELETE /api/notifications/{id}         # Delete notification
```

### Reactions, Comments & Moderation
```
POST   /api/posts/{post_id}/react      # Add emoji reaction
DELETE /api/posts/{post_id}/react      # Remove reaction
GET    /api/posts/{post_id}/reactions  # Get reaction counts
POST   /api/posts/{post_id}/comments   # Add comment
GET    /api/posts/{post_id}/comments   # List comments
POST   /api/reports                    # Report post/comment/user
GET    /api/admin/reports              # Moderation queue
PATCH  /api/admin/reports/{id}         # Admin moderation action
GET    /api/admin/flagged              # Auto-flagged content
```

### Analytics, Zones & Infra
```
GET    /api/analytics/daily?date=YYYY-MM-DD&zone_id=X
GET    /api/analytics/weekly?week_start=YYYY-MM-DD&zone_id=X
GET    /api/analytics/campus?date=YYYY-MM-DD
GET    /api/zones/trending             # Most active zones
POST   /api/push/subscribe             # Register push subscription
DELETE /api/push/subscribe/{id}        # Deactivate push subscription
```

**Note:** The backend now spans auth, privacy, social, messaging, moderation, search, analytics, caching, and optional background-job infrastructure. See backend docs for the complete API surface.

---

## 🔐 SECURITY FEATURES

### Authentication & Authorization
- ✅ JWT tokens with 24-hour expiration
- ✅ bcrypt password hashing (cost factor 12)
- ✅ @ulaval.ca email validation
- ✅ Email verification for new accounts
- ⏸️ Université Laval OIDC / Entra integration (implemented, disabled pending university access)
- ✅ Secure password reset flow
- ✅ Optional 2FA (TOTP)
- ✅ Session management and tracking
- ✅ Admin authorization for moderation routes

### Privacy Protection
- ✅ Anonymous posting with persistent pseudonyms
- ✅ User ID never exposed for anonymous posts
- ✅ Reaction privacy (only aggregates shown)
- ✅ Privacy threshold (≥10 posts) for analytics
- ✅ Profile visibility controls
- ✅ Account deactivation
- ✅ Search privacy filters for anonymous/private/deactivated content

### Data Protection
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS protection (input sanitization)
- ✅ CORS configuration
- ✅ File upload restrictions
- ✅ Rate limiting
- ✅ Security audit logs
- ✅ Moderation action logging
- ✅ Optional Redis-backed background jobs

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

**Backend Status:** Phase 6 backend regression suites passing

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
- **[backend/documentation/Phases/INITIAL_PHASES_TRACKER.md](backend/documentation/Phases/INITIAL_PHASES_TRACKER.md)** - Phases 1-4 history
- **[backend/documentation/PHASE_6_OVERVIEW.md](backend/documentation/PHASE_6_OVERVIEW.md)** - Phase 6 roadmap and completion tracker

### Phase Documentation
- **[backend/documentation/Phases/PHASE_1_OVERVIEW.md](backend/documentation/Phases/PHASE_1_OVERVIEW.md)** - Foundation (Complete)
- **[backend/documentation/Phases/PHASE_2_OVERVIEW.md](backend/documentation/Phases/PHASE_2_OVERVIEW.md)** - Posts & NLP (Complete)
- **[backend/documentation/Phases/PHASE_3_OVERVIEW.md](backend/documentation/Phases/PHASE_3_OVERVIEW.md)** - Social Features (Complete)
- **[backend/documentation/Phases/PHASE_4_OVERVIEW.md](backend/documentation/Phases/PHASE_4_OVERVIEW.md)** - Analytics (Complete)
- **[backend/documentation/Phases/PHASE_5_OVERVIEW.md](backend/documentation/Phases/PHASE_5_OVERVIEW.md)** - Production Auth & UX
- **[backend/documentation/PHASE_6_OVERVIEW.md](backend/documentation/PHASE_6_OVERVIEW.md)** - Scale, search, moderation, messaging, infra

### Technical Guides
- **[backend/documentation/Technical/BILINGUAL_GUIDE.md](backend/documentation/Technical/BILINGUAL_GUIDE.md)** - Bilingual NLP implementation
- **[backend/documentation/Technical/EMOJI_COLLATION_BUG.md](backend/documentation/Technical/EMOJI_COLLATION_BUG.md)** - Critical bug fix documentation
- **[backend/documentation/Technical/MIGRATION_GUIDE.md](backend/documentation/Technical/MIGRATION_GUIDE.md)** - Migration runbook
- **[backend/documentation/Technical/SEARCH_API_GUIDE.md](backend/documentation/Technical/SEARCH_API_GUIDE.md)** - Unified search behavior
- **[backend/documentation/Technical/MESSAGING_GUIDE.md](backend/documentation/Technical/MESSAGING_GUIDE.md)** - Direct messaging system
- **[backend/documentation/Technical/MODERATION_GUIDE.md](backend/documentation/Technical/MODERATION_GUIDE.md)** - Reporting and admin workflow
- **[backend/documentation/Technical/RATE_LIMITING_GUIDE.md](backend/documentation/Technical/RATE_LIMITING_GUIDE.md)** - Abuse prevention and Redis notes
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
- ✅ **Phase 5:** Production Auth & UX
- ✅ **Phase 6:** Search, moderation, messaging, push, caching, background jobs

**Current Backend State:**
- unified search across posts, users, and zones
- discovery and trending feeds
- moderation/reporting pipeline with admin actions
- direct messaging and unread tracking
- push subscription infrastructure
- response caching and optional Redis/RQ background jobs

### Frontend Progress

| Component | Status | Notes |
|-----------|--------|-------|
| Auth (login / register / reset) | ✅ Complete | JWT, @ulaval.ca validation, 2FA |
| Email verification | ✅ Complete | Banner + intercept for unverified users |
| Feed | ✅ Complete | Interest-based blending, infinite scroll, emoji picker popup, mobile drawer |
| Post Composer | ✅ Complete | Zone picker, anon toggle, image upload |
| Reactions | ✅ Complete | `+` trigger → animated emoji popup |
| Comments | ✅ Complete | Threaded display, @mention autocomplete |
| Profile Page | ✅ Complete | Public/own view, follow, edit, pinned post |
| Settings | ✅ Complete | Profile, preferences, pseudonym, security, 2FA |
| Direct Messages | ✅ Complete | Text, images, videos, voice messages, smooth polling |
| Notifications | ✅ Complete | Instagram-style, grouped, type icons, mark read |
| Analytics Dashboard | ✅ Complete | Charts, zone breakdown, privacy threshold |
| Search / Discovery | ✅ Complete | Unified search, discovery feed, trending zones |

**Overall Progress:** ~100%

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
DB_HOST=localhost
DB_PORT=3306
DB_USER=pulse_user
DB_PASSWORD=***
DB_NAME=pulse_db
JWT_SECRET_KEY=***
FRONTEND_URL=http://127.0.0.1:8000
SMTP_HOST=smtp.gmail.com
SMTP_FROM=Pulse <pulse.ulaval@gmail.com>
REDIS_URL=redis://localhost:6379/0
BACKGROUND_JOBS_ENABLED=false

# Frontend (hardcoded in auth.js)
BACKEND_URL=http://127.0.0.1:5000
# Production backend
BACKEND_URL=https://pulse-backend.up.railway.app
JWT_STORAGE_KEY=pulse_token
```

---

## 🚀 DEPLOYMENT

### Production Checklist

**Backend:**
- [ ] HTTPS enabled
- [ ] Environment variables secured
- [ ] SMTP server configured
- [ ] Redis configured if using background jobs or shared rate-limit storage
- [ ] OIDC app credentials obtained (only needed when re-enabling institutional login)
- [ ] File upload directory configured
- [ ] Database backups scheduled
- [ ] Rate limiting enabled
- [ ] Background worker running if Redis-backed jobs are enabled
- [ ] Logging configured
- [ ] Backend regression suites passing

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

**Current deployed backend:** `https://pulse-backend.up.railway.app/`

---

## 👥 TEAM

**Backend Developer:** Full-stack focus (Python, Flask, MySQL, NLP)  
**Frontend Developer (Principessa):** UI/UX focus (HTML, CSS, JavaScript, API integration)  
**University IT:** OIDC / Entra integration support (future re-enable)

---

## 🐛 KNOWN ISSUES

### Backend
- ✅ Phase 6 backend systems implemented
- ✅ Email verification and password reset active
- ✅ Search, moderation, messaging, push, caching, and background jobs available
- ⏸️ OIDC/Entra remains feature-flagged off until university rollout

### Frontend
- ✅ All pages fully implemented and wired to backend
- ✅ Bilingual (FR/EN) throughout
- ⏸️ Token refresh not implemented — users re-login after 24 h expiration

### Integration
- ✅ CORS working between frontend and backend
- ✅ JWT authentication working end-to-end
- ⏸️ OIDC/Entra feature-flagged off until university rollout

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
- Production API Base: https://pulse-backend.up.railway.app/
- Production Health Check: https://pulse-backend.up.railway.app/api/auth/me

**Documentation:**
- Frontend Guide: [Frontend/QUICKSTART.md](Frontend/QUICKSTART.md)
- Backend Guide: [backend/QUICKSTART.md](backend/QUICKSTART.md)
- Phase 6 Overview: [backend/documentation/PHASE_6_OVERVIEW.md](backend/documentation/PHASE_6_OVERVIEW.md)

---

**Last Updated:** 2026-04-07  
**Backend Status:** Phase 6 Complete  
**Frontend Status:** All phases complete (~100%)  
**Repository:** [github.com/mo-dev-x/pulse](https://github.com/mo-dev-x/pulse)

---

## 🎉 MILESTONE ACHIEVEMENTS

**April 2026:**
- ✅ Interest-based home feed (followed posts + interest signals from reactions/zones)
- ✅ Anonymous pseudonym management added to Settings (90-day cooldown, live UI)
- ✅ Voice messages + image/video messages in DMs
- ✅ Smooth DM polling (no more flash — DOM updates only on new messages)
- ✅ Instagram-style notifications (grouped, type icons, mark-read, delete)
- ✅ Emoji reaction popup (+ trigger → animated picker)
- ✅ Mobile hamburger drawer for navigation
- ✅ Email notifications wired end-to-end (Brevo, bilingual, on by default)
- ✅ Email verification banner + intercept on feed for unverified accounts

**March 2026:**
- ✅ Backend Phases 1-6 complete
- ✅ Frontend all phases complete (auth, feed, profile, DMs, notifications, settings, analytics, search)
- ✅ JWT authentication working end-to-end
- ✅ Search, moderation, messaging, push, caching, and background jobs added
- ✅ Architecture docs and technical guides updated

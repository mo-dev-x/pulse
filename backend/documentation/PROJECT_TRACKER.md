# 🎯 PULSE BACKEND — PROJECT TRACKER

**Last Updated:** 2026-02-14  
**University:** Université Laval  
**Project:** Pulse Backend (Privacy-First Campus Wellness Platform)  
**Tech Stack:** Python 3.12.3 + Flask + MySQL + CAS  
**Languages:** Bilingual (French/English)  
**Email Domain:** @ulaval.ca (Verified)

---

## 📊 PROJECT STATUS OVERVIEW

| Phase | Status | Completion | Tests |
|-------|--------|------------|-------|
| **Phase 1: Foundation** | ✅ Complete | 100% | 7/7 ✅ |
| **Phase 2: Posts & NLP** | ✅ Complete | 100% | 8/8 ✅ |
| **Phase 3: Social Features** | ✅ Complete | 100% | 26/26 ✅ |
| **Phase 4: Analytics** | ✅ Complete | 100% | 30/30 ✅ |
| **Phase 5: Production Auth & UX** | 🚧 In Progress | 0% | 0/50 |

**Overall Progress (Phases 1-4):** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100%  
**Phase 5 Progress:** 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 0%

---

## 🚀 PHASE 5: PRODUCTION AUTHENTICATION & USER EXPERIENCE

**Timeline:** 10-14 days  
**Priority:** High - Production Readiness  
**Status:** Planning Complete, Ready to Start

### **Phase 5A: Must Have (Priority 1) — 5 days**

#### 🔐 Authentication Security
- [ ] **Email Verification System**
  - [ ] `verification_token`, `verification_expires` fields in User model
  - [ ] Email service with SMTP integration (`app/services/email_service.py`)
  - [ ] `POST /api/auth/send-verification` — Resend verification email
  - [ ] `GET /api/auth/verify-email/{token}` — Verify email with token
  - [ ] Bilingual email templates (FR/EN)
  - [ ] Middleware: `@require_verification` decorator
  - [ ] Tests: Email sending, token validation, expiration
  
- [ ] **Université Laval CAS Integration**
  - [ ] Install `python-cas` library
  - [ ] CAS client configuration
  - [ ] `GET /api/auth/cas/login` — Redirect to CAS
  - [ ] `GET /api/auth/cas/callback` — Handle CAS response
  - [ ] User fields: `cas_username`, `account_type`, `is_verified`
  - [ ] Auto-create users from CAS attributes
  - [ ] Migration strategy for existing users
  - [ ] Tests: CAS flow, user creation, attribute mapping
  
- [ ] **Password Reset Flow**
  - [ ] User fields: `reset_token`, `reset_expires`
  - [ ] `POST /api/auth/forgot-password` — Request reset
  - [ ] `POST /api/auth/reset-password` — Reset with token
  - [ ] Password reset email template (bilingual)
  - [ ] Token expiration (1 hour)
  - [ ] Security: Always return success (don't reveal if email exists)
  - [ ] Tests: Token generation, expiration, password validation

#### 👤 Profile Customization
- [ ] **Basic Profile Features**
  - [ ] User fields: `bio`, `profile_picture`, `header_image`, `website`, `location`
  - [ ] `PATCH /api/auth/update-bio` — Update bio (max 500 chars)
  - [ ] `POST /api/auth/upload-profile-pic` — Upload profile picture
  - [ ] `POST /api/auth/upload-header` — Upload header image
  - [ ] File upload directory structure: `/uploads/profiles/`, `/uploads/headers/`
  - [ ] Image validation: types (jpg, png, gif, webp), size (5MB max)
  - [ ] Image optimization with Pillow (resize to 500x500 for profiles)
  - [ ] Tests: Upload validation, size limits, image optimization

#### 💬 Comment System
- [ ] **Comment Model & Routes**
  - [ ] Comment model (`app/models/comment.py`)
    - Fields: `content`, `post_id`, `user_id`, `parent_id`, `is_anonymous`
    - Threading support (parent_id for replies)
    - Cascade delete with posts
  - [ ] `POST /api/posts/{post_id}/comments` — Add comment
  - [ ] `GET /api/posts/{post_id}/comments` — List comments (paginated)
  - [ ] `GET /api/comments/{comment_id}/replies` — Get replies
  - [ ] `PATCH /api/comments/{comment_id}` — Edit (5 min window)
  - [ ] `DELETE /api/comments/{comment_id}` — Delete comment
  - [ ] Privacy: Anonymous comments hide user_id
  - [ ] Validation: 1-500 characters
  - [ ] Tests: Create, edit, delete, threading, anonymity

---

### **Phase 5B: Should Have (Priority 2) — 3 days**

#### 🔔 Notification System
- [ ] **Notification Model & Service**
  - [ ] Notification model (`app/models/notification.py`)
    - Types: new_follower, new_comment, comment_reply, post_reaction, mention, system
    - Fields: `user_id`, `type`, `title`, `message`, `related_type`, `related_id`, `actor_id`
  - [ ] Notification service (`app/services/notification_service.py`)
  - [ ] `GET /api/notifications` — List notifications
  - [ ] `PATCH /api/notifications/{id}/read` — Mark as read
  - [ ] `PATCH /api/notifications/read-all` — Mark all as read
  - [ ] `DELETE /api/notifications/{id}` — Delete notification
  - [ ] Auto-create notifications on follow, comment, reaction
  - [ ] Tests: Notification creation, marking read, deletion

#### 🔒 Session Management
- [ ] **Session Tracking**
  - [ ] Session model (`app/models/session.py`)
    - Fields: `user_id`, `token_jti`, `ip_address`, `user_agent`, `device_type`
  - [ ] `GET /api/auth/sessions` — List active sessions
  - [ ] `DELETE /api/auth/sessions/{id}` — Revoke session
  - [ ] `DELETE /api/auth/sessions/all` — Revoke all (except current)
  - [ ] Track on login/logout
  - [ ] Tests: Session creation, revocation, listing

#### @️⃣ Mentions & Bookmarks
- [ ] **@Mentions System**
  - [ ] Extract mentions from post/comment content (`@username`)
  - [ ] Create notification when mentioned
  - [ ] Link to mentioned users
  - [ ] Tests: Mention extraction, notification creation
  
- [ ] **Bookmarks**
  - [ ] Bookmark model (`app/models/bookmark.py`)
  - [ ] `POST /api/posts/{post_id}/bookmark` — Bookmark post
  - [ ] `DELETE /api/posts/{post_id}/bookmark` — Remove bookmark
  - [ ] `GET /api/bookmarks` — List bookmarked posts
  - [ ] Tests: Bookmark, unbookmark, list

---

### **Phase 5C: Nice to Have (Priority 3) — 2 days**

#### 🔐 Advanced Security
- [ ] **Two-Factor Authentication (2FA)**
  - [ ] Install `pyotp`, `qrcode` libraries
  - [ ] User fields: `totp_secret`, `totp_enabled`, `backup_codes`
  - [ ] `POST /api/auth/2fa/enable` — Enable 2FA
  - [ ] `POST /api/auth/2fa/verify` — Verify 2FA code
  - [ ] `POST /api/auth/2fa/disable` — Disable 2FA
  - [ ] `GET /api/auth/2fa/backup-codes` — Generate backup codes
  - [ ] QR code generation
  - [ ] Tests: 2FA enable/disable, code verification
  
- [ ] **Security Logs**
  - [ ] SecurityLog model (`app/models/security_log.py`)
    - Events: login_success, login_failed, password_change, 2fa_enabled, etc.
  - [ ] Log security events automatically
  - [ ] Tests: Log creation, event types

#### ⭐ UX Enhancements
- [ ] **Privacy Settings**
  - [ ] User fields: `profile_visibility`, `show_email`
  - [ ] `PATCH /api/auth/privacy-settings` — Update privacy
  - [ ] Enforce visibility in profile queries
  - [ ] Tests: Privacy enforcement
  
- [ ] **User Preferences**
  - [ ] User fields: `theme`, `email_notifications`, `push_notifications`
  - [ ] `PATCH /api/auth/preferences` — Update preferences
  - [ ] Tests: Preference updates
  
- [ ] **Post Pinning**
  - [ ] User field: `pinned_post_id`
  - [ ] Show pinned post on profile
  - [ ] Tests: Pin/unpin functionality
  
- [ ] **Account Deactivation**
  - [ ] User fields: `is_deactivated`, `deactivated_at`
  - [ ] `POST /api/auth/deactivate` — Deactivate account
  - [ ] `POST /api/auth/reactivate` — Reactivate account
  - [ ] Hide deactivated users from feeds
  - [ ] Tests: Deactivation/reactivation

---

## 📋 TASK BREAKDOWN

### **Database Schema Updates**

#### New Tables (5):
- [ ] `comments` — Post comments with threading
- [ ] `notifications` — User notifications
- [ ] `sessions` — Active user sessions
- [ ] `security_logs` — Security event audit trail
- [ ] `bookmarks` — Saved posts

#### Updated Tables:
- [ ] **users** — Add 20+ new fields:
  - Email verification: `is_verified`, `verification_token`, `verification_expires`
  - Password reset: `reset_token`, `reset_expires`
  - CAS: `cas_username`, `account_type`
  - Profile: `bio`, `header_image`, `website`, `location`
  - Privacy: `profile_visibility`, `show_email`
  - Preferences: `theme`, `email_notifications`, `push_notifications`
  - 2FA: `totp_secret`, `totp_enabled`, `backup_codes`
  - Status: `is_deactivated`, `deactivated_at`, `pinned_post_id`

---

### **New Services (3)**

- [ ] **Email Service** (`app/services/email_service.py`)
  - Send verification emails
  - Send password reset emails
  - Send notification emails
  - Bilingual templates
  - SMTP configuration

- [ ] **Notification Service** (`app/services/notification_service.py`)
  - Create notifications
  - Send push notifications (optional)
  - Batch notification creation

- [ ] **Session Service** (`app/services/session_service.py`)
  - Track sessions
  - Validate sessions
  - Revoke sessions

---

### **New Routes (~30 endpoints)**

**Authentication (8):**
- [ ] `POST /api/auth/send-verification`
- [ ] `GET /api/auth/verify-email/{token}`
- [ ] `GET /api/auth/cas/login`
- [ ] `GET /api/auth/cas/callback`
- [ ] `POST /api/auth/forgot-password`
- [ ] `POST /api/auth/reset-password`
- [ ] `POST /api/auth/deactivate`
- [ ] `POST /api/auth/reactivate`

**Profile (5):**
- [ ] `PATCH /api/auth/update-bio`
- [ ] `POST /api/auth/upload-profile-pic`
- [ ] `POST /api/auth/upload-header`
- [ ] `PATCH /api/auth/privacy-settings`
- [ ] `PATCH /api/auth/preferences`

**Comments (5):**
- [ ] `POST /api/posts/{post_id}/comments`
- [ ] `GET /api/posts/{post_id}/comments`
- [ ] `GET /api/comments/{comment_id}/replies`
- [ ] `PATCH /api/comments/{comment_id}`
- [ ] `DELETE /api/comments/{comment_id}`

**Notifications (4):**
- [ ] `GET /api/notifications`
- [ ] `PATCH /api/notifications/{id}/read`
- [ ] `PATCH /api/notifications/read-all`
- [ ] `DELETE /api/notifications/{id}`

**Sessions (3):**
- [ ] `GET /api/auth/sessions`
- [ ] `DELETE /api/auth/sessions/{id}`
- [ ] `DELETE /api/auth/sessions/all`

**Bookmarks (3):**
- [ ] `POST /api/posts/{post_id}/bookmark`
- [ ] `DELETE /api/posts/{post_id}/bookmark`
- [ ] `GET /api/bookmarks`

**2FA (4):**
- [ ] `POST /api/auth/2fa/enable`
- [ ] `POST /api/auth/2fa/verify`
- [ ] `POST /api/auth/2fa/disable`
- [ ] `GET /api/auth/2fa/backup-codes`

---

## 🧪 TESTING REQUIREMENTS

### **Test Suites to Create:**

- [ ] `test_email_verification.py` (~10 tests)
  - Email sending
  - Token validation
  - Token expiration
  - Resend verification
  - Verification enforcement

- [ ] `test_cas_integration.py` (~8 tests)
  - CAS login redirect
  - CAS callback handling
  - User creation from CAS
  - Attribute mapping
  - Error handling

- [ ] `test_password_reset.py` (~8 tests)
  - Reset request
  - Token generation
  - Token expiration
  - Password update
  - Security (no email enumeration)

- [ ] `test_profile_customization.py` (~10 tests)
  - Bio update
  - Profile picture upload
  - Header upload
  - Image validation
  - Size limits

- [ ] `test_comments.py` (~15 tests)
  - Create comment
  - List comments
  - Threading/replies
  - Edit comment
  - Delete comment
  - Anonymous comments
  - Validation

- [ ] `test_notifications.py` (~10 tests)
  - Notification creation
  - List notifications
  - Mark as read
  - Delete notification
  - Auto-creation on events

- [ ] `test_sessions.py` (~8 tests)
  - Session creation
  - Session listing
  - Session revocation
  - Device tracking

- [ ] `test_bookmarks.py` (~5 tests)
  - Bookmark post
  - Remove bookmark
  - List bookmarks

- [ ] `test_2fa.py` (~10 tests)
  - Enable 2FA
  - Verify code
  - Backup codes
  - Disable 2FA
  - Login with 2FA

**Target:** 50+ tests for Phase 5

---

## 📦 DEPENDENCIES TO ADD

```python
# requirements.txt additions:
python-cas>=1.6.0           # CAS authentication
pyotp>=2.8.0               # TOTP for 2FA
qrcode>=7.4.2              # QR code generation
Pillow>=10.0.0             # Image processing
redis>=4.5.0               # Session management (optional)
```

---

## 🔧 INFRASTRUCTURE SETUP

### **Pre-Development:**
- [ ] Obtain CAS credentials from Université Laval IT
- [ ] Configure SMTP server (Gmail/SendGrid/University SMTP)
- [ ] Create file upload directories
- [ ] Install required Python packages
- [ ] Set up environment variables

### **Environment Variables:**
```bash
# CAS Configuration
CAS_SERVER_URL=https://cas.ulaval.ca/cas/
CAS_SERVICE_URL=https://pulse.ulaval.ca/auth/callback

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@pulse.ulaval.ca
SMTP_PASSWORD=***

# File Upload
UPLOAD_DIR=/var/www/pulse/uploads
MAX_FILE_SIZE=5242880  # 5MB

# Security
JWT_SECRET_KEY=***
FRONTEND_URL=https://pulse.ulaval.ca
```

---

## 📊 CURRENT METRICS (Post Phase 4)

| Metric | Value |
|--------|-------|
| **Total Endpoints** | 25 |
| **Models** | 8 |
| **Database Tables** | 9 |
| **Services** | 2 (NLP, Aggregation) |
| **Tests** | 71/71 ✅ |
| **Documentation** | 12 files |

---

## 📊 TARGET METRICS (Post Phase 5)

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| **Total Endpoints** | 25 | ~55 | +30 |
| **Models** | 8 | 13 | +5 |
| **Database Tables** | 9 | 14 | +5 |
| **Services** | 2 | 5 | +3 |
| **Tests** | 71 | 120+ | +50 |
| **User Fields** | 15 | 35+ | +20 |

---

## 🛠 KNOWN ISSUES

**Resolved (Phases 1-4):**
- ✅ JWT identity type mismatch — Fixed Phase 1
- ✅ CampusZone column name mismatch — Fixed Phase 2
- ✅ Missing `updated_at` column — Fixed Phase 2
- ✅ Emoji collation bug — Fixed Phase 3 (see `EMOJI_COLLATION_BUG.md`)
- ✅ Analytics response structure — Fixed Phase 4

**Current (Phase 5):**
- None (Phase 5 not started)

**Anticipated Challenges:**
- ⚠️ CAS integration complexity
- ⚠️ Email deliverability (SMTP configuration)
- ⚠️ File upload security
- ⚠️ Image optimization performance
- ⚠️ Migration strategy for existing users

---

## 📚 DOCUMENTATION

### **Existing Documentation:**
| Document | Purpose |
|----------|---------|
| `README.md` | Project overview, API reference |
| `QUICKSTART.md` | Setup guide, first run |
| `ARCHITECTURE_DECISIONS.md` | Technical decisions (AD-001 to AD-023) |
| `PHASE_5_OVERVIEW.md` | Phase 5 planning & features |


### **Documentation to Create:**
- [ ] `CAS_INTEGRATION_GUIDE.md` — CAS setup instructions
- [ ] `EMAIL_SERVICE_GUIDE.md` — SMTP configuration
- [ ] `2FA_USER_GUIDE.md` — How to enable/use 2FA
- [ ] `FILE_UPLOAD_GUIDE.md` — File handling best practices
- [ ] `MIGRATION_GUIDE.md` — Existing user migration
- [ ] Updated `ARCHITECTURE_DECISIONS.md` — AD-024 to AD-035

---

## 🚀 DEPLOYMENT CHECKLIST

### **Phase 5 Deployment Requirements:**

**Infrastructure:**
- [ ] HTTPS enabled (required for CAS)
- [ ] SMTP server configured
- [ ] File upload directory with proper permissions
- [ ] Image processing libraries installed
- [ ] CAS credentials configured
- [ ] Redis installed (optional, for sessions)
- [ ] Backup strategy for uploaded files

**Security:**
- [ ] Environment variables secured
- [ ] File upload restrictions enforced
- [ ] Rate limiting on authentication endpoints
- [ ] CORS settings updated for CAS callback
- [ ] Session secret rotation policy

**Testing:**
- [ ] All 50+ Phase 5 tests passing
- [ ] CAS flow tested end-to-end
- [ ] Email delivery confirmed
- [ ] File uploads working
- [ ] Image optimization verified
- [ ] 2FA tested with multiple apps

**Documentation:**
- [ ] API docs updated
- [ ] CAS integration guide complete
- [ ] Email service guide complete
- [ ] Migration guide complete

---

## 📅 DEVELOPMENT TIMELINE

### **Week 1: Phase 5A (Must Have)**
**Days 1-2:** Email Verification
- Email service implementation
- Verification endpoints
- Email templates
- Testing

**Days 3-4:** CAS Integration
- CAS client setup
- Login/callback endpoints
- User creation logic
- Testing

**Day 5:** Password Reset & Profile Basics
- Reset flow implementation
- Basic profile endpoints
- Testing

### **Week 2: Phase 5B & 5C**
**Days 6-7:** Comment System
- Comment model
- CRUD endpoints
- Threading support
- Testing

**Days 8-9:** Notifications & Sessions
- Notification system
- Session tracking
- @Mentions
- Bookmarks
- Testing

**Days 10-12:** Advanced Features (Optional)
- 2FA implementation
- Security logs
- Privacy settings
- UX enhancements
- Comprehensive testing

**Days 13-14:** Buffer & Documentation
- Bug fixes
- Documentation
- Final testing
- Deployment preparation

---

## ✨ SUCCESS CRITERIA

**Phase 5 Complete When:**
- ✅ All Phase 5A features implemented and tested
- ✅ CAS integration working with Université Laval
- ✅ Email verification functional
- ✅ Password reset secure and working
- ✅ Profile customization available
- ✅ Comment system fully operational
- ✅ All tests passing (target: 120+ total)
- ✅ Documentation complete
- ✅ Security audit passed
- ✅ Ready for production deployment

---

## 📝 NOTES

**Development Philosophy:**
- Security first (CAS, 2FA, verified emails)
- Privacy always (anonymous comments, profile visibility)
- User experience matters (notifications, customization)
- Test everything (50+ new tests)
- Document thoroughly (guides for all features)

**Migration Strategy:**
- Phase 5A is backwards compatible
- Existing users can continue using password auth
- Gradual migration to CAS encouraged
- Email verification required for new features

**Team Coordination:**
- Backend: Focus on Phase 5A first
- Frontend: Start UI designs for new features
- DevOps: Prepare CAS credentials and SMTP
- University IT: Coordinate CAS integration

---

**📌 Remember:** Update this tracker daily during Phase 5 development!

**Last Achievement:** Phase 4 Complete — Analytics Operational 🎉  
**Current Milestone:** Phase 5 Started — Production Authentication 🚀  
**Next Milestone:** Phase 5A Complete — Core Security Features ✅

**Status:** 🟢 Ready to Start Phase 5A  
**Priority:** 🔴 High — Production Readiness  
**Timeline:** 📅 10-14 days estimated
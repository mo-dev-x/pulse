# 🎯 PULSE BACKEND — PROJECT TRACKER

**Last Updated:** 2026-02-17  
**University:** Université Laval  
**Project:** Pulse Backend (Privacy-First Campus Wellness Platform)  
**Tech Stack:** Python 3.12.3 + Flask + MySQL + OIDC (Azure Entra)  
**Languages:** Bilingual (French/English)  
**Email Domain:** @ulaval.ca (Verified)

---

## 📊 PROJECT STATUS OVERVIEW

**Current Focus:** Phase 5 - Production Authentication & User Experience

| Phase 5 Component | Status | Completion | Priority |
|-------------------|--------|------------|----------|
| **5A: Email Verification** | ✅ Implemented | 100% | Must Have |
| **5A: OIDC/Entra Integration** | ⏸️ Implemented but Paused | 100% | Must Have |
| **5A: Password Reset** | ✅ Implemented | 100% | Must Have |
| **5A: Profile Customization** | ✅ Implemented | 100% | Must Have |
| **5A: Comment System** | ✅ Implemented | 100% | Must Have |
| **5B: Notifications** | ✅ Implemented | 100% | Should Have |
| **5B: Session Management** | ✅ Implemented | 100% | Should Have |
| **5B: Mentions & Bookmarks** | ✅ Implemented | 100% | Should Have |
| **5C: 2FA & Security** | ✅ Implemented | 100% | Nice to Have |
| **5C: UX Enhancements** | ✅ Implemented | 100% | Nice to Have |

**Phase 5A Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% (Must Have - 5 days)  
**Phase 5B Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% (Should Have - 3 days)  
**Phase 5C Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% (Nice to Have - 2 days)

**Overall Phase 5 Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% / 100%

### Auth Direction Update (2026-02-16)
- Active path remains: `register/login + email verification`.
- Institutional OIDC routes are preserved but disabled by default with `ENABLE_OIDC_AUTH=false`.
- Re-enable instructions are documented in `backend/documentation/Technical/OIDC_REENABLE_PLAYBOOK.md`.

---

## 📝 FOUNDATION STATUS (Phases 1-4)

All foundational phases complete. See [INITIAL_PHASES_TRACKER.md](INITIAL_PHASES_TRACKER.md) for details.

- ✅ **Phase 1:** Foundation (7/7 tests)
- ✅ **Phase 2:** Posts & NLP (8/8 tests)
- ✅ **Phase 3:** Social Features (26/26 tests)
- ✅ **Phase 4:** Analytics (30/30 tests)

**Foundation Status:** 71/71 tests passing ✅

---

## 🗺️ PHASE 5 DETAILED PLANNING

### **Overview**
Phase 5 transforms Pulse into a production-ready platform with enterprise-grade authentication, enhanced user experience, and comprehensive security features.

**Timeline:** 10-14 days  
**Approach:** Iterative development with testing at each step  
**Priority:** Security first, then UX

---

## 📋 PHASE 5A: MUST HAVE FEATURES (Days 1-5)

### **Component 1: Email Verification System**
**Timeline:** Days 1-2 (2 days)  
**Priority:** Critical - Security Foundation

#### Planning Steps:

**Day 1 - Database & Service Setup:**
1. **Morning: Database Schema**
   - Add fields to User model:
     - `is_verified` (Boolean, default False)
     - `verification_token` (String 255)
     - `verification_expires` (DateTime)
   - Create migration script
   - Test schema changes

2. **Afternoon: Email Service**
   - Create `app/services/email_service.py`
   - Implement SMTP configuration
   - Create bilingual email templates (FR/EN)
   - Test email sending locally

**Day 2 - Endpoints & Integration:**
3. **Morning: Verification Endpoints**
   - `POST /api/auth/send-verification`
     - Generate secure token (secrets.token_urlsafe)
     - Store token with 24h expiration
     - Send bilingual email
     - Return success (no email enumeration)
   
   - `GET /api/auth/verify-email/{token}`
     - Validate token exists
     - Check expiration
     - Mark user as verified
     - Clear token
     - Return success/error

4. **Afternoon: Middleware & Testing**
   - Create `@require_verification` decorator
   - Apply to sensitive endpoints (posts, comments)
   - Write tests (10 test cases)
   - Integration testing

#### Architectural Decisions:

**AD-024: Token-Based Email Verification**
- **Decision:** Use cryptographically secure tokens (secrets.token_urlsafe)
- **Rationale:** More secure than UUID, URL-safe, 32 bytes = 256-bit security
- **Alternative Considered:** JWT tokens (rejected - overkill for single-use)
- **Implementation:** Store in database with expiration

**AD-025: 24-Hour Token Expiration**
- **Decision:** Verification tokens expire after 24 hours
- **Rationale:** Balance security and user convenience
- **Alternative Considered:** 1 hour (rejected - too short for email delivery)
- **Implementation:** Check expiration before accepting token

**AD-026: No Email Enumeration**
- **Decision:** Always return success when requesting verification
- **Rationale:** Prevents attackers from discovering valid emails
- **Alternative Considered:** Return error for invalid emails (rejected - security risk)
- **Implementation:** Send email only if user exists, always return 200

#### Deliverables:
- ✅ User model updated with verification fields
- ✅ Email service with SMTP integration
- ✅ Bilingual email templates
- ✅ 2 new endpoints
- ✅ Verification middleware
- ✅ 10 tests passing

---

### **Component 2: OIDC / Entra Integration (Paused by Feature Flag)**
**Timeline:** Days 3-4 (2 days)  
**Priority:** Critical - University Authentication

#### Planning Steps:

**Day 3 - OIDC Client Setup:**
1. **Morning: Dependencies & Configuration**
   - Install and verify OAuth/OIDC client support (`requests`)
   - Configure OIDC settings in config.py
   - Set up OIDC callback URL
   - Coordinate with University IT for credentials

2. **Afternoon: User Model Updates**
   - Add fields:
     - `cas_username` (String 50) - institutional external ID (legacy column name)
     - `account_type` (Enum: student/staff/faculty/alumni)
     - `is_verified` (auto-set to True for OIDC users)
   - Create migration script
   - Test schema changes

**Day 4 - OIDC Flow Implementation:**
3. **Morning: OIDC Login Endpoint**
   - `GET /api/auth/oidc/login`
     - Initialize OIDC authorization request
     - Generate state
     - Redirect to provider
     - Return redirect response

4. **Afternoon: OIDC Callback & Testing**
   - `GET /api/auth/oidc/callback`
     - Receive OAuth code
     - Exchange code at token endpoint
     - Extract user claims (email, external ID, displayName)
     - Create or update user in database
     - Generate JWT token
     - Return token + user info
   
   - Write tests (8 test cases)
   - Integration testing with provider sandbox

#### Architectural Decisions:

**AD-027: OIDC as Institutional Authentication**
- **Decision:** OIDC integration as institutional authentication method
- **Rationale:** Compatible with university SSO provider and standards-based flows
- **Alternative Considered:** Direct CAS client integration
- **Implementation:** Parallel with password auth during migration

**AD-028: Auto-Create Users from OIDC**
- **Decision:** Automatically create user accounts from OIDC claims
- **Rationale:** Seamless onboarding, no pre-registration needed
- **Alternative Considered:** Manual registration required (rejected - friction)
- **Implementation:** Check if user exists, create if not, always update attributes

**AD-029: External Identity Stored Separately**
- **Decision:** Store university IDUL separately from app username
- **Rationale:** IDUL is permanent, username can be customized
- **Alternative Considered:** Use IDUL as username (rejected - less friendly)
- **Implementation:** `cas_username` field stores IDUL, `username` is customizable

#### Deliverables:
- ✅ OIDC client flow integrated
- ✅ OIDC provider configuration supported
- ✅ User model with institutional identity fields
- ✅ 2 new endpoints (login, callback)
- ✅ Auto-create user logic
- ✅ 8 tests passing
- ✅ Feature flag (`ENABLE_OIDC_AUTH`) keeps implementation preserved but disabled by default

---

### **Component 3: Password Reset Flow**
**Timeline:** Day 5 Morning (0.5 days)  
**Priority:** High - User Support

#### Planning Steps:

**Day 5 Morning:**
1. **Database Schema**
   - Add fields:
     - `reset_token` (String 255)
     - `reset_expires` (DateTime)
   - Create migration

2. **Endpoints Implementation**
   - `POST /api/auth/forgot-password`
     - Validate email format
     - Find user (if exists)
     - Generate secure reset token
     - Store token with 1-hour expiration
     - Send reset email (bilingual)
     - Always return success
   
   - `POST /api/auth/reset-password`
     - Validate token
     - Check expiration
     - Validate new password strength
     - Hash and update password
     - Clear reset token
     - Return success

3. **Testing**
   - Write tests (8 test cases)
   - Test token expiration
   - Test security (no enumeration)

#### Architectural Decisions:

**AD-030: 1-Hour Reset Token Expiration**
- **Decision:** Reset tokens expire after 1 hour
- **Rationale:** Shorter window than verification (more sensitive)
- **Alternative Considered:** 24 hours (rejected - security risk)
- **Implementation:** Check expiration, clear after use

**AD-031: One-Time Use Tokens**
- **Decision:** Reset tokens are single-use, cleared after successful reset
- **Rationale:** Prevents replay attacks
- **Alternative Considered:** Multi-use tokens (rejected - security risk)
- **Implementation:** Clear token in database after password change

#### Deliverables:
- ✅ User model with reset fields
- ✅ 2 new endpoints
- ✅ Reset email template
- ✅ 8 tests passing

---

### **Component 4: Profile Customization**
**Timeline:** Day 5 Afternoon (0.5 days)  
**Priority:** High - User Experience

#### Planning Steps:

**Day 5 Afternoon:**
1. **Database Schema**
   - Add fields:
     - `bio` (Text, max 500 chars)
     - `profile_picture` (String 255, file path)
     - `header_image` (String 255, file path)
     - `website` (String 255)
     - `location` (String 100)
   - Create migration

2. **File Upload Setup**
   - Create `/uploads/profiles/` directory
   - Create `/uploads/headers/` directory
   - Configure upload limits (5MB)
   - Set up Pillow for image processing

3. **Endpoints**
   - `PATCH /api/auth/update-bio`
     - Validate length (max 500 chars)
     - Update bio field
     - Return updated user
   
   - `POST /api/auth/upload-profile-pic`
     - Validate file type (jpg, png, gif, webp)
     - Validate file size (5MB max)
     - Generate secure filename
     - Resize to 500x500 (Pillow)
     - Delete old picture
     - Save new picture
     - Update user record
     - Return image URL
   
   - `POST /api/auth/upload-header`
     - Similar to profile pic
     - Resize to 1500x500

4. **Testing**
   - Write tests (10 test cases)
   - Test file validation
   - Test image optimization

#### Architectural Decisions:

**AD-032: Server-Side Image Processing**
- **Decision:** Process images on server using Pillow
- **Rationale:** Consistent quality, prevents malicious uploads
- **Alternative Considered:** Client-side processing (rejected - inconsistent)
- **Implementation:** Resize, optimize, convert to standard format

**AD-033: Secure Filename Generation**
- **Decision:** Use user_id + random token for filenames
- **Rationale:** Prevents path traversal, ensures uniqueness
- **Alternative Considered:** Original filename (rejected - security risk)
- **Implementation:** `profile_{user_id}_{token}.{ext}`

**AD-034: 500-Character Bio Limit**
- **Decision:** Maximum 500 characters for bio
- **Rationale:** Encourages concise profiles, prevents abuse
- **Alternative Considered:** Unlimited (rejected - spam potential)
- **Implementation:** Validation in endpoint

#### Deliverables:
- ✅ User model with profile fields
- ✅ File upload system
- ✅ Image optimization (Pillow)
- ✅ 3 new endpoints
- ✅ 10 tests passing

---

### **Component 5: Comment System**
**Timeline:** Days 6-7 (2 days)  
**Priority:** High - User Engagement

#### Planning Steps:

**Day 6 - Model & Basic CRUD:**
1. **Morning: Database Schema**
   - Create Comment model:
     - `id` (Integer, PK)
     - `content` (Text, 1-500 chars)
     - `post_id` (FK to posts)
     - `user_id` (FK to users)
     - `parent_id` (FK to comments, nullable) - for threading
     - `is_anonymous` (Boolean)
     - `created_at` (DateTime)
     - `updated_at` (DateTime)
   - Add relationships
   - Create migration
   - Test schema

2. **Afternoon: Create & List Endpoints**
   - `POST /api/posts/{post_id}/comments`
     - Validate post exists
     - Validate content (1-500 chars)
     - Create comment
     - Return comment (privacy-aware)
   
   - `GET /api/posts/{post_id}/comments`
     - Query top-level comments (parent_id = NULL)
     - Paginate (20 per page)
     - Order by created_at DESC
     - Return comments (privacy-aware)

**Day 7 - Threading & Management:**
3. **Morning: Threading & Replies**
   - `GET /api/comments/{id}/replies`
     - Query comments with parent_id = {id}
     - Paginate
     - Return replies
   
   - Update create endpoint to accept parent_id

4. **Afternoon: Edit, Delete & Testing**
   - `PATCH /api/comments/{id}`
     - Validate ownership
     - Check 5-minute edit window
     - Update content
     - Update updated_at
     - Return updated comment
   
   - `DELETE /api/comments/{id}`
     - Validate ownership
     - Check if has replies (cascade or prevent?)
     - Delete comment
     - Return success
   
   - Write tests (15 test cases)
   - Test threading
   - Test privacy (anonymous)

#### Architectural Decisions:

**AD-035: 5-Minute Edit Window**
- **Decision:** Comments editable for 5 minutes after posting
- **Rationale:** Fix typos, prevent abuse (no context changes)
- **Alternative Considered:** No editing (rejected - user frustration)
- **Implementation:** Check `created_at` timestamp

**AD-036: Threaded Comments (1 Level)**
- **Decision:** Support one level of replies (comments → replies)
- **Rationale:** Simple, prevents deep nesting complexity
- **Alternative Considered:** Unlimited nesting (rejected - UI complexity)
- **Implementation:** `parent_id` field, UI shows 2 levels

**AD-037: Anonymous Comment Privacy**
- **Decision:** Same privacy rules as posts (show pseudonym, not user_id)
- **Rationale:** Consistency with existing privacy model
- **Alternative Considered:** Force public comments (rejected - reduces engagement)
- **Implementation:** Check `is_anonymous` in to_dict()

**AD-038: Comment Character Limit**
- **Decision:** 1-500 characters (same as posts)
- **Rationale:** Consistency, prevents spam
- **Alternative Considered:** Longer limit (rejected - encourage focused discussion)
- **Implementation:** Validation in endpoint

#### Deliverables:
- ✅ Comment model with threading
- ✅ 5 new endpoints
- ✅ Privacy-aware serialization
- ✅ Edit window enforcement
- ✅ 15 tests passing

---

## 📋 PHASE 5B: SHOULD HAVE FEATURES (Days 8-9)

### **Component 6: Notification System**
**Timeline:** Day 8 (1 day)  
**Priority:** Medium - User Engagement

#### Planning Steps:

**Day 8:**
1. **Morning: Models & Service**
   - Create Notification model
   - Create NotificationService
   - Implement auto-notification triggers

2. **Afternoon: Endpoints**
   - 4 notification endpoints
   - Write tests (10 test cases)

#### Architectural Decisions:

**AD-039: Real-Time vs Polling**
- **Decision:** Polling-based notifications (REST API)
- **Rationale:** Simpler implementation, WebSocket for Phase 6
- **Alternative Considered:** WebSocket (deferred to Phase 6)
- **Implementation:** Frontend polls every 30 seconds

**AD-040: Notification Types**
- **Decision:** 6 notification types (follower, comment, reply, reaction, mention, system)
- **Rationale:** Cover main user interactions
- **Alternative Considered:** More types (rejected - keep simple)
- **Implementation:** Enum in model

---

### **Component 7: Session Management**
**Timeline:** Day 8 Afternoon (0.5 days)  
**Priority:** Medium - Security

#### Planning Steps:

**Day 8 Afternoon:**
1. Create Session model
2. Track sessions on login
3. Implement revocation endpoints
4. Write tests (8 test cases)

#### Architectural Decisions:

**AD-041: Session Storage**
- **Decision:** Store sessions in database (not Redis yet)
- **Rationale:** Simpler for Phase 5, Redis in Phase 6
- **Alternative Considered:** Redis (deferred - no dependency)
- **Implementation:** Session model with JWT ID

---

### **Component 8: Mentions & Bookmarks**
**Timeline:** Day 9 (1 day)  
**Priority:** Medium - User Experience

#### Planning Steps:

**Day 9:**
1. **Morning: Mentions**
   - Extract @username from content
   - Create notifications
   - Write tests

2. **Afternoon: Bookmarks**
   - Create Bookmark model
   - Implement 3 endpoints
   - Write tests

#### Architectural Decisions:

**AD-042: Mention Pattern**
- **Decision:** Use regex `@(\w+)` to extract mentions
- **Rationale:** Simple, standard pattern
- **Alternative Considered:** Complex parser (rejected - overkill)
- **Implementation:** Extract in post/comment creation

**AD-043: Bookmark Privacy**
- **Decision:** Bookmarks are private, never shared
- **Rationale:** Personal collection, no social pressure
- **Alternative Considered:** Public bookmarks (rejected - privacy)
- **Implementation:** User-scoped queries only

---

## 📋 PHASE 5C: NICE TO HAVE FEATURES (Days 10-12)

### **Component 9: Two-Factor Authentication**
**Timeline:** Days 10-11 (2 days)  
**Priority:** Low - Optional Security

#### Planning Steps:

**Day 10:**
1. Install pyotp, qrcode
2. Add TOTP fields to User model
3. Implement enable/disable endpoints

**Day 11:**
1. QR code generation
2. Backup codes
3. Login flow with 2FA
4. Write tests (10 test cases)

#### Architectural Decisions:

**AD-044: TOTP-Based 2FA**
- **Decision:** Use TOTP (Time-based One-Time Password)
- **Rationale:** Standard, works with Google Authenticator
- **Alternative Considered:** SMS (rejected - cost, less secure)
- **Implementation:** pyotp library

**AD-045: Optional 2FA**
- **Decision:** 2FA is optional, user choice
- **Rationale:** Balance security and friction
- **Alternative Considered:** Mandatory (rejected - too restrictive)
- **Implementation:** Flag in user preferences

---

### **Component 10: UX Enhancements**
**Timeline:** Day 12 (1 day)  
**Priority:** Low - Polish

#### Planning Steps:

**Day 12:**
1. Privacy settings endpoints
2. User preferences endpoints
3. Account deactivation
4. Post pinning
5. Write tests

#### Architectural Decisions:

**AD-046: Profile Visibility Levels**
- **Decision:** 3 levels (public, followers, private)
- **Rationale:** Granular privacy control
- **Alternative Considered:** 2 levels (rejected - not enough control)
- **Implementation:** Enum in user model

---

## 🧪 TESTING STRATEGY

### Test-Driven Development Approach:
1. Write tests BEFORE implementing features
2. Run tests after each component
3. Integration tests after each phase
4. Cumulative regression testing

### Test Coverage Targets:
- Phase 5A: 46 tests
- Phase 5B: 18 tests  
- Phase 5C: 10 tests
- **Total Target: 50+ new tests**
- **Grand Total: 120+ tests**

---

## 🔄 DEVELOPMENT WORKFLOW

### Daily Workflow:
```
Morning:
  ├─ Review previous day
  ├─ Write tests for today's features
  ├─ Implement features
  └─ Run tests

Afternoon:
  ├─ Continue implementation
  ├─ Run integration tests
  ├─ Update documentation
  ├─ Commit changes
  └─ Plan next day
```

### Code Review Checkpoints:
- End of 5A (Day 5)
- End of 5B (Day 9)
- End of 5C (Day 12)

---

## 📊 PROGRESS TRACKING

### Daily Updates:
- Update checkboxes in PROJECT_TRACKER.md
- Update progress bars
- Document any blockers
- Adjust timeline if needed

### Weekly Review:
- Review completed components
- Test all features together
- Update documentation
- Plan adjustments

---

**Timeline:** 10-14 days  
**Priority:** High - Production Readiness  
**Status:** Implementation complete, moving to hardening

### **Phase 5A: Must Have (Priority 1) — 5 days**

#### 🔐 Authentication Security
- [x] **Email Verification System**
  - [x] `verification_token`, `verification_expires` fields in User model
  - [x] Email service with SMTP integration (`app/services/email_service.py`)
  - [x] `POST /api/auth/send-verification` — Resend verification email
  - [x] `GET /api/auth/verify-email/{token}` — Verify email with token
  - [x] Bilingual email templates (FR/EN)
  - [x] Middleware: `@require_verification` decorator
  - [x] Tests: Email sending, token validation, expiration
  
- [x] **Université Laval OIDC/Entra Integration (Paused by Flag)**
  - [x] OIDC client configuration
  - [x] `GET /api/auth/oidc/login` — Redirect to provider
  - [x] `GET /api/auth/oidc/callback` — Handle provider response
  - [x] `ENABLE_OIDC_AUTH` flag support (default `false`)
  - [x] User fields: `cas_username`, `account_type`, `is_verified`
  - [x] Auto-create users from OIDC claims
  - [x] Migration strategy for existing users
  - [x] Tests: OIDC flow, user creation, attribute mapping
  
- [x] **Password Reset Flow**
  - [x] User fields: `reset_token`, `reset_expires`
  - [x] `POST /api/auth/forgot-password` — Request reset
  - [x] `POST /api/auth/reset-password` — Reset with token
  - [x] Password reset email template (bilingual)
  - [x] Token expiration (1 hour)
  - [x] Security: Always return success (don't reveal if email exists)
  - [x] Tests: Token generation, expiration, password validation

#### 👤 Profile Customization
- [x] **Basic Profile Features**
  - [x] User fields: `bio`, `profile_picture`, `header_image`, `website`, `location`
  - [x] `PATCH /api/auth/update-bio` — Update bio (max 500 chars)
  - [x] `POST /api/auth/upload-profile-pic` — Upload profile picture
  - [x] `POST /api/auth/upload-header` — Upload header image
  - [x] File upload directory structure: `/uploads/profiles/`, `/uploads/headers/`
  - [x] Image validation: types (jpg, png, gif, webp), size (5MB max)
  - [x] Image optimization with Pillow (resize to 500x500 for profiles)
  - [x] Tests: Upload validation, size limits, image optimization

#### 💬 Comment System
- [x] **Comment Model & Routes**
  - [x] Comment model (`app/models/comment.py`)
    - Fields: `content`, `post_id`, `user_id`, `parent_id`, `is_anonymous`
    - Threading support (parent_id for replies)
    - Cascade delete with posts
  - [x] `POST /api/posts/{post_id}/comments` — Add comment
  - [x] `GET /api/posts/{post_id}/comments` — List comments (paginated)
  - [x] `GET /api/comments/{comment_id}/replies` — Get replies
  - [x] `PATCH /api/comments/{comment_id}` — Edit (5 min window)
  - [x] `DELETE /api/comments/{comment_id}` — Delete comment
  - [x] Privacy: Anonymous comments hide user_id
  - [x] Validation: 1-500 characters
  - [x] Tests: Create, edit, delete, threading, anonymity

---

### **Phase 5B: Should Have (Priority 2) — 3 days**

#### 🔔 Notification System
- [x] **Notification Model & Service**
  - [x] Notification model (`app/models/notification.py`)
    - Types: new_follower, new_comment, comment_reply, post_reaction, mention, system
    - Fields: `user_id`, `type`, `title`, `message`, `related_type`, `related_id`, `actor_id`
  - [x] Notification service (`app/services/notification_service.py`)
  - [x] `GET /api/notifications` — List notifications
  - [x] `PATCH /api/notifications/{id}/read` — Mark as read
  - [x] `PATCH /api/notifications/read-all` — Mark all as read
  - [x] `DELETE /api/notifications/{id}` — Delete notification
  - [x] Auto-create notifications on follow, comment, reaction
  - [x] Tests: Notification creation, marking read, deletion

#### 🔒 Session Management
- [x] **Session Tracking**
  - [x] Session model (`app/models/session.py`)
    - Fields: `user_id`, `token_jti`, `ip_address`, `user_agent`, `device_type`
  - [x] `GET /api/auth/sessions` — List active sessions
  - [x] `DELETE /api/auth/sessions/{id}` — Revoke session
  - [x] `DELETE /api/auth/sessions/all` — Revoke all (except current)
  - [x] Track on login/logout
  - [x] Tests: Session creation, revocation, listing

#### @️⃣ Mentions & Bookmarks
- [x] **@Mentions System**
  - [x] Extract mentions from post/comment content (`@username`)
  - [x] Create notification when mentioned
  - [x] Link to mentioned users
  - [x] Tests: Mention extraction, notification creation
  
- [x] **Bookmarks**
  - [x] Bookmark model (`app/models/bookmark.py`)
  - [x] `POST /api/posts/{post_id}/bookmark` — Bookmark post
  - [x] `DELETE /api/posts/{post_id}/bookmark` — Remove bookmark
  - [x] `GET /api/bookmarks` — List bookmarked posts
  - [x] Tests: Bookmark, unbookmark, list

---

### **Phase 5C: Nice to Have (Priority 3) — 2 days**

#### 🔐 Advanced Security
- [x] **Two-Factor Authentication (2FA)**
  - [x] TOTP setup/verification works without external OTP library
  - [x] Optional QR rendering when `qrcode` is installed
  - [x] User fields: `totp_secret`, `totp_enabled`, `backup_codes`
  - [x] `POST /api/auth/2fa/enable` — Enable 2FA
  - [x] `POST /api/auth/2fa/verify` — Verify 2FA code
  - [x] `POST /api/auth/2fa/disable` — Disable 2FA
  - [x] `GET /api/auth/2fa/backup-codes` — Generate backup codes
  - [x] QR code generation (best effort; returns `null` when `qrcode` is unavailable)
  - [x] Tests: 2FA enable/disable, code verification, login flow, security log events
  
- [x] **Security Logs**
  - [x] SecurityLog model (`app/models/security_log.py`)
    - Events: login_success, login_failed, password_change, 2fa_enabled, etc.
  - [x] Log security events automatically
  - [x] Tests: Log creation, event types

#### ⭐ UX Enhancements
- [x] **Privacy Settings**
  - [x] User fields: `profile_visibility`, `show_email`
  - [x] `PATCH /api/auth/privacy-settings` — Update privacy
  - [x] Enforce visibility in profile queries
  - [x] Tests: Privacy enforcement
  
- [x] **User Preferences**
  - [x] User fields: `theme`, `email_notifications`, `push_notifications`
  - [x] `PATCH /api/auth/preferences` — Update preferences
  - [x] Tests: Preference updates
  
- [x] **Post Pinning**
  - [x] User field: `pinned_post_id`
  - [x] Show pinned post on profile
  - [x] Tests: Pin/unpin functionality
  
- [x] **Account Deactivation**
  - [x] User fields: `is_deactivated`, `deactivated_at`
  - [x] `POST /api/auth/deactivate` — Deactivate account
  - [x] `POST /api/auth/reactivate` — Reactivate account
  - [x] Hide deactivated users from feeds
  - [x] Tests: Deactivation/reactivation

---

## 📋 TASK BREAKDOWN

### **Database Schema Updates**

#### New Tables (5):
- [x] `comments` — Post comments with threading
- [x] `notifications` — User notifications
- [x] `sessions` — Active user sessions
- [x] `security_logs` — Security event audit trail
- [x] `bookmarks` — Saved posts

#### Updated Tables:
- [x] **users** — Add 20+ new fields:
  - Email verification: `is_verified`, `verification_token`, `verification_expires`
  - Password reset: `reset_token`, `reset_expires`
  - Institutional identity: `cas_username`, `account_type`
  - Profile: `bio`, `header_image`, `website`, `location`
  - Privacy: `profile_visibility`, `show_email`
  - Preferences: `theme`, `email_notifications`, `push_notifications`
  - 2FA: `totp_secret`, `totp_enabled`, `backup_codes`
  - Status: `is_deactivated`, `deactivated_at`, `pinned_post_id`

---

### **New Services (3)**

- [x] **Email Service** (`app/services/email_service.py`)
  - Send verification emails
  - Send password reset emails
  - Send notification emails
  - Bilingual templates
  - SMTP configuration

- [x] **Notification Service** (`app/services/notification_service.py`)
  - Create notifications
  - Batch notification creation
  - Push delivery deferred to later infrastructure work

- [x] **Session Service** (`app/services/session_service.py`)
  - Track sessions
  - Validate sessions
  - Revoke sessions

---

### **New Routes (~30 endpoints)**

**Authentication (8):**
- [x] `POST /api/auth/send-verification`
- [x] `GET /api/auth/verify-email/{token}`
- [x] `GET /api/auth/oidc/login` (currently disabled by default via feature flag)
- [x] `GET /api/auth/oidc/callback` (currently disabled by default via feature flag)
- [x] `POST /api/auth/forgot-password`
- [x] `POST /api/auth/reset-password`
- [x] `POST /api/auth/deactivate`
- [x] `POST /api/auth/reactivate`

**Profile (5):**
- [x] `PATCH /api/auth/update-bio`
- [x] `POST /api/auth/upload-profile-pic`
- [x] `POST /api/auth/upload-header`
- [x] `PATCH /api/auth/privacy-settings`
- [x] `PATCH /api/auth/preferences`

**Comments (5):**
- [x] `POST /api/posts/{post_id}/comments`
- [x] `GET /api/posts/{post_id}/comments`
- [x] `GET /api/comments/{comment_id}/replies`
- [x] `PATCH /api/comments/{comment_id}`
- [x] `DELETE /api/comments/{comment_id}`

**Notifications (4):**
- [x] `GET /api/notifications`
- [x] `PATCH /api/notifications/{id}/read`
- [x] `PATCH /api/notifications/read-all`
- [x] `DELETE /api/notifications/{id}`

**Sessions (3):**
- [x] `GET /api/auth/sessions`
- [x] `DELETE /api/auth/sessions/{id}`
- [x] `DELETE /api/auth/sessions/all`

**Bookmarks (3):**
- [x] `POST /api/posts/{post_id}/bookmark`
- [x] `DELETE /api/posts/{post_id}/bookmark`
- [x] `GET /api/bookmarks`

**2FA (4):**
- [x] `POST /api/auth/2fa/enable`
- [x] `POST /api/auth/2fa/verify`
- [x] `POST /api/auth/2fa/disable`
- [x] `GET /api/auth/2fa/backup-codes`

---

## 🧪 TESTING REQUIREMENTS

### **Test Suites to Create:**

- [x] `test_email_verification.py` (5 tests)
  - Email sending
  - Token validation
  - Token expiration
  - Resend verification
  - Verification enforcement

- [x] `test_oidc_integration.py` (7 tests)
  - OIDC login redirect
  - OIDC callback handling
  - User creation from OIDC claims
  - Attribute mapping
  - Error handling

- [x] `test_password_reset.py` (5 tests)
  - Reset request
  - Token generation
  - Token expiration
  - Password update
  - Security (no email enumeration)

- [x] `test_profile_customization.py` (6 tests)
  - Bio update
  - Profile picture upload (real route path)
  - Header upload (real route path)
  - Image validation
  - Size limits

- [x] `test_comments.py` (7 tests)
  - Create comment
  - List comments
  - Threading/replies
  - Edit comment
  - Delete comment
  - Anonymous comments
  - Validation

- [x] `test_notifications.py` (3 tests)
  - Notification creation
  - List notifications
  - Mark as read
  - Delete notification
  - Auto-creation on events

- [x] `test_sessions.py` (3 tests)
  - Session creation
  - Session listing
  - Session revocation
  - Device tracking

- [x] `test_bookmarks.py` (1 test)
  - Bookmark post
  - Remove bookmark
  - List bookmarks

- [x] `test_2fa.py` (3 tests)
  - Enable 2FA
  - Verify code
  - Backup codes
  - Disable 2FA
  - Login with 2FA

- [x] `test_ux_enhancements.py` (2 tests)
  - Privacy settings enforcement
  - Preference updates
  - Pin/unpin post behavior
  - Deactivation/reactivation behavior

**Current:** 42 automated backend tests for Phase 5

---

## 📦 DEPENDENCIES TO ADD

```python
# requirements.txt additions:
qrcode>=7.4.2              # Optional QR code generation
Pillow>=10.0.0             # Optional image optimization
redis>=4.5.0               # Session management (optional)
```

---

## 🔧 INFRASTRUCTURE SETUP

### **Pre-Development:**
- [ ] Obtain OIDC/Entra app credentials from Université Laval IT
- [ ] Configure SMTP server (Gmail/SendGrid/University SMTP)
- [ ] Create file upload directories
- [ ] Install required Python packages
- [ ] Set up environment variables

### **Environment Variables:**
```bash
# OIDC Configuration
ENABLE_OIDC_AUTH=false
OIDC_AUTHORIZE_URL=https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/authorize
OIDC_TOKEN_URL=https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token
OIDC_USERINFO_URL=https://graph.microsoft.com/oidc/userinfo
OIDC_CLIENT_ID=***
OIDC_CLIENT_SECRET=***
OIDC_REDIRECT_URI=https://pulse.ulaval.ca/api/auth/oidc/callback

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
- ⚠️ OIDC tenant access/credential availability
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
| `EMOJI_COLLATION_BUG.md` | Bug fix documentation |
| `BILINGUAL_GUIDE.md` | NLP implementation guide |
| `ZONE_SEARCH_GUIDE.md` | Campus zone search and autocomplete |

### **Documentation to Create:**
- [x] `OIDC_ENTRA_INTEGRATION_GUIDE.md` — OIDC setup instructions
- [x] `OIDC_REENABLE_PLAYBOOK.md` — Step-by-step re-enable guide
- [x] `EMAIL_SERVICE_GUIDE.md` — SMTP configuration
- [x] `2FA_USER_GUIDE.md` — How to enable/use 2FA
- [x] `FILE_UPLOAD_GUIDE.md` — File handling best practices
- [x] `MIGRATION_GUIDE.md` — Existing user migration
- [x] Updated `ARCHITECTURE_DECISIONS.md` — AD-024 to AD-035

---

## 🚀 DEPLOYMENT CHECKLIST

### **Phase 5 Deployment Requirements:**

**Infrastructure:**
- [ ] HTTPS enabled (required for OIDC callback)
- [ ] SMTP server configured
- [ ] File upload directory with proper permissions
- [ ] Image processing libraries installed
- [ ] OIDC credentials configured
- [ ] Redis installed (optional, for sessions)
- [ ] Backup strategy for uploaded files

**Security:**
- [ ] Environment variables secured
- [ ] File upload restrictions enforced
- [ ] Rate limiting on authentication endpoints
- [ ] CORS settings updated for OIDC callback
- [ ] Session secret rotation policy

**Testing:**
- [x] All 42 current Phase 5 backend tests passing
- [ ] OIDC flow tested end-to-end (when `ENABLE_OIDC_AUTH=true`)
- [ ] Email delivery confirmed
- [ ] File uploads working
- [ ] Image optimization verified with Pillow installed
- [ ] 2FA tested with multiple apps

**Documentation:**
- [ ] API docs updated
- [x] OIDC integration guide complete
- [x] OIDC re-enable playbook complete
- [x] Email service guide complete
- [x] Migration guide complete

---

## 📅 DEVELOPMENT TIMELINE

### **Week 1: Phase 5A (Must Have)**
**Days 1-2:** Email Verification
- Email service implementation
- Verification endpoints
- Email templates
- Testing

**Days 3-4:** OIDC Integration
- OIDC client setup
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
- ✅ Institutional auth implementation preserved and documented
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
- Security first (verified emails, OIDC-ready, 2FA)
- Privacy always (anonymous comments, profile visibility)
- User experience matters (notifications, customization)
- Test everything (50+ new tests)
- Document thoroughly (guides for all features)

**Migration Strategy:**
- Phase 5A is backwards compatible
- Existing users can continue using password auth after verification
- OIDC can be re-enabled later without deleting current email-based flow
- Email verification required for new features
- Legacy script tests register verified users via shared helper (`tests/http_test_utils.py`)
- Live DB schema must stay in sync with ORM fields (`users.website`, `users.location`, etc.)

**Team Coordination:**
- Backend: Focus on Phase 5A first
- Frontend: Start UI designs for new features
- DevOps: Prepare OIDC credentials and SMTP
- University IT: Coordinate OIDC/Entra integration

---

**📌 Daily Update Protocol:**
1. Check off completed tasks (convert [ ] to [x])
2. Update progress bars for each component
3. Document any blockers or issues
4. Commit changes with descriptive message
5. Update timeline if needed

---

**Last Update:** 2026-03-14 (Phase 5 findings reconciled with runtime verification)  
**Current Component:** Phase 5 wrap-up + deployment hardening  
**Next Milestone:** End-to-end staging validation + optional dependency install verification (`qrcode`, `Pillow`)  
**Blockers:** OIDC/Entra credentials and tenant access from Université Laval IT pending
- **Validation Note:** 2FA tests now run without `pyotp`; QR rendering and image optimization still improve when optional packages are installed.

---

**Phase 5A Status:** ✅ Complete (5/5 components)  
**Phase 5B Status:** ✅ Complete (3/3 components)  
**Phase 5C Status:** ✅ Complete (2/2 components)

---

**Status:** 🟢 Development Active - Phase 5 implementation complete  
**Priority:** 🔴 High - Production Readiness Critical  
**Timeline:** 📅 10-14 days (as planned)  
**Confidence:** ✅ High - Detailed plan with architectural decisions

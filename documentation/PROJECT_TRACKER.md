# 🎯 PULSE BACKEND — PROJECT TRACKER

**Last Updated:** 2026-02-13  
**University:** Université Laval  
**Student:** Software Engineering Student  
**Project:** Pulse Backend (Privacy-First Campus Wellness Platform)  
**Tech Stack:** Python 3.12.3 + Flask + MySQL  
**Languages:** Bilingual (French/English)  
**Email Domain:** @ulaval.ca

---

## 📊 PROJECT STATUS OVERVIEW

| Phase | Status | Completion |
|-------|--------|------------|
| **Phase 1: Foundation** | ✅ Complete | 100% |
| **Phase 2: Posts & NLP** | ✅ Complete | 100% |
| **Phase 3: Social Features** | ⏳ Pending | 0% |
| **Phase 4: Analytics** | ⏳ Pending | 0% |

**Overall Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜ 80%

---

## ✅ COMPLETED TASKS

### Environment Setup
- [x] Python 3.12.3 confirmed
- [x] MySQL installed and accessible
- [x] Virtual environment created (`venv/`)
- [x] Dependencies installed
- [x] Project structure created
- [x] Configuration files created (.env.template, .gitignore, config.py)
- [x] Flask app factory created (app/__init__.py)
- [x] Entry point created (run.py)

### Database
- [x] MySQL database `pulse_db` created
- [x] Schema executed (users, posts, followers, reactions, etc.)
- [x] Campus zones seeded (10 zones)
- [x] Database connection tested
- [x] All 9 tables verified (users, followers, posts, reactions, etc.)
- [x] Added `updated_at` column to posts table

### Authentication
- [x] User model created (SQLAlchemy ORM)
- [x] Password hashing (bcrypt)
- [x] JWT token generation (string identity fix applied)
- [x] Register endpoint (`POST /api/auth/register`)
- [x] Login endpoint (`POST /api/auth/login`)
- [x] Logout endpoint (`POST /api/auth/logout`)
- [x] Authentication middleware
- [x] Profile endpoints (GET /me, PATCH /update-profile)
- [x] Pseudonym update endpoint (PATCH /update-pseudonym)
- [x] **ALL TESTS PASSING (7/7)** ✅

### Git & Documentation
- [x] .gitignore file created
- [x] requirements.txt created
- [x] GIT_SETUP_GUIDE.md created
- [x] QUICKSTART.md created
- [x] Pushed to GitHub (mo-dev-x/pulse-backend)
- [x] PHASE_1_OVERVIEW.md created
- [x] PHASE_2_COMPLETE.md created

### Posts (Phase 2 Complete ✅)
- [x] Post model created (`app/models/post.py`)
- [x] CampusZone model created (`app/models/campus_zone.py`)
- [x] Bilingual NLP service implemented (French + English)
- [x] Create post endpoint (`POST /api/posts`)
- [x] Sentiment analysis integration (VADER + Twitter RoBERTa)
- [x] Public vs. anonymous toggle working
- [x] Privacy enforcement (anonymous posts hide user_id)
- [x] Content validation (10-500 chars)
- [x] Zone validation
- [x] Test suite created (8/8 tests passing)
- [x] **ALL POSTS TESTS PASSING (8/8)** ✅

### Privacy & Anonymity (Partially Complete)
- [x] Pseudonym system (basic)
- [x] Anonymous post serialization (hides `user_id`)
- [ ] 90-day change cooldown enforcement
- [ ] Private "My Anonymous Posts" view endpoint

### Social Features
- [ ] Follower model
- [ ] Follow/unfollow endpoints
- [ ] Friends computation (mutual follows)
- [ ] User profile endpoint
- [ ] Feed generation (followers' public posts only)

### Interactions
- [ ] Reaction model
- [ ] React to post endpoint
- [ ] Remove reaction endpoint
- [ ] Reaction counts aggregation

### Media
- [ ] Media model
- [ ] File upload validation
- [ ] Image storage
- [ ] Media-post linkage

### Analytics
- [ ] Aggregation service
- [ ] Daily aggregates computation
- [ ] Weekly aggregates computation
- [ ] Minimum threshold enforcement (≥10 posts)
- [ ] Analytics API endpoints

---

## 🔄 CURRENT SPRINT: Phase 3 — Social Features

### 🎯 Next Task: Follow System

**Goal:** Enable users to follow each other and build social connections

**Steps:**
1. ⏳ **NEXT:** Create Follower model (SQLAlchemy)
2. ⏳ Create follow endpoint (`POST /api/follow/@{username}`)
3. ⏳ Create unfollow endpoint (`DELETE /api/unfollow/@{username}`)
4. ⏳ Implement friends computation (mutual follows)
5. ⏳ Create GET endpoints (followers, following, friends)
6. ⏳ Test social graph functionality

**Blockers:** None

**What we'll build:**
- Follower model with one-way relationships
- Follow/unfollow endpoints
- Friends view (mutual follows)
- Social graph queries

---

## 📋 PHASE 2 ACHIEVEMENTS

### Week 2: Posts & NLP Implementation

**Tasks Completed:**
- [x] Created Post model with sentiment fields
- [x] Created CampusZone model
- [x] Integrated bilingual NLP (French: Twitter RoBERTa, English: VADER)
- [x] Built POST /api/posts endpoint
- [x] Implemented privacy-aware serialization
- [x] Added comprehensive validation
- [x] Created test suite (8 tests)
- [x] Fixed database schema mismatches
- [x] Updated documentation

**Success Criteria Met:**
- ✅ Posts created successfully
- ✅ Sentiment analysis works for both languages
- ✅ Anonymous posts hide user_id in API
- ✅ All validations enforced
- ✅ 8/8 tests passing

**Key Learnings:**
- SQLAlchemy models must exactly match database schema
- French NLP first load is slow (~30s), then cached (~3-5s)
- Privacy must be enforced at API layer, not just database
- Comprehensive tests catch schema mismatches early

---

## 🧪 TESTING CHECKLIST

### Authentication Tests (7/7 Passing ✅)
- [x] Register with valid data succeeds
- [x] Register with duplicate email fails
- [x] Register with duplicate username fails
- [x] Register with weak password fails
- [x] Login with correct credentials succeeds
- [x] Login with wrong password fails
- [x] JWT token contains correct user_id

### Post Creation Tests (8/8 Passing ✅)
- [x] Create public English post (positive sentiment)
- [x] Create anonymous French post (negative sentiment)
- [x] French model caching works (<10s after first load)
- [x] Content too short (9 chars) fails with 400
- [x] Content too long (501 chars) fails with 400
- [x] Invalid zone_id fails with 404
- [x] Post without zone succeeds
- [x] Unauthenticated request fails with 401

### Privacy Tests
- [x] Anonymous post doesn't expose user_id in API
- [x] Anonymous post shows pseudonym instead of username
- [x] Public post shows full author info
- [ ] Followers can't see friends' anonymous posts in feed (Phase 3)
- [ ] User can see own anonymous posts in private view (Phase 3)
- [ ] Pseudonym change respects 90-day cooldown (Phase 3)

### Social Tests (Phase 3)
- [ ] Can follow a user
- [ ] Can unfollow a user
- [ ] Can't follow self
- [ ] Mutual follows appear in friends list
- [ ] Feed only shows public posts from followed users

---

## 🛠 KNOWN ISSUES

**Resolved:**
- ✅ JWT identity type mismatch (string vs int) - Fixed in Phase 1
- ✅ CampusZone model column name mismatch (`type` vs `zone_type`) - Fixed in Phase 2
- ✅ Missing `updated_at` column in posts table - Fixed in Phase 2
- ✅ Missing `is_active` column in campus_zones - Removed from model

**Current:**
- None

---

## 📚 LEARNING RESOURCES

### Topics Mastered:
- ✅ Flask blueprints and app factory pattern
- ✅ SQLAlchemy ORM relationships (one-to-many)
- ✅ JWT authentication flow
- ✅ bcrypt password hashing
- ✅ Bilingual NLP sentiment analysis
- ✅ Privacy-aware API design

### Topics to Study (Phase 3):
- Many-to-many relationships (followers)
- Complex SQL queries (friends computation)
- Feed generation algorithms
- API rate limiting strategies
- Caching strategies for performance

### Recommended Reading:
- Flask Mega-Tutorial (Miguel Grinberg)
- SQLAlchemy documentation on relationships
- OWASP Top 10 security risks
- Twitter RoBERTa paper (multilingual sentiment)

---

## 🎯 NEXT IMMEDIATE ACTIONS

### For Phase 3 (Social Features):

1. **Create Follower model**
   ```python
   class Follower(db.Model):
       follower_id  # User who follows
       following_id  # User being followed
   ```

2. **Build follow endpoints**
   ```
   POST   /api/follow/@{username}
   DELETE /api/unfollow/@{username}
   GET    /api/users/@{username}/followers
   GET    /api/users/@{username}/following
   GET    /api/users/me/friends  # Mutual follows
   ```

3. **Create feed endpoint**
   ```
   GET /api/posts/feed
   ```

4. **Test social graph**
   - Follow/unfollow flow
   - Friends computation
   - Feed generation

---

## 📊 METRICS

### Phase 1 (Complete):
- **Development Time:** ~12 days
- **Lines of Code:** ~2,000
- **Tests:** 7/7 passing
- **Endpoints:** 6

### Phase 2 (Complete):
- **Development Time:** ~3 hours
- **Lines of Code:** ~800
- **Tests:** 8/8 passing
- **Endpoints:** 1 (POST /api/posts)

### Overall:
- **Total Endpoints:** 7
- **Total Tests:** 15/15 passing (100%)
- **Models:** 3 (User, Post, CampusZone)
- **Database Tables:** 9
- **Code Quality:** ✅ Production-ready

---

**📌 Remember:** Update this document after every completed task!

**Last Achievement:** Phase 2 Complete - Bilingual Posts with NLP! 🎉  
**Next Milestone:** Phase 3 - Social Features 🚀

**📝 Note:** All architectural decisions are documented in `ARCHITECTURE_DECISIONS.md`
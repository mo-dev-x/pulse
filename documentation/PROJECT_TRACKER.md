# 🎯 PULSE BACKEND — PROJECT TRACKER

**Last Updated:** 2026-02-11  
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
| **Phase 2: Privacy & Social** | 🔄 In Progress | 0% |
| **Phase 3: Interactions** | ⏳ Pending | 0% |
| **Phase 4: Analytics** | ⏳ Pending | 0% |

**Overall Progress:** 🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50%

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
- [x] SETUP_FOR_TEAMMATES.md created
- [x] Pushed to GitHub (mo-dev-x/pulse-backend)
- [x] Repository shared with team
- [x] Documentation consolidated (removed duplicate QUICKSTART.md)

### Posts
- [ ] Post model created
- [ ] NLP service implemented (VADER)
- [ ] Create post endpoint (`POST /api/posts`)
- [ ] Sentiment analysis integration
- [ ] Public vs. anonymous toggle

### Privacy & Anonymity
- [ ] Pseudonym system
- [ ] 90-day change cooldown
- [ ] Anonymous post serialization (hides `user_id`)
- [ ] Private "My Anonymous Posts" view

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

## 🔄 CURRENT SPRINT: Phase 2 — Posts & NLP

### 🎯 Active Task: Post Model & Sentiment Analysis

**Goal:** Create posts with NLP-powered sentiment analysis

**Steps:**
1. ⏳ **NEXT:** Create Post model (SQLAlchemy)
2. ⏳ Create CampusZone model
3. ⏳ Build NLP sentiment service (VADER)
4. ⏳ Create POST /api/posts endpoint
5. ⏳ Test post creation with sentiment analysis
6. ⏳ Verify anonymous vs public posts work correctly

**Blockers:** None

**What we'll build:**
- Post model with `is_anonymous` flag
- NLP service for sentiment analysis (positive/neutral/negative)
- Create post endpoint with zone selection
- Privacy enforcement (anonymous posts hide user_id in API)

---

### 📋 Phase 1 Tasks Breakdown

#### Week 1: Day 1-2 — Database Setup

**Tasks:**
- [ ] Create virtual environment
- [ ] Install Python dependencies
- [ ] Create MySQL database `pulse_db`
- [ ] Create database user with privileges
- [ ] Execute schema creation SQL
- [ ] Seed `campus_zones` table with initial data
- [ ] Test database connection from Python

**Success Criteria:**
- Can connect to MySQL from Python
- All tables exist with correct schema
- Foreign keys and indexes created
- At least 5 campus zones seeded

---

#### Week 1: Day 3-4 — User Authentication

**Tasks:**
- [ ] Create Flask app factory (`app/__init__.py`)
- [ ] Set up configuration (`app/config.py`)
- [ ] Create User model (`app/models/user.py`)
- [ ] Create auth blueprint (`app/routes/auth.py`)
- [ ] Implement password hashing with bcrypt
- [ ] Implement JWT token generation
- [ ] Build registration endpoint
- [ ] Build login endpoint
- [ ] Test with Postman/curl

**Success Criteria:**
- User can register with email, username, password
- Password is hashed in database (never plaintext)
- Login returns valid JWT token
- Token can be decoded to extract user_id

**Security Checklist:**
- [ ] Email validation (proper format)
- [ ] Password strength requirements (min 8 chars, mix of types)
- [ ] Username uniqueness enforced
- [ ] SQL injection prevented (ORM parameterized queries)
- [ ] Rate limiting on registration (prevent spam accounts)

---

#### Week 1: Day 5-7 — Basic Post Creation

**Tasks:**
- [ ] Create Post model (`app/models/post.py`)
- [ ] Create CampusZone model (`app/models/campus_zone.py`)
- [ ] Create NLP service (`app/services/nlp_service.py`)
- [ ] Install VADER sentiment analyzer
- [ ] Create posts blueprint (`app/routes/posts.py`)
- [ ] Implement `POST /api/posts` endpoint
- [ ] Integrate sentiment analysis
- [ ] Store post with sentiment in database
- [ ] Test post creation flow

**Success Criteria:**
- User can create a post with content
- VADER analyzes sentiment correctly
- Sentiment score and label stored in database
- Post includes zone association
- Returns created post with sentiment to user

**NLP Testing:**
- [ ] Test positive text: "I love this campus! ❤️"
- [ ] Test negative text: "So stressed about exams 😭"
- [ ] Test neutral text: "Library closes at 10pm"
- [ ] Test edge case: Very short text (<10 chars)
- [ ] Test edge case: Emojis only

---

## 🚧 UPCOMING TASKS (Phase 2)

### Week 2: Privacy & Social Features

**Not started yet** — Will be detailed when Phase 1 completes

Key components:
- Anonymous posting with pseudonyms
- 90-day pseudonym change cooldown
- Follow/unfollow system
- Friends computation
- Feed generation (excluding anonymous posts from friends)

---

## 📝 DECISIONS LOG

### Decision 1: Anonymity Model
**Date:** 2026-02-10  
**Decision:** Pseudo-Anonymous (store `user_id`, but hide from API)  
**Rationale:** Users can see their own anonymous posts, enables deletion  
**Impact:** Database stores link, backend enforces privacy in API layer

### Decision 2: Pseudonym System
**Date:** 2026-02-10  
**Decision:** Persistent pseudonym with 90-day change cooldown  
**Rationale:** Balance between consistency and privacy  
**Impact:** All past anonymous posts reflect current pseudonym

### Decision 3: Reactions on Anonymous Posts
**Date:** 2026-02-10  
**Decision:** Allow reactions on all posts (public and anonymous)  
**Rationale:** Anonymous posts should behave like public posts  
**Risk:** Could enable pattern tracking (mitigated by aggregate analytics only)

### Decision 4: Edit vs. Delete
**Date:** 2026-02-10  
**Decision:** Users can DELETE but NOT EDIT anonymous posts  
**Rationale:** Editing could reveal identity through writing style changes  
**Impact:** Simpler UX, clearer privacy guarantee

### Decision 5: Social Model
**Date:** 2026-02-10  
**Decision:** Hybrid — Followers (one-way) + Friends (mutual)  
**Rationale:** Flexibility for users to follow without reciprocity  
**Impact:** Need to compute friends dynamically from followers table

---

## 🔍 TESTING CHECKLIST

### Authentication Tests
- [ ] Register with valid data succeeds
- [ ] Register with duplicate email fails
- [ ] Register with duplicate username fails
- [ ] Register with weak password fails
- [ ] Login with correct credentials succeeds
- [ ] Login with wrong password fails
- [ ] JWT token contains correct user_id
- [ ] Expired token is rejected

### Post Creation Tests
- [ ] Create public post succeeds
- [ ] Create anonymous post succeeds
- [ ] Post without authentication fails (401)
- [ ] Post with invalid zone_id fails (400)
- [ ] Post with empty content fails (400)
- [ ] Post exceeding 500 chars fails (400)
- [ ] Sentiment analysis runs correctly
- [ ] Rate limiting blocks 11th post in hour

### Privacy Tests
- [ ] Anonymous post doesn't expose user_id in API
- [ ] Followers can't see friends' anonymous posts in feed
- [ ] User can see own anonymous posts in private view
- [ ] Pseudonym change respects 90-day cooldown
- [ ] Changing pseudonym updates all past anonymous posts

### Social Tests
- [ ] Can follow a user
- [ ] Can unfollow a user
- [ ] Can't follow self
- [ ] Mutual follows appear in friends list
- [ ] Feed only shows public posts from followed users

---

## 🐛 KNOWN ISSUES

**None yet** — Will be tracked as development progresses

---

## 📚 LEARNING RESOURCES

### Topics to Study:
- Flask blueprints and app factory pattern
- SQLAlchemy ORM relationships (one-to-many, many-to-many)
- JWT authentication flow
- bcrypt password hashing
- VADER sentiment analysis
- SQL indexing for performance
- API rate limiting strategies

### Recommended Reading:
- Flask Mega-Tutorial (Miguel Grinberg)
- SQLAlchemy documentation on relationships
- OWASP Top 10 security risks

---

## 🎯 NEXT IMMEDIATE ACTIONS

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy flask-jwt-extended flask-cors pymysql cryptography bcrypt vaderSentiment python-dotenv
   ```

3. **Create project structure**
   ```
   pulse-backend/
   ├── venv/
   ├── app/
   │   ├── __init__.py
   │   ├── config.py
   │   ├── models/
   │   ├── routes/
   │   ├── services/
   │   └── middleware/
   ├── requirements.txt
   ├── .env
   └── run.py
   ```

4. **Create MySQL database**
   ```sql
   CREATE DATABASE pulse_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

5. **Execute schema SQL**

---

**📌 Remember:** Update this document after every completed task!

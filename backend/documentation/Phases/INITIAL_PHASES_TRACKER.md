# 🎯 PULSE BACKEND — PROJECT TRACKER

**Last Updated:** 2026-02-13  
**University:** Université Laval  
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
| **Phase 3: Social Features** | ✅ Complete | 100% |
| **Phase 4: Analytics** | ✅ Complete | 100% |

**Overall Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100%

---

## ✅ COMPLETED TASKS

### Phase 1: Foundation
- [x] Python 3.12.3, MySQL 8.0, virtual environment
- [x] Flask app factory with SQLAlchemy, JWT, CORS
- [x] Database schema — 9 tables, 10 campus zones seeded
- [x] User model with password hashing, email validation (@ulaval.ca)
- [x] Authentication endpoints (register, login, logout, profile, pseudonym)
- [x] Bilingual i18n utility (`app/utils/i18n.py`)
- [x] **7/7 auth tests passing** ✅

### Phase 2: Posts & NLP
- [x] Post model with sentiment fields
- [x] CampusZone model
- [x] Bilingual NLP service (`app/services/nlp_service_camembert.py`)
  - VADER for English, Twitter XLM-RoBERTa for French
  - Automatic language detection via `langdetect`
- [x] `POST /api/posts` — create post with sentiment analysis
- [x] Privacy-aware serialization (anonymous posts hide `user_id`)
- [x] Content validation (10–500 chars)
- [x] **8/8 post tests passing** ✅

### Phase 3: Social Features & Interactions
- [x] Follower model (`app/models/follower.py`)
  - One-way follows, friends = mutual follows (computed)
  - Helper methods: `is_following()`, `get_friends()`, `get_following_ids()`, counts
- [x] Social routes (`app/routes/social.py`)
  - `POST /api/follow/@{username}` — follow user
  - `DELETE /api/unfollow/@{username}` — unfollow user
  - `GET /api/users/@{username}/followers` — paginated followers list
  - `GET /api/users/@{username}/following` — paginated following list
  - `GET /api/users/me/friends` — mutual follows
  - `GET /api/users/@{username}` — public profile with counts and recent posts
- [x] Feed & post retrieval (`app/routes/posts.py`)
  - `GET /api/posts/feed` — public posts from followed users only
  - `GET /api/posts/me` — own public posts
  - `GET /api/posts/me/anonymous` — own anonymous posts (private view)
  - `GET /api/posts/@{username}` — user's public posts
  - `GET /api/posts/zone/{zone_id}` — zone feed
  - `DELETE /api/posts/{post_id}` — delete own post (24h window)
- [x] Reaction model (`app/models/reaction.py`)
  - 10 allowed emojis, one per user per post
  - Privacy: only aggregate counts exposed, never "who reacted"
- [x] Reaction routes (`app/routes/reactions.py`)
  - `POST /api/posts/{post_id}/react` — add/update reaction
  - `DELETE /api/posts/{post_id}/react` — remove reaction
  - `GET /api/posts/{post_id}/reactions` — counts + user's own reaction
- [x] Media model (`app/models/media.py`)
- [x] Image upload support in `POST /api/posts` (multipart/form-data)
- [x] Models registered in `app/models/__init__.py`
- [x] Blueprints registered in `app/__init__.py`
- [x] 15+ bilingual i18n messages added

### Phase 4: Analytics
- [x] DailyAggregate and WeeklyAggregate models (`app/models/aggregate.py`)
  - Privacy threshold: data only shown when `total_posts >= 10`
  - Mood label computation from avg_sentiment
- [x] Aggregation service (`app/services/aggregation_service.py`)
  - `compute_daily_aggregate()` — per-date, optionally per-zone
  - `compute_weekly_aggregate()` — per-week, optionally per-zone
  - `get_campus_mood_overview()` — campus-wide + per-zone breakdown
- [x] Analytics routes (`app/routes/analytics.py`)
  - `GET /api/analytics/daily?date=YYYY-MM-DD&zone_id=X`
  - `GET /api/analytics/weekly?week_start=YYYY-MM-DD&zone_id=X`
  - `GET /api/analytics/campus?date=YYYY-MM-DD`

---

## 📈 METRICS

| Metric | Value |
|--------|-------|
| **Total Endpoints** | 24 |
| **Models** | 8 (User, Post, CampusZone, Follower, Reaction, Media, DailyAggregate, WeeklyAggregate) |
| **Database Tables** | 9 |
| **Auth Tests** | 7/7 ✅ |
| **Post Tests** | 8/8 ✅ |
| **Syntax Validation** | 13/13 files ✅ |

---

## 🛠 KNOWN ISSUES

**Resolved:**
- ✅ JWT identity type mismatch (string vs int) — Fixed in Phase 1
- ✅ CampusZone model column name mismatch (`type` vs `zone_type`) — Fixed in Phase 2
- ✅ Missing `updated_at` column in posts table — Fixed in Phase 2
- ✅ Missing `is_active` column in campus_zones — Removed from model
- ✅ **Emoji collation bug in reactions table** — Fixed Feb 14, 2026
  - **Issue:** MySQL `utf8mb4_unicode_ci` collation caused GROUP BY to incorrectly aggregate different emojis together
  - **Fix:** Changed `reactions.emoji` column to `utf8mb4_bin` collation for byte-by-byte comparison
  - **Details:** See `EMOJI_COLLATION_BUG.md`

**Current:**
- None

---

## 📚 DOCUMENTATION

| Document | Purpose |
|----------|---------|
| `README.md` | Project overview, API reference, architecture |
| `QUICKSTART.md` | Setup guide, environment config, first run |
| `ARCHITECTURE_DECISIONS.md` | All technical decisions (AD-001 through AD-013) |
| `PROJECT_TRACKER.md` | This file — development progress |

---

**📌 Remember:** Update this document after every completed task!

**Last Achievement:** Phase 4 Complete — All features implemented 🎉  
**Next Milestone:** Integration testing & deployment preparation 🚀

**📝 Note:** All architectural decisions are documented in `ARCHITECTURE_DECISIONS.md`
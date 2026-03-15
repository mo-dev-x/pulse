# 🚀 PHASE 6 OVERVIEW — SCALE, SEARCH & PLATFORM INTELLIGENCE

**Pulse Backend — Backend-Only Roadmap (Frontend-Independent)**

**Status:** Planning  
**Priority:** High — Production Scale & Platform Completeness  
**Estimated Time:** 12–16 days  
**Context:** Phase 5 is 100% complete. Frontend is in active development. This phase is designed entirely for the backend developer to progress independently while the frontend catches up.

> **Design principle for Phase 6:** Every feature in this phase is either a pure backend concern (rate limiting, search indexing, moderation pipeline) or produces fully documented, testable API endpoints that the frontend can wire in when ready. Nothing here requires a UI to be built first.

---

## 🎯 PHASE 6 GOALS

Phase 6 transforms Pulse from a feature-complete MVP into a platform that can handle real university-scale traffic:

- **Search** — Unified full-text search across posts, users, and zones
- **Feed intelligence** — Discovery feed, trending content, zone-based feed
- **Rate limiting & abuse prevention** — Protect all endpoints from spam/bots
- **Moderation pipeline** — Report system, content flags, admin controls
- **Direct messaging** — Private conversations between users
- **Push notification infrastructure** — FCM/APNS-ready notification delivery
- **Performance hardening** — Query optimization, caching layer, background jobs

---

## 📊 PHASE 6 STATUS OVERVIEW

| Component | Priority | Status | Estimated Days |
|-----------|----------|--------|----------------|
| **6A: Search API** | Must Have | ✅ Complete | 2 days |
| **6A: Discovery & trending feed** | Must Have | ✅ Complete | 2 days |
| **6A: Rate limiting** | Must Have | ✅ Complete | 1 day |
| **6B: Moderation & reporting** | Should Have | ✅ Complete | 2 days |
| **6B: Direct messaging** | Should Have | ✅ Complete | 3 days |
| **6B: Zone feed endpoint** | Should Have | ✅ Complete | 1 day |
| **6C: Push notifications** | Nice to Have | ✅ Complete | 2 days |
| **6C: Caching layer** | Nice to Have | ✅ Complete | 1 day |
| **6C: Background job queue** | Nice to Have | ✅ Complete | 2 days |

**Phase 6A Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% (Must Have — 5 days)  
**Phase 6B Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% (Should Have — 6 days)  
**Phase 6C Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% (Nice to Have — 5 days)

**Overall Phase 6 Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% / 100%

---

## 📋 PHASE 6A: MUST HAVE (Days 1–5)

---

### **Component 1: Unified Search API**
**Timeline:** Days 1–2  
**Priority:** Critical — Core UX blocker on frontend side

#### Problem
There is currently no search. Users cannot find other users, browse posts by keyword, or discover zones. The frontend's search bar has nowhere to point.

#### Solution
A single `/api/search` endpoint with type filtering, backed by MySQL `FULLTEXT` indexes for relevance-ranked results.

#### Database Changes

Add `FULLTEXT` indexes to existing tables (migration script):

```sql
-- Posts full-text index
ALTER TABLE posts ADD FULLTEXT INDEX ft_posts_content (content);

-- Users full-text index (username + display_name + bio)
ALTER TABLE users ADD FULLTEXT INDEX ft_users_identity (username, display_name, bio);

-- Campus zones full-text index (already has name/description, add FULLTEXT)
ALTER TABLE campus_zones ADD FULLTEXT INDEX ft_zones_search (name, description);
```

> These indexes are required before production-scale search traffic. Search should narrow result sets in SQL first and only rank the smaller candidate set in Python.

> **AD-051** — See Architecture Decisions section below.

#### Endpoints to Build

**`GET /api/search`** — Unified search across all entity types

```
Query params:
  q        (string, required, min 2 chars)
  type     (string, optional: "posts" | "users" | "zones" | "all", default "all")
  page     (int, default 1)
  per_page (int, default 20, max 50)
  zone_id  (int, optional — scope post results to a zone)

Response:
{
  "query": "bibliotheque",
  "results": {
    "posts": [ ...post objects with match_score ],
    "users": [ ...public user objects ],
    "zones": [ ...zone objects ]
  },
  "counts": { "posts": 14, "users": 2, "zones": 1 },
  "page": 1,
  "has_next": false
}
```

**Privacy rules to enforce in search:**
- Anonymous posts are **never** returned in search results (same rule as the feed)
- Users with `profile_visibility = 'private'` are **not** returned
- Deactivated users are **not** returned
- Post content from deactivated users is **not** returned

**`GET /api/search/users`** — User-only search (for @mention autocomplete)

```
Query params:
  q        (string, required, min 1 char)
  limit    (int, default 5, max 20)

Response:
{
  "users": [
    { "username": "jdoe", "display_name": "Jane Doe", "profile_picture": "..." }
  ]
}
```

> This endpoint will be used by the frontend's @mention system in the post composer and comment box.

#### File to Create
`app/routes/search.py` — new Blueprint `search`

Register in `app/__init__.py`:
```python
from app.routes.search import bp as search_bp
app.register_blueprint(search_bp, url_prefix='/api')
```

#### Tests to Write (`test_search.py`)
- Search returns posts matching keyword ✓
- Anonymous posts excluded from search ✓
- Private-profile users excluded from search ✓
- Deactivated users excluded from search ✓
- `type=users` returns only users ✓
- `type=zones` returns only zones ✓
- Query under 2 chars returns 400 ✓
- Missing `q` param returns 400 ✓
- Pagination works correctly ✓
- User-only search endpoint works for @mentions ✓

**Target: 10 tests**

---

### **Component 2: Discovery Feed & Trending**
**Timeline:** Days 3–4  
**Priority:** Critical — New users with zero follows see an empty feed today

#### Problem
A brand-new user who follows nobody gets an empty feed (`feed_empty`). There is nothing to discover. This is the worst possible first-time experience.

#### Solution
Two new feed modes:
1. **Discovery feed** — recent public posts from all verified users, ranked by engagement
2. **Trending endpoint** — top posts and zones over a configurable time window

#### Endpoints to Build

**`GET /api/posts/discover`** — Campus-wide discovery feed

```
Query params:
  page     (int, default 1)
  per_page (int, default 20, max 50)
  zone_id  (int, optional — filter by zone)
  sentiment (string, optional: "positive" | "negative" | "neutral")

Ranking logic (descending):
  score = reaction_count * 2 + comment_count + (1 / hours_since_posted * 10)

Privacy rules:
  - Only public (non-anonymous) posts
  - Only from verified, non-deactivated users
  - Does NOT expose who wrote an anonymous post
```

**`GET /api/posts/trending`** — Trending posts

```
Query params:
  window   (string: "1h" | "6h" | "24h" | "7d", default "24h")
  limit    (int, default 10, max 25)
  zone_id  (int, optional)

Response:
{
  "window": "24h",
  "posts": [ ...top posts by engagement score ],
  "trending_zones": [
    { "zone": {...}, "post_count": 47, "avg_sentiment": "positive" }
  ]
}
```

**`GET /api/zones/trending`** — Most active zones (used by frontend zone browser)

```
Query params:
  window  (string: "1h" | "6h" | "24h" | "7d", default "24h")
  limit   (int, default 10)

Response:
{
  "zones": [
    { "zone": {...}, "post_count": 47, "reaction_count": 213, "mood": "positive" }
  ]
}
```

#### Tests to Write
- Discovery feed returns public posts only ✓
- Anonymous posts excluded from discovery ✓
- Zone filter works on discovery ✓
- Trending returns posts ordered by engagement ✓
- Time window filtering works ✓
- Empty result when no posts in window ✓
- Trending zones returns correct counts ✓

**Target: 7 tests**

---

### **Component 3: Rate Limiting**
**Timeline:** Day 5  
**Priority:** Critical — Required before any public launch

#### Problem
All endpoints are currently unprotected against abuse. A bad actor could spam posts, brute-force logins, enumerate users, or flood notifications.

#### Solution
Per-endpoint rate limits using `flask-limiter` with an in-memory store (upgradeable to Redis).

#### Setup

```bash
pip install flask-limiter
```

Add to `requirements.txt`:
```
flask-limiter==3.8.0
```

Initialize in `app/__init__.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # swap to redis:// in production
)
limiter.init_app(app)
```

#### Rate Limits by Endpoint Category

| Endpoint(s) | Limit | Rationale |
|-------------|-------|-----------|
| `POST /api/auth/login` | 10/minute per IP | Brute force protection |
| `POST /api/auth/register` | 5/hour per IP | Prevent spam accounts |
| `POST /api/auth/forgot-password` | 5/hour per IP | Prevent email flooding |
| `POST /api/auth/send-verification` | 5/hour per IP | Prevent email flooding |
| `POST /api/posts` | 15/hour per user | Prevent post spam |
| `POST /api/posts/<id>/react` | 30/minute per user | Prevent reaction spam |
| `POST /api/comments` | 20/hour per user | Prevent comment spam |
| `GET /api/search` | 60/minute per IP | Prevent scraping |
| `POST /api/messages` (Phase 6B) | 60/hour per user | Prevent DM spam |

#### Error Response Format
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

Bilingual — add to `i18n.py`:
- EN: `"Too many requests. Please try again in {n} seconds."`
- FR: `"Trop de requêtes. Veuillez réessayer dans {n} secondes."`

#### Tests to Write
- Login rate limit triggers after 10 attempts ✓
- Rate limit returns 429 with correct headers ✓
- Different users have independent limits ✓

**Target: 3 tests**

---

## 📋 PHASE 6B: SHOULD HAVE (Days 6–11)

---

### **Component 4: Moderation & Reporting Pipeline**
**Timeline:** Days 6–7  
**Priority:** High — Required for a safe campus platform

#### Problem
Users currently have no way to report harmful content. There is no admin tooling to act on reports. For a wellness platform, this is a meaningful safety gap.

#### Solution
A report system with status tracking, and admin-level moderation endpoints protected by a role check.

#### Database Changes

```sql
CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id INT NOT NULL,
    target_type ENUM('post', 'comment', 'user') NOT NULL,
    target_id INT NOT NULL,
    reason ENUM(
        'spam',
        'harassment',
        'self_harm',
        'misinformation',
        'inappropriate',
        'other'
    ) NOT NULL,
    details TEXT NULL,                          -- Optional extra context from reporter
    status ENUM('pending', 'reviewed', 'actioned', 'dismissed') NOT NULL DEFAULT 'pending',
    reviewed_by INT NULL,                       -- Admin user ID
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_reports_status (status),
    INDEX idx_reports_target (target_type, target_id)
);

-- Add moderation fields to posts
ALTER TABLE posts
    ADD COLUMN is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN flagged_at TIMESTAMP NULL,
    ADD COLUMN hidden_by_mod BOOLEAN NOT NULL DEFAULT FALSE;

-- Add is_admin to users
ALTER TABLE users
    ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
```

> **AD-052** — See Architecture Decisions section below.

#### Endpoints to Build

**`POST /api/reports`** — Submit a content report

```
Body:
{
  "target_type": "post",
  "target_id": 42,
  "reason": "self_harm",
  "details": "Optional description"
}

Response 201:
{ "message": "Report submitted. Our team will review it.", "report_id": 7 }

Rules:
- A user cannot report the same target twice (return 409)
- Reporter cannot report their own content (return 400)
- Bilingual response messages
```

**`GET /api/admin/reports`** — List pending reports (admin only)

```
Query params:
  status   (string: "pending" | "reviewed" | "actioned" | "dismissed", default "pending")
  page, per_page

Response:
{
  "reports": [ ...report objects with target content preview ],
  "total": 12
}
```

**`PATCH /api/admin/reports/<id>`** — Act on a report (admin only)

```
Body:
{
  "action": "dismiss" | "hide_content" | "warn_user" | "deactivate_user"
}
```

**`DELETE /api/admin/posts/<id>`** — Hard-delete a post (admin only)

**`GET /api/admin/flagged`** — Auto-flagged content queue (admin only)

> Auto-flagging: if a post receives 5+ reports within 24h, set `is_flagged = TRUE` automatically. Flagged posts are hidden from public feeds until reviewed.

#### Admin Role Guard

Create `app/middleware.py` decorator:
```python
def require_admin(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper
```

#### File to Create
`app/routes/moderation.py` — Blueprint `moderation`  
`app/models/report.py` — Report model

#### Tests to Write
- User can submit a report ✓
- Duplicate report returns 409 ✓
- User cannot report own content ✓
- Non-admin cannot access admin endpoints ✓
- Admin can view pending reports ✓
- Admin can dismiss a report ✓
- Admin can hide post via report action ✓
- Auto-flag triggers at threshold ✓

**Target: 8 tests**

---

### **Component 5: Direct Messaging**
**Timeline:** Days 8–10  
**Priority:** High — The `msgList` panel in `feed.html` is currently demo-only hardcoded data

#### Problem
The frontend has a "Messages" panel with demo data. The backend has no messaging system. This is the most visible placeholder in the current UI.

#### Solution
A conversation-based direct messaging system. No real-time socket required at this stage — polling-friendly REST endpoints designed to be upgradeable to WebSocket later.

#### Database Changes

```sql
CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_a INT NOT NULL,     -- Always store as lower user ID
    participant_b INT NOT NULL,     -- Always store as higher user ID
    last_message_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_a) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_b) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_conversation (participant_a, participant_b),
    INDEX idx_conv_last_msg (last_message_at DESC)
);

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_msg_conv_time (conversation_id, created_at DESC)
);
```

> **AD-053** — See Architecture Decisions section below.

#### Endpoints to Build

**`GET /api/messages/conversations`** — List all conversations for current user

```
Response:
{
  "conversations": [
    {
      "id": 1,
      "other_user": { "username": "...", "display_name": "...", "profile_picture": "..." },
      "last_message": { "content": "...", "created_at": "...", "is_mine": true },
      "unread_count": 2
    }
  ]
}
```

**`POST /api/messages/conversations`** — Start or retrieve a conversation

```
Body: { "username": "jdoe" }
Response 200/201: { "conversation": { "id": 5, "other_user": {...} } }

Rules:
- Cannot message yourself
- Cannot message a user who has blocked you (Phase 6C)
- Returns existing conversation if one already exists (idempotent)
```

**`GET /api/messages/conversations/<id>`** — Get messages in a conversation

```
Query params: page, per_page (default 50)
Response: { "messages": [...], "has_more": true }

Privacy: only participants can read the conversation — 403 otherwise.
```

**`POST /api/messages/conversations/<id>`** — Send a message

```
Body: { "content": "..." }
Limits: 1–1000 characters. Rate limited (see Phase 6A Component 3).
Response 201: { "message": { "id": 99, "content": "...", "created_at": "..." } }
```

**`PATCH /api/messages/conversations/<id>/read`** — Mark conversation as read

```
Response 200: { "marked_read": 3 }  -- number of messages marked read
```

**`GET /api/messages/unread-count`** — Total unread message count (for badge in UI)

```
Response: { "unread_conversations": 2, "unread_messages": 5 }
```

#### File to Create
`app/routes/messages.py` — Blueprint `messages`  
`app/models/conversation.py`  
`app/models/message.py`

#### Tests to Write (`test_messages.py`)
- User can start a conversation ✓
- Starting same conversation twice is idempotent ✓
- Cannot message yourself ✓
- Can send a message ✓
- Messages paginate correctly ✓
- Non-participant cannot read conversation ✓
- Mark as read updates unread count ✓
- Unread count endpoint is correct ✓
- Message content validated (min/max length) ✓

**Target: 9 tests**

---

### **Component 6: Zone Feed Endpoint**
**Timeline:** Day 11  
**Priority:** High — Zone autocomplete exists, but there is no zone-scoped feed

#### Problem
The frontend zone picker lets users tag posts to a zone, but there is no way to browse posts by zone. The existing `/api/posts/zone/<zone_id>` endpoint exists but has no pagination metadata in its response.

#### Solution
Upgrade the existing zone posts endpoint and add a zone activity summary endpoint.

#### Endpoints to Upgrade / Add

**`GET /api/posts/zone/<zone_id>`** — (Already exists — upgrade it)

Add missing response fields:
```json
{
  "zone": { "id": 3, "name": "PEPS", "zone_type": "sports" },
  "posts": [...],
  "total": 47,
  "page": 1,
  "pages": 3,
  "has_next": true
}
```

**`GET /api/zones/<id>/activity`** — Zone mood and activity summary

```
Response:
{
  "zone": { "id": 3, "name": "PEPS" },
  "last_24h": {
    "post_count": 47,
    "reaction_count": 213,
    "dominant_sentiment": "positive",
    "sentiment_breakdown": { "positive": 0.62, "neutral": 0.28, "negative": 0.10 }
  },
  "recent_posts": [ ...5 most recent public posts ]
}
```

#### Tests to Write
- Zone feed returns paginated posts ✓
- Zone feed excludes anonymous posts ✓
- Zone activity summary returns correct sentiment breakdown ✓

**Target: 3 tests**

---

## 📋 PHASE 6C: NICE TO HAVE (Days 12–16)

---

### **Component 7: Push Notification Infrastructure**
**Timeline:** Days 12–13

The notification system from Phase 5B generates in-app notifications. This component adds the delivery layer so notifications can reach users on mobile/desktop even when the app is closed.

#### Database Changes

```sql
CREATE TABLE push_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    platform ENUM('web', 'ios', 'android') NOT NULL,
    token TEXT NOT NULL,           -- FCM token or Web Push subscription JSON
    device_label VARCHAR(100) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_push_user (user_id),
    INDEX idx_push_active (is_active)
);
```

#### Endpoints to Build

**`POST /api/push/subscribe`** — Register a device token

```
Body: { "platform": "web", "token": "...", "device_label": "MacBook Chrome" }
Response 201: { "subscription_id": 12 }
```

**`DELETE /api/push/subscribe/<id>`** — Unregister a device

**`POST /api/push/test`** — Send a test notification to the current user (dev/debug only, gated by `FLASK_ENV=development`)

#### Delivery Service

Create `app/services/push_service.py`:

```python
def send_push_notification(user_id: int, title: str, body: str, data: dict = None):
    """
    Dispatch a push notification to all active subscriptions for a user.
    Silently skips if FCM is not configured (PUSH_ENABLED=false).
    """
    if not current_app.config.get('PUSH_ENABLED', False):
        return
    # FCM HTTP v1 API call here
    ...
```

Hook into `notification_service.py` — after creating a DB notification, call `send_push_notification` in a background thread so it never blocks the request.

> **AD-054** — See Architecture Decisions section below.

---

### **Component 8: Caching Layer**
**Timeline:** Day 14

Cache expensive, frequently-read endpoints to reduce database load.

#### Target Endpoints for Caching

| Endpoint | TTL | Invalidation |
|----------|-----|-------------|
| `GET /api/zones` | 1 hour | On zone data change |
| `GET /api/zones/trending` | 5 minutes | TTL only |
| `GET /api/posts/trending` | 2 minutes | TTL only |
| `GET /api/analytics/campus-mood` | 5 minutes | TTL only |
| `GET /api/users/@<username>` (public profile) | 2 minutes | On profile update |

#### Implementation

```bash
pip install flask-caching
```

Add to `requirements.txt`:
```
flask-caching==2.3.0
```

Initialize in `app/__init__.py`:
```python
from flask_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})  # swap to RedisCache in prod
cache.init_app(app)
```

Usage:
```python
@bp.route('/zones', methods=['GET'])
@cache.cached(timeout=3600, key_prefix='all_zones')
def get_all_zones():
    ...
```

If a cached endpoint includes user-specific fields such as `my_reaction`, the cache key must include the authenticated user identity rather than only the URL/query string.

---

### **Component 9: Background Job Queue**
**Timeline:** Days 15–16

Some operations are too slow or too risky to run inside the HTTP request cycle.

#### Candidates for Background Processing

| Task | Current | Target |
|------|---------|--------|
| NLP sentiment analysis | Blocking (in request) | Background queue |
| Push notification delivery | N/A | Background queue |
| Email sending | Blocking (in request) | Background queue |
| Auto-flag check (5+ reports) | N/A | Background job |
| Aggregation refresh | On-demand | Scheduled every 15min |

#### Implementation with `rq`

```bash
pip install rq redis
```

Add to `requirements.txt`:
```
rq==1.16.2
redis==5.0.8
```

Create `app/tasks/`:
- `app/tasks/nlp_tasks.py` — async sentiment analysis
- `app/tasks/email_tasks.py` — async email delivery
- `app/tasks/push_tasks.py` — async push dispatch
- `app/tasks/moderation_tasks.py` — auto-flag evaluation

> **AD-055** — See Architecture Decisions section below.

---

## 🗂️ ARCHITECTURE DECISIONS (Phase 6)

### **AD-051: MySQL FULLTEXT Search Over External Engine**

**Date:** 2026-03-15  
**Decision:** Use MySQL `FULLTEXT` indexes for Phase 6 search instead of Elasticsearch or Meilisearch.

**Rationale:** The existing stack is Python + MySQL. Adding a dedicated search engine adds operational complexity (extra service, extra sync logic, extra infra cost) that is not justified at university-project scale. MySQL FULLTEXT in `IN BOOLEAN MODE` provides ranked results, stop-word filtering, and bilingual support sufficient for Pulse's needs. Can be migrated to Meilisearch in a future phase if needed.

**Trade-off:** No fuzzy matching, no typo tolerance. Mitigated partially by the zone alias system already in `zones.py`.

---

### **AD-052: Report System as Moderation Inbox, Not Auto-Remove**

**Date:** 2026-03-15  
**Decision:** Reports go into a review queue. Content is NOT automatically removed on report submission.

**Rationale:** Automatic removal on report is trivially abusable — any user could silence another by mass-reporting. Given Pulse is a wellness platform handling sensitive content, false positives carry real harm risk. The exception is the auto-flag threshold (5+ reports in 24h), which hides content from feeds pending review but does not delete it.

**Implementation:** `status` field on `reports` table. Admin workflow in `moderation.py`.

---

### **AD-053: Conversations Keyed by Sorted User ID Pair**

**Date:** 2026-03-15  
**Decision:** Store `participant_a = min(id_a, id_b)` and `participant_b = max(id_a, id_b)` with a `UNIQUE` constraint on the pair.

**Rationale:** Prevents duplicate conversations between the same two users regardless of who initiates. A single lookup `WHERE (participant_a=X AND participant_b=Y)` is always correct without needing to check both orderings.

---

### **AD-054: Push Notifications Fire-and-Forget via Background Thread**

**Date:** 2026-03-15  
**Decision:** Push delivery runs in a daemon thread, not in the request cycle.

**Rationale:** FCM/APNS calls have variable latency (50–500ms). Blocking a post-creation or comment request on external push delivery would visibly degrade API response times. If the push fails, the in-app notification (Phase 5B) already exists as fallback.

**Implementation:** `threading.Thread(target=send_push_notification, daemon=True).start()` in `notification_service.py`. Upgrade to `rq` queue in Phase 6C.

---

### **AD-055: rq Over Celery for Background Jobs**

**Date:** 2026-03-15  
**Decision:** Use `rq` (Redis Queue) rather than Celery for background tasks.

**Rationale:** `rq` has a significantly simpler setup, no broker configuration files, and the same Redis instance used for rate limiting (if enabled) can serve double duty as the job queue. Celery's power is not needed at this scale. If job volume grows, migration to Celery is straightforward since both use Redis.

---

## 🗺️ NEW ENDPOINTS SUMMARY (Phase 6)

| Method | Endpoint | Component | Auth |
|--------|----------|-----------|------|
| GET | `/api/search` | 6A — Search | JWT |
| GET | `/api/search/users` | 6A — Search | JWT |
| GET | `/api/posts/discover` | 6A — Discovery | JWT |
| GET | `/api/posts/trending` | 6A — Trending | JWT |
| GET | `/api/zones/trending` | 6A — Trending | JWT |
| POST | `/api/reports` | 6B — Moderation | JWT |
| GET | `/api/admin/reports` | 6B — Moderation | JWT + Admin |
| PATCH | `/api/admin/reports/<id>` | 6B — Moderation | JWT + Admin |
| DELETE | `/api/admin/posts/<id>` | 6B — Moderation | JWT + Admin |
| GET | `/api/admin/flagged` | 6B — Moderation | JWT + Admin |
| GET | `/api/messages/conversations` | 6B — DMs | JWT |
| POST | `/api/messages/conversations` | 6B — DMs | JWT |
| GET | `/api/messages/conversations/<id>` | 6B — DMs | JWT |
| POST | `/api/messages/conversations/<id>` | 6B — DMs | JWT |
| PATCH | `/api/messages/conversations/<id>/read` | 6B — DMs | JWT |
| GET | `/api/messages/unread-count` | 6B — DMs | JWT |
| GET | `/api/zones/<id>/activity` | 6B — Zone feed | JWT |
| POST | `/api/push/subscribe` | 6C — Push | JWT |
| DELETE | `/api/push/subscribe/<id>` | 6C — Push | JWT |

**Total new endpoints: 19**

---

## 📊 TARGET METRICS (Post Phase 6)

| Metric | Post Phase 5 | Target Phase 6 | Delta |
|--------|-------------|----------------|-------|
| Total Endpoints | ~55 | ~74 | +19 |
| Models | 13 | 18 | +5 |
| Database Tables | 14 | 18 | +4 |
| Services | 5 | 8 | +3 |
| Tests | 113 | 170+ | +57 |

---

## 📦 NEW DEPENDENCIES

```
flask-limiter==3.8.0       # Rate limiting (6A)
flask-caching==2.3.0       # Response caching (6C)
rq==1.16.2                 # Background job queue (6C)
redis==5.0.8               # Required by rq and limiter in production (6C)
```

> `redis` is optional in development — both `flask-limiter` and `flask-caching` fall back to in-memory stores. Set `REDIS_URL` in `.env` for production.

Add to `.env`:
```
REDIS_URL=redis://localhost:6379/0
PUSH_ENABLED=false
FCM_SERVER_KEY=***
```

---

## 🛠️ KNOWN RISKS & MITIGATIONS

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| FULLTEXT index performance on large post volume | Low at current scale | Acceptable; add Meilisearch in Phase 7 if needed |
| DM content moderation gap | Medium | Report system (6B) covers DMs via `target_type='message'` extension |
| Push token staleness (invalid tokens) | High over time | Catch FCM 404 responses and auto-deactivate subscription |
| Admin endpoint discovery | Low | Rate limit admin endpoints; log all admin actions to `security_logs` |
| rq worker not running | Medium | Document worker startup in `QUICKSTART.md`; degrade gracefully without it |

---

## 🚀 DEPLOYMENT CHECKLIST (Phase 6 Additions)

**Database:**
- [ ] Run FULLTEXT index migrations
- [ ] Run `reports`, `conversations`, `messages`, `push_subscriptions` table migrations
- [ ] Add `is_flagged`, `hidden_by_mod` to `posts` table
- [ ] Add `is_admin` to `users` table

**Infrastructure:**
- [ ] Redis installed and running (required for rate limiting in production)
- [ ] rq worker process configured (`rq worker --with-scheduler`)
- [ ] FCM credentials set if push notifications enabled

**Security:**
- [ ] Confirm admin endpoints are rate-limited
- [ ] Confirm admin actions are written to `security_logs`
- [ ] DM content does not appear in search results

**Testing:**
- [ ] All 57+ new Phase 6 tests passing
- [ ] Rate limiting tested end-to-end
- [ ] Search tested with bilingual queries (FR + EN)
- [ ] Admin workflow tested with a test admin account

---

## 📚 DOCUMENTATION TO CREATE

- [x] `SEARCH_API_GUIDE.md` — Query syntax, type filters, privacy rules
- [x] `MESSAGING_GUIDE.md` — DM system, conversation model, read receipts
- [x] `MODERATION_GUIDE.md` — Report workflow, admin actions, auto-flag rules
- [x] `RATE_LIMITING_GUIDE.md` — Limits per endpoint, Redis setup, custom key functions
- [x] Updated `ARCHITECTURE_DECISIONS.md` — AD-051 to AD-055

---

## 📅 DEVELOPMENT TIMELINE

### Week 1: Phase 6A (Must Have)
**Days 1–2:** Search API  
**Days 3–4:** Discovery & Trending feeds  
**Day 5:** Rate limiting

### Week 2: Phase 6B (Should Have)
**Days 6–7:** Moderation & reporting  
**Days 8–10:** Direct messaging  
**Day 11:** Zone feed upgrade

### Week 3: Phase 6C (Nice to Have)
**Days 12–13:** Push notification infrastructure  
**Day 14:** Caching layer  
**Days 15–16:** Background job queue + documentation

---

## ✨ SUCCESS CRITERIA

**Phase 6 Complete When:**
- [x] Unified search endpoint with privacy rules enforced
- [x] Discovery and trending feeds replace the empty-follow-list problem
- [x] Rate limiting active on all auth and write endpoints
- [x] Report system operational with admin review workflow
- [x] Direct messaging fully functional with unread counts
- [ ] All 57+ new tests passing
- [ ] No regression in Phase 1–5 tests (113 still green)
- [ ] Documentation complete for all new systems

---

## 📝 DEVELOPMENT NOTES

**Frontend Independence:** Every endpoint in this phase is usable via `curl` or Postman immediately after implementation. The frontend team can wire them in asynchronously. Share the endpoint table above with your frontend developer as a handoff contract.

**Suggested dev order within each component:** Model → Migration script → Route → Tests → Documentation. Never skip the migration script — schema changes committed without a migration file cause pain for every future collaborator.

**Privacy audit reminder:** Before marking any component complete, verify: (1) anonymous posts cannot be identified through the new endpoint, (2) private-profile users are excluded from search/discovery, (3) deactivated users are fully invisible. These three checks should be in every test suite.

---

**Last Updated:** 2026-03-15 (Phase 6 initial planning)  
**Status:** 🔵 Planning — Ready to begin Phase 6A  
**Confidence:** ✅ High — All components are backend-only and frontend-independent  
**Blockers:** None — Phase 6 can begin immediately

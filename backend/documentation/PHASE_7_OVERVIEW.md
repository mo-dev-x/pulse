# 🧩 PHASE 7 OVERVIEW — BACKEND FEATURES IMPLEMENTED BUT NOT DOCUMENTED

**Pulse Backend — Documentation Gap-Fill (Post Phase 6)**

**Status:** Implemented (in code), undocumented  
**Scope:** Backend-only features present in `backend/app/` but missing from existing phase docs / technical guides  

> This document intentionally covers **only** features that are implemented but **not** documented elsewhere. It does not restate Phase 1–6 systems.

---

## ✅ 7A — Mood Check-Ins (Lightweight “How are you feeling?”)

### Feature
**Mood check-ins** let a user record a simple emotion for the day without creating a post. The backend can compute a daily campus-wide distribution (“Pulse”) from these check-ins.

### How it works (high-level)
- A check-in stores `(user_id, emotion, checked_at)` in `mood_checkins`.
- The API enforces a **12-hour cooldown** between check-ins to reduce spam and re-submissions.
- “Pulse” aggregates **today’s** check-ins by emotion and returns a distribution + dominant emotion.

### Endpoints
- `POST /api/mood/checkin`
  - **Auth:** JWT required
  - **Body:** `{ "emotion": "joy" }`
  - **Valid emotions:** `joy | sadness | anger | fear | disgust | surprise | neutral`
  - **Cooldown behavior:** returns `429` with `retry_after` seconds when within cooldown window.

- `GET /api/mood/pulse`
  - **Auth:** JWT required
  - **Returns:** `{ dominant, distribution, total, user_emotion, cooldown_seconds }`

### Relevant code
- **Route:** `backend/app/routes/mood.py`
- **Model:** `backend/app/models/mood_checkin.py`

### Notes / constraints
- **Cooldown is per-user** and currently based on the most recent check-in within the last 12 hours.
- “Pulse” is computed from the `mood_checkins` table (separate from post sentiment analytics).

---

## ✅ 7B — Generic Cloudinary Upload Endpoint (Media URL Pre-Upload)

### Feature
A **generic authenticated upload endpoint** for sending a file and receiving a **Cloudinary URL** that can be referenced later in posts/messages/etc.

### How it works (high-level)
- Accepts `multipart/form-data` with a single `file` field.
- Validates extension + enforces a **10 MB** hard limit.
- Uploads to Cloudinary using `resource_type="auto"` so images + audio are supported.
- Returns `{ "url": "<secure_url>" }`.
- If Cloudinary is not configured, returns `503` (media storage unavailable).

### Endpoint
- `POST /api/upload`
  - **Auth:** JWT required
  - **Form field:** `file`
  - **Allowed extensions:**
    - Images: `png, jpg, jpeg, gif, webp`
    - Audio: `webm, ogg, mp4, m4a, wav, opus`
  - **Errors:**
    - `400`: missing file / unsupported extension
    - `413`: file too large
    - `503`: Cloudinary not configured

### Relevant code
- **Route:** `backend/app/routes/uploads.py`
- **Cloudinary helper:** `backend/app/utils/cloudinary_utils.py`

### Notes / constraints
- This endpoint is **Cloudinary-only** (no local-disk fallback by design).
- Cloudinary credentials are read from config keys:
  - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

---

## ✅ 7C — Cloudinary Storage Behavior Across Existing Upload Flows (Fallback + URL Storage)

### Feature
Existing upload flows now support **Cloudinary as the preferred storage backend**, with a **local-disk fallback** (development-friendly) for some endpoints.

### How it works (high-level)
- When Cloudinary is configured:
  - profile/header images are resized (when Pillow is available) and uploaded to Cloudinary
  - posts and DM media/audio upload streams go directly to Cloudinary (no disk write)
  - returned values are **full secure URLs** stored directly in user/media/message fields
- When Cloudinary is not configured:
  - profile/header images fall back to writing under `uploads/`
  - post image uploads and DM audio/image uploads fall back to writing under `UPLOAD_FOLDER`

### Relevant endpoints (implemented elsewhere, but Cloudinary behavior is undocumented)
- `POST /api/auth/upload-profile-pic`
- `POST /api/auth/upload-header`
- `POST /api/posts` (multipart `image` field)
- `POST /api/messages/conversations/<id>/audio` (multipart `audio` field)
- `POST /api/messages/conversations/<id>/media` (multipart `media` field)

### Relevant code
- **Cloudinary helper:** `backend/app/utils/cloudinary_utils.py`
- **Auth uploads:** `backend/app/routes/auth.py`
- **Post upload:** `backend/app/routes/posts.py`
- **DM uploads:** `backend/app/routes/messages.py`

### Notes / constraints
- DM `/media` currently accepts **images only** (video is rejected) even though the message prefix convention supports `[video]...`.
- Post creation stores both `Media.file_path` (legacy) and `Media.media_url` (Cloudinary URL) when available.

---

## ✅ 7D — Direct Messages: Replies + “Unsend” (Message Delete)

### Feature
Direct messages now support:
- **Reply metadata** (link to a prior message + a snapshot preview for quoting)
- **Message deletion (“unsend”)** by the original sender

### How it works (high-level)
#### Reply metadata
- `send_message` accepts optional `reply_to_id` and `reply_preview`.
- The backend validates `reply_to_id` belongs to the same conversation.
- It stores:
  - `messages.reply_to_id` (FK to `messages.id`)
  - `messages.reply_preview` (up to 255 chars) so the UI can render a quote without an extra lookup.

#### Message delete (“unsend”)
- Only the sender can delete their own message.
- Deletion is scoped to a conversation and message id.

### Endpoints
- `POST /api/messages/conversations/<conversation_id>`
  - **Body (optional fields):**
    - `reply_to_id` (int)
    - `reply_preview` (string; optional; server truncates to 255)

- `DELETE /api/messages/conversations/<conversation_id>/messages/<message_id>`
  - **Auth:** JWT required
  - **Rules:**
    - `404` if not found / not in conversation
    - `403` if requester is not the sender
    - `200` with `{ "deleted": true }` on success

### Relevant code
- **Routes:** `backend/app/routes/messages.py`
- **Model fields:** `backend/app/models/message.py`

### Notes / constraints
- Reply metadata is **non-threaded** (one hop) and is intended for simple quote rendering, not nested threads.

---

## ✅ 7E — Bootstrap & Operational Patterns Introduced in App Startup

### Feature
Several operational behaviors exist in the app factory but are not documented as architecture decisions or runbook notes.

### What happens at startup (high-level)
- **Production:** calls `setup_database()` during app init (Railway-focused) to ensure schema presence.
- Applies a small set of **idempotent “lightweight migrations”** on boot (currently adds DM reply columns and `media.media_url`).
- JWT blocklist checks are backed by DB sessions but include a **30-second cache** for known-valid JTIs to reduce DB load.
- Rate limiting supports a **per-user key function** (prefer JWT identity, else remote IP) for write endpoints.

### Relevant code
- `backend/app/__init__.py`

### Notes / constraints
- The boot-time migration pattern is intentionally minimal: additive-only, “best effort”, no destructive changes.

---

## Frontend Additions

> This section documents frontend behaviors implemented in `Frontend/` that are not captured in the existing frontend phase documents (F1–F6), but materially affect product UX and system behavior.

### 1) Global shell helpers (shared UX + resilience)
**What it does:** Standardizes the app “shell” across authenticated pages (theme, offline state, error surfacing, unread badges).

**How it behaves (high-level):**
- Theme: toggles `data-theme` (dark/light) with persistence in `localStorage` (`pulse_theme`) and system preference support.
- Offline banner: shows/hides an `#offlineBanner` element on `online/offline` events.
- Global error handling: converts `unhandledrejection` into an error toast (ignores `AbortError`).
- Accessibility: auto-injects a “Skip to main content” link and creates an ARIA live toast container when missing.
- Unread badges: polls unread message/notification counts and updates any `[data-message-badge]` / `[data-notification-badge]` nodes.

**Relevant logic:**
- `Frontend/js/theme.js` (`initThemeToggle`, `initOfflineBanner`, `initGlobalErrorHandler`, `initUnreadBadges`)
- `Frontend/js/bus.js` — in-page event bus to refresh unread badges immediately after mark-as-read
- `Frontend/js/notify.js` — toast helpers (`notify`, `runAsyncUI`)

**Notes / constraints:**
- Unread badge refresh is resilient by design (silently ignores failures).
- Event bus is **in-page only** (not cross-tab).

### 2) Feed rendering strategy: targeted re-render, not full list replacement
**What it does:** Keeps feed interactions responsive by updating **only the affected post** rather than rebuilding the entire feed DOM.

**How it behaves (high-level):**
- Maintains in-memory state (`currentPosts`, `bookmarkedPostIds`, `expandedComments`, `commentsCache`).
- Optimistic updates for reactions and bookmarks update state first, then call the API, then reconcile counts with server response or rollback.
- Comments are cached per post; expanding a thread reuses cache unless a refresh is requested.

**Relevant logic:** `Frontend/js/feed.js` (`onReact`, `toggleBookmark`, `toggleComments`, `loadCommentsForPost`, `rerenderPost`)

**Notes / constraints:**
- This pattern reduces flicker (especially for media) and supports smoother infinite scrolling.

### 3) Direct messages: smooth polling + optimistic sends + reply/quote UX
**What it does:** Makes DMs feel “chat-like” without WebSockets.

**How it behaves (high-level):**
- Smooth polling: polls every 5 seconds but **only updates the DOM when new messages arrive**, and appends only new bubbles to avoid re-render flicker.
- Optimistic sends:
  - Text: appends a temporary “Sending…” bubble immediately.
  - Images: shows an instant local preview via `URL.createObjectURL()` while upload is in-flight.
  - Audio: records with `MediaRecorder`, shows a temporary sending state, uploads the blob.
- Reply UX:
  - Each bubble has a reply affordance.
  - The reply context is rendered as a quote block above the outgoing message.
  - Supports both structured `reply_preview` and legacy inline `↩ preview\ncontent` prefix parsing.
- Unsend: sender can delete a message, with immediate UI removal and a forced re-sync on next poll.

**Relevant logic:** `Frontend/js/messages.js`

**Notes / constraints:**
- Polling uses guards to prevent overlapping requests on slow networks.
- Media in DMs is currently **images only** in the UI (video upload is blocked before sending).

### 4) Notifications: grouped timeline + optimistic actions
**What it does:** Provides an Instagram-style notification centre experience.

**How it behaves (high-level):**
- Groups notifications into **Today / This week / Earlier** sections based on `created_at`.
- Optimistic “mark all read”: flips UI state immediately, fires API call in background.
- Optimistic delete: removes a row immediately and cleans up empty sections; API call is fire-and-forget.
- Single delegated click handler prevents listener accumulation.

**Relevant logic:** `Frontend/js/notifications.js`

### 5) PWA behaviors: install banner, service worker caching, and push handling
**What it does:** Adds offline resilience and an installable “app-like” experience.

**How it behaves (high-level):**
- Install prompt: listens for `beforeinstallprompt`, shows a banner after a short delay, persists dismissal.
- Web Push subscription:
  - Fetches VAPID public key from backend and silently no-ops if unavailable.
  - Subscribes via `PushManager` and syncs to backend (`/api/push/subscribe`) as `{ platform: "web", token: "<subscription JSON>" }`.
- Service worker:
  - Static assets: cache-first
  - API (`/api/*`): network-first with cached fallback
  - Navigation: network-first with `offline.html` fallback
  - Handles `push` events and navigates on notification click.

**Relevant logic:**
- `Frontend/js/pwa.js`
- `Frontend/sw.js`
- `Frontend/offline.html`, `Frontend/manifest.json`


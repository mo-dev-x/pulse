# 🫀 PULSE FRONTEND — PROJECT TRACKER

**Last Updated:** 2026-04-08
**University:** Université Laval  
**Project:** Pulse Frontend (Privacy-First Campus Wellness Platform)  
**Tech Stack:** Vanilla JavaScript (ES Modules) + HTML5 + CSS3  
**Languages:** Bilingual (French/English)  
**Email Domain:** @ulaval.ca  
**Backend API:** Flask REST API (Phases 1–6 ✅ Complete)

---

## 📊 PROJECT STATUS OVERVIEW

| Phase | Name | Status | Completion |
|-------|------|--------|------------|
| **Phase F1** | Foundation & Auth Shell | ✅ Implemented | ~95% |
| **Phase F2** | Feed, Posts & Interactions | ✅ Implemented | ~95% |
| **Phase F3** | Profile, Social & Following | ✅ Implemented | ~95% |
| **Phase F4** | Campus Mood & Analytics | ✅ Implemented | ~95% |
| **Phase F5** | Notifications, DMs & Settings | ✅ Implemented | ~95% |
| **Phase F6** | Search, Discovery & Polish | ✅ Implemented | ~95% |

**Overall Frontend Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜ ~95%

---

## 🏗️ TECH STACK DECISIONS

| Concern | Choice | Rationale |
|---------|--------|-----------|
| **Framework** | Vanilla JS (ES Modules) | No build step, works directly in browser, existing codebase |
| **Styling** | CSS custom properties + BEM | Consistent theming, bilingual-safe, no framework lock-in |
| **Auth** | JWT in `localStorage` | Existing `auth.js` pattern — `apiFetch()` wrapper already built |
| **Routing** | Hash-based SPA (`#feed`, `#profile`) | No server config needed for static host |
| **i18n** | `lang` attribute + JS locale module | Mirrors backend `i18n.py` — FR default, EN toggle |
| **Charts** | Chart.js (CDN) | Lightweight, no build step, good bilingual support |
| **Bundler** | None | Vanilla ES Modules — `type="module"` in `<script>` tags |

---

## 📁 TARGET FILE STRUCTURE

```
Frontend/
├── index.html                  # SPA shell / router
├── login.html                  # Auth — Login page
├── register.html               # Auth — Registration page
├── feed.html                   # Main feed
├── profile.html                # User profile page
├── zone.html                   # Zone/campus area page
├── analytics.html              # Campus mood dashboard
├── search.html                 # Unified search page
├── discover.html               # Discovery feed
├── messages.html               # Direct messages
├── notifications.html          # Notification centre
├── settings.html               # Account settings + 2FA
│
├── css/
│   ├── variables.css           # Design tokens (colours, spacing, typography)
│   ├── base.css                # Reset + global styles
│   ├── components.css          # Reusable components (cards, buttons, modals)
│   ├── login.css               # Auth pages (existing, extend)
│   ├── feed.css                # Feed layout (existing, extend)
│   ├── profile.css             # Profile page
│   ├── analytics.css           # Charts + mood widgets
│   ├── messages.css            # DM thread layout
│   └── notifications.css       # Notification list
│
└── js/
    ├── auth.js                 # Token helpers + apiFetch (existing, extend)
    ├── login.js                # Login page logic (existing)
    ├── register.js             # Registration logic (existing)
    ├── feed.js                 # Feed + post composer (existing, major extend)
    ├── profile.js              # Profile page + follow actions
    ├── zone.js                 # Zone feed + zone autocomplete
    ├── analytics.js            # Campus mood charts
    ├── messages.js             # DM conversations + polling
    ├── notifications.js        # Notification list + badge
    ├── settings.js             # Account settings + 2FA setup
    ├── search.js               # Search bar + results
    ├── discover.js             # Discovery feed + trending zones
    ├── theme.js                # Theme persistence + offline banner
    ├── zone_autocomplete.js    # Zone picker (existing)
    ├── i18n.js                 # FR/EN locale strings
    └── router.js               # Hash-based client-side routing
```

---

## 🎨 DESIGN SYSTEM

> **Note:** The default design direction remains glassmorphism, with dark and light theme token support implemented.

### Colour Palette (as implemented in `feed.css` / `login.css`)

#### Feed / App Shell (`feed.css`)

| CSS Variable | Value | Usage |
|---|---|---|
| `--bg` | `#05060d` | Page background |
| `--panel` | `rgba(20, 18, 33, 0.72)` | Glass cards / panels |
| `--panel2` | `rgba(20, 18, 33, 0.88)` | Modal / menu backgrounds |
| `--border` | `rgba(255,255,255,0.08)` | Panel borders |
| `--text` | `rgba(255,255,255,0.92)` | Primary text |
| `--muted` | `rgba(255,255,255,0.60)` | Secondary / muted text |
| `--accent` | `#ff4d7d` | CTA buttons, active states, Pulse brand |
| `--accent2` | `#ff6aa1` | Button gradient end, hover tint |
| `--radius` | `18px` | Default border radius |

**Background gradient** (fixed layer on `body::before`):
- Purple glow: `rgba(124, 58, 237, 0.22)` at top-left
- Pink glow: `rgba(255, 77, 125, 0.18)` at top-right
- Blue glow: `rgba(59, 130, 246, 0.10)` at bottom-center
- Base: `linear-gradient(180deg, #05060d → #070816 → #05060d)`

**Sentiment badge border colours** (`.badge.green / .yellow / .red`):
- Positive: `rgba(34,197,94,0.35)`
- Neutral: `rgba(234,179,8,0.35)`
- Negative: `rgba(239,68,68,0.35)`

#### Auth Pages (`login.css`)

| Property | Value | Usage |
|---|---|---|
| Body background | `#0b1220` + radial gradients | Deep navy base |
| Gradient 1 | `#1d4ed8` (blue) at 20% 10% | Left radial glow |
| Gradient 2 | `#9333ea` (purple) at 90% 20% | Right radial glow |
| Login button | `#2563eb` | Primary action |
| Checkbox accent | `#60a5fa` | Remember me checkbox |
| Link colour | `#93c5fd` | "Register" / "Forgot" links |
| Error text | `#fca5a5` | Inline field errors |
| Text colour | `#e5e7eb` | Body text |

### Typography

- **Font (actual):** `system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif` (same in both `feed.css` and `login.css`)
- **Scale (planned):** 12 / 14 / 16 / 18 / 24 / 32 / 48px
- **Bilingual note:** All font sizes must accommodate French text (typically 15–20% longer than English)

### Emotion Colours (Phase F4 — used in analytics charts)

| Emotion | Colour | Usage |
|---------|--------|-------|
| Joy | `#FFD93D` | 🌟 |
| Sadness | `#74B9FF` | 💙 |
| Anger | `#E74C3C` | 🔴 |
| Fear | `#A29BFE` | 💜 |
| Surprise | `#FD79A8` | 🌸 |
| Disgust | `#55EFC4` | 🌿 |

---

## 📋 PHASE TASK SUMMARY

### Phase F1 — Foundation & Auth Shell
- [x] Design token CSS (`variables.css`) ✅
- [x] Base reset + typography (`base.css`) ✅
- [x] Bilingual i18n module (`i18n.js`) — FR/EN with toggle ✅
- [x] `auth.js` — token helpers + `apiFetch()` wrapper ✅
- [x] Extend `auth.js` — 401 handling + auth state cleanup ✅
- [x] Login page (`login.html` + `login.js` + `login.css`) — validation, error states ✅
- [x] Registration page (`register.html` + `register.js`) — @ulaval.ca email enforcement ✅
- [x] Email verification waiting screen (`verify-email.html`) ✅
- [x] Password reset flow (`forgot-password.html` + `reset-password.html`) ✅
- [x] Hash router (`router.js`) ✅

### Phase F2 — Feed, Posts & Interactions
- [x] Feed page structure (`feed.html`) — topbar, sidebar, main column, right panel ✅
- [x] Feed CSS (`feed.css`) — full glassmorphism dark theme, responsive grid ✅
- [x] Feed JS (`feed.js`) — posts loading, auth guard, logout ✅
- [x] Post card component — author label, zone, timestamp, sentiment badge ✅
- [x] Post composer modal — text, zone picker, anonymous toggle, image upload field ✅
- [x] Character counter in composer ✅
- [x] Zone autocomplete (`zone_autocomplete.js`) ✅
- [x] Search bar UI (topbar) ✅
- [x] Loading / empty state (`#stateBox`) ✅
- [x] Infinite scroll / pagination ✅
- [x] Reaction picker — `+` trigger button, animated popup on click, global dismiss ✅
- [x] Comment thread — nested display, submit ✅
- [x] Bookmark toggle ✅
- [x] Delete own post UI wired (`feed.js`) ✅
- [x] Image upload wired in composer via `FormData` ✅
- [x] Email verification banner — shown to unverified users; intercepts post/comment buttons ✅
- [x] Mobile hamburger drawer — slide-in nav, overlay backdrop, links to all pages ✅

### Phase F3 — Profile, Social & Following
- [x] Profile page (`profile.html` + `profile.js` + `profile.css`) — structured and data-wired ✅
- [x] Public profile page — posts, bio, follower/following counts, pinned post ✅
- [x] Own profile — edit display name, bio, avatar ✅
- [x] Follow / unfollow button wired ✅
- [x] Followers / Following lists modal ✅
- [x] Friends list (mutual follows) ✅
- [x] Zone autocomplete in post composer ✅
- [x] Zone feed page (`zone.html` + `zone.js`) ✅

### Phase F4 — Campus Mood & Analytics
- [x] Campus mood overview widget ✅
- [x] Daily mood trend chart (Chart.js line chart) ✅
- [x] Weekly mood trend chart ✅
- [x] Per-zone mood breakdown ✅
- [x] Emotion breakdown donut chart (joy / sadness / anger / fear…) ✅
- [x] Privacy threshold notice (< 10 posts = no data shown) ✅
- [x] Zone activity feed via `/api/zones/<id>/activity` ✅

### Phase F5 — Notifications, DMs & Settings
- [x] Notification centre — Instagram-style, grouped (Today/This week/Earlier), type icons (reaction/comment/follow/mention), mark read, delete ✅
- [x] DM conversation list ✅
- [x] DM thread view — text, images, videos, voice messages, read receipts ✅
- [x] DM smooth polling — DOM only updates when new messages arrive (no flash) ✅
- [x] Unread DM badge in nav ✅
- [x] Settings page — display name, bio, avatar, language preference ✅
- [x] Settings — anonymous pseudonym management (change with 90-day cooldown, live UI) ✅
- [x] Security settings — change password, active sessions, revoke sessions ✅
- [x] 2FA setup — QR code display, TOTP verify, backup codes ✅
- [x] Push notification permission request (browser) ✅

### Phase F6 — Search, Discovery & Polish
- [x] Search bar UI in topbar ✅
- [x] Search results wired via unified `GET /api/search` ✅
- [x] Search results page with type tabs ✅
- [x] @mention autocomplete in composer + comments ✅
- [x] Discovery feed page (trending content) ✅
- [x] Trending zones widget ✅
- [x] Dark mode toggle + persistence ✅
- [x] Accessibility audit (WCAG 2.1 AA) ✅
- [x] Loading skeletons for all feeds ✅
- [x] Empty states (bilingual, illustrated) ✅
- [x] Error boundaries + offline state ✅

### PWA & Platform Polish (post-F6)
- [x] Web App Manifest (`manifest.json`) — install prompt, shortcuts, icons ✅
- [x] Service Worker (`sw.js`) — cache-first for static assets, network-first for API, offline fallback page ✅
- [x] Real Web Push notifications via VAPID/pywebpush — OS-level notifications even when app is closed ✅
- [x] In-app install banner (`pwa.js`) — `beforeinstallprompt` with persistent dismiss ✅
- [x] Push subscription flow — requests permission, syncs to `/api/push/subscribe` ✅
- [x] SW push handler — shows OS notification, click navigates to correct page ✅
- [x] Skip-to-content link auto-injected on all pages via `initThemeToggle()` ✅
- [x] Toast container auto-injected on any page missing one ✅
- [x] Global unhandled rejection handler (`initGlobalErrorHandler()`) shows error toasts ✅
- [x] `loading="lazy"` on all dynamically-rendered `<img>` tags across all JS modules ✅
- [x] Mobile long-press (500ms touch-and-hold) on own DM bubbles opens delete menu ✅
- [x] Zone sidebar populated with live post count, type, and description ✅
- [x] Discover page: infinite scroll via IntersectionObserver with `?page=` pagination ✅
- [x] Mobile drawer added to discover and zone pages ✅
- [x] Share profile uses `FRONTEND_ORIGIN` — blocked with toast on localhost ✅
- [x] `vercel.json` headers: `sw.js` served `no-cache` + `Service-Worker-Allowed: /` ✅

---

## 🔗 BACKEND API REFERENCE (All Endpoints Available)

All 74+ backend endpoints are live. Key ones for frontend:

| Frontend Feature | Method | Endpoint |
|-----------------|--------|----------|
| Register | POST | `/api/auth/register` |
| Login | POST | `/api/auth/login` |
| Logout | POST | `/api/auth/logout` |
| Own profile | GET | `/api/users/me` |
| Feed | GET | `/api/posts/feed` |
| Create post | POST | `/api/posts` |
| Discovery feed | GET | `/api/posts/discover` |
| Trending | GET | `/api/posts/trending` |
| React to post | POST | `/api/posts/<id>/react` |
| Comments | GET/POST | `/api/posts/<id>/comments` |
| Bookmark | POST | `/api/posts/<id>/bookmark` |
| Follow user | POST | `/api/follow/@<username>` |
| Public profile | GET | `/api/users/@<username>` |
| Search | GET | `/api/search` |
| Analytics daily | GET | `/api/analytics/daily` |
| Analytics campus | GET | `/api/analytics/campus` |
| Notifications | GET | `/api/notifications` |
| DM conversations | GET | `/api/messages/conversations` |
| Send DM (text) | POST | `/api/messages/conversations/<id>` |
| Send DM (audio) | POST | `/api/messages/conversations/<id>/audio` |
| Send DM (media) | POST | `/api/messages/conversations/<id>/media` |
| Mark DM read | PATCH | `/api/messages/conversations/<id>/read` |
| Update pseudonym | PATCH | `/api/auth/update-pseudonym` |
| Sessions | GET | `/api/sessions` |
| 2FA setup | POST | `/api/auth/2fa/setup` |
| Push subscribe | POST | `/api/push/subscribe` |

---

## 📈 METRICS TARGETS

| Metric | Start | Target (F6 Complete) |
|--------|-------|----------------------|
| Pages / Views | 15 (`index`, `login`, `register`, `verify-email`, `forgot-password`, `reset-password`, `feed`, `profile`, `zone`, `analytics`, `notifications`, `messages`, `settings`, `search`, `discover`) | 15+ |
| JS Modules | 20 (`auth`, `api`, `i18n`, `router`, `theme`, `login`, `register`, `verify_email`, `forgot_password`, `reset_password`, `feed`, `profile`, `zone`, `zone_autocomplete`, `analytics`, `notifications`, `messages`, `settings`, `search`, `discover`) | 15+ |
| CSS Files | 9 (`variables`, `base`, `components`, `login`, `feed`, `profile`, `analytics`, `messages`, `notifications`) | 9 |
| Bilingual Coverage | Partial | 100% |
| Lighthouse Score | — | ≥ 90 (Perf + A11y) |
| WCAG | — | 2.1 AA |

---

## 🛠️ EXISTING FRONTEND FILES

| File | Status | Notes |
|------|--------|-------|
| `login.html` / `login.css` / `login.js` | ✅ Working | JWT login, remember-me token storage, error/success UI, password toggle |
| `register.html` / `register.js` | ✅ Working | @ulaval.ca enforced, username + password validation, backend errors shown |
| `verify-email.html` / `verify_email.js` | ✅ Working | Verification wait screen + resend flow |
| `forgot-password.html` / `forgot_password.js` | ✅ Working | Password reset request flow |
| `reset-password.html` / `reset_password.js` | ✅ Working | Password reset confirm flow |
| `feed.html` | ✅ Working | Full layout: topbar (with mobile hamburger), sidebar, composer, feed, right panel, create modal, mobile slide-in drawer |
| `feed.css` | ✅ Working | Full glassmorphism dark theme, responsive breakpoints, reaction popup, verification banner, mobile drawer |
| `feed.js` | ✅ Working | Interest-based feed, pagination, comments, bookmarks, emoji reaction popup, create post, image upload, delete, verification banner intercept, mobile drawer |
| `profile.html` / `profile.js` / `profile.css` | ✅ Working | Public/own profile views, edit profile modal, follow/unfollow, followers/following/friends modals |
| `zone.html` / `zone.js` | ✅ Working | Zone feed page + zone lookup |
| `analytics.html` / `analytics.css` / `analytics.js` | ✅ Working | Campus mood hero, charts, zone breakdown, privacy notice, zone activity details |
| `notifications.html` / `notifications.css` / `notifications.js` | ✅ Working | Instagram-style: grouped by time, type icons, mark read, mark all read, delete |
| `messages.html` / `messages.css` / `messages.js` | ✅ Working | Conversation list, thread view, text/image/video/voice messages, smooth polling |
| `settings.html` / `settings.js` | ✅ Working | Profile/preferences/security tabs, avatar upload, pseudonym management, change password, sessions, 2FA, push permission |
| `search.html` / `search.js` | ✅ Working | Unified search page with tabs, paging, search skeletons, mention autocomplete helper used by composer/comments |
| `discover.html` / `discover.js` | ✅ Working | Discovery feed with sentiment filter + trending zones sidebar |
| `auth.js` | ✅ Working | Token helpers, 401 auth cleanup, language-aware API requests |
| `theme.js` | ✅ Working | Theme persistence, toggle, offline banner, skip link + toast injection, global error handler |
| `pwa.js` | ✅ Working | Install prompt banner, Web Push subscription (VAPID) |
| `zone_autocomplete.js` | ✅ Working | Integrated into post composer modal |
| `i18n.js` / `router.js` | ✅ Working | Language toggles + index hash router |
| `api.js` | ⚠️ Empty | Placeholder file |
| `manifest.json` | ✅ Working | PWA manifest — name, icons, display:standalone, shortcuts |
| `sw.js` | ✅ Working | Service worker: cache-first static, network-first API, push handler, offline fallback |
| `offline.html` | ✅ Working | Offline fallback page served by SW when navigation fails |

---

## 📚 DOCUMENTATION TO CREATE

| Document | Phase | Purpose |
|----------|-------|---------|
| `FRONTEND_QUICKSTART.md` | F1 | Dev setup, how to run locally |
| `DESIGN_SYSTEM.md` | F1 | Colours, typography, components |
| `I18N_GUIDE.md` | F1 | How to add translations, key conventions |
| `COMPONENT_GUIDE.md` | F2 | Reusable component patterns |
| `ANALYTICS_DISPLAY_GUIDE.md` | F4 | Chart config, privacy threshold UI |

---

**📌 Remember:** Update this tracker after every completed phase!

**Backend Status:** ✅ All 6 phases complete — 74+ endpoints available + VAPID push  
**Frontend Status:** ✅ All phases complete + PWA — installable, offline-capable, push-enabled
**Last Updated:** 2026-04-08
**Next Milestone:** Translation coverage expansion, in-browser accessibility verification, and regression testing

**📝 Note:** All frontend architecture decisions will be documented in `FRONTEND_ARCHITECTURE_DECISIONS.md` as they are made.

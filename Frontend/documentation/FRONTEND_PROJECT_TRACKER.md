# 🫀 PULSE FRONTEND — PROJECT TRACKER

**Last Updated:** 2026-03-16  
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
| **Phase F1** | Foundation & Auth Shell | 🟡 In Progress | ~65% |
| **Phase F2** | Feed, Posts & Interactions | 🟡 In Progress | ~30% |
| **Phase F3** | Profile, Social & Following | 🟡 In Progress | ~20% |
| **Phase F4** | Campus Mood & Analytics | 🔵 Planning | 0% |
| **Phase F5** | Notifications, DMs & Settings | 🔵 Planning | 0% |
| **Phase F6** | Search, Discovery & Polish | 🔵 Planning | 0% |

**Overall Frontend Progress:** 🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜ ~25%

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
    ├── post.js                 # Post card component + reactions
    ├── profile.js              # Profile page + follow actions
    ├── zone.js                 # Zone feed + zone autocomplete
    ├── analytics.js            # Campus mood charts
    ├── messages.js             # DM conversations + polling
    ├── notifications.js        # Notification list + badge
    ├── settings.js             # Account settings + 2FA setup
    ├── search.js               # Search bar + results
    ├── zone_autocomplete.js    # Zone picker (existing)
    ├── i18n.js                 # FR/EN locale strings
    └── router.js               # Hash-based client-side routing
```

---

## 🎨 DESIGN SYSTEM

> **Note:** The design is dark-only (glassmorphism). No light mode palette is implemented yet.

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

### Emotion Colours (Phase F4 — planned, not yet implemented)

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
- [ ] Design token CSS (`variables.css`) ⚠️ *tokens currently inline in `feed.css` `:root`*
- [ ] Base reset + typography (`base.css`) ⚠️ *reset currently inline in `feed.css`*
- [ ] Bilingual i18n module (`i18n.js`) — FR/EN with toggle
- [x] `auth.js` — token helpers + `apiFetch()` wrapper ✅
- [ ] Extend `auth.js` — refresh token handling, 401 interceptor
- [x] Login page (`login.html` + `login.js` + `login.css`) — validation, error states ✅
- [x] Registration page (`register.html` + `register.js`) — @ulaval.ca email enforcement ✅
- [ ] Email verification waiting screen
- [ ] Password reset flow (request + confirm)
- [ ] Hash router (`router.js`)

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
- [ ] Infinite scroll / pagination
- [ ] Reaction picker (10 emojis) — privacy-safe (only counts shown)
- [ ] Comment thread — nested display, submit
- [ ] Bookmark toggle
- [ ] Delete own post (with 24h guard) ⚠️ *API exists, UI not wired*
- [ ] Image upload — file input present in modal, backend wiring pending

### Phase F3 — Profile, Social & Following
- [x] Profile page (`profile.html` + `profile.js` + `profile.css`) — basic structure exists ✅
- [ ] Public profile page — posts, bio, follower counts (full wiring pending)
- [ ] Own profile — edit display name, bio, avatar, profile visibility
- [ ] Follow / unfollow button with optimistic UI
- [ ] Followers / Following lists (modal or page)
- [ ] Friends list (mutual follows)
- [x] Zone autocomplete in post composer ✅

### Phase F4 — Campus Mood & Analytics
- [ ] Campus mood overview widget
- [ ] Daily mood trend chart (Chart.js line chart)
- [ ] Weekly mood trend chart
- [ ] Per-zone mood breakdown
- [ ] Emotion breakdown donut chart (joy / sadness / anger / fear…)
- [ ] Privacy threshold notice (< 10 posts = no data shown)
- [ ] Zone activity feed (`/api/zones/<id>/activity`)

### Phase F5 — Notifications, DMs & Settings
- [ ] Notification centre — list, mark read, badge count
- [ ] DM conversation list
- [ ] DM thread view — send, receive, read receipts
- [ ] Unread DM badge in nav
- [ ] Settings page — display name, bio, avatar, language preference
- [ ] Security settings — change password, active sessions, revoke sessions
- [ ] 2FA setup — QR code display, TOTP verify, backup codes
- [ ] Push notification permission request (browser)

### Phase F6 — Search, Discovery & Polish
- [x] Search bar UI in topbar ✅
- [ ] Search results wired to `GET /api/search`
- [ ] Search results page with type tabs
- [ ] @mention autocomplete in composer + comments
- [ ] Discovery feed page (trending content)
- [ ] Trending zones widget
- [ ] Dark mode toggle + persistence ⚠️ *already dark-only, toggle not implemented*
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Loading skeletons for all feeds
- [ ] Empty states (bilingual, illustrated)
- [ ] Error boundaries + offline state

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
| Send DM | POST | `/api/messages/conversations/<id>` |
| Sessions | GET | `/api/sessions` |
| 2FA setup | POST | `/api/auth/2fa/setup` |
| Push subscribe | POST | `/api/push/subscribe` |

---

## 📈 METRICS TARGETS

| Metric | Start | Target (F6 Complete) |
|--------|-------|----------------------|
| Pages / Views | 3 (login, register, feed) | 10+ |
| JS Modules | 5 | 15+ |
| CSS Files | 2 | 9 |
| Bilingual Coverage | Partial | 100% |
| Lighthouse Score | — | ≥ 90 (Perf + A11y) |
| WCAG | — | 2.1 AA |

---

## 🛠️ EXISTING FRONTEND FILES

| File | Status | Notes |
|------|--------|-------|
| `login.html` / `login.css` / `login.js` | ✅ Working | JWT auth, error display, password toggle |
| `register.html` / `register.js` | ✅ Working | @ulaval.ca enforced, backend errors shown |
| `feed.html` | ✅ Working | Full layout: topbar, sidebar, composer, feed, right panel, create modal |
| `feed.css` | ✅ Working | Full glassmorphism dark theme, responsive breakpoints |
| `feed.js` | ✅ Working | Posts loading, auth guard, logout, search UI, reactions |
| `profile.html` / `profile.js` / `profile.css` | 🟡 Partial | Page exists, full wiring pending |
| `auth.js` | ✅ Working | Token helpers + `apiFetch()` — needs 401 interceptor + refresh |
| `zone_autocomplete.js` | ✅ Working | Integrated into post composer modal |
| `api.js` | ⚠️ Empty | Placeholder file |

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

**Backend Status:** ✅ All 6 phases complete — 74+ endpoints available  
**Frontend Status:** 🟡 Phase F1 ~65% · Phase F2 ~30% · Phase F3 ~20%  
**Last Updated:** 2026-03-18  
**Next Milestone:** Complete Phase F1 (i18n, 401 interceptor, hash router, email verification screen)

**📝 Note:** All frontend architecture decisions will be documented in `FRONTEND_ARCHITECTURE_DECISIONS.md` as they are made.

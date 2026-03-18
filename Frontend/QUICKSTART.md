# 🎯 PULSE FRONTEND — PROJECT TRACKER (Principessa)

| Info | Value |
|---|---|
| **Last Updated** | 2026-02-14 |
| **University** | Université Laval |
| **Project** | Pulse Frontend (Campus Wellness UI) |
| **Tech Stack** | HTML + CSS + JavaScript (ES Modules) |
| **Run Method** | `python3 -m http.server` |
| **Integration** | Flask REST API + JWT + CORS |
| **Backend URL** | http://127.0.0.1:5000 |
| **Frontend URL** | http://127.0.0.1:8000 |
| **JWT Storage Key** | `pulse_token` |

---

## ✅ Quick Facts

- ✅ ES Modules working via HTTP server (**not** `file://`)
- ✅ Token stored in LocalStorage key: `pulse_token`
- ✅ Backend base URL: http://127.0.0.1:5000

---

## 📊 Project Status Overview

| Phase | Status | Completion |
|---|---|---:|
| Phase 1: Frontend Foundation | ✅ Complete | 100% |
| Phase 2: Auth Integration (Login + Register + Token) | ✅ Complete | 100% |
| Phase 3: Feed UI (Layout + Components) | ✅ Complete | 100% |
| Phase 4: Feed API Integration (Posts) | 🟡 In Progress | ~60% |
| Phase 5: UX Polish (toasts/spinners/empty states) | 🔵 Later | 0% |
| Phase 6: Map + Mood Analytics UI | 🔵 Later | 0% |

**Overall Progress:** 🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜ **~60%**  
**Current Focus:** Feed API integration — posts loading and wiring reactions/comments to backend.

---

## 🗂️ Current Frontend Structure (as-is)

```text
Frontend/
  css/
    login.css
  js/
    auth.js
    login.js
    register.js
    api.js          (optional)
    config.js       (optional)
  login.html
  register.html
  feed.html
```

## ✅ Completed Tasks (What’s Done)

### ✅ Phase 1 — Frontend Foundation

* ✅ Frontend folder added to repository
* ✅ Global UI base (glass layout, inputs, buttons, error styling)
* ✅ ES Modules enabled (`type="module"`) and working via HTTP server
* ✅ Consistent design theme (calm supportive UI, blue/purple gradient background)

### ✅ Phase 2 — Auth Integration (Complete)

**Core helpers**

* ✅ `auth.js` created (token helpers + `apiFetch`)
* ✅ Token stored in `localStorage` under key: `pulse_token`

**Login**

* ✅ `POST /api/auth/login`
* ✅ Saves JWT → redirect to `feed.html`
* ✅ Displays backend error messages (invalid credentials, etc.)
* ✅ Password show/hide toggle

**Register**

* ✅ Frontend validation: email must end with `@ulaval.ca`
* ✅ `POST /api/auth/register`
* ✅ Displays backend validation errors (password rules, etc.)

**Manual verification**

* ✅ `localStorage.getItem("pulse_token")` returns JWT
* ✅ `GET /api/auth/me` works with `Authorization: Bearer <token>`
* ✅ Logout button implemented (clears token + redirects to login)

### ✅ Phase 3 — Feed UI (Complete)

* ✅ `feed.html` created — full page structure
* ✅ Topbar created (search bar, create button, user chip + menu)
* ✅ Sidebar created (profile panel + nav links + Create Post button)
* ✅ Middle feed section — posts list + post cards (author, zone, timestamp, sentiment badge)
* ✅ Post composer modal (text, char counter, zone picker, anonymous toggle, image upload)
* ✅ Right panel — messages section + follow requests section
* ✅ "Campus Pulse" stories card (neon ring, emotion tiles)
* ✅ Loading / empty state (`#stateBox`)
* ✅ Auth guard (redirects to login if no token)
* ✅ `feed.css` full glassmorphism dark theme with responsive breakpoints
* ✅ `zone_autocomplete.js` integrated in composer
* ✅ `profile.html` + `profile.js` + `profile.css` — basic profile page

---

## 🧪 How To Run + Test (for collaborators)

### 1) Start Backend (Terminal 1)

```bash
cd ~/Desktop/Pulse/backend
source venv/bin/activate
python3 run.py
```

✅ Expected: `Running on http://127.0.0.1:5000`

### 2) Start Frontend (Terminal 2)

```bash
cd ~/Desktop/Pulse/Frontend
python3 -m http.server 8000
```

Open:

* [http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html)
* [http://127.0.0.1:8000/register.html](http://127.0.0.1:8000/register.html)
* [http://127.0.0.1:8000/feed.html](http://127.0.0.1:8000/feed.html)

---

## ✅ Auth Test Checklist (Expected Behavior)

### A) Register

* [ ] Open `register.html`
* [ ] Try invalid email (`test@gmail.com`)

  * ✅ Expected: shows “Email must end with @ulaval.ca”
* [ ] Try valid email (`test@ulaval.ca`) + strong password

  * ✅ Expected: registers OR shows backend error clearly
* [ ] If success → token must exist:

```js
localStorage.getItem("pulse_token")
```

### B) Login

* [ ] Open `login.html`
* [ ] Login with valid credentials

  * ✅ Expected: redirect to `feed.html`
* [ ] Token must exist:

```js
localStorage.getItem("pulse_token")
```

### C) Verify Backend Accepts Token

Run in DevTools Console:

```js
fetch("http://127.0.0.1:5000/api/auth/me", {
  headers: { Authorization: "Bearer " + localStorage.getItem("pulse_token") }
}).then(r => r.json()).then(console.log)
```

✅ Expected: user profile JSON

### D) Protected Page (feed)

Remove token:

```js
localStorage.removeItem("pulse_token")
```

Refresh `feed.html`
✅ Expected: redirect to `login.html`

---

## 🔌 Frontend ↔ Backend Contract (Current)

### Endpoints (in use now)

* ✅ `POST /api/auth/register`
* ✅ `POST /api/auth/login`
* ✅ `GET /api/auth/me`

### Accepted token keys

* ✅ `{ "token": "..." }`
* ✅ `{ "access_token": "..." }`

---

## 🛠 Known Issues

### ✅ Resolved

* ✅ “API is not defined” — fixed by defining/exporting API base in `auth.js`
* ✅ Port already in use — frontend moved to port **8000**
* ✅ Token visibility confusion — verified key `pulse_token`
* ✅ Logout button — implemented (clears token + redirects to login)
* ✅ Feed posts layout — post cards built

### ⚠️ Current

* ⚠️ Feed reactions / comments not fully wired to backend yet
* ⚠️ Image upload in composer — UI present, backend wiring pending
* ⚠️ Token refresh not implemented (24h expiration, then manual re-login needed)
* ⚠️ 401 interceptor in `apiFetch` not yet added

---

## ✅ Next Steps (Ordered To-Do)

### Phase 2 — Auth (Complete ✅)

* [x] Logout button (clears `pulse_token` → redirect `login.html`)
* [x] Register success → auto-login or redirect to login
* [x] Protected-route check on all private pages

### Phase 3 — Feed UI (Complete ✅)

* [x] Middle feed layout (posts container)
* [x] Post card component (author/anonymous label, zone, timestamp, sentiment badge)
* [x] Empty state (“No posts yet”)
* [x] Loading state (spinner/skeleton)

### Phase 4 — Feed API Integration (current)

* [ ] `GET /api/posts/feed` fully wired (Authorization: `Bearer <token>`)
* [ ] Render posts dynamically from API data
* [ ] Reactions wired to `POST /api/posts/<id>/react`
* [ ] Comments wired to `GET/POST /api/posts/<id>/comments`
* [ ] Handle errors:

  * [ ] 401 → logout + redirect login
  * [ ] 4xx/5xx → show user-friendly error UI

---

## 🏁 Definition of Done (Current Milestone)

* [x] Register wired (frontend validation + backend call)
* [x] Login wired (backend call + token saved)
* [x] Token stored under `pulse_token`
* [x] `/api/auth/me` works with Bearer token
* [x] Feed accessible only when authenticated (token exists)
* [x] Logout exists (token clear + redirect)
* [x] Post cards rendered with author, zone, timestamp, sentiment badge
* [ ] Reactions / comments wired to backend
* [ ] Full error handling (401 interceptor)

**Last Achievement:** Feed UI complete — layout, post cards, composer modal, auth guard all working ✅  
**Next Milestone:** Wire remaining feed interactions (reactions, comments) and complete API integration 🚀

```
```

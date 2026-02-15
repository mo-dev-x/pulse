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
| Phase 2: Auth Integration (Login + Register + Token) | ✅ Mostly Complete | 90% |
| Phase 3: Feed UI (Layout + Components) | 🟡 In Progress | 60% |
| Phase 4: Feed API Integration (Posts) | 🟠 Next | 0% |
| Phase 5: UX Polish (toasts/spinners/empty states) | 🔵 Later | 0% |
| Phase 6: Map + Mood Analytics UI | 🔵 Later | 0% |

**Overall Progress:** 🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜ **~65%**  
**Current Focus:** Feed page — **sidebar + navbar done**, now building the **middle feed section** (posts list + cards).

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

### ✅ Phase 2 — Auth Integration (Mostly Complete)

**Core helpers**

* ✅ `auth.js` created (token helpers + `apiFetch`)
* ✅ Token stored in `localStorage` under key: `pulse_token`

**Login**

* ✅ `POST /api/auth/login`
* ✅ Saves JWT → redirect to `feed.html`
* ✅ Displays backend error messages (invalid credentials, etc.)

**Register**

* ✅ Frontend validation: email must end with `@ulaval.ca`
* ✅ `POST /api/auth/register`
* ✅ Displays backend validation errors (password rules, etc.)

**Manual verification**

* ✅ `localStorage.getItem("pulse_token")` returns JWT
* ✅ `GET /api/auth/me` works with `Authorization: Bearer <token>`

### 🟡 Phase 3 — Feed UI (In Progress)

* ✅ `feed.html` created (skeleton)
* ✅ Navbar created
* ✅ Sidebar created
* 🟡 Middle feed section in progress (posts layout + cards)

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

### ⚠️ Current

* ⚠️ Logout button not implemented yet (manual token removal works)
* ⚠️ Feed route protection must stay active (avoid commented module import)
* ⚠️ Feed posts API integration not started yet

---

## ✅ Next Steps (Ordered To-Do)

### Phase 2 — Finish Auth (last 10%)

* [ ] Add **Logout** button (clear `pulse_token` → redirect `login.html`)
* [ ] Decide register success flow:

  * [ ] Option A: auto-login → save token → go feed
  * [ ] Option B: redirect to login after successful register
* [ ] Ensure protected-route check is finalized on all private pages

### Phase 3 — Feed UI (current)

* [ ] Build middle feed layout (posts container)
* [ ] Create Post Card component:

  * [ ] author/anonymous label
  * [ ] zone + timestamp
  * [ ] sentiment badge (🟢🟡🔴)
  * [ ] content text
* [ ] Add empty state (“No posts yet”)
* [ ] Add loading state (spinner/skeleton)

### Phase 4 — Feed API Integration (next major)

* [ ] `GET /api/posts/feed` (Authorization: `Bearer <token>`)
* [ ] Render posts dynamically
* [ ] Handle errors:

  * [ ] 401 → logout + redirect login
  * [ ] 4xx/5xx → show user-friendly error UI

---

## 🏁 Definition of Done (Current Milestone)

* [x] Register wired (frontend validation + backend call)
* [x] Login wired (backend call + token saved)
* [x] Token stored under `pulse_token`
* [x] `/api/auth/me` works with Bearer token
* [ ] Feed accessible only when authenticated (token exists)
* [ ] Logout exists (token clear + redirect)

**Last Achievement:** Auth integration working end-to-end (JWT stored + `/api/auth/me` verified) ✅
**Next Milestone:** Feed UI complete + connect `GET /api/posts/feed` 🚀

```
```

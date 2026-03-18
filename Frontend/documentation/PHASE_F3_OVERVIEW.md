# 🔵 PHASE F3 OVERVIEW — PROFILE, SOCIAL & FOLLOWING

**Pulse Frontend — Vanilla JS · Université Laval**

**Status:** 🔵 Planning  
**Priority:** High — Social graph is core to Pulse identity  
**Estimated Time:** 4–5 days  
**Depends on:** Phase F1 (design system, auth), Phase F2 (post card component)

> **Design principle for Phase F3:** The profile is the human face of Pulse. Every student should feel ownership over their page. Make the follow action feel instant — optimistic UI is mandatory here.

---

## 🎯 PHASE F3 GOALS

- Build the **public profile page** — bio, follower/following counts, recent posts
- Build the **own profile** — edit display name, bio, avatar, visibility toggle
- Build the **follow / unfollow** action with optimistic UI
- Build the **followers / following modal** (list of users)
- Build the **friends list** (mutual follows)
- Ensure zone feed is accessible from zone tags on posts and zones page

---

## 📊 PHASE F3 STATUS OVERVIEW

| Component | Priority | Status | Est. Days |
|-----------|----------|--------|-----------|
| Public profile page | Must Have | 🔵 Not started | 1.5 |
| Own profile + edit | Must Have | 🔵 Not started | 1 |
| Follow / unfollow | Must Have | 🔵 Not started | 0.5 |
| Followers / Following lists | Should Have | 🔵 Not started | 0.5 |
| Friends list | Should Have | 🔵 Not started | 0.5 |
| Zone feed page | Should Have | 🔵 Not started | 0.5 |
| Avatar upload | Nice to Have | 🔵 Not started | 0.5 |

**Overall Phase F3 Progress:** 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 0%

---

## 📋 COMPONENT 1: Public Profile Page

**File:** `profile.html`, `js/profile.js`, `css/profile.css`  
**Route:** `#profile?u=<username>`

### Layout

```
┌──────────────────────────────────────────────┐
│  ← Retour                                    │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  [avatar 80px]  Marie Tremblay         │  │
│  │                 @marie_t               │  │
│  │                 Bio: Étudiante en droit │  │
│  │                                        │  │
│  │  42 publications · 128 abonnés         │  │
│  │  · 95 abonnements                      │  │
│  │                                        │  │
│  │  [  ✅ Abonné(e)  ▾ ]  [ Message ]    │  │  ← own profile: [Modifier]
│  └────────────────────────────────────────┘  │
│                                              │
│  ─ Publications ──────────────────────────   │
│  [POST CARD]                                 │
│  [POST CARD]                                 │
└──────────────────────────────────────────────┘
```

### Data Loading

```javascript
async function loadProfile(username) {
  const [profileRes, postsRes] = await Promise.all([
    apiFetch(`/api/users/@${username}`),
    apiFetch(`/api/posts/@${username}?page=1`)
  ]);
  const profile = await profileRes.json();
  const posts = await postsRes.json();
  renderProfile(profile);
  renderPosts(posts.posts);
}
```

### Own Profile Detection

```javascript
const me = JSON.parse(localStorage.getItem('pulse_user'));
const isOwnProfile = me?.username === username;
// Show "Modifier" instead of "Abonner"
```

---

## 📋 COMPONENT 2: Own Profile Edit

**File:** `js/profile.js` — edit modal or inline edit  
**Route:** `#settings` or inline on `#profile`

### Editable Fields

| Field | Endpoint | Notes |
|-------|----------|-------|
| Display name | PATCH `/api/users/me` | 1–50 chars |
| Bio | PATCH `/api/users/me` | 0–160 chars |
| Profile visibility | PATCH `/api/users/me` | `public` / `private` |
| Avatar | POST `/api/users/me/avatar` | Image upload |

### Edit Form Layout

```
┌──────────────────────────────────────┐
│  Modifier le profil                  │
│                                      │
│  [avatar]  [Changer la photo]        │
│                                      │
│  Nom affiché                         │
│  ┌──────────────────────────────┐    │
│  │ Marie Tremblay               │    │
│  └──────────────────────────────┘    │
│                                      │
│  Biographie (0/160)                  │
│  ┌──────────────────────────────┐    │
│  │ Étudiante en droit           │    │
│  └──────────────────────────────┘    │
│                                      │
│  Visibilité du profil                │
│  ● Publique  ○ Privée               │
│                                      │
│  [Enregistrer]   [Annuler]           │
└──────────────────────────────────────┘
```

---

## 📋 COMPONENT 3: Follow / Unfollow

**File:** `js/profile.js`

### Button States

| State | Label (FR) | Label (EN) | Style |
|-------|-----------|-----------|-------|
| Not following | Suivre | Follow | Primary (red) |
| Following | Abonné(e) ✓ | Following ✓ | Secondary + dropdown |
| Processing | … | … | Disabled |

### Dropdown on "Abonné(e)"

```
┌──────────────────┐
│  ✅ Abonné(e)  ▾ │
└──────────────────┘
        ↓ (click)
┌──────────────────┐
│  Se désabonner   │
└──────────────────┘
```

### Optimistic UI

```javascript
async function toggleFollow(username, currentlyFollowing) {
  // Immediately update button
  setFollowButton(username, !currentlyFollowing);
  updateFollowerCount(!currentlyFollowing ? +1 : -1);

  const method = currentlyFollowing ? 'DELETE' : 'POST';
  const endpoint = currentlyFollowing
    ? `/api/unfollow/@${username}`
    : `/api/follow/@${username}`;

  const res = await apiFetch(endpoint, { method });
  if (!res || !res.ok) {
    // Revert on failure
    setFollowButton(username, currentlyFollowing);
    updateFollowerCount(currentlyFollowing ? +1 : -1);
    showToast(t('error.network'));
  }
}
```

---

## 📋 COMPONENT 4: Followers / Following Lists

**File:** `js/profile.js` — modal overlay

### Modal Layout

```
┌───────────────────────────────────┐
│  Abonnés (128)              [✕]   │
│  ┌─────────────────────────────┐  │
│  │ 🔍  Rechercher…             │  │
│  └─────────────────────────────┘  │
│  ─────────────────────────────    │
│  [avatar] Sophie M.  @sophie_m    │
│           [Suivre]                │
│  [avatar] Jean B.    @jean_b      │
│           [Abonné(e) ✓]           │
│  ─────────────────────────────    │
│  [ Charger plus… ]                │
└───────────────────────────────────┘
```

### Backend Endpoints

| Action | Endpoint |
|--------|----------|
| Followers list | `GET /api/users/@<username>/followers?page=1` |
| Following list | `GET /api/users/@<username>/following?page=1` |
| Friends (mutual) | `GET /api/users/me/friends` |

---

## 📋 COMPONENT 5: Friends List

**Route:** `#friends` or accessible from own profile

Brief dedicated view — mutual follows displayed as a contact-book-style list.

```
┌──────────────────────────────────┐
│  Amis (18)                       │
│                                  │
│  [avatar] Marie T.     → profil  │
│  [avatar] Jean B.      → profil  │
│  [avatar] Sophie M.    → profil  │
└──────────────────────────────────┘
```

Backend: `GET /api/users/me/friends`

---

## 📋 COMPONENT 6: Zone Feed Page

**File:** `zone.html`, `js/zone.js`, route: `#zone?id=<zone_id>`

### Layout

```
┌──────────────────────────────────────────┐
│  ← Retour                                │
│                                          │
│  📍 Bibliothèque                         │
│  Zone · Campus principal                 │
│                                          │
│  ─ Activité récente ─────────────────    │
│  [POST CARD]                             │
│  [POST CARD]                             │
└──────────────────────────────────────────┘
```

### Backend Endpoints

| Action | Endpoint |
|--------|----------|
| Zone feed | `GET /api/posts/zone/<id>` |
| Zone activity | `GET /api/zones/<id>/activity` |

Zone names are always bilingual — display both or choose based on user's `getLang()`.

---

## 🔗 BACKEND ENDPOINTS USED IN PHASE F3

| Action | Method | Endpoint |
|--------|--------|----------|
| Get own profile | GET | `/api/users/me` |
| Update own profile | PATCH | `/api/users/me` |
| Upload avatar | POST | `/api/users/me/avatar` |
| Get public profile | GET | `/api/users/@<username>` |
| Get user's posts | GET | `/api/posts/@<username>` |
| Follow | POST | `/api/follow/@<username>` |
| Unfollow | DELETE | `/api/unfollow/@<username>` |
| Followers list | GET | `/api/users/@<username>/followers` |
| Following list | GET | `/api/users/@<username>/following` |
| Friends list | GET | `/api/users/me/friends` |
| Zone feed | GET | `/api/posts/zone/<id>` |
| Zone activity | GET | `/api/zones/<id>/activity` |

---

## ✅ SUCCESS CRITERIA

**Phase F3 Complete When:**

- [ ] Public profile page loads correctly for any `@username` via hash route
- [ ] Own profile detected — shows "Modifier" instead of "Suivre"
- [ ] Follow button is optimistic — count updates instantly, reverts on error
- [ ] "Abonné(e)" state shows dropdown with "Se désabonner" option
- [ ] Edit profile form: display name, bio, visibility — saves to backend
- [ ] Avatar upload works (image preview + upload progress)
- [ ] Followers / Following modals load paginated lists
- [ ] Each user in list shows correct follow state
- [ ] Zone feed page loads posts filtered to selected zone
- [ ] All text bilingual (FR / EN) throughout

---

**Last Updated:** 2026-03-16  
**Status:** 🔵 Planning  
**Blockers:** Phase F1 + F2 must be complete  
**Depends on:** Backend Phase 3 (social, followers, zones) ✅ Complete

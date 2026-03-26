# 🔵 PHASE F3 OVERVIEW — PROFILE, SOCIAL & FOLLOWING

**Pulse Frontend — Vanilla JS · Université Laval**

**Status:** ✅ Implemented in code
**Priority:** High — Social graph is core to Pulse identity  
**Estimated Time:** 4–5 days  
**Depends on:** Phase F1 (design system, auth), Phase F2 (post card component)

> **Design principle for Phase F3:** The profile is the human face of Pulse. Every student should feel ownership over their page. Make the follow action feel instant — optimistic UI is mandatory here.

> **Implementation note:** The public profile, own-profile edit flow, followers/following/friends modals, and zone feed are implemented. The current follow/unfollow behaviour refreshes profile state instead of doing a fully optimistic update, and avatar upload works with preview but not upload progress UI.

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
| Public profile page | Must Have | ✅ Implemented | 1.5 |
| Own profile + edit | Must Have | ✅ Implemented | 1 |
| Follow / unfollow | Must Have | ✅ Implemented with refresh-based follow state updates | 0.5 |
| Followers / Following lists | Should Have | ✅ Implemented | 0.5 |
| Friends list | Should Have | ✅ Implemented | 0.5 |
| Zone feed page | Should Have | ✅ Implemented | 0.5 |
| Avatar upload | Nice to Have | ✅ Implemented with preview | 0.5 |

**Overall Phase F3 Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜ ~95%

## 🧩 SHIPPED IMPLEMENTATION

| Area | Shipped code |
|------|--------------|
| Profile page | `profile.html`, `css/profile.css`, `js/profile.js` |
| Own-profile edit | Inline modal on `profile.html`, save flows in `js/profile.js` |
| Social graph | Followers, following, and friends modals in `js/profile.js` |
| Zone feed | `zone.html`, `js/zone.js` |
| Notable deviation | Follow/unfollow reloads profile state rather than applying a fully optimistic update, and avatar upload has preview but no progress UI |

---

## 📋 COMPONENT 1: Public Profile Page

**File:** `profile.html`, `js/profile.js`, `css/profile.css`  
**Route:** `profile.html?u=<username>`

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
**Route:** Inline on `profile.html`

### Editable Fields

| Field | Endpoint | Notes |
|-------|----------|-------|
| Display name | PATCH `/api/auth/update-profile` | 1–100 chars |
| Bio | PATCH `/api/auth/update-profile` | 0–500 chars |
| Profile visibility | PATCH `/api/auth/privacy-settings` | `public` / `followers` / `private` |
| Avatar | POST `/api/auth/upload-profile-pic` | Image upload |

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

**Route:** Accessible from own profile via modal

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
| Get own profile | GET | `/api/auth/me` |
| Update own profile | PATCH | `/api/auth/update-profile` |
| Update privacy settings | PATCH | `/api/auth/privacy-settings` |
| Upload avatar | POST | `/api/auth/upload-profile-pic` |
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

- [x] Public profile page loads correctly for any `@username`
- [x] Own profile detection shows edit controls instead of follow controls
- [~] Follow/unfollow works correctly, but not with the originally planned fully optimistic update
- [~] The planned follower-state dropdown pattern is not implemented; the current UI uses direct buttons
- [x] Edit profile form saves successfully
- [~] Avatar upload works with preview, but not with upload-progress UI
- [x] Followers / Following modals load correctly
- [x] User lists render the expected identity/follow context
- [x] Zone feed page loads posts filtered to the selected zone
- [~] Bilingual coverage in the profile area is partial rather than complete

---

**Last Updated:** 2026-03-26
**Status:** ✅ Implemented in code
**Blockers:** Phase F1 + F2 must be complete  
**Depends on:** Backend Phase 3 (social, followers, zones) ✅ Complete

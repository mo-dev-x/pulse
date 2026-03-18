# 🔵 PHASE F2 OVERVIEW — FEED, POSTS & INTERACTIONS

**Pulse Frontend — Vanilla JS · Université Laval**

**Status:** 🔵 Planning  
**Priority:** Critical — Core user loop  
**Estimated Time:** 5–7 days  
**Depends on:** Phase F1 complete (design system, i18n, auth)

> **Design principle for Phase F2:** The feed is the heartbeat of Pulse. Every millisecond of perceived lag on the feed degrades the product. Use optimistic UI for reactions and loading skeletons for the initial render — never show a blank screen.

---

## 🎯 PHASE F2 GOALS

- Build the main **feed** with infinite scroll, pulling from `/api/posts/feed`
- Build the **post composer** — public/anonymous toggle, zone picker, char counter, image upload
- Build the **post card** component — reactions, comments inline, timestamps, report button
- Build the **reaction picker** (10 emojis) with optimistic UI and privacy-safe display
- Build the **comment thread** — nested display, submit, delete own comment
- Build the **bookmark** toggle
- Build the **delete post** action with 24h guard
- Wire existing `feed.html` / `feed.js` / `feed.css` to all of the above

---

## 📊 PHASE F2 STATUS OVERVIEW

| Component | Priority | Status | Est. Days |
|-----------|----------|--------|-----------|
| Feed layout + infinite scroll | Must Have | 🔵 Not started | 1 |
| Post composer | Must Have | 🔵 Not started | 1.5 |
| Post card component | Must Have | 🔵 Not started | 1 |
| Reaction picker | Must Have | 🔵 Not started | 0.5 |
| Comment thread | Should Have | 🔵 Not started | 1 |
| Bookmark toggle | Should Have | 🔵 Not started | 0.5 |
| Delete post (24h guard) | Should Have | 🔵 Not started | 0.5 |
| Image upload in composer | Nice to Have | 🔵 Not started | 0.5 |

**Overall Phase F2 Progress:** 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 0%

---

## 📋 COMPONENT 1: Feed Layout + Infinite Scroll

**File:** `js/feed.js` (major extension), `css/feed.css` (extend)

### Layout

```
┌────────────────────────────────────────┐
│  🫀 Pulse  [search]  🔔  👤  [FR|EN]  │  ← Nav bar
├────────────────────────────────────────┤
│  ┌────────────────────────────────┐    │
│  │ 🖊  Quoi de neuf ?        [→]  │    │  ← Composer teaser
│  └────────────────────────────────┘    │
│  ─────────────────────────────         │
│  [POST CARD]                           │
│  [POST CARD]                           │
│  [POST CARD]                           │
│  ⏳ Chargement…                        │  ← Infinite scroll trigger
└────────────────────────────────────────┘
```

### Infinite Scroll Implementation

```javascript
const observer = new IntersectionObserver(async (entries) => {
  if (entries[0].isIntersecting && !loading && hasNext) {
    page++;
    await loadFeed(page);
  }
}, { threshold: 0.1 });

observer.observe(document.querySelector('#scroll-sentinel'));
```

### Feed Endpoint

`GET /api/posts/feed?page=1&per_page=20`

Response shape:
```json
{
  "posts": [...],
  "page": 1,
  "has_next": true
}
```

### Loading Skeleton

While feed is loading, show 3 skeleton cards:

```css
.skeleton {
  background: linear-gradient(90deg,
    var(--color-surface) 25%,
    var(--color-surface-2) 50%,
    var(--color-surface) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

### Empty State

When `posts.length === 0`:

```
     🌱
  Votre fil est vide
  Suivez des gens pour voir leurs publications
  [ Explorer la découverte ]
```

FR: "Votre fil est vide · Suivez des gens pour voir leurs publications"  
EN: "Your feed is empty · Follow people to see their posts"

---

## 📋 COMPONENT 2: Post Composer

**File:** `js/feed.js` (composer section), modal or inline panel

### Layout

```
┌────────────────────────────────────────────┐
│  👤  Qu'est-ce que vous pensez ?           │
│  ┌──────────────────────────────────────┐  │
│  │                                      │  │
│  │                                      │  │
│  │                                    ↵ │  │
│  └──────────────────────────────────────┘  │
│  0 / 500                                   │  ← char counter
│                                            │
│  Zone: [ Bibliothèque ▾ ]                  │  ← zone picker
│                                            │
│  🔒 [Publique ●] [Anonyme]   [🖼] [Publier]│
└────────────────────────────────────────────┘
```

### Composer Logic

```javascript
// Character counter — colour changes at thresholds
function updateCharCounter(text) {
  const count = text.length;
  const max = 500;
  const el = document.querySelector('#char-counter');
  el.textContent = `${count} / ${max}`;
  el.className = count > 480 ? 'counter-danger'
               : count > 400 ? 'counter-warning'
               : 'counter-ok';
}
```

### Anonymous / Public Toggle

- Default: **Public** (linked to profile)
- Anonymous: post appears with pseudonym, `is_anonymous: true`
- Toggle is visually clear — not buried

```html
<div class="post-mode-toggle">
  <button class="toggle-btn active" data-mode="public">
    👤 <span data-i18n="composer.public">Publique</span>
  </button>
  <button class="toggle-btn" data-mode="anonymous">
    🎭 <span data-i18n="composer.anonymous">Anonyme</span>
  </button>
</div>
```

### Zone Picker

Integrate `zone_autocomplete.js` (existing):

```javascript
// Zone picker — shows a dropdown from /api/zones
import { initZoneAutocomplete } from './zone_autocomplete.js';
initZoneAutocomplete('#zone-input', (zone) => {
  selectedZoneId = zone.id;
});
```

### Image Upload

- `<input type="file" accept="image/*">` — hidden, triggered by camera icon
- Preview thumbnail before submit
- Send as `multipart/form-data`
- Show upload progress bar
- Max size enforced client-side (2MB)

### Submit Payload

```javascript
const body = {
  content: textarea.value.trim(),
  is_anonymous: selectedMode === 'anonymous',
  zone_id: selectedZoneId || null,
};
// If image: use FormData instead of JSON
```

Backend endpoint: `POST /api/posts`

---

## 📋 COMPONENT 3: Post Card

**File:** `js/post.js` (new), `css/feed.css`

### Card Layout

```
┌──────────────────────────────────────────────┐
│  👤 Marie T.  @marie_t  ·  il y a 5 min      │
│  Zone: Bibliothèque                           │
├──────────────────────────────────────────────┤
│  C'est une belle journée pour étudier !       │
│  [image if present]                           │
├──────────────────────────────────────────────┤
│  😊 12  ❤️ 8  😂 3   💬 4    🔖    ···       │
└──────────────────────────────────────────────┘
```

Anonymous card:
```
┌──────────────────────────────────────────────┐
│  🎭 Fantôme nocturne  ·  il y a 20 min       │
│  Zone: Cafétéria                             │
├──────────────────────────────────────────────┤
│  Les examens approchent... 😰                 │
└──────────────────────────────────────────────┘
```

### Post Card Template Function

```javascript
export function renderPost(post, currentUserId) {
  const isOwn = post.user_id === currentUserId;
  const isAnon = post.is_anonymous;
  return `
    <article class="post-card" data-post-id="${post.id}">
      <header class="post-header">
        <div class="post-author">
          ${isAnon
            ? `<span class="anon-avatar">🎭</span>
               <span class="anon-name">${esc(post.pseudonym)}</span>`
            : `<img class="avatar" src="${esc(post.author.profile_picture || '')}" alt="">
               <a href="#profile?u=${esc(post.author.username)}" class="author-name">
                 ${esc(post.author.display_name)}
               </a>`
          }
          <time class="post-time" datetime="${post.created_at}">
            ${timeAgo(post.created_at)}
          </time>
        </div>
        ${isOwn ? '<button class="post-menu-btn">···</button>' : ''}
      </header>
      <div class="post-body">${esc(post.content)}</div>
      ${post.media?.length ? renderMedia(post.media) : ''}
      <footer class="post-footer">
        <div class="reactions-bar" data-post-id="${post.id}">
          ${renderReactionCounts(post.reactions, post.user_reaction)}
        </div>
        <button class="comment-btn">💬 ${post.comment_count}</button>
        <button class="bookmark-btn ${post.is_bookmarked ? 'active' : ''}">🔖</button>
      </footer>
    </article>`;
}
```

### Time Ago (Bilingual)

```javascript
export function timeAgo(isoDate) {
  const lang = getLang();
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return lang === 'fr' ? "à l'instant" : 'just now';
  if (mins < 60) return lang === 'fr' ? `il y a ${mins} min` : `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return lang === 'fr' ? `il y a ${hrs} h` : `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return lang === 'fr' ? `il y a ${days} j` : `${days}d ago`;
}
```

---

## 📋 COMPONENT 4: Reaction Picker

**File:** `js/post.js`

### Allowed Emojis (from backend)

`👍 ❤️ 😂 😮 😢 😡 🙌 🔥 💯 🎉`

### Picker UI

```
┌──────────────────────┐
│ 👍 ❤️ 😂 😮 😢      │
│ 😡 🙌 🔥 💯 🎉      │
└──────────────────────┘
```

Shown on hover/long-press over the reaction area.

### Privacy Rules (enforced client-side too)

- **Never** display who reacted — only aggregate counts
- Show user's own current reaction highlighted
- No "X people reacted with ❤️" list

### Optimistic UI

```javascript
async function toggleReaction(postId, emoji) {
  // 1. Update DOM immediately
  updateReactionCountUI(postId, emoji, +1);

  // 2. Send to backend
  const res = await apiFetch(`/api/posts/${postId}/react`, {
    method: 'POST',
    body: JSON.stringify({ emoji })
  });

  // 3. If failed, revert
  if (!res || !res.ok) {
    updateReactionCountUI(postId, emoji, -1);
    showToast(t('error.network'));
  }
}
```

Backend: `POST /api/posts/<id>/react` / `DELETE /api/posts/<id>/react`

---

## 📋 COMPONENT 5: Comment Thread

**File:** `js/post.js` (comments section)

### Layout (inline, toggled by 💬 button)

```
┌──────────────────────────────────────────────┐
│  💬 4 commentaires                           │
├──────────────────────────────────────────────┤
│  👤 Jean B.  il y a 2 min                    │
│  Super post !                                │
│                                              │
│  👤 Sophie M.  il y a 5 min                  │
│  Je suis d'accord 👍                         │
├──────────────────────────────────────────────┤
│  ┌────────────────────────────────────┐      │
│  │ Ajouter un commentaire…            │      │
│  └────────────────────────────────────┘      │
│  [ Commenter ]                               │
└──────────────────────────────────────────────┘
```

### Backend Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Get comments | GET | `/api/posts/<id>/comments` |
| Post comment | POST | `/api/posts/<id>/comments` |
| Delete own comment | DELETE | `/api/comments/<id>` |

### Own Comment Delete

Show a `···` menu on own comments → "Supprimer" / "Delete"  
No 24h restriction on comment deletion (only posts have it).

---

## 📋 COMPONENT 6: Bookmark Toggle

**File:** `js/post.js`

```javascript
async function toggleBookmark(postId, btn) {
  const isActive = btn.classList.contains('active');
  btn.classList.toggle('active');         // optimistic
  const method = isActive ? 'DELETE' : 'POST';
  const res = await apiFetch(`/api/posts/${postId}/bookmark`, { method });
  if (!res || !res.ok) btn.classList.toggle('active');  // revert on fail
}
```

Backend: `POST /api/posts/<id>/bookmark` / `DELETE /api/posts/<id>/bookmark`

---

## 📋 COMPONENT 7: Delete Post (24h Guard)

Only shown on own posts in the `···` menu.

```javascript
async function deletePost(postId, createdAt) {
  const hoursSince = (Date.now() - new Date(createdAt)) / 3600000;
  if (hoursSince > 24) {
    showToast(t('post.delete_expired'));  // "Les publications ne peuvent être supprimées que dans les 24h"
    return;
  }
  if (!confirm(t('post.delete_confirm'))) return;
  const res = await apiFetch(`/api/posts/${postId}`, { method: 'DELETE' });
  if (res?.ok) document.querySelector(`[data-post-id="${postId}"]`).remove();
}
```

Backend: `DELETE /api/posts/<id>`

---

## 🔗 BACKEND ENDPOINTS USED IN PHASE F2

| Action | Method | Endpoint |
|--------|--------|----------|
| Get feed | GET | `/api/posts/feed` |
| Create post | POST | `/api/posts` |
| Delete post | DELETE | `/api/posts/<id>` |
| Get reactions | GET | `/api/posts/<id>/reactions` |
| Add/update reaction | POST | `/api/posts/<id>/react` |
| Remove reaction | DELETE | `/api/posts/<id>/react` |
| Get comments | GET | `/api/posts/<id>/comments` |
| Add comment | POST | `/api/posts/<id>/comments` |
| Delete comment | DELETE | `/api/comments/<id>` |
| Bookmark | POST | `/api/posts/<id>/bookmark` |
| Remove bookmark | DELETE | `/api/posts/<id>/bookmark` |
| Get zones | GET | `/api/zones` |

---

## ✅ SUCCESS CRITERIA

**Phase F2 Complete When:**

- [ ] Feed loads from `/api/posts/feed` with loading skeletons on first render
- [ ] Infinite scroll loads next pages automatically
- [ ] Empty feed state shows bilingual message + discovery link
- [ ] Post composer opens, validates (min 10 / max 500 chars), submits public and anonymous posts
- [ ] Zone picker autocompletes from backend zones list
- [ ] Post cards render correctly for named and anonymous authors
- [ ] Timestamps display in bilingual relative format (`il y a 5 min` / `5m ago`)
- [ ] Reaction picker opens, user can add/change/remove reaction
- [ ] Reaction counts are privacy-safe (no "who reacted" disclosure)
- [ ] Comment thread toggles open/closed, user can post and delete own comments
- [ ] Bookmark toggle is optimistic and persists on reload
- [ ] Delete post: only own posts, only within 24h, confirm dialog
- [ ] New post prepended to feed immediately on submit (optimistic)

---

**Last Updated:** 2026-03-16  
**Status:** 🔵 Planning  
**Blockers:** Phase F1 must be complete  
**Depends on:** Backend Phases 2–3 (posts, reactions, comments, bookmarks) ✅ Complete

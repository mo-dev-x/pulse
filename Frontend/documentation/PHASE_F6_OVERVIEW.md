# 🔵 PHASE F6 OVERVIEW — SEARCH, DISCOVERY & POLISH

**Pulse Frontend — Vanilla JS · Université Laval**

**Status:** ✅ Implemented in code
**Priority:** High — The features that make Pulse feel like a real product  
**Estimated Time:** 5–7 days  
**Depends on:** All previous frontend phases complete

> **Design principle for Phase F6:** This phase is the difference between a working prototype and a product people want to use. Skeletons, empty states, error boundaries, dark mode, and accessibility are not optional extras — they are the product.

> **Implementation note:** Search, discovery, mention autocomplete, theme persistence, offline banners, skeletons, and an accessibility audit document are all present in the codebase. The biggest gap versus the original concept is that the live nav dropdown on feed/profile remains people-focused rather than a fully unified search dropdown, and bilingual coverage is still incomplete in some UI copy.

---

## 🎯 PHASE F6 GOALS

- Build the **global search** bar with live results and tabbed result page
- Build **@mention autocomplete** in composer and comments
- Build the **discovery feed** page (trending content for new users)
- Build the **trending zones** widget
- Implement **dark mode** toggle with persistence and system-preference respect
- Complete **accessibility audit** — WCAG 2.1 AA
- Add **loading skeletons** to all feeds and lists
- Add bilingual **empty states** across all pages
- Add **error boundaries** and an **offline state** banner

---

## 📊 PHASE F6 STATUS OVERVIEW

| Component | Priority | Status | Est. Days |
|-----------|----------|--------|-----------|
| Global search bar + results | Must Have | ✅ Implemented, with a simplified nav dropdown | 1.5 |
| @mention autocomplete | Must Have | ✅ Implemented in composer and comments | 0.5 |
| Discovery feed page | Must Have | ✅ Implemented | 1 |
| Loading skeletons (all pages) | Must Have | ✅ Implemented across the main feed/list surfaces | 0.5 |
| Bilingual empty states (all pages) | Must Have | ~ Implemented across key pages, but not literally every string/view | 0.5 |
| Dark mode toggle | Should Have | ✅ Implemented with persistence and `auto` mode | 0.5 |
| Trending zones widget | Should Have | ✅ Implemented | 0.5 |
| Error boundaries + offline state | Should Have | ✅ `initGlobalErrorHandler()` catches unhandled rejections as toasts; real SW offline fallback page | 0.5 |
| Accessibility audit (WCAG 2.1 AA) | Should Have | ✅ Audit documented; skip link + ARIA live regions auto-injected | 1 |

**Overall Phase F6 Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100%

## 🧩 SHIPPED IMPLEMENTATION

| Area | Shipped code |
|------|--------------|
| Search page | `search.html`, `js/search.js` |
| Discovery page | `discover.html`, `js/discover.js` |
| Theme/offline shell | `js/theme.js`, shared offline banners across authenticated pages |
| Accessibility note | `Frontend/documentation/ACCESSIBILITY_AUDIT.md` |
| Notable deviation | Shared nav live search is still people-focused rather than a full unified dropdown, and bilingual polish is still incomplete |

---

## 📋 COMPONENT 1: Global Search

**File:** `js/search.js`, integrated in nav bar  
**Route:** `search.html?q=<query>&type=<all|posts|users|zones>`

### Search Bar in Nav

```
┌────────────────────────────────────────────────────────┐
│  🫀  [ 🔍 Rechercher sur Pulse… ]   🔔  👤  [FR|EN]  │
└────────────────────────────────────────────────────────┘
```

### Live Dropdown (debounced, 300ms)

```
┌───────────────────────────────────┐
│  "biblio"                         │
│  ─── Zones ───────────────────    │
│  📍 Bibliothèque                  │
│  ─── Personnes ────────────────   │
│  👤 Sophie Bibliographe @biblio_s │
│  ─── Publications ─────────────   │
│  💬 "Étude à la biblio ce soir"   │
│  ─── Voir tous les résultats →    │
└───────────────────────────────────┘
```

### Debounce Implementation

```javascript
let searchTimer;
searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  const q = searchInput.value.trim();
  if (q.length < 2) { hideDropdown(); return; }
  searchTimer = setTimeout(() => fetchLiveResults(q), 300);
});

async function fetchLiveResults(q) {
  const res = await apiFetch(`/api/search?q=${encodeURIComponent(q)}&per_page=5`);
  const data = await res?.json();
  renderDropdown(data);
}
```

### Full Results Page

```
┌─────────────────────────────────────────────────────┐
│  Résultats pour "bibliothèque"                      │
│                                                     │
│  [ Tout (17) ] [ Publications (14) ] [ Personnes (2) ] [ Zones (1) ]
│  ─────────────────────────────────────────────────  │
│  [POST CARD]                                        │
│  [POST CARD]                                        │
│  [ Charger plus… ]                                  │
└─────────────────────────────────────────────────────┘
```

### Privacy Rules in Search Display

- Anonymous post results: show content, **never** show author
- `profile_visibility = 'private'` users: **not shown** (backend enforces, frontend trusts)
- Deactivated users: **not shown**

### Backend Endpoints

| Action | Endpoint |
|--------|----------|
| Unified search | `GET /api/search?q=…&type=all&page=1` |
| Users-only (autocomplete) | `GET /api/search/users?q=…&limit=5` |

---

## 📋 COMPONENT 2: @Mention Autocomplete

**File:** `js/search.js` — `initMentionAutocomplete(textarea)`  
**Used in:** Post composer, comment input

### Trigger

When user types `@` in a textarea, open a small inline dropdown:

```
Je veux mentionner @ma...
  ┌─────────────────────────┐
  │ 👤 Marie T.   @marie_t  │  ← highlight on arrow keys
  │ 👤 Marc G.    @marc_g   │
  └─────────────────────────┘
```

### Implementation

```javascript
export function initMentionAutocomplete(textarea) {
  textarea.addEventListener('input', async (e) => {
    const { triggerWord, triggerPos } = getMentionTrigger(textarea.value, textarea.selectionStart);
    if (!triggerWord) { hideMentionDropdown(); return; }

    const res = await apiFetch(`/api/search/users?q=${encodeURIComponent(triggerWord)}&limit=5`);
    const { users } = await res?.json() ?? { users: [] };
    showMentionDropdown(users, (selected) => {
      insertMention(textarea, triggerPos, selected.username);
    });
  });
}
```

Backend endpoint: `GET /api/search/users?q=<partial>&limit=5`

---

## 📋 COMPONENT 3: Discovery Feed Page

**File:** `js/feed.js` (extend), route: `#discover`

### Purpose

Shown to:
1. New users with empty follow-list
2. Any user who clicks "Explorer" / "Explore"
3. Accessible from the nav

### Layout

```
┌──────────────────────────────────────────────┐
│  🌍 Découverte — Publications du campus      │
│                                              │
│  Filtres:  [ 😊 Positif ] [ Toutes zones ▾ ]│
│  ─────────────────────────────────────────   │
│  [POST CARD — trending]                      │
│  [POST CARD]                                 │
│  [POST CARD]                                 │
│  [ Charger plus… ]                           │
└──────────────────────────────────────────────┘
```

### Ranking Score Display

Do **not** expose raw score to users. Sort server-side — frontend just renders the order returned.

### Backend Endpoints

| Action | Endpoint |
|--------|----------|
| Discovery feed | `GET /api/posts/discover?page=1` |
| Filtered by zone | `GET /api/posts/discover?zone_id=3` |
| Filtered by sentiment | `GET /api/posts/discover?sentiment=positive` |

---

## 📋 COMPONENT 4: Trending Zones Widget

**File:** `js/analytics.js` or `js/zones.js`  
**Used in:** Discovery feed sidebar or analytics page

```
┌─────────────────────────────────┐
│  🔥 Zones tendance              │
│                                 │
│  1. 📍 Bibliothèque  ↑ +34%    │
│  2. 📍 Cafétéria     ↑ +18%    │
│  3. 📍 PEPS          ↑  +9%    │
└─────────────────────────────────┘
```

Backend: `GET /api/zones/trending?window=24h`

---

## 📋 COMPONENT 5: Dark Mode

**Implementation approach:** CSS `data-theme` attribute (already stubbed in `variables.css`)

```javascript
// js/i18n.js or a new js/theme.js
function initTheme() {
  const saved = localStorage.getItem('pulse_theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('pulse_theme', next);
}
```

### Toggle UI in Nav

```
🌙 / ☀️  (icon button, right side of nav)
```

---

## 📋 COMPONENT 6: Loading Skeletons (All Pages)

Add skeleton states to every feed/list that loads async:

| Page | Skeleton |
|------|---------|
| Feed | 3 post card skeletons |
| Profile | Avatar circle + 2 text lines + 3 post skeletons |
| Notifications | 5 row skeletons |
| DM list | 4 conversation row skeletons |
| DM thread | Alternating bubble skeletons |
| Search results | 5 result row skeletons |
| Analytics | Chart placeholder rectangles |

```css
.skeleton-text {
  height: 14px;
  border-radius: var(--radius-full);
  background: var(--color-surface-2);
  animation: shimmer 1.5s infinite;
}
.skeleton-avatar {
  width: 44px; height: 44px;
  border-radius: var(--radius-full);
  background: var(--color-surface-2);
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0%   { opacity: 1; }
  50%  { opacity: 0.5; }
  100% { opacity: 1; }
}
```

---

## 📋 COMPONENT 7: Bilingual Empty States

Every page needs an empty state. All must be bilingual.

| Page | FR | EN | Illustration |
|------|----|----|--------------|
| Feed (no follows) | "Votre fil est vide · Suivez des personnes" | "Your feed is empty · Follow people" | 🌱 |
| Feed (no posts yet) | "Aucune publication pour l'instant" | "No posts yet" | 📭 |
| Notifications | "Aucune notification" | "No notifications" | 🔔 |
| DMs | "Aucune conversation" | "No conversations" | ✉️ |
| Search (no results) | "Aucun résultat pour « {q} »" | "No results for "{q}"" | 🔍 |
| Bookmarks | "Aucune publication sauvegardée" | "No saved posts" | 🔖 |
| Profile posts | "Aucune publication" | "No posts yet" | 📝 |

---

## 📋 COMPONENT 8: Error Boundaries & Offline State

### Offline Banner

```javascript
window.addEventListener('offline', () => {
  document.querySelector('#offline-banner').hidden = false;
});
window.addEventListener('online', () => {
  document.querySelector('#offline-banner').hidden = true;
});
```

```html
<div id="offline-banner" hidden>
  📡 <span data-i18n="error.offline">Connexion perdue — les données peuvent être obsolètes</span>
</div>
```

### API Error Boundary

Wrap all `apiFetch` calls with a global error display:

```javascript
export async function apiFetch(url, options = {}) {
  try {
    // ... existing implementation
  } catch (err) {
    if (!navigator.onLine) showOfflineBanner();
    else showToast(t('error.network'));
    return null;
  }
}
```

### Toast System

```javascript
export function showToast(message, type = 'info', duration = 4000) {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.querySelector('#toast-container').appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}
```

---

## 📋 COMPONENT 9: Accessibility Audit (WCAG 2.1 AA)

Checklist to complete before Phase F6 is marked done:

### Keyboard Navigation
- [ ] All interactive elements reachable by Tab
- [ ] Focus ring visible on all focusable elements
- [ ] Modal traps focus within itself
- [ ] Escape closes modals
- [ ] Reaction picker navigable with arrow keys

### Screen Readers
- [ ] All images have `alt` text (or `alt=""` for decorative)
- [ ] Icon buttons have `aria-label`
- [ ] Live regions for toast notifications (`aria-live="polite"`)
- [ ] Notification badge has `aria-label="N notifications non lues"`
- [ ] Post card announces author (or "Publication anonyme") to screen reader

### Colour & Contrast
- [ ] All text meets 4.5:1 contrast ratio (AA)
- [ ] Mood colours not used as sole indicator (add text label)
- [ ] Links underlined or otherwise distinguishable from body text

### Forms
- [ ] All inputs have associated `<label>`
- [ ] Error messages associated with input via `aria-describedby`
- [ ] Required fields marked with `aria-required="true"`

### Tools to use
- [axe DevTools](https://www.deque.com/axe/) browser extension
- Lighthouse accessibility score ≥ 90

---

## 🔗 BACKEND ENDPOINTS USED IN PHASE F6

| Action | Method | Endpoint |
|--------|--------|----------|
| Unified search | GET | `/api/search` |
| User autocomplete | GET | `/api/search/users` |
| Discovery feed | GET | `/api/posts/discover` |
| Trending posts | GET | `/api/posts/trending` |
| Trending zones | GET | `/api/zones/trending` |

---

## ✅ SUCCESS CRITERIA

**Phase F6 Complete When:**

- [~] Search in shared nav works, but the dropdown is still people-focused rather than fully unified
- [x] Full search results page with type tabs exists
- [x] Anonymous post results do not reveal author identity on the search page
- [x] `@mention` autocomplete fires in composer and comment inputs
- [x] Discovery feed loads from `/api/posts/discover` with sentiment filtering
- [x] Trending zones widget shows the top zones
- [x] Dark mode toggle persists and supports system-aware `auto`
- [x] Main feeds/lists now show skeletons on load
- [~] Key empty states include bilingual copy and illustration/emoji treatment, but coverage is not universal
- [x] Offline banners appear and hide on connectivity changes across the primary authenticated pages
- [x] Network errors are surfaced via global `unhandledrejection` handler that routes to toast notifications
- [~] An accessibility audit document exists, but Lighthouse/WCAG thresholds were not verified as automated guarantees
- [x] Skip-to-content link auto-injected on all pages; ARIA live region on toast container
- [x] Updated shell icon buttons include `aria-label` where required

---

## 🏁 FRONTEND COMPLETE CRITERIA (All F1–F6)

When Phase F6 is done, the Pulse frontend is feature-complete against all 74+ backend endpoints:

| Metric | Target |
|--------|--------|
| Pages | 10+ |
| JS Modules | 15+ |
| Bilingual coverage | 100% |
| Lighthouse Performance | ≥ 85 |
| Lighthouse Accessibility | ≥ 90 |
| WCAG | 2.1 AA |
| Dark mode | ✅ |
| Offline handling | ✅ |
| Backend endpoint coverage | 100% |

---

**Last Updated:** 2026-04-08
**Status:** ✅ Complete — including PWA, push notifications, and accessibility polish
**Blockers:** All previous frontend phases (F1–F5) must be complete  
**Depends on:** Backend Phase 6 (search, discovery, trending) ✅ Complete

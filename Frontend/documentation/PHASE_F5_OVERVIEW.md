# 🔵 PHASE F5 OVERVIEW — NOTIFICATIONS, DMs & SETTINGS

**Pulse Frontend — Vanilla JS · Université Laval**

**Status:** ✅ Implemented in code
**Priority:** High — Retention and trust features  
**Estimated Time:** 5–6 days  
**Depends on:** Phase F1 (auth, i18n), Phase F2 (apiFetch), Phase F3 (profile)

> **Design principle for Phase F5:** Notifications and messages are the stickiest part of any social platform. The unread badge must always be accurate — optimistic mark-as-read, never stale. DMs must feel like messaging, not email.

> **Implementation note:** Notifications, DMs, sessions, 2FA, push permission, unread badges, avatar upload, and direct password change are implemented. The biggest differences from the original plan are endpoint naming, mixed translation coverage, and the use of list payload unread counts instead of a dedicated notifications unread-count endpoint.

---

## 🎯 PHASE F5 GOALS

- Build the **notification centre** — list, mark read, unread badge in nav
- Build the **DM conversation list** and **DM thread view**
- Build the **unread DM badge** in the nav bar
- Build the **settings page** — display name, bio, avatar, language preference
- Build the **security settings** — password change, active sessions, revoke session
- Build the **2FA setup flow** — QR code display, TOTP confirm, backup codes
- Wire the **push notification permission** request (browser Web Push API)

---

## 📊 PHASE F5 STATUS OVERVIEW

| Component | Priority | Status | Est. Days |
|-----------|----------|--------|-----------|
| Notification centre | Must Have | ✅ Implemented | 1 |
| DM conversation list | Must Have | ✅ Implemented | 0.5 |
| DM thread view + send | Must Have | ✅ Implemented | 1.5 |
| Unread DM badge | Must Have | ✅ Implemented in shared navigation helpers | 0.5 |
| Settings page (profile) | Must Have | ✅ Implemented | 0.5 |
| Security settings + sessions | Should Have | ✅ Implemented | 0.5 |
| 2FA setup flow | Should Have | ✅ Implemented | 1 |
| Push notification permission | Nice to Have | ✅ Implemented | 0.5 |

**Overall Phase F5 Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜ ~95%

## 🧩 SHIPPED IMPLEMENTATION

| Area | Shipped code |
|------|--------------|
| Notifications | `notifications.html`, `css/notifications.css`, `js/notifications.js` |
| Messages | `messages.html`, `css/messages.css`, `js/messages.js` |
| Settings | `settings.html`, `js/settings.js` |
| Security support | `backend/app/routes/auth.py`, `backend/tests/test_change_password.py` |
| Notable deviation | Translation coverage is mixed, and some unread-count UI is derived from list payloads instead of a dedicated notifications unread-count endpoint |

---

## 📋 COMPONENT 1: Notification Centre

**File:** `js/notifications.js`, `css/notifications.css`  
**Route:** `notifications.html`

### Nav Badge

```javascript
async function updateNotifBadge() {
  const res = await apiFetch('/api/notifications?per_page=1');
  const { unread_count } = await res.json();
  const badge = document.querySelector('#notif-badge');
  badge.textContent = unread_count > 0 ? Math.min(unread_count, 99) : '';
  badge.hidden = unread_count === 0;
}
// Poll every 30s
setInterval(updateNotifBadge, 30000);
```

### Notification List Layout

```
┌──────────────────────────────────────────────┐
│  🔔 Notifications             [Tout lire]    │
│  ─────────────────────────────────────────   │
│  🔵 ❤️  Marie T. a réagi à votre publication │
│      il y a 2 min                            │
│  ─────────────────────────────────────────   │
│  🔵 💬  Jean B. a commenté votre publication  │
│      il y a 15 min                           │
│  ─────────────────────────────────────────   │
│     👤  Sophie M. vous suit maintenant       │
│      il y a 1 h                              │
└──────────────────────────────────────────────┘
```

### Notification Type Mapping

| Backend `type` | Icon | FR Message | EN Message |
|----------------|------|-----------|-----------|
| `new_follower` | 👤 | `{name} vous suit maintenant` | `{name} followed you` |
| `post_reaction` | ❤️ | `{name} a réagi à votre publication` | `{name} reacted to your post` |
| `post_comment` | 💬 | `{name} a commenté votre publication` | `{name} commented on your post` |
| `comment_reply` | ↩️ | `{name} a répondu à votre commentaire` | `{name} replied to your comment` |
| `new_message` | ✉️ | `Nouveau message de {name}` | `New message from {name}` |

### Backend Endpoints

| Action | Endpoint |
|--------|----------|
| Get notifications | `GET /api/notifications?page=1` |
| Unread count | Included in `GET /api/notifications` response as `unread_count` |
| Mark one read | `PATCH /api/notifications/<id>/read` |
| Mark all read | `POST /api/notifications/read-all` |

---

## 📋 COMPONENT 2: DM Conversation List

**File:** `js/messages.js`, `css/messages.css`  
**Route:** `messages.html`

### Layout

```
┌──────────────────────────────────────────────┐
│  ✉️  Messages                    [✏️ Nouveau] │
│  ─────────────────────────────────────────   │
│  [avatar] Marie T.                           │
│           Ça se passe bien?    · il y a 5 min│
│           🔵 (2 non lus)                     │
│  ─────────────────────────────────────────   │
│  [avatar] Jean B.                            │
│           Super, merci!        · hier        │
└──────────────────────────────────────────────┘
```

### New Conversation

```javascript
async function startConversation(username) {
  // Look up user first (search or profile page → Message button)
  const res = await apiFetch('/api/messages/conversations', {
    method: 'POST',
    body: JSON.stringify({ username })
  });
  const { conversation_id } = await res.json();
  window.location.href = `messages.html`;
}
```

Backend: `POST /api/messages/conversations` → returns existing or new conversation

---

## 📋 COMPONENT 3: DM Thread View

**Route:** `messages.html` with active conversation state

### Layout

```
┌──────────────────────────────────────────────┐
│  ← Messages    Marie T. @marie_t             │
│  ─────────────────────────────────────────   │
│                                              │
│                    Salut! Ça va? ┐           │
│                         il y a 1 h ┘         │
│  ┌ Oui, super! Et toi?                       │
│  └ il y a 55 min                             │
│                                              │
│                  Très bien, merci! ┐         │
│                         il y a 50 min ┘      │
│                               ✓✓ (lu)        │
│                                              │
│  ─────────────────────────────────────────   │
│  ┌──────────────────────────────────────┐    │
│  │ Écrivez un message…               ↗ │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

### Message Bubbles

- Own messages: right-aligned, primary colour background
- Their messages: left-aligned, surface background
- Read receipts: `✓✓` when partner has read

### Polling (No WebSocket in Vanilla JS Phase)

```javascript
// Poll for new messages every 5s when thread is open
let pollInterval;

function startPolling(conversationId) {
  pollInterval = setInterval(async () => {
    const res = await apiFetch(
      `/api/messages/conversations/${conversationId}?since=${lastMessageId}`
    );
    const data = await res?.json();
    if (data?.messages?.length) appendMessages(data.messages);
  }, 5000);
}

function stopPolling() { clearInterval(pollInterval); }
```

> **Note:** WebSocket upgrade is a Phase F6+ enhancement. 5-second polling is acceptable for MVP DMs.

### Mark as Read

```javascript
// On entering a thread, mark as read
await apiFetch(`/api/messages/conversations/${id}/read`, { method: 'PATCH' });
updateDMBadge();
```

### Backend Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| List conversations | GET | `/api/messages/conversations` |
| Start conversation | POST | `/api/messages/conversations` |
| Get messages | GET | `/api/messages/conversations/<id>` |
| Send message | POST | `/api/messages/conversations/<id>` |
| Mark read | PATCH | `/api/messages/conversations/<id>/read` |
| Unread count | GET | `/api/messages/unread-count` |

---

## 📋 COMPONENT 4: Unread DM Badge

Mirrors the notification badge pattern:

```javascript
async function updateDMBadge() {
  const res = await apiFetch('/api/messages/unread-count');
  const { unread_count } = await res.json();
  const badge = document.querySelector('#dm-badge');
  badge.textContent = unread_count > 0 ? Math.min(unread_count, 99) : '';
  badge.hidden = unread_count === 0;
}
setInterval(updateDMBadge, 30000);
```

---

## 📋 COMPONENT 5: Settings Page

**File:** `js/settings.js`  
**Route:** `settings.html`

### Layout (Tabbed)

```
┌──────────────────────────────────────────────┐
│  ⚙️  Paramètres                              │
│                                              │
│  [ Profil ] [ Sécurité ] [ Notifications ]   │
│  ─────────────────────────────────────────   │
│                                              │
│  PROFIL                                      │
│  Nom affiché  ┌──────────────────────────┐   │
│               │ Marie Tremblay           │   │
│               └──────────────────────────┘   │
│  Biographie   ┌──────────────────────────┐   │
│               │                          │   │
│               └──────────────────────────┘   │
│  Langue       ● Français  ○ English           │
│  Visibilité   ● Publique  ○ Privée            │
│                                              │
│  [ Enregistrer les modifications ]           │
└──────────────────────────────────────────────┘
```

### Language Setting

When user changes language in settings, call `setLang()` and trigger `applyTranslations()` — the entire page re-renders in the selected language without reload.

---

## 📋 COMPONENT 6: Security Settings

**Tab:** Sécurité / Security

```
┌──────────────────────────────────────────────┐
│  SÉCURITÉ                                    │
│                                              │
│  Mot de passe                                │
│  ┌──────────────────────────────────────┐    │
│  │ Mot de passe actuel              👁  │    │
│  └──────────────────────────────────────┘    │
│  ┌──────────────────────────────────────┐    │
│  │ Nouveau mot de passe             👁  │    │
│  └──────────────────────────────────────┘    │
│  [ Changer le mot de passe ]                 │
│                                              │
│  ─ Sessions actives ───────────────────────  │
│  💻 macOS · Chrome  · Québec   Actuelle      │
│  📱 iOS   · Safari  · Montréal  [ Révoquer ] │
│  📱 Android · Chrome · Laval   [ Révoquer ]  │
│                                              │
│  [ Révoquer toutes les autres sessions ]     │
│                                              │
│  ─ Authentification à deux facteurs ───────  │
│  ✅ Activée   [ Configurer ]                 │
└──────────────────────────────────────────────┘
```

### Backend Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Change password | POST | `/api/auth/change-password` |
| Get sessions | GET | `/api/auth/sessions` |
| Revoke session | DELETE | `/api/auth/sessions/<id>` |
| Revoke all others | DELETE | `/api/auth/sessions/all` |

---

## 📋 COMPONENT 7: 2FA Setup Flow

**Trigger:** "Configurer" button in Security tab (or post-registration prompt)

### Step 1 — QR Code Display

```
┌─────────────────────────────────────────┐
│  Activer l'authentification à 2 facteurs│
│                                         │
│  1. Ouvrez votre application            │
│     d'authentification                  │
│  2. Scannez ce code QR :                │
│                                         │
│  ┌─────────────────┐                    │
│  │  [QR CODE IMG]  │                    │
│  └─────────────────┘                    │
│                                         │
│  Ou entrez ce code manuellement :       │
│  JBSWY3DPEHPK3PXP                       │
│                                         │
│  [ Copier ]                             │
│                                         │
│  Entrez le code à 6 chiffres            │
│  ┌──────────────────┐                   │
│  │  _ _ _  _ _ _    │                   │
│  └──────────────────┘                   │
│  [ Vérifier et activer ]                │
└─────────────────────────────────────────┘
```

### Step 2 — Backup Codes

```
┌─────────────────────────────────────────┐
│  ✅ 2FA activé !                        │
│                                         │
│  Codes de secours — conservez-les !     │
│  ┌─────────────────────────────────┐    │
│  │  a1b2-c3d4   e5f6-g7h8         │    │
│  │  i9j0-k1l2   m3n4-o5p6         │    │
│  └─────────────────────────────────┘    │
│  [ Télécharger ]   [ Copier ]           │
│                                         │
│  ⚠️ Ces codes ne seront affichés        │
│  qu'une seule fois.                     │
└─────────────────────────────────────────┘
```

### QR Code Rendering

Use `qrcode.js` (CDN) to render the TOTP URI server-side response as a QR image:

```html
<script src="https://cdn.jsdelivr.net/npm/qrcode/build/qrcode.min.js"></script>
```

```javascript
const { totp_uri } = await res.json();
QRCode.toCanvas(document.querySelector('#qr-canvas'), totp_uri);
```

### Backend Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Init 2FA setup | POST | `/api/auth/2fa/enable` |
| Verify + activate | POST | `/api/auth/2fa/verify` |
| Disable 2FA | DELETE | `/api/auth/2fa` |

---

## 📋 COMPONENT 8: Push Notification Permission

**Trigger:** Settings → Notifications tab, or prompted after first login

```javascript
async function requestPushPermission() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    showToast(t('push.not_supported'));
    return;
  }

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') return;

  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
  });

  await apiFetch('/api/push/subscribe', {
    method: 'POST',
    body: JSON.stringify(subscription)
  });
}
```

> **Note:** Requires a service worker file (`sw.js`) and VAPID public key from backend config. This is a "Nice to Have" — gracefully skipped if not configured.

---

## 🔗 BACKEND ENDPOINTS USED IN PHASE F5

| Action | Method | Endpoint |
|--------|--------|----------|
| Notifications list | GET | `/api/notifications` |
| Unread notif count | Included in `GET /api/notifications` response |
| Mark notif read | PATCH | `/api/notifications/<id>/read` |
| Mark all read | POST | `/api/notifications/read-all` |
| DM conversations | GET | `/api/messages/conversations` |
| Start DM | POST | `/api/messages/conversations` |
| DM messages | GET | `/api/messages/conversations/<id>` |
| Send DM | POST | `/api/messages/conversations/<id>` |
| Mark DMs read | PATCH | `/api/messages/conversations/<id>/read` |
| DM unread count | GET | `/api/messages/unread-count` |
| Update profile | PATCH | `/api/auth/update-profile` |
| Update privacy settings | PATCH | `/api/auth/privacy-settings` |
| Update preferences | PATCH | `/api/auth/preferences` |
| Upload avatar | POST | `/api/auth/upload-profile-pic` |
| Change password | POST | `/api/auth/change-password` |
| Get sessions | GET | `/api/auth/sessions` |
| Revoke session | DELETE | `/api/auth/sessions/<id>` |
| Revoke all others | DELETE | `/api/auth/sessions/all` |
| 2FA setup | POST | `/api/auth/2fa/enable` |
| 2FA verify | POST | `/api/auth/2fa/verify` |
| 2FA disable | POST | `/api/auth/2fa/disable` |
| Regenerate backup codes | GET | `/api/auth/2fa/backup-codes` |
| Push subscribe | POST | `/api/push/subscribe` |

---

## ✅ SUCCESS CRITERIA

**Phase F5 Complete When:**

- [x] Notification badge in nav shows unread counts
- [~] Notification list works, but bilingual message coverage is incomplete
- [x] Mark-as-read works individually and "mark all read" works
- [x] DM conversation list shows conversations with preview and unread counts
- [x] DM thread view renders message history and distinguishes own/other bubbles
- [~] Send message works correctly, but it refreshes thread state instead of using a truly optimistic append
- [x] Thread polling refreshes while open
- [x] Mark-as-read fires on entering a thread, and the DM badge updates
- [x] Settings profile tab edits save successfully
- [~] Language preference is persisted, but the page does not fully re-render all hardcoded strings without reload-level coverage
- [x] Security tab password change works with validation
- [x] Active sessions list shows sessions, and revoke-one / revoke-all flows work
- [x] 2FA flow renders QR/secret, verifies code, and shows or regenerates backup codes

---

**Last Updated:** 2026-03-26
**Status:** ✅ Implemented in code
**Blockers:** Phase F1 + F2 must be complete  
**Depends on:** Backend Phases 5–6 (notifications, DMs, sessions, 2FA, push) ✅ Complete

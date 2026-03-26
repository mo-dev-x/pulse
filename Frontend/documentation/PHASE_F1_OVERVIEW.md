# 🔵 PHASE F1 OVERVIEW — FOUNDATION & AUTH SHELL

**Pulse Frontend — Vanilla JS · Université Laval**

**Status:** ✅ Implemented in code
**Priority:** Critical — Everything depends on this  
**Estimated Time:** 4–6 days  
**Context:** Backend Phases 1–6 are 100% complete. Auth endpoints, email verification, password reset, 2FA, and session management are all live. This phase wires the frontend to the existing auth system and establishes the design foundation every subsequent phase builds on.

> **Design principle for Phase F1:** No page should exist without a bilingual fallback. Every string is a translation key from day one. Retrofitting i18n after 6 phases of hardcoded strings is painful — ask the backend team.

> **Implementation note:** The auth shell, router, design tokens, theme helpers, and auth pages are implemented. The original "every string is a translation key from day one" goal was only partially met, so translation coverage outside the auth core still has follow-up work.

---

## 🎯 PHASE F1 GOALS

- Establish the CSS design system (tokens, reset, base typography)
- Build the bilingual i18n module (`i18n.js`) — FR default, EN toggle, persisted preference
- Extend `auth.js` with 401 interceptor, token refresh awareness, and logout-on-expiry
- Build a polished **Login** page — bilingual validation, error states, "remember me"
- Build a polished **Registration** page — @ulaval.ca enforcement, password strength meter
- Build the **Email Verification** waiting screen
- Build the **Password Reset** flow (request email + confirm new password)
- Build the **hash-based client router** (`router.js`) for the SPA shell
- Stub all remaining pages so routing is wired before Phase F2 content is added

---

## 📊 PHASE F1 STATUS OVERVIEW

| Component | Priority | Status | Est. Days |
|-----------|----------|--------|-----------|
| CSS design tokens + base | Must Have | ✅ Implemented | 0.5 |
| i18n module (FR/EN) | Must Have | ✅ Implemented | 0.5 |
| `auth.js` extension | Must Have | ✅ Implemented | 0.5 |
| Login page (full) | Must Have | ✅ Implemented | 1 |
| Registration page (full) | Must Have | ✅ Implemented | 1 |
| Email verification screen | Must Have | ✅ Implemented | 0.5 |
| Password reset flow | Should Have | ✅ Implemented | 1 |
| Hash router + page stubs | Should Have | ✅ Implemented and expanded beyond the original stub set | 0.5 |
| 2FA login step (TOTP prompt) | Nice to Have | ~ No dedicated frontend login prompt is implemented | 0.5 |

**Phase F1A Progress (Must Have):** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100%
**Phase F1B Progress (Should Have):** 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100%
**Overall Phase F1 Progress:** 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜ ~95%

## 🧩 SHIPPED IMPLEMENTATION

| Area | Shipped code |
|------|--------------|
| Tokens + base | `css/variables.css`, `css/base.css`, `css/components.css` |
| Auth pages | `login.html`, `register.html`, `verify-email.html`, `forgot-password.html`, `reset-password.html` |
| Auth logic | `js/auth.js`, `js/login.js`, `js/register.js`, `js/verify_email.js`, `js/forgot_password.js`, `js/reset_password.js` |
| i18n + routing | `js/i18n.js`, `js/router.js` |
| Notable deviation | No dedicated frontend 2FA login prompt; translation coverage extends beyond auth, but is not total |

---

## 📋 COMPONENT 1: CSS Design System

**Timeline:** Day 1 (morning)  
**Files:** `css/variables.css`, `css/base.css`, `css/components.css`

### `variables.css` — Design Tokens

```css
:root {
  /* Brand */
  --color-primary:        #E63946;
  --color-primary-hover:  #C1121F;
  --color-primary-light:  rgba(230, 57, 70, 0.1);

  /* Backgrounds */
  --color-bg:             #FFFFFF;
  --color-surface:        #F8F9FA;
  --color-surface-2:      #F1F3F5;

  /* Borders */
  --color-border:         #E9ECEF;
  --color-border-focus:   #E63946;

  /* Text */
  --color-text:           #212529;
  --color-text-muted:     #6C757D;
  --color-text-inverse:   #FFFFFF;

  /* Mood Semantic */
  --color-positive:       #2ECC71;
  --color-neutral:        #F39C12;
  --color-negative:       #E74C3C;

  /* Emotions */
  --emotion-joy:          #FFD93D;
  --emotion-sadness:      #74B9FF;
  --emotion-anger:        #E74C3C;
  --emotion-fear:         #A29BFE;
  --emotion-surprise:     #FD79A8;
  --emotion-disgust:      #55EFC4;

  /* Spacing scale */
  --space-1: 4px;   --space-2: 8px;   --space-3: 12px;
  --space-4: 16px;  --space-5: 24px;  --space-6: 32px;
  --space-7: 48px;  --space-8: 64px;

  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-size-xs:  12px;  --font-size-sm: 14px;
  --font-size-md:  16px;  --font-size-lg: 18px;
  --font-size-xl:  24px;  --font-size-2xl: 32px;

  /* Radius */
  --radius-sm: 6px;  --radius-md: 12px;  --radius-lg: 20px;  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.10);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);

  /* Transitions */
  --transition-fast: 120ms ease;
  --transition-base: 200ms ease;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary:    #FF6B6B;
    --color-bg:         #0F1117;
    --color-surface:    #1A1D24;
    --color-surface-2:  #23262F;
    --color-border:     #2D3139;
    --color-text:       #E9ECEF;
    --color-text-muted: #868E96;
  }
}

/* JS-controlled dark mode (overrides system) */
[data-theme="dark"]  { /* same as @media dark */ }
[data-theme="light"] { /* same as :root light values */ }
```

### `base.css` — Reset + Typography

- CSS reset (box-sizing, margin 0, padding 0)
- Smooth scroll, `font-family: var(--font-sans)`
- Link, focus ring, selection styles
- `.sr-only` for screen reader text (accessibility)
- Utility classes: `.text-muted`, `.text-positive`, `.text-negative`, `.text-neutral`

### `components.css` — Reusable UI

Shared components needed across all pages:

| Component | Class | Notes |
|-----------|-------|-------|
| Button primary | `.btn-primary` | Red, full radius |
| Button secondary | `.btn-secondary` | Ghost border |
| Button ghost | `.btn-ghost` | Text-only |
| Input field | `.input` | Focus ring, error state |
| Form group | `.form-group` | Label + input + error msg |
| Card | `.card` | Surface bg, shadow-sm |
| Badge | `.badge` | Small pill label |
| Spinner | `.spinner` | CSS animation |
| Toast | `.toast` | Success / error / info |
| Modal | `.modal` + `.modal-overlay` | Accessible focus trap |
| Language toggle | `.lang-toggle` | FR / EN switcher |

---

## 📋 COMPONENT 2: i18n Module

**Timeline:** Day 1 (afternoon)  
**File:** `js/i18n.js`

### Architecture

```javascript
// js/i18n.js
const TRANSLATIONS = {
  fr: {
    // Auth
    'auth.login.title':          'Connexion',
    'auth.login.email':          'Adresse courriel',
    'auth.login.password':       'Mot de passe',
    'auth.login.submit':         'Se connecter',
    'auth.login.no_account':     "Pas de compte ? S'inscrire",
    'auth.login.forgot':         'Mot de passe oublié ?',
    'auth.register.title':       'Créer un compte',
    'auth.register.email_hint':  'Adresse @ulaval.ca requise',
    'auth.register.submit':      "S'inscrire",
    'auth.verify.title':         'Vérifiez votre courriel',
    'auth.verify.body':          'Un lien de vérification a été envoyé à {email}.',
    'auth.reset.title':          'Réinitialiser le mot de passe',
    // Errors
    'error.invalid_email':       'Adresse courriel invalide',
    'error.ulaval_only':         'Seules les adresses @ulaval.ca sont acceptées',
    'error.password_short':      'Le mot de passe doit contenir au moins 8 caractères',
    'error.network':             'Erreur de connexion. Veuillez réessayer.',
    'error.invalid_credentials': 'Courriel ou mot de passe incorrect',
    // Generic
    'action.save':               'Enregistrer',
    'action.cancel':             'Annuler',
    'action.close':              'Fermer',
    'action.loading':            'Chargement…',
  },
  en: {
    'auth.login.title':          'Sign In',
    'auth.login.email':          'Email address',
    'auth.login.password':       'Password',
    'auth.login.submit':         'Sign in',
    'auth.login.no_account':     "No account? Register",
    'auth.login.forgot':         'Forgot password?',
    'auth.register.title':       'Create Account',
    'auth.register.email_hint':  '@ulaval.ca address required',
    'auth.register.submit':      'Register',
    'auth.verify.title':         'Check your email',
    'auth.verify.body':          'A verification link was sent to {email}.',
    'auth.reset.title':          'Reset Password',
    'error.invalid_email':       'Invalid email address',
    'error.ulaval_only':         'Only @ulaval.ca addresses are accepted',
    'error.password_short':      'Password must be at least 8 characters',
    'error.network':             'Connection error. Please try again.',
    'error.invalid_credentials': 'Incorrect email or password',
    'action.save':               'Save',
    'action.cancel':             'Cancel',
    'action.close':              'Close',
    'action.loading':            'Loading…',
  }
};

let currentLang = localStorage.getItem('pulse_lang') || 'fr';

export function t(key, vars = {}) {
  let str = TRANSLATIONS[currentLang]?.[key] ?? TRANSLATIONS['fr']?.[key] ?? key;
  // Replace {var} placeholders
  return str.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? `{${k}}`);
}

export function setLang(lang) {
  currentLang = lang;
  localStorage.setItem('pulse_lang', lang);
  document.documentElement.setAttribute('lang', lang);
  document.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));
}

export function getLang() { return currentLang; }

export function applyTranslations(root = document) {
  root.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  root.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
}
```

### Usage in HTML

```html
<h1 data-i18n="auth.login.title">Connexion</h1>
<input placeholder="" data-i18n-placeholder="auth.login.email">
```

The `data-i18n` attribute holds the translation key. The hardcoded fallback text in HTML is French (default). When `applyTranslations()` runs, it replaces text content automatically.

---

## 📋 COMPONENT 3: auth.js Extension

**Timeline:** Day 1 (afternoon)  
**File:** `js/auth.js` (extend existing)

### Additions to Existing File

```javascript
// Add to existing auth.js

// 401 interceptor — redirect to login on expired token
export async function apiFetch(url, options = {}) {
  const token = getToken();
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    }
  });

  if (res.status === 401) {
    clearToken();
    window.location.hash = '#login';
    return null;
  }

  return res;
}

// Check auth status and redirect accordingly
export function requireAuth() {
  if (!getToken()) {
    window.location.hash = '#login';
    return false;
  }
  return true;
}

export function requireGuest() {
  if (getToken()) {
    window.location.hash = '#feed';
    return false;
  }
  return true;
}
```

---

## 📋 COMPONENT 4: Login Page

**Timeline:** Day 2  
**Files:** `login.html`, `css/login.css` (extend), `js/login.js` (extend)

### Layout

```
┌─────────────────────────────────┐
│  🫀 Pulse          [FR | EN]    │
│                                 │
│     Connexion                   │
│                                 │
│  ┌─────────────────────────┐    │
│  │ Adresse courriel        │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │ Mot de passe        👁  │    │
│  └─────────────────────────┘    │
│                                 │
│  [ Se connecter          ]      │
│                                 │
│  Mot de passe oublié ?          │
│  Pas de compte ? S'inscrire     │
│                                 │
│  ──── ou ────                   │
│  [ Continuer avec OIDC Laval ]  │
└─────────────────────────────────┘
```

### States to Handle

| State | Behaviour |
|-------|-----------|
| Empty submit | Show inline validation errors |
| Invalid email | `error.invalid_email` message |
| Non-@ulaval.ca | `error.ulaval_only` message |
| Wrong credentials | `error.invalid_credentials` banner |
| Network error | `error.network` banner |
| Loading | Disable button + show spinner |
| 2FA required | Show TOTP input step (Phase F1 nice-to-have) |
| Success | Redirect to `#feed` |
| Unverified email | Show re-send verification link |

### 2FA Step (Nice to Have — F1)

```
┌─────────────────────────────────┐
│  🔐 Vérification en deux étapes │
│                                 │
│  Entrez le code de votre        │
│  application d'authentification │
│                                 │
│  ┌──────────────────────────┐   │
│  │   _ _ _  _ _ _           │   │
│  └──────────────────────────┘   │
│                                 │
│  [ Vérifier ]                   │
│  Utiliser un code de secours    │
└─────────────────────────────────┘
```

Backend endpoint: `POST /api/auth/2fa/verify`

---

## 📋 COMPONENT 5: Registration Page

**Timeline:** Day 3  
**Files:** `register.html`, `js/register.js` (extend)

### Layout

```
┌─────────────────────────────────┐
│  🫀 Pulse          [FR | EN]    │
│                                 │
│     Créer un compte             │
│  @ulaval.ca requis              │
│                                 │
│  Prénom        Nom              │
│  ┌──────────┐ ┌──────────┐     │
│  └──────────┘ └──────────┘     │
│                                 │
│  Nom d'utilisateur              │
│  ┌─────────────────────────┐    │
│  └─────────────────────────┘    │
│                                 │
│  Adresse courriel               │
│  ┌─────────────────────────┐    │
│  │ prenom.nom@ulaval.ca    │    │
│  └─────────────────────────┘    │
│                                 │
│  Mot de passe                   │
│  ┌─────────────────────────┐    │
│  │                     👁  │    │
│  └─────────────────────────┘    │
│  ████░░░░ Moyen                 │  ← password strength bar
│                                 │
│  [ S'inscrire ]                 │
│                                 │
│  Déjà un compte ? Se connecter  │
└─────────────────────────────────┘
```

### Validations (client-side mirror of backend)

| Field | Rule |
|-------|------|
| Email | Must end with `@ulaval.ca` (case-insensitive) |
| Username | 3–30 chars, alphanumeric + `_` + `-` |
| Password | Min 8 chars, strength meter (weak/medium/strong) |
| Display name | 1–50 chars |

### Password Strength Meter

```javascript
function getStrength(password) {
  let score = 0;
  if (password.length >= 8)  score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  return ['', 'weak', 'medium', 'strong', 'strong', 'strong'][score];
}
```

---

## 📋 COMPONENT 6: Email Verification Screen

**Timeline:** Day 3  
**File:** Add to `register.html` or create `verify.html`

### Layout

```
┌─────────────────────────────────┐
│  🫀 Pulse                       │
│                                 │
│       ✉️                        │
│                                 │
│   Vérifiez votre courriel       │
│                                 │
│  Un lien de vérification a été  │
│  envoyé à prenom.nom@ulaval.ca  │
│                                 │
│  [ Renvoyer le courriel ]       │
│                                 │
│  ← Retour à la connexion        │
└─────────────────────────────────┘
```

Backend endpoint: `POST /api/auth/send-verification`

---

## 📋 COMPONENT 7: Password Reset Flow

**Timeline:** Day 4  
**Files:** `reset.html` or modal inside `login.html`

### Step 1 — Request

```
┌─────────────────────────────────┐
│  Mot de passe oublié            │
│                                 │
│  Entrez votre adresse courriel  │
│  ┌─────────────────────────┐    │
│  │                         │    │
│  └─────────────────────────┘    │
│                                 │
│  [ Envoyer le lien ]            │
│  ← Retour à la connexion        │
└─────────────────────────────────┘
```

Backend endpoint: `POST /api/auth/forgot-password`

### Step 2 — Confirm (via email link `?token=...`)

```
┌─────────────────────────────────┐
│  Nouveau mot de passe           │
│  ┌─────────────────────────┐    │
│  │                     👁  │    │
│  └─────────────────────────┘    │
│  Confirmer le mot de passe      │
│  ┌─────────────────────────┐    │
│  └─────────────────────────┘    │
│  [ Réinitialiser ]              │
└─────────────────────────────────┘
```

Backend endpoint: `POST /api/auth/reset-password`

---

## 📋 COMPONENT 8: Hash Router

**Timeline:** Day 4  
**File:** `js/router.js`

### Architecture

```javascript
// js/router.js
const routes = {
  '#login':         () => import('./login.js'),
  '#register':      () => import('./register.js'),
  '#feed':          () => { requireAuth(); import('./feed.js'); },
  '#profile':       () => { requireAuth(); import('./profile.js'); },
  '#messages':      () => { requireAuth(); import('./messages.js'); },
  '#notifications': () => { requireAuth(); import('./notifications.js'); },
  '#analytics':     () => { requireAuth(); import('./analytics.js'); },
  '#settings':      () => { requireAuth(); import('./settings.js'); },
  '#search':        () => { requireAuth(); import('./search.js'); },
};

function route() {
  const hash = window.location.hash || '#feed';
  const handler = routes[hash.split('?')[0]];
  if (handler) handler();
  else routes['#feed']?.();
}

window.addEventListener('hashchange', route);
document.addEventListener('DOMContentLoaded', route);
```

### Page Stubs

Create minimal HTML stubs for all pages so routing works before Phase F2 fills them in:

- `feed.html` — already exists, extend
- `profile.html` — stub
- `messages.html` — stub
- `notifications.html` — stub
- `analytics.html` — stub
- `settings.html` — stub

---

## 🔗 BACKEND ENDPOINTS USED IN PHASE F1

| Action | Method | Endpoint |
|--------|--------|----------|
| Register | POST | `/api/auth/register` |
| Login | POST | `/api/auth/login` |
| Logout | POST | `/api/auth/logout` |
| Verify email | GET | `/api/auth/verify-email/<token>` |
| Resend verification | POST | `/api/auth/send-verification` |
| Request password reset | POST | `/api/auth/forgot-password` |
| Confirm password reset | POST | `/api/auth/reset-password` |
| Verify 2FA TOTP | POST | `/api/auth/2fa/verify` |

---

## ✅ SUCCESS CRITERIA

**Phase F1 Complete When:**

- [x] `variables.css` defines the active design tokens and `theme.js` drives `data-theme`
- [x] `i18n.js` exports the translation helpers used by the auth shell
- [x] Language toggle persists to `localStorage` and survives page reload
- [x] `auth.js` has 401 cleanup/redirect behaviour for expired sessions
- [x] Login page has inline validation, loading state, and redirect on success
- [x] Registration page enforces `@ulaval.ca` and routes to the verification screen
- [x] Email verification screen is displayed after registration
- [x] Password reset request + confirm forms are wired to backend
- [x] Hash router works and now resolves more than the original 8 routes
- [~] French-by-default / English-toggle behaviour exists, but all-page translation coverage is still incomplete

---

**Last Updated:** 2026-03-26
**Status:** ✅ Implemented in code
**Blockers:** None  
**Depends on:** Backend Phase 1–2 auth endpoints (✅ Complete)

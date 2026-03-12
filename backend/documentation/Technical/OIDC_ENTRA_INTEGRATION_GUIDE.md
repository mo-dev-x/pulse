# OIDC / Microsoft Entra Integration Guide

## Purpose
Configure institutional login for Pulse using OpenID Connect (OAuth2 code flow) with Microsoft Entra ID.

## Current Status
- OIDC code is implemented but intentionally disabled by default.
- Active authentication path is currently `email + password + email verification`.
- To re-enable institutional login later, follow `OIDC_REENABLE_PLAYBOOK.md`.

## Required `.env` Variables

```env
ENABLE_OIDC_AUTH=true
OIDC_AUTHORIZE_URL=https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/authorize
OIDC_TOKEN_URL=https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token
OIDC_USERINFO_URL=https://graph.microsoft.com/oidc/userinfo
OIDC_CLIENT_ID=<app-client-id>
OIDC_CLIENT_SECRET=<app-client-secret>
OIDC_REDIRECT_URI=http://127.0.0.1:5000/api/auth/oidc/callback
OIDC_SCOPE=openid profile email
```

## Backend Endpoints

- `GET /api/auth/oidc/login`
  - Redirects to the Entra authorize endpoint.
- `GET /api/auth/oidc/callback`
  - Exchanges `code` for tokens.
  - Reads user claims from userinfo (or ID token fallback).
  - Upserts local user and sets `is_verified=True`.

## Identity Mapping

- Local unique external identity is currently stored in legacy column `users.cas_username`.
- Collision behavior:
  - If that external identity is already linked to another local account, API returns `409`.

## Notes

- Legacy routes `/api/auth/cas/login` and `/api/auth/cas/callback` now redirect to OIDC routes for compatibility.
- For production:
  - Use HTTPS callback URL.
  - Restrict app registration to expected tenant and domains.

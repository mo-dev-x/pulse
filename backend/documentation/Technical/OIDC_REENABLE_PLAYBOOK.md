# OIDC Re-enable Playbook (When University Access Is Available)

## Goal
Restore institutional login (`/api/auth/oidc/*`) without rebuilding the feature from scratch.

## Current Baseline (as of 2026-02-16)
- OIDC routes and user-mapping logic still exist in `backend/app/routes/auth.py`.
- OIDC is guarded by `ENABLE_OIDC_AUTH` and defaults to `false`.
- Email verification remains the active production auth gate.

## Step-by-Step Re-enable
1. Confirm university/IT access for a Microsoft Entra app registration.
2. Collect tenant-specific values:
   - `OIDC_AUTHORIZE_URL`
   - `OIDC_TOKEN_URL`
   - `OIDC_USERINFO_URL`
   - `OIDC_CLIENT_ID`
   - `OIDC_CLIENT_SECRET`
   - Production `OIDC_REDIRECT_URI`
3. Update backend environment:
   - Set `ENABLE_OIDC_AUTH=true`.
   - Fill all OIDC variables in `backend/.env`.
4. Restart backend and verify routes:
   - `GET /api/auth/oidc/login` should return a redirect, not `503`.
   - `GET /api/auth/cas/login` should redirect to `/api/auth/oidc/login`.
5. Run automated tests:
   - `python -m pytest backend/tests/test_oidc_integration.py`
   - `python -m pytest backend/tests/test_email_verification.py backend/tests/test_password_reset.py`
6. Validate DB behavior on staging:
   - Existing users can still use email/password.
   - New OIDC users are created with `is_verified=True`.
   - Identity collisions on `cas_username` return `409`.
7. Frontend rollout:
   - Add or re-enable institutional login button/flow.
   - Keep email/password path as fallback unless policy requires SSO-only.
8. Production readiness checks:
   - HTTPS callback URL only.
   - Restrict tenant and expected email domain.
   - Monitor auth errors and login success rates after release.

## Rollback Plan
1. Set `ENABLE_OIDC_AUTH=false`.
2. Restart backend.
3. Email/password + verification continues to function.

## Reference
- `backend/documentation/Technical/OIDC_ENTRA_INTEGRATION_GUIDE.md`

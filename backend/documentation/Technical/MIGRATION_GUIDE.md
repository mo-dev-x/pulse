# Phase 5A Migration Guide (OIDC/Entra + Verified Login)

## Purpose
This runbook defines how existing password users migrate safely to institutional OIDC identity in Phase 5A.

## Final Policy
- Login is allowed only for `is_verified = true`.
- Verification can come from:
  - Email verification link, or
  - CAS authentication callback.
- Institutional identity (`cas_username` legacy column) is unique and cannot be linked to multiple accounts.

## Migration Strategy
### 1. Existing Users (No CAS Yet)
- Keep current account and data.
- User can verify by email (one-time link) and continue with password login.
- When user authenticates with CAS later:
  - Account is linked by matching `email` (`@ulaval.ca`),
  - `cas_username`, `account_type`, and `is_verified` are updated.

### 2. New CAS Users
- If CAS email does not exist in DB:
  - Create new account from CAS attributes,
  - Set `is_verified = true`,
  - Store `cas_username` and `account_type`.

### 3. CAS Collision Handling
- If incoming CAS identity is already linked to another account:
  - Reject callback with `409 Conflict`,
  - Return localized `cas_identity_conflict` message,
  - Do not mutate either account.

## Backend Behavior Reference
- Endpoint: `GET /api/auth/cas/callback`
- Collision check:
  - Find owner by `cas_username`,
  - If owner exists and is not the same account resolved by email => `409`.

## Validation Checklist
- [x] New CAS user is created and verified.
- [x] Existing email-matched user is linked and verified.
- [x] Collision on create path returns `409`.
- [x] Collision on update path returns `409`.
- [x] No duplicate `cas_username` links allowed.

## Tests
- `backend/tests/test_cas_integration.py`
  - create user via CAS
  - update existing user via CAS
  - invalid ticket
  - collision on create path
  - collision on update path

## Operational Notes
- Ensure `users` table includes:
  - `is_verified`, `cas_username`, `account_type`
- Ensure CAS callback URL and CAS server URL are configured in `.env`.
- Production still requires real CAS credentials and HTTPS callback.

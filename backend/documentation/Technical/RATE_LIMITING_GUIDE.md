# Rate Limiting Guide

## Purpose
Document the Phase 6 abuse-prevention layer and how limits are configured.

## Core Dependency
- `flask-limiter`

## Strategy
- Authenticated requests prefer a user-based key
- Anonymous requests fall back to remote IP
- Limits are configured per endpoint category

## Covered Areas
- login attempts
- forgot-password flow
- comment creation
- post creation
- reactions
- search endpoints

## Configuration
Important app config values:
- `RATELIMIT_STORAGE_URL`
- `REDIS_URL` for production-compatible Redis setups

## Key Function
- `rate_limit_key_user()` prefers JWT identity when present
- If no authenticated user is available, the limiter uses remote IP

## Production Notes
- In development/tests, in-memory storage is acceptable
- In production, Redis-backed storage is recommended for correctness across processes

## Implementation Notes
- App init: `backend/app/__init__.py`
- Example protected routes:
  - `backend/app/routes/auth.py`
  - `backend/app/routes/comments.py`
  - `backend/app/routes/reactions.py`
  - `backend/app/routes/search.py`

## Validation
1. Exceed the configured login limit and confirm `429`.
2. Confirm `Retry-After` metadata is returned.
3. Verify two different users do not share the same authenticated write limit bucket.

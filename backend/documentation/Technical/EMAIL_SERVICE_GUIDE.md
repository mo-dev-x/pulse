# Email Service Guide

## Purpose
Configure and operate Pulse outbound email for verification, password reset, and notification-style messages.

## Current Scope
- Verification emails: `send_verification_email`
- Password reset emails: `send_password_reset_email`
- Notification emails: `send_notification_email`
- SMTP transport is configured through `backend/.env`

## Required `.env` Variables

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@pulse.ulaval.ca
SMTP_PASSWORD=<smtp-password>
SMTP_FROM=noreply@pulse.ulaval.ca
SMTP_USE_TLS=true
FRONTEND_URL=https://pulse.ulaval.ca
```

## Runtime Behavior
- If `SMTP_HOST`, `SMTP_PORT`, or `SMTP_FROM` is missing:
  - Email delivery is skipped.
  - API flows still succeed when designed to be non-blocking.
  - Backend logs include a warning explaining why delivery did not occur.
- Verification and password reset tokens are still generated and persisted before send is attempted.

## Backend References
- Service: `backend/app/services/email_service.py`
- Registration flow: `backend/app/routes/auth.py`
- Verification resend: `POST /api/auth/send-verification`
- Password reset request: `POST /api/auth/forgot-password`

## Supported Email Flows
### 1. Verification Email
- Token validity: 24 hours
- Frontend link:
  - `${FRONTEND_URL}/verify-email?token=<token>`

### 2. Password Reset Email
- Token validity: 1 hour
- Frontend link:
  - `${FRONTEND_URL}/reset-password?token=<token>`

### 3. Notification Email
- Intended for optional product notifications.
- Delivery respects `user.email_notifications`.

## Local Verification
1. Set SMTP values in `backend/.env`.
2. Restart backend.
3. Register a new user.
4. Confirm warning logs disappear and the verification message is delivered.
5. Trigger `POST /api/auth/forgot-password` for a known account and confirm delivery.

## Troubleshooting
- `SMTP is not configured`
  - Required SMTP variables are missing.
- Connection timeout or auth failure
  - Re-check host, port, credentials, firewall, and TLS requirement.
- Links point to wrong frontend
  - Correct `FRONTEND_URL` in `backend/.env`.

## Operational Notes
- Use a dedicated sender mailbox.
- Prefer an SMTP relay with rate limits and monitoring.
- In production, keep SMTP credentials out of source control and rotate them when access changes.

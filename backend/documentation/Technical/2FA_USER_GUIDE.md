# 2FA User Guide

## Purpose
Explain how users enable, use, and recover Pulse two-factor authentication.

## What 2FA Protects
- Password-only login is upgraded with a second factor.
- After 2FA is enabled, login requires:
  - Password, and
  - Current authenticator code or a backup code

## Endpoints
- `POST /api/auth/2fa/enable`
- `POST /api/auth/2fa/verify`
- `POST /api/auth/2fa/disable`
- `GET /api/auth/2fa/backup-codes`

## Enable 2FA
1. Sign in to Pulse.
2. Start setup by calling `POST /api/auth/2fa/enable`.
3. Pulse returns:
   - `totp_secret`
   - `provisioning_uri`
   - `qr_code_data_url` when QR rendering is available
   - `backup_codes`
4. Add the account to an authenticator app:
   - Scan the QR code when available, or
   - Enter the secret manually
5. Submit one current authenticator code to `POST /api/auth/2fa/verify`.
6. After verification succeeds, `totp_enabled` becomes `true`.

## Login Flow
- If 2FA is enabled and no code is provided:
  - Login returns `401` with `requires_2fa=true`
- Complete login by resubmitting with:
  - `totp_code`, or
  - `backup_code`

## Backup Codes
- Pulse generates 10 backup codes during setup.
- Each backup code is single use.
- Regenerate the set with `GET /api/auth/2fa/backup-codes` after setup is complete.
- Store them outside the device that runs the authenticator app.

## Disable 2FA
- Call `POST /api/auth/2fa/disable` with:
  - a valid `code`, or
  - a valid `backup_code`
- On success, Pulse clears:
  - `totp_enabled`
  - `totp_secret`
  - `backup_codes`

## Recovery Guidance
- If the authenticator app is unavailable:
  - Use a backup code
- If all backup codes are gone:
  - The current backend does not yet provide admin-assisted recovery flow
  - Keep at least one backup code stored safely before relying on 2FA daily

## Recommended Authenticator Apps
- 1Password
- Bitwarden Authenticator
- Google Authenticator
- Microsoft Authenticator
- Authy

## Operational Notes
- QR rendering requires `qrcode` in the backend virtualenv.
- Even without QR rendering, 2FA still works using the returned secret and provisioning URI.

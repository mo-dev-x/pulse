# Moderation Guide

## Purpose
Document the Phase 6 reporting and admin moderation workflow.

## Endpoints
- `POST /api/reports`
- `GET /api/admin/reports`
- `PATCH /api/admin/reports/<id>`
- `DELETE /api/admin/posts/<id>`
- `GET /api/admin/flagged`

## Report Flow
1. A user submits a report against a post, comment, or user.
2. The report is stored with `status='pending'`.
3. Admins review pending reports from the moderation queue.
4. Admins can dismiss, hide content, warn a user, or deactivate a user.

## Auto-Flag Behavior
- Posts are not deleted automatically on report submission
- Repeated recent reports can auto-flag and hide a post pending review
- Auto-flag evaluation now runs through the background job layer

## Admin Auditability
- Admin moderation actions write to `security_logs`
- Hidden or deleted content remains traceable through admin events

## Privacy and Safety Rules
- Users cannot report their own content
- Duplicate reports from the same user for the same target are blocked
- Moderation visibility is server-side enforced

## Implementation Notes
- Model: `backend/app/models/report.py`
- Routes: `backend/app/routes/reports.py`
- Background moderation task: `backend/app/tasks/moderation_tasks.py`

## Validation
1. Submit a report for a post as another user.
2. Confirm it appears in `/api/admin/reports`.
3. Apply `hide_content` and confirm the post is hidden.
4. Submit enough reports to trigger auto-flagging.
5. Confirm moderation actions appear in `security_logs`.

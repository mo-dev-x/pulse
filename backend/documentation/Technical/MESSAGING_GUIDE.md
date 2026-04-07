# Messaging Guide

## Purpose
Document the direct messaging system: conversations, text messages, voice messages, and media (image/video) messages.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/messages/conversations` | List user's conversations |
| POST | `/api/messages/conversations` | Create or reuse a conversation |
| GET | `/api/messages/conversations/<id>` | Fetch messages in a thread |
| POST | `/api/messages/conversations/<id>` | Send a text message |
| PATCH | `/api/messages/conversations/<id>/read` | Mark conversation as read |
| GET | `/api/messages/unread-count` | Unread conversation count |
| POST | `/api/messages/conversations/<id>/audio` | Send a voice/audio message |
| POST | `/api/messages/conversations/<id>/media` | Send an image or video |

## Conversation Model
- One conversation exists per user pair
- Participants are stored in sorted order:
  - `participant_a = min(user_id_1, user_id_2)`
  - `participant_b = max(user_id_1, user_id_2)`
- Duplicate conversation creation is prevented by a unique constraint

## Behavioral Rules
- Users cannot message themselves
- Deactivated accounts are not messageable
- Non-participants cannot read or write in a conversation
- Creating the same conversation twice returns the existing thread
- Messages support unread counts and read receipts

## Media Message Convention
Audio, image, and video messages reuse the `content` text field with a prefix that signals the media type:

| Type | Content format | Allowed extensions |
|------|---------------|--------------------|
| Voice/audio | `[audio]/api/uploads/<filename>` | webm, ogg, mp4, m4a, wav, opus |
| Image | `[image]/api/uploads/<filename>` | jpg, jpeg, png, gif, webp |
| Video | `[video]/api/uploads/<filename>` | mp4, mov, webm |

The frontend detects these prefixes in `renderBubbleContent()` and renders the appropriate `<audio>`, `<img>`, or `<video>` element. Plain text messages have no prefix.

### Audio recording (frontend)
The browser `MediaRecorder` API captures audio chunks in `ondataavailable`, assembles them into a `Blob` on `onstop`, and sends it as `multipart/form-data` to the `/audio` endpoint. The MIME type is chosen dynamically via `MediaRecorder.isTypeSupported()` (prefers `audio/webm;codecs=opus`, falls back to `audio/ogg` then `audio/mp4`).

## Smooth Polling
The frontend polls for new messages every 5 seconds using `lastKnownMessageId`. The DOM is only re-rendered when a new message arrives — the polling function compares the latest message ID against the cached value and skips the update entirely if unchanged. This prevents the visible flash/re-render that occurred with the previous approach of unconditionally replacing `innerHTML` on every poll cycle.

## Data Model
- `Conversation` — stores the participant pair and `last_message_at`
- `Message` — stores sender, content (text or media prefix + URL), `is_read`, and `read_at`

## Implementation
- Models: `backend/app/models/conversation.py`, `backend/app/models/message.py`
- Routes: `backend/app/routes/messages.py`
- Frontend: `Frontend/js/messages.js`, `Frontend/css/messages.css`

## Validation Checklist
1. Create a conversation between two verified users.
2. Send text messages in both directions.
3. Confirm unread counts increase for the recipient.
4. Mark the conversation as read and confirm unread counts drop to zero.
5. Verify a third user receives `403` on access.
6. Record and send a voice message — confirm `[audio]` prefix in DB, `<audio>` element in UI.
7. Send an image — confirm `[image]` prefix in DB, `<img>` element in UI.
8. Send a video — confirm `[video]` prefix in DB, `<video>` element in UI.
9. Rapid-fire polling test: send a message, confirm it appears within 5 s with no UI flash.

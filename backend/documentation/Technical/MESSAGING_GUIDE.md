# Messaging Guide

## Purpose
Document the Phase 6 direct messaging system and its backend rules.

## Endpoints
- `GET /api/messages/conversations`
- `POST /api/messages/conversations`
- `GET /api/messages/conversations/<id>`
- `POST /api/messages/conversations/<id>`
- `PATCH /api/messages/conversations/<id>/read`
- `GET /api/messages/unread-count`

## Conversation Model
- One conversation exists per user pair
- Participants are stored in sorted order:
  - `participant_a = min(user_id_1, user_id_2)`
  - `participant_b = max(user_id_1, user_id_2)`
- Duplicate conversation creation is prevented by a unique constraint

## Behavioral Rules
- Users cannot message themselves
- Non-participants cannot read or write in a conversation
- Creating the same conversation twice returns the existing thread
- Messages support unread counts and read receipts

## Data Model
- `Conversation` stores the participant pair and `last_message_at`
- `Message` stores sender, content, `is_read`, and `read_at`

## Implementation Notes
- Models:
  - `backend/app/models/conversation.py`
  - `backend/app/models/message.py`
- Routes:
  - `backend/app/routes/messages.py`

## Validation
1. Create a conversation between two verified users.
2. Send messages in both directions.
3. Confirm unread counts increase for the recipient.
4. Mark the conversation as read and confirm unread counts drop.
5. Verify a third user receives `403` on access.

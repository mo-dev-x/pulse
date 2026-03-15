"""Notification service for creation and mention extraction."""

import re

from app import db
from app.models.notification import Notification
from app.models.user import User
from app.services.job_queue_service import enqueue_task

MENTION_PATTERN = re.compile(r'@(\w+)')


def create_notification(user_id, notification_type, title, message, related_type=None, related_id=None, actor_id=None):
    """Create a notification record unless it would notify the actor about their own action."""
    if actor_id is not None and user_id == actor_id:
        return None

    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        related_type=related_type,
        related_id=related_id,
        actor_id=actor_id,
    )
    db.session.add(notification)

    enqueue_task(
        'app.tasks.push_tasks.deliver_push',
        user_id,
        title,
        message,
        {
            'notification_type': notification_type,
            'related_type': related_type,
            'related_id': related_id,
        },
        queue_name='push',
    )
    return notification


def create_notifications_batch(payloads):
    """Create multiple notifications from iterable payload dictionaries."""
    created = []
    for payload in payloads or []:
        notification = create_notification(
            user_id=payload.get('user_id'),
            notification_type=payload.get('notification_type'),
            title=payload.get('title'),
            message=payload.get('message'),
            related_type=payload.get('related_type'),
            related_id=payload.get('related_id'),
            actor_id=payload.get('actor_id'),
        )
        if notification is not None:
            created.append(notification)
    return created


def extract_mentions(content):
    """Return unique lowercase usernames mentioned with @username syntax."""
    mentions = [m.lower() for m in MENTION_PATTERN.findall(content or '')]
    return list(dict.fromkeys(mentions))


def create_mention_notifications(content, actor_id, related_type, related_id):
    """Create mention notifications for referenced usernames."""
    usernames = extract_mentions(content)
    if not usernames:
        return []

    users = User.query.filter(User.username.in_(usernames)).all()
    created = []
    for user in users:
        notification = create_notification(
            user_id=user.id,
            notification_type='mention',
            title='You were mentioned',
            message='Someone mentioned you in a conversation.',
            related_type=related_type,
            related_id=related_id,
            actor_id=actor_id,
        )
        if notification is not None:
            created.append(notification)

    return created

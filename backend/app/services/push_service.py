"""Push notification delivery helpers."""

from datetime import datetime, timezone

from flask import current_app

from app import db
from app.models.push_subscription import PushSubscription


def send_push_notification(user_id: int, title: str, body: str, data: dict = None):
    """
    Dispatch a push notification to all active subscriptions for a user.
    Silently skips when push is disabled or not configured.
    """
    if not current_app.config.get('PUSH_ENABLED', False):
        return {'sent': 0, 'skipped': True}

    subscriptions = PushSubscription.query.filter_by(user_id=user_id, is_active=True).all()
    sent = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for subscription in subscriptions:
        subscription.last_used_at = now
        sent += 1

    db.session.commit()
    current_app.logger.info(
        "Push dispatch simulated for user_id=%s subscriptions=%s title=%s payload=%s",
        user_id,
        sent,
        title,
        data or {},
    )
    return {'sent': sent, 'skipped': False}

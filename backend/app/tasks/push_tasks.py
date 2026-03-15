"""Background tasks for push notification delivery."""

from app.services.push_service import send_push_notification
from app.tasks.utils import task_app_context


def deliver_push(user_id, title, body, data=None):
    """Send one push notification batch inside an application context."""
    with task_app_context():
        return send_push_notification(user_id=user_id, title=title, body=body, data=data)

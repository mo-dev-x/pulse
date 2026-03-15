"""Background tasks for outbound email delivery."""

from app.services.email_service import _send_html_email
from app.tasks.utils import task_app_context


def deliver_email(recipient, subject, html_body):
    """Send one HTML email inside an application context."""
    with task_app_context():
        return _send_html_email(recipient=recipient, subject=subject, html_body=html_body)

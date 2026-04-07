"""Background tasks for outbound email delivery."""

from app.services.email_service import _send_html_email
from app.tasks.utils import task_app_context


def deliver_email(recipient, subject, html_body):
    """Send one HTML email inside an application context."""
    with task_app_context():
        return _send_html_email(recipient=recipient, subject=subject, html_body=html_body)


def deliver_notification_email(user_id, title, message):
    """Send a notification email to the user if email_notifications is enabled."""
    with task_app_context():
        from app import db
        from app.models.user import User
        user = db.session.get(User, user_id)
        if not user or not user.email_notifications:
            return False, 'Skipped'

        frontend_url = _get_frontend_url()
        lang = (getattr(user, 'preferred_language', None) or 'en').lower()
        greeting = user.display_name or user.username or 'there'

        if lang == 'fr':
            subject = f'Pulse — {title}'
            html = f"""
            <html><body style="font-family:sans-serif;color:#111;max-width:480px;margin:0 auto;padding:24px">
              <h3 style="margin:0 0 8px">Salut {greeting},</h3>
              <p style="margin:0 0 16px;font-size:15px;line-height:1.5">{message}</p>
              <a href="{frontend_url}/notifications.html"
                 style="display:inline-block;background:#e63b75;color:#fff;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:700;font-size:14px">
                Voir les notifications
              </a>
              <p style="margin:24px 0 0;font-size:12px;color:#888">
                Vous recevez cet email car les notifications par email sont activées.<br>
                <a href="{frontend_url}/settings.html">Se désabonner</a>
              </p>
            </body></html>"""
        else:
            subject = f'Pulse — {title}'
            html = f"""
            <html><body style="font-family:sans-serif;color:#111;max-width:480px;margin:0 auto;padding:24px">
              <h3 style="margin:0 0 8px">Hi {greeting},</h3>
              <p style="margin:0 0 16px;font-size:15px;line-height:1.5">{message}</p>
              <a href="{frontend_url}/notifications.html"
                 style="display:inline-block;background:#e63b75;color:#fff;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:700;font-size:14px">
                View notifications
              </a>
              <p style="margin:24px 0 0;font-size:12px;color:#888">
                You're receiving this because email notifications are on.<br>
                <a href="{frontend_url}/settings.html">Unsubscribe</a>
              </p>
            </body></html>"""

        return _send_html_email(recipient=user.email, subject=subject, html_body=html)


def _get_frontend_url():
    try:
        from flask import current_app
        return current_app.config.get('FRONTEND_URL', 'https://pulse.app').rstrip('/')
    except Exception:
        return 'https://pulse.app'

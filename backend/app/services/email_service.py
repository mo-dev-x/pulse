"""Email service for verification and password reset flows."""

import secrets
import requests
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

from app import db
from app.services.job_queue_service import enqueue_task


def _send_html_email(recipient, subject, html_body):
    api_key = current_app.config.get("BREVO_API_KEY")
    sender_email = current_app.config.get("BREVO_SENDER_EMAIL")

    if not api_key:
        return False, "Brevo API key not configured"

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "sender": {"email": sender_email},
                "to": [{"email": recipient}],
                "subject": subject,
                "htmlContent": html_body,
            },
            timeout=10,
        )

        if response.status_code >= 400:
            return False, response.text

    except Exception as exc:
        return False, str(exc)

    return True, None


def _resolve_user_language(user):
    """Return language for outbound user email templates."""
    lang = (getattr(user, 'preferred_language', None) or '').lower()
    return 'fr' if lang == 'fr' else 'en'


def create_verification_token(user):
    """Return existing valid token or create a new one valid for 24 hours.

    Reusing the same token while it's still valid prevents previous email
    links from being invalidated when the user requests a resend.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if user.verification_token and user.verification_expires and user.verification_expires > now:
        return user.verification_token
    token = secrets.token_urlsafe(32)
    user.verification_token = token
    user.verification_expires = now + timedelta(hours=24)
    db.session.commit()
    return token


def create_password_reset_token(user):
    """Create and persist a one-time reset token valid for 1 hour."""
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    db.session.commit()
    return token


def _build_verification_email(user, token):
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000').rstrip('/')
    verify_link = f'{frontend_url}/verify-email?token={token}'
    greeting_name = user.display_name or user.username or 'there'
    lang = _resolve_user_language(user)

    if lang == 'fr':
        subject = 'Bienvenue sur Pulse - Verifiez votre courriel'
        html = f"""
        <html>
          <body>
            <h2>Salut {greeting_name},</h2>
            <p>Bienvenue sur Pulse, l'endroit ou vous pouvez vous exprimer librement.</p>
            <p>Veuillez cliquer sur le lien ci-dessous pour verifier votre adresse courriel :</p>
            <p><a href="{verify_link}">Verifier mon courriel</a></p>
            <p>Ce lien expire dans 24 heures.</p>
            <p>Bienvenue dans votre nouveau chez-vous.</p>
          </body>
        </html>
        """
    else:
        subject = 'Welcome to Pulse - Verify your email'
        html = f"""
        <html>
          <body>
            <h2>Hi {greeting_name},</h2>
            <p>Welcome to Pulse, the place where you can express yourself freely.</p>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{verify_link}">Verify my email</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>Welcome to your new home.</p>
          </body>
        </html>
        """

    return subject, html


def _build_password_reset_email(user, token):
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000').rstrip('/')
    reset_link = f'{frontend_url}/reset-password?token={token}'
    lang = _resolve_user_language(user)

    if lang == 'fr':
        subject = 'Pulse - Reinitialisation du mot de passe'
        html = f"""
        <html>
          <body>
            <h2>Reinitialisation du mot de passe</h2>
            <p>Pour reinitialiser votre mot de passe, cliquez sur le lien ci-dessous.</p>
            <p><a href="{reset_link}">Reinitialiser mon mot de passe</a></p>
            <p>Ce lien expire dans 1 heure.</p>
          </body>
        </html>
        """
    else:
        subject = 'Pulse - Password reset'
        html = f"""
        <html>
          <body>
            <h2>Password reset</h2>
            <p>To reset your password, click the link below.</p>
            <p><a href="{reset_link}">Reset my password</a></p>
            <p>This link expires in 1 hour.</p>
          </body>
        </html>
        """

    return subject, html


def send_verification_email(user):
    """Send account verification email."""
    token = create_verification_token(user)
    subject, html = _build_verification_email(user, token)
    dispatch = enqueue_task(
        'app.tasks.email_tasks.deliver_email',
        user.email,
        subject,
        html,
        queue_name='email',
    )
    if dispatch.mode in {'eager', 'inline'}:
        return dispatch.result
    return True, None


def send_password_reset_email(user):
    """Send password reset email."""
    token = create_password_reset_token(user)
    subject, html = _build_password_reset_email(user, token)
    dispatch = enqueue_task(
        'app.tasks.email_tasks.deliver_email',
        user.email,
        subject,
        html,
        queue_name='email',
    )
    if dispatch.mode in {'eager', 'inline'}:
        return dispatch.result
    return True, None


def send_notification_email(user, subject, body_html):
    """Send a notification-style email when email notifications are enabled."""
    if not getattr(user, 'email_notifications', True):
        return False, 'Email notifications disabled'
    return _send_html_email(recipient=user.email, subject=subject, html_body=body_html)

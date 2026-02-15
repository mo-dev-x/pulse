"""Email service for verification and password reset flows."""

import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

from app import db


def _send_html_email(recipient, subject, html_body):
    """Send an HTML email using configured SMTP credentials."""
    smtp_host = current_app.config.get('SMTP_HOST')
    smtp_port = current_app.config.get('SMTP_PORT')
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    smtp_from = current_app.config.get('SMTP_FROM')

    if not smtp_host or not smtp_port or not smtp_from:
        return False, 'SMTP is not configured'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_from
    msg['To'] = recipient
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if current_app.config.get('SMTP_USE_TLS', True):
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as exc:
        return False, str(exc)

    return True, None


def create_verification_token(user):
    """Create and persist a one-time verification token valid for 24 hours."""
    token = secrets.token_urlsafe(32)
    user.verification_token = token
    user.verification_expires = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()
    return token


def create_password_reset_token(user):
    """Create and persist a one-time reset token valid for 1 hour."""
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    return token


def send_verification_email(user):
    """Send account verification email."""
    token = create_verification_token(user)
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    verify_link = f'{frontend_url}/verify-email?token={token}'

    html = f"""
    <html>
      <body>
        <h2>Bienvenue sur Pulse / Welcome to Pulse</h2>
        <p>Veuillez verifier votre adresse courriel @ulaval.ca.</p>
        <p>Please verify your @ulaval.ca email address.</p>
        <p><a href="{verify_link}">Verifier / Verify</a></p>
        <p>Ce lien expire dans 24 heures / This link expires in 24 hours.</p>
      </body>
    </html>
    """

    return _send_html_email(
        recipient=user.email,
        subject='Pulse - Verification de courriel / Email Verification',
        html_body=html
    )


def send_password_reset_email(user):
    """Send password reset email."""
    token = create_password_reset_token(user)
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    reset_link = f'{frontend_url}/reset-password?token={token}'

    html = f"""
    <html>
      <body>
        <h2>Reinitialisation du mot de passe / Password Reset</h2>
        <p>Pour reinitialiser votre mot de passe, cliquez sur le lien ci-dessous.</p>
        <p>To reset your password, click the link below.</p>
        <p><a href="{reset_link}">Reinitialiser / Reset</a></p>
        <p>Ce lien expire dans 1 heure / This link expires in 1 hour.</p>
      </body>
    </html>
    """

    return _send_html_email(
        recipient=user.email,
        subject='Pulse - Reinitialisation du mot de passe / Password Reset',
        html_body=html
    )

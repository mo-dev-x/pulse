"""Shared helpers for script-style HTTP API tests."""

from datetime import datetime
import os
from pathlib import Path
import sys

import pymysql
import requests
from dotenv import load_dotenv

# Ensure backend package imports work from repo root and backend/tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def mark_user_verified(email):
    """
    Mark a user as verified in the app database.

    Returns:
        tuple[bool, str | None]: success flag and optional error details.
    """
    backend_dir = Path(__file__).resolve().parents[1]
    load_dotenv(backend_dir / ".env")
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "pulse_db"),
            charset="utf8mb4",
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET is_verified = %s,
                        verification_token = %s,
                        verification_expires = %s
                    WHERE email = %s
                    """,
                    (1, None, None, email.lower()),
                )
                if cur.rowcount == 0:
                    return False, f"User not found in DB after registration: {email}"
            conn.commit()
        return True, None
    except Exception as exc:  # pragma: no cover - helper for manual scripts
        return False, f"DB verification update failed: {exc}"


def register_verified_user(base_url, username_prefix, display_name, password='SecurePass123!'):
    """
    Register a unique @ulaval.ca user through the API, then mark it verified in DB.

    Returns:
        tuple[str | None, str | None, str | None]: token, username, error
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    username = f"{username_prefix}_{timestamp}"
    email = f"{username}@ulaval.ca"
    payload = {
        'email': email,
        'password': password,
        'username': username,
        'display_name': display_name
    }

    try:
        response = requests.post(f"{base_url}/api/auth/register", json=payload, timeout=20)
    except Exception as exc:  # pragma: no cover - helper for manual scripts
        return None, None, f"Registration request failed: {exc}"

    if response.status_code != 201:
        return None, None, f"Registration failed ({response.status_code}): {response.text}"

    ok, error = mark_user_verified(email)
    if not ok:
        return None, None, error

    token = response.json().get('token')
    if not token:
        return None, None, "Registration succeeded but token was missing in response"

    return token, username, None

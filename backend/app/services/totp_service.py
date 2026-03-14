"""Lightweight TOTP helpers used when external OTP libraries are unavailable."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote


def generate_secret(length=32):
    """Return a base32 TOTP secret without padding."""
    random_bytes = secrets.token_bytes(max(20, (length * 5) // 8))
    return base64.b32encode(random_bytes).decode('ascii').rstrip('=')[:length]


def _normalize_secret(secret):
    normalized = (secret or '').strip().upper().replace(' ', '')
    padding = '=' * ((8 - len(normalized) % 8) % 8)
    return normalized + padding


def generate_totp(secret, for_time=None, step=30, digits=6):
    """Generate a TOTP code for a given secret and timestamp."""
    timestamp = int(for_time if for_time is not None else time.time())
    counter = timestamp // step
    key = base64.b32decode(_normalize_secret(secret), casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(binary % (10 ** digits)).zfill(digits)


def verify_totp(secret, code, valid_window=1, for_time=None, step=30, digits=6):
    """Validate a TOTP code, allowing a small time drift window."""
    if not secret or not code:
        return False

    now = int(for_time if for_time is not None else time.time())
    normalized_code = str(code).strip()
    for offset in range(-valid_window, valid_window + 1):
        candidate_time = now + (offset * step)
        if generate_totp(secret, for_time=candidate_time, step=step, digits=digits) == normalized_code:
            return True
    return False


def build_provisioning_uri(secret, name, issuer_name, algorithm='SHA1', digits=6, period=30):
    """Return an otpauth provisioning URI compatible with authenticator apps."""
    label = quote(f"{issuer_name}:{name}")
    issuer = quote(issuer_name)
    return (
        f"otpauth://totp/{label}?secret={secret}"
        f"&issuer={issuer}&algorithm={algorithm}&digits={digits}&period={period}"
    )

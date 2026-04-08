"""Push notification delivery using Web Push (VAPID) via pywebpush."""

import json
from datetime import datetime, timezone

from flask import current_app

from app import db
from app.models.push_subscription import PushSubscription


def send_push_notification(user_id: int, title: str, body: str, data: dict = None):
    """
    Dispatch a Web Push notification to all active subscriptions for a user.

    Requires PUSH_ENABLED=true, VAPID_PUBLIC_KEY, and VAPID_PRIVATE_KEY in config.
    Silently no-ops when push is disabled or keys are not set.
    Automatically deactivates expired/invalid subscriptions (HTTP 404/410).
    """
    if not current_app.config.get('PUSH_ENABLED', False):
        return {'sent': 0, 'skipped': True}

    vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
    vapid_public_key = current_app.config.get('VAPID_PUBLIC_KEY')
    vapid_sub = current_app.config.get('VAPID_CLAIMS_SUB', 'mailto:admin@pulse.app')

    if not vapid_private_key or not vapid_public_key:
        current_app.logger.warning("PUSH_ENABLED=true but VAPID keys are not set in config.")
        return {'sent': 0, 'skipped': True}

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        current_app.logger.error(
            "pywebpush is not installed. Run: pip install pywebpush"
        )
        return {'sent': 0, 'skipped': True}

    subscriptions = PushSubscription.query.filter_by(
        user_id=user_id, platform='web', is_active=True
    ).all()

    if not subscriptions:
        return {'sent': 0, 'skipped': False}

    payload = json.dumps({'title': title, 'body': body, 'data': data or {}})
    vapid_claims = {'sub': vapid_sub}
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    sent = 0
    expired_ids = []

    for sub in subscriptions:
        try:
            sub_info = json.loads(sub.token)
            webpush(
                subscription_info=sub_info,
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims,
            )
            sub.last_used_at = now
            sent += 1
        except WebPushException as exc:
            if exc.response is not None and exc.response.status_code in (404, 410):
                # Browser unregistered or subscription expired — clean it up
                expired_ids.append(sub.id)
            else:
                current_app.logger.warning(
                    "Web Push failed for subscription %s: %s", sub.id, exc
                )
        except (json.JSONDecodeError, KeyError):
            # Malformed token stored in DB — deactivate it
            expired_ids.append(sub.id)
        except Exception as exc:  # noqa: BLE001
            current_app.logger.error(
                "Unexpected push error for subscription %s: %s", sub.id, exc
            )

    if expired_ids:
        PushSubscription.query.filter(
            PushSubscription.id.in_(expired_ids)
        ).update({'is_active': False}, synchronize_session=False)

    db.session.commit()

    current_app.logger.info(
        "Push dispatch: user_id=%s sent=%s expired=%s title=%r",
        user_id, sent, len(expired_ids), title,
    )
    return {'sent': sent, 'expired': len(expired_ids)}

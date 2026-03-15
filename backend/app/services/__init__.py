"""
Services package

Business logic and processing services.
"""

from app.services.nlp_service_camembert import FrenchTwitterNLPService, analyze_sentiment, nlp_service
from app.services.aggregation_service import (
    compute_daily_aggregate,
    compute_weekly_aggregate,
    compute_all_daily_aggregates,
    compute_all_weekly_aggregates,
    get_campus_mood_overview
)
from app.services.email_service import (
    send_verification_email,
    send_password_reset_email,
    send_notification_email,
    create_verification_token,
    create_password_reset_token
)
from app.services.notification_service import (
    create_notification,
    create_notifications_batch,
    extract_mentions,
    create_mention_notifications
)
from app.services.job_queue_service import enqueue_task
from app.services.meilisearch_service import search as meilisearch_search, upsert_documents, delete_document
from app.services.session_service import (
    track_session,
    revoke_session,
    touch_session
)
from app.services.security_log_service import log_security_event
from app.services.totp_service import generate_secret, generate_totp, verify_totp, build_provisioning_uri

__all__ = [
    'FrenchTwitterNLPService', 'analyze_sentiment', 'nlp_service',
    'compute_daily_aggregate', 'compute_weekly_aggregate',
    'compute_all_daily_aggregates', 'compute_all_weekly_aggregates',
    'get_campus_mood_overview',
    'send_verification_email', 'send_password_reset_email', 'send_notification_email',
    'create_verification_token', 'create_password_reset_token',
    'create_notification', 'create_notifications_batch', 'extract_mentions', 'create_mention_notifications',
    'enqueue_task',
    'meilisearch_search', 'upsert_documents', 'delete_document',
    'track_session', 'revoke_session', 'touch_session',
    'log_security_event',
    'generate_secret', 'generate_totp', 'verify_totp', 'build_provisioning_uri'
]

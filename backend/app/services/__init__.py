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
    create_verification_token,
    create_password_reset_token
)

__all__ = [
    'FrenchTwitterNLPService', 'analyze_sentiment', 'nlp_service',
    'compute_daily_aggregate', 'compute_weekly_aggregate',
    'compute_all_daily_aggregates', 'compute_all_weekly_aggregates',
    'get_campus_mood_overview',
    'send_verification_email', 'send_password_reset_email',
    'create_verification_token', 'create_password_reset_token'
]

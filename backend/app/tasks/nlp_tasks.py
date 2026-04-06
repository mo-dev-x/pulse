"""Background tasks for sentiment analysis."""

from datetime import timedelta

from app import db
from app.models import Post
from app.services import analyze_sentiment
from app.services.aggregation_service import compute_daily_aggregate, compute_weekly_aggregate
from app.tasks.utils import task_app_context


def analyze_post_sentiment(post_id):
    """Recompute and persist sentiment for one post, then refresh aggregates."""
    with task_app_context():
        post = db.session.get(Post, post_id)
        if not post:
            return {'updated': False}

        result = analyze_sentiment(post.content)
        post.sentiment_score = result['score']
        post.sentiment_label = result['label']
        post.emotion_label = result.get('emotion_label')
        post.emotion_display = result.get('emotion_display')
        post.detected_language = result['language']
        db.session.commit()

        # Refresh aggregates now that real sentiment is known
        target_date = post.created_at.date()
        week_start = target_date - timedelta(days=target_date.weekday())
        compute_daily_aggregate(target_date, zone_id=None)
        compute_weekly_aggregate(week_start, zone_id=None)
        if post.zone_id is not None:
            compute_daily_aggregate(target_date, zone_id=post.zone_id)
            compute_weekly_aggregate(week_start, zone_id=post.zone_id)

        return {'updated': True, 'post_id': post_id}

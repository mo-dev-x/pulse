"""Background tasks for aggregate refreshes."""

from datetime import timedelta

from app import db
from app.models import Post
from app.services.aggregation_service import compute_daily_aggregate, compute_weekly_aggregate
from app.tasks.utils import task_app_context


def refresh_post_aggregates(post_id):
    """Refresh campus-wide and zone-specific aggregates for a post timestamp."""
    with task_app_context():
        post = db.session.get(Post, post_id)
        if not post or not post.created_at:
            return {'refreshed': False}

        target_date = post.created_at.date()
        week_start = target_date - timedelta(days=target_date.weekday())

        compute_daily_aggregate(target_date, zone_id=None)
        compute_weekly_aggregate(week_start, zone_id=None)
        if post.zone_id is not None:
            compute_daily_aggregate(target_date, zone_id=post.zone_id)
            compute_weekly_aggregate(week_start, zone_id=post.zone_id)

        return {'refreshed': True, 'post_id': post_id}

"""Background tasks for moderation workflows."""

from datetime import datetime, timedelta, timezone

from app import db
from app.models import Post, Report
from app.tasks.utils import task_app_context

AUTO_FLAG_THRESHOLD = 5
AUTO_FLAG_WINDOW = timedelta(hours=24)


def evaluate_auto_flag_post(post_id):
    """Hide a post after repeated recent reports."""
    with task_app_context():
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - AUTO_FLAG_WINDOW
        recent_count = Report.query.filter(
            Report.target_type == 'post',
            Report.target_id == post_id,
            Report.created_at >= cutoff
        ).count()

        post = db.session.get(Post, post_id)
        if not post or recent_count < AUTO_FLAG_THRESHOLD:
            return {'flagged': False, 'recent_reports': recent_count}

        post.is_flagged = True
        post.hidden_by_mod = True
        post.flagged_at = post.flagged_at or datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()
        return {'flagged': True, 'recent_reports': recent_count}

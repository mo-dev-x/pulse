"""Background tasks for sentiment analysis."""

from app import db
from app.models import Post
from app.services import analyze_sentiment
from app.tasks.utils import task_app_context


def analyze_post_sentiment(post_id):
    """Recompute and persist sentiment for one post."""
    with task_app_context():
        post = db.session.get(Post, post_id)
        if not post:
            return {'updated': False}

        result = analyze_sentiment(post.content)
        post.sentiment_score = result['score']
        post.sentiment_label = result['label']
        post.detected_language = result['language']
        db.session.commit()
        return {'updated': True, 'post_id': post_id}

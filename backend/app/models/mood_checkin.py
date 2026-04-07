from datetime import datetime, timezone, date, timedelta
from app import db


class MoodCheckin(db.Model):
    __tablename__ = 'mood_checkins'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    emotion = db.Column(db.String(30), nullable=False)
    checked_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    @classmethod
    def get_today_for_user(cls, user_id):
        today = date.today()
        return cls.query.filter(
            cls.user_id == user_id,
            db.func.date(cls.checked_at) == today,
        ).first()

    @classmethod
    def get_last_checkin_for_user(cls, user_id):
        """Return the user's most recent check-in if it was within the last 12 hours."""
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=12)
        return (
            cls.query
            .filter(cls.user_id == user_id, cls.checked_at >= cutoff)
            .order_by(cls.checked_at.desc())
            .first()
        )

    @classmethod
    def today_distribution(cls):
        today = date.today()
        rows = (
            db.session.query(cls.emotion, db.func.count(cls.id))
            .filter(db.func.date(cls.checked_at) == today)
            .group_by(cls.emotion)
            .all()
        )
        return {emotion: count for emotion, count in rows}

"""Direct message conversation model."""

from datetime import datetime, timezone

from app import db


class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    participant_a = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    participant_b = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    last_message_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False, index=True)

    user_a = db.relationship('User', foreign_keys=[participant_a])
    user_b = db.relationship('User', foreign_keys=[participant_b])

    __table_args__ = (
        db.UniqueConstraint('participant_a', 'participant_b', name='uq_conversation'),
    )

    @staticmethod
    def normalize_pair(user_one_id, user_two_id):
        return tuple(sorted((int(user_one_id), int(user_two_id))))

    @staticmethod
    def find_between(user_one_id, user_two_id):
        participant_a, participant_b = Conversation.normalize_pair(user_one_id, user_two_id)
        return Conversation.query.filter_by(participant_a=participant_a, participant_b=participant_b).first()

    def other_user_id(self, current_user_id):
        return self.participant_b if self.participant_a == current_user_id else self.participant_a

    def has_participant(self, user_id):
        return user_id in {self.participant_a, self.participant_b}

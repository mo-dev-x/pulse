"""Moderation report model."""

from datetime import datetime

from app import db


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    target_type = db.Column(
        db.Enum('post', 'comment', 'user', name='report_target_type_enum'),
        nullable=False,
        index=True
    )
    target_id = db.Column(db.Integer, nullable=False, index=True)
    reason = db.Column(
        db.Enum(
            'spam',
            'harassment',
            'self_harm',
            'misinformation',
            'inappropriate',
            'other',
            name='report_reason_enum'
        ),
        nullable=False
    )
    details = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum('pending', 'reviewed', 'actioned', 'dismissed', name='report_status_enum'),
        nullable=False,
        default='pending',
        index=True
    )
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    reporter = db.relationship('User', foreign_keys=[reporter_id], backref=db.backref('reports_submitted', lazy='dynamic'))
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref=db.backref('reports_reviewed', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('reporter_id', 'target_type', 'target_id', name='unique_reporter_target'),
    )

    def to_dict(self, target_preview=None):
        return {
            'id': self.id,
            'reporter_id': self.reporter_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'reason': self.reason,
            'details': self.details,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() + 'Z' if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'target_preview': target_preview,
        }

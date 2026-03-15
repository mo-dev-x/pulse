"""Automated tests for Phase 6 background job queue helpers."""

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import DailyAggregate, Notification, Post, User, WeeklyAggregate
from app.services.email_service import send_password_reset_email, send_verification_email
from app.services.job_queue_service import enqueue_task
from app.services.notification_service import create_notification
from tests.phase5_test_utils import Phase5BaseTestCase


class TestBackgroundJobs(Phase5BaseTestCase):

    def test_enqueue_task_runs_eagerly_in_testing(self):
        calls = []

        def sample_task(value):
            calls.append(value)
            return value * 2

        dispatch = enqueue_task(sample_task, 21)
        self.assertFalse(dispatch.queued)
        self.assertEqual(dispatch.mode, 'eager')
        self.assertEqual(dispatch.result, 42)
        self.assertEqual(calls, [21])

    def test_verification_email_delivery_is_enqueued_after_token_creation(self):
        self.register_user(email='bg_verify@ulaval.ca', username='bg_verify')
        user = User.query.filter_by(email='bg_verify@ulaval.ca').first()

        with patch('app.services.email_service.enqueue_task') as mocked_enqueue:
            mocked_enqueue.return_value.mode = 'rq'
            mocked_enqueue.return_value.result = None
            sent, error = send_verification_email(user)

        self.assertTrue(sent)
        self.assertIsNone(error)
        self.assertIsNotNone(user.verification_token)
        mocked_enqueue.assert_called_once()

    def test_password_reset_delivery_is_enqueued_after_token_creation(self):
        self.register_user(email='bg_reset@ulaval.ca', username='bg_reset')
        user = User.query.filter_by(email='bg_reset@ulaval.ca').first()

        with patch('app.services.email_service.enqueue_task') as mocked_enqueue:
            mocked_enqueue.return_value.mode = 'rq'
            mocked_enqueue.return_value.result = None
            sent, error = send_password_reset_email(user)

        self.assertTrue(sent)
        self.assertIsNone(error)
        self.assertIsNotNone(user.reset_token)
        mocked_enqueue.assert_called_once()

    def test_notification_creation_queues_push_delivery(self):
        actor = User(email='bg_actor@ulaval.ca', password='SecurePass123', username='bg_actor', is_verified=True)
        target = User(email='bg_target@ulaval.ca', password='SecurePass123', username='bg_target', is_verified=True)
        db.session.add_all([actor, target])
        db.session.commit()

        with patch('app.services.notification_service.enqueue_task') as mocked_enqueue:
            notification = create_notification(
                user_id=target.id,
                notification_type='mention',
                title='Queued push',
                message='Testing push queue integration.',
                related_type='post',
                related_id=99,
                actor_id=actor.id,
            )

        self.assertIsInstance(notification, Notification)
        mocked_enqueue.assert_called_once()

    def test_post_creation_refreshes_aggregates_via_background_task(self):
        token, _ = self.register_user(email='bg_post@ulaval.ca', username='bg_post')
        self.mark_verified('bg_post@ulaval.ca')

        post_id = self.create_post(token, content='A background aggregate refresh should happen after this post.')

        post = db.session.get(Post, post_id)
        self.assertIsNotNone(post)
        self.assertIsNotNone(DailyAggregate.query.filter_by(date=post.created_at.date(), zone_id=None).first())
        week_start = post.created_at.date().replace(day=post.created_at.day)  # placeholder to keep coverage deterministic
        self.assertGreaterEqual(WeeklyAggregate.query.count(), 1)

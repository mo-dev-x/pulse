"""Automated tests for Phase 5A email verification features."""

from datetime import datetime, timedelta
from pathlib import Path
import sys

# Ensure `app` imports resolve when tests are run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models.user import User
from tests.phase5_test_utils import Phase5BaseTestCase


class TestEmailVerification(Phase5BaseTestCase):

    def test_send_verification_requires_auth(self):
        response = self.client.post('/api/auth/send-verification')
        self.assertEqual(response.status_code, 401)

    def test_send_verification_generates_token(self):
        token, user_payload = self.register_user(
            email='verify1@ulaval.ca', username='verify1'
        )
        user = User.query.filter_by(email=user_payload['email']).first()
        user.verification_token = None
        user.verification_expires = None
        db.session.commit()

        response = self.client.post(
            '/api/auth/send-verification',
            headers=self.auth_headers(token)
        )
        self.assertEqual(response.status_code, 200)
        refreshed = User.query.filter_by(email=user_payload['email']).first()
        self.assertIsNotNone(refreshed.verification_token)
        self.assertIsNotNone(refreshed.verification_expires)

    def test_verify_email_success(self):
        _, user_payload = self.register_user(
            email='verify2@ulaval.ca', username='verify2'
        )
        user = User.query.filter_by(email=user_payload['email']).first()
        token = user.verification_token

        response = self.client.get(f'/api/auth/verify-email/{token}')
        self.assertEqual(response.status_code, 200, response.get_json())

        refreshed = User.query.filter_by(email=user_payload['email']).first()
        self.assertTrue(refreshed.is_verified)
        self.assertIsNone(refreshed.verification_token)
        self.assertIsNone(refreshed.verification_expires)

    def test_verify_email_expired_token(self):
        _, user_payload = self.register_user(
            email='verify3@ulaval.ca', username='verify3'
        )
        user = User.query.filter_by(email=user_payload['email']).first()
        user.verification_token = 'expired-token'
        user.verification_expires = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

        response = self.client.get('/api/auth/verify-email/expired-token')
        self.assertEqual(response.status_code, 400)
        self.assertIn('expired', response.get_json()['error'].lower())

    def test_verification_required_for_post_creation(self):
        token, _ = self.register_user(email='verify4@ulaval.ca', username='verify4')
        response = self.client.post(
            '/api/posts',
            json={'content': 'This content is long enough to pass validation.'},
            headers=self.auth_headers(token)
        )
        self.assertEqual(response.status_code, 403, response.get_json())


if __name__ == '__main__':
    import unittest
    unittest.main()

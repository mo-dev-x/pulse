"""Automated tests for Phase 5A password reset flow."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Ensure `app` imports resolve when tests are run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models.user import User
from tests.phase5_test_utils import Phase5BaseTestCase


class TestPasswordReset(Phase5BaseTestCase):

    def test_forgot_password_always_returns_success(self):
        self.register_user(email='reset1@ulaval.ca', username='reset1')

        known = self.client.post('/api/auth/forgot-password', json={'email': 'reset1@ulaval.ca'})
        unknown = self.client.post('/api/auth/forgot-password', json={'email': 'missing@ulaval.ca'})

        self.assertEqual(known.status_code, 200)
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(known.get_json()['message'], unknown.get_json()['message'])

    def test_forgot_password_generates_token_for_existing_user(self):
        self.register_user(email='reset2@ulaval.ca', username='reset2')
        response = self.client.post('/api/auth/forgot-password', json={'email': 'reset2@ulaval.ca'})
        self.assertEqual(response.status_code, 200)

        user = User.query.filter_by(email='reset2@ulaval.ca').first()
        self.assertIsNotNone(user.reset_token)
        self.assertIsNotNone(user.reset_expires)

    def test_reset_password_invalid_token(self):
        response = self.client.post('/api/auth/reset-password', json={
            'token': 'nope',
            'new_password': 'NewSecurePass123'
        })
        self.assertEqual(response.status_code, 400)

    def test_reset_password_expired_token(self):
        self.register_user(email='reset3@ulaval.ca', username='reset3')
        user = User.query.filter_by(email='reset3@ulaval.ca').first()
        user.reset_token = 'expired-reset-token'
        user.reset_expires = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=2)
        db.session.commit()

        response = self.client.post('/api/auth/reset-password', json={
            'token': 'expired-reset-token',
            'new_password': 'NewSecurePass123'
        })
        self.assertEqual(response.status_code, 400)
        error_text = response.get_json()['error'].lower()
        self.assertTrue('expired' in error_text or 'expire' in error_text)

    def test_reset_password_success_updates_credentials(self):
        self.register_user(email='reset4@ulaval.ca', username='reset4', password='OldSecurePass123')
        self.mark_verified('reset4@ulaval.ca')
        self.client.post('/api/auth/forgot-password', json={'email': 'reset4@ulaval.ca'})

        user = User.query.filter_by(email='reset4@ulaval.ca').first()
        token = user.reset_token
        response = self.client.post('/api/auth/reset-password', json={
            'token': token,
            'new_password': 'NewSecurePass123'
        })
        self.assertEqual(response.status_code, 200, response.get_json())

        refreshed = User.query.filter_by(email='reset4@ulaval.ca').first()
        self.assertIsNone(refreshed.reset_token)
        self.assertIsNone(refreshed.reset_expires)

        old_login = self.client.post('/api/auth/login', json={
            'email': 'reset4@ulaval.ca',
            'password': 'OldSecurePass123'
        })
        new_login = self.client.post('/api/auth/login', json={
            'email': 'reset4@ulaval.ca',
            'password': 'NewSecurePass123'
        })
        self.assertEqual(old_login.status_code, 401)
        self.assertEqual(new_login.status_code, 200)


if __name__ == '__main__':
    import unittest
    unittest.main()

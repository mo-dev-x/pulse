"""Automated tests for Phase 5A CAS integration."""

from pathlib import Path
import sys
from unittest.mock import patch

# Ensure `app` imports resolve when tests are run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models.user import User
from tests.phase5_test_utils import Phase5BaseTestCase


class FakeCASClient:
    """Simple CAS test double."""

    def __init__(self, version=None, service_url=None, server_url=None):
        self.version = version
        self.service_url = service_url
        self.server_url = server_url

    def get_login_url(self):
        return 'https://cas.ulaval.ca/cas/login?service=http://test/callback'

    def verify_ticket(self, ticket):
        if ticket == 'ok-ticket':
            return (
                'idul123',
                {
                    'mail': 'casuser@ulaval.ca',
                    'displayName': 'CAS User',
                    'eduPersonPrimaryAffiliation': 'student'
                },
                None
            )
        return (None, {}, None)


class TestCASIntegration(Phase5BaseTestCase):

    def test_cas_login_redirect(self):
        with patch('app.routes.auth.CASClient', FakeCASClient):
            response = self.client.get('/api/auth/cas/login')
        self.assertEqual(response.status_code, 302)
        self.assertIn('cas.ulaval.ca', response.location)

    def test_cas_callback_creates_user(self):
        with patch('app.routes.auth.CASClient', FakeCASClient):
            response = self.client.get('/api/auth/cas/callback?ticket=ok-ticket')

        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertIn('token', payload)
        self.assertEqual(payload['user']['email'], 'casuser@ulaval.ca')
        self.assertEqual(payload['user']['cas_username'], 'idul123')
        self.assertTrue(payload['user']['is_verified'])

    def test_cas_callback_updates_existing_user(self):
        self.register_user(email='casuser@ulaval.ca', username='legacy_user')
        user = User.query.filter_by(email='casuser@ulaval.ca').first()
        user.display_name = 'Legacy'
        user.is_verified = False
        user.cas_username = None
        db.session.commit()

        with patch('app.routes.auth.CASClient', FakeCASClient):
            response = self.client.get('/api/auth/cas/callback?ticket=ok-ticket')

        self.assertEqual(response.status_code, 200, response.get_json())
        updated = User.query.filter_by(email='casuser@ulaval.ca').first()
        self.assertEqual(updated.cas_username, 'idul123')
        self.assertEqual(updated.display_name, 'CAS User')
        self.assertTrue(updated.is_verified)

    def test_cas_callback_invalid_ticket(self):
        with patch('app.routes.auth.CASClient', FakeCASClient):
            response = self.client.get('/api/auth/cas/callback?ticket=bad-ticket')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    import unittest
    unittest.main()

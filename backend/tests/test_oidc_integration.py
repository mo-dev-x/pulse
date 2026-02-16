"""Automated tests for Phase 5A OIDC (Azure Entra) integration."""

from pathlib import Path
import sys
from unittest.mock import patch

# Ensure `app` imports resolve when tests are run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models.user import User
from tests.phase5_test_utils import Phase5BaseTestCase


class FakeResponse:
    """Minimal requests.Response-like test double."""

    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def fake_post(url, data=None, timeout=10):
    """Mock OIDC token endpoint."""
    if data and data.get('code') == 'ok-code':
        return FakeResponse(200, {
            'access_token': 'access-ok',
            'id_token': 'id-token-placeholder',
            'token_type': 'Bearer'
        })
    if data and data.get('code') == 'other-code':
        return FakeResponse(200, {
            'access_token': 'access-other',
            'id_token': 'id-token-placeholder',
            'token_type': 'Bearer'
        })
    return FakeResponse(400, {'error': 'invalid_grant'})


def fake_get(url, headers=None, timeout=10):
    """Mock OIDC userinfo endpoint."""
    auth = (headers or {}).get('Authorization', '')
    if auth == 'Bearer access-ok':
        return FakeResponse(200, {
            'oid': 'oid-123',
            'email': 'oidcuser@ulaval.ca',
            'name': 'OIDC User',
            'eduPersonPrimaryAffiliation': 'student'
        })
    if auth == 'Bearer access-other':
        return FakeResponse(200, {
            'oid': 'oid-123',
            'email': 'otheroidc@ulaval.ca',
            'name': 'Other OIDC User',
            'eduPersonPrimaryAffiliation': 'student'
        })
    return FakeResponse(401, {})


class TestOIDCIntegration(Phase5BaseTestCase):

    def setUp(self):
        super().setUp()
        self.app.config.update(
            ENABLE_OIDC_AUTH=True,
            OIDC_AUTHORIZE_URL='https://login.microsoftonline.com/test/oauth2/v2.0/authorize',
            OIDC_TOKEN_URL='https://login.microsoftonline.com/test/oauth2/v2.0/token',
            OIDC_USERINFO_URL='https://graph.microsoft.com/oidc/userinfo',
            OIDC_CLIENT_ID='client-id',
            OIDC_CLIENT_SECRET='client-secret',
            OIDC_REDIRECT_URI='http://127.0.0.1:5000/api/auth/oidc/callback',
            OIDC_SCOPE='openid profile email',
        )

    def test_oidc_routes_disabled_when_flag_off(self):
        self.app.config['ENABLE_OIDC_AUTH'] = False

        login_response = self.client.get('/api/auth/oidc/login')
        self.assertEqual(login_response.status_code, 503)

        callback_response = self.client.get('/api/auth/oidc/callback?code=ok-code&state=state-123')
        self.assertEqual(callback_response.status_code, 503)

    def test_oidc_login_redirect(self):
        response = self.client.get('/api/auth/oidc/login')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login.microsoftonline.com', response.location)

    def test_oidc_callback_creates_user(self):
        with self.client.session_transaction() as sess:
            sess['oidc_state'] = 'state-123'

        with patch('app.routes.auth.requests.post', side_effect=fake_post), patch(
            'app.routes.auth.requests.get', side_effect=fake_get
        ):
            response = self.client.get('/api/auth/oidc/callback?code=ok-code&state=state-123')

        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertIn('token', payload)
        self.assertEqual(payload['user']['email'], 'oidcuser@ulaval.ca')
        self.assertEqual(payload['user']['cas_username'], 'oid-123')
        self.assertTrue(payload['user']['is_verified'])

    def test_oidc_callback_updates_existing_user(self):
        self.register_user(email='oidcuser@ulaval.ca', username='legacy_user')
        user = User.query.filter_by(email='oidcuser@ulaval.ca').first()
        user.display_name = 'Legacy'
        user.is_verified = False
        user.cas_username = None
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['oidc_state'] = 'state-456'

        with patch('app.routes.auth.requests.post', side_effect=fake_post), patch(
            'app.routes.auth.requests.get', side_effect=fake_get
        ):
            response = self.client.get('/api/auth/oidc/callback?code=ok-code&state=state-456')

        self.assertEqual(response.status_code, 200, response.get_json())
        updated = User.query.filter_by(email='oidcuser@ulaval.ca').first()
        self.assertEqual(updated.cas_username, 'oid-123')
        self.assertEqual(updated.display_name, 'OIDC User')
        self.assertTrue(updated.is_verified)

    def test_oidc_callback_invalid_code(self):
        with self.client.session_transaction() as sess:
            sess['oidc_state'] = 'state-789'

        with patch('app.routes.auth.requests.post', side_effect=fake_post), patch(
            'app.routes.auth.requests.get', side_effect=fake_get
        ):
            response = self.client.get('/api/auth/oidc/callback?code=bad-code&state=state-789')
        self.assertEqual(response.status_code, 401)

    def test_oidc_callback_rejects_collision_on_create(self):
        self.register_user(email='linked@ulaval.ca', username='linked_user')
        linked = User.query.filter_by(email='linked@ulaval.ca').first()
        linked.cas_username = 'oid-123'
        linked.is_verified = True
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['oidc_state'] = 'state-abc'

        with patch('app.routes.auth.requests.post', side_effect=fake_post), patch(
            'app.routes.auth.requests.get', side_effect=fake_get
        ):
            response = self.client.get('/api/auth/oidc/callback?code=other-code&state=state-abc')

        self.assertEqual(response.status_code, 409, response.get_json())
        self.assertIn('identit', response.get_json()['message'].lower())

    def test_oidc_callback_rejects_invalid_state(self):
        with self.client.session_transaction() as sess:
            sess['oidc_state'] = 'expected'

        response = self.client.get('/api/auth/oidc/callback?code=ok-code&state=unexpected')
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    import unittest
    unittest.main()

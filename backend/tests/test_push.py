"""Automated tests for Phase 6 push subscriptions."""

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import PushSubscription
from tests.phase5_test_utils import Phase5BaseTestCase


class TestPush(Phase5BaseTestCase):

    def setUp(self):
        super().setUp()
        self.app.config['PUSH_ENABLED'] = True

    def _verified_user(self, email, username):
        token, _ = self.register_user(email=email, username=username)
        self.mark_verified(email)
        return token

    def test_subscribe_and_unsubscribe_device(self):
        token = self._verified_user('push1@ulaval.ca', 'push1')
        subscribe = self.client.post(
            '/api/push/subscribe',
            json={'platform': 'web', 'token': 'abc123', 'device_label': 'Chrome'},
            headers=self.auth_headers(token),
        )
        self.assertEqual(subscribe.status_code, 201, subscribe.get_json())
        subscription_id = subscribe.get_json()['subscription_id']
        self.assertEqual(PushSubscription.query.count(), 1)

        delete_resp = self.client.delete(f'/api/push/subscribe/{subscription_id}', headers=self.auth_headers(token))
        self.assertEqual(delete_resp.status_code, 200, delete_resp.get_json())
        self.assertFalse(db.session.get(PushSubscription, subscription_id).is_active)

    def test_subscribe_is_idempotent_for_same_token(self):
        token = self._verified_user('push2@ulaval.ca', 'push2')
        first = self.client.post('/api/push/subscribe', json={'platform': 'web', 'token': 'same-token'}, headers=self.auth_headers(token))
        second = self.client.post('/api/push/subscribe', json={'platform': 'ios', 'token': 'same-token'}, headers=self.auth_headers(token))
        self.assertEqual(first.status_code, 201, first.get_json())
        self.assertEqual(second.status_code, 200, second.get_json())
        self.assertEqual(PushSubscription.query.count(), 1)

    def test_test_push_endpoint_calls_service(self):
        token = self._verified_user('push3@ulaval.ca', 'push3')
        self.client.post('/api/push/subscribe', json={'platform': 'web', 'token': 'notify-me'}, headers=self.auth_headers(token))

        with patch('app.routes.push.send_push_notification', return_value={'sent': 1, 'skipped': False}) as mocked:
            response = self.client.post('/api/push/test', headers=self.auth_headers(token))
        self.assertEqual(response.status_code, 200, response.get_json())
        mocked.assert_called_once()

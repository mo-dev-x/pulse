"""Automated tests for Phase 6 direct messaging."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import Conversation, Message, User
from tests.phase5_test_utils import Phase5BaseTestCase


class TestMessages(Phase5BaseTestCase):

    def _verified_user(self, email, username):
        token, user = self.register_user(email=email, username=username)
        self.mark_verified(email)
        return token, user

    def _start_conversation(self, token, username):
        response = self.client.post(
            '/api/messages/conversations',
            json={'username': username},
            headers=self.auth_headers(token),
        )
        self.assertIn(response.status_code, (200, 201), response.get_json())
        return response.get_json()['conversation']['id'], response

    def _send_message(self, token, conversation_id, content='Hello there'):
        response = self.client.post(
            f'/api/messages/conversations/{conversation_id}',
            json={'content': content},
            headers=self.auth_headers(token),
        )
        return response

    def test_user_can_start_a_conversation(self):
        token_a, _ = self._verified_user('dm_start_a@ulaval.ca', 'dm_start_a')
        _, user_b = self._verified_user('dm_start_b@ulaval.ca', 'dm_start_b')

        response = self.client.post('/api/messages/conversations', json={'username': user_b['username']}, headers=self.auth_headers(token_a))
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(Conversation.query.count(), 1)

    def test_starting_same_conversation_twice_is_idempotent(self):
        token_a, _ = self._verified_user('dm_idem_a@ulaval.ca', 'dm_idem_a')
        _, user_b = self._verified_user('dm_idem_b@ulaval.ca', 'dm_idem_b')

        first_id, first = self._start_conversation(token_a, user_b['username'])
        second_id, second = self._start_conversation(token_a, user_b['username'])
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first_id, second_id)
        self.assertEqual(Conversation.query.count(), 1)

    def test_cannot_message_yourself(self):
        token_a, user_a = self._verified_user('dm_self@ulaval.ca', 'dm_self')
        response = self.client.post('/api/messages/conversations', json={'username': user_a['username']}, headers=self.auth_headers(token_a))
        self.assertEqual(response.status_code, 400)

    def test_cannot_start_conversation_with_deactivated_user(self):
        token_a, _ = self._verified_user('dm_deact_a@ulaval.ca', 'dm_deact_a')
        _, user_b = self._verified_user('dm_deact_b@ulaval.ca', 'dm_deact_b')
        db_user = db.session.get(User, user_b['id'])
        db_user.is_deactivated = True
        db.session.commit()

        response = self.client.post('/api/messages/conversations', json={'username': user_b['username']}, headers=self.auth_headers(token_a))
        self.assertEqual(response.status_code, 404, response.get_json())

    def test_can_send_a_message(self):
        token_a, _ = self._verified_user('dm_send_a@ulaval.ca', 'dm_send_a')
        _, user_b = self._verified_user('dm_send_b@ulaval.ca', 'dm_send_b')
        conversation_id, _ = self._start_conversation(token_a, user_b['username'])

        response = self._send_message(token_a, conversation_id, 'First DM')
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(Message.query.count(), 1)

    def test_messages_paginate_correctly(self):
        token_a, _ = self._verified_user('dm_page_a@ulaval.ca', 'dm_page_a')
        token_b, user_b = self._verified_user('dm_page_b@ulaval.ca', 'dm_page_b')
        conversation_id, _ = self._start_conversation(token_a, user_b['username'])

        for idx in range(3):
            sender = token_a if idx % 2 == 0 else token_b
            response = self._send_message(sender, conversation_id, f'Message {idx}')
            self.assertEqual(response.status_code, 201, response.get_json())

        page_one = self.client.get(
            f'/api/messages/conversations/{conversation_id}?page=1&per_page=2',
            headers=self.auth_headers(token_a),
        )
        self.assertEqual(page_one.status_code, 200, page_one.get_json())
        payload = page_one.get_json()
        self.assertEqual(len(payload['messages']), 2)
        self.assertTrue(payload['has_more'])

    def test_non_participant_cannot_read_conversation(self):
        token_a, _ = self._verified_user('dm_forbid_a@ulaval.ca', 'dm_forbid_a')
        _, user_b = self._verified_user('dm_forbid_b@ulaval.ca', 'dm_forbid_b')
        token_c, _ = self._verified_user('dm_forbid_c@ulaval.ca', 'dm_forbid_c')
        conversation_id, _ = self._start_conversation(token_a, user_b['username'])

        response = self.client.get(f'/api/messages/conversations/{conversation_id}', headers=self.auth_headers(token_c))
        self.assertEqual(response.status_code, 403)

    def test_mark_as_read_updates_unread_count(self):
        token_a, _ = self._verified_user('dm_read_a@ulaval.ca', 'dm_read_a')
        token_b, user_b = self._verified_user('dm_read_b@ulaval.ca', 'dm_read_b')
        conversation_id, _ = self._start_conversation(token_a, user_b['username'])
        self._send_message(token_a, conversation_id, 'Unread one')
        self._send_message(token_a, conversation_id, 'Unread two')

        before = self.client.get('/api/messages/unread-count', headers=self.auth_headers(token_b))
        self.assertEqual(before.get_json()['unread_messages'], 2)

        marked = self.client.patch(f'/api/messages/conversations/{conversation_id}/read', headers=self.auth_headers(token_b))
        self.assertEqual(marked.status_code, 200, marked.get_json())
        self.assertEqual(marked.get_json()['marked_read'], 2)

        after = self.client.get('/api/messages/unread-count', headers=self.auth_headers(token_b))
        self.assertEqual(after.get_json()['unread_messages'], 0)

    def test_unread_count_endpoint_is_correct(self):
        token_a, _ = self._verified_user('dm_count_a@ulaval.ca', 'dm_count_a')
        token_b, user_b = self._verified_user('dm_count_b@ulaval.ca', 'dm_count_b')
        token_c, user_c = self._verified_user('dm_count_c@ulaval.ca', 'dm_count_c')

        conversation_ab, _ = self._start_conversation(token_a, user_b['username'])
        conversation_ac, _ = self._start_conversation(token_a, user_c['username'])
        self._send_message(token_a, conversation_ab, 'AB 1')
        self._send_message(token_a, conversation_ab, 'AB 2')
        self._send_message(token_a, conversation_ac, 'AC 1')

        unread = self.client.get('/api/messages/unread-count', headers=self.auth_headers(token_b))
        self.assertEqual(unread.get_json()['unread_conversations'], 1)
        self.assertEqual(unread.get_json()['unread_messages'], 2)

    def test_message_content_validated_min_max(self):
        token_a, _ = self._verified_user('dm_valid_a@ulaval.ca', 'dm_valid_a')
        _, user_b = self._verified_user('dm_valid_b@ulaval.ca', 'dm_valid_b')
        conversation_id, _ = self._start_conversation(token_a, user_b['username'])

        empty = self._send_message(token_a, conversation_id, '   ')
        self.assertEqual(empty.status_code, 400)

        too_long = self._send_message(token_a, conversation_id, 'x' * 1001)
        self.assertEqual(too_long.status_code, 400)

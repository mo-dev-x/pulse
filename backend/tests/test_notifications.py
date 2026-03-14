"""Automated tests for Phase 5B notifications."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.notification import Notification
from tests.phase5_test_utils import Phase5BaseTestCase


class TestNotifications(Phase5BaseTestCase):

    def _make_verified_user(self, email, username):
        token, user = self.register_user(email=email, username=username)
        self.mark_verified(email)
        return token, user

    def test_notification_endpoints_mark_read_and_delete(self):
        token, user = self._make_verified_user('notif1@ulaval.ca', 'notif1')
        n = Notification(
            user_id=user['id'],
            type='system',
            title='System',
            message='Welcome',
        )
        from app import db
        db.session.add(n)
        db.session.commit()

        listing = self.client.get('/api/notifications', headers=self.auth_headers(token))
        self.assertEqual(listing.status_code, 200)
        payload = listing.get_json()
        self.assertEqual(payload['total'], 1)
        self.assertEqual(payload['unread_count'], 1)
        notification_id = payload['notifications'][0]['id']

        mark_read = self.client.patch(f'/api/notifications/{notification_id}/read', headers=self.auth_headers(token))
        self.assertEqual(mark_read.status_code, 200)

        mark_all = self.client.patch('/api/notifications/read-all', headers=self.auth_headers(token))
        self.assertEqual(mark_all.status_code, 200)

        delete_resp = self.client.delete(f'/api/notifications/{notification_id}', headers=self.auth_headers(token))
        self.assertEqual(delete_resp.status_code, 200)
        self.assertEqual(Notification.query.count(), 0)

    def test_auto_notification_on_follow(self):
        actor_token, _ = self._make_verified_user('notif2a@ulaval.ca', 'notif2a')
        _, target = self._make_verified_user('notif2b@ulaval.ca', 'notif2b')

        follow = self.client.post('/api/follow/@notif2b', headers=self.auth_headers(actor_token))
        self.assertEqual(follow.status_code, 201, follow.get_json())

        notification = Notification.query.filter_by(user_id=target['id'], type='new_follower').first()
        self.assertIsNotNone(notification)

    def test_auto_notification_on_comment_reaction_and_mentions(self):
        owner_token, owner = self._make_verified_user('notif3owner@ulaval.ca', 'notif3owner')
        actor_token, _ = self._make_verified_user('notif3actor@ulaval.ca', 'notif3actor')
        mention_token, mention_user = self._make_verified_user('notif3mention@ulaval.ca', 'notif3mention')

        post_id = self.create_post(owner_token, content='This post mentions nobody and is long enough.')

        comment = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': f'Hello @notif3mention nice post'},
            headers=self.auth_headers(actor_token),
        )
        self.assertEqual(comment.status_code, 201, comment.get_json())

        reaction = self.client.post(
            f'/api/posts/{post_id}/react',
            json={'emoji': '❤️'},
            headers=self.auth_headers(actor_token),
        )
        self.assertIn(reaction.status_code, (200, 201), reaction.get_json())

        self.assertIsNotNone(Notification.query.filter_by(user_id=owner['id'], type='new_comment').first())
        self.assertIsNotNone(Notification.query.filter_by(user_id=owner['id'], type='post_reaction').first())
        self.assertIsNotNone(Notification.query.filter_by(user_id=mention_user['id'], type='mention').first())

        # Mention in post creation
        post_with_mention = self.client.post(
            '/api/posts',
            json={'content': 'Creating a fresh post for @notif3mention with enough characters.', 'is_anonymous': False},
            headers=self.auth_headers(actor_token),
        )
        self.assertEqual(post_with_mention.status_code, 201, post_with_mention.get_json())


if __name__ == '__main__':
    import unittest
    unittest.main()

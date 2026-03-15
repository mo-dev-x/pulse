"""Automated tests for Phase 5A comment system."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Ensure `app` imports resolve when tests are run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models.comment import Comment
from tests.phase5_test_utils import Phase5BaseTestCase


class TestComments(Phase5BaseTestCase):

    def _verified_user_and_post(self, email, username):
        token, user = self.register_user(email=email, username=username)
        self.mark_verified(user['email'])
        post_id = self.create_post(token)
        return token, user, post_id

    def test_create_and_list_comments(self):
        token, _, post_id = self._verified_user_and_post('comment1@ulaval.ca', 'comment1')
        create = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'First comment'},
            headers=self.auth_headers(token)
        )
        self.assertEqual(create.status_code, 201, create.get_json())

        listing = self.client.get(f'/api/posts/{post_id}/comments')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.get_json()['total'], 1)

    def test_anonymous_comment_hides_user_id(self):
        token, _, post_id = self._verified_user_and_post('comment2@ulaval.ca', 'comment2')
        create = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'Anonymous comment', 'is_anonymous': True},
            headers=self.auth_headers(token)
        )
        self.assertEqual(create.status_code, 201, create.get_json())
        author = create.get_json()['comment']['author']
        self.assertIn('pseudonym', author)
        self.assertNotIn('id', author)

    def test_reply_and_fetch_replies(self):
        token, _, post_id = self._verified_user_and_post('comment3@ulaval.ca', 'comment3')
        parent_resp = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'Parent comment'},
            headers=self.auth_headers(token)
        )
        parent_id = parent_resp.get_json()['comment']['id']
        reply_resp = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'Reply comment', 'parent_id': parent_id},
            headers=self.auth_headers(token)
        )
        self.assertEqual(reply_resp.status_code, 201, reply_resp.get_json())

        replies = self.client.get(f'/api/comments/{parent_id}/replies')
        self.assertEqual(replies.status_code, 200)
        self.assertEqual(replies.get_json()['total'], 1)

    def test_nested_reply_is_rejected(self):
        token, _, post_id = self._verified_user_and_post('comment4@ulaval.ca', 'comment4')
        parent = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'Parent'},
            headers=self.auth_headers(token)
        ).get_json()['comment']['id']
        child = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'Child', 'parent_id': parent},
            headers=self.auth_headers(token)
        ).get_json()['comment']['id']

        nested = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'Nested child', 'parent_id': child},
            headers=self.auth_headers(token)
        )
        self.assertEqual(nested.status_code, 400)

    def test_edit_window_enforced(self):
        token, _, post_id = self._verified_user_and_post('comment5@ulaval.ca', 'comment5')
        comment_id = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'Editable comment'},
            headers=self.auth_headers(token)
        ).get_json()['comment']['id']

        ok_edit = self.client.patch(
            f'/api/comments/{comment_id}',
            json={'content': 'Updated in time'},
            headers=self.auth_headers(token)
        )
        self.assertEqual(ok_edit.status_code, 200, ok_edit.get_json())

        comment = db.session.get(Comment, comment_id)
        comment.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=6)
        db.session.commit()

        late_edit = self.client.patch(
            f'/api/comments/{comment_id}',
            json={'content': 'Too late'},
            headers=self.auth_headers(token)
        )
        self.assertEqual(late_edit.status_code, 400)

    def test_delete_comment(self):
        token, _, post_id = self._verified_user_and_post('comment6@ulaval.ca', 'comment6')
        comment_id = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'To delete'},
            headers=self.auth_headers(token)
        ).get_json()['comment']['id']

        delete_resp = self.client.delete(
            f'/api/comments/{comment_id}',
            headers=self.auth_headers(token)
        )
        self.assertEqual(delete_resp.status_code, 200)
        self.assertIsNone(db.session.get(Comment, comment_id))

    def test_comment_creation_requires_verified_account(self):
        token, _ = self.register_user(email='comment7@ulaval.ca', username='comment7')
        self.mark_verified('comment7@ulaval.ca')
        post_id = self.create_post(token)

        unverified_token, _ = self.register_user(email='comment8@ulaval.ca', username='comment8')
        response = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': 'I should be blocked'},
            headers=self.auth_headers(unverified_token)
        )
        self.assertEqual(response.status_code, 403)


if __name__ == '__main__':
    import unittest
    unittest.main()

"""Automated tests for Phase 5B bookmarks."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.phase5_test_utils import Phase5BaseTestCase


class TestBookmarks(Phase5BaseTestCase):

    def _verified(self, email, username):
        token, user = self.register_user(email=email, username=username)
        self.mark_verified(email)
        return token, user

    def test_bookmark_unbookmark_and_list(self):
        owner_token, _ = self._verified('bookmark_owner@ulaval.ca', 'bookmark_owner')
        reader_token, _ = self._verified('bookmark_reader@ulaval.ca', 'bookmark_reader')

        post_id = self.create_post(owner_token, content='Bookmark target post with enough characters.')

        bookmark = self.client.post(f'/api/posts/{post_id}/bookmark', headers=self.auth_headers(reader_token))
        self.assertEqual(bookmark.status_code, 201, bookmark.get_json())

        duplicate = self.client.post(f'/api/posts/{post_id}/bookmark', headers=self.auth_headers(reader_token))
        self.assertEqual(duplicate.status_code, 200, duplicate.get_json())

        listing = self.client.get('/api/bookmarks', headers=self.auth_headers(reader_token))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.get_json()['total'], 1)

        remove_resp = self.client.delete(f'/api/posts/{post_id}/bookmark', headers=self.auth_headers(reader_token))
        self.assertEqual(remove_resp.status_code, 200)

        listing_after = self.client.get('/api/bookmarks', headers=self.auth_headers(reader_token))
        self.assertEqual(listing_after.get_json()['total'], 0)


if __name__ == '__main__':
    import unittest
    unittest.main()

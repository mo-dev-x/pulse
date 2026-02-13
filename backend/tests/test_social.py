"""
Test Suite: Social Features API (Phase 3A)

Tests for follow/unfollow, followers/following lists, friends, user profiles, and feed.

Covers:
- POST   /api/follow/@{username}
- DELETE /api/unfollow/@{username}
- GET    /api/users/@{username}/followers
- GET    /api/users/@{username}/following
- GET    /api/users/me/friends
- GET    /api/users/@{username}
- GET    /api/posts/feed
- GET    /api/posts/me
- GET    /api/posts/me/anonymous
- GET    /api/posts/@{username}
- GET    /api/posts/zone/{zone_id}
- DELETE /api/posts/{post_id}

Usage:
    1. Start the Flask app: python run.py
    2. In another terminal: python tests/test_social.py
"""

import sys
import requests
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5000"

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

tests_passed = 0
tests_failed = 0


def print_header(title):
    print(f"\n{'=' * 70}")
    print(f"{BLUE}{title.center(70)}{RESET}")
    print(f"{'=' * 70}\n")


def print_test(test_name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        print(f"{GREEN}✅ PASS:{RESET} {test_name}")
    else:
        tests_failed += 1
        print(f"{RED}❌ FAIL:{RESET} {test_name}")
    if details:
        print(f"   {details}")


def register_user(suffix):
    """Register a new user and return (token, username)"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    username = f"social_{suffix}_{timestamp}"
    user_data = {
        'email': f'{username}@ulaval.ca',
        'password': 'SecurePass123!',
        'username': username,
        'display_name': f'Test {suffix.capitalize()}'
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code == 201:
        return response.json()['token'], username
    print(f"{RED}❌ Failed to register {suffix}: {response.status_code} {response.text}{RESET}")
    return None, None


def main():
    global tests_passed, tests_failed

    print_header("PULSE SOCIAL FEATURES TEST SUITE")
    print(f"{YELLOW}ℹ️  Make sure Flask app is running at {BASE_URL}{RESET}\n")

    # ─── Setup: Register two users ───────────────────────────────────────
    print_header("SETUP: Creating Test Users")

    token_a, username_a = register_user("alice")
    if not token_a:
        print(f"{RED}Cannot continue without users{RESET}")
        return 1

    token_b, username_b = register_user("bob")
    if not token_b:
        print(f"{RED}Cannot continue without users{RESET}")
        return 1

    headers_a = {"Authorization": f"Bearer {token_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {token_b}", "Content-Type": "application/json"}

    print(f"{GREEN}✅ Created users: {username_a} and {username_b}{RESET}")

    # ─── TEST 1: Follow a user ───────────────────────────────────────────
    print_header("TEST 1: Follow a User")

    response = requests.post(f"{BASE_URL}/api/follow/@{username_b}", headers=headers_a)
    print_test("Alice follows Bob → 201", response.status_code == 201,
               f"Status: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print_test("Response contains 'following' info",
                   'following' in data and data['following']['username'] == username_b)

    # ─── TEST 2: Can't follow self ───────────────────────────────────────
    print_header("TEST 2: Cannot Follow Self")

    response = requests.post(f"{BASE_URL}/api/follow/@{username_a}", headers=headers_a)
    print_test("Alice can't follow self → 400", response.status_code == 400,
               f"Status: {response.status_code}")

    # ─── TEST 3: Can't follow twice ──────────────────────────────────────
    print_header("TEST 3: Cannot Follow Twice")

    response = requests.post(f"{BASE_URL}/api/follow/@{username_b}", headers=headers_a)
    print_test("Already following → 400", response.status_code == 400,
               f"Status: {response.status_code}")

    # ─── TEST 4: Follow nonexistent user ─────────────────────────────────
    print_header("TEST 4: Follow Nonexistent User")

    response = requests.post(f"{BASE_URL}/api/follow/@ghost_user_999", headers=headers_a)
    print_test("Nonexistent user → 404", response.status_code == 404,
               f"Status: {response.status_code}")

    # ─── TEST 5: Get followers list ──────────────────────────────────────
    print_header("TEST 5: Followers List")

    response = requests.get(f"{BASE_URL}/api/users/@{username_b}/followers", headers=headers_a)
    print_test("Get Bob's followers → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        print_test("Total followers is 1", data.get('total') == 1,
                   f"Total: {data.get('total')}")
        followers = data.get('followers', [])
        print_test("Alice is in Bob's follower list",
                   len(followers) > 0 and followers[0]['username'] == username_a)

    # ─── TEST 6: Get following list ──────────────────────────────────────
    print_header("TEST 6: Following List")

    response = requests.get(f"{BASE_URL}/api/users/@{username_a}/following", headers=headers_a)
    print_test("Get Alice's following → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        print_test("Total following is 1", data.get('total') == 1,
                   f"Total: {data.get('total')}")
        following = data.get('following', [])
        print_test("Bob is in Alice's following list",
                   len(following) > 0 and following[0]['username'] == username_b)

    # ─── TEST 7: Friends (no mutual follow yet) ─────────────────────────
    print_header("TEST 7: Friends — One-Way Follow (Not Friends Yet)")

    response = requests.get(f"{BASE_URL}/api/users/me/friends", headers=headers_a)
    print_test("Get friends → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        print_test("Friends list is empty (one-way follow)",
                   data.get('total') == 0,
                   f"Total friends: {data.get('total')}")

    # ─── TEST 8: Bob follows Alice back → Friends! ───────────────────────
    print_header("TEST 8: Mutual Follow → Friends")

    response = requests.post(f"{BASE_URL}/api/follow/@{username_a}", headers=headers_b)
    print_test("Bob follows Alice back → 201", response.status_code == 201)

    # Check friends now
    response = requests.get(f"{BASE_URL}/api/users/me/friends", headers=headers_a)
    if response.status_code == 200:
        data = response.json()
        print_test("Now friends (mutual follow)",
                   data.get('total') == 1,
                   f"Total friends: {data.get('total')}")
        friends = data.get('friends', [])
        print_test("Bob is Alice's friend",
                   len(friends) > 0 and friends[0]['username'] == username_b)

    # ─── TEST 9: User profile ────────────────────────────────────────────
    print_header("TEST 9: User Profile")

    response = requests.get(f"{BASE_URL}/api/users/@{username_b}", headers=headers_a)
    print_test("Get Bob's profile → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        user = data.get('user', {})
        print_test("Profile has follower_count", 'follower_count' in user,
                   f"Followers: {user.get('follower_count')}")
        print_test("Profile has following_count", 'following_count' in user,
                   f"Following: {user.get('following_count')}")
        print_test("is_following is True", user.get('is_following') is True)
        print_test("is_friend is True", user.get('is_friend') is True)
        print_test("is_you is False", user.get('is_you') is False)

    # ─── TEST 10: Create posts for feed tests ────────────────────────────
    print_header("TEST 10: Create Posts for Feed Testing")

    # Bob creates a public post
    response = requests.post(f"{BASE_URL}/api/posts", headers=headers_b,
        json={"content": "Hey everyone! Having a great day at campus! 🎉", "zone_id": 1, "is_anonymous": False})
    public_post_id = None
    if response.status_code == 201:
        public_post_id = response.json()['post']['id']
        print_test("Bob creates public post → 201", True, f"Post ID: {public_post_id}")
    else:
        print_test("Bob creates public post", False, f"Status: {response.status_code}")

    # Bob creates an anonymous post
    response = requests.post(f"{BASE_URL}/api/posts", headers=headers_b,
        json={"content": "Feeling overwhelmed with assignments... 😞", "zone_id": 1, "is_anonymous": True})
    anon_post_id = None
    if response.status_code == 201:
        anon_post_id = response.json()['post']['id']
        print_test("Bob creates anonymous post → 201", True, f"Post ID: {anon_post_id}")
    else:
        print_test("Bob creates anonymous post", False, f"Status: {response.status_code}")

    # Alice creates a public post
    response = requests.post(f"{BASE_URL}/api/posts", headers=headers_a,
        json={"content": "Studying hard for finals. Let's do this! 💪", "zone_id": 2, "is_anonymous": False})
    alice_post_id = None
    if response.status_code == 201:
        alice_post_id = response.json()['post']['id']
        print_test("Alice creates public post → 201", True, f"Post ID: {alice_post_id}")
    else:
        print_test("Alice creates public post", False, f"Status: {response.status_code}")

    # ─── TEST 11: Feed (public posts from followed users only) ───────────
    print_header("TEST 11: Feed — Privacy Enforcement")

    response = requests.get(f"{BASE_URL}/api/posts/feed", headers=headers_a)
    print_test("Get Alice's feed → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        posts = data.get('posts', [])
        print_test("Feed is not empty", len(posts) > 0,
                   f"Total posts in feed: {data.get('total')}")

        # Check that Bob's public post is in the feed
        post_ids_in_feed = [p['id'] for p in posts]
        if public_post_id:
            print_test("Bob's public post is in feed",
                       public_post_id in post_ids_in_feed)

        # CRITICAL: Bob's anonymous post should NOT be in the feed
        if anon_post_id:
            print_test("Bob's anonymous post is NOT in feed (privacy!)",
                       anon_post_id not in post_ids_in_feed)

        # Verify no posts in feed are anonymous
        all_public = all(not p.get('is_anonymous', True) for p in posts)
        print_test("All feed posts are public (is_anonymous=False)", all_public)

    # ─── TEST 12: My Posts ───────────────────────────────────────────────
    print_header("TEST 12: My Posts")

    response = requests.get(f"{BASE_URL}/api/posts/me", headers=headers_a)
    print_test("Get Alice's public posts → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        posts = data.get('posts', [])
        all_public = all(not p.get('is_anonymous', True) for p in posts)
        print_test("All returned posts are public", all_public)

    # ─── TEST 13: My Anonymous Posts (private view) ──────────────────────
    print_header("TEST 13: My Anonymous Posts")

    response = requests.get(f"{BASE_URL}/api/posts/me/anonymous", headers=headers_b)
    print_test("Get Bob's anonymous posts → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        posts = data.get('posts', [])
        print_test("Has anonymous posts", len(posts) > 0,
                   f"Count: {len(posts)}")
        if len(posts) > 0:
            all_anon = all(p.get('is_anonymous', False) for p in posts)
            print_test("All returned posts are anonymous", all_anon)

    # ─── TEST 14: User's public posts ────────────────────────────────────
    print_header("TEST 14: User's Public Posts")

    response = requests.get(f"{BASE_URL}/api/posts/@{username_b}", headers=headers_a)
    print_test("Get Bob's public posts → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        posts = data.get('posts', [])
        # Should NOT contain anonymous posts
        all_public = all(not p.get('is_anonymous', True) for p in posts)
        print_test("Only public posts returned (no anonymous)", all_public)

    # ─── TEST 15: Zone posts ─────────────────────────────────────────────
    print_header("TEST 15: Zone Posts")

    response = requests.get(f"{BASE_URL}/api/posts/zone/1", headers=headers_a)
    print_test("Get Zone 1 posts → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        print_test("Has zone info", 'zone' in data)
        print_test("Has posts list", 'posts' in data)

    # ─── TEST 16: Delete post ────────────────────────────────────────────
    print_header("TEST 16: Delete Own Post")

    if alice_post_id:
        response = requests.delete(f"{BASE_URL}/api/posts/{alice_post_id}", headers=headers_a)
        print_test("Alice deletes own post → 200", response.status_code == 200)

        # Try to delete someone else's post
        if public_post_id:
            response = requests.delete(f"{BASE_URL}/api/posts/{public_post_id}", headers=headers_a)
            print_test("Alice can't delete Bob's post → 403",
                       response.status_code == 403,
                       f"Status: {response.status_code}")

    # ─── TEST 17: Unfollow ───────────────────────────────────────────────
    print_header("TEST 17: Unfollow")

    response = requests.delete(f"{BASE_URL}/api/unfollow/@{username_b}", headers=headers_a)
    print_test("Alice unfollows Bob → 200", response.status_code == 200)

    # Verify no longer following
    response = requests.get(f"{BASE_URL}/api/users/@{username_a}/following", headers=headers_a)
    if response.status_code == 200:
        data = response.json()
        print_test("Alice's following is now 0", data.get('total') == 0,
                   f"Total: {data.get('total')}")

    # Not following → unfollow should fail
    response = requests.delete(f"{BASE_URL}/api/unfollow/@{username_b}", headers=headers_a)
    print_test("Unfollow again → 400 (not following)", response.status_code == 400)

    # ─── TEST 18: Feed is empty after unfollow ───────────────────────────
    print_header("TEST 18: Feed After Unfollow")

    response = requests.get(f"{BASE_URL}/api/posts/feed", headers=headers_a)
    if response.status_code == 200:
        data = response.json()
        print_test("Feed is empty after unfollow",
                   data.get('total') == 0,
                   f"Total: {data.get('total')}")

    # ─── SUMMARY ─────────────────────────────────────────────────────────
    print_header("TEST SUMMARY")
    total = tests_passed + tests_failed
    print(f"Total: {total} | {GREEN}Passed: {tests_passed}{RESET} | {RED}Failed: {tests_failed}{RESET}")

    if tests_failed == 0:
        print(f"\n{GREEN}🎉 ALL SOCIAL TESTS PASSED! 🎉{RESET}\n")
        return 0
    else:
        print(f"\n{YELLOW}⚠️  Some tests failed. Check the output above.{RESET}\n")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests cancelled by user{RESET}")
    except requests.exceptions.ConnectionError:
        print(f"\n{RED}❌ Cannot connect to {BASE_URL}. Is the Flask app running?{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}❌ Unexpected error: {e}{RESET}\n")
        sys.exit(1)

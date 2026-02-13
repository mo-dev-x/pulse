"""
Test Suite: Reactions API (Phase 3C)

Tests for emoji reactions on posts.

Covers:
- POST   /api/posts/{post_id}/react      — Add/update reaction
- DELETE /api/posts/{post_id}/react      — Remove reaction
- GET    /api/posts/{post_id}/reactions  — Get counts

Privacy enforcement:
- Only aggregate counts returned (never "who reacted")
- Reactions on anonymous posts allowed
- One reaction per user per post

Usage:
    1. Start the Flask app: python run.py
    2. In another terminal: python tests/test_reactions.py
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
    username = f"react_{suffix}_{timestamp}"
    user_data = {
        'email': f'{username}@ulaval.ca',
        'password': 'SecurePass123!',
        'username': username,
        'display_name': f'React {suffix.capitalize()}'
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code == 201:
        return response.json()['token'], username
    print(f"{RED}❌ Failed to register {suffix}: {response.status_code}{RESET}")
    return None, None


def main():
    global tests_passed, tests_failed

    print_header("PULSE REACTIONS API TEST SUITE")
    print(f"{YELLOW}ℹ️  Make sure Flask app is running at {BASE_URL}{RESET}\n")

    # ─── Setup: Register users and create posts ──────────────────────────
    print_header("SETUP: Creating Test Users and Posts")

    token_a, username_a = register_user("user1")
    token_b, username_b = register_user("user2")
    if not token_a or not token_b:
        print(f"{RED}Cannot continue without users{RESET}")
        return 1

    headers_a = {"Authorization": f"Bearer {token_a}", "Content-Type": "application/json"}
    headers_b = {"Authorization": f"Bearer {token_b}", "Content-Type": "application/json"}

    # Create a public post
    response = requests.post(f"{BASE_URL}/api/posts", headers=headers_a,
        json={"content": "This is a public post for reaction testing! 🙂", "is_anonymous": False})
    public_post_id = response.json()['post']['id'] if response.status_code == 201 else None

    # Create an anonymous post
    response = requests.post(f"{BASE_URL}/api/posts", headers=headers_a,
        json={"content": "This is an anonymous post for reaction testing 🤫", "is_anonymous": True})
    anon_post_id = response.json()['post']['id'] if response.status_code == 201 else None

    if not public_post_id:
        print(f"{RED}Cannot continue without posts{RESET}")
        return 1

    print(f"{GREEN}✅ Created users and posts (public ID: {public_post_id}, anon ID: {anon_post_id}){RESET}")

    # ─── TEST 1: Add reaction ────────────────────────────────────────────
    print_header("TEST 1: Add Reaction to Public Post")

    response = requests.post(f"{BASE_URL}/api/posts/{public_post_id}/react",
        headers=headers_a, json={"emoji": "❤️"})
    print_test("Add ❤️ reaction → 201", response.status_code == 201,
               f"Status: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print_test("Response has counts",
                   'counts' in data,
                   f"Counts: {data.get('counts')}")

    # ─── TEST 2: Second user reacts ──────────────────────────────────────
    print_header("TEST 2: Second User Reacts")

    response = requests.post(f"{BASE_URL}/api/posts/{public_post_id}/react",
        headers=headers_b, json={"emoji": "👍"})
    print_test("User B adds 👍 → 201", response.status_code == 201)

    if response.status_code == 201:
        counts = response.json().get('counts', {})
        print_test("❤️ count is 1", counts.get('❤️') == 1, f"Got: {counts.get('❤️')}")
        print_test("👍 count is 1", counts.get('👍') == 1, f"Got: {counts.get('👍')}")

    # ─── TEST 3: Update reaction (same user reacts again) ────────────────
    print_header("TEST 3: Update Existing Reaction")

    response = requests.post(f"{BASE_URL}/api/posts/{public_post_id}/react",
        headers=headers_a, json={"emoji": "🔥"})
    print_test("User A changes ❤️ → 🔥 → 200", response.status_code == 200,
               f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print_test("Previous emoji returned",
                   data.get('reaction', {}).get('previous_emoji') == '❤️',
                   f"Previous: {data.get('reaction', {}).get('previous_emoji')}")
        counts = data.get('counts', {})
        print_test("❤️ count is now 0", counts.get('❤️', 0) == 0)
        print_test("🔥 count is now 1", counts.get('🔥') == 1)

    # ─── TEST 4: Invalid emoji ───────────────────────────────────────────
    print_header("TEST 4: Invalid Emoji Rejected")

    response = requests.post(f"{BASE_URL}/api/posts/{public_post_id}/react",
        headers=headers_a, json={"emoji": "🤡"})
    print_test("Invalid emoji → 400", response.status_code == 400,
               f"Status: {response.status_code}")

    if response.status_code == 400:
        data = response.json()
        print_test("Response has allowed_emojis", 'allowed_emojis' in data)

    # ─── TEST 5: Missing emoji ───────────────────────────────────────────
    print_header("TEST 5: Missing Emoji Field")

    response = requests.post(f"{BASE_URL}/api/posts/{public_post_id}/react",
        headers=headers_a, json={})
    print_test("No emoji → 400", response.status_code == 400)

    # ─── TEST 6: React to nonexistent post ───────────────────────────────
    print_header("TEST 6: React to Nonexistent Post")

    response = requests.post(f"{BASE_URL}/api/posts/999999/react",
        headers=headers_a, json={"emoji": "❤️"})
    print_test("Nonexistent post → 404", response.status_code == 404)

    # ─── TEST 7: Get reaction counts ─────────────────────────────────────
    print_header("TEST 7: Get Reaction Counts")

    response = requests.get(f"{BASE_URL}/api/posts/{public_post_id}/reactions",
        headers=headers_a)
    print_test("Get reactions → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        print_test("Has reaction counts", 'reactions' in data)
        print_test("Has total_reactions", 'total_reactions' in data,
                   f"Total: {data.get('total_reactions')}")
        print_test("Has my_reaction", 'my_reaction' in data,
                   f"My reaction: {data.get('my_reaction')}")

        # PRIVACY: verify no user info is leaked
        raw = str(data)
        print_test("No 'user_id' in response (privacy)", 'user_id' not in raw)
        print_test("No 'username' in response (privacy)", 'username' not in raw)

    # ─── TEST 8: React to anonymous post ─────────────────────────────────
    print_header("TEST 8: React to Anonymous Post")

    if anon_post_id:
        response = requests.post(f"{BASE_URL}/api/posts/{anon_post_id}/react",
            headers=headers_b, json={"emoji": "🙏"})
        print_test("React to anonymous post → 201", response.status_code == 201)

        # Get counts — should work, only counts returned
        response = requests.get(f"{BASE_URL}/api/posts/{anon_post_id}/reactions",
            headers=headers_b)
        if response.status_code == 200:
            data = response.json()
            print_test("Anonymous post reactions return counts only",
                       'reactions' in data and data.get('total_reactions', 0) > 0)

    # ─── TEST 9: Remove reaction ─────────────────────────────────────────
    print_header("TEST 9: Remove Reaction")

    response = requests.delete(f"{BASE_URL}/api/posts/{public_post_id}/react",
        headers=headers_a)
    print_test("Remove reaction → 200", response.status_code == 200)

    if response.status_code == 200:
        counts = response.json().get('counts', {})
        print_test("🔥 count is now 0 after removal", counts.get('🔥', 0) == 0)

    # ─── TEST 10: Remove nonexistent reaction ────────────────────────────
    print_header("TEST 10: Remove Nonexistent Reaction")

    response = requests.delete(f"{BASE_URL}/api/posts/{public_post_id}/react",
        headers=headers_a)
    print_test("Remove again → 404 (no reaction)", response.status_code == 404)

    # ─── TEST 11: Verify final state ─────────────────────────────────────
    print_header("TEST 11: Verify Final Reaction State")

    response = requests.get(f"{BASE_URL}/api/posts/{public_post_id}/reactions",
        headers=headers_a)
    if response.status_code == 200:
        data = response.json()
        print_test("User A has no reaction", data.get('my_reaction') is None)
        print_test("Total reactions is 1 (only User B's 👍)",
                   data.get('total_reactions') == 1,
                   f"Total: {data.get('total_reactions')}")

    # ─── SUMMARY ─────────────────────────────────────────────────────────
    print_header("TEST SUMMARY")
    total = tests_passed + tests_failed
    print(f"Total: {total} | {GREEN}Passed: {tests_passed}{RESET} | {RED}Failed: {tests_failed}{RESET}")

    if tests_failed == 0:
        print(f"\n{GREEN}🎉 ALL REACTION TESTS PASSED! 🎉{RESET}\n")
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

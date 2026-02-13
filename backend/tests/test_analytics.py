"""
Test Suite: Analytics API (Phase 4)

Tests for analytics endpoints and privacy threshold enforcement.

Covers:
- GET /api/analytics/daily?date=YYYY-MM-DD&zone_id=X
- GET /api/analytics/weekly?week_start=YYYY-MM-DD&zone_id=X
- GET /api/analytics/campus?date=YYYY-MM-DD

Privacy enforcement:
- Aggregates only shown when total_posts >= 10
- Below threshold returns "insufficient data" message
- Disclaimer included in every response

Usage:
    1. Start the Flask app: python run.py
    2. In another terminal: python tests/test_analytics.py

Note: Some tests may show "insufficient data" if fewer than 10 posts
      exist in the database — this is correct privacy behavior.
"""

import sys
import requests
from datetime import datetime, timedelta

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
    username = f"analytics_{suffix}_{timestamp}"
    user_data = {
        'email': f'{username}@ulaval.ca',
        'password': 'SecurePass123!',
        'username': username,
        'display_name': f'Analytics {suffix.capitalize()}'
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code == 201:
        return response.json()['token'], username
    print(f"{RED}❌ Failed to register {suffix}: {response.status_code}{RESET}")
    return None, None


def create_posts(token, count, zone_id=1):
    """Create a batch of posts for aggregation testing"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    created = 0
    sentiments = [
        "I'm so happy today! The weather is beautiful! 😊",
        "Feeling great about my project progress! 🎉",
        "Love the new library renovation, it's amazing! ❤️",
        "Campus food has really improved this semester! 👍",
        "Just had the best study session ever! 💪",
        "Morning coffee at the bistro was perfect today ☕",
        "Really enjoying my algorithms class this term 🧑‍💻",
        "The fall foliage on campus is gorgeous! 🍂",
        "Had an awesome practice session at the gym! 🏋️",
        "Finally finished my thesis proposal! So relieved! 😌",
        "Group project went surprisingly well today! 🤝",
        "Great talk by the guest speaker at the auditorium! 🎤",
    ]

    for i in range(count):
        content = sentiments[i % len(sentiments)]
        response = requests.post(f"{BASE_URL}/api/posts", headers=headers,
            json={"content": content, "zone_id": zone_id, "is_anonymous": False})
        if response.status_code == 201:
            created += 1
    return created


def main():
    global tests_passed, tests_failed

    print_header("PULSE ANALYTICS API TEST SUITE")
    print(f"{YELLOW}ℹ️  Make sure Flask app is running at {BASE_URL}{RESET}\n")

    # ─── Setup ───────────────────────────────────────────────────────────
    print_header("SETUP: Creating Test Users and Posts")

    token_a, username_a = register_user("poster1")
    if not token_a:
        print(f"{RED}Cannot continue without users{RESET}")
        return 1

    headers_a = {"Authorization": f"Bearer {token_a}", "Content-Type": "application/json"}

    # Create 12 posts in zone 1 (above the privacy threshold of 10)
    created = create_posts(token_a, 12, zone_id=1)
    print(f"{GREEN}✅ Created {created} posts in Zone 1{RESET}")

    today = datetime.now().strftime('%Y-%m-%d')
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')

    # ─── TEST 1: Daily analytics ─────────────────────────────────────────
    print_header("TEST 1: Daily Analytics")

    response = requests.get(f"{BASE_URL}/api/analytics/daily",
        headers=headers_a, params={"date": today})
    print_test("Get daily analytics → 200", response.status_code == 200,
               f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print_test("Has 'aggregate' field", 'aggregate' in data)
        agg = data.get('aggregate', {})

        # The aggregate will either have data or an insufficient data message
        if 'message' in agg:
            print_test("Below threshold: returns 'insufficient data' message",
                       'insufficient' in agg.get('message', '').lower(),
                       f"Message: {agg.get('message')}")
            print_test("Shows minimum required",
                       agg.get('minimum_required') == 10,
                       f"Min: {agg.get('minimum_required')}")
        else:
            print_test("Has total_posts", 'total_posts' in agg,
                       f"Total: {agg.get('total_posts')}")
            print_test("Has avg_sentiment", 'avg_sentiment' in agg)
            print_test("Has mood_label", 'mood_label' in agg,
                       f"Mood: {agg.get('mood_label')}")
            print_test("Total posts >= 10 (threshold met)",
                       agg.get('total_posts', 0) >= 10)

    # ─── TEST 2: Daily analytics with zone filter ────────────────────────
    print_header("TEST 2: Daily Analytics with Zone Filter")

    response = requests.get(f"{BASE_URL}/api/analytics/daily",
        headers=headers_a, params={"date": today, "zone_id": 1})
    print_test("Get daily analytics for Zone 1 → 200",
               response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        print_test("Response has aggregate", 'aggregate' in data)
        print_test("Zone filter applied", data.get('zone_id') == 1 or 'zone_id' in str(data))

    # ─── TEST 3: Daily analytics — empty zone ───────────────────────────
    print_header("TEST 3: Daily Analytics — Empty Zone")

    response = requests.get(f"{BASE_URL}/api/analytics/daily",
        headers=headers_a, params={"date": today, "zone_id": 9})
    print_test("Empty zone → 200 (with threshold message or empty)",
               response.status_code == 200,
               f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        agg = data.get('aggregate', {})
        # Should show insufficient data for a zone with no posts
        has_insufficient = 'message' in agg or agg.get('total_posts', 0) == 0
        print_test("Returns insufficient data or empty aggregate",
                   has_insufficient,
                   f"Response: {str(agg)[:100]}")

    # ─── TEST 4: Weekly analytics ────────────────────────────────────────
    print_header("TEST 4: Weekly Analytics")

    response = requests.get(f"{BASE_URL}/api/analytics/weekly",
        headers=headers_a, params={"week_start": week_start})
    print_test("Get weekly analytics → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        print_test("Has 'aggregate' field", 'aggregate' in data)
        agg = data.get('aggregate', {})

        if 'message' not in agg:
            print_test("Has total_posts", 'total_posts' in agg)
            print_test("Has avg_sentiment", 'avg_sentiment' in agg)
            print_test("Has mood_label", 'mood_label' in agg)

    # ─── TEST 5: Weekly analytics with zone ──────────────────────────────
    print_header("TEST 5: Weekly Analytics with Zone Filter")

    response = requests.get(f"{BASE_URL}/api/analytics/weekly",
        headers=headers_a, params={"week_start": week_start, "zone_id": 1})
    print_test("Weekly Zone 1 analytics → 200", response.status_code == 200)

    # ─── TEST 6: Campus-wide analytics ───────────────────────────────────
    print_header("TEST 6: Campus-Wide Analytics")

    response = requests.get(f"{BASE_URL}/api/analytics/campus",
        headers=headers_a, params={"date": today})
    print_test("Get campus analytics → 200", response.status_code == 200)

    if response.status_code == 200:
        data = response.json()
        print_test("Has 'campus_overview' field", 'campus_overview' in data)
        print_test("Has 'zone_breakdown' field", 'zone_breakdown' in data)
        print_test("Has discord disclaimer", 'disclaimer' in data,
                   f"Disclaimer: {data.get('disclaimer', 'MISSING')[:60]}...")

        overview = data.get('campus_overview', {})
        if 'message' not in overview:
            print_test("Campus overview has total_posts", 'total_posts' in overview)
            print_test("Campus overview has mood_label", 'mood_label' in overview)

    # ─── TEST 7: Campus analytics — default date (today) ─────────────────
    print_header("TEST 7: Campus Analytics — No Date Parameter")

    response = requests.get(f"{BASE_URL}/api/analytics/campus", headers=headers_a)
    print_test("No date param defaults to today → 200",
               response.status_code == 200)

    # ─── TEST 8: Invalid date format ─────────────────────────────────────
    print_header("TEST 8: Invalid Date Format")

    response = requests.get(f"{BASE_URL}/api/analytics/daily",
        headers=headers_a, params={"date": "not-a-date"})
    print_test("Invalid date format → 400", response.status_code == 400,
               f"Status: {response.status_code}")

    # ─── TEST 9: Future date (no data) ───────────────────────────────────
    print_header("TEST 9: Future Date")

    future = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    response = requests.get(f"{BASE_URL}/api/analytics/daily",
        headers=headers_a, params={"date": future})
    print_test("Future date → 200 (with threshold/empty)", response.status_code == 200)

    if response.status_code == 200:
        agg = response.json().get('aggregate', {})
        print_test("No data for future date",
                   'message' in agg or agg.get('total_posts', 0) == 0)

    # ─── TEST 10: Authentication required ────────────────────────────────
    print_header("TEST 10: Authentication Required")

    response = requests.get(f"{BASE_URL}/api/analytics/daily",
        params={"date": today})
    print_test("No auth token → 401", response.status_code == 401,
               f"Status: {response.status_code}")

    response = requests.get(f"{BASE_URL}/api/analytics/campus")
    print_test("Campus without auth → 401", response.status_code == 401)

    # ─── TEST 11: Privacy threshold validation ───────────────────────────
    print_header("TEST 11: Privacy Threshold Behavior")

    # Create a post in a rarely used zone to test threshold
    token_b, _ = register_user("poster2")
    if token_b:
        headers_b = {"Authorization": f"Bearer {token_b}", "Content-Type": "application/json"}
        # Only 1 post in zone 8 — well below threshold
        requests.post(f"{BASE_URL}/api/posts", headers=headers_b,
            json={"content": "Testing privacy threshold in a quiet zone 🤫",
                   "zone_id": 8, "is_anonymous": False})

        response = requests.get(f"{BASE_URL}/api/analytics/daily",
            headers=headers_b, params={"date": today, "zone_id": 8})

        if response.status_code == 200:
            agg = response.json().get('aggregate', {})
            if 'message' in agg:
                print_test("Below threshold: privacy message shown",
                           'insufficient' in agg.get('message', '').lower())
                print_test("Shows minimum_required = 10",
                           agg.get('minimum_required') == 10)
                print_test("Does NOT expose avg_sentiment", 'avg_sentiment' not in agg)
            else:
                # If there were already 10+ posts in zone 8, data will be shown
                print_test("Zone 8 has enough data (threshold met)",
                           agg.get('total_posts', 0) >= 10,
                           f"Total: {agg.get('total_posts')}")

    # ─── SUMMARY ─────────────────────────────────────────────────────────
    print_header("TEST SUMMARY")
    total = tests_passed + tests_failed
    print(f"Total: {total} | {GREEN}Passed: {tests_passed}{RESET} | {RED}Failed: {tests_failed}{RESET}")

    if tests_failed == 0:
        print(f"\n{GREEN}🎉 ALL ANALYTICS TESTS PASSED! 🎉{RESET}\n")
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

"""
Test Suite: Posts API
Tests for post creation, sentiment analysis, and privacy enforcement.
Run with: python tests/test_posts.py
"""

import sys
import json
import requests
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_USER_EMAIL = "student@ulaval.ca"
TEST_USER_PASSWORD = "TestPass123!"

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

tests_passed = 0
tests_failed = 0

def print_header(title):
    print(f"\n{'='*70}")
    print(f"{BLUE}{title.center(70)}{RESET}")
    print(f"{'='*70}\n")

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

def login_and_get_token():
    response = requests.post(f"{BASE_URL}/api/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD})
    if response.status_code == 200:
        return response.json()['token']
    else:
        print(f"{RED}❌ Login failed!{RESET}")
        sys.exit(1)

def main():
    print_header("PULSE POSTS API TEST SUITE")
    token = login_and_get_token()
    
    # Test 1: Public English Post
    print_header("TEST 1: Public English Post")
    response = requests.post(f"{BASE_URL}/api/posts",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"content": "I love this campus! Amazing! 😊", "zone_id": 1, "is_anonymous": False})
    print_test("Creates public post", response.status_code == 201)
    if response.status_code == 201:
        post = response.json().get('post', {})
        print_test("Sentiment is positive", post.get('sentiment') == 'positive')
        print_test("Shows username", 'username' in post.get('author', {}))
    
    # Test 2: Anonymous French Post
    print_header("TEST 2: Anonymous French Post")
    response = requests.post(f"{BASE_URL}/api/posts",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"content": "Les examens me stressent beaucoup... 😰", "zone_id": 1, "is_anonymous": True})
    print_test("Creates anonymous post", response.status_code == 201)
    if response.status_code == 201:
        post = response.json().get('post', {})
        print_test("Sentiment is negative", post.get('sentiment') == 'negative')
        print_test("Shows pseudonym only", 'pseudonym' in post.get('author', {}))
        print_test("Hides username", 'username' not in post.get('author', {}))
    
    # Summary
    print_header("TEST SUMMARY")
    total = tests_passed + tests_failed
    print(f"Total: {total} | Passed: {tests_passed} | Failed: {tests_failed}")
    if tests_failed == 0:
        print(f"{GREEN}🎉 ALL TESTS PASSED!{RESET}\n")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())

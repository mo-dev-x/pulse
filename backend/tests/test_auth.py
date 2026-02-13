#!/usr/bin/env python3
"""
Authentication API Test Script

Tests the authentication endpoints:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- PATCH /api/auth/update-profile
- PATCH /api/auth/update-pseudonym

Usage:
    1. Start the Flask app: python run.py
    2. In another terminal: python tests/test_auth.py
"""

import requests
import json
from datetime import datetime
import sys
import os

# Add parent directory to path so we can import from app if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API base URL
BASE_URL = 'http://127.0.0.1:5000/api/auth'

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{YELLOW}ℹ️  {text}{RESET}")


def test_register():
    """Test user registration"""
    print_header("TEST 1: USER REGISTRATION")
    
    # Generate unique username with timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    test_user = {
        'email': f'testuser_{timestamp}@ulaval.ca',
        'password': 'SecurePass123!',
        'username': f'testuser_{timestamp}',
        'display_name': 'Test User'
    }
    
    print_info(f"Registering user: {test_user['username']}")
    
    try:
        response = requests.post(f'{BASE_URL}/register', json=test_user)
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"User registered successfully!")
            print(f"  User ID: {data['user']['id']}")
            print(f"  Username: {data['user']['username']}")
            print(f"  Email: {data['user']['email']}")
            print(f"  Token: {data['token'][:20]}...")
            return data['token'], test_user
        else:
            print_error(f"Registration failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return None, None
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return None, None


def test_login(user_credentials):
    """Test user login"""
    print_header("TEST 2: USER LOGIN")
    
    login_data = {
        'email': user_credentials['email'],
        'password': user_credentials['password']
    }
    
    print_info(f"Logging in as: {user_credentials['email']}")
    
    try:
        response = requests.post(f'{BASE_URL}/login', json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Login successful!")
            print(f"  Username: {data['user']['username']}")
            print(f"  Last login: {data['user'].get('created_at', 'N/A')}")
            print(f"  Token: {data['token'][:20]}...")
            return data['token']
        else:
            print_error(f"Login failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return None
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return None


def test_get_current_user(token):
    """Test getting current user profile"""
    print_header("TEST 3: GET CURRENT USER")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f'{BASE_URL}/me', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            user = data['user']
            print_success("Profile retrieved successfully!")
            print(f"  Username: {user['username']}")
            print(f"  Display Name: {user['display_name']}")
            print(f"  Email: {user['email']}")
            print(f"  Pseudonym: {user['pseudonym']}")
            print(f"  Can change pseudonym: {user['can_change_pseudonym']}")
            return True
        else:
            print_error(f"Failed to get profile: {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False


def test_update_profile(token):
    """Test updating user profile"""
    print_header("TEST 4: UPDATE PROFILE")
    
    headers = {'Authorization': f'Bearer {token}'}
    update_data = {
        'display_name': 'Updated Test User',
        'bio': 'This is my test bio for the Pulse platform!'
    }
    
    print_info("Updating profile with new display name and bio")
    
    try:
        response = requests.patch(f'{BASE_URL}/update-profile', 
                                 json=update_data, 
                                 headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            user = data['user']
            print_success("Profile updated successfully!")
            print(f"  New Display Name: {user['display_name']}")
            print(f"  New Bio: {user['bio']}")
            return True
        else:
            print_error(f"Profile update failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False


def test_update_pseudonym(token):
    """Test updating pseudonym"""
    print_header("TEST 5: UPDATE PSEUDONYM")
    
    headers = {'Authorization': f'Bearer {token}'}
    pseudonym_data = {
        'pseudonym': 'test_warrior'
    }
    
    print_info("Updating pseudonym to 'test_warrior'")
    
    try:
        response = requests.patch(f'{BASE_URL}/update-pseudonym', 
                                 json=pseudonym_data, 
                                 headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Pseudonym updated successfully!")
            print(f"  New Pseudonym: {data['pseudonym']}")
            print(f"  Next change available: 90 days from now")
            return True
        else:
            print_error(f"Pseudonym update failed: {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False


def test_invalid_login():
    """Test login with invalid credentials"""
    print_header("TEST 6: INVALID LOGIN (Should Fail)")
    
    invalid_data = {
        'email': 'nonexistent@ulaval.ca',
        'password': 'WrongPassword123!'
    }
    
    print_info("Attempting login with invalid credentials")
    
    try:
        response = requests.post(f'{BASE_URL}/login', json=invalid_data)
        
        if response.status_code == 401:
            print_success("Correctly rejected invalid credentials!")
            print(f"  Status: {response.status_code}")
            print(f"  Message: {response.json()['message']}")
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            print(f"  Should have returned 401 Unauthorized")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False


def test_weak_password():
    """Test registration with weak password"""
    print_header("TEST 7: WEAK PASSWORD (Should Fail)")
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    weak_password_user = {
        'email': f'weak_{timestamp}@ulaval.ca',
        'password': 'weak',  # Too short, no uppercase, no digit
        'username': f'weak_{timestamp}'
    }
    
    print_info("Attempting registration with weak password")
    
    try:
        response = requests.post(f'{BASE_URL}/register', json=weak_password_user)
        
        if response.status_code == 400:
            print_success("Correctly rejected weak password!")
            print(f"  Status: {response.status_code}")
            print(f"  Message: {response.json()['message']}")
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            print(f"  Should have returned 400 Bad Request")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False


def main():
    """Run all tests"""
    print(f"\n{BLUE}{'*' * 60}{RESET}")
    print(f"{BLUE}{'PULSE AUTHENTICATION API TESTS':^60}{RESET}")
    print(f"{BLUE}{'*' * 60}{RESET}\n")
    
    print_info("Make sure Flask app is running at http://127.0.0.1:5000")
    
    results = {
        'passed': 0,
        'failed': 0
    }
    
    # Test 1: Register
    token, user_credentials = test_register()
    if token and user_credentials:
        results['passed'] += 1
    else:
        results['failed'] += 1
        print_error("Cannot continue tests without valid registration")
        return results
    
    # Test 2: Login
    login_token = test_login(user_credentials)
    if login_token:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 3: Get current user
    if test_get_current_user(token):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 4: Update profile
    if test_update_profile(token):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 5: Update pseudonym
    if test_update_pseudonym(token):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 6: Invalid login
    if test_invalid_login():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 7: Weak password
    if test_weak_password():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Summary
    print_header("TEST SUMMARY")
    total = results['passed'] + results['failed']
    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {results['passed']}{RESET}")
    print(f"{RED}Failed: {results['failed']}{RESET}")
    
    if results['failed'] == 0:
        print(f"\n{GREEN}🎉 ALL TESTS PASSED! 🎉{RESET}\n")
    else:
        print(f"\n{YELLOW}⚠️  Some tests failed. Check the output above.{RESET}\n")
    
    return results


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Tests cancelled by user{RESET}\n")
    except Exception as e:
        print(f"\n\n{RED}Unexpected error: {e}{RESET}\n")
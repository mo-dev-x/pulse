#!/usr/bin/env python3
"""
Bilingual NLP Service Test Script

Tests sentiment analysis for both French and English text.

Usage:
    python test_nlp_bilingual.py
"""

import sys
sys.path.insert(0, '.')

from backend.app.services._DEPRECATED_nlp_service_textblob import BilingualNLPService

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


def print_result(text, expected, result):
    """Print test result"""
    lang = result.get('language', 'unknown')
    label = result.get('label', 'unknown')
    score = result.get('score', 0.0)
    
    success = (label == expected)
    symbol = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
    
    print(f"{symbol} [{lang.upper()}] \"{text}\"")
    print(f"   Expected: {expected} | Got: {label} (score: {score})")
    
    return success


def main():
    """Run all NLP tests"""
    print(f"\n{BLUE}{'*' * 60}{RESET}")
    print(f"{BLUE}{'BILINGUAL NLP SERVICE TESTS':^60}{RESET}")
    print(f"{BLUE}{'*' * 60}{RESET}\n")
    
    nlp = BilingualNLPService()
    
    results = {'passed': 0, 'failed': 0}
    
    # ========================================
    # ENGLISH TESTS
    # ========================================
    print_header("ENGLISH SENTIMENT TESTS")
    
    english_tests = [
        ("I absolutely love this campus! 😊", "positive"),
        ("This place is amazing!!", "positive"),
        ("Having a great time here", "positive"),
        ("I'm so stressed about exams 😭", "negative"),
        ("This is terrible and frustrating", "negative"),
        ("Feeling overwhelmed and anxious", "negative"),
        ("The library is open today", "neutral"),
        ("Class starts at 9am", "neutral"),
        ("Meeting in the cafeteria", "neutral"),
    ]
    
    for text, expected in english_tests:
        try:
            result = nlp.analyze_sentiment(text)
            if print_result(text, expected, result):
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print(f"{RED}❌ ERROR: {e}{RESET}")
            results['failed'] += 1
    
    # ========================================
    # FRENCH TESTS
    # ========================================
    print_header("FRENCH SENTIMENT TESTS")
    
    french_tests = [
        ("J'adore ce campus! 😊", "positive"),
        ("C'est vraiment génial!!", "positive"),
        ("Je passe un excellent moment ici", "positive"),
        ("Je suis tellement stressé par les examens 😭", "negative"),
        ("C'est terrible et frustrant", "negative"),
        ("Je me sens dépassé et anxieux", "negative"),
        ("La bibliothèque est ouverte aujourd'hui", "neutral"),
        ("Le cours commence à 9h", "neutral"),
        ("Rendez-vous à la cafétéria", "neutral"),
    ]
    
    for text, expected in french_tests:
        try:
            result = nlp.analyze_sentiment(text)
            if print_result(text, expected, result):
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print(f"{RED}❌ ERROR: {e}{RESET}")
            results['failed'] += 1
    
    # ========================================
    # MIXED / EDGE CASES
    # ========================================
    print_header("EDGE CASES & MIXED LANGUAGE")
    
    edge_cases = [
        ("Stressé but ça va! 😊", "positive"),  # Mixed FR/EN
        ("I'm stressed mais ça va aller", "neutral"),  # Mixed EN/FR
        ("😊😊😊", "positive"),  # Emojis only
        ("!!!", "neutral"),  # Punctuation only
    ]
    
    for text, expected in edge_cases:
        try:
            result = nlp.analyze_sentiment(text)
            print_result(text, expected, result)
            # Don't count these as pass/fail since they're edge cases
        except Exception as e:
            print(f"{YELLOW}⚠️  Expected edge case handling: {e}{RESET}")
    
    # ========================================
    # LANGUAGE DETECTION TEST
    # ========================================
    print_header("LANGUAGE DETECTION")
    
    detection_tests = [
        ("This is an English sentence", "en"),
        ("Ceci est une phrase française", "fr"),
        ("I love this! J'adore ça!", "en"),  # Mixed (should detect primary)
    ]
    
    for text, expected_lang in detection_tests:
        lang = nlp.detect_language(text)
        symbol = f"{GREEN}✅{RESET}" if lang == expected_lang else f"{YELLOW}⚠️{RESET}"
        print(f"{symbol} \"{text}\" → Detected: {lang} (expected: {expected_lang})")
    
    # ========================================
    # SUMMARY
    # ========================================
    print_header("TEST SUMMARY")
    
    total = results['passed'] + results['failed']
    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {results['passed']}{RESET}")
    print(f"{RED}Failed: {results['failed']}{RESET}")
    
    if results['failed'] == 0:
        print(f"\n{GREEN}🎉 ALL TESTS PASSED! 🎉{RESET}\n")
    else:
        percentage = (results['passed'] / total) * 100 if total > 0 else 0
        print(f"\n{YELLOW}Success Rate: {percentage:.1f}%{RESET}\n")
    
    print(f"{BLUE}{'*' * 60}{RESET}\n")
    
    print(f"{YELLOW}Note:{RESET} French sentiment analysis may be less accurate than English.")
    print("TextBlob provides basic sentiment for French, while VADER is optimized for English.")
    print("\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Tests cancelled by user{RESET}\n")
    except Exception as e:
        print(f"\n\n{RED}Unexpected error: {e}{RESET}\n")
        import traceback
        traceback.print_exc()

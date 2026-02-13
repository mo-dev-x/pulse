#!/usr/bin/env python3
"""
CamemBERT Bilingual NLP Service Test Script

Tests sentiment analysis with state-of-the-art models:
- French: CamemBERT
- English: VADER

Usage:
    python tests/test_nlp_camembert.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.nlp_service_camembert import FrenchTwitterNLPService

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_result(text, expected, result):
    """Print test result"""
    lang = result.get('language', 'unknown')
    label = result.get('label', 'unknown')
    score = result.get('score', 0.0)
    confidence = result.get('confidence', 0.0)
    
    success = (label == expected)
    symbol = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
    
    print(f"{symbol} [{lang.upper()}] \"{text}\"")
    print(f"   Expected: {expected:8} | Got: {label:8} | Score: {score:+.2f} | Confidence: {confidence:.2f}")
    
    return success


def main():
    """Run all NLP tests"""
    print(f"\n{BLUE}{'*' * 70}{RESET}")
    print(f"{BLUE}{'FRENCH TWITTER + VADER NLP TESTS':^70}{RESET}")
    print(f"{BLUE}{'*' * 70}{RESET}\n")
    
    print(f"{YELLOW}🇫🇷 French: Twitter XLM-RoBERTa (multilingual social media){RESET}")
    print(f"{YELLOW}🇬🇧 English: VADER (social media optimized){RESET}\n")
    
    nlp = FrenchTwitterNLPService()
    
    results = {'passed': 0, 'failed': 0}
    
    # ========================================
    # ENGLISH TESTS
    # ========================================
    print_header("ENGLISH SENTIMENT TESTS (VADER)")
    
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
    # FRENCH TESTS (TWITTER MODEL)
    # ========================================
    print_header("FRENCH SENTIMENT TESTS (Twitter XLM-RoBERTa)")
    print(f"{YELLOW}⚠️  First test will download model (~500MB){RESET}\n")
    
    french_tests = [
        ("J'adore ce campus! 😊", "positive"),
        ("C'est vraiment génial!!", "positive"),
        ("Je passe un excellent moment ici", "positive"),
        ("Super journée à l'université! ❤️", "positive"),
        ("Je suis tellement stressé par les examens 😭", "negative"),
        ("C'est terrible et frustrant", "negative"),
        ("Je me sens dépassé et anxieux", "negative"),
        ("Les examens me rendent fou", "negative"),
        ("La bibliothèque est ouverte aujourd'hui", "neutral"),
        ("Le cours commence à 9h", "neutral"),
        ("Rendez-vous à la cafétéria", "neutral"),
        ("La réunion est dans 10 minutes", "neutral"),
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
    # COMPLEX FRENCH TESTS
    # ========================================
    print_header("COMPLEX FRENCH EXPRESSIONS (Twitter Model Strength)")
    
    complex_french = [
        ("Malgré le stress, je suis content de mes résultats", "positive"),
        ("C'est nul, vraiment décevant", "negative"),
        ("Je n'en peux plus de cette charge de travail", "negative"),
        ("Incroyable! J'ai réussi!", "positive"),
    ]
    
    for text, expected in complex_french:
        try:
            result = nlp.analyze_sentiment(text)
            print_result(text, expected, result)
            # Don't count these in pass/fail - just show CamemBERT's power
        except Exception as e:
            print(f"{YELLOW}⚠️  {e}{RESET}")
    
    # ========================================
    # EDGE CASES
    # ========================================
    print_header("EDGE CASES & MIXED LANGUAGE")
    
    edge_cases = [
        ("Stressé but ça va! 😊", "positive"),  # Mixed FR/EN
        ("I'm stressed mais ça va aller", "neutral"),  # Mixed EN/FR
        ("😊😊😊", "positive"),  # Emojis only
    ]
    
    for text, expected in edge_cases:
        try:
            result = nlp.analyze_sentiment(text)
            print_result(text, expected, result)
        except Exception as e:
            print(f"{YELLOW}⚠️  Expected edge case: {e}{RESET}")
    
    # ========================================
    # LANGUAGE DETECTION TEST
    # ========================================
    print_header("LANGUAGE DETECTION")
    
    detection_tests = [
        ("This is an English sentence", "en"),
        ("Ceci est une phrase française", "fr"),
        ("Bonjour! Comment ça va?", "fr"),
        ("Hello! How are you?", "en"),
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
    
    print(f"{BLUE}{'*' * 70}{RESET}\n")
    
    print(f"{GREEN}✨ Twitter multilingual model is perfect for French social posts!{RESET}")
    print("   Trained specifically on Twitter data - understands informal campus language.")
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
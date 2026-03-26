"""Unit tests for the bilingual NLP emotion service."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.nlp_service_camembert import (
    EMOTION_LABELS,
    EMOTION_TO_DISPLAY,
    FrenchTwitterNLPService,
)


class FrenchTwitterNLPServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = FrenchTwitterNLPService()

    def test_emotion_label_and_display_are_valid_for_supported_emotions(self):
        for emotion in EMOTION_LABELS:
            with self.subTest(emotion=emotion):
                result = self.service._classify_score(
                    -0.8 if emotion in {'sadness', 'anger', 'fear', 'disgust'} else 0.8,
                    'fr',
                    confidence=0.91,
                    emotion_label=emotion,
                )

                self.assertIn(result['emotion_label'], EMOTION_LABELS)
                self.assertIn(
                    result['emotion_display'],
                    {EMOTION_TO_DISPLAY[label] for label in EMOTION_LABELS},
                )

    def test_high_fear_text_maps_to_stressed(self):
        result = self.service.analyze_english(
            "I am terrified about finals and panicking about everything."
        )

        self.assertEqual(result['emotion_label'], 'fear')
        self.assertEqual(result['emotion_display'], 'Stressed')
        self.assertEqual(result['label'], 'negative')

    def test_backward_compatibility_sentiment_label_is_derived_from_emotion(self):
        positive = self.service._classify_score(0.72, 'fr', confidence=0.88, emotion_label='joy')
        negative = self.service._classify_score(-0.81, 'fr', confidence=0.93, emotion_label='anger')
        neutral = self.service._classify_score(0.12, 'fr', confidence=0.22, emotion_label='surprise')

        self.assertEqual(positive['label'], 'positive')
        self.assertEqual(negative['label'], 'negative')
        self.assertEqual(neutral['label'], 'neutral')
        self.assertEqual(neutral['emotion_label'], 'neutral')
        self.assertEqual(neutral['emotion_display'], 'Neutral')

    def test_heartbreak_phrase_maps_to_sadness_not_joy(self):
        result = self.service.analyze_english("It broke my heart when everything fell apart.")

        self.assertEqual(result['emotion_label'], 'sadness')
        self.assertEqual(result['label'], 'negative')


if __name__ == '__main__':
    unittest.main()

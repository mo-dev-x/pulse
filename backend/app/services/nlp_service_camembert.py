"""
Bilingual NLP service using Hugging Face Inference API.

- French / multilingual: cardiffnlp/twitter-xlm-roberta-base-emotion via HF Inference API
- English: VADER (social media optimized) with campus emotion heuristics

No local model weights are downloaded or stored. Inference is delegated to
Hugging Face's hosted infrastructure, keeping the Railway deployment lightweight.
"""

import os
import re

import requests
from langdetect import detect, LangDetectException
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

HF_MODEL = "cardiffnlp/twitter-xlm-roberta-base-emotion"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

EMOTION_TO_DISPLAY = {
    'joy': 'Joy',
    'sadness': 'Sad',
    'anger': 'Frustrated',
    'fear': 'Stressed',
    'disgust': 'Overwhelmed',
    'surprise': 'Surprised',
    'neutral': 'Neutral',
}
EMOTION_TO_SENTIMENT = {
    'joy': 'positive',
    'surprise': 'positive',
    'sadness': 'negative',
    'anger': 'negative',
    'fear': 'negative',
    'disgust': 'negative',
    'neutral': 'neutral',
}
LOW_CONFIDENCE_THRESHOLD = 0.35


class FrenchTwitterNLPService:
    """
    Bilingual sentiment analysis.

    French/multilingual posts are sent to the HF Inference API
    (cardiffnlp/twitter-xlm-roberta-base-emotion). English posts
    are handled locally by VADER, which is lightweight and needs
    no network call.

    Falls back to VADER for French when HUGGINGFACE_API_KEY is not
    set or the API is unreachable.
    """

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    def clean_text(self, text):
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'([!?.]){4,}', r'\1\1\1', text)
        return text.strip()

    def detect_language(self, text):
        try:
            lang = detect(text)
            return 'fr' if lang == 'fr' else 'en'
        except LangDetectException:
            return 'fr'  # default to French (Université Laval)

    # ------------------------------------------------------------------
    # Analysers
    # ------------------------------------------------------------------

    def analyze_english(self, text):
        """Analyse English text with VADER."""
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']
        emotion_label, confidence = self._infer_english_emotion(text, compound)
        return self._classify_score(compound, 'en', confidence=confidence, emotion_label=emotion_label)

    def analyze_french(self, text):
        """
        Analyse French (and mixed-language) text via the HF Inference API.

        The API returns emotion probabilities for joy, sadness, anger, fear,
        disgust, and surprise. We pick the top emotion and derive a coarse
        [-1, +1] sentiment score from the positive/negative probability mass.
        """
        api_key = os.getenv('HUGGINGFACE_API_KEY')
        if not api_key:
            return self._vader_fallback(text, 'fr')

        try:
            response = requests.post(
                HF_API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"inputs": text},
                timeout=15,
            )

            if response.status_code == 503:
                # Model is warming up on HF's side
                return self._vader_fallback(text, 'fr')

            response.raise_for_status()
            raw = response.json()

            # Response shape: [[{"label": "joy", "score": 0.9}, ...]]
            emotions = raw[0] if raw and isinstance(raw[0], list) else raw

            score_map = {e['label'].lower(): float(e['score']) for e in emotions}
            top = max(emotions, key=lambda x: x['score'])
            emotion_label = top['label'].lower()
            confidence = float(top['score'])

            positive_mass = score_map.get('joy', 0.0) + score_map.get('surprise', 0.0)
            negative_mass = (
                score_map.get('sadness', 0.0)
                + score_map.get('anger', 0.0)
                + score_map.get('fear', 0.0)
                + score_map.get('disgust', 0.0)
            )
            score = max(min(positive_mass - negative_mass, 1.0), -1.0)

            return self._classify_score(score, 'fr', confidence=confidence, emotion_label=emotion_label)

        except Exception as e:
            return self._vader_fallback(text, 'fr', error=str(e))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _vader_fallback(self, text, language, error=None):
        """Use VADER when the HF API is unavailable."""
        result = self.analyze_english(text)
        result['language'] = language
        result['fallback'] = 'vader'
        if error:
            result['error'] = error
        return result

    def _infer_english_emotion(self, text, score):
        """Map English VADER score + keywords to a campus emotion label."""
        lowered = text.lower()
        keyword_map = {
            'fear':    ('stressed', 'stress', 'anxious', 'anxiety', 'panic', 'panicked', 'worried', 'nervous', 'scared', 'afraid', 'terrified', 'fear'),
            'anger':   ('angry', 'mad', 'furious', 'rage', 'frustrated', 'annoyed', 'irritated'),
            'disgust': ('overwhelmed', 'burned out', 'burnt out', 'disgusted', 'gross', 'drained', 'exhausted'),
            'sadness': ('sad', 'down', 'depressed', 'hopeless', 'lonely', 'crying', 'miserable', 'heartbroken', 'broken heart', 'broke my heart', 'breaks my heart', 'hurt so much', 'hurts so much', 'grief', 'grieving'),
            'surprise': ('surprised', 'shocked', 'unexpected', 'unbelievable', 'wow'),
            'joy':     ('happy', 'love', 'loving', 'amazing', 'great', 'awesome', 'excited', 'glad', 'relieved', 'proud'),
        }
        for emotion, keywords in keyword_map.items():
            if any(keyword in lowered for keyword in keywords):
                base_confidence = abs(score) if emotion not in {'joy', 'surprise'} else max(score, 0.0)
                return emotion, round(max(base_confidence, 0.6), 2)

        if score > 0.2:
            return 'joy', round(abs(score), 2)
        if score < -0.2:
            return 'sadness', round(abs(score), 2)
        return 'neutral', round(abs(score), 2)

    def _classify_score(self, score, language, confidence=None, emotion_label=None):
        """Build the standard result dict from a score and emotion label."""
        if confidence is None:
            confidence = abs(score)

        emotion_label = emotion_label or 'neutral'
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            emotion_label = 'neutral'

        label = EMOTION_TO_SENTIMENT.get(emotion_label, 'neutral')
        return {
            'score': round(score, 2),
            'label': label,
            'emotion_label': emotion_label,
            'emotion_display': EMOTION_TO_DISPLAY.get(emotion_label, 'Neutral'),
            'confidence': round(confidence, 2),
            'language': language,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_sentiment(self, text):
        """
        Analyse sentiment with automatic language detection.

        Args:
            text (str): Post content in any language.

        Returns:
            dict: score, label, emotion_label, emotion_display, confidence, language.

        Raises:
            ValueError: If text is too short (< 10 characters after cleaning).
        """
        cleaned = self.clean_text(text)
        if len(cleaned) < 10:
            raise ValueError("Text too short for reliable sentiment analysis")
        language = self.detect_language(cleaned)
        return self.analyze_french(cleaned) if language == 'fr' else self.analyze_english(cleaned)

    def analyze_batch(self, texts):
        """Analyse a list of texts, returning one result dict per entry."""
        results = []
        for text in texts:
            try:
                results.append(self.analyze_sentiment(text))
            except ValueError as e:
                results.append({'error': str(e), 'text': text})
        return results


# Singleton used across the application
nlp_service = FrenchTwitterNLPService()


def analyze_sentiment(text):
    """
    Convenience wrapper around nlp_service.analyze_sentiment.

    Usage:
        from app.services.nlp_service_camembert import analyze_sentiment
        result = analyze_sentiment("J'adore ce campus! 😊")
    """
    return nlp_service.analyze_sentiment(text)

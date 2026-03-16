"""
Production-grade bilingual NLP service with Twitter emotion detection.

Uses state-of-the-art models:
- French: cardiffnlp/twitter-xlm-roberta-base-emotion (multilingual Twitter)
- English: VADER (social media optimized) + lightweight campus emotion mapping

Designed for Universite Laval's bilingual campus community.
Perfect for social media-style wellness posts.
"""

import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect, LangDetectException

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


EMOTION_LABELS = ('joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise')
EMOTION_INDEX_TO_LABEL = dict(enumerate(EMOTION_LABELS))
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
    Production-grade bilingual sentiment analysis.

    French: cardiffnlp/twitter-xlm-roberta-base-emotion (multilingual Twitter)
    English: VADER (optimized for social media) with campus emotion heuristics
    """
    
    def __init__(self):
        """
        Initialize models
        
        Note: transformer models are loaded lazily on first use
        to avoid long startup times during development
        """
        # English analyzer (lightweight, always loaded)
        self.vader = SentimentIntensityAnalyzer()
        
        # French analyzer (heavy, loaded on first use)
        self._french_tokenizer = None
        self._french_model = None
        self._french_device = None
        self._use_french_fallback = not TORCH_AVAILABLE
    
    def _load_camembert(self):
        """
        Load French emotion model (lazy loading)
        
        This is expensive (~500MB download + GPU/CPU setup)
        so we only load when first needed
        """
        if self._french_model is not None or self._use_french_fallback:
            return  # Already loaded

        if not TORCH_AVAILABLE:
            print("⚠️  torch/transformers not available — French posts will use VADER fallback")
            self._use_french_fallback = True
            return

        print("Loading French emotion model...")
        print("   (This may take a minute on first run)")

        try:
            model_name = "cardiffnlp/twitter-xlm-roberta-base-emotion"
            self._french_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._french_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self._french_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._french_model.to(self._french_device)
            self._french_model.eval()
            print(f"French emotion model loaded successfully on {self._french_device}")
        except Exception as e:
            print(f"Failed to load French emotion model: {e}")
            print("   Falling back to basic French sentiment analysis")
            self._use_french_fallback = True

    def _analyze_french_fallback(self, text):
        """
        Lightweight fallback when the transformer model is unavailable.

        This keeps deployment environments like Railway working even when
        torch/model downloads are not possible.
        """
        result = self.analyze_english(text)
        result['language'] = 'fr'
        result['fallback'] = 'vader'
        return result
    
    def clean_text(self, text):
        """
        Prepare text for analysis
        
        Args:
            text (str): Raw user input
        
        Returns:
            str: Cleaned text
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove excessive punctuation (but keep some for sentiment)
        text = re.sub(r'([!?.]){4,}', r'\1\1\1', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def detect_language(self, text):
        """
        Detect if text is French or English
        
        Args:
            text (str): Text to analyze
        
        Returns:
            str: 'fr' or 'en'
        """
        try:
            lang = detect(text)
            return 'fr' if lang == 'fr' else 'en'
        except LangDetectException:
            # Default to French (primary language at Laval)
            return 'fr'
    
    def analyze_english(self, text):
        """
        Analyze English text using VADER
        
        VADER is specifically designed for social media text and handles:
        - Emojis
        - Slang
        - Capitalization (for emphasis)
        - Punctuation (!!!)
        
        Args:
            text (str): English text
        
        Returns:
            dict: Sentiment result
        """
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']  # -1 to +1
        
        emotion_label, confidence = self._infer_english_emotion(text, compound)
        return self._classify_score(
            compound,
            'en',
            confidence=confidence,
            emotion_label=emotion_label
        )
    
    def analyze_french(self, text):
        """
        Analyze French text using multilingual Twitter emotion model.
        
        Args:
            text (str): French text
        
        Returns:
            dict: Sentiment result
        """
        # Load model if not already loaded
        if self._french_model is None:
            self._load_camembert()

        if self._use_french_fallback or self._french_model is None or self._french_tokenizer is None:
            return self._analyze_french_fallback(text)
        
        try:
            # Tokenize text
            inputs = self._french_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Move to same device as model
            inputs = {k: v.to(self._french_device) for k, v in inputs.items()}
            
            # Get prediction
            with torch.no_grad():
                outputs = self._french_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            probs = predictions[0].cpu().numpy()

            predicted_index = int(probs.argmax())
            emotion_label = EMOTION_INDEX_TO_LABEL[predicted_index]
            confidence = float(probs[predicted_index])
            score = float(self._emotion_probabilities_to_score(probs))

            return self._classify_score(
                score,
                'fr',
                confidence=confidence,
                emotion_label=emotion_label
            )

        except Exception as e:
            # If French analysis fails, return neutral with error
            return {
                'score': 0.0,
                'label': 'neutral',
                'emotion_label': 'neutral',
                'emotion_display': EMOTION_TO_DISPLAY['neutral'],
                'confidence': 0.0,
                'language': 'fr',
                'error': str(e)
            }

    def _emotion_probabilities_to_score(self, probs):
        """Convert emotion probabilities into a coarse sentiment score."""
        positive_mass = float(probs[0] + probs[5])
        negative_mass = float(probs[1] + probs[2] + probs[3] + probs[4])
        return max(min(positive_mass - negative_mass, 1.0), -1.0)

    def _infer_english_emotion(self, text, score):
        """Map English text to a campus emotion label for API consistency."""
        lowered = text.lower()
        keyword_map = {
            'fear': ('stressed', 'stress', 'anxious', 'anxiety', 'panic', 'panicked', 'worried', 'nervous', 'scared', 'afraid', 'terrified', 'fear'),
            'anger': ('angry', 'mad', 'furious', 'rage', 'frustrated', 'annoyed', 'irritated'),
            'disgust': ('overwhelmed', 'burned out', 'burnt out', 'disgusted', 'gross', 'drained', 'exhausted'),
            'sadness': ('sad', 'down', 'depressed', 'hopeless', 'lonely', 'crying', 'miserable'),
            'surprise': ('surprised', 'shocked', 'unexpected', 'unbelievable', 'wow'),
            'joy': ('happy', 'love', 'loving', 'amazing', 'great', 'awesome', 'excited', 'glad', 'relieved', 'proud'),
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
        """
        Classify coarse sentiment and campus emotion labels.
        
        Args:
            score (float): Sentiment score from -1 to 1
            language (str): 'fr' or 'en'
            confidence (float, optional): Model confidence
        
        Returns:
            dict: Classification result
        """
        if confidence is None:
            confidence = abs(score)

        emotion_label = emotion_label or 'neutral'
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            emotion_label = 'neutral'

        label = EMOTION_TO_SENTIMENT.get(emotion_label, 'neutral')
        result = {
            'score': round(score, 2),
            'label': label,
            'emotion_label': emotion_label,
            'emotion_display': EMOTION_TO_DISPLAY.get(emotion_label, 'Neutral'),
            'confidence': round(confidence, 2),
            'language': language
        }

        return result
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment with automatic language detection
        
        This is the main method to use from other parts of the application.
        
        Args:
            text (str): User's post content (any language)
        
        Returns:
            dict with score, coarse sentiment label, emotion labels, confidence,
            and detected language.
        
        Raises:
            ValueError: If text is too short (< 10 characters)
        
        Example:
            >>> nlp = FrenchTwitterNLPService()
            >>> nlp.analyze_sentiment("J'adore ce campus! 😊")
            {
                'score': 0.87,
                'label': 'positive',
                'emotion_label': 'joy',
                'emotion_display': 'Joy',
                'confidence': 0.92,
                'language': 'fr'
            }
        """
        # Clean text
        cleaned_text = self.clean_text(text)
        
        # Validate length
        if len(cleaned_text) < 10:
            raise ValueError("Text too short for reliable sentiment analysis")
        
        # Detect language
        language = self.detect_language(cleaned_text)
        
        # Analyze with appropriate method
        if language == 'fr':
            result = self.analyze_french(cleaned_text)
        else:
            result = self.analyze_english(cleaned_text)
        
        return result
    
    def analyze_batch(self, texts):
        """
        Analyze multiple texts at once
        
        More efficient than calling analyze_sentiment() repeatedly
        because the transformer model can process batches.
        
        Args:
            texts (list): List of text strings
        
        Returns:
            list: List of sentiment results
        """
        results = []
        for text in texts:
            try:
                result = self.analyze_sentiment(text)
                results.append(result)
            except ValueError as e:
                results.append({
                    'error': str(e),
                    'text': text
                })
        
        return results


# Create a singleton instance for use across the application
nlp_service = FrenchTwitterNLPService()


# Convenience function for direct import
def analyze_sentiment(text):
    """
    Convenience function for sentiment analysis
    
    Usage:
        from app.services.nlp_service_camembert import analyze_sentiment
        result = analyze_sentiment("I love this place!")
    """
    return nlp_service.analyze_sentiment(text)

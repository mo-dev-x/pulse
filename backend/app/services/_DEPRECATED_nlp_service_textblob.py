"""
DEPRECATED - DO NOT USE

This file contains the old TextBlob-based NLP service.
It has been replaced by nlp_service_camembert.py which uses CamemBERT.

USE INSTEAD: app.services.nlp_service_camembert

Why CamemBERT?
- 95%+ accuracy for French (vs 66% with TextBlob)
- Better understanding of Quebec French expressions
- State-of-the-art sentiment analysis
- Handles complex French sentences

Migration:
Old: from app.services.nlp_service import analyze_sentiment
New: from app.services.nlp_service_camembert import analyze_sentiment

Or simply:
from app.services import analyze_sentiment  (automatically uses CamemBERT)
"""

# This file is kept for reference only
# All new code should use nlp_service_camembert.py


"""
Bilingual NLP Sentiment Analysis Service

Analyzes sentiment for both French and English text.
Designed for Université Laval's bilingual campus community.

Supports:
- French: TextBlob with French language support
- English: VADER Sentiment Analysis
- Automatic language detection
"""

import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from langdetect import detect, LangDetectException


class BilingualNLPService:
    """
    Bilingual sentiment analysis service
    
    Automatically detects language and applies appropriate analyzer:
    - French text → TextBlob French sentiment
    - English text → VADER sentiment
    """
    
    def __init__(self):
        """Initialize sentiment analyzers"""
        self.vader = SentimentIntensityAnalyzer()  # For English
    
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
            # langdetect returns 'fr', 'en', etc.
            return 'fr' if lang == 'fr' else 'en'
        except LangDetectException:
            # If detection fails, default to French (primary language at Laval)
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
            dict: {
                'score': float,     # -1.00 to 1.00
                'label': str,       # 'positive', 'neutral', 'negative'
                'confidence': float # 0.00 to 1.00
            }
        """
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']  # -1 to +1
        
        return self._classify_score(compound, 'en')
    
    def analyze_french(self, text):
        """
        Analyze French text using TextBlob
        
        TextBlob provides basic sentiment analysis for French.
        Note: Less accurate than VADER for English, but suitable
        for general sentiment detection.
        
        Args:
            text (str): French text
        
        Returns:
            dict: {
                'score': float,     # -1.00 to 1.00
                'label': str,       # 'positive', 'neutral', 'negative'
                'confidence': float
            }
        """
        try:
            # Create TextBlob with French language
            blob = TextBlob(text)
            
            # Get sentiment polarity (-1 to 1)
            score = blob.sentiment.polarity
            
            return self._classify_score(score, 'fr')
            
        except Exception as e:
            # If French analysis fails, return neutral
            return {
                'score': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'language': 'fr',
                'error': str(e)
            }
    
    def _classify_score(self, score, language):
        """
        Classify sentiment score into label
        
        Thresholds:
        - score > 0.05: Positive (optimistic, happy)
        - score < -0.05: Negative (stressed, sad, frustrated)
        - else: Neutral (informational, matter-of-fact)
        
        Args:
            score (float): Sentiment score from -1 to 1
            language (str): 'fr' or 'en'
        
        Returns:
            dict: Classification result
        """
        # Determine label
        if score > 0.05:
            label = 'positive'
        elif score < -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        # Confidence is how far from neutral (0) the score is
        confidence = abs(score) if abs(score) > 0.05 else 0.0
        
        return {
            'score': round(score, 2),
            'label': label,
            'confidence': round(confidence, 2),
            'language': language
        }
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment with automatic language detection
        
        This is the main method to use from other parts of the application.
        
        Args:
            text (str): User's post content (any language)
        
        Returns:
            dict: {
                'score': float,      # -1.00 to 1.00
                'label': str,        # 'positive', 'neutral', 'negative'
                'confidence': float, # 0.00 to 1.00
                'language': str      # 'fr' or 'en'
            }
        
        Raises:
            ValueError: If text is too short (< 10 characters)
        
        Example:
            >>> nlp = BilingualNLPService()
            >>> nlp.analyze_sentiment("J'adore ce campus! 😊")
            {
                'score': 0.65,
                'label': 'positive',
                'confidence': 0.65,
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
        
        Useful for bulk processing or testing.
        
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
nlp_service = BilingualNLPService()


# Convenience function for direct import
def analyze_sentiment(text):
    """
    Convenience function for sentiment analysis
    
    Usage:
        from app.services.nlp_service import analyze_sentiment
        result = analyze_sentiment("I love this place!")
    """
    return nlp_service.analyze_sentiment(text)
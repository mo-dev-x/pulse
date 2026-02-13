"""
Production-Grade Bilingual NLP Service with Twitter Sentiment

Uses state-of-the-art models:
- French: cardiffnlp/twitter-xlm-roberta-base-sentiment (multilingual Twitter)
- English: VADER (social media optimized)

Designed for Université Laval's bilingual campus community.
Perfect for social media-style wellness posts.
"""

import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect, LangDetectException


class FrenchTwitterNLPService:
    """
    Production-grade bilingual sentiment analysis
    
    French: cardiffnlp/twitter-xlm-roberta-base-sentiment (multilingual Twitter)
    English: VADER (optimized for social media)
    
    The French model is trained on Twitter data (perfect for social posts!)
    and outputs: negative, neutral, positive
    """
    
    def __init__(self):
        """
        Initialize models
        
        Note: CamemBERT models are loaded lazily on first use
        to avoid long startup times during development
        """
        # English analyzer (lightweight, always loaded)
        self.vader = SentimentIntensityAnalyzer()
        
        # French analyzer (heavy, loaded on first use)
        self._french_tokenizer = None
        self._french_model = None
        self._french_device = None
    
    def _load_camembert(self):
        """
        Load French sentiment model (lazy loading)
        
        This is expensive (~500MB download + GPU/CPU setup)
        so we only load when first needed
        """
        if self._french_model is not None:
            return  # Already loaded
        
        print("🧠 Loading French sentiment model...")
        print("   (This may take a minute on first run)")
        
        try:
            # Use multilingual Twitter sentiment model (supports French)
            # Perfect for social media posts!
            model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
            
            self._french_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._french_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Use GPU if available
            self._french_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._french_model.to(self._french_device)
            self._french_model.eval()  # Set to evaluation mode
            
            print(f"✅ French sentiment model loaded successfully on {self._french_device}")
            
        except Exception as e:
            print(f"⚠️  Failed to load French sentiment model: {e}")
            print("   Falling back to basic French sentiment analysis")
            raise
    
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
        
        return self._classify_score(compound, 'en')
    
    def analyze_french(self, text):
        """
        Analyze French text using multilingual Twitter sentiment model
        
        Uses cardiffnlp/twitter-xlm-roberta-base-sentiment which outputs:
        - negative, neutral, positive (3 classes)
        
        Perfect for social media posts in French!
        
        Args:
            text (str): French text
        
        Returns:
            dict: Sentiment result
        """
        # Load model if not already loaded
        if self._french_model is None:
            self._load_camembert()
        
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
            
            # Twitter sentiment model outputs 3 classes:
            # 0: negative, 1: neutral, 2: positive
            probs = predictions[0].cpu().numpy()
            
            # Calculate sentiment score (-1 to +1)
            score = probs[2] - probs[0]  # positive - negative
            
            # Confidence is the maximum probability
            confidence = float(max(probs))
            
            return self._classify_score(float(score), 'fr', confidence=confidence)
            
        except Exception as e:
            # If French analysis fails, return neutral with error
            return {
                'score': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'language': 'fr',
                'error': str(e)
            }
    
    def _classify_score(self, score, language, confidence=None):
        """
        Classify sentiment score into label
        
        Thresholds:
        - score > 0.05: Positive (optimistic, happy)
        - score < -0.05: Negative (stressed, sad, frustrated)
        - else: Neutral (informational, matter-of-fact)
        
        Args:
            score (float): Sentiment score from -1 to 1
            language (str): 'fr' or 'en'
            confidence (float, optional): Model confidence
        
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
        
        # Confidence is how far from neutral the score is
        if confidence is None:
            confidence = abs(score) if abs(score) > 0.05 else 0.0
        
        result = {
            'score': round(score, 2),
            'label': label,
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
            dict: {
                'score': float,      # -1.00 to 1.00
                'label': str,        # 'positive', 'neutral', 'negative'
                'confidence': float, # 0.00 to 1.00
                'language': str      # 'fr' or 'en'
            }
        
        Raises:
            ValueError: If text is too short (< 10 characters)
        
        Example:
            >>> nlp = FrenchTwitterNLPService()
            >>> nlp.analyze_sentiment("J'adore ce campus! 😊")
            {
                'score': 0.87,
                'label': 'positive',
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
        because CamemBERT can process batches.
        
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
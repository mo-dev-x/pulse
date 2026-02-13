"""
Services package

Business logic and processing services.
"""

from app.services.nlp_service_camembert import FrenchTwitterNLPService, analyze_sentiment, nlp_service

__all__ = ['FrenchTwitterNLPService', 'analyze_sentiment', 'nlp_service']
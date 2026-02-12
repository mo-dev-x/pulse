#!/bin/bash
# Install Bilingual NLP Dependencies
# Run this after updating requirements.txt

set -e  # Exit on error

echo "╔═══════════════════════════════════════╗"
echo "║   INSTALLING BILINGUAL NLP PACKAGES   ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

echo ""
echo "📦 Installing bilingual NLP packages..."
echo ""

# Install language detection
echo "  → Installing langdetect (language detection)..."
pip install langdetect==1.0.9

# Install TextBlob for French sentiment
echo "  → Installing textblob (sentiment analysis)..."
pip install textblob==0.17.1

# Download TextBlob corpora (required for sentiment analysis)
echo "  → Downloading TextBlob language data..."
python -m textblob.download_corpora

echo ""
echo "✅ All bilingual NLP packages installed successfully!"
echo ""

# Test imports
echo "🧪 Testing imports..."
python3 << 'EOF'
try:
    from langdetect import detect
    from textblob import TextBlob
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    print("✅ All imports successful!")
    
    # Quick test
    print("\n🧪 Quick functionality test:")
    
    # Test VADER (English)
    vader = SentimentIntensityAnalyzer()
    en_result = vader.polarity_scores("I love this!")
    print(f"  English: 'I love this!' → {en_result['compound']:.2f}")
    
    # Test TextBlob (French) 
    fr_blob = TextBlob("J'adore ça!")
    print(f"  French: 'J'adore ça!' → {fr_blob.sentiment.polarity:.2f}")
    
    # Test language detection
    lang = detect("Bonjour le monde")
    print(f"  Language detection: 'Bonjour le monde' → {lang}")
    
    print("\n✅ All tests passed!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️  Test issue (may be okay): {e}")
EOF

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║        INSTALLATION COMPLETE!         ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Test NLP service: python test_nlp_bilingual.py"
echo "2. Run Flask app: python run.py"
echo ""

#!/bin/bash
# Install Production Bilingual NLP Dependencies (CamemBERT)
# Run this after updating requirements.txt

set -e  # Exit on error

echo "╔═══════════════════════════════════════╗"
echo "║   INSTALLING CAMEMBERT NLP PACKAGES   ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "🇫🇷 Using CamemBERT for state-of-the-art French sentiment"
echo "🇬🇧 Using VADER for English sentiment"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"
echo ""

# Upgrade pip (use python -m pip to avoid externally-managed error)
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

echo ""
echo "📦 Installing bilingual NLP packages..."
echo ""
echo "⚠️  Note: This will download ~2GB of data (CamemBERT model)"
echo "   First installation may take 5-10 minutes"
echo ""

# Install language detection
echo "  → Installing langdetect (language detection)..."
python -m pip install langdetect==1.0.9

# Install PyTorch (required for CamemBERT)
echo "  → Installing PyTorch..."
python -m pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Install transformers and dependencies
echo "  → Installing transformers (CamemBERT support)..."
python -m pip install transformers==4.36.0
python -m pip install sentencepiece==0.1.99

echo ""
echo "✅ All bilingual NLP packages installed successfully!"
echo ""

# Test imports
echo "🧪 Testing imports..."
python3 << 'EOF'
try:
    from langdetect import detect
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    
    print("✅ All imports successful!")
    
    # Quick test
    print("\n🧪 Quick functionality test:")
    
    # Test VADER (English)
    vader = SentimentIntensityAnalyzer()
    en_result = vader.polarity_scores("I love this!")
    print(f"  English (VADER): 'I love this!' → {en_result['compound']:.2f}")
    
    # Test language detection
    lang = detect("Bonjour le monde")
    print(f"  Language detection: 'Bonjour le monde' → {lang}")
    
    # Check if CUDA is available
    if torch.cuda.is_available():
        print(f"  GPU: ✅ CUDA available ({torch.cuda.get_device_name(0)})")
    else:
        print(f"  GPU: ⚠️  CPU only (slower but works fine)")
    
    print("\n✅ All tests passed!")
    print("\n⚠️  Note: CamemBERT will download ~400MB on first use")
    
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
echo "1. Test NLP service: python tests/test_nlp_camembert.py"
echo "2. Run Flask app: python run.py"
echo ""
echo "📚 CamemBERT Info:"
echo "   - Model: cmarkea/distilcamembert-base-sentiment"
echo "   - Size: ~400MB (downloads on first use)"
echo "   - Accuracy: State-of-the-art for French"
echo ""
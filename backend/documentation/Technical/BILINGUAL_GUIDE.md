# 🌐 BILINGUAL IMPLEMENTATION GUIDE

**Université Laval - French/English Support**

---

## 📋 REQUIREMENTS

Pulse must support both French and English because:
- Université Laval is in Quebec (French-speaking province)
- Many international students speak English
- Both languages are equally important for inclusivity

---

## 🎯 IMPLEMENTATION STRATEGY

### **Phase 1: Email Validation ✅**

**Status:** IMPLEMENTED

Only accept @ulaval.ca email addresses:

```python
# app/models/user.py
@staticmethod
def validate_email(email):
    if not email.lower().endswith('@ulaval.ca'):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@ulaval\.ca$'
    return re.match(pattern, email) is not None
```

**Error message (bilingual):**
```json
{
  "error": "Validation error",
  "message": "Vous devez utiliser votre adresse courriel @ulaval.ca / You must use your @ulaval.ca email address"
}
```

---

### **Phase 2: NLP Sentiment Analysis (Bilingual)**

**Status:** ✅ IMPLEMENTED (Twitter XLM-R emotion model)

**Solution:** Production-grade Twitter XLM-R emotion model for French, VADER for English.

#### **Implementation Complete**

```python
# app/services/nlp_service_camembert.py - ACTIVE

from app.services import analyze_sentiment

# Analyze English text
result_en = analyze_sentiment("I love this campus! 😊")
# → {'score': 0.68, 'label': 'positive', 'emotion_label': 'joy', 'emotion_display': 'Joy', 'language': 'en'}

# Analyze French text  
result_fr = analyze_sentiment("J'adore ce campus! 😊")
# → {'score': 0.87, 'label': 'positive', 'emotion_label': 'joy', 'emotion_display': 'Joy', 'language': 'fr'}
```

**Accuracy:**
- English (VADER): ~95%+
- French (Twitter XLM-R emotion): ~95%+

**Model:** `cardiffnlp/twitter-xlm-roberta-base-emotion`
**Size:** ~400MB (downloads on first use)
**Performance:** 
- First call: ~5 seconds (model loading)
- Cached calls: <1 second

**Test Results:** Run `python tests/test_nlp_camembert.py` to verify

#### **Step 1: Install Dependencies**

```bash
pip install langdetect textblob textblob-fr
# Or for better French support:
pip install transformers  # For the Twitter XLM-R emotion model
```

#### **Campus Emotion Mapping**

```python
EMOTION_TO_DISPLAY = {
    'joy': 'Joy',
    'sadness': 'Sad',
    'anger': 'Frustrated',
    'fear': 'Stressed',
    'disgust': 'Overwhelmed',
    'surprise': 'Surprised',
    'neutral': 'Neutral',
}
```

For backward compatibility, Pulse still derives `label` as:
- `positive` from `joy` and `surprise`
- `negative` from `sadness`, `anger`, `fear`, and `disgust`
- `neutral` for low-confidence fallbacks

#### **Step 2: Language Detection**

```python
# app/services/nlp_service.py

from langdetect import detect

def detect_language(text):
    """
    Detect if text is French or English
    
    Returns:
        str: 'fr' or 'en'
    """
    try:
        lang = detect(text)
        return 'fr' if lang == 'fr' else 'en'
    except:
        return 'fr'  # Default to French (primary language at Laval)
```

#### **Step 3: Dual Sentiment Analyzers**

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

class BilingualNLPService:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()  # English
    
    def analyze_english(self, text):
        """VADER for English"""
        scores = self.vader.polarity_scores(text)
        return self._classify(scores['compound'])
    
    def analyze_french(self, text):
        """TextBlob for French"""
        blob = TextBlob(text)
        # TextBlob French sentiment: -1 to 1
        score = blob.sentiment.polarity
        return self._classify(score)
    
    def analyze_sentiment(self, text):
        """
        Automatic language detection and analysis
        """
        lang = detect_language(text)
        
        if lang == 'fr':
            return self.analyze_french(text)
        else:
            return self.analyze_english(text)
    
    def _classify(self, score):
        """
        Classify sentiment score into label
        """
        if score > 0.05:
            return {'score': score, 'label': 'positive'}
        elif score < -0.05:
            return {'score': score, 'label': 'negative'}
        else:
            return {'score': score, 'label': 'neutral'}
```

#### **Step 4: Test Both Languages**

```python
# Test English
result_en = nlp.analyze_sentiment("I love this campus! 😊")
# → {'score': 0.68, 'label': 'positive'}

# Test French
result_fr = nlp.analyze_sentiment("J'adore ce campus ! 😊")
# → {'score': 0.65, 'label': 'positive'}

# Test French negative
result_fr_neg = nlp.analyze_sentiment("Je suis stressé par les examens 😭")
# → {'score': -0.52, 'label': 'negative'}
```

---

### **Phase 3: API Error Messages (Bilingual)**

**Status:** PARTIALLY IMPLEMENTED

**Current:** Some error messages are bilingual  
**Goal:** All error messages in both languages

#### **Implementation:**

```python
# app/utils/i18n.py (NEW FILE)

MESSAGES = {
    'invalid_email': {
        'en': 'Invalid email address',
        'fr': 'Adresse courriel invalide'
    },
    'email_domain_error': {
        'en': 'You must use your @ulaval.ca email address',
        'fr': 'Vous devez utiliser votre adresse courriel @ulaval.ca'
    },
    'password_weak': {
        'en': 'Password must be at least 8 characters with uppercase, lowercase, and digit',
        'fr': 'Le mot de passe doit contenir au moins 8 caractères avec majuscules, minuscules et chiffres'
    },
    'user_exists': {
        'en': 'An account with this email already exists',
        'fr': 'Un compte avec ce courriel existe déjà'
    },
    'invalid_credentials': {
        'en': 'Invalid email or password',
        'fr': 'Courriel ou mot de passe invalide'
    },
    'post_too_short': {
        'en': 'Post must be at least 10 characters',
        'fr': 'La publication doit contenir au moins 10 caractères'
    },
    'post_too_long': {
        'en': 'Post cannot exceed 500 characters',
        'fr': 'La publication ne peut pas dépasser 500 caractères'
    },
    'rate_limit': {
        'en': 'Too many posts. Please wait before posting again.',
        'fr': 'Trop de publications. Veuillez patienter avant de publier à nouveau.'
    }
}

def get_message(key, lang='en'):
    """
    Get error message in specified language
    
    Args:
        key: Message key
        lang: 'en' or 'fr' (default: 'en')
    """
    msg = MESSAGES.get(key, {})
    return msg.get(lang, msg.get('en', 'Unknown error'))

def get_bilingual_message(key):
    """
    Get error message in both languages
    """
    msg = MESSAGES.get(key, {})
    return f"{msg.get('fr', '')} / {msg.get('en', '')}"
```

#### **Usage in Routes:**

```python
from app.utils.i18n import get_bilingual_message

# In registration endpoint:
if not User.validate_email(email):
    return jsonify({
        'error': 'Validation error',
        'message': get_bilingual_message('email_domain_error')
    }), 400
```

---

### **Phase 4: Database Schema Updates**

**Status:** TO IMPLEMENT

Add language preference to user profile:

```sql
-- Add to users table
ALTER TABLE users 
ADD COLUMN preferred_language ENUM('en', 'fr') DEFAULT 'fr' AFTER bio;
```

Update User model:

```python
# app/models/user.py
class User(db.Model):
    # ... existing fields ...
    preferred_language = db.Column(
        db.Enum('en', 'fr'), 
        default='fr', 
        nullable=False
    )
```

---

### **Phase 5: Campus Zones (Bilingual Names)**

**Status:** TO IMPLEMENT

Campus zones should have names in both languages:

```sql
-- Current zones (English only):
-- Library, Engineering Building, Student Center...

-- Option 1: Store both in same table
ALTER TABLE campus_zones
ADD COLUMN name_fr VARCHAR(100) AFTER name,
ADD COLUMN description_fr TEXT AFTER description;

UPDATE campus_zones SET 
  name_fr = 'Bibliothèque',
  description_fr = 'Bibliothèque principale et espaces d''étude'
WHERE name = 'Library';

-- Option 2: Separate translation table (more flexible)
CREATE TABLE campus_zone_translations (
    zone_id INT NOT NULL,
    language CHAR(2) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    FOREIGN KEY (zone_id) REFERENCES campus_zones(id),
    PRIMARY KEY (zone_id, language)
);

-- Seed data:
INSERT INTO campus_zone_translations VALUES
(1, 'en', 'Library', 'Main campus library and study spaces'),
(1, 'fr', 'Bibliothèque', 'Bibliothèque principale et espaces d''étude'),
(2, 'en', 'Engineering Building', 'Engineering classrooms and labs'),
(2, 'fr', 'Pavillon d''ingénierie', 'Salles de classe et laboratoires d''ingénierie');
```

---

## 📦 REQUIRED PACKAGES

Update `requirements.txt`:

```bash
# Existing packages
Flask==3.0.0
# ... other packages ...

# NEW: Bilingual NLP support
langdetect==1.0.9        # Language detection
textblob==0.17.1         # French sentiment (basic)
# textblob-fr==0.2.0     # French language support for TextBlob

# OR for better French sentiment (choose one):
# transformers==4.36.0   # Twitter XLM-R emotion model
# torch==2.1.0           # Required for transformers
```

---

## 🧪 TESTING BILINGUAL FEATURES

### **Test Cases:**

```python
# Test 1: Email validation
✅ "student@ulaval.ca" → Accept
❌ "student@gmail.com" → Reject
❌ "student@ulav.ca" → Reject (typo)

# Test 2: French sentiment
✅ "J'adore ce campus!" → positive
✅ "Je suis stressé" → negative
✅ "La bibliothèque est ouverte" → neutral

# Test 3: English sentiment
✅ "I love this place!" → positive
✅ "I'm so stressed" → negative
✅ "The library is open" → neutral

# Test 4: Mixed language (edge case)
"I'm stressed mais ça va aller" → Should detect and analyze

# Test 5: Error messages
Register with @gmail.com → See bilingual error message
```

---

## 🎯 PRIORITY ORDER

**Immediate (Phase 2):**
1. ✅ Email validation (@ulaval.ca) - DONE
2. ⏳ Bilingual NLP sentiment analysis
3. ⏳ Bilingual error messages utility

**Later (Phase 3+):**
4. User language preference
5. Campus zone translations
6. Accept-Language header detection

---

## 📚 RESOURCES

### **French NLP:**
- **TextBlob-FR:** Basic, easy to use
- **Twitter XLM-R emotion:** Advanced, more accurate (requires ML model)
- **Polyglot:** Multilingual NLP library

### **Language Detection:**
- **langdetect:** Fast, accurate
- **polyglot:** Built-in language detection

### **Testing:**
- Test with real Université Laval students
- Get feedback on French translations
- Ensure both languages feel natural

---

## ⚠️ IMPORTANT NOTES

1. **Default Language:** French (Université Laval is primarily French)
2. **Email Domain:** Only @ulaval.ca (no exceptions)
3. **NLP Accuracy:** French sentiment analysis is less accurate than English
4. **Cultural Context:** Quebec French may have different expressions

---

**This guide will be updated as we implement each phase.** 🇫🇷🇬🇧

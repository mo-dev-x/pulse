# 🚀 QUICKSTART GUIDE - PULSE BACKEND

**Complete setup guide for Université Laval's Pulse platform**

---

## 📋 PREREQUISITES

Before you start, make sure you have:

- **Python 3.12+** installed
- **MySQL 8.0+** installed and running
- **Git** installed
- **~3GB free disk space** (for CamemBERT model)

---

## 🎯 STEP 1: CLONE REPOSITORY

```bash
# Clone the repository
git clone https://github.com/mo-dev-x/pulse-backend.git
cd pulse-backend

# Navigate to backend folder
cd backend
```

---

## 🐍 STEP 2: SET UP PYTHON ENVIRONMENT

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify activation
which python  # Should show: /path/to/pulse-backend/backend/venv/bin/python
```

---

## 📦 STEP 3: INSTALL DEPENDENCIES

### 🐧 **Linux users — install system build tools (REQUIRED)**

The French emotion model depends on SentencePiece, which requires C++ build tools.

**Run once before installing Python packages:**

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config libprotobuf-dev protobuf-compiler
```

---

### 🔥 **Install PyTorch (CPU version)**

This project runs in CPU environments (laptops / VMs).  
Install the lightweight CPU version of PyTorch first:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Why separate?**  
PyTorch is installed separately to avoid downloading ~4GB of unnecessary CUDA libraries.

---

### **Option A: Standard Installation (Recommended)**

```bash
# Install remaining dependencies after PyTorch
pip install -r requirements.txt
```

**This installs:**
- Flask & extensions
- MySQL driver (PyMySQL)
- Security (bcrypt, JWT)
- NLP libraries (VADER, French emotion model, language detection)

**Note:** French emotion model (~250MB) downloads on first use, not during installation.


---

## 🔐 STEP 4: CONFIGURE ENVIRONMENT

### **Generate Secret Keys**

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate JWT_SECRET_KEY  
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

Copy the outputs - you'll need them next!

---

### **Create .env File**

```bash
# Copy template
cp .env.template .env

# Edit with your favorite editor
nano .env  # or: vim .env, code .env, etc.
```

**Fill in these values:**

```bash
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
DEBUG=True

# Security Keys (PASTE YOUR GENERATED KEYS HERE!)
SECRET_KEY=your_generated_secret_key_here
JWT_SECRET_KEY=your_generated_jwt_secret_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=pulse_db
DB_USER=root                    # Your MySQL username
DB_PASSWORD=your_mysql_password # Your MySQL password

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES=86400  # 24 hours

# File Upload Configuration
MAX_CONTENT_LENGTH=5242880      # 5MB
UPLOAD_FOLDER=uploads/

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
```

**Save and close** (Ctrl+O, Enter, Ctrl+X in nano)

---

## 🗄️ STEP 5: SET UP DATABASE

### **Option A: Interactive Setup (Recommended)**

```bash
python setup_db.py
```

**Follow the prompts:**
```
╔═══════════════════════════════════════╗
║   PULSE DATABASE SETUP WIZARD         ║
╚═══════════════════════════════════════╝

MySQL Username [root]: root
MySQL Password: ********

✅ Successfully connected to MySQL
✅ Database 'pulse_db' created
✅ Schema executed successfully
✅ Setup completed successfully!
```

---

### **Option B: Manual Setup**

```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE pulse_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Grant privileges (if needed)
GRANT ALL PRIVILEGES ON pulse_db.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;

exit;

# Execute schema
mysql -u root -p pulse_db < schema.sql
```

---

### **Verify Database**

```bash
mysql -u root -p pulse_db
```

```sql
-- Check tables
SHOW TABLES;
-- Should show: users, posts, followers, campus_zones, etc.

-- Check campus zones
SELECT COUNT(*) FROM campus_zones;
-- Should show: 10

-- Check users table structure
DESCRIBE users;
-- Should include: preferred_language ENUM('en','fr')

exit;
```

---

## 🧪 STEP 6: TEST THE SETUP

### **Test 1: Start Flask**

```bash
# Make sure venv is activated
source venv/bin/activate

# Start Flask
python run.py
```

**Expected output:**
```
╔═══════════════════════════════════════╗
║     PULSE BACKEND - STARTING UP       ║
╚═══════════════════════════════════════╝

Environment: development
Host: 127.0.0.1
Port: 5000
Debug: True

API will be available at: http://127.0.0.1:5000

 * Running on http://127.0.0.1:5000
```

**✅ Success!** Keep this terminal open.

---

### **Test 2: Authentication API (New Terminal)**

```bash
cd pulse-backend/backend
source venv/bin/activate

# Run auth tests
python tests/test_auth.py
```

**Expected:**
```
************************************************************
               PULSE AUTHENTICATION API TESTS               
************************************************************

✅ User registered successfully!
✅ Login successful!
✅ Profile retrieved successfully!
...

🎉 ALL TESTS PASSED! 🎉
```

---

### **Test 3: Bilingual NLP (CamemBERT)**

```bash
# Run NLP tests
python tests/test_nlp_camembert.py
```

**Expected:**
```
**********************************************************************
                    CAMEMBERT BILINGUAL NLP TESTS                    
**********************************************************************

🇫🇷 French: CamemBERT (state-of-the-art)
🇬🇧 English: VADER (social media optimized)

⚠️  First test will download model (~400MB)

✅ [EN] "I absolutely love this campus! 😊"
   Expected: positive  | Got: positive  | Score: +0.90 | Confidence: 0.92

✅ [FR] "J'adore ce campus! 😊"
   Expected: positive  | Got: positive  | Score: +0.87 | Confidence: 0.95

🎉 ALL TESTS PASSED! 🎉

✨ French emotion model excels at campus wellness posts!
```

**Note:** First run downloads CamemBERT (~400MB). Subsequent runs are instant.

---

## 🎯 STEP 7: MANUAL API TESTING

### **Test Registration**

```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@ulaval.ca",
    "password": "TestPass123!",
    "username": "lavaletudiant",
    "display_name": "Étudiant Laval"
  }'
```

**Expected response:**
```json
{
  "message": "Utilisateur créé avec succès / User created successfully",
  "user": {
    "id": 1,
    "username": "lavaletudiant",
    "email": "student@ulaval.ca",
    "pseudonym": "anonymous",
    "preferred_language": "fr"
  },
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**✅ Copy the token!** You'll need it for authenticated requests.

---

### **Test Login**

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@ulaval.ca",
    "password": "TestPass123!"
  }'
```

---

### **Test Profile (Authenticated)**

```bash
# Replace YOUR_TOKEN with actual token from registration
curl http://127.0.0.1:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔄 DAILY WORKFLOW

### **Starting Work**

```bash
cd pulse-backend/backend

# Activate venv
source venv/bin/activate

# Start MySQL (if not running)
sudo systemctl start mysql  # Linux
# brew services start mysql  # macOS

# Start Flask
python run.py
```

---

### **Stopping Work**

```bash
# Stop Flask: Ctrl+C

# Deactivate venv
deactivate

# Stop MySQL (optional)
sudo systemctl stop mysql
```

---

## 🐛 TROUBLESHOOTING

### **"No module named 'flask'"**

```bash
# Check if venv is activated
which python
# Should show: /path/to/backend/venv/bin/python

# If not, activate it
source venv/bin/activate

# Reinstall if needed
pip install -r requirements.txt
```

---

### **"Can't connect to MySQL"**

```bash
# Check MySQL is running
sudo systemctl status mysql

# Start MySQL
sudo systemctl start mysql

# Test connection
mysql -u root -p
# Enter your password
```

---

### **"Email must be @ulaval.ca"**

This is intentional! Pulse is for Université Laval students only.

```bash
# ✅ Valid:
student@ulaval.ca

# ❌ Invalid:
student@gmail.com
student@outlook.com
```

---

### **CamemBERT download fails**

```bash
# Check internet connection
ping google.com

# Try manual download
python3 << 'EOF'
from transformers import AutoTokenizer, AutoModelForSequenceClassification
model_name = "cmarkea/distilcamembert-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
print("✅ Downloaded successfully!")
EOF
```

---

### **Tests fail with "Connection refused"**

Make sure Flask is running in another terminal:

```bash
# Terminal 1:
python run.py

# Terminal 2:
python tests/test_auth.py
```

---

## 📂 PROJECT STRUCTURE

```
pulse-backend/
├── backend/                    # All code here
│   ├── app/
│   │   ├── models/             # SQLAlchemy models
│   │   ├── routes/             # API endpoints
│   │   ├── services/           # Business logic (NLP)
│   │   ├── utils/              # i18n, helpers
│   │   └── __init__.py
│   ├── tests/                  # Test files
│   │   ├── test_auth.py
│   │   └── test_nlp_camembert.py
│   ├── venv/                   # Virtual environment
│   ├── .env                    # Your secrets (NOT in git)
│   ├── .env.template           # Template
│   ├── requirements.txt        # Python dependencies
│   ├── run.py                  # Entry point
│   ├── setup_db.py             # Database setup
│   └── schema.sql              # Database schema
│
├── documentation/              # All docs
│   ├── QUICKSTART.md          # This file
│   ├── PROJECT_TRACKER.md
│   ├── ARCHITECTURE_DECISIONS.md
│   └── ...
│
├── README.md                   # Project overview
└── .gitignore                  # Git ignore rules
```

---

## ✅ COMPLETE CHECKLIST

Before moving on, verify:

- [ ] Python 3.12+ installed
- [ ] MySQL 8.0+ running
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip list`)
- [ ] `.env` file configured with secret keys
- [ ] Database `pulse_db` created
- [ ] Schema executed (10 campus zones seeded)
- [ ] Flask starts without errors
- [ ] Auth tests pass (7/7)
- [ ] NLP tests pass
- [ ] Can register with @ulaval.ca email
- [ ] CamemBERT model downloaded (~400MB)

---

## 🎓 LEARNING RESOURCES

### **Key Technologies:**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [JWT Authentication](https://flask-jwt-extended.readthedocs.io/)
- [CamemBERT Paper](https://arxiv.org/abs/1911.03894)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)

### **Université Laval Resources:**
- Campus counseling: Available if sentiment trends show concern
- French language support: CamemBERT understands Quebec expressions

---

## 🚀 NEXT STEPS

Once setup is complete:

1. **Review Documentation**
   - Read `../documentation/PROJECT_TRACKER.md` for progress
   - Read `../documentation/ARCHITECTURE_DECISIONS.md` for design choices

2. **Start Development**
   - Create Post model
   - Build create post endpoint
   - Integrate bilingual NLP

3. **Test Everything**
   - Write tests as you go
   - Aim for >80% test coverage

---

## 💡 TIPS

- **Git Workflow:** Commit often, push daily
- **Testing:** Run tests before every commit
- **Documentation:** Update PROJECT_TRACKER.md after each task
- **French Support:** CamemBERT is production-grade for Quebec French
- **Performance:** First CamemBERT call is slow (~5s), then cached

---

**✨ You're ready to build Pulse! Good luck!** 🫀
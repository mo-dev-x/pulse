# 🚀 PULSE BACKEND - TEAMMATE SETUP

**For my Frontend Developers (& Future New Team Members)**

This guide helps you set up the Pulse backend on your local machine.

---

## ✅ PREREQUISITES

- Python 3.12+
- MySQL 8.0+
- Git

---

## 📥 STEP 1: CLONE REPOSITORY

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/pulse-backend.git
cd pulse-backend
```

---

## 🐍 STEP 2: SET UP PYTHON ENVIRONMENT

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔐 STEP 3: CONFIGURE ENVIRONMENT

```bash
# Copy environment template
cp .env.template .env

# Edit .env file
nano .env  # or use your preferred editor
```

**Fill in these values:**

```bash
# Generate secret keys:
# Run these commands and paste the output into .env:
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"

# Database credentials:
DB_HOST=localhost
DB_PORT=3306
DB_NAME=pulse_db
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
```

**Save and close.**

---

## 🗄️ STEP 4: SET UP DATABASE

```bash
# Make sure MySQL is running
sudo systemctl start mysql  # Linux
# or: brew services start mysql  # macOS

# Run setup script
python setup_db.py
```

**Follow the prompts:**
- Enter your MySQL username (usually `root`)
- Enter your MySQL password
- Script will create database and tables

---

## 🧪 STEP 5: TEST THE SETUP

```bash
# Terminal 1: Start Flask
python run.py

# Terminal 2: Run tests
python test_auth.py
```

**Expected result:** 7/7 tests passing ✅

---

## 📡 STEP 6: TEST API MANUALLY

```bash
# Register a user
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ulaval.ca",
    "password": "TestPass123!",
    "username": "testuser"
  }'
```

You should get a JSON response with a token!

---

## 🔄 KEEPING UP TO DATE

```bash
# Pull latest changes from main branch
git pull origin main

# If requirements.txt changed, update dependencies
pip install -r requirements.txt

# If schema.sql changed, update database
python setup_db.py
```

---

## 🐛 TROUBLESHOOTING

### "No module named 'flask'"
```bash
# Make sure venv is activated
source venv/bin/activate
which python  # Should show: /path/to/pulse-backend/venv/bin/python
```

### "Can't connect to MySQL"
```bash
# Check MySQL is running
sudo systemctl status mysql

# Start if stopped
sudo systemctl start mysql
```

### "Table already exists"
```bash
# Drop and recreate database
mysql -u root -p
mysql> DROP DATABASE pulse_db;
mysql> exit;

# Run setup again
python setup_db.py
```

---

## 📚 DOCUMENTATION

- **README.md** - Project overview
- **QUICKSTART.md** - Detailed setup guide
- **TESTING_GUIDE.md** - How to test endpoints
- **PROJECT_TRACKER.md** - Development progress
- **ARCHITECTURE_DECISIONS.md** - Technical decisions

---

## 🤝 CONTRIBUTING

Before making changes:

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

3. **Test everything:**
   ```bash
   python test_auth.py  # All tests must pass
   ```

4. **Commit with clear message:**
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```

5. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request on GitHub**

---

## 📞 NEED HELP?

- Check documentation in repo
- Ask in team Discord (well now bc we are 2 insta will do :)
- Contact backend lead: TYRANT CP

---

**Welcome to the team! 🎉**

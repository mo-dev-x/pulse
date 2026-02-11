# 🚀 PULSE BACKEND - QUICK START GUIDE

**Last Updated:** 2026-02-10

---

## ✅ WHAT YOU'VE DONE SO FAR

- [x] Created virtual environment
- [x] Installed Python dependencies
- [x] Created project structure
- [x] Generated configuration files

---

## 📋 NEXT STEPS: DATABASE SETUP

### Step 1: Copy Files to Your Project

All the files you need are in the `/outputs` folder. Copy them to your `pulse-backend/` directory:

```bash
# Navigate to your project folder
cd ~/pulse-backend

# Copy the app folder, configuration files, and scripts
# (You should already have these from creating the structure)
```

**Files you should now have:**
```
pulse-backend/
├── venv/                      # Your virtual environment
├── app/
│   ├── __init__.py           # Flask app factory ✅
│   ├── config.py             # Configuration ✅
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── middleware/
│   └── utils/
├── run.py                     # Entry point ✅
├── setup_db.py                # Database setup script ✅
├── schema.sql                 # Database schema ✅
├── .env.template              # Environment variables template ✅
├── .gitignore                 # Git ignore rules ✅
└── requirements.txt
```

---

### Step 2: Generate Secret Keys

Your app needs secure secret keys. Generate them:

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate JWT_SECRET_KEY  
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

**Copy the output** - you'll need it for the next step!

Example output:
```
SECRET_KEY=a1b2c3d4e5f6...
JWT_SECRET_KEY=x9y8z7w6v5u4...
```

---

### Step 3: Create .env File

```bash
# Copy the template
cp .env.template .env

# Edit it with your favorite editor
nano .env   # or: vim .env, code .env, etc.
```

**Fill in these values:**

```bash
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
DEBUG=True

# Security Keys (PASTE YOUR GENERATED KEYS HERE!)
SECRET_KEY=your-generated-secret-key-from-step-2
JWT_SECRET_KEY=your-generated-jwt-secret-from-step-2

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=pulse_db
DB_USER=your_mysql_username      # Usually 'root' for local development
DB_PASSWORD=your_mysql_password  # Your MySQL password

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES=86400  # 24 hours

# File Upload Configuration
MAX_CONTENT_LENGTH=5242880  # 5MB
UPLOAD_FOLDER=uploads/

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
```

**Save and close the file.**

---

### Step 4: Run Database Setup

The `setup_db.py` script will:
1. Test MySQL connection
2. Create `pulse_db` database
3. Create all tables
4. Seed campus zones
5. Verify everything worked

```bash
# Make sure venv is activated
source venv/bin/activate

# Run setup script
python setup_db.py
```

**Follow the prompts:**
- Enter your MySQL username (usually `root`)
- Enter your MySQL password
- Script will create database and run schema

**Expected output:**
```
╔═══════════════════════════════════════╗
║   PULSE DATABASE SETUP WIZARD         ║
╚═══════════════════════════════════════╝

==================================================
  DATABASE CREDENTIALS
==================================================

MySQL Username [root]: root
MySQL Password: ********

==================================================
  TESTING CONNECTION
==================================================

✅ Successfully connected to MySQL at localhost:3306

==================================================
  CREATING DATABASE
==================================================

✅ Database 'pulse_db' created (or already exists)

==================================================
  EXECUTING SCHEMA
==================================================

✅ Schema executed successfully (XX statements)

==================================================
  VERIFYING SETUP
==================================================

Tables created:
  ✅ users
  ✅ followers
  ✅ campus_zones
  ✅ posts
  ✅ media
  ✅ reactions
  ✅ daily_aggregates
  ✅ weekly_aggregates
  ✅ events

Campus zones seeded: 10 zones
Sample zones:
  - Library
  - Engineering Building
  - Student Center
  - Residence Hall A
  - Gym & Recreation Center

✅ Setup completed successfully!
```

---

### Step 5: Test Flask App

```bash
# Make sure venv is activated
source venv/bin/activate

# Start the server
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

Press CTRL+C to stop the server

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

**Test it:**

Open another terminal and run:
```bash
curl http://127.0.0.1:5000/
```

You should get a 404 response (this is expected - we haven't created any routes yet!):
```json
{"error": "Not found", "message": "The requested resource does not exist"}
```

**This is good!** It means Flask is running correctly.

---

## 🎯 WHAT'S NEXT?

Now that your foundation is set up, we'll build:

**Phase 1, Week 1 (Days 3-4): User Authentication**
- User model (SQLAlchemy ORM)
- Password hashing with bcrypt
- JWT token generation
- Register endpoint (`POST /api/auth/register`)
- Login endpoint (`POST /api/auth/login`)

Tell me when your database setup is complete and working, and we'll start building authentication!

---

## 🐛 TROUBLESHOOTING

### "Can't connect to MySQL server"

**Check if MySQL is running:**
```bash
sudo systemctl status mysql
# or
sudo service mysql status
```

**Start MySQL if stopped:**
```bash
sudo systemctl start mysql
# or
sudo service mysql start
```

---

### "Access denied for user 'root'@'localhost'"

**Reset MySQL root password:**
```bash
sudo mysql
mysql> ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_new_password';
mysql> FLUSH PRIVILEGES;
mysql> exit;
```

Then update your `.env` file with the new password.

---

### "ImportError: No module named 'flask'"

**Make sure virtual environment is activated:**
```bash
# You should see (venv) in your terminal prompt
source venv/bin/activate

# Verify Python is from venv
which python
# Should output: /path/to/pulse-backend/venv/bin/python
```

---

### "Table already exists" errors

**This is usually fine!** If you run `setup_db.py` multiple times, some tables might already exist. As long as the verification step passes, you're good.

If you want a completely fresh start:
```bash
# Connect to MySQL
mysql -u root -p

# Drop and recreate database
mysql> DROP DATABASE pulse_db;
mysql> CREATE DATABASE pulse_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql> exit;

# Run setup again
python setup_db.py
```

---

## 📚 DOCUMENTATION REFERENCE

- **PROJECT_TRACKER.md** - Current progress and task list
- **ARCHITECTURE_DECISIONS.md** - Technical decisions and code patterns
- **This guide (QUICKSTART.md)** - Setup instructions

---

## ✅ VERIFICATION CHECKLIST

Before moving to Phase 2, verify:

- [ ] Virtual environment is activated
- [ ] All dependencies installed (`pip list` shows flask, pymysql, etc.)
- [ ] `.env` file exists with your secret keys
- [ ] MySQL is running
- [ ] `pulse_db` database exists
- [ ] All 9 tables created (check with `setup_db.py` output)
- [ ] 10 campus zones seeded
- [ ] Flask app starts without errors (`python run.py`)
- [ ] Can curl the API (even if it returns 404)

**Once all checked, you're ready for authentication!** 🚀

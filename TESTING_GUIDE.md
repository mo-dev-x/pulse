# 🧪 TESTING GUIDE: AUTHENTICATION

**Last Updated:** 2026-02-10

---

## ✅ WHAT WE JUST BUILT

You now have a complete authentication system with:

### **User Model** (`app/models/user.py`)
- Password hashing with bcrypt
- Email & username validation
- Pseudonym management (90-day cooldown)
- Helper methods for authentication

### **Authentication Routes** (`app/routes/auth.py`)
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Get JWT token
- `GET /api/auth/me` - Get current user profile
- `PATCH /api/auth/update-profile` - Update display name, bio
- `PATCH /api/auth/update-pseudonym` - Change anonymous pseudonym
- `POST /api/auth/logout` - Logout (client-side)

---

## 🚀 HOW TO TEST

### **Method 1: Automated Test Script (Recommended)**

I've created a comprehensive test script that verifies all endpoints.

```bash
# Terminal 1: Start Flask app
cd ~/pulse-backend
source venv/bin/activate
python run.py

# Terminal 2: Run tests
cd ~/pulse-backend
source venv/bin/activate
python test_auth.py
```

**Expected Output:**
```
============================================================
        PULSE AUTHENTICATION API TESTS
============================================================

ℹ️  Make sure Flask app is running at http://127.0.0.1:5000

============================================================
          TEST 1: USER REGISTRATION
============================================================

ℹ️  Registering user: testuser_20260210143022
✅ User registered successfully!
  User ID: 1
  Username: testuser_20260210143022
  Email: testuser_20260210143022@university.edu
  Token: eyJhbGciOiJIUzI1NiI...

[... more tests ...]

============================================================
          TEST SUMMARY
============================================================
Total Tests: 7
Passed: 7
Failed: 0

🎉 ALL TESTS PASSED! 🎉
```

---

### **Method 2: Manual Testing with curl**

If you prefer to test manually:

#### **1. Register a New User**

```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@university.edu",
    "password": "SecurePass123!",
    "username": "johndoe",
    "display_name": "John Doe"
  }'
```

**Expected Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "display_name": "John Doe",
    "email": "john@university.edu",
    "pseudonym": "anonymous",
    "can_change_pseudonym": true
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Copy the token!** You'll need it for authenticated requests.

---

#### **2. Login**

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@university.edu",
    "password": "SecurePass123!"
  }'
```

**Expected Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": { ... },
  "token": "eyJhbGciOiJIUzI1NiI..."
}
```

---

#### **3. Get Current User Profile**

```bash
# Replace YOUR_TOKEN with the token from login/register
curl http://127.0.0.1:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "display_name": "John Doe",
    "bio": null,
    "email": "john@university.edu",
    "pseudonym": "anonymous",
    "can_change_pseudonym": true
  }
}
```

---

#### **4. Update Profile**

```bash
curl -X PATCH http://127.0.0.1:5000/api/auth/update-profile \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Johnny Doe",
    "bio": "CS major | Coffee enthusiast"
  }'
```

**Expected Response (200 OK):**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "display_name": "Johnny Doe",
    "bio": "CS major | Coffee enthusiast",
    ...
  }
}
```

---

#### **5. Update Pseudonym**

```bash
curl -X PATCH http://127.0.0.1:5000/api/auth/update-pseudonym \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pseudonym": "stressed_student"
  }'
```

**Expected Response (200 OK):**
```json
{
  "message": "Pseudonym updated successfully",
  "pseudonym": "stressed_student",
  "can_change_again_at": "2026-02-10T14:30:00"
}
```

---

### **Method 3: Postman / Insomnia**

If you use API testing tools:

1. **Import Collection:**
   - Base URL: `http://127.0.0.1:5000`
   - Create requests for each endpoint above

2. **Set Environment Variables:**
   - `base_url`: `http://127.0.0.1:5000`
   - `token`: (save from login/register response)

3. **Test Workflow:**
   - Register → Save token
   - Login → Verify token works
   - Get profile → Verify data
   - Update profile → Check changes
   - Update pseudonym → Verify cooldown

---

## 🧪 TEST CASES TO VERIFY

### ✅ **Happy Path (Should Succeed)**

- [ ] Register with valid email, password, username
- [ ] Login with correct credentials
- [ ] Get current user profile with valid token
- [ ] Update profile with valid data
- [ ] Update pseudonym for the first time

---

### ❌ **Error Cases (Should Fail Gracefully)**

- [ ] Register with duplicate email → 400 "User already exists"
- [ ] Register with duplicate username → 400 "Username already taken"
- [ ] Register with weak password → 400 "Password requirements not met"
- [ ] Register with invalid email → 400 "Invalid email format"
- [ ] Register with short username (< 3 chars) → 400 "Username must be 3-50 characters"
- [ ] Login with wrong password → 401 "Invalid email or password"
- [ ] Login with non-existent email → 401 "Invalid email or password"
- [ ] Get profile without token → 401 "Missing authorization header"
- [ ] Get profile with invalid token → 422 "Invalid token"
- [ ] Update pseudonym twice in 90 days → 400 "Can change pseudonym in X days"
- [ ] Update pseudonym with reserved name → 400 "This pseudonym is reserved"

---

## 🔍 DATABASE VERIFICATION

After testing, verify data in MySQL:

```bash
mysql -u root -p pulse_db
```

```sql
-- Check users table
SELECT id, username, email, pseudonym, created_at FROM users;

-- Verify password is hashed (not plaintext!)
SELECT username, password_hash FROM users LIMIT 1;
-- Should see: bcrypt hash starting with $2b$

-- Check pseudonym change timestamps
SELECT username, pseudonym, pseudonym_last_changed FROM users;
```

---

## 🐛 COMMON ISSUES & FIXES

### Issue: "Could not import 'app'"

**Fix:** Make sure you're in the project root directory with venv activated:
```bash
cd ~/pulse-backend
source venv/bin/activate
python run.py
```

---

### Issue: "No module named 'bcrypt'"

**Fix:** Install missing dependency:
```bash
pip install bcrypt
```

---

### Issue: "Table 'pulse_db.users' doesn't exist"

**Fix:** Run database setup again:
```bash
python setup_db.py
```

---

### Issue: "401 Unauthorized" on protected routes

**Fix:** Check your token:
```bash
# Verify token is in Authorization header
curl http://127.0.0.1:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACTUAL_TOKEN_HERE"

# NOT: "Token YOUR_TOKEN" (wrong format)
# NOT: No header at all
```

---

### Issue: Token expires

**Default:** Tokens expire after 24 hours

**Fix:** Just login again to get a new token:
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@university.edu", "password": "SecurePass123!"}'
```

---

## 🔐 SECURITY VERIFICATION CHECKLIST

After testing, verify these security measures are working:

- [ ] **Passwords are hashed**
  - Check database: password_hash should be ~60 chars of gibberish
  - Should start with `$2b$` (bcrypt identifier)

- [ ] **Invalid credentials are rejected**
  - Wrong password returns 401
  - Non-existent email returns 401
  - No information leakage (don't say "email doesn't exist")

- [ ] **Weak passwords are rejected**
  - < 8 characters rejected
  - No uppercase rejected
  - No digit rejected

- [ ] **Protected routes require authentication**
  - GET /api/auth/me without token → 401
  - Update profile without token → 401

- [ ] **JWT tokens work correctly**
  - Token contains user_id
  - Token can be decoded to get identity
  - Expired tokens are rejected (after 24 hours)

---

## 📊 WHAT'S NEXT?

Once authentication is tested and working, we'll build:

**Phase 1 Completion:**
- [ ] Campus zones model
- [ ] Post model (with anonymous flag)
- [ ] NLP sentiment service
- [ ] POST /api/posts endpoint

Tell me when your tests pass and we'll continue! 🚀

---

## 📝 NOTES FOR LEARNING

### **Why bcrypt for password hashing?**

```python
# BAD (NEVER DO THIS):
user.password = password  # Plaintext stored

# GOOD (WHAT WE DO):
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode(), salt)
user.password_hash = hashed.decode()
```

**Benefits:**
- Salted (each password has unique hash)
- Slow (prevents brute force)
- Industry standard
- Future-proof (can increase cost factor)

---

### **Why JWT tokens?**

**Traditional Sessions:**
- Server stores session ID in database
- Client sends session cookie
- Server looks up session on every request
- Doesn't scale well

**JWT Tokens:**
- Server creates signed token with user_id
- Client stores token (localStorage, cookie)
- Client sends token in Authorization header
- Server verifies signature (no database lookup needed)
- Stateless and scalable

**Structure:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.  ← Header
eyJpZGVudGl0eSI6MX0.                   ← Payload (user_id: 1)
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV      ← Signature
```

Decode at: https://jwt.io (safe, just don't paste real tokens!)

---

**Happy Testing!** 🎯

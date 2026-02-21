# Plan: Add Login System to sci.platformai.org

## Goal

Add authentication to sci.platformai.org using the same SSO + local login method as CompareGPT-AIScientist and aiXiv (pwm_aixiv).

---

## Current State

- **sci.platformai.org** is a static HTML/CSS site served by Nginx
- No backend, no authentication, no database
- The CompareGPT-AIScientist and aiXiv platforms both use:
  - SSO via CompareGPT (`comparegpt.io/sso-redirect` → `auth.comparegpt.io/sso/validate`)
  - Local username/password registration and login
  - JWT tokens (HS256, 7-day expiry) stored in httponly cookies
  - SQLite database for user storage
  - FastAPI backend

---

## Architecture

```
Browser
  │
  ├── GET /                    → Nginx serves static index.html
  ├── GET /style.css           → Nginx serves static CSS
  ├── GET /login               → FastAPI renders login.html template
  ├── GET /sso/callback        → FastAPI handles SSO token exchange
  ├── POST /api/auth/login     → FastAPI local login
  ├── POST /api/auth/register  → FastAPI local registration
  ├── GET /api/auth/me         → FastAPI returns current user info
  └── GET /api/auth/logout     → FastAPI clears session cookie
```

---

## Implementation Steps

### Step 1: Create Backend Structure

Create the following files under `/home/spiritai/science/targeting/backend/`:

```
backend/
├── app.py              # FastAPI application with all routes
├── auth.py             # JWT creation, verification, SSO exchange
├── database.py         # SQLite database setup and user operations
└── requirements.txt    # Python dependencies
```

### Step 2: Implement `auth.py`

Reuse the same pattern from `pwm_aixiv/backend/auth.py`:

- **JWT Config**: `HS256`, 7-day expiry, secret key from env var
- **`create_jwt(user_id, user_name, role)`** → encode JWT payload
- **`verify_jwt(token)`** → decode and validate JWT
- **`_extract_jwt_from_request(request)`** → check cookie `sci_token` first, then `Authorization: Bearer` header
- **`exchange_sso_token(sso_token)`** → POST to `https://auth.comparegpt.io/sso/validate` with Bearer token, parse response to extract `user_id`, `user_name`, `api_key`, `credit`, `token`, `role`
- **`get_current_user(request)`** → FastAPI dependency (required auth, raises 401)
- **`get_optional_user(request)`** → FastAPI dependency (optional auth, returns None)

SSO URLs:
```python
SSO_REDIRECT_URL = "https://comparegpt.io/sso-redirect"
SSO_VALIDATE_URL = "https://auth.comparegpt.io/sso/validate"
SSO_CALLBACK_URL = "https://sci.platformai.org/sso/callback"
```

### Step 3: Implement `database.py`

SQLite database at `backend/data/sci.db`:

```sql
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT UNIQUE NOT NULL,
    user_name   TEXT NOT NULL DEFAULT '',
    role        TEXT DEFAULT 'user',
    credit      REAL DEFAULT 0,
    token       INTEGER DEFAULT 0,
    sso_token   TEXT DEFAULT '',
    api_key     TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
```

Functions:
- `init_db()` — create tables if not exist
- `get_db()` → connection
- `upsert_user(user_info, sso_token)` — insert or update user record
- `get_user(user_id)` — fetch user by ID

### Step 4: Implement `app.py`

FastAPI app with Jinja2 templates:

**Routes:**

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/login` | No | Render login page with SSO URL |
| GET | `/sso/callback` | No | Exchange SSO token, set cookie, redirect |
| POST | `/api/auth/login` | No | Local login (username + password) |
| POST | `/api/auth/register` | No | Local registration |
| GET | `/api/auth/me` | Yes | Return current user info |
| GET | `/api/auth/logout` | No | Clear cookie, redirect to login |

**SSO Callback flow:**
1. Receive `access_token` query param from CompareGPT redirect
2. Call `exchange_sso_token(access_token)` → validate with auth.comparegpt.io
3. Upsert user in database
4. Create JWT, set `sci_token` httponly cookie (7 days, samesite=lax)
5. Redirect to `/`

**Local Login flow:**
1. Receive `{username, password}` JSON body
2. Hash password with SHA256
3. Look up user in database where `user_id = local_{username}` and `sso_token = hash`
4. If found, create JWT, set cookie, return `{redirect: "/"}`
5. If not found, return 401

**Local Register flow:**
1. Receive `{username, email, password}` JSON body
2. Validate username exists, password >= 8 chars
3. Hash password, create `user_id = local_{username}`
4. Insert into database
5. Create JWT, set cookie, return `{redirect: "/"}`

### Step 5: Create Login Page Template

Create `backend/templates/login.html` matching the aiXiv login page style:

**Left panel**: SSO sign-in with CompareGPT button
- Links to `comparegpt.io/sso-redirect?redirect=https://sci.platformai.org/sso/callback`

**Right panel**: Local account (tabbed Sign In / Register)
- Sign In: username + password → `POST /api/auth/login`
- Register: username + email (optional) + password + confirm → `POST /api/auth/register`

Style should match the existing dark theme of sci.platformai.org.

### Step 6: Add Auth-Aware Navigation to `index.html`

Update `index.html` to:
1. On page load, call `GET /api/auth/me`
2. If authenticated: show user name + logout button in navbar
3. If not authenticated: show "Sign In" button in navbar linking to `/login`

### Step 7: Update Nginx Configuration

Add proxy rules for the FastAPI backend (run on port 8502):

```nginx
server {
    server_name sci.platformai.org;
    root /home/spiritai/science/targeting;
    index index.html;

    # Auth API routes → FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8502;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Login page → FastAPI
    location /login {
        proxy_pass http://127.0.0.1:8502;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SSO callback → FastAPI
    location /sso/callback {
        proxy_pass http://127.0.0.1:8502;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files served by Nginx
    location / {
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # SSL (managed by Certbot)
    listen [::]:443 ssl;
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/sci.platformai.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sci.platformai.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
```

### Step 8: Create Startup Script

Create `start.sh`:
```bash
#!/bin/bash
cd /home/spiritai/science/targeting/backend
uvicorn app:app --host 127.0.0.1 --port 8502
```

Optionally set up PM2:
```bash
pm2 start "uvicorn app:app --host 127.0.0.1 --port 8502" --name sci-backend --cwd /home/spiritai/science/targeting/backend
```

---

## Dependencies

```
fastapi>=0.100.0
uvicorn>=0.22.0
httpx>=0.24.0
pyjwt>=2.0
jinja2>=3.0
python-multipart>=0.0.5
```

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `backend/auth.py` | **Create** | JWT + SSO authentication module |
| `backend/database.py` | **Create** | SQLite database setup and operations |
| `backend/app.py` | **Create** | FastAPI application with auth routes |
| `backend/templates/login.html` | **Create** | Login page (SSO + local) |
| `backend/requirements.txt` | **Create** | Python dependencies |
| `start.sh` | **Create** | Startup script |
| `index.html` | **Modify** | Add auth-aware navbar (sign in/out) |
| Nginx config | **Modify** | Add proxy rules for `/api/`, `/login`, `/sso/callback` |

---

## Auth Flow Summary

```
SSO Login:
  User → /login → Click "Sign in with CompareGPT"
    → comparegpt.io/sso-redirect?redirect=https://sci.platformai.org/sso/callback
    → CompareGPT authenticates user
    → Redirect to /sso/callback?access_token=XXX
    → Backend validates with auth.comparegpt.io/sso/validate
    → Upsert user in DB, create JWT, set cookie
    → Redirect to /

Local Login:
  User → /login → Enter username + password
    → POST /api/auth/login
    → Verify credentials in DB
    → Create JWT, set cookie
    → Redirect to /
```

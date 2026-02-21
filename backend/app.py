"""FastAPI application for sci.platformai.org authentication."""

import urllib.parse
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from auth import (
    SSO_REDIRECT_URL,
    SSO_CALLBACK_URL,
    create_jwt,
    exchange_sso_token,
    get_current_user,
    hash_password,
)
from database import init_db, get_db, upsert_user, get_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Science Auth", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sci.platformai.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# Initialize database on startup
init_db()


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    sso_url = f"{SSO_REDIRECT_URL}?redirect={urllib.parse.quote(SSO_CALLBACK_URL)}"
    return templates.TemplateResponse(
        "login.html", {"request": request, "sso_url": sso_url, "error": error}
    )


# ---------------------------------------------------------------------------
# SSO callback
# ---------------------------------------------------------------------------
@app.get("/sso/callback")
async def sso_callback(
    request: Request,
    access_token: str = "",
    token: str = "",
    code: str = "",
    sso_token: str = "",
):
    """Handle SSO redirect from CompareGPT."""
    tok = access_token or token or code or sso_token
    if not tok:
        return RedirectResponse("/login?error=No+token+received")

    user_info = await exchange_sso_token(tok)
    if not user_info or not user_info.get("user_id"):
        return RedirectResponse("/login?error=SSO+validation+failed")

    upsert_user(user_info, tok)

    jwt_token = create_jwt(
        user_info["user_id"],
        user_info.get("user_name", ""),
        user_info.get("role", "user"),
    )
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        "sci_token",
        jwt_token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return response


# ---------------------------------------------------------------------------
# Local login
# ---------------------------------------------------------------------------
@app.post("/api/auth/login")
async def local_login(request: Request):
    """Local login with username + password."""
    data = await request.json()
    username = (data.get("username") or "").strip()
    password = data.get("password", "")

    if not username or not password:
        raise HTTPException(400, "Username and password are required")

    pw_hash = hash_password(password)
    user_id = f"local_{username.lower().replace(' ', '_')}"

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE (user_id = ? OR user_name = ?) AND sso_token = ?",
        (user_id, username, pw_hash),
    ).fetchone()
    conn.close()

    if not user:
        raise HTTPException(401, "Invalid username or password")

    jwt_token = create_jwt(user["user_id"], user["user_name"], user["role"])
    response = JSONResponse(
        {"user_id": user["user_id"], "user_name": user["user_name"], "redirect": "/"}
    )
    response.set_cookie(
        "sci_token",
        jwt_token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return response


# ---------------------------------------------------------------------------
# Local registration
# ---------------------------------------------------------------------------
@app.post("/api/auth/register")
async def local_register(request: Request):
    """Register a local account."""
    data = await request.json()
    username = (data.get("username") or "").strip()
    password = data.get("password", "")

    if not username or not password:
        raise HTTPException(400, "Username and password are required")
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")

    pw_hash = hash_password(password)
    user_id = f"local_{username.lower().replace(' ', '_')}"

    conn = get_db()
    existing = conn.execute(
        "SELECT user_id FROM users WHERE user_id = ? OR user_name = ?",
        (user_id, username),
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Username already taken")
    conn.close()

    upsert_user(
        {"user_id": user_id, "user_name": username, "role": "user"},
        sso_token=pw_hash,
    )

    jwt_token = create_jwt(user_id, username, "user")
    response = JSONResponse(
        {"user_id": user_id, "user_name": username, "status": "registered", "redirect": "/"}
    )
    response.set_cookie(
        "sci_token",
        jwt_token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return response


# ---------------------------------------------------------------------------
# Current user info
# ---------------------------------------------------------------------------
@app.get("/api/auth/me")
async def auth_me(request: Request):
    """Return current user info or 401."""
    from auth import get_current_user

    user = await get_current_user(request)
    return JSONResponse(
        {
            "user_id": user["user_id"],
            "user_name": user["user_name"],
            "role": user["role"],
        }
    )


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
@app.get("/api/auth/logout")
async def logout():
    """Clear session cookie and redirect to login."""
    response = RedirectResponse("/login")
    response.delete_cookie("sci_token", path="/")
    return response

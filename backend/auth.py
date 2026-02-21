"""JWT authentication and SSO integration for sci.platformai.org"""

import os
import time
import logging
import hashlib

import jwt
import httpx
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JWT config
# ---------------------------------------------------------------------------
JWT_SECRET = os.environ.get("JWT_SECRET", "sci_jwt_s3cr3t_k3y_ch4ng3_m3")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY = 60 * 60 * 24 * 7  # 7 days

# ---------------------------------------------------------------------------
# SSO config (CompareGPT)
# ---------------------------------------------------------------------------
SSO_REDIRECT_URL = "https://comparegpt.io/sso-redirect"
SSO_VALIDATE_URL = "https://auth.comparegpt.io/sso/validate"
SSO_CALLBACK_URL = os.environ.get(
    "SSO_CALLBACK_URL", "https://sci.platformai.org/sso/callback"
)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def create_jwt(user_id: str, user_name: str = "", role: str = "user") -> str:
    """Create a JWT token for a user."""
    payload = {
        "sub": user_id,
        "name": user_name,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> dict | None:
    """Verify and decode a JWT token. Returns payload dict or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT: {e}")
        return None


def _extract_jwt_from_request(request: Request) -> str | None:
    """Extract JWT from cookie or Authorization header."""
    token = request.cookies.get("sci_token")
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


# ---------------------------------------------------------------------------
# SSO token exchange
# ---------------------------------------------------------------------------
async def exchange_sso_token(sso_token: str) -> dict | None:
    """Exchange an SSO token with auth.comparegpt.io/sso/validate.

    Returns user info dict or None on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                SSO_VALIDATE_URL,
                headers={"Authorization": f"Bearer {sso_token}"},
            )
            logger.info(f"SSO validate response: {resp.status_code}")
            if resp.status_code == 200:
                body = resp.json()
                data = body.get("data") or body
                user_info = data.get("user_info") or data
                balance = data.get("balance") or {}
                return {
                    "user_id": str(
                        user_info.get("user_id", user_info.get("id", ""))
                    ),
                    "user_name": user_info.get(
                        "user_name", user_info.get("name", "")
                    ),
                    "api_key": data.get(
                        "api_key", user_info.get("api_key", "")
                    ),
                    "credit": balance.get("credit", data.get("credit", 0)),
                    "token": balance.get("token", data.get("token", 0)),
                    "role": user_info.get("role", "user"),
                }
            else:
                logger.error(
                    f"SSO validate failed: {resp.status_code} {resp.text}"
                )
                return None
    except Exception as e:
        logger.error(f"SSO exchange error: {e}")
        return None


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------
def _build_user_dict(payload: dict, db_user: dict | None) -> dict:
    """Build user context dict from JWT payload and optional DB record."""
    user = {
        "user_id": payload["sub"],
        "user_name": payload.get("name", ""),
        "role": payload.get("role", "user"),
    }
    if db_user:
        user["user_name"] = db_user.get("user_name") or user["user_name"]
        user["role"] = db_user.get("role") or user["role"]
        user["credit"] = db_user.get("credit", 0)
        user["token"] = db_user.get("token", 0)
    return user


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency — requires authentication. Raises 401."""
    from database import get_user

    token = _extract_jwt_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    db_user = get_user(payload["sub"])
    return _build_user_dict(payload, db_user)


async def get_optional_user(request: Request) -> dict | None:
    """FastAPI dependency — returns user dict if authenticated, None otherwise."""
    from database import get_user

    token = _extract_jwt_from_request(request)
    if not token:
        return None
    payload = verify_jwt(token)
    if not payload:
        return None
    db_user = get_user(payload["sub"])
    return _build_user_dict(payload, db_user)

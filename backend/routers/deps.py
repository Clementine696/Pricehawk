from datetime import datetime, timedelta
from typing import Optional
import secrets
import os

from fastapi import HTTPException, Cookie, Header, Request
from database import get_user_by_username
import bcrypt

SESSION_EXPIRE_MINUTES = 10080  # 7 days
COOKIE_NAME = "session_token"
sessions: dict[str, dict] = {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def get_current_user(
    session_token: Optional[str] = Cookie(None, alias=COOKIE_NAME),
    authorization: Optional[str] = Header(None)
) -> dict:
    token = _extract_bearer_token(authorization) or session_token
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = sessions[token]
    if datetime.utcnow() > session["expires"]:
        del sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")
    session["last_activity"] = datetime.utcnow()
    return session["user"]


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _parse_search_input(search: str) -> list[str]:
    normalised = search.replace('\n', ' ').replace('\r', ' ').replace(',', ' ')
    return [s.strip() for s in normalised.split() if s.strip()]

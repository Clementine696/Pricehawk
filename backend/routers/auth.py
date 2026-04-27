from datetime import datetime, timedelta
from typing import Optional
import os
import logging

from fastapi import APIRouter, HTTPException, Response, Depends, Cookie, Header, Request
from pydantic import BaseModel

from database import get_user_by_username
from routers.deps import (
    SESSION_EXPIRE_MINUTES, COOKIE_NAME, sessions,
    verify_password, get_current_user, get_client_ip, _extract_bearer_token
)

logger = logging.getLogger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str


@router.post("/api/auth/login")
def login(data: LoginRequest, response: Response, request: Request):
    user = get_user_by_username(data.username)
    if not user or not verify_password(data.password, user["hashed_password"]):
        logger.warning(f"Failed login attempt for username: {data.username} from IP: {get_client_ip(request)}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    import secrets
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRE_MINUTES)
    login_time = datetime.utcnow()

    sessions[token] = {
        "user": {"user_id": user["user_id"], "username": user["username"]},
        "expires": expires,
        "login_time": login_time,
        "last_activity": login_time,
        "ip_address": get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", "unknown"),
    }

    logger.info(f"LOGIN | User: {user['username']} | IP: {get_client_ip(request)} | Time: {login_time.isoformat()}")

    is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
    if is_production:
        cookie_value = f"{COOKIE_NAME}={token}; HttpOnly; Secure; SameSite=None; Partitioned; Max-Age={SESSION_EXPIRE_MINUTES * 60}; Path=/"
        response.headers.append("Set-Cookie", cookie_value)
    else:
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            max_age=SESSION_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=False,
        )

    return {"message": "Login successful", "username": user["username"], "token": token}


@router.post("/api/auth/logout")
def logout(
    response: Response,
    request: Request,
    session_token: Optional[str] = Cookie(None, alias=COOKIE_NAME),
    authorization: Optional[str] = Header(None)
):
    token = _extract_bearer_token(authorization) or session_token
    if token and token in sessions:
        session = sessions[token]
        username = session["user"]["username"]
        login_time = session.get("login_time", datetime.utcnow())
        logout_time = datetime.utcnow()
        session_duration = (logout_time - login_time).total_seconds()
        logger.info(f"LOGOUT | User: {username} | IP: {get_client_ip(request)} | Duration: {session_duration:.0f} seconds")
        del sessions[token]

    is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
    response.delete_cookie(
        key=COOKIE_NAME,
        samesite="none" if is_production else "lax",
        secure=True if is_production else False,
    )
    return {"message": "Logged out"}


@router.get("/api/auth/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    return user


@router.get("/api/health")
def health_check():
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

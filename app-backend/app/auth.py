"""Google sign-in + cookie session for the personal account area.

Flow: the frontend gets a Google ID token (Google Identity Services), POSTs it to
/api/auth/google; we verify it, upsert the user, and set an httpOnly JWT cookie.
`current_user` / `require_user` read that cookie on the personal endpoints.
"""
import datetime
import logging
import os

import jwt
from fastapi import Cookie, HTTPException, Response, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

logger = logging.getLogger("auth")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")  # public, also shipped to the frontend
SESSION_SECRET = os.getenv("SESSION_SECRET")       # signs the session JWT
COOKIE_NAME = "optibet_session"
SESSION_DAYS = 30
# Secure cookie in prod; the dev proxy is http://localhost so allow override.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() != "false"

_google_request = google_requests.Request()


def auth_configured() -> bool:
    return bool(GOOGLE_CLIENT_ID and SESSION_SECRET)


def verify_google_token(token: str) -> dict:
    """Return the Google claims (sub, email, name, picture) or raise 401."""
    if not auth_configured():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Sign-in is not configured")
    try:
        claims = google_id_token.verify_oauth2_token(token, _google_request, GOOGLE_CLIENT_ID)
    except Exception as e:  # noqa: BLE001 - any verification failure is a 401
        logger.info("Google token rejected: %s", e)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google token") from e
    if claims.get("sub") is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google token")
    return claims


def issue_session(response: Response, user_id: int) -> None:
    exp = datetime.datetime.utcnow() + datetime.timedelta(days=SESSION_DAYS)
    token = jwt.encode({"uid": user_id, "exp": exp}, SESSION_SECRET, algorithm="HS256")
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_DAYS * 86400, httponly=True,
                        secure=COOKIE_SECURE, samesite="lax", path="/")


def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def current_user(**cookies: str) -> int | None:
    """User id from the session cookie, or None. Takes the cookie value as kwarg `session`."""
    token = cookies.get("session")
    if not token or not auth_configured():
        return None
    try:
        return int(jwt.decode(token, SESSION_SECRET, algorithms=["HS256"])["uid"])
    except Exception:  # noqa: BLE001 - expired/invalid cookie = anonymous
        return None


def optional_user(optibet_session: str | None = Cookie(default=None)) -> int | None:
    return current_user(session=optibet_session)


def require_user(optibet_session: str | None = Cookie(default=None)) -> int:
    uid = current_user(session=optibet_session)
    if uid is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in required")
    return uid

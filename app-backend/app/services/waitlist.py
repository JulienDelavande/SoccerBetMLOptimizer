"""Waitlist for the future paid offer: validation, storage, owner notification, unsubscribe.

No payment, no promise: the form only records who wants to hear about the launch, which
formula and budget they have in mind, and an optional message. Each signup pings the owner
through ntfy (NTFY_URL, skipped when empty).
"""
import base64
import collections
import hashlib
import hmac
import logging
import os
import re
import threading
import time
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import text

logger = logging.getLogger("waitlist")

PLANS = ("monthly", "yearly", "unsure")
BUDGETS = ("lt10", "10_20", "20_30", "30plus")
MESSAGE_MAX = 1000
NOTIFY_MESSAGE_MAX = 300
HONEYPOT_FIELD = "website"
# Pragmatic shape check (one @, a dot in the domain, no spaces); the real proof is the launch email.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class WaitlistIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str = Field(max_length=320)
    plan: Literal["monthly", "yearly", "unsure"]
    budget: Literal["lt10", "10_20", "20_30", "30plus"]
    message: str | None = Field(default=None, max_length=MESSAGE_MAX)
    lang: Literal["fr", "en"] = "fr"
    consent: Literal[True]  # contact about the launch
    adult: Literal[True]    # 18+ confirmation

    @field_validator("email", mode="before")
    @classmethod
    def _email(cls, v):
        if not isinstance(v, str):
            raise ValueError("email must be a string")
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("invalid email")
        return v

    @field_validator("message", mode="before")
    @classmethod
    def _message(cls, v):
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("message must be a string")
        v = v.strip()
        return v or None


def is_bot(payload: object) -> bool:
    """A filled honeypot means an automated submission: accept silently, store nothing."""
    return isinstance(payload, dict) and bool(str(payload.get(HONEYPOT_FIELD) or "").strip())


# --- storage ---------------------------------------------------------------------------
UPSERT_SQL = """
INSERT INTO waitlist (email, user_id, plan, budget, message, lang, consent_at)
VALUES (:email, :uid, :plan, :budget, :message, :lang, CURRENT_TIMESTAMP)
ON CONFLICT (email) DO UPDATE SET
    user_id = COALESCE(EXCLUDED.user_id, waitlist.user_id),
    plan = EXCLUDED.plan, budget = EXCLUDED.budget, message = EXCLUDED.message, lang = EXCLUDED.lang,
    consent_at = EXCLUDED.consent_at, updated_at = CURRENT_TIMESTAMP
RETURNING (xmax = 0) AS inserted
"""


def account_email(uid: int) -> str | None:
    from app._config import engine
    with engine.connect() as conn:
        email = conn.execute(text("SELECT email FROM users WHERE user_id = :uid"), {"uid": uid}).scalar()
    return email.strip().lower() if email else None


def upsert(entry: WaitlistIn, uid: int | None) -> bool:
    """Insert or update the row for this email (created_at kept). True when the row is new.

    The row is linked to the signed-in account only when the email is the account's own, so a
    signed-in visitor cannot attach somebody else's address to their account.
    """
    from app._config import engine
    link = uid if uid is not None and account_email(uid) == entry.email else None
    with engine.begin() as conn:
        return bool(conn.execute(text(UPSERT_SQL), {
            "email": entry.email, "uid": link, "plan": entry.plan, "budget": entry.budget,
            "message": entry.message, "lang": entry.lang,
        }).scalar_one())


def remove(email: str) -> bool:
    from app._config import engine
    with engine.begin() as conn:
        return conn.execute(text("DELETE FROM waitlist WHERE email = :email"),
                            {"email": email.strip().lower()}).rowcount > 0


# Run inside users.delete_account's transaction: rows linked to the account, and the row
# registered with the account's email before signing in.
DELETE_FOR_USER_SQL = """
DELETE FROM waitlist
WHERE user_id = :uid OR email = (SELECT lower(email) FROM users WHERE user_id = :uid)
"""


# --- one-click unsubscribe ---------------------------------------------------------------
def _secret() -> bytes | None:
    s = os.getenv("SESSION_SECRET")
    return s.encode() if s else None


def unsubscribe_token(email: str) -> str:
    secret = _secret()
    if secret is None:
        raise RuntimeError("SESSION_SECRET is not set")
    msg = f"waitlist-unsubscribe:{email.strip().lower()}".encode()
    return base64.urlsafe_b64encode(hmac.new(secret, msg, hashlib.sha256).digest()).decode().rstrip("=")


def unsubscribe_url(email: str, base: str = "https://optibet.delavande.fr/api") -> str:
    """Link to put in launch emails (the public site proxies /api to this backend)."""
    from urllib.parse import urlencode
    return f"{base}/waitlist/unsubscribe?" + urlencode({"email": email.strip().lower(), "token": unsubscribe_token(email)})


def valid_unsubscribe_token(email: str, token: str) -> bool:
    if _secret() is None or not email or not token:
        return False
    return hmac.compare_digest(unsubscribe_token(email), token)


# --- rate limit (per process, per client IP) ----------------------------------------------
class RateLimiter:
    """Sliding window: at most `limit` hits per `window` seconds per key."""

    def __init__(self, limit: int = 5, window: float = 3600.0):
        self.limit, self.window = limit, window
        self._hits: dict[str, collections.deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            q = self._hits.setdefault(key, collections.deque())
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            # Forget idle keys so the map does not grow with every visitor.
            if len(self._hits) > 10_000:
                for k in [k for k, v in self._hits.items() if not v or v[-1] <= now - self.window]:
                    del self._hits[k]
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_ip(headers, peer: str | None) -> str:
    """Visitor IP: first X-Forwarded-For hop (set by Traefik, passed on by the web nginx), else the peer."""
    fwd = headers.get("x-forwarded-for", "")
    first = fwd.split(",")[0].strip()
    return first or peer or "unknown"


# --- owner notification (ntfy) -------------------------------------------------------------
NOTIFY_TITLE = "OptiBet · liste d'attente"
PLAN_LABEL = {"monthly": "Mensuel", "yearly": "Annuel", "unsure": "Je ne sais pas"}
BUDGET_LABEL = {"lt10": "< 10 €", "10_20": "10-20 €", "20_30": "20-30 €", "30plus": "30 € et +"}


def rfc2047(value: str) -> str:
    """HTTP headers are latin-1 at best; ntfy decodes RFC 2047 encoded-words."""
    try:
        value.encode("ascii")
        return value
    except UnicodeEncodeError:
        return "=?UTF-8?B?" + base64.b64encode(value.encode()).decode() + "?="


def notification(entry: WaitlistIn, created: bool) -> tuple[dict[str, str], str]:
    """Headers and body of the ntfy push for one signup."""
    msg = entry.message or ""
    if len(msg) > NOTIFY_MESSAGE_MAX:
        msg = msg[:NOTIFY_MESSAGE_MAX - 1] + "…"
    lines = [
        f"{'Nouvelle inscription' if created else 'Mise à jour'} : {entry.email}",
        f"Formule : {PLAN_LABEL[entry.plan]}",
        f"Budget : {BUDGET_LABEL[entry.budget]}",
        f"Langue : {entry.lang}",
    ]
    if msg:
        lines.append(f"Message : {msg}")
    headers = {"Title": rfc2047(NOTIFY_TITLE), "Tags": "lock"}
    return headers, "\n".join(lines)


def notify(entry: WaitlistIn, created: bool) -> None:
    """Push to ntfy; never raises (runs as a background task after the response)."""
    url = os.getenv("NTFY_URL", "").strip()
    if not url:
        return
    headers, body = notification(entry, created)
    try:
        httpx.post(url, content=body.encode(), headers=headers, timeout=5.0).raise_for_status()
    except Exception as e:  # noqa: BLE001 - a lost ping must never surface to the visitor
        # Class and status only: the topic URL is a secret and httpx errors quote it.
        status = getattr(getattr(e, "response", None), "status_code", None)
        logger.warning("ntfy notification failed: %s %s", type(e).__name__, status or "")

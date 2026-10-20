import importlib

import pytest
from fastapi import HTTPException


def reload_auth(monkeypatch, client_id="cid", secret="s3cret"):
    if client_id is None:
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    else:
        monkeypatch.setenv("GOOGLE_CLIENT_ID", client_id)
    if secret is None:
        monkeypatch.delenv("SESSION_SECRET", raising=False)
    else:
        monkeypatch.setenv("SESSION_SECRET", secret)
    import app.auth as auth
    return importlib.reload(auth)


def test_session_roundtrip(monkeypatch):
    auth = reload_auth(monkeypatch)

    class Resp:
        def __init__(self): self.cookies = {}
        def set_cookie(self, name, value, **kw): self.cookies[name] = value
    r = Resp()
    auth.issue_session(r, 42)
    token = r.cookies[auth.COOKIE_NAME]
    assert auth.current_user(session=token) == 42
    assert auth.current_user(session="garbage") is None
    assert auth.current_user(session=None) is None


def test_require_user_rejects_anonymous(monkeypatch):
    auth = reload_auth(monkeypatch)
    with pytest.raises(HTTPException) as e:
        auth.require_user(optibet_session=None)
    assert e.value.status_code == 401


def test_verify_google_token_needs_config(monkeypatch):
    auth = reload_auth(monkeypatch, client_id=None, secret=None)
    assert auth.auth_configured() is False
    with pytest.raises(HTTPException) as e:
        auth.verify_google_token("whatever")
    assert e.value.status_code == 503


def test_verify_google_token_rejects_bad_token(monkeypatch):
    auth = reload_auth(monkeypatch)
    monkeypatch.setattr(auth.google_id_token, "verify_oauth2_token",
                        lambda *a, **k: (_ for _ in ()).throw(ValueError("bad")))
    with pytest.raises(HTTPException) as e:
        auth.verify_google_token("bad")
    assert e.value.status_code == 401


def test_verify_google_token_accepts_valid(monkeypatch):
    auth = reload_auth(monkeypatch)
    monkeypatch.setattr(auth.google_id_token, "verify_oauth2_token",
                        lambda *a, **k: {"sub": "123", "email": "a@b.c", "name": "A"})
    assert auth.verify_google_token("ok")["sub"] == "123"

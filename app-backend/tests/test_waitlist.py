"""Waitlist: validation, honeypot, upsert, rate limit, ntfy notification, unsubscribe, account deletion.

API tests patch the storage functions (no database in CI). The SQL itself is covered by the
integration tests at the bottom, which run only when OPTIBET_TEST_DB_URL points at a throwaway
Postgres migrated to head (`cd db && alembic upgrade head`), e.g.
OPTIBET_TEST_DB_URL=postgresql+psycopg2://kube:pw@localhost:55499/optimsportbets-db
"""
import base64
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import auth
from app.services import users as users_service
from app.services import waitlist as wl

REAL_NOTIFY = wl.notify  # captured before any fixture patches it
VALID = {"email": "  Alice@Example.COM ", "plan": "yearly", "budget": "10_20", "message": "  Hâte de voir  ",
         "lang": "fr", "consent": True, "adult": True, "website": ""}


@pytest.fixture
def client(monkeypatch):
    import main
    wl.limiter.reset()
    calls = {"upsert": [], "notify": [], "remove": []}

    def fake_upsert(entry, uid):
        calls["upsert"].append((entry, uid))
        return len(calls["upsert"]) == 1

    monkeypatch.setattr(wl, "upsert", fake_upsert)
    monkeypatch.setattr(wl, "notify", lambda entry, created: calls["notify"].append((entry, created)))
    monkeypatch.setattr(wl, "remove", lambda email: calls["remove"].append(email) or True)
    c = TestClient(main.app)
    c.calls = calls
    yield c
    wl.limiter.reset()


# --- validation ----------------------------------------------------------------------------
def test_valid_entry_is_normalised():
    e = wl.WaitlistIn.model_validate(VALID)
    assert e.email == "alice@example.com"
    assert e.message == "Hâte de voir"
    assert (e.plan, e.budget, e.lang) == ("yearly", "10_20", "fr")


def test_blank_message_becomes_none():
    assert wl.WaitlistIn.model_validate({**VALID, "message": "   "}).message is None
    assert wl.WaitlistIn.model_validate({k: v for k, v in VALID.items() if k != "message"}).message is None


@pytest.mark.parametrize("patch", [
    {"email": "not-an-email"},
    {"email": "a@b"},
    {"email": "a b@c.fr"},
    {"email": ""},
    {"email": "x" * 320 + "@a.fr"},
    {"plan": "weekly"},
    {"budget": "50plus"},
    {"lang": "de"},
    {"message": "x" * 1001},
    {"consent": False},
    {"adult": False},
    {"consent": None},
])
def test_invalid_entries_are_rejected(patch):
    with pytest.raises(ValidationError):
        wl.WaitlistIn.model_validate({**VALID, **patch})


@pytest.mark.parametrize("missing", ["email", "plan", "budget", "consent", "adult"])
def test_required_fields(missing):
    with pytest.raises(ValidationError):
        wl.WaitlistIn.model_validate({k: v for k, v in VALID.items() if k != missing})


def test_message_of_exactly_1000_chars_is_accepted():
    assert len(wl.WaitlistIn.model_validate({**VALID, "message": "é" * 1000}).message) == 1000


def test_honeypot_detection():
    assert wl.is_bot({**VALID, "website": "http://spam"})
    assert not wl.is_bot(VALID)
    assert not wl.is_bot({**VALID, "website": "  "})
    assert not wl.is_bot([1, 2])


# --- rate limit + client ip -------------------------------------------------------------------
def test_rate_limiter_window():
    rl = wl.RateLimiter(limit=5, window=3600)
    assert all(rl.allow("1.2.3.4", now=t) for t in range(5))
    assert not rl.allow("1.2.3.4", now=10)
    assert rl.allow("5.6.7.8", now=10)          # per key
    assert rl.allow("1.2.3.4", now=3600.5)      # first hit left the window


def test_client_ip_prefers_first_forwarded_hop():
    assert wl.client_ip({"x-forwarded-for": "203.0.113.9, 10.42.0.7"}, "10.42.0.8") == "203.0.113.9"
    assert wl.client_ip({}, "10.42.0.8") == "10.42.0.8"
    assert wl.client_ip({}, None) == "unknown"


# --- notification ----------------------------------------------------------------------------
def test_notification_payload():
    e = wl.WaitlistIn.model_validate({**VALID, "message": "m" * 400, "lang": "en"})
    headers, body = wl.notification(e, created=True)
    assert headers["Tags"] == "lock"
    title = headers["Title"]
    assert title.startswith("=?UTF-8?B?") and title.endswith("?=")
    assert base64.b64decode(title[10:-2]).decode() == "OptiBet · liste d'attente"
    title.encode("ascii")  # header-safe
    lines = body.split("\n")
    assert lines[0] == "Nouvelle inscription : alice@example.com"
    assert "Formule : Annuel" in lines and "Budget : 10-20 €" in lines and "Langue : en" in lines
    msg = next(line for line in lines if line.startswith("Message : "))
    assert len(msg) == len("Message : ") + 300 and msg.endswith("…")


def test_notification_update_without_message():
    e = wl.WaitlistIn.model_validate({**VALID, "message": None, "plan": "unsure", "budget": "lt10"})
    _, body = wl.notification(e, created=False)
    assert body.startswith("Mise à jour : alice@example.com")
    assert "Formule : Je ne sais pas" in body and "Budget : < 10 €" in body
    assert "Message" not in body


def test_rfc2047_keeps_ascii():
    assert wl.rfc2047("OptiBet waitlist") == "OptiBet waitlist"


def test_notify_skipped_without_url(monkeypatch):
    monkeypatch.delenv("NTFY_URL", raising=False)
    monkeypatch.setattr(wl.httpx, "post", lambda *a, **k: pytest.fail("must not post"))
    wl.notify(wl.WaitlistIn.model_validate(VALID), True)


def test_notify_posts_to_ntfy(monkeypatch):
    monkeypatch.setenv("NTFY_URL", "https://ntfy.example/optibet-secret")
    sent = {}

    class Resp:
        def raise_for_status(self): pass

    def post(url, content, headers, timeout):
        sent.update(url=url, content=content, headers=headers, timeout=timeout)
        return Resp()

    monkeypatch.setattr(wl.httpx, "post", post)
    e = wl.WaitlistIn.model_validate(VALID)
    wl.notify(e, True)
    headers, body = wl.notification(e, True)
    assert sent == {"url": "https://ntfy.example/optibet-secret", "content": body.encode(), "headers": headers, "timeout": 5.0}


def test_notify_swallows_errors(monkeypatch, caplog):
    monkeypatch.setenv("NTFY_URL", "https://ntfy.example/optibet-secret")

    def boom(*a, **k):
        raise wl.httpx.ConnectTimeout("timed out talking to https://ntfy.example/optibet-secret")

    monkeypatch.setattr(wl.httpx, "post", boom)
    wl.notify(wl.WaitlistIn.model_validate(VALID), True)  # must not raise
    assert "ConnectTimeout" in caplog.text
    assert "optibet-secret" not in caplog.text  # the topic URL is a secret


# --- API ---------------------------------------------------------------------------------------
def test_post_records_and_notifies(client):
    r = client.post("/waitlist", json=VALID)
    assert r.status_code == 204 and r.content == b""
    (entry, uid), = client.calls["upsert"]
    assert entry.email == "alice@example.com" and uid is None
    assert client.calls["notify"] == [(entry, True)]


def test_post_update_notifies_as_update(client):
    client.post("/waitlist", json=VALID)
    r = client.post("/waitlist", json={**VALID, "plan": "monthly"})
    assert r.status_code == 204
    assert [c for _, c in client.calls["notify"]] == [True, False]


def test_post_honeypot_is_silently_ignored(client):
    r = client.post("/waitlist", json={**VALID, "website": "http://spam.example", "plan": "nonsense"})
    assert r.status_code == 204
    assert client.calls["upsert"] == [] and client.calls["notify"] == []


def test_post_invalid_is_422_without_echoing_input(client):
    r = client.post("/waitlist", json={**VALID, "email": "secret-value-not-an-email", "consent": False})
    assert r.status_code == 422
    assert "secret-value" not in r.text
    locs = {tuple(d["loc"]) for d in r.json()["detail"]}
    assert ("email",) in locs and ("consent",) in locs
    assert client.calls["upsert"] == []


def test_post_non_object_body_is_422(client):
    assert client.post("/waitlist", json=["a"]).status_code == 422


def test_post_rate_limited_per_ip(client):
    ip = {"X-Forwarded-For": "198.51.100.7"}
    for i in range(5):
        assert client.post("/waitlist", json={**VALID, "email": f"u{i}@ex.fr"}, headers=ip).status_code == 204
    assert client.post("/waitlist", json=VALID, headers=ip).status_code == 429
    assert len(client.calls["upsert"]) == 5
    assert client.post("/waitlist", json=VALID, headers={"X-Forwarded-For": "198.51.100.8"}).status_code == 204


def test_notification_failure_does_not_break_the_request(client, monkeypatch):
    monkeypatch.setenv("NTFY_URL", "https://ntfy.example/t")
    monkeypatch.setattr(wl, "notify", REAL_NOTIFY)  # the real one, over the fixture's recorder

    def boom(*a, **k):
        raise wl.httpx.ConnectError("down")

    monkeypatch.setattr(wl.httpx, "post", boom)
    assert client.post("/waitlist", json=VALID).status_code == 204
    assert len(client.calls["upsert"]) == 1


def test_signed_in_user_id_is_passed(client, monkeypatch):
    monkeypatch.setattr(auth, "GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setattr(auth, "SESSION_SECRET", "s3cret")
    import jwt
    token = jwt.encode({"uid": 42}, "s3cret", algorithm="HS256")
    client.cookies.set(auth.COOKIE_NAME, token)
    assert client.post("/waitlist", json=VALID).status_code == 204
    assert client.calls["upsert"][0][1] == 42


def test_unsubscribe_with_valid_token(client, monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "s3cret")
    token = wl.unsubscribe_token("Alice@Example.com")
    r = client.get("/waitlist/unsubscribe", params={"email": "alice@example.com", "token": token})
    assert r.status_code == 200 and "retirée" in r.text
    assert client.calls["remove"] == ["alice@example.com"]


@pytest.mark.parametrize("params", [
    {"email": "alice@example.com", "token": "forged"},
    {"email": "alice@example.com"},
    {},
])
def test_unsubscribe_rejects_bad_token(client, monkeypatch, params):
    monkeypatch.setenv("SESSION_SECRET", "s3cret")
    r = client.get("/waitlist/unsubscribe", params=params)
    assert r.status_code == 400
    assert client.calls["remove"] == []


def test_unsubscribe_token_is_per_email_and_secret(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "a")
    t1 = wl.unsubscribe_token("x@y.fr")
    assert wl.valid_unsubscribe_token("X@Y.fr", t1)
    assert not wl.valid_unsubscribe_token("z@y.fr", t1)
    monkeypatch.setenv("SESSION_SECRET", "b")
    assert not wl.valid_unsubscribe_token("x@y.fr", t1)
    monkeypatch.delenv("SESSION_SECRET")
    assert not wl.valid_unsubscribe_token("x@y.fr", t1)


def test_unsubscribe_url(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "a")
    url = wl.unsubscribe_url("A+b@y.fr")
    assert url.startswith("https://optibet.delavande.fr/api/waitlist/unsubscribe?email=a%2Bb%40y.fr&token=")


# --- account deletion ---------------------------------------------------------------------------
def test_delete_account_removes_waitlist_row_first(monkeypatch):
    executed = []

    class Conn:
        def execute(self, stmt, params=None):
            executed.append((str(stmt), params))

    class Begin:
        def __enter__(self): return Conn()
        def __exit__(self, *a): return False

    class Engine:
        def begin(self): return Begin()

    import app._config
    monkeypatch.setattr(app._config, "engine", Engine())
    users_service.delete_account(7)
    assert "DELETE FROM waitlist" in executed[0][0] and executed[0][1] == {"uid": 7}
    assert "DELETE FROM users" in executed[1][0]


# --- SQL against a real Postgres (opt-in) ---------------------------------------------------------
PG_URL = os.getenv("OPTIBET_TEST_DB_URL")
pg = pytest.mark.skipif(not PG_URL, reason="set OPTIBET_TEST_DB_URL to a throwaway Postgres migrated to head")


@pytest.fixture
def pg_engine(monkeypatch):
    from sqlalchemy import create_engine, text
    engine = create_engine(PG_URL)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE waitlist, users RESTART IDENTITY CASCADE"))
    import app._config
    monkeypatch.setattr(app._config, "engine", engine)
    yield engine
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE waitlist, users RESTART IDENTITY CASCADE"))
    engine.dispose()


def _rows(engine):
    from sqlalchemy import text
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(text("SELECT * FROM waitlist ORDER BY id")).mappings()]


@pg
def test_pg_upsert_keeps_created_at(pg_engine):
    import time
    e = wl.WaitlistIn.model_validate(VALID)
    assert wl.upsert(e, None) is True
    first = _rows(pg_engine)[0]
    time.sleep(0.05)
    assert wl.upsert(wl.WaitlistIn.model_validate({**VALID, "email": "ALICE@example.com", "plan": "monthly", "message": None}), None) is False
    (row,) = _rows(pg_engine)
    assert row["email"] == "alice@example.com" and row["plan"] == "monthly" and row["message"] is None
    assert row["created_at"] == first["created_at"] and row["updated_at"] > first["updated_at"]
    assert row["consent_at"] >= first["consent_at"]


@pg
def test_pg_user_link_only_for_own_email_and_account_deletion(pg_engine):
    from sqlalchemy import text
    uid = users_service.upsert_user({"sub": "g1", "email": "Alice@Example.com", "name": "A"})
    other = users_service.upsert_user({"sub": "g2", "email": "bob@example.com", "name": "B"})
    wl.upsert(wl.WaitlistIn.model_validate(VALID), uid)                                  # own email: linked
    wl.upsert(wl.WaitlistIn.model_validate({**VALID, "email": "carol@example.com"}), other)  # not bob's: unlinked
    rows = {r["email"]: r["user_id"] for r in _rows(pg_engine)}
    assert rows == {"alice@example.com": uid, "carol@example.com": None}
    users_service.delete_account(uid)
    assert [r["email"] for r in _rows(pg_engine)] == ["carol@example.com"]
    with pg_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM users")).scalar() == 1


@pg
def test_pg_account_deletion_removes_row_signed_up_anonymously(pg_engine):
    wl.upsert(wl.WaitlistIn.model_validate({**VALID, "email": "dave@example.com"}), None)
    uid = users_service.upsert_user({"sub": "g3", "email": "Dave@Example.com"})
    users_service.delete_account(uid)
    assert _rows(pg_engine) == []


@pg
def test_pg_remove(pg_engine):
    wl.upsert(wl.WaitlistIn.model_validate(VALID), None)
    assert wl.remove("ALICE@example.com") is True
    assert wl.remove("alice@example.com") is False
    assert _rows(pg_engine) == []

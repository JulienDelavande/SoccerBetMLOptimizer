from unittest import mock

import pytest
import requests

from optibet_lib.soccerdata import _common
from optibet_lib.soccerdata.fbref import FBref

SOLUTION = {
    "status": "ok",
    "solution": {
        "userAgent": "Mozilla/5.0 test-agent",
        "cookies": [
            {"name": "cf_clearance", "value": "abc", "domain": ".fbref.com", "path": "/"},
            {"name": "__cf_bm", "value": "xyz", "domain": ".fbref.com", "path": "/"},
        ],
    },
}


def _post_returning(payload):
    response = mock.Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return mock.patch.object(_common.requests, "post", return_value=response)


def test_session_carries_user_agent_and_clearance_cookies():
    with _post_returning(SOLUTION) as post:
        session = _common._flaresolverr_session("http://fs:8191/", "https://fbref.com/en/")

    assert isinstance(session, requests.Session)
    assert session.headers["User-Agent"] == "Mozilla/5.0 test-agent"
    assert session.cookies.get("cf_clearance", domain=".fbref.com") == "abc"
    assert session.cookies.get("__cf_bm", domain=".fbref.com") == "xyz"
    url, = post.call_args.args
    assert url == "http://fs:8191/v1"
    assert post.call_args.kwargs["json"]["url"] == "https://fbref.com/en/"


def test_unsolved_challenge_raises():
    with _post_returning({"status": "error", "message": "IP banned"}):
        with pytest.raises(ConnectionError, match="IP banned"):
            _common._flaresolverr_session("http://fs:8191", "https://fbref.com/en/")


def test_fbref_uses_flaresolverr_only_when_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("FLARESOLVERR_URL", "http://fs:8191")
    with _post_returning(SOLUTION) as post:
        reader = FBref(leagues="ENG-Premier League", seasons="2425", data_dir=tmp_path)
    assert post.called
    assert reader._session.headers["User-Agent"] == "Mozilla/5.0 test-agent"

    monkeypatch.delenv("FLARESOLVERR_URL")
    with mock.patch.object(_common.requests, "post") as post:
        FBref(leagues="ENG-Premier League", seasons="2425", data_dir=tmp_path)
    assert not post.called

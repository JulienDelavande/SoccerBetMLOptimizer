import datetime

import pandas as pd
import pytest

from app.services.match_detail import books_table, build_match_detail, head_to_head, line_series, team_form
from tests.test_site_payload import NOW, bet, frame

D = datetime.date


def matches():
    return pd.DataFrame([
        {"game": "a", "date": D(2026, 10, 1), "league": "ESP-La Liga", "home": "H1", "away": "X", "home_g": 2, "away_g": 0},
        {"game": "b", "date": D(2026, 10, 5), "league": "ESP-La Liga", "home": "Y", "away": "H1", "home_g": 1, "away_g": 1},
        {"game": "c", "date": D(2026, 10, 8), "league": "ESP-La Liga", "home": "A1", "away": "H1", "home_g": 3, "away_g": 1},
        {"game": "d", "date": D(2026, 10, 12), "league": "ESP-La Liga", "home": "H1", "away": "Z", "home_g": None, "away_g": None},
        {"game": "e", "date": D(2026, 10, 30), "league": "ESP-La Liga", "home": "H1", "away": "W", "home_g": 4, "away_g": 0},
    ])


def test_team_form_is_before_kickoff_newest_first_from_team_view():
    f = team_form(matches(), "H1", D(2026, 10, 20))
    assert [x["result"] for x in f] == ["L", "D", "W"]  # unplayed 12/10 and future 30/10 excluded
    assert f[0] == {"date": "2026-10-08", "opponent": "A1", "venue": "A", "score": "3-1", "result": "L", "league": "ESP-La Liga"}


def test_head_to_head_both_venues():
    h = head_to_head(matches(), "A1", "H1", D(2026, 10, 20))
    assert [x["score"] for x in h] == ["3-1"]


def test_line_series_keeps_price_changes_only():
    t = pd.to_datetime(["2026-10-18 10:00", "2026-10-18 12:00", "2026-10-19 10:00"])
    odds = pd.DataFrame({"datetime_insert": t, "side": ["home"] * 3, "price": [2.0, 2.0, 1.9]})
    s = line_series(odds)
    assert [p["price"] for p in s["home"]] == [2.0, 1.9]
    assert s["draw"] == [] and s["away"] == []


def test_books_table_sorted_by_margin_and_marks_ours():
    books = pd.DataFrame({"bookmaker_key": ["a"] * 3 + ["onexbet"] * 3 + ["c"] * 2,
                          "bookmaker_title": ["A"] * 3 + ["1xBet"] * 3 + ["C"] * 2,
                          "side": ["home", "draw", "away"] * 2 + ["home", "draw"],
                          "price": [1.9, 3.3, 3.8, 2.0, 3.5, 4.0, 2.1, 3.6]})
    t = books_table(books, "onexbet")
    assert [b["key"] for b in t] == ["onexbet", "a"]  # incomplete "c" dropped, lower margin first
    assert t[0]["ours"] and not t[1]["ours"]
    assert t[0]["margin"] == pytest.approx(1 / 2.0 + 1 / 3.5 + 1 / 4.0 - 1)


def test_build_match_detail():
    b = frame(bet(1, "2026-10-20", "home", 2.2, 0.02, score=(2, 1)))
    b["home_xg"], b["away_xg"], b["venue"], b["referee"] = 1.8, 0.7, "Stadium", "Ref"
    t = pd.to_datetime(["2026-10-19 10:00"] * 3 + ["2026-10-20 18:00"] * 3)
    pin = pd.DataFrame({"datetime_insert": t, "side": ["home", "draw", "away"] * 2,
                        "price": [2.1, 3.4, 3.6, 1.95, 3.5, 4.0]})
    books = pd.DataFrame({"bookmaker_key": ["onexbet"] * 3, "bookmaker_title": ["1xBet"] * 3,
                          "side": ["home", "draw", "away"], "price": [2.2, 3.3, 3.5]})
    d = build_match_detail(b, pin, books, matches(), NOW)
    assert d["score"] == "2-1" and d["xg"] == [1.8, 0.7] and d["status"] == "won"
    assert d["bet"]["price"] == 2.2 and d["bet"]["clv"] == pytest.approx(2.2 / d["closing_fair_price"]["home"] - 1)
    assert len(d["pinnacle"]["home"]) == 2 and d["books"][0]["ours"]
    assert d["form"]["home"][0]["opponent"] == "A1"


def test_build_match_detail_unknown_bet():
    assert build_match_detail(pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), matches(), NOW) is None

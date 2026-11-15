import datetime

import numpy as np
import pandas as pd
import pytest

from app.services.site_payload import (LIVE_SINCE, START_BANKROLL, bet_table, build_payload, closing_fair, equity_curve,
                                       live_only)

NOW = datetime.datetime(2026, 10, 19, 12, 0)
LATER = datetime.datetime(2026, 11, 15, 12, 0)
NO_CLOSING = pd.DataFrame(columns=["match_id", "side", "price"])


def bet(game, day, side, price, stake, score=None, league="ESP-La Liga", notes=None, time="20:00:00", fair=None, odds_at=None):
    fair = fair or 1 / price * 1.04
    probs = {"home": (fair, 0.25, 0.75 - fair), "draw": (0.4, fair, 0.6 - fair), "away": (0.75 - fair, 0.25, fair)}[side]
    row = {"match_id": f"m{game}", "game": f"g{game}", "sport_key": None, "league": league,
           "datetime_optim": odds_at or f"{day} 10:05:00",
           "date_match": day, "time_match": time, "home_team": f"H{game}", "away_team": f"A{game}",
           "prob_home_win": probs[0], "prob_draw": probs[1], "prob_away_win": probs[2], "notes": notes,
           "home_g": None if score is None else score[0], "away_g": None if score is None else score[1]}
    for s in ("home", "draw", "away"):
        row[f"odds_{s}"] = price if s == side else np.nan
        row[f"f_{s}"] = stake if s == side else 0.0
        row[f"bookmaker_{s}_key"] = "onexbet" if s == side else None
    return row


def frame(*rows):
    return pd.DataFrame(list(rows))


def closing(match_id, home, draw, away):
    return pd.DataFrame({"match_id": [match_id] * 3, "side": ["home", "draw", "away"], "price": [home, draw, away]})


def test_status_and_gain():
    t = bet_table(frame(
        bet(1, "2026-10-10", "home", 2.0, 0.02, score=(2, 1)),
        bet(2, "2026-10-10", "away", 3.0, 0.01, score=(1, 1)),
        bet(3, "2026-10-20", "draw", 3.2, 0.01),
        bet(4, "2026-10-19", "home", 2.5, 0.01, time="08:00:00"),
        bet(5, "2026-10-11", "home", 2.0, 0.01, score=(3, 2), notes="Required Extra Time"),
    ), pd.DataFrame(columns=["match_id", "side", "price"]), NOW).set_index("game")
    assert t.loc["g1", "status"] == "won" and t.loc["g1", "gain"] == pytest.approx(0.02)
    assert t.loc["g2", "status"] == "lost" and t.loc["g2", "gain"] == pytest.approx(-0.01)
    assert t.loc["g3", "status"] == "upcoming"
    assert t.loc["g4", "status"] == "pending"  # kicked off, not settled yet
    assert t.loc["g5", "status"] == "void" and t.loc["g5", "gain"] == 0


def test_closing_line_value_uses_shin_fair_price():
    c = closing("m1", 1.9, 3.6, 4.4)
    fair = closing_fair(c)
    assert fair.loc["m1"].sum() == pytest.approx(1)
    t = bet_table(frame(bet(1, "2026-10-10", "home", 2.1, 0.02, score=(1, 0))), c, NOW)
    assert t.loc[0, "clv"] == pytest.approx(2.1 * fair.loc["m1", "home"] - 1)


def test_closing_ignores_incomplete_or_invalid_prices():
    c = pd.DataFrame({"match_id": ["m1", "m1", "m2", "m2", "m2"], "side": ["home", "draw", "home", "draw", "away"],
                      "price": [2.0, 3.0, 1.0, 3.0, 4.0]})
    assert closing_fair(c).empty


def test_equity_compounds_daily_and_starts_at_bankroll():
    t = bet_table(frame(
        bet(1, "2026-10-10", "home", 2.0, 0.10, score=(1, 0)),
        bet(2, "2026-10-10", "home", 2.0, 0.10, score=(0, 1)),
        bet(3, "2026-10-11", "home", 3.0, 0.10, score=(2, 0)),
    ), pd.DataFrame(columns=["match_id", "side", "price"]), NOW)
    eq = equity_curve(t)
    assert eq["bankroll"].tolist() == pytest.approx([START_BANKROLL, START_BANKROLL, START_BANKROLL * 1.2])


def test_start_bankroll_is_the_fictitious_10k():
    assert START_BANKROLL == 10000


def test_payload_kpis_and_breakdowns():
    p = build_payload(frame(
        bet(1, "2026-10-20", "home", 2.0, 0.05, score=(1, 0)),
        bet(2, "2026-10-22", "away", 3.2, 0.05, score=(1, 0), league="GER-Bundesliga"),
        bet(3, "2026-11-01", "draw", 3.0, 0.05, score=(0, 0)),
        bet(4, "2026-11-25", "home", 2.2, 0.01),
    ), closing("m1", 2.1, 3.4, 3.6), LATER)
    k = p["kpis"]
    assert p["start_bankroll"] == 10000
    assert k["bets"] == 3 and k["win_rate"] == pytest.approx(2 / 3)
    assert k["bankroll"] == pytest.approx(10000 * 1.05 * 0.95 * 1.10)
    assert k["return"] == pytest.approx(1.05 * 0.95 * 1.10 - 1)
    assert k["max_drawdown"] == pytest.approx(-0.05)
    assert k["clv_coverage"] == pytest.approx(1 / 3)
    assert k["since"] == "2026-10-20"
    assert p["equity"][0] == {"day": "2026-10-19", "bankroll": 10000}
    assert [m["month"] for m in p["monthly"]] == ["2026-10", "2026-11"]
    assert p["monthly"][0]["return"] == pytest.approx(1.05 * 0.95 - 1)
    assert [x["name"] for x in p["by_odds"]] == ["2.00 – 2.49", "≥ 3.00"]
    assert {x["name"] for x in p["by_league"]} == {"LaLiga", "Bundesliga"}
    laliga = next(x for x in p["by_league"] if x["name"] == "LaLiga")
    assert laliga["profit"] == pytest.approx((0.05 + 0.10) * 10000)  # flat, on the 10 000 € base
    assert [b["home"] for b in p["bets"]] == ["H1", "H2", "H3", "H4"]  # by recommendation time
    assert [b["status"] for b in p["bets"]] == ["won", "lost", "won", "upcoming"]
    assert p["bets"][0]["league_key"] == "soccer_spain_la_liga" and p["bets"][1]["league_key"] == "soccer_germany_bundesliga"
    assert "published" not in p["bets"][0]  # every public bet is a live one


def test_replayed_bets_never_reach_the_payload():
    """Bets recommended before LIVE_SINCE were replayed: no bet row, equity, KPI or breakdown counts them."""
    replayed = [
        bet(1, "2026-09-10", "home", 2.0, 0.05, score=(1, 0)),
        bet(2, "2026-10-18", "away", 3.2, 0.05, score=(0, 1), league="GER-Bundesliga"),
        # recommended the day before LIVE_SINCE for a match played after it: still replayed
        bet(3, "2026-10-20", "home", 2.5, 0.05, score=(2, 0), odds_at="2026-10-18 23:59:59"),
    ]
    live = [
        bet(10, "2026-10-19", "home", 2.0, 0.02, score=(0, 1), odds_at=f"{LIVE_SINCE:%Y-%m-%d} 00:00:00"),
        bet(11, "2026-10-21", "draw", 3.0, 0.02, score=(1, 1)),
        bet(12, "2026-11-20", "away", 2.4, 0.01),
    ]
    p = build_payload(frame(*replayed, *live), closing("m1", 2.1, 3.4, 3.6), LATER)
    assert [b["home"] for b in p["bets"]] == ["H10", "H11", "H12"]
    k = p["kpis"]
    assert k["bets"] == 2 and k["win_rate"] == pytest.approx(0.5)
    assert k["clv"] is None and k["clv_coverage"] == 0  # m1 closing belongs to a replayed bet
    assert k["since"] == "2026-10-19"
    assert p["equity"][0]["bankroll"] == START_BANKROLL and p["equity"][0]["day"] == "2026-10-18"
    assert k["bankroll"] == pytest.approx(START_BANKROLL * 0.98 * 1.04)
    assert [m["month"] for m in p["monthly"]] == ["2026-10"]
    assert {x["name"] for x in p["by_league"]} == {"LaLiga"}
    assert sum(x["bets"] for x in p["by_odds"]) == 2
    assert p["clv_series"] == []


def test_only_replayed_bets_is_an_empty_record():
    p = build_payload(frame(bet(1, "2026-09-10", "home", 2.0, 0.05, score=(1, 0))), NO_CLOSING, LATER)
    assert p["bets"] == [] and p["kpis"] is None and p["equity"] == []
    assert p["start_bankroll"] == START_BANKROLL


def test_live_only_boundary():
    t = bet_table(frame(
        bet(1, "2026-10-18", "home", 2.0, 0.05, odds_at="2026-10-18 23:59:59"),
        bet(2, "2026-10-19", "home", 2.0, 0.05, odds_at="2026-10-19 00:00:00"),
    ), NO_CLOSING, NOW)
    assert live_only(t)["game"].tolist() == ["g2"]
    assert live_only(pd.DataFrame()).empty


def test_empty_payload():
    p = build_payload(pd.DataFrame(), pd.DataFrame(), NOW)
    assert p["kpis"] is None and p["bets"] == []


def test_only_open_bets_has_no_kpis():
    p = build_payload(frame(bet(1, "2026-10-25", "home", 2.2, 0.01)), NO_CLOSING, NOW)
    assert p["kpis"] is None and len(p["bets"]) == 1


def test_bookmaker_link_attached_to_the_bet_book():
    links = pd.DataFrame({"match_id": ["m1", "m1"], "bookmaker_key": ["onexbet", "williamhill"],
                          "bookmaker_link": ["https://1xbet.example/m1", "https://wh.example/m1"]})
    p = build_payload(frame(bet(1, "2026-10-25", "home", 2.2, 0.01)), pd.DataFrame(columns=["match_id", "side", "price"]),
                      NOW, links)
    assert p["bets"][0]["link"] == "https://1xbet.example/m1"
    p = build_payload(frame(bet(1, "2026-10-25", "home", 2.2, 0.01)), pd.DataFrame(columns=["match_id", "side", "price"]), NOW)
    assert p["bets"][0]["link"] is None

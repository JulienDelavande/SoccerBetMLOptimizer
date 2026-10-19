import numpy as np
import pandas as pd
import pytest

from optibet_lib.betting import blend_with_model, devig, kelly_stakes, select_value_bets


def test_devig_removes_margin_and_keeps_ranking():
    prices = np.array([[2.0, 3.5, 4.0]])
    implied = 1 / prices[0]
    np.testing.assert_allclose(devig(prices, "proportional")[0], implied / implied.sum())
    p = devig(prices)  # Shin by default
    assert p.sum() == pytest.approx(1)
    assert p[0, 0] > p[0, 1] > p[0, 2]


def test_shin_moves_margin_onto_the_longshot():
    prices = np.array([[1.30, 5.50, 11.0]])
    prop, shin = devig(prices, "proportional")[0], devig(prices, "shin")[0]
    assert shin[0] > prop[0]        # favourite gets more probability
    assert shin[2] < prop[2]        # longshot gets less
    np.testing.assert_allclose(devig(np.array([[2.0, 4.0, 4.0]]) * 1.0, "shin").sum(), 1)


def test_devig_rejects_invalid_prices():
    with pytest.raises(ValueError):
        devig(np.array([[1.0, 3.0, 4.0]]))


def test_blend_weight_zero_is_market_and_nan_model_keeps_market():
    market = np.array([[0.5, 0.3, 0.2], [0.4, 0.3, 0.3]])
    model = np.array([[0.6, 0.2, 0.2], [np.nan, np.nan, np.nan]])
    np.testing.assert_allclose(blend_with_model(market, model, 0.0), market)
    b = blend_with_model(market, model, 0.1)
    np.testing.assert_allclose(b[1], market[1])
    assert b[0].sum() == pytest.approx(1)
    assert market[0, 0] < b[0, 0] < model[0, 0]


def test_select_keeps_best_edge_per_game_and_applies_filters():
    c = pd.DataFrame([
        ("g1", "onexbet", "home", 2.20, 0.50),   # edge 0.10
        ("g1", "betsson", "home", 2.10, 0.50),   # edge 0.05
        ("g1", "onexbet", "draw", 3.50, 0.30),   # edge 0.05
        ("g2", "onexbet", "away", 8.00, 0.20),   # edge 0.60 but price above cap
        ("g3", "onexbet", "home", 2.00, 0.505),  # edge 0.01 below min edge
    ], columns=["game", "book", "side", "price", "p"])
    bets = select_value_bets(c, min_edge=0.02, max_price=3.5)
    assert bets[["game", "book", "side"]].values.tolist() == [["g1", "onexbet", "home"]]
    assert bets["edge"].iloc[0] == pytest.approx(0.10)


def test_kelly_fraction_caps_and_total_scaling():
    # p=0.5 at 2.2: full Kelly = 0.1/1.2 = 0.0833
    assert kelly_stakes([0.5], [2.2], 0.25, 0.05, 0.3)[0] == pytest.approx(0.25 * 0.1 / 1.2)
    assert kelly_stakes([0.9], [2.2], 1.0, 0.05, 0.3)[0] == pytest.approx(0.05)
    f = kelly_stakes([0.9] * 10, [2.2] * 10, 1.0, 0.05, 0.3)
    assert f.sum() == pytest.approx(0.3)
    assert (kelly_stakes([0.4], [2.2], 0.25, 0.05, 0.3) == 0).all()  # negative edge -> no stake


def _odds(rows):
    """rows: (match_id, book, home, draw, away, updated) -> long odds frame as read from the DB."""
    out = []
    for mid, book, h, d, a, upd in rows:
        for side, price in (("home", h), ("draw", d), ("away", a)):
            out.append({"match_id": mid, "sport_key": "soccer_epl", "commence_time": pd.Timestamp("2026-10-20 19:00"),
                        "home_team": f"H{mid}", "away_team": f"A{mid}", "book": book, "side": side, "price": price,
                        "updated": pd.Timestamp(upd)})
    return pd.DataFrame(out)


PARAMS = dict(books=["onexbet"], min_edge=0.02, max_price=3.5, kelly_fraction=0.25, max_stake=0.05,
              max_total=0.30, blend_weight=0.0, fresh_hours=6)


def test_compute_value_bets_end_to_end():
    from optibet_lib.betting import compute_value_bets
    odds = _odds([
        ("m1", "pinnacle", 2.00, 3.60, 4.00, "2026-10-19 11:00"),   # fair home ~0.488
        ("m1", "onexbet", 2.20, 3.40, 3.70, "2026-10-19 10:30"),    # home edge ~ +7%
        ("m2", "pinnacle", 1.80, 3.80, 4.80, "2026-10-19 11:00"),
        ("m2", "onexbet", 1.70, 3.70, 4.60, "2026-10-19 10:30"),    # no value
        ("m3", "pinnacle", 2.00, 3.60, 4.00, "2026-10-19 11:00"),
        ("m3", "onexbet", 2.40, 3.40, 3.70, "2026-10-18 20:00"),    # value but stale (15h behind)
        ("m4", "onexbet", 3.00, 3.00, 3.00, "2026-10-19 11:00"),    # no Pinnacle line
    ])
    bets = compute_value_bets(odds, None, **PARAMS)
    assert bets["match_id"].tolist() == ["m1"]
    row = bets.iloc[0]
    assert row["side"] == "home" and row["book"] == "onexbet" and row["price"] == 2.20
    assert 0 < row["stake"] <= 0.05
    assert row["edge"] == pytest.approx(row["fair_home"] * 2.20 - 1)


def test_compute_value_bets_skips_already_recommended_and_blends_model():
    from optibet_lib.betting import compute_value_bets
    odds = _odds([("m1", "pinnacle", 2.00, 3.60, 4.00, "2026-10-19 11:00"),
                  ("m1", "onexbet", 2.20, 3.40, 3.70, "2026-10-19 10:30")])
    assert compute_value_bets(odds, None, already=["m1"], **PARAMS).empty
    model = pd.DataFrame([{"game": "x", "date_match": pd.Timestamp("2026-10-20").date(), "home_team": "Hm1",
                           "away_team": "Am1", "datetime_inference": pd.Timestamp("2026-10-19"),
                           "prob_home_win": 0.30, "prob_draw": 0.30, "prob_away_win": 0.40}])
    base = compute_value_bets(odds, None, **PARAMS)
    blended = compute_value_bets(odds, model, **{**PARAMS, "blend_weight": 0.5})
    # A pessimistic model lowers the home probability, so the edge shrinks (or disappears).
    assert blended.empty or blended.iloc[0]["edge"] < base.iloc[0]["edge"]


def test_empty_books_uses_all_soft_books_but_excludes_exchanges():
    from optibet_lib.betting import compute_value_bets
    odds = _odds([
        ("m1", "pinnacle", 2.00, 3.60, 4.00, "2026-10-19 11:00"),       # fair home ~0.488
        ("m1", "williamhill", 2.20, 3.40, 3.70, "2026-10-19 10:30"),    # value at a book not in the default list
        ("m2", "pinnacle", 2.00, 3.60, 4.00, "2026-10-19 11:00"),
        ("m2", "betfair_ex_eu", 2.60, 3.40, 3.70, "2026-10-19 10:30"),  # big value but it's an exchange
    ])
    # Default config (1xbet only) finds nothing here.
    assert compute_value_bets(odds, None, **{**PARAMS, "books": ["onexbet"]}).empty
    # Empty list = every soft book: William Hill is picked, the exchange is ignored.
    bets = compute_value_bets(odds, None, **{**PARAMS, "books": []})
    assert bets["match_id"].tolist() == ["m1"] and bets.iloc[0]["book"] == "williamhill"

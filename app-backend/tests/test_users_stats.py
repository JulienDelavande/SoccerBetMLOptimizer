import datetime

import pandas as pd
import pytest

from app.services.users import RISK_PRESETS, stats_from_ledger


def bet(status, gain, stake, day):
    return {"match_id": f"m{day}", "side": "home", "recommended_price": 2.0, "placed_price": 2.0,
            "stake": stake, "status": status, "settled_gain": gain,
            "created_at": datetime.datetime(2026, 10, day, 12, 0)}


def test_risk_presets_map_to_kelly_fractions():
    assert RISK_PRESETS == {"prudent": 0.25, "balanced": 0.5, "aggressive": 1.0}


def test_stats_empty_ledger():
    s = stats_from_ledger(pd.DataFrame(columns=["status", "settled_gain", "stake", "created_at"]))
    assert s["bets"] == 0 and s["settled"] == 0 and s["roi"] is None and s["equity"] == []


def test_stats_from_settled_bets():
    df = pd.DataFrame([
        bet("won", 10.0, 10.0, 1),
        bet("lost", -10.0, 10.0, 2),
        bet("won", 20.0, 10.0, 3),
        {"match_id": "mx", "side": "draw", "recommended_price": 3.0, "placed_price": None, "stake": None,
         "status": "placed", "settled_gain": None, "created_at": datetime.datetime(2026, 10, 4, 12, 0)},
    ])
    s = stats_from_ledger(df)
    assert s["bets"] == 4 and s["settled"] == 3
    assert s["bankroll_delta"] == 20.0
    assert s["roi"] == pytest.approx(20.0 / 30.0)
    assert s["win_rate"] == pytest.approx(2 / 3)
    assert [p["delta"] for p in s["equity"]] == [10.0, 0.0, 20.0]  # cumulative


def test_ledger_records_is_json_safe():
    import datetime as dt

    import numpy as np
    from app.services.users import ledger_records

    df = pd.DataFrame([
        {"match_id": "m1", "side": "home", "stake": 5.0, "settled_gain": np.nan,
         "created_at": dt.datetime(2026, 10, 20, 12, 0), "commence_time": pd.Timestamp("2026-10-21 19:00"),
         "home_team": "A", "away_team": "B"},
    ])
    rec = ledger_records(df)[0]
    assert rec["settled_gain"] is None
    assert rec["created_at"] == "2026-10-20T12:00:00"
    assert rec["commence_time"] == "2026-10-21T19:00:00"
    import json
    json.dumps(rec)  # must not raise

import datetime

import pandas as pd
import pytest

from app.services.team_charts import elo_history, elo_series, xg_series

D = datetime.date


def test_elo_history_is_pre_match_and_moves_with_results():
    m = pd.DataFrame([
        {"date": D(2026, 1, 1), "home": "A", "away": "B", "home_g": 3, "away_g": 0},
        {"date": D(2026, 1, 8), "home": "B", "away": "A", "home_g": 0, "away_g": 1},
        {"date": D(2026, 1, 15), "home": "A", "away": "C", "home_g": None, "away_g": None},  # unplayed
    ])
    h = elo_history(m)
    a = h[h["team"] == "A"]["elo"].tolist()
    assert a[0] == 1500 and a[1] > 1500  # rating before the 2nd match includes the 1st win
    assert len(h) == 4  # unplayed match not in the history
    b = elo_series(h, "B", D(2026, 1, 1), D(2026, 1, 31))
    assert [p["d"] for p in b] == ["2026-01-01", "2026-01-08"] and b[1]["v"] < 1500


def test_xg_series_rolling_from_team_view():
    m = pd.DataFrame([
        {"date": D(2026, 1, i), "home": "A" if i % 2 else "X", "away": "X" if i % 2 else "A",
         "home_xg": float(i), "away_xg": 1.0} for i in range(1, 6)
    ])
    s = xg_series(m, "A", D(2026, 2, 1), window=3)
    # A's xG for: 1 (home), 1 (away), 3 (home), 1 (away), 5 (home)
    assert [p["for"] for p in s] == [pytest.approx(5 / 3, abs=0.01), pytest.approx(5 / 3, abs=0.01), pytest.approx(3.0)]
    assert xg_series(m, "Z", D(2026, 2, 1)) == []


def test_xg_series_hidden_when_stale():
    m = pd.DataFrame([{"date": D(2025, 1, i), "home": "A", "away": "X", "home_xg": 1.0, "away_xg": 1.0} for i in range(1, 6)])
    assert xg_series(m, "A", D(2025, 2, 1), window=3) != []
    assert xg_series(m, "A", D(2025, 9, 1), window=3) == []

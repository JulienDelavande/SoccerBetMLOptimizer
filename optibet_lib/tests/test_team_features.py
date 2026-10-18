import datetime

import numpy as np
import pandas as pd
import pytest

from optibet_lib.feature_eng.format_df import add_signals, format_sofifa_fbref_data
from optibet_lib.feature_eng.team_stats import form_stats

STOP = datetime.datetime(2025, 3, 1)
RATING_COLS = [
    'elo_home_before', 'elo_away_before', 'elo_diff_before',
    'glicko2_home_before', 'glicko2_away_before',
    'trueskill_home_before', 'trueskill_away_before',
    'home_form_ppg', 'away_form_ppg', 'home_form_gd', 'away_form_gd',
]


def matches():
    """Four played matches in February, one fixture in March (no score)."""
    rows = [
        ("2025-02-01", "A", "B", 2, 0),
        ("2025-02-08", "B", "C", 1, 1),
        ("2025-02-15", "C", "A", 0, 3),
        ("2025-02-22", "A", "C", 1, 0),
        ("2025-03-05", "B", "A", None, None),
    ]
    df = pd.DataFrame(rows, columns=["date", "home_team", "away_team", "home_g", "away_g"])
    df["date"] = pd.to_datetime(df["date"])
    df["time"] = pd.NaT
    df["score"] = [f"{h}–{a}" if h is not None else None for _, _, _, h, a in rows]
    df["season"] = "2425"
    df["game"] = df["date"].dt.strftime("%Y-%m-%d") + " " + df["home_team"] + "-" + df["away_team"]
    return df


def signals(df):
    formatted = format_sofifa_fbref_data(df.copy(), datetime_stop=STOP)
    return add_signals(formatted, datetime_stop=STOP).set_index("game")


def test_formatting_needs_no_sofifa_columns_and_keeps_fixtures():
    formatted = format_sofifa_fbref_data(matches(), datetime_stop=STOP)
    assert len(formatted) == 5
    assert formatted["FTR"].tolist()[:4] == [1, 0, -1, 1]
    assert pd.isna(formatted["FTR"].iloc[4])


def test_ratings_do_not_depend_on_row_order():
    ordered = signals(matches())
    shuffled = signals(matches().sample(frac=1, random_state=3))
    pd.testing.assert_frame_equal(
        ordered.loc[ordered.index, RATING_COLS], shuffled.loc[ordered.index, RATING_COLS]
    )


def test_fixture_gets_current_ratings_not_init_values():
    df = signals(matches())
    fixture = df.loc["2025-03-05 B-A"]
    assert fixture["trueskill_home_before"] != 0
    assert fixture["trueskill_away_before"] != 0
    # A won all three of its matches: its Elo is above B's, which lost one.
    assert fixture["elo_away_before"] > fixture["elo_home_before"]
    assert fixture["elo_diff_before"] == pytest.approx(fixture["elo_home_before"] - fixture["elo_away_before"])
    assert not df[RATING_COLS].isna().any().any()


def test_features_only_use_earlier_matches():
    base = signals(matches())
    altered = matches()
    altered.loc[altered["date"] == "2025-02-22", ["home_g", "away_g", "score"]] = [0, 4, "0–4"]
    changed = signals(altered)
    earlier = [g for g in base.index if g < "2025-02-22"]
    pd.testing.assert_frame_equal(base.loc[earlier, RATING_COLS], changed.loc[earlier, RATING_COLS])
    assert base.loc["2025-03-05 B-A", "elo_away_before"] != changed.loc["2025-03-05 B-A", "elo_away_before"]


def test_form_window_and_values():
    df = pd.DataFrame({
        "home_team": ["A", "A", "A", "A"],
        "away_team": ["B", "C", "D", "E"],
        "home_g": [1, 0, 2, np.nan],
        "away_g": [0, 0, 3, np.nan],
        "datetime": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]),
    })
    form_stats(df, window=2)
    assert df["home_form_ppg"].tolist() == [0, 3, 2, 0.5]   # last two before match 4: draw, loss
    assert df["home_form_gd"].tolist() == [0, 1, 0.5, -0.5]
    assert df["away_form_ppg"].tolist() == [0, 0, 0, 0]

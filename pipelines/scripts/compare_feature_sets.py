"""Compare the SoFIFA feature set with the FBref-only (Elo/form) feature set.

Season-by-season walk-forward: for each test season, both models train on every
earlier match of their own dataset and are scored on the SAME test matches
(intersection by game), so the comparison isolates the feature set.

Usage: DATABASE_URL=postgresql://... python compare_feature_sets.py [--cutoff 2025-11-01]
"""
import argparse
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.pipeline__RSF_PR_LR.utils.test_model_and_infer import FEATURES as NEW_FEATURES  # noqa: E402
from optibet_lib.feature_eng.format_df import add_signals, format_sofifa_fbref_data  # noqa: E402

SOFIFA_FEATURES = [
    'home_overall', 'home_attack', 'home_midfield', 'home_defence', 'home_transfer_budget', 'home_club_worth',
    'home_defence_domestic_prestige', 'home_international_prestige', 'home_players', 'home_starting_xi_average_age',
    'home_whole_team_average_age', 'away_overall', 'away_attack', 'away_midfield', 'away_defence',
    'away_transfer_budget', 'away_club_worth', 'away_defence_domestic_prestige', 'away_international_prestige',
    'away_players', 'away_starting_xi_average_age', 'away_whole_team_average_age']
OLD_SCORES = [
    'home_team_number_of_match_played', 'away_team_number_of_match_played',
    'glicko2_home_before', 'glicko2_away_before', 'glicko2_rd_home_before', 'glicko2_rd_away_before',
    'glicko2_vol_home_before', 'glicko2_vol_away_before', 'trueskill_home_before', 'trueskill_away_before']
OLD_FEATURES = SOFIFA_FEATURES + OLD_SCORES
CLASSES = [-1, 0, 1]
TEST_SEASON_STARTS = ["2021-07-01", "2022-07-01", "2023-07-01", "2024-07-01", "2025-07-01"]

FBREF_QUERY = """
SELECT m.*, th.canonical_name AS home_team_canonical_name, ta.canonical_name AS away_team_canonical_name
FROM mv_fbref_matches_norm_2006 m
JOIN teams th ON th.team_id = m.home_team_id
JOIN teams ta ON ta.team_id = m.away_team_id
ORDER BY m.match_ts, m.game
"""


def build(df, cutoff, dropna_cols):
    df["home_team"] = df["home_team_canonical_name"]
    df["away_team"] = df["away_team_canonical_name"]
    df = format_sofifa_fbref_data(df, datetime_stop=cutoff, dropna_cols=dropna_cols)
    df = add_signals(df, datetime_stop=cutoff)
    return df[df["datetime"] < cutoff].dropna(subset=["FTR"]).set_index("game")


def ece_top_label(proba, y, bins=10):
    conf = proba.max(axis=1)
    correct = (np.array(CLASSES)[proba.argmax(axis=1)] == y).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (conf > lo) & (conf <= hi)
        if mask.any():
            ece += mask.mean() * abs(correct[mask].mean() - conf[mask].mean())
    return ece


def scores(proba, y):
    onehot = (y[:, None] == np.array(CLASSES)[None, :]).astype(float)
    return {
        "log_loss": log_loss(y, proba, labels=CLASSES),
        "brier": float(((proba - onehot) ** 2).sum(axis=1).mean()),
        "accuracy": accuracy_score(y, np.array(CLASSES)[proba.argmax(axis=1)]),
        "ece": ece_top_label(proba, y),
    }


def fit_predict(train, test, features):
    model = Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=1000))])
    model.fit(train[features], train["FTR"].astype(int))
    return model.predict_proba(test[features])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoff", default="2025-11-01")
    args = parser.parse_args()
    cutoff = pd.Timestamp(args.cutoff).to_pydatetime()

    engine = create_engine(os.environ["DATABASE_URL"])
    t0 = time.time()
    with engine.connect() as conn:
        old_raw = pd.read_sql(text("SELECT * FROM v_matches_enrichis"), conn)
        new_raw = pd.read_sql(text(FBREF_QUERY), conn)
    print(f"loaded sofifa-joined={len(old_raw)} fbref-all={len(new_raw)} rows in {time.time() - t0:.0f}s", flush=True)

    t0 = time.time()
    old = build(old_raw, cutoff, dropna_cols=["home_overall", "away_overall"])
    new = build(new_raw, cutoff, dropna_cols=())
    print(f"features built in {time.time() - t0:.0f}s: old={len(old)} new={len(new)} played matches", flush=True)

    rows = []
    starts = [pd.Timestamp(s) for s in TEST_SEASON_STARTS] + [pd.Timestamp(cutoff)]
    for start, end in zip(starts[:-1], starts[1:]):
        common = old.index[(old["datetime"] >= start) & (old["datetime"] < end)].intersection(new.index)
        if len(common) < 50:
            continue
        y = new.loc[common, "FTR"].astype(int).to_numpy()
        old_train, new_train = old[old["datetime"] < start], new[new["datetime"] < start]
        base_rates = new_train["FTR"].astype(int).value_counts(normalize=True).reindex(CLASSES).to_numpy()
        variants = {
            "baseline (class frequencies)": np.tile(base_rates, (len(common), 1)),
            "old: SoFIFA + ratings (32)": fit_predict(old_train, old.loc[common], OLD_FEATURES),
            "new: Elo + form + ratings (17)": fit_predict(new_train, new.loc[common], NEW_FEATURES),
        }
        new_only = new.index[(new["datetime"] >= start) & (new["datetime"] < end)]
        variants_all = {"new, all FBref matches": (fit_predict(new_train, new.loc[new_only], NEW_FEATURES),
                                                   new.loc[new_only, "FTR"].astype(int).to_numpy())}
        season = f"{start.year}-{str(start.year + 1)[2:]}"
        for name, proba in variants.items():
            rows.append({"season": season, "model": name, "n": len(common), **scores(proba, y)})
        for name, (proba, y_all) in variants_all.items():
            rows.append({"season": season, "model": name, "n": len(y_all), **scores(proba, y_all)})
        print(f"season {season} done (common test matches: {len(common)})", flush=True)

    res = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print("\n=== per season ===")
    print(res.round(4).to_string(index=False))
    print("\n=== weighted mean over seasons ===")
    agg = res.groupby("model").apply(
        lambda g: pd.Series({m: np.average(g[m], weights=g["n"]) for m in ["log_loss", "brier", "accuracy", "ece"]} | {"n": g["n"].sum()}),
        include_groups=False)
    print(agg.round(4).to_string())


if __name__ == "__main__":
    main()

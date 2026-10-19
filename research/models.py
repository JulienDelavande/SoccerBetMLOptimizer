"""Walk-forward out-of-sample probabilities for candidate models + market benchmarks.

Each month from --start: every model is fitted on all played matches before the
month and predicts the month (production refits daily, monthly is a close and
cheaper proxy). Output: /work/data/oos.parquet (game, model, p_away, p_draw, p_home).
"""
import argparse
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BASE = [
    'elo_home_before', 'elo_away_before', 'elo_diff_before',
    'glicko2_home_before', 'glicko2_away_before', 'glicko2_rd_home_before', 'glicko2_rd_away_before',
    'glicko2_vol_home_before', 'glicko2_vol_away_before', 'trueskill_home_before', 'trueskill_away_before',
    'home_team_number_of_match_played', 'away_team_number_of_match_played',
    'home_form_ppg', 'away_form_ppg', 'home_form_gd', 'away_form_gd',
]
EXTRA = ['home_xg_for', 'home_xg_against', 'away_xg_for', 'away_xg_against', 'xg_diff_form',
         'home_rest_days', 'away_rest_days']
CLASSES = [-1, 0, 1]


def lr():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))


def hgb():
    from app.pipeline__RSF_PR_LR.utils.test_model_and_infer import make_model
    return make_model()


CANDIDATES = {
    "lr_base": (lr, BASE),            # = production model
    "lr_xg_rest": (lr, BASE + EXTRA),
    "hgb_xg_rest": (hgb, BASE + EXTRA),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="/work/data")
    parser.add_argument("--start", default="2024-08-01")
    args = parser.parse_args()
    df = pd.read_parquet(f"{args.data}/matches.parquet")
    df["datetime"] = pd.to_datetime(df["datetime"])
    played = df.dropna(subset=["FTR"])
    months = pd.date_range(args.start, df["datetime"].max() + pd.offsets.MonthBegin(1), freq="MS")
    out = []
    t0 = time.time()
    for m_start, m_end in zip(months[:-1], months[1:]):
        train = played[played["datetime"] < m_start]
        test = df[(df["datetime"] >= m_start) & (df["datetime"] < m_end)]
        if test.empty:
            continue
        y = train["FTR"].astype(int)
        for name, (factory, feats) in CANDIDATES.items():
            model = factory().fit(train[feats], y)
            p = model.predict_proba(test[feats])
            out.append(pd.DataFrame({"game": test["game"].values, "model": name,
                                     "p_away": p[:, 0], "p_draw": p[:, 1], "p_home": p[:, 2]}))
        print(f"{m_start:%Y-%m}: train={len(train)} test={len(test)} ({time.time() - t0:.0f}s)", flush=True)
    pd.concat(out).to_parquet(f"{args.data}/oos.parquet", index=False)


if __name__ == "__main__":
    main()

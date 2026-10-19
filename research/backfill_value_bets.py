"""Write the production value-bet strategy, replayed on past odds snapshots, into optim_results.

Same rules as pipelines/app/pipeline__VB (Pinnacle Shin fair line at first sighting,
fresh soft prices, edge > 2%, odds <= 3.5, one bet per game, half Kelly capped at 5%
per bet and 30% per day) so the site shows one continuous track record. Games already
recommended live for the label are skipped; reruns are idempotent (same keys).
"""
import argparse
import os

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

import research.backtest_sync as bs
from research.bookmaker_combos import long_table, pick_bets, stakes

SPORT_KEYS = {"ENG-Premier League": "soccer_epl", "ESP-La Liga": "soccer_spain_la_liga",
              "ITA-Serie A": "soccer_italy_serie_a", "GER-Bundesliga": "soccer_germany_bundesliga",
              "FRA-Ligue 1": "soccer_france_ligue_one"}


def build_rows(data, books, label, until, kelly=0.5, max_stake=0.05, max_day=0.30):
    L, fair = long_table(data, with_fair=True)
    c = pick_bets(L, books)
    c = c[pd.to_datetime(c["commence_time"]) < until]
    # One row per match_id: a few fixtures appear under two game strings (name/date variants).
    c = c.drop_duplicates("game").reset_index(drop=True)
    c["stake"] = stakes(c, kelly, max_stake, max_day)
    snaps = pd.read_parquet(f"{data}/snapshots.parquet")
    ids = snaps.drop_duplicates("game").set_index("game")
    league = pd.read_parquet(f"{data}/matches.parquet").set_index("game")["league"]
    kickoff = pd.to_datetime(c["commence_time"])
    p = fair.loc[c["game"]]
    rows = pd.DataFrame({
        "match_id": ids.loc[c["game"], "match_id"].to_numpy(),
        "sport_key": league.reindex(c["game"]).map(SPORT_KEYS).to_numpy(),
        "game": c["game"].to_numpy(), "date_match": kickoff.dt.date, "time_match": kickoff.dt.time,
        "home_team": ids.loc[c["game"], "home_team_canonical"].to_numpy(),
        "away_team": ids.loc[c["game"], "away_team_canonical"].to_numpy(),
        "model": "RSF_PR_LR", "datetime_inference": pd.to_datetime(c["datetime_insert"]),
        "prob_home_win": p["home"].to_numpy(), "prob_draw": p["draw"].to_numpy(), "prob_away_win": p["away"].to_numpy(),
        "datetime_optim": pd.to_datetime(c["datetime_insert"]), "utility_fn": "ValueKelly", "optim_label": label,
    })
    for s in bs.SIDES:
        chosen = (c["side"] == s).to_numpy()
        rows[f"odds_{s}"] = np.where(chosen, c["price"], np.nan)
        rows[f"bookmaker_{s}_key"] = np.where(chosen, c["bookmaker_key"], None)
        rows[f"bookmaker_{s}"] = rows[f"bookmaker_{s}_key"]
        rows[f"f_{s}"] = np.where(chosen, c["stake"], 0.0)
    return rows.drop_duplicates(subset=["match_id", "model", "datetime_inference", "datetime_optim"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/work/data")
    ap.add_argument("--books", nargs="*", default=[], help="empty = every soft book (recommended)")
    ap.add_argument("--label", default="value_pinnacle")
    ap.add_argument("--until", default="2026-10-19", help="live recommendations start here")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    rows = build_rows(args.data, args.books, args.label, pd.Timestamp(args.until))
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as conn:
        live = set(pd.read_sql(text("SELECT DISTINCT game FROM optim_results WHERE optim_label = :l"), conn,
                               params={"l": args.label})["game"])
        rows = rows[~rows["game"].isin(live)]
        print(f"{len(rows)} historical bets ({rows['date_match'].min()} .. {rows['date_match'].max()}), "
              f"{len(live)} games already stored for {args.label}")
        if args.write and len(rows):
            rows.to_sql("optim_results", conn, if_exists="append", index=False)
            print("written")


if __name__ == "__main__":
    main()

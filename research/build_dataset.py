"""Build the research dataset: leakage-free match features + bookmaker odds.

Outputs (parquet, in --out):
- matches.parquet: one row per FBref match (played and upcoming) with pre-match features.
- odds.parquet: one row per (game, bookmaker) with opening and closing 1X2 prices.

Every feature is computed from matches strictly before the row's kickoff, so a
single chronological pass over all data is leakage-free (ratings record the
pre-match value, then update with the result).
"""
import argparse
import os
import time
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from optibet_lib.feature_eng.format_df import add_signals, format_sofifa_fbref_data

MATCHES_SQL = "SELECT * FROM v_matches_fbref"

# Opening = first snapshot we stored; closing = last bookmaker update before kickoff.
ODDS_SQL = """
WITH h2h AS (
  SELECT match_id, commence_time, home_team_canonical, away_team_canonical, bookmaker_key,
         outcome_name, outcome_price, bookmaker_last_update, datetime_insert,
         CASE WHEN outcome_name = home_team THEN 'home' WHEN outcome_name = away_team THEN 'away'
              WHEN outcome_name = 'Draw' THEN 'draw' END AS side
  FROM mv_soccer_odds_normalized
  WHERE market_key = 'h2h' AND bookmaker_last_update < commence_time
),
opening AS (
  SELECT DISTINCT ON (match_id, bookmaker_key, side) match_id, bookmaker_key, side, outcome_price AS price_open
  FROM h2h WHERE side IS NOT NULL ORDER BY match_id, bookmaker_key, side, datetime_insert, bookmaker_last_update
),
closing AS (
  SELECT DISTINCT ON (match_id, bookmaker_key, side) match_id, commence_time, home_team_canonical, away_team_canonical,
         bookmaker_key, side, outcome_price AS price_close, bookmaker_last_update AS close_ts
  FROM h2h WHERE side IS NOT NULL ORDER BY match_id, bookmaker_key, side, bookmaker_last_update DESC, datetime_insert DESC
)
SELECT c.*, o.price_open FROM closing c JOIN opening o USING (match_id, bookmaker_key, side)
"""


# Every stored snapshot of 1X2 prices before kickoff, to rebuild synchronised bet times.
SNAPSHOTS_SQL = """
SELECT match_id, commence_time, home_team_canonical, away_team_canonical, datetime_insert, bookmaker_key,
       bookmaker_last_update,
       CASE WHEN outcome_name = home_team THEN 'home' WHEN outcome_name = away_team THEN 'away'
            WHEN outcome_name = 'Draw' THEN 'draw' END AS side,
       outcome_price AS price
FROM mv_soccer_odds_normalized
WHERE market_key = 'h2h' AND bookmaker_last_update < commence_time AND datetime_insert < commence_time
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="/work/data")
    args = parser.parse_args()
    engine = create_engine(os.environ["DATABASE_URL"])

    t0 = time.time()
    with engine.begin() as conn:
        for mv in ("mv_fbref_matches_norm", "mv_fbref_matches_norm_2006", "mv_soccer_odds_normalized"):
            conn.execute(text(f"REFRESH MATERIALIZED VIEW {mv}"))
        raw = pd.read_sql(text(MATCHES_SQL), conn)
        odds = pd.read_sql(text(ODDS_SQL), conn)
        snaps = pd.read_sql(text(SNAPSHOTS_SQL), conn)
    print(f"loaded {len(raw)} matches, {len(odds)} odds rows in {time.time() - t0:.0f}s", flush=True)

    raw["home_team"], raw["away_team"] = raw["home_team_canonical_name"], raw["away_team_canonical_name"]
    for c in ("home_xg", "away_xg"):
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    # 1X2 settles after 90 minutes: FBref scores include extra time, flag those matches.
    notes = raw["notes"].fillna("").str.lower()
    raw["extra_time"] = notes.str.contains("extra time") | notes.str.contains("penalt")
    df = format_sofifa_fbref_data(raw, datetime_stop=pd.Timestamp.max.to_pydatetime())
    df = add_signals(df, datetime_stop=None)
    df = df.sort_values("datetime", kind="stable").reset_index(drop=True)
    keep = [c for c in df.columns if c not in ("score", "match_report", "notes", "venue", "referee", "attendance")]
    df[keep].to_parquet(f"{args.out}/matches.parquet", index=False)

    wide = odds.pivot_table(index=["match_id", "commence_time", "home_team_canonical", "away_team_canonical", "bookmaker_key"],
                            columns="side", values=["price_open", "price_close"], aggfunc="first")
    wide.columns = [f"{v}_{s}" for v, s in wide.columns]
    wide = wide.reset_index().dropna()
    games = df[["game", "date", "home_team", "away_team"]].copy()
    games["date"] = pd.to_datetime(games["date"])
    wide["kick_date"] = pd.to_datetime(wide["commence_time"]).dt.normalize()
    merged = wide.merge(games, left_on=["home_team_canonical", "away_team_canonical"], right_on=["home_team", "away_team"])
    merged = merged[(merged["kick_date"] - merged["date"]).abs() <= pd.Timedelta(days=1)]
    merged.drop(columns=["home_team", "away_team", "date"]).to_parquet(f"{args.out}/odds.parquet", index=False)
    game_of_match = merged.drop_duplicates("match_id").set_index("match_id")["game"]
    snaps = snaps[snaps["side"].notna() & snaps["match_id"].isin(game_of_match.index)].copy()
    snaps["game"] = snaps["match_id"].map(game_of_match)
    snaps.to_parquet(f"{args.out}/snapshots.parquet", index=False)
    print(f"snapshots: {len(snaps)} rows, {snaps['datetime_insert'].nunique()} batches", flush=True)
    n_odds_matches = wide["match_id"].nunique()
    print(f"matches={len(df)} odds: {n_odds_matches} events, {merged['game'].nunique()} matched to FBref "
          f"({merged['game'].nunique() / n_odds_matches:.1%}), {merged['bookmaker_key'].nunique()} bookmakers; "
          f"total {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()

"""Download football-data.co.uk 1X2 odds (2012-13..2025-26, Big 5) and match them to FBref games.

Team names differ between sources; the mapping is learned by voting on matches
played the same day (±1) with the same score. Output: /work/data/fd_matched.parquet
with the FBref game id, Bet365 / Pinnacle opening (PS) / Pinnacle closing (PSC) /
market max prices.
"""
import argparse
import io
import os
import time
import urllib.request

import numpy as np
import pandas as pd

DIVISIONS = {"E0": "ENG", "SP1": "ESP", "I1": "ITA", "D1": "GER", "F1": "FRA"}
SEASONS = [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in range(2012, 2026)]
PRICE_SETS = {"b365": "B365", "pin_open": "PS", "pin_close": "PSC"}


def fetch(url, cache_path, attempts=6):
    """Download once (cached on disk), retrying the site's frequent 5xx."""
    if os.path.exists(cache_path):
        return open(cache_path, "rb").read()
    for i in range(attempts):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            open(cache_path, "wb").write(raw)
            return raw
        except Exception as e:  # noqa: BLE001 - retry any transient network error
            if i == attempts - 1:
                raise
            time.sleep(5 * (i + 1))


def download(season, div, cache_dir):
    url = f"https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"
    raw = fetch(url, f"{cache_dir}/{season}_{div}.csv")
    df = pd.read_csv(io.BytesIO(raw), encoding="latin-1").dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    out = pd.DataFrame({"season": season, "div": div,
                        "date": pd.to_datetime(df["Date"], format="mixed", dayfirst=True, errors="coerce"),
                        "fd_home": df["HomeTeam"].str.strip(), "fd_away": df["AwayTeam"].str.strip(),
                        "hg": df["FTHG"].astype(int), "ag": df["FTAG"].astype(int)})
    for name, prefix in PRICE_SETS.items():
        for side, s in (("home", "H"), ("draw", "D"), ("away", "A")):
            out[f"{name}_{side}"] = pd.to_numeric(df.get(f"{prefix}{s}"), errors="coerce")
    for side, s in (("home", "H"), ("draw", "D"), ("away", "A")):
        col = f"Max{s}" if f"Max{s}" in df else f"BbMx{s}"
        out[f"max_{side}"] = pd.to_numeric(df.get(col), errors="coerce")
    return out


def learn_names(fd, fb):
    """fd team name -> FBref canonical name, by voting on same-league, same-day (±1), same-score matches.

    Other games with the same score on the same day add noise, so a name is kept when its
    best candidate has at least 5 votes and twice as many as the runner-up.
    """
    votes = []
    for delta in (-1, 0, 1):
        f = fd.assign(key_date=fd["date"] + pd.Timedelta(days=delta), country=fd["div"].map(DIVISIONS))
        j = f.merge(fb, left_on=["country", "key_date", "hg", "ag"], right_on=["country", "date", "home_g", "away_g"])
        votes.append(pd.DataFrame({"fd": j["fd_home"], "fb": j["home_team"]}))
        votes.append(pd.DataFrame({"fd": j["fd_away"], "fb": j["away_team"]}))
    v = pd.concat(votes).value_counts().rename("n").reset_index().sort_values("n", ascending=False)
    top = v.groupby("fd").head(2).assign(rank=lambda x: x.groupby("fd").cumcount())
    first = top[top["rank"] == 0].set_index("fd")
    second = top[top["rank"] == 1].set_index("fd")["n"].reindex(first.index).fillna(0)
    keep = (first["n"] >= 5) & (first["n"] >= 2 * second)
    return first.loc[keep, "fb"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/work/data")
    args = ap.parse_args()
    fd = pd.concat([download(s, d, f"{args.data}/fd_raw") for s in SEASONS for d in DIVISIONS], ignore_index=True).dropna(subset=["date"])
    m = pd.read_parquet(f"{args.data}/matches.parquet")
    fb = m.dropna(subset=["home_g", "away_g"])[["game", "date", "home_team", "away_team", "home_g", "away_g", "league"]].copy()
    fb["date"] = pd.to_datetime(fb["date"]).dt.normalize()
    fb["country"] = m.loc[fb.index, "league"].str[:3]
    fb[["home_g", "away_g"]] = fb[["home_g", "away_g"]].astype(int)
    names = learn_names(fd, fb)
    fd["home_team"], fd["away_team"] = fd["fd_home"].map(names), fd["fd_away"].map(names)
    unmapped = sorted(set(fd.loc[fd["home_team"].isna(), "fd_home"]) | set(fd.loc[fd["away_team"].isna(), "fd_away"]))
    j = fd.dropna(subset=["home_team", "away_team"]).merge(
        fb.drop(columns=["country", "league"]).rename(columns={"date": "fb_date"}), on=["home_team", "away_team"])
    j = j[(j["date"] - j["fb_date"]).abs() <= pd.Timedelta(days=1)]
    j = j[(j["hg"] == j["home_g"]) & (j["ag"] == j["away_g"])].drop_duplicates(["season", "div", "fd_home", "fd_away"])
    j.drop(columns=["fb_date", "home_g", "away_g"]).to_parquet(f"{args.data}/fd_matched.parquet", index=False)
    print(f"football-data rows: {len(fd)}, names mapped: {len(names)}, unmapped: {unmapped[:15]}{'...' if len(unmapped) > 15 else ''}")
    print(f"matched to FBref games: {len(j)} ({len(j) / len(fd):.1%}); with Pinnacle closing: {j['pin_close_home'].notna().sum()}")
    print(j.groupby("season").size().to_string())


if __name__ == "__main__":
    main()

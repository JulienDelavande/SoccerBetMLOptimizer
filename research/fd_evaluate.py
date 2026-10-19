"""14-season validation (2012-13..2025-26, Big 5) on football-data.co.uk odds.

Prices are collected at the same time for Bet365 and Pinnacle opening (PS), so a
"bet at Bet365 when it beats Pinnacle's opening fair line" strategy is realistic;
Pinnacle closing (PSC) gives the closing-line value. Settlement uses the 90' score.
"""
import argparse

import numpy as np
import pandas as pd
from scipy.optimize import brentq

SIDES = ["home", "draw", "away"]
FTR_SIDE = {1: "home", 0: "draw", -1: "away"}


def devig(prices, method):
    q = 1 / prices
    if method == "proportional":
        return q / q.sum(axis=1, keepdims=True)
    out = np.full_like(q, np.nan)
    for i, row in enumerate(q):
        if np.isnan(row).any():
            continue
        if method == "power":
            k = brentq(lambda k: (row ** k).sum() - 1, 0.5, 3.0)
            out[i] = row ** k
        elif method == "shin":
            s = row.sum()
            f = lambda z: (((np.sqrt(z * z + 4 * (1 - z) * row * row / s) - z) / (2 * (1 - z))).sum() - 1)
            z = brentq(f, 0.0, 0.4) if f(0.0) > 0 else 0.0
            out[i] = (np.sqrt(z * z + 4 * (1 - z) * row * row / s) - z) / (2 * (1 - z))
        out[i] /= out[i].sum()
    return out


def log_loss(p, y_idx):
    return float(-np.log(np.clip(p[np.arange(len(p)), y_idx], 1e-12, 1)).mean())


def blend(a, b, w):
    z = np.exp((1 - w) * np.log(a) + w * np.log(np.clip(b, 1e-9, 1)))
    return z / z.sum(axis=1, keepdims=True)


def bankroll(bets, kelly=0.5, max_stake=0.05, max_day=0.30, start=1000.0):
    f = np.clip(kelly * bets["edge"] / (bets["price"] - 1), 0, max_stake).to_numpy()
    day = bets["date"].to_numpy()
    tot = pd.Series(f).groupby(day).transform("sum").to_numpy()
    f = np.where(tot > max_day, f * max_day / tot, f)
    ret = f * np.where(bets["won"], bets["price"] - 1, -1.0)
    daily = pd.Series(ret).groupby(day).sum()
    path = np.cumprod(1 + daily.to_numpy())
    return start * path[-1], 100 * (1 - path / np.maximum.accumulate(path)).max()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/work/data")
    args = ap.parse_args()
    fd = pd.read_parquet(f"{args.data}/fd_matched.parquet")
    oos = pd.read_parquet(f"{args.data}/oos_long.parquet")
    fd = fd.dropna(subset=[f"{k}_{s}" for k in ("b365", "pin_open", "pin_close") for s in SIDES])
    fd = fd[(fd[[f"{k}_{s}" for k in ("b365", "pin_open", "pin_close") for s in SIDES]] > 1).all(axis=1)]
    for m in ("hgb_xg_rest", "lr_base"):
        mm = oos[oos["model"] == m].set_index("game")
        fd = fd.join(mm[["p_home", "p_draw", "p_away"]].rename(columns=lambda c: f"{m}_{c[2:]}"), on="game")
    fd = fd.dropna(subset=["hgb_xg_rest_home"]).sort_values("date").reset_index(drop=True)
    y = np.where(fd["hg"] > fd["ag"], 0, np.where(fd["hg"] == fd["ag"], 1, 2))
    px = {k: fd[[f"{k}_{s}" for s in SIDES]].to_numpy(float) for k in ("b365", "pin_open", "pin_close", "max")}
    P = {
        "pinnacle closing (proportional)": devig(px["pin_close"], "proportional"),
        "pinnacle closing (power)": devig(px["pin_close"], "power"),
        "pinnacle closing (shin)": devig(px["pin_close"], "shin"),
        "pinnacle opening (shin)": devig(px["pin_open"], "shin"),
        "bet365 opening (shin)": devig(px["b365"], "shin"),
        "model hgb_xg_rest": fd[[f"hgb_xg_rest_{s}" for s in SIDES]].to_numpy(),
        "model lr_base": fd[[f"lr_base_{s}" for s in SIDES]].to_numpy(),
    }
    P["blend 10% model + pinnacle opening"] = blend(P["pinnacle opening (shin)"], P["model hgb_xg_rest"], 0.1)
    print(f"games: {len(fd)} ({fd['season'].min()}..{fd['season'].max()})\n")
    rows = [{"source": k, "log_loss": log_loss(v, y)} for k, v in P.items()]
    print("=== accuracy (lower log loss is better) ===")
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    seasons = sorted(fd["season"].unique())
    per = pd.DataFrame({s: {k: log_loss(v[(fd["season"] == s).to_numpy()], y[(fd["season"] == s).to_numpy()])
                            for k, v in P.items() if k in ("pinnacle closing (shin)", "pinnacle opening (shin)", "model hgb_xg_rest")}
                        for s in seasons}).round(3)
    print("\nlog loss per season:"); print(per.to_string())

    close_fair = P["pinnacle closing (shin)"]
    strategies = {
        "VALUE: Bet365 vs Pinnacle opening (shin)": (P["pinnacle opening (shin)"], "b365"),
        "VALUE: Bet365 vs Pinnacle opening (proportional)": (devig(px["pin_open"], "proportional"), "b365"),
        "VALUE + 10% model blend, Bet365": (P["blend 10% model + pinnacle opening"], "b365"),
        "MODEL ONLY (hgb) vs Bet365": (P["model hgb_xg_rest"], "b365"),
        "MODEL ONLY (lr) vs Bet365": (P["model lr_base"], "b365"),
        "VALUE: best market price vs Pinnacle opening (shin)": (P["pinnacle opening (shin)"], "max"),
        "MODEL ONLY (hgb) vs best market price": (P["model hgb_xg_rest"], "max"),
    }
    out, per_season = [], {}
    for name, (p, book) in strategies.items():
        price = px[book]
        if book == "max":
            price = np.where(np.isnan(price), px["b365"], price)
        edge = p * price - 1
        edge[(price > 3.5) | np.isnan(edge)] = -np.inf
        side = edge.argmax(axis=1)
        best = edge[np.arange(len(fd)), side]
        keep = best > 0.02
        b = pd.DataFrame({"date": fd["date"].to_numpy()[keep], "season": fd["season"].to_numpy()[keep],
                          "price": price[np.arange(len(fd)), side][keep], "edge": best[keep],
                          "won": (side == y)[keep],
                          "clv": (price[np.arange(len(fd)), side] * close_fair[np.arange(len(fd)), side] - 1)[keep]})
        r = np.where(b["won"], b["price"] - 1, -1.0)
        se = r.std(ddof=1) / np.sqrt(len(r))
        final, dd = bankroll(b)
        seasons_pos = (b.assign(r=r).groupby("season")["r"].mean() > 0)
        out.append({"strategy": name, "bets": len(b), "roi_per_bet_%": 100 * r.mean(), "t": r.mean() / se,
                    "clv_%": 100 * b["clv"].mean(), "seasons_positive": f"{int(seasons_pos.sum())}/{len(seasons_pos)}",
                    "1000€ half Kelly ->": round(final), "max_dd_%": dd})
        per_season[name] = b.assign(r=r).groupby("season")["r"].mean().mul(100).round(1)
    pd.set_option("display.width", 250)
    print("\n=== strategies, flat ROI per bet (edge>2%, odds<=3.5, one bet per game) ===")
    print(pd.DataFrame(out).round(2).to_string(index=False))
    print("\nROI per bet (%) per season:")
    print(pd.DataFrame(per_season).T.to_string())


if __name__ == "__main__":
    main()

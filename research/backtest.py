"""Bankroll backtest of betting strategies on historical 1X2 odds.

Probability sources (walk-forward, no look-ahead):
- model: walk-forward model probabilities (research/models.py)
- pinnacle: Pinnacle de-vigged probabilities at bet time
- blend: p ∝ p_model^w * p_pinnacle^(1-w), w refitted monthly on past games only

Bets: on each game, each side whose price at the chosen bookmaker(s) gives
EV = p * price - 1 > min_edge. Staking: flat or fractional Kelly with caps.
Bankroll is updated per kickoff day (stakes from the start-of-day bankroll).
"""
import argparse
import itertools

import numpy as np
import pandas as pd

from research.evaluate import CLASSES, P, devig, load

SIDES = ["away", "draw", "home"]


def bet_table(odds, phase):
    """One row per game and bookmaker with prices at bet time (open or close)."""
    cols = {f"price_{phase}_{s}": s for s in SIDES}
    t = odds[["game", "bookmaker_key", "commence_time", *cols]].rename(columns=cols)
    return t.drop_duplicates(["game", "bookmaker_key"])


def pinnacle_probs(table):
    pin = table[table["bookmaker_key"] == "pinnacle"]
    p = devig(pin[SIDES].to_numpy(float))
    return pd.DataFrame(p, columns=P, index=pin["game"].values)


def blend_probs(model, market, played, months):
    """Geometric blend, weight chosen each month by log loss on all earlier games."""
    common = model.index.intersection(market.index)
    lm, lk = np.log(np.clip(model.loc[common, P].to_numpy(), 1e-9, 1)), np.log(market.loc[common, P].to_numpy())
    y = played.reindex(common)["FTR"]
    when = played.reindex(common)["datetime"]
    grid = np.linspace(0, 1, 21)

    def combine(w, a, b):
        z = np.exp(w * a + (1 - w) * b)
        return z / z.sum(axis=1, keepdims=True)

    out, weights = [], {}
    for start, end in zip(months[:-1], months[1:]):
        past = (when < start).to_numpy() & y.notna().to_numpy()
        cur = ((when >= start) & (when < end)).to_numpy()
        if not cur.any():
            continue
        w = 0.0
        if past.sum() >= 300:
            onehot = (y[past].astype(int).to_numpy()[:, None] == CLASSES[None, :])
            losses = [-np.log((combine(g, lm[past], lk[past]) * onehot).sum(axis=1)).mean() for g in grid]
            w = float(grid[int(np.argmin(losses))])
        weights[f"{start:%Y-%m}"] = w
        out.append(pd.DataFrame(combine(w, lm[cur], lk[cur]), columns=P, index=common[cur]))
    return pd.concat(out), weights


def simulate(bets, staking, kelly_frac=0.25, max_stake=0.05, max_day=0.25, flat=0.01):
    """bets: rows with day, p, price, won. Returns stats dict and bankroll path."""
    bank, peak, max_dd, path = 1.0, 1.0, 0.0, []
    staked = profit = 0.0
    n = 0
    for day, g in bets.groupby("day", sort=True):
        if staking == "flat":
            stakes = np.full(len(g), flat)
        else:
            edge = g["p"].to_numpy() * g["price"].to_numpy() - 1
            stakes = np.clip(kelly_frac * edge / (g["price"].to_numpy() - 1), 0, max_stake)
        if stakes.sum() > max_day:
            stakes *= max_day / stakes.sum()
        amounts = stakes * bank
        pnl = np.where(g["won"].to_numpy(), amounts * (g["price"].to_numpy() - 1), -amounts)
        bank += pnl.sum()
        staked += amounts.sum()
        profit += pnl.sum()
        n += len(g)
        peak = max(peak, bank)
        max_dd = max(max_dd, 1 - bank / peak)
        path.append((day, bank))
        if bank <= 0.01:
            break
    return {"bets": n, "final_bankroll": bank, "roi_on_stakes": profit / staked if staked else 0.0,
            "max_drawdown": max_dd}, path


def candidate_bets(probs, table, books, min_edge, max_price, outcomes):
    t = table[table["bookmaker_key"].isin(books)].merge(outcomes, on="game")
    t = t[t["game"].isin(probs.index)]
    rows = []
    for side, pcol, cls in zip(SIDES, P, CLASSES):
        p = probs.loc[t["game"], pcol].to_numpy()
        price = t[side].to_numpy(float)
        rows.append(pd.DataFrame({"game": t["game"].values, "book": t["bookmaker_key"].values, "side": side,
                                  "p": p, "price": price, "won": (t["FTR"].to_numpy() == cls),
                                  "day": pd.to_datetime(t["commence_time"]).dt.normalize().values}))
    c = pd.concat(rows)
    c = c[(c["p"] * c["price"] - 1 > min_edge) & (c["price"] <= max_price)]
    # Best price per game and side across the allowed books, then one side per game (highest EV).
    c = c.sort_values("price", ascending=False).drop_duplicates(["game", "side"])
    c["ev"] = c["p"] * c["price"] - 1
    return c.sort_values("ev", ascending=False).drop_duplicates("game")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="/work/data")
    parser.add_argument("--from", dest="start", default="2025-01-01")
    args = parser.parse_args()
    matches, oos, odds = load(args.data)
    matches["datetime"] = pd.to_datetime(matches["datetime"])
    played = matches.dropna(subset=["FTR"]).set_index("game")[["FTR", "datetime"]]
    played["FTR"] = played["FTR"].astype(int)
    outcomes = played.reset_index()[["game", "FTR"]]
    months = pd.date_range("2024-08-01", "2026-11-01", freq="MS")

    soft = sorted(set(odds["bookmaker_key"]) - {"pinnacle", "betfair_ex_eu", "betfair_ex_uk", "matchbook", "smarkets"})
    book_sets = {"1xbet only": ["onexbet"], "best of soft books": soft}
    rows = []
    for phase in ("close", "open"):
        table = bet_table(odds, phase)
        pin = pinnacle_probs(table)
        sources = {"pinnacle fair": pin}
        for m in ("lr_base", "hgb_xg_rest"):
            model = oos[oos["model"] == m].set_index("game")[P]
            sources[f"model {m}"] = model
            blend, weights = blend_probs(model, pin, played, months)
            sources[f"blend {m}+pinnacle"] = blend
            if phase == "close":
                print(f"blend weights on {m} (share of model): {list(weights.values())[-12:]}")
        for (src, probs), (bname, books), min_edge, staking in itertools.product(
                sources.items(), book_sets.items(), (0.0, 0.02, 0.05), ("flat", "kelly")):
            bets = candidate_bets(probs, table, books, min_edge, 6.0, outcomes)
            bets = bets[bets["day"] >= pd.Timestamp(args.start)]
            if bets.empty:
                continue
            stats, _ = simulate(bets, staking)
            rows.append({"bet_time": phase, "probabilities": src, "books": bname, "min_edge": min_edge,
                         "staking": staking, **stats})
    res = pd.DataFrame(rows)
    res.to_csv(f"{args.data}/backtest.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.sort_values("final_bankroll", ascending=False).round(3).head(25).to_string(index=False))
    print("\nmodel-only strategies (for reference):")
    print(res[res["probabilities"].str.startswith("model")].sort_values("final_bankroll", ascending=False)
          .round(3).head(8).to_string(index=False))


if __name__ == "__main__":
    main()

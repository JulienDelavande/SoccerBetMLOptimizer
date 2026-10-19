"""Realistic value-betting backtest on synchronised odds snapshots.

At a bet time (one ingestion batch), the fair probability of each outcome is
Pinnacle's de-vigged price IN THAT BATCH (optionally blended with the model).
Soft-book prices are taken from the same batch and only if fresh (updated within
`fresh_hours` of Pinnacle's update), so no stale or future price is used.
Matches decided after extra time are not settled (1X2 settles at 90').

Reports bankroll, ROI, drawdown and closing-line value (CLV = price x Pinnacle
closing fair probability - 1), the most reliable edge measure.
"""
import argparse
import itertools

import numpy as np
import pandas as pd

from research.backtest import simulate

SIDES = ["away", "draw", "home"]
EXCHANGES = {"betfair_ex_eu", "betfair_ex_uk", "matchbook", "smarkets", "betfair_sb_uk"}
SIDE_TO_FTR = {"away": -1, "draw": 0, "home": 1}


def batch_prices(snaps):
    """Wide prices per (game, batch, book): price + last update per side."""
    w = snaps.pivot_table(index=["game", "commence_time", "datetime_insert", "bookmaker_key"], columns="side",
                          values=["price", "bookmaker_last_update"], aggfunc="last")
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    return w.reset_index().dropna(subset=[f"price_{s}" for s in SIDES])


def pick_batches(pin, how):
    pin = pin.sort_values("datetime_insert")
    ko = pd.to_datetime(pin["commence_time"])
    if how == "open":
        return pin.groupby("game").head(1)
    if how == "close":
        return pin.groupby("game").tail(1)
    if how == "day_before":
        early = pin[pd.to_datetime(pin["datetime_insert"]) <= ko - pd.Timedelta(hours=18)]
        return early.groupby("game").tail(1)
    raise ValueError(how)


def fair(df):
    inv = 1 / df[[f"price_{s}" for s in SIDES]].to_numpy(float)
    return inv / inv.sum(axis=1, keepdims=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="/work/data")
    parser.add_argument("--from", dest="start", default="2024-09-01")
    parser.add_argument("--fresh-hours", type=float, default=6)
    parser.add_argument("--blend", type=float, default=0.0, help="model weight in the geometric blend with Pinnacle")
    parser.add_argument("--model", default="hgb_xg_rest")
    args = parser.parse_args()

    snaps = pd.read_parquet(f"{args.data}/snapshots.parquet")
    matches = pd.read_parquet(f"{args.data}/matches.parquet")
    settle = matches[matches["FTR"].notna() & ~matches["extra_time"]].set_index("game")["FTR"].astype(int)

    prices = batch_prices(snaps)
    pin = prices[prices["bookmaker_key"] == "pinnacle"]
    close = pick_batches(pin, "close").set_index("game")
    close_fair = pd.DataFrame(fair(close), columns=SIDES, index=close.index)
    soft_books = sorted(set(prices["bookmaker_key"]) - EXCHANGES - {"pinnacle"})
    book_sets = {"1xbet": ["onexbet"], "1xbet+betsson+unibet": ["onexbet", "betsson", "unibet_eu"],
                 "all soft books": soft_books}

    rows, kept = [], {}
    for how in ("open", "day_before", "close"):
        at = pick_batches(pin, how)
        at = at[at["game"].isin(settle.index) & (pd.to_datetime(at["commence_time"]) >= args.start)]
        p_fair = pd.DataFrame(fair(at), columns=SIDES, index=at["game"].values)
        if args.blend > 0:
            oos = pd.read_parquet(f"{args.data}/oos.parquet")
            m = oos[oos["model"] == args.model].set_index("game")[["p_away", "p_draw", "p_home"]]
            m.columns = SIDES
            m = m.reindex(p_fair.index)
            has = m.notna().all(axis=1).to_numpy()
            z = p_fair.to_numpy().copy()
            z[has] = np.exp((1 - args.blend) * np.log(z[has]) + args.blend * np.log(np.clip(m.to_numpy()[has], 1e-9, 1)))
            p_fair = pd.DataFrame(z / z.sum(axis=1, keepdims=True), columns=SIDES, index=p_fair.index)
        pin_upd = at.set_index("game")[[f"bookmaker_last_update_{s}" for s in SIDES]].max(axis=1)
        soft = prices.merge(at[["game", "datetime_insert"]], on=["game", "datetime_insert"])
        soft = soft[soft["bookmaker_key"].isin(soft_books)]
        upd = soft[[f"bookmaker_last_update_{s}" for s in SIDES]].min(axis=1)
        soft = soft[(pd.to_datetime(soft["game"].map(pin_upd)) - pd.to_datetime(upd)) <= pd.Timedelta(hours=args.fresh_hours)]
        long = []
        for s in SIDES:
            t = soft[["game", "commence_time", "bookmaker_key", f"price_{s}"]].rename(columns={f"price_{s}": "price"})
            t["side"] = s
            long.append(t)
        long = pd.concat(long)
        long["p"] = p_fair.lookup(long["game"], long["side"]) if hasattr(p_fair, "lookup") else \
            p_fair.to_numpy()[p_fair.index.get_indexer(long["game"]), [SIDES.index(x) for x in long["side"]]]
        long["ev"] = long["p"] * long["price"] - 1
        cf = close_fair.reindex(long["game"]).to_numpy()
        long["clv"] = long["price"] * cf[np.arange(len(long)), [SIDES.index(x) for x in long["side"]]] - 1
        long["won"] = long["side"].map(SIDE_TO_FTR).to_numpy() == settle.reindex(long["game"]).to_numpy()
        long["day"] = pd.to_datetime(long["commence_time"]).dt.normalize()
        for (bname, books), min_edge, max_price in itertools.product(book_sets.items(), (0.0, 0.02, 0.04, 0.06), (3.5, 6.0)):
            c = long[long["bookmaker_key"].isin(books) & (long["ev"] > min_edge) & (long["price"] <= max_price)]
            c = c.sort_values("ev", ascending=False).drop_duplicates("game")
            if len(c) < 30:
                continue
            clv = c["clv"].to_numpy()
            base = {"bet_time": how, "books": bname, "min_edge": min_edge, "max_price": max_price, "bets": len(c),
                    "avg_ev": c["ev"].mean(), "avg_clv": clv.mean(), "clv_t": clv.mean() / (clv.std() / np.sqrt(len(clv)))}
            for staking, kf in (("flat 1%", None), ("kelly x0.25", 0.25), ("kelly x0.5", 0.5)):
                stats, _ = simulate(c, "flat" if kf is None else "kelly", kelly_frac=kf or 0.25, max_stake=0.05,
                                    max_day=0.30, flat=0.01)
                rows.append({**base, "staking": staking, **stats})
            kept[(how, bname, min_edge, max_price)] = c

    res = pd.DataFrame(rows)
    res.to_csv(f"{args.data}/backtest_sync.csv", index=False)
    pd.set_option("display.width", 260)
    cols = ["bet_time", "books", "min_edge", "max_price", "staking", "bets", "avg_ev", "avg_clv", "clv_t",
            "final_bankroll", "roi_on_stakes", "max_drawdown"]
    print("=== best by final bankroll ===")
    print(res.sort_values("final_bankroll", ascending=False)[cols].round(3).head(20).to_string(index=False))
    print("\n=== 1xbet only, quarter Kelly ===")
    print(res[(res["books"] == "1xbet") & (res["staking"] == "kelly x0.25")][cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()

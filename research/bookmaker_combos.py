"""Which 3 bookmakers? Value bets (Pinnacle Shin fair line, first sighting, edge > 2%,
odds <= 3.5, one bet per game, half Kelly capped) restricted to each 3-book set.

Combos are ranked on the first season (2024-25) and judged on the second (2025-26),
so the choice is not fitted to the period it is scored on. Expected gain uses the
closing-line value (sum of stake x CLV), the realised gain uses actual results.
"""
import argparse
import itertools

import numpy as np
import pandas as pd

import research.backtest_sync as bs
from optibet_lib.betting import devig
from research.simulate_strategies import paths

FR_LICENSED = {"winamax_fr", "betclic_fr", "unibet_fr", "parionssport_fr", "pmu_fr"}
SPLIT = pd.Timestamp("2025-07-01")


def long_table(data):
    snaps = pd.read_parquet(f"{data}/snapshots.parquet")
    matches = pd.read_parquet(f"{data}/matches.parquet")
    settle = matches[matches["FTR"].notna() & ~matches["extra_time"]].set_index("game")["FTR"].astype(int)
    prices = bs.batch_prices(snaps)
    pin = prices[prices["bookmaker_key"] == "pinnacle"]
    cols = [f"price_{s}" for s in bs.SIDES]
    close = bs.pick_batches(pin, "close").set_index("game")
    close_fair = pd.DataFrame(devig(close[cols].to_numpy()), columns=bs.SIDES, index=close.index)
    at = bs.pick_batches(pin, "open")
    at = at[at["game"].isin(settle.index) & at["game"].isin(close_fair.index)
            & (pd.to_datetime(at["commence_time"]) >= "2024-09-01")]
    fair = pd.DataFrame(devig(at[cols].to_numpy()), columns=bs.SIDES, index=at["game"].values)
    pin_upd = at.set_index("game")[[f"bookmaker_last_update_{s}" for s in bs.SIDES]].max(axis=1)
    soft = prices.merge(at[["game", "datetime_insert"]], on=["game", "datetime_insert"])
    soft = soft[~soft["bookmaker_key"].isin(bs.EXCHANGES | {"pinnacle"})]
    upd = soft[[f"bookmaker_last_update_{s}" for s in bs.SIDES]].min(axis=1)
    soft = soft[(pd.to_datetime(soft["game"].map(pin_upd)) - pd.to_datetime(upd)) <= pd.Timedelta(hours=6)]
    rows = []
    for s in bs.SIDES:
        t = soft[["game", "commence_time", "bookmaker_key", f"price_{s}"]].rename(columns={f"price_{s}": "price"})
        rows.append(t.assign(side=s))
    L = pd.concat(rows)
    idx = L["side"].map({s: i for i, s in enumerate(bs.SIDES)}).to_numpy()
    L["p"] = fair.to_numpy()[fair.index.get_indexer(L["game"]), idx]
    L["p_true"] = close_fair.reindex(L["game"]).to_numpy()[np.arange(len(L)), idx]
    L["ev"] = L["p"] * L["price"] - 1
    L["won"] = L["side"].map(bs.SIDE_TO_FTR).to_numpy() == settle.reindex(L["game"]).to_numpy()
    L["day"] = pd.to_datetime(L["commence_time"]).dt.normalize()
    return L[(L["ev"] > 0.02) & (L["price"] <= 3.5)]


def evaluate(L, books, kelly=0.5, max_stake=0.05, max_day=0.30):
    c = L[L["bookmaker_key"].isin(books)].sort_values("ev", ascending=False).drop_duplicates("game")
    c = c.sort_values("day", kind="stable").reset_index(drop=True)
    if c.empty:
        return None
    f = np.clip(kelly * c["ev"].to_numpy() / (c["price"].to_numpy() - 1), 0, max_stake)
    tot = pd.Series(f).groupby(c["day"].to_numpy()).transform("sum").to_numpy()
    f = np.where(tot > max_day, f * max_day / tot, f)
    clv = c["p_true"].to_numpy() * c["price"].to_numpy() - 1
    out = {}
    for name, mask in (("train", c["day"] < SPLIT), ("test", c["day"] >= SPLIT)):
        m = mask.to_numpy()
        if not m.any():
            out.update({f"{name}_bets": 0, f"{name}_exp_gain_%": 0.0, f"{name}_real_gain_%": 0.0, f"{name}_clv_%": np.nan})
            continue
        real = paths(c[m].reset_index(drop=True), f[m], c["won"].to_numpy()[m][None, :])[0][-1]
        out.update({f"{name}_bets": int(m.sum()), f"{name}_clv_%": 100 * clv[m].mean(),
                    f"{name}_exp_gain_%": 100 * (f[m] * clv[m]).sum(), f"{name}_real_gain_%": 100 * (real - 1)})
    rng = np.random.default_rng(0)
    won = rng.random((2000, len(c))) < c["p_true"].to_numpy()[None, :]
    final = paths(c, f, won)[:, -1]
    out.update({"all_bets": len(c), "mc_median_gain_%": 100 * (np.median(final) - 1),
                "mc_loss_prob_%": 100 * (final < 1).mean(),
                "real_gain_%": 100 * (paths(c, f, c["won"].to_numpy()[None, :])[0][-1] - 1)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/work/data")
    ap.add_argument("--min-games", type=int, default=800)
    args = ap.parse_args()
    L = long_table(args.data)
    snaps_cov = pd.read_parquet(f"{args.data}/snapshots.parquet").groupby("bookmaker_key")["game"].nunique()
    books = sorted(b for b in L["bookmaker_key"].unique() if snaps_cov.get(b, 0) >= args.min_games)
    print(f"{len(books)} soft books with >= {args.min_games} games")
    singles = pd.DataFrame([{"books": b, **evaluate(L, [b])} for b in books]).sort_values("train_exp_gain_%", ascending=False)
    trios = pd.DataFrame([{"books": " + ".join(t), "fr_licensed": set(t) <= FR_LICENSED, **evaluate(L, list(t))}
                          for t in itertools.combinations(books, 3)])
    pd.set_option("display.width", 260)
    cols = ["books", "train_bets", "train_clv_%", "train_exp_gain_%", "test_bets", "test_clv_%", "test_exp_gain_%",
            "test_real_gain_%", "mc_median_gain_%", "mc_loss_prob_%", "real_gain_%"]
    print("\n=== single books (ranked on 2024-25) ===")
    print(singles[cols].round(1).head(12).to_string(index=False))
    top = trios.sort_values("train_exp_gain_%", ascending=False)
    print(f"\n=== best 10 trios chosen on 2024-25, judged on 2025-26 (of {len(trios)}) ===")
    print(top[cols].round(1).head(10).to_string(index=False))
    print("\n=== French-licensed trios ===")
    print(top[top["fr_licensed"]][cols].round(1).to_string(index=False))
    print("\n=== reference: 1xbet only ===")
    print(singles[singles["books"] == "onexbet"][cols].round(1).to_string(index=False))
    trios.to_csv(f"{args.data}/trios.csv", index=False)


if __name__ == "__main__":
    main()

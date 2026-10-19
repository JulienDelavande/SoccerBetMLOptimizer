"""Compare betting strategies on our two seasons of odds, in euros.

For each strategy: the realised result (actual match outcomes) and a Monte Carlo
range where every bet's outcome is redrawn from Pinnacle's closing fair
probabilities (the best estimate of the true odds), separating edge from luck.
Stakes are fractions of the start-of-day bankroll, so the final bankroll is the
product of daily returns (vectorised over draws).
"""
import argparse

import numpy as np
import pandas as pd

import research.backtest_sync as bs

SOFT_EXCLUDED = bs.EXCHANGES | {"pinnacle"}
SIDE_IDX = {s: i for i, s in enumerate(bs.SIDES)}


class Data:
    def __init__(self, path):
        snaps = pd.read_parquet(f"{path}/snapshots.parquet")
        matches = pd.read_parquet(f"{path}/matches.parquet")
        oos = pd.read_parquet(f"{path}/oos.parquet")
        self.settle = matches[matches["FTR"].notna() & ~matches["extra_time"]].set_index("game")["FTR"].astype(int)
        self.prices = bs.batch_prices(snaps)
        self.pin = self.prices[self.prices["bookmaker_key"] == "pinnacle"]
        close = bs.pick_batches(self.pin, "close").set_index("game")
        self.close_fair = pd.DataFrame(bs.fair(close), columns=bs.SIDES, index=close.index)
        self.model = oos[oos["model"] == "hgb_xg_rest"].set_index("game")[["p_away", "p_draw", "p_home"]]
        self.model.columns = bs.SIDES
        self.soft_books = sorted(set(self.prices["bookmaker_key"]) - SOFT_EXCLUDED)

    def candidates(self, bet_time, books, source, blend, start, fresh_hours=6):
        at = bs.pick_batches(self.pin, bet_time)
        at = at[at["game"].isin(self.settle.index) & at["game"].isin(self.close_fair.index)
                & (pd.to_datetime(at["commence_time"]) >= start)]
        pin_p = pd.DataFrame(bs.fair(at), columns=bs.SIDES, index=at["game"].values)
        if source == "model":
            p = self.model.reindex(pin_p.index)
        else:
            p = pin_p.copy()
            if blend > 0:
                m = self.model.reindex(p.index)
                ok = m.notna().all(axis=1).to_numpy()
                z = p.to_numpy().copy()
                z[ok] = np.exp((1 - blend) * np.log(z[ok]) + blend * np.log(np.clip(m.to_numpy()[ok], 1e-9, 1)))
                p[:] = z / z.sum(axis=1, keepdims=True)
        pin_upd = at.set_index("game")[[f"bookmaker_last_update_{s}" for s in bs.SIDES]].max(axis=1)
        soft = self.prices.merge(at[["game", "datetime_insert"]], on=["game", "datetime_insert"])
        soft = soft[soft["bookmaker_key"].isin(books)]
        upd = soft[[f"bookmaker_last_update_{s}" for s in bs.SIDES]].min(axis=1)
        soft = soft[(pd.to_datetime(soft["game"].map(pin_upd)) - pd.to_datetime(upd)) <= pd.Timedelta(hours=fresh_hours)]
        long = pd.concat([
            soft[["game", "commence_time", "bookmaker_key", f"price_{s}"]].rename(columns={f"price_{s}": "price"}).assign(side=s)
            for s in bs.SIDES])
        idx = long["side"].map(SIDE_IDX).to_numpy()
        long["p"] = p.to_numpy()[p.index.get_indexer(long["game"]), idx]
        long["p_true"] = self.close_fair.reindex(long["game"]).to_numpy()[np.arange(len(long)), idx]
        long["ev"] = long["p"] * long["price"] - 1
        long["won"] = long["side"].map(bs.SIDE_TO_FTR).to_numpy() == self.settle.reindex(long["game"]).to_numpy()
        long["day"] = pd.to_datetime(long["commence_time"]).dt.normalize()
        return long.dropna(subset=["p"])


def stakes_for(bets, staking, kelly, max_stake=0.05, max_day=0.30, flat=0.01):
    if staking == "flat":
        f = np.full(len(bets), flat)
    else:
        f = np.clip(kelly * bets["ev"].to_numpy() / (bets["price"].to_numpy() - 1), 0, max_stake)
    day = bets["day"].to_numpy()
    total = pd.Series(f).groupby(day).transform("sum").to_numpy()
    return np.where(total > max_day, f * max_day / np.maximum(total, 1e-12), f)


def paths(bets, f, won):
    """won: (draws, n) booleans -> bankroll path per day (draws, days), bets sorted by day."""
    price = bets["price"].to_numpy()
    ret = f * np.where(won, price - 1, -1.0)
    _, starts = np.unique(bets["day"].to_numpy(), return_index=True)
    daily = np.add.reduceat(ret, starts, axis=1)
    return np.cumprod(1 + daily, axis=1)


def summarize(name, bets, f, start_eur, rng, draws):
    bets = bets.assign(f=f)
    real = paths(bets, f, bets["won"].to_numpy()[None, :])[0]
    peak = np.maximum.accumulate(np.r_[1, real])[1:]
    mc_won = rng.random((draws, len(bets))) < bets["p_true"].to_numpy()[None, :]
    mc = paths(bets, f, mc_won)
    final_mc = mc[:, -1]
    stake_eur = (f * start_eur).sum()
    return {
        "strategy": name, "bets": len(bets),
        "avg_stake_%": 100 * f.mean(), "avg_clv_%": 100 * (bets["p_true"] * bets["price"] - 1).mean(),
        "real_final_eur": start_eur * real[-1], "real_profit_eur": start_eur * (real[-1] - 1),
        "real_max_dd_%": 100 * (1 - real / peak).max(),
        "mc_median_eur": start_eur * np.median(final_mc), "mc_p5_eur": start_eur * np.percentile(final_mc, 5),
        "mc_p95_eur": start_eur * np.percentile(final_mc, 95), "mc_loss_prob_%": 100 * (final_mc < 1).mean(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/work/data")
    ap.add_argument("--start", default="2024-09-01")
    ap.add_argument("--bankroll", type=float, default=1000.0)
    ap.add_argument("--draws", type=int, default=2000)
    args = ap.parse_args()
    d = Data(args.data)
    rng = np.random.default_rng(0)
    trio = ["onexbet", "betsson", "unibet_eu"]
    # (name, bet_time, books, source, blend, min_edge, max_price, staking, kelly)
    S = [
        ("CURRENT: 1xbet, edge>2%, odds<=3.5, half Kelly, blend 10%", "open", ["onexbet"], "pinnacle", 0.1, 0.02, 3.5, "kelly", 0.5),
        ("same, quarter Kelly", "open", ["onexbet"], "pinnacle", 0.1, 0.02, 3.5, "kelly", 0.25),
        ("same, full Kelly", "open", ["onexbet"], "pinnacle", 0.1, 0.02, 3.5, "kelly", 1.0),
        ("same, flat 1% per bet", "open", ["onexbet"], "pinnacle", 0.1, 0.02, 3.5, "flat", None),
        ("same, Pinnacle only (no model blend)", "open", ["onexbet"], "pinnacle", 0.0, 0.02, 3.5, "kelly", 0.5),
        ("same, edge>0% (more bets)", "open", ["onexbet"], "pinnacle", 0.1, 0.0, 3.5, "kelly", 0.5),
        ("same, edge>4% (fewer bets)", "open", ["onexbet"], "pinnacle", 0.1, 0.04, 3.5, "kelly", 0.5),
        ("same, odds up to 6", "open", ["onexbet"], "pinnacle", 0.1, 0.02, 6.0, "kelly", 0.5),
        ("1xbet+Betsson+Unibet, half Kelly", "open", trio, "pinnacle", 0.1, 0.02, 3.5, "kelly", 0.5),
        ("all soft books, half Kelly", "open", d.soft_books, "pinnacle", 0.1, 0.02, 3.5, "kelly", 0.5),
        ("all soft books, edge>4%, odds<=6, half Kelly", "open", d.soft_books, "pinnacle", 0.1, 0.04, 6.0, "kelly", 0.5),
        ("1xbet, bet the day before kickoff", "day_before", ["onexbet"], "pinnacle", 0.1, 0.02, 3.5, "kelly", 0.5),
        ("1xbet, bet at closing", "close", ["onexbet"], "pinnacle", 0.1, 0.02, 3.5, "kelly", 0.5),
        ("OLD APPROACH: model only, 1xbet, half Kelly", "open", ["onexbet"], "model", 0.0, 0.02, 3.5, "kelly", 0.5),
        ("OLD APPROACH: model only, all soft books, half Kelly", "open", d.soft_books, "model", 0.0, 0.02, 3.5, "kelly", 0.5),
    ]
    cache, rows = {}, []
    for name, bt, books, src, blend, edge, maxp, staking, kelly in S:
        key = (bt, tuple(books), src, blend)
        if key not in cache:
            cache[key] = d.candidates(bt, books, src, blend, args.start)
        c = cache[key]
        c = c[(c["ev"] > edge) & (c["price"] <= maxp)].sort_values("ev", ascending=False).drop_duplicates("game")
        c = c.sort_values("day", kind="stable").reset_index(drop=True)
        f = stakes_for(c, staking, kelly or 0.0)
        rows.append(summarize(name, c, f, args.bankroll, rng, args.draws))
    res = pd.DataFrame(rows)
    pd.set_option("display.width", 300)
    pd.set_option("display.max_colwidth", 60)
    print(res.round(1).to_string(index=False))
    res.to_csv(f"{args.data}/strategies.csv", index=False)


if __name__ == "__main__":
    main()

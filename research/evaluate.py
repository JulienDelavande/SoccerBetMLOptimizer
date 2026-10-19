"""Score walk-forward model probabilities against the betting market.

Market benchmark = closing Pinnacle 1X2 probabilities with the margin removed
(proportional de-vig). Only games with Pinnacle closing odds are scored, so every
row compares models and market on the same matches.
"""
import argparse

import numpy as np
import pandas as pd

CLASSES = np.array([-1, 0, 1])
P = ["p_away", "p_draw", "p_home"]


def devig(prices):
    inv = 1.0 / prices
    return inv / inv.sum(axis=1, keepdims=True)


def market_probs(odds, book, phase):
    b = odds[odds["bookmaker_key"] == book]
    prices = b[[f"price_{phase}_away", f"price_{phase}_draw", f"price_{phase}_home"]].to_numpy(float)
    p = devig(prices)
    return pd.DataFrame({"game": b["game"].values, "p_away": p[:, 0], "p_draw": p[:, 1], "p_home": p[:, 2]}).drop_duplicates("game")


def metrics(p, y):
    onehot = (y[:, None] == CLASSES[None, :]).astype(float)
    p = np.clip(p, 1e-12, 1)
    return {"log_loss": float(-np.log((p * onehot).sum(axis=1)).mean()),
            "brier": float(((p - onehot) ** 2).sum(axis=1).mean()),
            "accuracy": float((CLASSES[p.argmax(axis=1)] == y).mean())}


def load(data):
    matches = pd.read_parquet(f"{data}/matches.parquet")
    oos = pd.read_parquet(f"{data}/oos.parquet")
    odds = pd.read_parquet(f"{data}/odds.parquet")
    return matches, oos, odds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="/work/data")
    args = parser.parse_args()
    matches, oos, odds = load(args.data)
    played = matches.dropna(subset=["FTR"])[["game", "FTR", "datetime"]]
    pin_close = market_probs(odds, "pinnacle", "close")
    pin_open = market_probs(odds, "pinnacle", "open")
    games = played.merge(pin_close[["game"]], on="game")
    print(f"scored games (played, with Pinnacle closing odds): {len(games)} "
          f"from {games['datetime'].min():%Y-%m-%d} to {games['datetime'].max():%Y-%m-%d}")
    y = games.set_index("game").loc[games["game"], "FTR"].astype(int).to_numpy()
    rows = []
    for name, probs in [("market: Pinnacle closing", pin_close), ("market: Pinnacle opening", pin_open)] + \
                       [(f"model: {m}", g) for m, g in oos.groupby("model")]:
        p = probs.set_index("game").reindex(games["game"])[P].to_numpy()
        ok = ~np.isnan(p).any(axis=1)
        rows.append({"source": name, "n": int(ok.sum()), **metrics(p[ok], y[ok])})
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == "__main__":
    main()

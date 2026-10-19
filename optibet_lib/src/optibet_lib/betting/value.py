"""Value betting against the sharp market (Pinnacle), as validated by research/backtest_sync.py.

The fair probability of an outcome is Pinnacle's price with the margin removed,
optionally blended with the model. A soft-book price is a value bet when
p * price - 1 exceeds `min_edge`. Stakes are fractional Kelly with caps.
Backtest 2024-09..2026-10 (bet at first sighting, 1xbet, quarter Kelly): mean
closing-line value +2 to +3 % per bet. Over 14 seasons (2012-2026, Big 5) the model alone loses
-4.5 % per bet and blending it in degrades Pinnacle, so the default blend weight is 0; the edge
comes from comparing many books (best price: +7.2 % per bet, 11 of 14 seasons positive).
"""
import numpy as np
import pandas as pd
from scipy.optimize import brentq

SIDES = ("home", "draw", "away")


def devig(prices: np.ndarray, method: str = "shin") -> np.ndarray:
    """Rows of decimal prices (home, draw, away) -> probabilities without the bookmaker margin.

    - proportional: implied probabilities rescaled to sum to 1 (spreads the margin evenly)
    - shin: Shin (1993) model, puts more of the margin on longshots, as bookmakers do.
      14 seasons of Pinnacle prices (research/fd_evaluate.py): best closing log loss and the
      best value-betting ROI of the three methods tried.
    """
    prices = np.asarray(prices, dtype=float)
    if (prices <= 1).any():
        raise ValueError("decimal prices must be > 1")
    q = 1.0 / prices
    if method == "proportional":
        return q / q.sum(axis=1, keepdims=True)
    if method != "shin":
        raise ValueError(f"unknown de-vig method {method!r}")
    out = np.empty_like(q)
    for i, row in enumerate(q):
        s = row.sum()
        shin = lambda z: (np.sqrt(z * z + 4 * (1 - z) * row * row / s) - z) / (2 * (1 - z))
        z = brentq(lambda z: shin(z).sum() - 1, 0.0, 0.4) if shin(0.0).sum() > 1 else 0.0
        p = shin(z)
        out[i] = p / p.sum()
    return out


def blend_with_model(p_market: np.ndarray, p_model: np.ndarray, weight: float) -> np.ndarray:
    """Geometric blend p ∝ p_market^(1-w) * p_model^w. Rows where the model is NaN keep the market."""
    p_market = np.asarray(p_market, dtype=float)
    p_model = np.asarray(p_model, dtype=float)
    out = p_market.copy()
    if weight <= 0:
        return out
    ok = ~np.isnan(p_model).any(axis=1)
    z = np.exp((1 - weight) * np.log(p_market[ok]) + weight * np.log(np.clip(p_model[ok], 1e-9, 1)))
    out[ok] = z / z.sum(axis=1, keepdims=True)
    return out


def select_value_bets(candidates: pd.DataFrame, min_edge: float, max_price: float) -> pd.DataFrame:
    """Pick at most one bet per game: the (book, side) with the highest edge.

    candidates: one row per (game, book, side) with columns game, book, side, price, p.
    Returns the chosen rows with an `edge` column (p * price - 1), highest edge first.
    """
    c = candidates.copy()
    c["edge"] = c["p"] * c["price"] - 1
    c = c[(c["edge"] > min_edge) & (c["price"] <= max_price)]
    return c.sort_values(["edge", "price"], ascending=False).drop_duplicates("game").reset_index(drop=True)


def kelly_stakes(p, price, fraction: float, max_stake: float, max_total: float) -> np.ndarray:
    """Fractional Kelly stake (share of bankroll) per bet, capped per bet and in total.

    Kelly for a single outcome at decimal price o: f* = (p*o - 1) / (o - 1).
    The total cap applies to bets placed together (same run), scaled proportionally.
    """
    p = np.asarray(p, dtype=float)
    price = np.asarray(price, dtype=float)
    f = np.clip(fraction * (p * price - 1) / (price - 1), 0, max_stake)
    total = f.sum()
    if total > max_total > 0:
        f *= max_total / total
    return f


SHARP_BOOK = "pinnacle"


def _prices_wide(odds: pd.DataFrame) -> pd.DataFrame:
    w = odds.pivot_table(index=["match_id", "book"], columns="side", values=["price", "updated"], aggfunc="last")
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    return w.dropna(subset=[f"price_{s}" for s in SIDES]).reset_index()


def compute_value_bets(odds, model, books, min_edge, max_price, kelly_fraction, max_stake, max_total,
                       blend_weight, fresh_hours, already=()):
    """Pure computation, separated from I/O for testing. Returns one row per recommended bet."""
    odds = odds[odds["side"].notna()]
    if odds.empty:
        return pd.DataFrame()
    games = odds.drop_duplicates("match_id").set_index("match_id")[
        ["sport_key", "commence_time", "home_team", "away_team"]]
    wide = _prices_wide(odds)
    sharp = wide[wide["book"] == SHARP_BOOK].set_index("match_id")
    if sharp.empty:
        return pd.DataFrame()
    p_fair = pd.DataFrame(devig(sharp[[f"price_{s}" for s in SIDES]].to_numpy()), index=sharp.index, columns=SIDES)

    if model is not None and not model.empty and blend_weight > 0:
        g = games.loc[p_fair.index].reset_index()
        g["date"] = pd.to_datetime(g["commence_time"]).dt.normalize()
        m = model.drop(columns=["date"], errors="ignore")
        # Kickoff is UTC, FBref dates are local: allow one day of difference.
        j = g.merge(m, on=["home_team", "away_team"], how="left")
        j["gap"] = (j["date"] - pd.to_datetime(j["date_match"])).abs()
        j = j[j["date_match"].isna() | (j["gap"] <= pd.Timedelta(days=1))]
        j = j.sort_values("gap").drop_duplicates("match_id").set_index("match_id").reindex(p_fair.index)
        p_model = j[["prob_home_win", "prob_draw", "prob_away_win"]].to_numpy(float)
        p_fair[:] = blend_with_model(p_fair.to_numpy(), p_model, blend_weight)

    sharp_updated = sharp[[f"updated_{s}" for s in SIDES]].max(axis=1)
    soft = wide[wide["book"].isin(books) & (wide["book"] != SHARP_BOOK) & wide["match_id"].isin(p_fair.index)]
    soft_updated = soft[[f"updated_{s}" for s in SIDES]].min(axis=1)
    lag = pd.to_datetime(soft["match_id"].map(sharp_updated)) - pd.to_datetime(soft_updated)
    soft = soft[lag <= pd.Timedelta(hours=fresh_hours)]
    soft = soft[~soft["match_id"].isin(set(already))]
    if soft.empty:
        return pd.DataFrame()

    cands = pd.concat([
        pd.DataFrame({"game": soft["match_id"].values, "book": soft["book"].values, "side": s,
                      "price": soft[f"price_{s}"].to_numpy(float),
                      "p": p_fair.loc[soft["match_id"], s].to_numpy()})
        for s in SIDES])
    bets = select_value_bets(cands, min_edge=min_edge, max_price=max_price)
    if bets.empty:
        return bets
    bets["stake"] = kelly_stakes(bets["p"], bets["price"], kelly_fraction, max_stake, max_total)
    bets = bets.rename(columns={"game": "match_id"}).join(games, on="match_id")
    fair = p_fair.loc[bets["match_id"]].reset_index(drop=True)
    for s in SIDES:
        bets[f"fair_{s}"] = fair[s].to_numpy()
    return bets[bets["stake"] > 0].reset_index(drop=True)



"""Can a results-only model beat Pinnacle's early line in some league? (22 leagues, 2012-13..2025-26)

Self-contained on football-data.co.uk: PS = Pinnacle price when the file is compiled
(Friday / Tuesday before the round, the "early" line we could bet), PSC = closing.

Model: HGB on pre-match Elo, rolling form (goals, shots on target, points), rest days,
division; trained walk-forward on all previous seasons. Stack: multinomial LR on
log(p_early) + log(p_model), also walk-forward, i.e. "does the model add information
to the market?". Bets are placed at the early Pinnacle price; CLV is measured against
the Shin de-vigged closing line. Leagues are selected on 2014-15..2019-20 and judged
on 2020-21..2025-26 to avoid picking lucky ones.
"""
import argparse
from collections import defaultdict, deque

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from research.fd_evaluate import devig, log_loss
from research.football_data import fetch

import io

DIVS = ["E0", "E1", "E2", "E3", "SC0", "SC1", "D1", "D2", "I1", "I2", "SP1", "SP2",
        "F1", "F2", "N1", "B1", "P1", "T1", "G1", "SC2", "SC3", "EC"]
SEASONS = [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in range(2012, 2026)]
SIDES = ["home", "draw", "away"]
SELECT_END, JUDGE_START = "1920", "2021"


def load(data):
    frames = []
    for s in SEASONS:
        for d in DIVS:
            try:
                raw = fetch(f"https://www.football-data.co.uk/mmz4281/{s}/{d}.csv", f"{data}/fd_raw/{s}_{d}.csv")
            except Exception as e:  # noqa: BLE001
                print("skip", s, d, e)
                continue
            df = pd.read_csv(io.BytesIO(raw), encoding="latin-1", on_bad_lines="skip").dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
            out = pd.DataFrame({"season": s, "div": d, "country": d.rstrip("0123C") or d,
                                "date": pd.to_datetime(df["Date"], format="mixed", dayfirst=True, errors="coerce"),
                                "home": df["HomeTeam"].str.strip(), "away": df["AwayTeam"].str.strip(),
                                "hg": df["FTHG"].astype(int), "ag": df["FTAG"].astype(int)})
            for c in ("HST", "AST"):
                out[c] = pd.to_numeric(df[c], errors="coerce") if c in df else np.nan
            for pre, name in (("PS", "early"), ("PSC", "close")):
                for side, k in zip(SIDES, "HDA"):
                    out[f"{name}_{side}"] = pd.to_numeric(df[f"{pre}{k}"], errors="coerce") if f"{pre}{k}" in df else np.nan
            frames.append(out)
    fd = pd.concat(frames, ignore_index=True).dropna(subset=["date"])
    fd["country"] = fd["div"].map(lambda d: "ENG" if d.startswith("E") else d.rstrip("0123"))
    return fd.sort_values(["date", "div"], kind="stable").reset_index(drop=True)


def features(fd, k=20.0, hfa=60.0, n=8):
    """Sequential pre-match features; teams are keyed by (country, name) so ratings follow promotions."""
    elo, div_mean = {}, defaultdict(lambda: 1500.0)
    hist = defaultdict(lambda: deque(maxlen=n))
    last = {}
    rows = []
    for r in fd.itertuples(index=False):
        h, a = (r.country, r.home), (r.country, r.away)
        for t in (h, a):
            if t not in elo:
                elo[t] = div_mean[r.div] - 50.0
        f = {"elo_h": elo[h], "elo_a": elo[a], "elo_diff": elo[h] - elo[a] + hfa}
        for tag, t in (("h", h), ("a", a)):
            H = hist[t]
            arr = np.array(H, dtype=float) if H else np.full((1, 5), np.nan)
            f.update({f"gf_{tag}": np.nanmean(arr[:, 0]), f"ga_{tag}": np.nanmean(arr[:, 1]),
                      f"sotf_{tag}": np.nanmean(arr[:, 2]) if np.isfinite(arr[:, 2]).any() else np.nan,
                      f"sota_{tag}": np.nanmean(arr[:, 3]) if np.isfinite(arr[:, 3]).any() else np.nan,
                      f"pts_{tag}": np.nanmean(arr[:, 4]), f"n_{tag}": len(H),
                      f"rest_{tag}": min((r.date - last[t]).days, 30) if t in last else np.nan})
        rows.append(f)
        exp_h = 1 / (1 + 10 ** (-(elo[h] + hfa - elo[a]) / 400))
        res = 1.0 if r.hg > r.ag else 0.5 if r.hg == r.ag else 0.0
        delta = k * np.log1p(abs(r.hg - r.ag)) * (res - exp_h) if r.hg != r.ag else k * (res - exp_h)
        elo[h] += delta
        elo[a] -= delta
        div_mean[r.div] = 0.98 * div_mean[r.div] + 0.01 * (elo[h] + elo[a])
        ph, pa = (3, 0) if r.hg > r.ag else (1, 1) if r.hg == r.ag else (0, 3)
        hist[h].append((r.hg, r.ag, r.HST, r.AST, ph))
        hist[a].append((r.ag, r.hg, r.AST, r.HST, pa))
        last[h] = last[a] = r.date
    X = pd.DataFrame(rows, index=fd.index)
    X["div_code"] = fd["div"].map({d: i for i, d in enumerate(DIVS)})
    return X


def walk_forward(fd, X, y):
    p_model = np.full((len(fd), 3), np.nan)
    p_stack = np.full((len(fd), 3), np.nan)
    log_early = np.log(fd[[f"early_p_{s}" for s in SIDES]].to_numpy())
    seasons = sorted(fd["season"].unique())
    for i, s in enumerate(seasons[2:], start=2):
        tr = (fd["season"] < s).to_numpy() & (X["n_h"] >= 3).to_numpy() & (X["n_a"] >= 3).to_numpy()
        te = (fd["season"] == s).to_numpy()
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.04, max_leaf_nodes=15, min_samples_leaf=80,
                                           l2_regularization=1.0, categorical_features=[X.columns.get_loc("div_code")],
                                           random_state=0)
        m.fit(X[tr], y[tr])
        p_model[te] = m.predict_proba(X[te])
        st = (fd["season"] < s).to_numpy() & np.isfinite(p_model).all(axis=1) & np.isfinite(log_early).all(axis=1)
        if st.sum() > 2000:
            Z = lambda idx: np.hstack([log_early[idx], np.log(np.clip(p_model[idx], 1e-6, 1))])
            lr = LogisticRegression(C=1.0, max_iter=1000).fit(Z(st), y[st])
            ok = te & np.isfinite(log_early).all(axis=1)
            p_stack[ok] = lr.predict_proba(Z(ok))
        print("season", s, "trained on", int(tr.sum()), flush=True)
    return p_model, p_stack


def bets(fd, p, y, min_edge, max_price=3.5):
    price = fd[[f"early_{s}" for s in SIDES]].to_numpy()
    close = fd[[f"close_p_{s}" for s in SIDES]].to_numpy()
    edge = p * price - 1
    edge[(price > max_price) | ~np.isfinite(edge)] = -np.inf
    side = edge.argmax(axis=1)
    idx = np.arange(len(fd))
    keep = edge[idx, side] > min_edge
    return pd.DataFrame({"div": fd["div"].to_numpy(), "season": fd["season"].to_numpy(),
                         "r": np.where(side == y, price[idx, side] - 1, -1.0),
                         "clv": price[idx, side] * close[idx, side] - 1})[keep]


def summarise(b, by):
    g = b.groupby(by)
    out = pd.DataFrame({"bets": g.size(), "roi_%": 100 * g["r"].mean(), "clv_%": 100 * g["clv"].mean(),
                        "clv_t": g["clv"].mean() / (g["clv"].std(ddof=1) / np.sqrt(g.size()))})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/work/data")
    args = ap.parse_args()
    fd = load(args.data)
    X = features(fd)
    cols = [f"{k}_{s}" for k in ("early", "close") for s in SIDES]
    ok = (fd[cols] > 1).all(axis=1) & fd[cols].notna().all(axis=1)
    print(f"games: {len(fd)}, with Pinnacle early+close: {ok.sum()}")
    fd, X = fd[ok].reset_index(drop=True), X[ok].reset_index(drop=True)
    for k in ("early", "close"):
        p = devig(fd[[f"{k}_{s}" for s in SIDES]].to_numpy(float), "shin")
        for i, s in enumerate(SIDES):
            fd[f"{k}_p_{s}"] = p[:, i]
    y = np.where(fd["hg"] > fd["ag"], 0, np.where(fd["hg"] == fd["ag"], 1, 2))
    p_model, p_stack = walk_forward(fd, X, y)
    ev = np.isfinite(p_stack).all(axis=1)
    early = fd[[f"early_p_{s}" for s in SIDES]].to_numpy()
    close = fd[[f"close_p_{s}" for s in SIDES]].to_numpy()
    pd.set_option("display.width", 250)

    def ll_table(mask):
        rows = []
        for d in DIVS:
            m = mask & (fd["div"] == d).to_numpy()
            if m.sum() < 300:
                continue
            rows.append({"div": d, "games": int(m.sum()), "pin_early": log_loss(early[m], y[m]), "pin_close": log_loss(close[m], y[m]),
                         "model": log_loss(p_model[m], y[m]), "stack": log_loss(p_stack[m], y[m])})
        t = pd.DataFrame(rows)
        t["stack_gain_vs_early"] = t["pin_early"] - t["stack"]
        return t.round(4)

    print("\n=== log loss per league, all evaluated seasons (lower is better) ===")
    print(ll_table(ev).to_string(index=False))
    print("ALL:", {k: round(log_loss(v[ev], y[ev]), 4) for k, v in (("pin_early", early), ("pin_close", close), ("model", p_model), ("stack", p_stack))})

    sel = ev & (fd["season"] <= SELECT_END).to_numpy()
    jud = ev & (fd["season"] >= JUDGE_START).to_numpy()
    for name, p, edge in (("MODEL ONLY", p_model, 0.03), ("STACK (model + Pinnacle early)", p_stack, 0.02)):
        bs = bets(fd[sel], p[sel], y[sel], edge)
        bj = bets(fd[jud], p[jud], y[jud], edge)
        t = summarise(bs, "div").add_prefix("sel_").join(summarise(bj, "div").add_prefix("judge_"), how="outer")
        print(f"\n=== {name}: bet at Pinnacle early price, edge > {edge:.0%}, odds <= 3.5 ===")
        print("selection 2014-20 | judged 2020-26")
        print(t.round(2).sort_values("sel_clv_t", ascending=False).to_string())
        picked = t.index[(t["sel_clv_t"] > 2) & (t["sel_bets"] >= 50)]
        bj_p = bj[bj["div"].isin(picked)]
        if len(bj_p):
            print(f"leagues picked on 2014-20 (CLV t>2): {list(picked)} -> 2020-26: bets={len(bj_p)}, "
                  f"roi={100 * bj_p['r'].mean():.2f}%, clv={100 * bj_p['clv'].mean():.2f}% "
                  f"(t={bj_p['clv'].mean() / (bj_p['clv'].std(ddof=1) / np.sqrt(len(bj_p))):.2f}), "
                  f"seasons with positive ROI: {(bj_p.groupby('season')['r'].mean() > 0).sum()}/{bj_p['season'].nunique()}")
        else:
            print("no league passes the selection")
        allb = pd.concat([bs, bj])
        print(f"all leagues, all seasons: bets={len(allb)}, roi={100 * allb['r'].mean():.2f}%, clv={100 * allb['clv'].mean():.2f}%")


if __name__ == "__main__":
    main()

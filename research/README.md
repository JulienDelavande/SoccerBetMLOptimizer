# Research: model and betting strategy evaluation

Offline, leakage-free evaluation of models and staking strategies against the betting market.
Runs next to the database (in-cluster pod), reads only.

| Script | What it does |
|---|---|
| `build_dataset.py` | Pre-match features for every FBref match (`matches.parquet`), opening/closing 1X2 prices per bookmaker (`odds.parquet`), every pre-kickoff odds snapshot (`snapshots.parquet`). |
| `models.py` | Monthly walk-forward out-of-sample probabilities for candidate models (`oos.parquet`). |
| `evaluate.py` | Log loss / Brier / accuracy of models vs Pinnacle (de-vigged) on the same games. |
| `backtest.py` | First, naive bankroll backtest (unsynchronised prices; kept for `simulate`). |
| `simulate_strategies.py` | Euros per strategy on our two seasons: realised result and Monte Carlo range (outcomes redrawn from Pinnacle closing). |
| `football_data.py`, `fd_evaluate.py` | 14-season validation on football-data.co.uk odds (below). |
| `backtest_sync.py` | Realistic backtest: synchronised snapshots, fresh soft prices only, extra-time matches not settled, CLV. |

## Findings (2024-08 to 2026-10, 2,748 games with Pinnacle odds)

- Market beats every model: log loss Pinnacle closing 0.9589, opening 0.9665, best model (`hgb_xg_rest`, now in production) 0.9756, previous LR 0.9787.
- Betting model-only edges loses money once prices are synchronised.
- Value betting against Pinnacle's fair line works: bet the first time a soft-book price beats it. Production parameters (1xbet, edge > 2%, price <= 3.5, blend 10% model, caps 5%/bet 30%/run): 179 bets, mean CLV +3.0% (t = 4.6), positive in both full seasons; bankroll x1.29 at quarter Kelly (max drawdown 5.7%), x1.63 at half Kelly (11%).
- Expect long-run ROI close to the CLV (~3%), not the realised +24%. Soft books limit winning accounts.

## 14-season validation (football-data.co.uk, 2012-13..2025-26, Big 5, 24,214 games)

`football_data.py` downloads Bet365 / Pinnacle opening / Pinnacle closing / market max prices and
matches them to FBref games (team names learned by voting on same-league same-day same-score games,
98.7% matched). `fd_evaluate.py` (walk-forward model from `models.py --start 2012-08-01`):

- Pinnacle beats the model every season (closing log loss 0.963 vs 0.984).
- Model-only betting loses: -4.5% per bet vs Bet365 (t = -3.8, 3/14 seasons positive). The +6% of
  2024-26 was luck.
- Blending 10% model into Pinnacle degrades it (0.9656 vs 0.9651): production blend weight is 0.
- Value betting at the best market price vs Pinnacle opening (Shin de-vig): +7.2% per bet, t = 4.2,
  CLV +3.7%, 11/14 seasons positive. One soft book alone rarely triggers (116 bets in 14 seasons):
  the edge comes from comparing many books.
- Shin de-vig is now the default (`optibet_lib.betting.devig`).

## Running

```bash
kubectl --context homelab -n optimsportbets apply -f <research pod>   # python:3.11, pandas 2.3.3, sklearn 1.7.2
tar czf code.tgz research optibet_lib/src && kubectl cp code.tgz research:/tmp/ && ...
/work/run.sh research/build_dataset.py && /work/run.sh research/models.py && /work/run.sh research/evaluate.py
/work/run.sh -m research.backtest_sync --blend 0.1
```
`run.sh` sets `PYTHONPATH` (optibet_lib, repo root, pipelines) and `DATABASE_URL` (`postgresql+psycopg2://...`).

# avellaneda-stoikov-sim

A Python simulation of the Avellaneda-Stoikov (2008) market making model. Built as a small project to understand how optimal bid/ask quotes are derived from first principles.

---

## What this is

The A-S model solves for a market maker's optimal quotes accounting for two competing forces:

- **Inventory risk** — the longer you hold a position, the more price moves can hurt you. The model skews your quotes to attract trades that reduce your exposure.
- **Execution risk** — quotes too far from mid won't get filled. The model calibrates spread width against realistic order arrival probabilities.

The result is a closed-form solution for bid/ask quotes that balances these two forces optimally at every point in the trading session.

I read through the paper properly before building this — notes on the derivations are [here](https://www.notion.so/bunchcapital/AVELLANEDA-STOIKOV-31aa8bd6cafd80289780fd97f61dab9d).

---

## The model

**Reservation price** (dealer's personal valuation, adjusted for inventory):
```
r = S - q * γ * σ² * (T - t)
```

**Optimal spread** (two components):
```
spread = γ * σ² * (T-t)              ← inventory risk
       + (2/γ) * ln(1 + γ/κ)         ← execution risk
```

**Final quotes:**
```
bid = r - spread/2
ask = r + spread/2
```

**Order arrival** (Poisson process, exponential decay with distance from mid):
```
prob_ask_hit = A * exp(-κ * (ask - S)) * dt
prob_bid_hit = A * exp(-κ * (S - bid)) * dt
```

---

## Repo structure

```
avellaneda_stoikov/
├── config.py         — all parameters in one place
├── simulation.py     — price process + order arrival
├── market_maker.py   — reservation price, spread, quote calculation
├── main.py           — simulation loop
└── visualisation.py  — 4-panel output plots
```

---

## Parameters

```python
S0 = 100.0       # initial asset price
T = 1.0          # one trading session, normalised to 1
N_STEPS = 10000  # timesteps (higher = smoother paths)
DT = T / N_STEPS

SIGMA = 0.15     # volatility per session
KAPPA = 10.0     # order arrival decay rate (price sensitivity of market)
A = 1.0 * N_STEPS  # arrival intensity, scaled to step frequency

GAMMA = 0.2      # risk aversion (0.01 = low, 0.1 = moderate, 0.5+ = high)
TRADE_SIZE = 1   # shares per fill
```

**A note on calibration:** these params are illustrative, not calibrated to real tick data. `SIGMA=0.15` is higher than realistic for a large-cap equity (~0.02) — the lower value makes the inventory skew invisible at this step scale. `KAPPA=10` reflects a price-sensitive market where execution probability decays quickly with distance from mid, which keeps the spread components roughly balanced. A proper calibration would involve fitting to real order book data.

---

## Output

Running `main.py` produces a 4-panel plot:

1. **Mid price vs bid/ask quotes** — quotes should track mid throughout the session, with visible asymmetry when inventory builds
2. **Inventory over time** — should oscillate around zero (mean-reverting)
3. **Cumulative P&L** — should trend upward as the market maker earns the spread
4. **Spread width over time** — should narrow as the session end approaches (less time remaining = less inventory risk)

---

## What I learned building this

The model is straightforward to implement but the parameter interactions are non-obvious. A few things that tripped me up:

**Order arrival probabilities need DT scaling.** Without multiplying by `DT`, probabilities aren't per-timestep — they're per-session. With `A=1000` and no scaling, `prob > 1` always, so both sides fill every step. P&L becomes a perfectly straight line and inventory flatlines at zero. The fix is one line but it took a while to diagnose.

**A needs to scale with N_STEPS.** `A=1.0` with 10,000 steps means roughly 0.0001 of the session per step — a near-dead market. Setting `A = 1.0 * N_STEPS` keeps order arrival density consistent regardless of step count.

**The spread is dominated by the execution risk term.** With `GAMMA=0.1`, the `2/γ` multiplier is 20 — so even a small log term produces a large constant spread (~1.29). The inventory risk component is ~0.00004, effectively invisible. This means the model's core mechanism (skewing quotes in response to inventory) has almost no effect on spread width. Increasing KAPPA to 10 directly reduces the execution term and lets inventory risk hold meaningful weight. You arrive at `KAPPA=10` for the right reason: it reflects a market where execution probability is highly sensitive to price, which is realistic for liquid, competitive markets.

**SIGMA and GAMMA interact.** The inventory skew is `q * γ * σ²`. With small sigma, even large inventory barely moves your quotes. `SIGMA=0.15` is needed for the skew to be visually meaningful in the simulation — at the cost of some realism.

---

## What's next

- **Gamma experiment** — run three simulations with `GAMMA = 0.01, 0.1, 0.5` overlaid. Should show how risk aversion affects spread width, inventory bounds, and P&L trajectory.
- **Adverse selection extension** — model two trader types: uninformed retail (symmetric, safe) and informed traders who trade profitably against you. The A-S paper ignores this; it's what real market making desks think about constantly.
- **Proper calibration** — fit `σ`, `κ`, `A` to real tick data from a liquid equity.

---

## References

- Avellaneda, M. & Stoikov, S. (2008). *High-frequency trading in a limit order book.* Quantitative Finance, 8(3), 217–224.
# avellaneda-stoikov-sim

A Python simulation of the Avellaneda–Stoikov (2008) market making model, extended with a Glosten–Milgrom style adverse-selection layer. Built to understand optimal quoting and how it degrades under informed flow.

---

## V1 — Avellaneda–Stoikov

### What this is

The A–S model solves for a market maker's optimal quotes accounting for two competing forces:

- **Inventory risk** — the longer you hold a position, the more price moves can hurt you. The model skews your quotes to attract trades that reduce your exposure.
- **Execution risk** — quotes too far from mid won't get filled. The model calibrates spread width against realistic order arrival probabilities.

The result is a closed-form solution for bid/ask quotes that balances these two forces optimally at every point in the trading session.

**My personal notes on the A–S paper** (derivations, intuition, implementation) are [here](https://remarkable-mandevilla-1be.notion.site/Avellaneda-Stoikov-High-frequency-trading-in-a-limit-order-book-31bc59be727d80e1914cd4e8b59db29f?source=copy_link).

### The model

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

### Repo structure

```
avellaneda_stoikov/
├── config.py         — all parameters in one place
├── simulation.py     — price process + order arrival (+ informed/uninformed flow in V2)
├── market_maker.py   — reservation price, spread, quote calculation (A–S only)
├── main.py           — simulation loop
└── visualisation.py  — multi-panel output plots
```

### Parameters (V1 + shared)

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

**A note on calibration:** these params are illustrative, not calibrated to real tick data. `SIGMA=0.15` is higher than realistic for a large-cap equity (~0.02) — the lower value makes the inventory skew visible at this step scale. `KAPPA=10` reflects a price-sensitive market where execution probability decays quickly with distance from mid. A proper calibration would involve fitting to real order book data.

### What I learned building V1

**Order arrival probabilities need DT scaling.** Without multiplying by `DT`, probabilities aren't per-timestep — they're per-session. With `A=1000` and no scaling, `prob > 1` always, so both sides fill every step. P&L becomes a straight line and inventory flatlines at zero.

**A needs to scale with N_STEPS.** `A=1.0` with 10,000 steps means a near-dead market. Setting `A = 1.0 * N_STEPS` keeps order arrival density consistent regardless of step count.

**The spread is dominated by the execution risk term.** With `GAMMA=0.1`, the `2/γ` multiplier is 20 — so even a small log term produces a large constant spread (~1.29). The inventory risk component is tiny. Increasing KAPPA to 10 reduces the execution term and lets inventory risk matter.

**SIGMA and GAMMA interact.** The inventory skew is `q * γ * σ²`. With small sigma, even large inventory barely moves quotes. `SIGMA=0.15` is needed for the skew to be visually meaningful — at the cost of some realism.

---

## V2 — Glosten–Milgrom Extension

V1 simulated a pure A–S market maker against noise traders only. V2 adds **adverse selection** via a Glosten–Milgrom style flow model: two trader types (informed and uninformed), a regime-switching Markov chain (normal vs toxic), and Kyle's lambda for permanent price impact after informed trades. The A–S quoting strategy is unchanged — the goal is to see how it behaves under GM-style flow.

We follow the idea that the specialist faces heterogeneously informed traders (Glosten & Milgrom, 1985): in toxic regimes, a larger fraction of order flow is informed, so the market maker is more often picked off. The informed trader’s signal is modelled as a noisy observation of the fundamental value *V*; when they trade, *S* is updated by a Kyle-style permanent impact so that *S* and *V* can diverge over time (in practice they stay close because λ is small and *S*, *V* share the same Brownian driver).

**Citation:** Glosten, L. R., & Milgrom, P. R. (1985). Bid, ask and transaction prices in a specialist market with heterogeneously informed traders. *Journal of Financial Economics*, 14(1), 71–100.

### V2 Development Notes

**What V2 adds**

- **Informed vs uninformed flow** — Each arriving order is typed as informed or uninformed. Uninformed trade is symmetric and safe; informed trade uses a noisy signal around fundamental *V* and triggers permanent impact on *S* (Kyle’s λ).
- **Regime switching** — A Markov chain toggles between *normal* and *toxic* regimes. Probability of an informed trader is higher in toxic (`INFORMED_PROB_TOXIC`) than in normal (`INFORMED_PROB_NORMAL`). Transitions are asymmetric: low prob normal→toxic, higher prob toxic→normal, so toxic periods are short stress events.
- **S and V** — Fundamental *V* and mid *S* are both driven by the same Brownian increment each step; informed trades move *S* by λ·size. The A–S quotes are still based on *S* and inventory only; there is no regime-dependent quoting.

**Design decisions**

- **S and V share the same dW** — *V* and *S* use the same Brownian increment each step. Diffusion is treated as public; the informed trader’s edge is a noisy signal around *V*, not a separate process. So *S* ≈ *V* by construction — that’s intended, not a bug.

**Things that didn’t work first time**

- **Regime switching was too frequent** — With a symmetric `REGIME_TRANSITION_PROB = 0.01` and 10,000 steps, the chain converged to ~50/50 normal/toxic. Toxic should be a rare stress state. Fixed by asymmetric transition probs: low probability into toxic, higher probability out (`PROB_NORMAL_TO_TOXIC`, `PROB_TOXIC_TO_NORMAL`).
- **S–V divergence panel was flat** — A dedicated S−V panel was added to show Kyle impact. It stayed flat because informed trades are rare, λ is small, and *S* and *V* share dW so any divergence is swamped by the next common shock. That’s correct given the model. The adverse selection effect shows up in **inventory and P&L during toxic regimes**, not in a visible mid-vs-fundamental gap. The panel was removed; *V* remains in the log and on the price chart.

**What the output shows**

- Spread narrows over time (A–S: time remaining → 0).
- Inventory becomes more directional during toxic regimes.
- P&L grows but with visible slope changes around toxic periods.
- The A–S strategy earns the spread but does not widen quotes in toxic regimes — it has no mechanism to detect or react to informed flow.

---

## What's next

- **Gamma experiment** — run multiple simulations with different GAMMA overlaid (spread width, inventory bounds, P&L).
- **Regime-aware quoting** — widen spread or skew more aggressively in toxic regimes (would require a regime signal or proxy).
- **Proper calibration** — fit σ, κ, A and GM params to real tick data.

---

## References

- Avellaneda, M. & Stoikov, S. (2008). *High-frequency trading in a limit order book.* Quantitative Finance, 8(3), 217–224.
- Glosten, L. R., & Milgrom, P. R. (1985). Bid, ask and transaction prices in a specialist market with heterogeneously informed traders. *Journal of Financial Economics*, 14(1), 71–100.
- [My notes on the A–S paper](https://remarkable-mandevilla-1be.notion.site/Avellaneda-Stoikov-High-frequency-trading-in-a-limit-order-book-31bc59be727d80e1914cd4e8b59db29f?source=copy_link) (Notion) — derivations, intuition, implementation.

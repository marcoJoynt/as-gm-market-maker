# avellaneda-stoikov-sim

A Python simulation of the Avellaneda–Stoikov (2008) market making model, extended with a Glosten–Milgrom style adverse-selection layer and an interactive Streamlit dashboard. Built to understand optimal quoting and how it degrades under informed flow.

**Live demo:** [app](https://as-gm-market-maker-production.up.railway.app)

---

## Quick Start

### Local (Python)

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Docker

```bash
docker compose up --build
# open http://localhost:8501
```

Or without Compose:

```bash
docker build -t asgm-sim .
docker run -p 8501:8501 asgm-sim
```

---

## V1 — Avellaneda–Stoikov

### What this is

The A–S model solves for a market maker's optimal quotes accounting for two competing forces:

- **Inventory risk** — the longer you hold a position, the more price moves can hurt you. The model skews your quotes to attract trades that reduce your exposure.
- **Execution risk** — quotes too far from mid won't get filled. The model calibrates spread width against realistic order arrival probabilities.

The result is a closed-form solution for bid/ask quotes that balances these two forces optimally at every point in the trading session.

**Personal notes on the A–S paper** (derivations, intuition, implementation) are [here](https://remarkable-mandevilla-1be.notion.site/Avellaneda-Stoikov-High-frequency-trading-in-a-limit-order-book-31bc59be727d80e1914cd4e8b59db29f?source=copy_link).

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
as-gm-market-maker/
├── config.py         — all parameters in one place
├── simulation.py     — price process + order arrival (+ informed/uninformed flow in V2)
├── market_maker.py   — reservation price, spread, quote calculation (A–S only)
├── main.py           — simulation loop
├── visualisation.py  — static multi-panel output plots
├── app.py            — interactive Streamlit dashboard
├── Dockerfile        — containerised deployment
└── docker-compose.yml
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

### V1 Learnings

**Order arrival probabilities need DT scaling.** Without multiplying by `DT`, probabilities aren't per-timestep — they're per-session. With `A=1000` and no scaling, `prob > 1` always, so both sides fill every step. P&L becomes a straight line and inventory flatlines at zero.

**A needs to scale with N_STEPS.** `A=1.0` with 10,000 steps means a near-dead market. Setting `A = 1.0 * N_STEPS` keeps order arrival density consistent regardless of step count.

**The spread is dominated by the execution risk term.** With `GAMMA=0.1`, the `2/γ` multiplier is 20 — so even a small log term produces a large constant spread (~1.29). The inventory risk component is tiny. Increasing KAPPA to 10 reduces the execution term and lets inventory risk matter.

**SIGMA and GAMMA interact.** The inventory skew is `q * γ * σ²`. With small sigma, even large inventory barely moves quotes. `SIGMA=0.15` is needed for the skew to be visually meaningful — at the cost of some realism.

---

## V2 — Glosten–Milgrom Extension

V1 simulated a pure A–S market maker against noise traders only. V2 adds **adverse selection** via a Glosten–Milgrom style flow model: two trader types (informed and uninformed), a regime-switching Markov chain (normal vs toxic), and Kyle's lambda for permanent price impact after informed trades. The A–S quoting strategy is unchanged — the goal is to see how it behaves under GM-style flow.

We follow the idea that the specialist faces heterogeneously informed traders (Glosten & Milgrom, 1985): in toxic regimes, a larger fraction of order flow is informed, so the market maker is more often picked off. The informed trader's signal is modelled as a noisy observation of the fundamental value *V*; when they trade, *S* is updated by a Kyle-style permanent impact so that *S* and *V* can diverge over time (in practice they stay close because λ is small and *S*, *V* share the same Brownian driver).

**Citation:** Glosten, L. R., & Milgrom, P. R. (1985). Bid, ask and transaction prices in a specialist market with heterogeneously informed traders. *Journal of Financial Economics*, 14(1), 71–100.

### Adverse selection mechanics

| Component | Role |
|---|---|
| **Informed trader** | Observes fundamental value V with small signal noise; trades only when signal crosses the quote (a genuinely profitable opportunity) |
| **Uninformed (noise) trader** | Arrives as a Poisson process; hit probability decays exponentially with distance from mid (A–S mechanics) |
| **Regime (Markov chain)** | Switches between *normal* and *toxic*; toxic raises informed-trader probability from `INFORMED_PROB_NORMAL` (5%) to `INFORMED_PROB_TOXIC` (30%) |
| **Kyle's λ** | Permanent price impact applied to mid-price *S* after each informed trade, causing S to drift toward V |

### Adverse selection parameters

```python
INFORMED_PROB_NORMAL  = 0.05   # prob of informed trader arrival in normal regime
INFORMED_PROB_TOXIC   = 0.30   # prob of informed trader arrival in toxic regime
PROB_NORMAL_TO_TOXIC  = 0.005  # per-step transition prob into toxic (rare)
PROB_TOXIC_TO_NORMAL  = 0.05   # per-step transition prob out of toxic (quick recovery)
SIGNAL_NOISE          = 0.02   # std of noise on informed trader's signal around V
KYLE_LAMBDA           = 0.1    # permanent price impact per unit traded
```

**Transition asymmetry is intentional.** With symmetric probabilities the Markov chain converges to ~50/50 stationary distribution — toxic would be half the simulation. Asymmetric design (rare entry, quick exit) makes toxic feel like a short stress event, which is more realistic and makes its P&L and inventory effects visible as distinct episodes.

### What the output shows

| Panel | What to look for |
|---|---|
| **Mid Price vs Quotes** | Quote skew during long inventory streaks; spread narrows as T→0 |
| **Inventory** | More directional drift during toxic (shaded red) periods |
| **Regime State** | Frequency and duration of toxic episodes |
| **Spread Width** | Time-decaying spread from A–S; constant width regardless of inventory |
| **Mark-to-Market P&L** | Slope flattens or reverses during toxic — the market maker is being picked off |
| **Spread capture KDE** | Informed trades cluster near zero (or negative); noise trades cluster near half-spread |
| **Inventory violin** | Toxic distribution is wider and less centred — inventory control degrades |

### Key insight from V2

The A–S strategy has **no adverse selection defence**. It narrows the spread as time runs out and skews quotes for inventory — but it cannot detect or react to informed flow. During toxic regimes the market maker continues quoting the same spread, gets picked off repeatedly, and accumulates directional inventory precisely when it's most dangerous. The P&L slope change around toxic episodes quantifies this cost directly.

### V2 development notes

**S and V share the same dW** — Diffusion is treated as public information; the informed trader's edge is a noisy signal around *V*, not a separate process. So *S* ≈ *V* by construction — that's intended. Adverse selection shows up in **inventory and P&L**, not in a visible S−V gap.

**Regime switching was too frequent first** — With symmetric `REGIME_TRANSITION_PROB = 0.01` the chain hit ~50/50. Fixed by asymmetric probs.

**S–V divergence panel removed** — A dedicated S−V panel was flat because informed trades are rare, λ is small, and shared dW swamps any divergence. *V* remains in the log and on the price chart for reference.

---

## Interactive Dashboard

The Streamlit dashboard (`app.py`) exposes five parameters via sidebar sliders:

| Slider | Effect |
|---|---|
| **Volatility (σ)** | Scales both price diffusion and the inventory-risk component of the spread |
| **Risk aversion (γ)** | Controls inventory skew magnitude and spread width |
| **Kyle's λ** | Permanent price impact per informed trade |
| **Informed prob (toxic)** | Fraction of flow that is informed during toxic regimes |
| **P(normal → toxic)** | Controls how frequently toxic episodes begin |

Summary metrics displayed: Final P&L, Spread Capture Ratio (mean/std of per-trade spread capture — measures consistency, not annualised risk-adjusted returns), informed flow %, time in toxic %, and max absolute inventory.

---

## What's next

- **Regime-aware quoting** — widen spread or skew more aggressively in toxic regimes (requires a regime signal or proxy, e.g. recent fill imbalance).
- **Gamma experiment** — run multiple simulations with different GAMMA overlaid (spread width, inventory bounds, P&L comparison).
- **Proper calibration** — fit σ, κ, A and GM params to real tick data (e.g. from a public L2 feed).
- **Stoikov extension** — add the infinite-horizon ω parameter to enforce a hard inventory cap.

---

## References

- Avellaneda, M. & Stoikov, S. (2008). *High-frequency trading in a limit order book.* Quantitative Finance, 8(3), 217–224.
- Glosten, L. R., & Milgrom, P. R. (1985). Bid, ask and transaction prices in a specialist market with heterogeneously informed traders. *Journal of Financial Economics*, 14(1), 71–100.
- [Personal notes on the A–S paper](https://remarkable-mandevilla-1be.notion.site/Avellaneda-Stoikov-High-frequency-trading-in-a-limit-order-book-31bc59be727d80e1914cd4e8b59db29f?source=copy_link) (Notion) — derivations, intuition, implementation.

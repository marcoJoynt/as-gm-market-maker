# Params for the simulation #

### Sim Params ###

S0 = 100.0  # Initial asset price, arbitrary amount and currency
T = 1 # one trading session (e.g. 6.5hr day, normalised to 1)
N_STEPS= 10000 # Number of total timesteps to simulate
DT = T/N_STEPS # time / timestep

### Market Params ###

SIGMA = 0.15 # Volatility (per session)
KAPPA = 10 # Order arrival rate (per session) -> Needed to increase: 
### 1. tighter spreadln(1 + γ/κ)  gets smaller decrease Execution-risk and have inventory risk non-negligible in comparison.
### 2. could be realistic for competitive, liquid markets where everyone has tight quotes.
A = 1.0 * N_STEPS # Baseline arrival intensity 

### Dealer Params ###
GAMMA = 0.2  # risk aversion — realistic range 0.01-0.1
### Slightly highter GAMMA to show inventory mean reversion effect.
TRADE_SIZE = 1 # Trade size (Shares per trade, non-fractional)

### Initial conditions ###
INITIAL_CASH = 0.0
INITIAL_INVENTORY = 0

# Adverse selection params
## S and V stay close by design; adverse selection shows up in inventory and P&L during toxic regimes, not in a large S−V gap.
## Learnings: symmetric transition prob made toxic ~50% of the time (stationary dist). Asymmetric: rare entry into toxic, quick exit so it feels like a stress event.
## Learnings: Kyle's lambda is too low, and V, S is indistinguishable on graph, increasing KYLE_LAMBDA from 0.05 to 0.1.
INFORMED_PROB_NORMAL = 0.05     # prob of informed trader in normal regime
INFORMED_PROB_TOXIC = 0.30      # prob of informed trader in toxic regime
PROB_NORMAL_TO_TOXIC = 0.005   # prob each step of switching normal → toxic (rare)
PROB_TOXIC_TO_NORMAL = 0.05    # prob each step of switching toxic → normal (quick exit)
SIGNAL_NOISE = 0.02             # std of noise on informed trader's signal
KYLE_LAMBDA = 0.1              # price impact per unit traded (Kyle's lambda)



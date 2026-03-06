# Params for the simulation #

### Sim Params ###

S0 = 100.0  # Initial asset price, arbitrary amount and currency
T = 1 # one trading session (e.g. 6.5hr day, normalised to 1)
N_STEPS= 10000 # Number of total timesteps to simulate
dT = T/N_STEPS # time / timestep

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



# Params for the simulation #

### Sim Params ###

S0 = 100.0  # Initial asset price, arbitrary amount and currency
T = 1 # total trading session legneth ( Normalising to 1 (units irrelevant))
N_STEPS= 1000 # Number of total timesteps to simulate
dT = T/N_STEPS # time / timestep

### Market Params ###

SIGMA = 0.01 # Volatility (per session)
KAPPA = 1.5 # Order arrival rate (per session)
A = 1.0 # Baseline arrival intensity 

### Dealer Params ###
GAMMA = 0.1 # risk aversion (test dif values later)
TRADE_SIZE = 1 # Trade size (Shares per trade, non-fractional)

### Initial conditions ###
INITIAL_CASH = 0.0
INITIAL_INVENTORY = 0



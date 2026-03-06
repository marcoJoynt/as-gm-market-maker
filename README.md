# avellaneda-stoikov-sim


### Learning 1:
### With:
SIGMA = 0.01 # Volatility (per session)
KAPPA = 1.5 # Order arrival rate (per session)
GAMMA = 0.1 # risk aversion (test dif values later)

    inventory_risk_component = 0.1 * 1.5**2 * 1 = 0.00004
    execution_risk_component = (2 / 0.1) * np.log(1 + 0.1 / 1.5) = 1.29
### The execution risk term is 30,000x larger. So the spread is basically just a constant ~1.29.
### Which is why it looks like a straight line narrowing only very slightly.
### Tweak, Increase GAMMA (Risk aversion) which will make inventory risk non-negligable. (Need to check logic of this though)
GAMMA=0.5 :tick:
inventory_risk_component = GAMMA * SIGMA**2 * time_remaining 
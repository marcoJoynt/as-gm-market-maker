import numpy as np
from config import GAMMA, SIGMA, KAPPA


def reservation_price(s, inventory, time_remaining)
    """
    Adjust mid price for inventory risk.
    The more inventory we hold, the more we skew our quotes
    to attract trades that reduce our position.
    ## Notes: https://www.notion.so/bunchcapital/AVELLANEDA-STOIKOV-31aa8bd6cafd80289780fd97f61dab9d?source=copy_link#31ba8bd6cafd80da94ddc0f70ceb14c3 for more details.
    
    r = S - q * gamma * sigma^2 * (T - t)
    ## s.t. q->0, r -> S
    """
    return S - inventory * GAMMA * SIGMA**2 * time_remaining


def optimal_spread(time_remaining):
    """
    Calculate the theoretically optimal bid/ask spread.
    Spread widens with volatility, risk averseness and time remaining in session.
    
    spread = gamma * sigma^2 * (T-t) + (2/gamma) * ln(1 + gamma/kappa)
    ## Notes: https://www.notion.so/bunchcapital/AVELLANEDA-STOIKOV-31aa8bd6cafd80289780fd97f61dab9d?source=copy_link#31ba8bd6cafd80888ac3c400609403a2 for more details.
    ## depends on time_remaining, not inventory.
    """
    inventory_risk_component = GAMMA * SIGMA**2 * time_remaining
    execution_risk_component = (2 / GAMMA) * np.log(1 + GAMMA / KAPPA)
    
    return inventory_risk_component + execution_risk_component


## Returns the final bid and ask quotes.
def get_quotes(S, inventory, time_remaining):
    """
    Calculate final bid and ask quotes.
    Centred on reservation price, not mid price.
    ## Notes: https://www.notion.so/bunchcapital/AVELLANEDA-STOIKOV-31aa8bd6cafd80289780fd97f61dab9d?source=copy_link#31ba8bd6cafd80588e8edc6b1bd9ce94 for more details.
    """
    r = reservation_price(S, inventory, time_remaining)
    spread = optimal_spread(time_remaining)
    
    bid = r - spread / 2
    ask = r + spread / 2
    
    return bid, ask
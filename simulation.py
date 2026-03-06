import numpy as np
from config import SIGMA, dT, KAPPA, A, TRADE_SIZE

def update_price(S):
    """
    Move mid price one timestep using Brownian motion
    dS = sigma * sqrt(dt) * dW
    """
    return S + SIGMA * np.sqrt(dT)*np.random.normal()

def simulate_orders(bid, ask, S, inventory, cash):
    """
    Simulate whether orders arrive and hit our quotes.
    Uses Poisson arrival process, probability of being hit
    goes down exponentially the further price is from mid.
    """
    # probability of someone hitting our ask (they're buying from us)
    prob_ask_hit = A * np.exp(-KAPPA * (ask - S))
    
    # probability of someone hitting our bid (they're selling to us)
    prob_bid_hit = A * np.exp(-KAPPA * (S - bid))

    # ask hit → we sell to them → inventory decreases, cash increases
    if np.random.uniform() < prob_ask_hit:
        inventory -= TRADE_SIZE
        cash += ask * TRADE_SIZE

    # bid hit → we buy from them → inventory increases, cash decreases
    if np.random.uniform() < prob_bid_hit:
        inventory += TRADE_SIZE
        cash -= bid * TRADE_SIZE

    return inventory, cash
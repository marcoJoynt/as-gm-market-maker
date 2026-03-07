import numpy as np
from config import SIGMA, DT, KAPPA, A, TRADE_SIZE,INFORMED_PROB_NORMAL, INFORMED_PROB_TOXIC, SIGNAL_NOISE

def update_price(S, V, sigma=None):
    """
    Move mid price one timestep using Brownian motion
    dS = sigma * sqrt(dt) * dW
    """
    if sigma is None:
        sigma = SIGMA
    dW = np.random.normal()
    S = S + sigma * np.sqrt(DT) * dW
    V = V + sigma * np.sqrt(DT) * dW
    return S, V


def simulate_orders(bid, ask, S, V, inventory, cash, regime, informed_prob_toxic=None, informed_prob_normal=None):
    """
    Simulate whether orders arrive and hit our quotes.
    Uses Poisson arrival process, probability of being hit
    goes down exponentially the further price is from mid.
    """
    # Determine if this arrival is an informed trader
    if informed_prob_toxic is None:
        informed_prob_toxic = INFORMED_PROB_TOXIC
    if informed_prob_normal is None:
        informed_prob_normal = INFORMED_PROB_NORMAL
    informed_prob = informed_prob_toxic if regime == "toxic" else informed_prob_normal
    is_informed = np.random.uniform() < informed_prob

    buy = False
    sell = False

    if is_informed:
        # Informed trader observes V with noise
        signal = V + SIGNAL_NOISE * np.random.normal()

        if signal > ask:
            inventory -= TRADE_SIZE
            cash += ask * TRADE_SIZE
            sell = True  # market maker's perspective: sell to informed buyer
        elif signal < bid:
            inventory += TRADE_SIZE
            cash -= bid * TRADE_SIZE
            buy = True   # market maker's perspective: buy from informed seller

    else:
        # probability of someone hitting our ask (they're buying from us)
        prob_ask_hit = A * DT * np.exp(-KAPPA * (ask - S))
        # probability of someone hitting our bid (they're selling to us)
        prob_bid_hit = A * DT * np.exp(-KAPPA * (S - bid))

    # ask hit → we sell to them → inventory decreases, cash increases
        if np.random.uniform() < prob_ask_hit:
            inventory -= TRADE_SIZE
            cash += ask * TRADE_SIZE
            sell = True

    # bid hit → we buy from them → inventory increases, cash decreases
        if np.random.uniform() < prob_bid_hit:
            inventory += TRADE_SIZE
            cash -= bid * TRADE_SIZE
            buy = True

    return {
        "inventory": inventory,
        "cash": cash,
        "buy": buy,
        "sell": sell,
        "informed": is_informed,
    }
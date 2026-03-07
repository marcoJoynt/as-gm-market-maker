import numpy as np
from config import N_STEPS, dT, T, S0, INITIAL_CASH, INITIAL_INVENTORY, PROB_NORMAL_TO_TOXIC, PROB_TOXIC_TO_NORMAL, KYLE_LAMBDA, TRADE_SIZE
from simulation import update_price, simulate_orders
from market_maker import get_quotes
from visualisation import plot_simulation


def run_simulation():
    S = S0
    V = S0
    cash = INITIAL_CASH
    inventory = INITIAL_INVENTORY
    regime = "normal"

    log = []

    for step in range(N_STEPS):
        # 1. Regime transition (asymmetric: rare into toxic, quick exit)
        p_switch = PROB_TOXIC_TO_NORMAL if regime == "toxic" else PROB_NORMAL_TO_TOXIC
        if np.random.uniform() < p_switch:
            regime = "toxic" if regime == "normal" else "normal"

        # 2. Price update — same dW for S and V
        S, V = update_price(S, V)

        # 3. Quotes
        time_remaining = T - step * dT
        bid, ask = get_quotes(S, inventory, time_remaining)

        # 4. Simulate orders
        result = simulate_orders(bid, ask, S, V, inventory, cash, regime)
        inventory = result["inventory"]
        cash = result["cash"]

        # 5. Permanent price impact if informed trade
        if result["informed"] and result["sell"]:  # informed buyer hit the ask
            S += KYLE_LAMBDA * TRADE_SIZE
        elif result["informed"] and result["buy"]:  # informed seller hit the bid
            S -= KYLE_LAMBDA * TRADE_SIZE

        pnl = cash + inventory * S

        log.append({
            "step": step,
            "S": S,
            "V": V,
            "bid": bid,
            "ask": ask,
            "spread": ask - bid,
            "inventory": inventory,
            "cash": cash,
            "pnl": pnl,
            "regime": regime,
            "informed": result["informed"],
        })

    return log


if __name__ == "__main__":
    import visualisation

    log = run_simulation()
    visualisation.plot_simulation(log)
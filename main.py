import numpy as np
import pandas as pd
from config import (
    N_STEPS,
    DT,
    T,
    S0,
    INITIAL_CASH,
    INITIAL_INVENTORY,
    PROB_NORMAL_TO_TOXIC,
    PROB_TOXIC_TO_NORMAL,
    KYLE_LAMBDA,
    TRADE_SIZE,
    SIGMA,
    GAMMA,
    INFORMED_PROB_NORMAL,
    INFORMED_PROB_TOXIC,
)
from simulation import update_price, simulate_orders
from market_maker import get_quotes
from visualisation import plot_simulation


def run_simulation(
    sigma=None,
    gamma=None,
    kyle_lambda=None,
    informed_prob_toxic=None,
    prob_normal_to_toxic=None,
):
    sigma = sigma if sigma is not None else SIGMA
    gamma = gamma if gamma is not None else GAMMA
    kyle_lambda = kyle_lambda if kyle_lambda is not None else KYLE_LAMBDA
    informed_prob_toxic = informed_prob_toxic if informed_prob_toxic is not None else INFORMED_PROB_TOXIC
    prob_normal_to_toxic = (
        prob_normal_to_toxic if prob_normal_to_toxic is not None else PROB_NORMAL_TO_TOXIC
    )

    S = S0
    V = S0
    cash = INITIAL_CASH
    inventory = INITIAL_INVENTORY
    regime = "normal"

    log = []

    for step in range(N_STEPS):
        # 1. Regime transition (asymmetric: rare into toxic, quick exit)
        p_switch = PROB_TOXIC_TO_NORMAL if regime == "toxic" else prob_normal_to_toxic
        if np.random.uniform() < p_switch:
            regime = "toxic" if regime == "normal" else "normal"

        # 2. Price update — same dW for S and V
        S, V = update_price(S, V, sigma=sigma)

        # 3. Quotes
        time_remaining = T - step * DT
        bid, ask = get_quotes(S, inventory, time_remaining, gamma=gamma, sigma=sigma)

        # 4. Simulate orders
        result = simulate_orders(
            bid, ask, S, V, inventory, cash, regime,
            informed_prob_toxic=informed_prob_toxic,
            informed_prob_normal=INFORMED_PROB_NORMAL,
        )
        inventory = result["inventory"]
        cash = result["cash"]

        # 5. Permanent price impact if informed trade
        S_at_trade = S  # mid at time of trade (before Kyle update)
        if result["informed"] and result["sell"]:  # informed buyer hit the ask
            S += kyle_lambda * TRADE_SIZE
        elif result["informed"] and result["buy"]:  # informed seller hit the bid
            S -= kyle_lambda * TRADE_SIZE

        pnl = cash + inventory * S
        trade_pnl = (ask - S_at_trade) if result["sell"] else (S_at_trade - bid) if result["buy"] else 0.0
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
            "trade_pnl": trade_pnl,
        })

    return pd.DataFrame(log)


if __name__ == "__main__":
    df = run_simulation()
    # steps_per_minute = int(N_STEPS / (T * 60 * 6.5))
    # returns = df["pnl"].iloc[::steps_per_minute].diff().dropna()
    # print(df["pnl"])
    # print(df["trade_pnl"])
    # print(returns)
    plot_simulation(df)
from config import N_STEPS, dT, T, S0, INITIAL_CASH, INITIAL_INVENTORY
from simulation import update_price, simulate_orders
from market_maker import get_quotes
from visualisation import plot_simulation


def run_simulation():
    S = S0
    cash = INITIAL_CASH
    inventory = INITIAL_INVENTORY

    log = []

    for step in range(N_STEPS):
        S = update_price(S)

        time_remaining = T - step * dT

        bid, ask = get_quotes(S, inventory, time_remaining)

        inventory, cash = simulate_orders(bid, ask, S, inventory, cash)

        pnl = cash + inventory * S

        log.append({
            "step": step,
            "S": S,
            "bid": bid,
            "ask": ask,
            "spread": ask - bid,
            "inventory": inventory,
            "cash": cash,
            "pnl": pnl,
        })

    return log


if __name__ == "__main__":
    import visualisation

    log = run_simulation()
    visualisation.plot_simulation(log)
import matplotlib.pyplot as plt


def plot_simulation(log):
    steps = [r["step"] for r in log]
    S = [r["S"] for r in log]
    bid = [r["bid"] for r in log]
    ask = [r["ask"] for r in log]
    spread = [r["spread"] for r in log]
    inventory = [r["inventory"] for r in log]
    pnl = [r["pnl"] for r in log]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Avellaneda-Stoikov Market Making Simulation")

    # mid price vs bid/ask
    ax = axes[0, 0]
    ax.plot(steps, S, label="mid", color="black", linewidth=1)
    ax.plot(steps, bid, label="bid", color="green", linewidth=0.8, linestyle="--")
    ax.plot(steps, ask, label="ask", color="red", linewidth=0.8, linestyle="--")
    ax.set_title("Mid Price vs Quotes")
    ax.set_xlabel("step")
    ax.set_ylabel("price")
    ax.legend()

    # inventory
    ax = axes[0, 1]
    ax.plot(steps, inventory, color="steelblue", linewidth=1)
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_title("Inventory")
    ax.set_xlabel("step")
    ax.set_ylabel("units")

    # cumulative pnl
    ax = axes[1, 0]
    ax.plot(steps, pnl, color="darkorange", linewidth=1)
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_title("Mark-to-Market P&L")
    ax.set_xlabel("step")
    ax.set_ylabel("pnl")

    # spread over time
    ax = axes[1, 1]
    ax.plot(steps, spread, color="purple", linewidth=1)
    ax.set_title("Spread Width")
    ax.set_xlabel("step")
    ax.set_ylabel("spread")
    ## Set y-axis limits to fit the spread values (for better visualization)
    spreads = [r["spread"] for r in log]
    ax.set_ylim(min(spreads) * 0.995, max(spreads) * 1.005)

    plt.tight_layout()
    plt.savefig("simulation.png", dpi=150)
    plt.show()
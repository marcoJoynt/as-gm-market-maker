import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def plot_simulation(log):
    steps = [r["step"] for r in log]
    S = [r["S"] for r in log]
    bid = [r["bid"] for r in log]
    ask = [r["ask"] for r in log]
    spread = [r["spread"] for r in log]
    inventory = [r["inventory"] for r in log]
    pnl = [r["pnl"] for r in log]

    fig = plt.figure(figsize=(12, 9))
    gs = GridSpec(3, 2, figure=fig, height_ratios=[1, 1, 1], hspace=0.35)

    # Top: mid price vs quotes (full width)
    ax_price = fig.add_subplot(gs[0, :])
    ax_price.fill_between(steps, bid, ask, color="gray", alpha=0.12)
    ax_price.plot(steps, S, label="mid", color="black", linewidth=1)
    ax_price.plot(steps, bid, label="bid", color="green", linewidth=0.8, linestyle="--")
    ax_price.plot(steps, ask, label="ask", color="red", linewidth=0.8, linestyle="--")
    ax_price.set_title("Mid Price vs Quotes")
    ax_price.set_ylabel("price")
    ax_price.set_xlabel("step")
    ax_price.legend()
    ax_price.grid(True, alpha=0.3)

    # Middle: inventory (full width, shared x with price)
    ax_inv = fig.add_subplot(gs[1, :], sharex=ax_price)
    ax_inv.plot(steps, inventory, color="steelblue", linewidth=1)
    ax_inv.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax_inv.set_title("Inventory")
    ax_inv.set_ylabel("units")
    ax_inv.set_xlabel("step")
    ax_inv.grid(True, alpha=0.3)

    # Bottom: spread and P&L side by side
    ax_spread = fig.add_subplot(gs[2, 0], sharex=ax_inv)
    ax_spread.plot(steps, spread, color="purple", linewidth=1)
    ax_spread.set_title("Spread Width")
    ax_spread.set_xlabel("step")
    ax_spread.set_ylabel("spread")
    ax_spread.grid(True, alpha=0.3)
    spread_vals = [r["spread"] for r in log]
    ax_spread.set_ylim(min(spread_vals) * 0.995, max(spread_vals) * 1.005)

    ax_pnl = fig.add_subplot(gs[2, 1], sharex=ax_inv)
    ax_pnl.plot(steps, pnl, color="darkorange", linewidth=1)
    ax_pnl.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax_pnl.set_title("Mark-to-Market P&L")
    ax_pnl.set_xlabel("step")
    ax_pnl.set_ylabel("pnl")
    ax_pnl.grid(True, alpha=0.3)

    fig.suptitle("Avellaneda–Stoikov Market Making Simulation", y=1.02)
    plt.tight_layout()
    plt.savefig("simulation.png", dpi=150, bbox_inches="tight")
    plt.show()
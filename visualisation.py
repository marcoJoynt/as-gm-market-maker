import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec


def plot_simulation(df):
    steps      = df["step"]
    S          = df["S"]
    V          = df["V"]
    bid        = df["bid"]
    ask        = df["ask"]
    spread     = df["spread"]
    inventory  = df["inventory"]
    pnl        = df["pnl"]
    regime     = df["regime"]

    # Build toxic period spans for shading
    toxic_spans = []
    in_toxic = False
    start = None
    for i, reg in enumerate(regime):
        if reg == "toxic" and not in_toxic:
            in_toxic = True
            start = steps.iloc[i]
        elif reg == "normal" and in_toxic:
            in_toxic = False
            toxic_spans.append((start, steps.iloc[i]))
    if in_toxic:
        toxic_spans.append((start, steps.iloc[-1]))

    def shade_toxic(ax):
        for (x0, x1) in toxic_spans:
            ax.axvspan(x0, x1, color="red", alpha=0.08, linewidth=0)

    fig = plt.figure(figsize=(12, 11))
    gs = GridSpec(4, 2, figure=fig, height_ratios=[1.2, 1, 0.6, 1], hspace=0.45)

    # ── Row 0: mid price + fundamental value + quotes (full width) ──
    ax_price = fig.add_subplot(gs[0, :])
    shade_toxic(ax_price)
    ax_price.fill_between(steps, bid, ask, color="gray", alpha=0.12)
    ax_price.plot(steps, V,   label="fundamental (V)", color="royalblue",  linewidth=0.9, linestyle=":")
    ax_price.plot(steps, S,   label="mid (S)",         color="black",      linewidth=1)
    ax_price.plot(steps, bid, label="bid",             color="green",      linewidth=0.8, linestyle="--")
    ax_price.plot(steps, ask, label="ask",             color="red",        linewidth=0.8, linestyle="--")
    ax_price.set_title("Mid Price vs Quotes")
    ax_price.set_ylabel("price")
    ax_price.set_xlabel("step")
    ax_price.legend(loc="upper left", fontsize=8)
    ax_price.grid(True, alpha=0.3)

    # ── Row 1: inventory (full width) ──
    ax_inv = fig.add_subplot(gs[1, :], sharex=ax_price)
    shade_toxic(ax_inv)
    ax_inv.plot(steps, inventory, color="steelblue", linewidth=1)
    ax_inv.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax_inv.set_title("Inventory")
    ax_inv.set_ylabel("units")
    ax_inv.set_xlabel("step")
    ax_inv.grid(True, alpha=0.3)

    # ── Row 2: regime indicator (full width) ──
    ax_regime = fig.add_subplot(gs[2, :], sharex=ax_price)
    regime_binary = (regime == "toxic").astype(int)
    ax_regime.fill_between(steps, regime_binary, color="red", alpha=0.4, step="post")
    ax_regime.set_yticks([0, 1])
    ax_regime.set_yticklabels(["normal", "toxic"], fontsize=8)
    ax_regime.set_title("Regime State")
    ax_regime.set_xlabel("step")
    ax_regime.grid(True, alpha=0.2)

    # ── Row 3: spread and P&L side by side ──
    ax_spread = fig.add_subplot(gs[3, 0], sharex=ax_price)
    shade_toxic(ax_spread)
    ax_spread.plot(steps, spread, color="purple", linewidth=1)
    ax_spread.set_title("Spread Width")
    ax_spread.set_xlabel("step")
    ax_spread.set_ylabel("spread")
    ax_spread.grid(True, alpha=0.3)
    ax_spread.set_ylim(spread.min() * 0.995, spread.max() * 1.005)

    ax_pnl = fig.add_subplot(gs[3, 1], sharex=ax_price)
    shade_toxic(ax_pnl)
    ax_pnl.plot(steps, pnl, color="darkorange", linewidth=1)
    ax_pnl.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax_pnl.set_title("Mark-to-Market P&L")
    ax_pnl.set_xlabel("step")
    ax_pnl.set_ylabel("pnl")
    ax_pnl.grid(True, alpha=0.3)

    # Legend for toxic shading
    toxic_patch = mpatches.Patch(color="red", alpha=0.15, label="toxic regime")
    fig.legend(handles=[toxic_patch], loc="upper right", fontsize=8, framealpha=0.7)

    fig.suptitle("Avellaneda–Stoikov + Glosten–Milgrom Adverse Selection", y=1.01)
    plt.tight_layout()
    plt.savefig("simulation.png", dpi=150, bbox_inches="tight")
    plt.show()
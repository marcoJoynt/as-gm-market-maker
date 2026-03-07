import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
import streamlit as st

# Simulation lives in main.py (single source of truth); we pass sidebar params into
# run_simulation() and only pull N_STEPS from config for metrics (e.g. Sharpe).
sns.set_theme(
    style="dark",
    rc={
        "axes.facecolor": "#161b22",
        "figure.facecolor": "#0e1117",
        "axes.edgecolor": "#30363d",
        "grid.color": "#21262d",
        "text.color": "#e6edf3",
        "axes.labelcolor": "#8b949e",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
    },
)

from main import run_simulation
from config import N_STEPS

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AS-GM Market Making Sim",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark theme styling ────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #161b22; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #e6edf3 !important;
    }
    [data-testid="stSidebar"] .stSlider label {
        color: #e6edf3 !important;
    }
    [data-testid="stSidebar"] h2 {
        color: #e6edf3 !important;
    }
    [data-testid="stSidebar"] div[data-testid="stSlider"] label,
    [data-testid="stSidebar"] [data-testid="stSlider"] span {
        color: #e6edf3 !important;
    }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 4px 0;
    }
    .metric-label { color: #8b949e; font-size: 12px; font-family: monospace; letter-spacing: 0.05em; }
    .metric-value { color: #e6edf3; font-size: 22px; font-weight: 600; font-family: monospace; }
    .metric-value.positive { color: #3fb950; }
    .metric-value.negative { color: #f85149; }
    h1, h2, h3 { color: #e6edf3 !important; }
    .stButton > button {
        background: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        font-family: monospace;
        font-weight: 600;
        width: 100%;
        padding: 12px;
        font-size: 14px;
    }
    .stButton > button:hover { background: #2ea043; }
</style>
""", unsafe_allow_html=True)

# ── Matplotlib dark style ─────────────────────────────────────────────────────
plt.style.use("dark_background")
CHART_BG    = "#0e1117"
PANEL_BG    = "#161b22"
GRID_COLOR  = "#21262d"
TEXT_COLOR  = "#8b949e"

# ── Sidebar — parameter controls ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Parameters")
    st.markdown("---")

    st.markdown("**Market dynamics**")
    sigma = st.slider("Volatility (σ)", 0.05, 0.50, 0.15, 0.01,
                      help="Brownian motion std dev of the price process")
    gamma = st.slider("Risk aversion (γ)", 0.01, 1.0, 0.2, 0.01,
                      help="A-S inventory penalty — higher γ = tighter inventory control")

    st.markdown("---")
    st.markdown("**Adverse selection**")
    kyle_lambda = st.slider("Kyle's λ", 0.01, 0.50, 0.05, 0.01,
                             help="Permanent price impact per informed trade")
    informed_prob_toxic = st.slider("Informed prob (toxic)", 0.10, 0.80, 0.30, 0.05,
                                     help="Probability of informed trader arrival in toxic regime")
    prob_normal_to_toxic = st.slider("P(normal → toxic)", 0.001, 0.05, 0.005, 0.001,
                                      format="%.3f",
                                      help="Probability of switching into toxic regime each step")

    st.markdown("---")
    run = st.button("▶  Run Simulation")

# ── Summary metrics ───────────────────────────────────────────────────────────
# Uses N_STEPS from config for Sharpe scaling; df comes from main.run_simulation() and
# includes trade_pnl (spread capture per trade, logged in main).
def compute_metrics(df):
    pnl_returns     = df["pnl"].diff().dropna()
    sharpe          = (pnl_returns.mean() / pnl_returns.std() * np.sqrt(N_STEPS)
                       if pnl_returns.std() > 0 else 0)
    total_trades    = ((df["spread"] > 0) & (df["inventory"].diff() != 0)).sum()
    informed_pct    = df["informed"].mean() * 100
    toxic_pct       = (df["regime"] == "toxic").mean() * 100
    final_pnl       = df["pnl"].iloc[-1]
    max_inventory   = df["inventory"].abs().max()
    return {
        "Final P&L":        (final_pnl,    f"{final_pnl:+.2f}"),
        "Sharpe":           (sharpe,        f"{sharpe:.2f}"),
        "Informed flow":    (0,             f"{informed_pct:.1f}%"),
        "Time in toxic":    (0,             f"{toxic_pct:.1f}%"),
        "Max |inventory|":  (0,             f"{max_inventory:.0f}"),
    }

# ── Chart ─────────────────────────────────────────────────────────────────────
def make_figure(df):
    steps     = df["step"]
    S         = df["S"]
    V         = df["V"]
    bid       = df["bid"]
    ask       = df["ask"]
    spread    = df["spread"]
    inventory = df["inventory"]
    pnl       = df["pnl"]
    regime    = df["regime"]

    # Toxic spans
    toxic_spans, in_toxic, start = [], False, None
    for i, reg in enumerate(regime):
        if reg == "toxic" and not in_toxic:
            in_toxic = True; start = steps.iloc[i]
        elif reg == "normal" and in_toxic:
            in_toxic = False; toxic_spans.append((start, steps.iloc[i]))
    if in_toxic:
        toxic_spans.append((start, steps.iloc[-1]))

    def shade(ax):
        for x0, x1 in toxic_spans:
            ax.axvspan(x0, x1, color="#f85149", alpha=0.07, linewidth=0)
        ax.set_facecolor(PANEL_BG)
        ax.grid(True, color=GRID_COLOR, linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor("#30363d")
        ax.tick_params(colors=TEXT_COLOR, labelsize=8)
        ax.xaxis.label.set_color(TEXT_COLOR)
        ax.yaxis.label.set_color(TEXT_COLOR)
        ax.title.set_color("#e6edf3")

    fig = plt.figure(figsize=(14, 12), facecolor=CHART_BG)
    gs  = GridSpec(4, 2, figure=fig, height_ratios=[1.2, 1, 0.5, 1], hspace=0.5)

    # Price
    ax_price = fig.add_subplot(gs[0, :])
    ax_price.fill_between(steps, bid, ask, color="#8b949e", alpha=0.08)
    ax_price.plot(steps, V,   color="#388bfd", linewidth=0.8, linestyle=":", label="fundamental (V)")
    ax_price.plot(steps, S,   color="#e6edf3", linewidth=1,                   label="mid (S)")
    ax_price.plot(steps, bid, color="#3fb950", linewidth=0.8, linestyle="--", label="bid")
    ax_price.plot(steps, ask, color="#f85149", linewidth=0.8, linestyle="--", label="ask")
    ax_price.set_title("Mid Price vs Quotes"); ax_price.set_ylabel("price"); ax_price.set_xlabel("step")
    ax_price.legend(loc="upper left", fontsize=7, framealpha=0.3)
    shade(ax_price)

    # Inventory
    ax_inv = fig.add_subplot(gs[1, :], sharex=ax_price)
    ax_inv.plot(steps, inventory, color="#388bfd", linewidth=1)
    ax_inv.axhline(0, color="#8b949e", linewidth=0.5, linestyle="--")
    ax_inv.set_title("Inventory"); ax_inv.set_ylabel("units"); ax_inv.set_xlabel("step")
    shade(ax_inv)

    # Regime
    ax_regime = fig.add_subplot(gs[2, :], sharex=ax_price)
    regime_binary = (regime == "toxic").astype(int)
    ax_regime.fill_between(steps, regime_binary, color="#f85149", alpha=0.5, step="post")
    ax_regime.set_yticks([0, 1]); ax_regime.set_yticklabels(["normal", "toxic"], fontsize=7)
    ax_regime.set_title("Regime State"); ax_regime.set_xlabel("step")
    shade(ax_regime)

    # Spread
    ax_spread = fig.add_subplot(gs[3, 0], sharex=ax_price)
    ax_spread.plot(steps, spread, color="#bc8cff", linewidth=1)
    ax_spread.set_title("Spread Width"); ax_spread.set_xlabel("step"); ax_spread.set_ylabel("spread")
    ax_spread.set_ylim(spread.min() * 0.995, spread.max() * 1.005)
    shade(ax_spread)

    # P&L
    ax_pnl = fig.add_subplot(gs[3, 1], sharex=ax_price)
    ax_pnl.plot(steps, pnl, color="#e3b341", linewidth=1)
    ax_pnl.axhline(0, color="#8b949e", linewidth=0.5, linestyle="--")
    ax_pnl.set_title("Mark-to-Market P&L"); ax_pnl.set_xlabel("step"); ax_pnl.set_ylabel("pnl")
    shade(ax_pnl)

    toxic_patch = mpatches.Patch(color="#f85149", alpha=0.4, label="toxic regime")
    fig.legend(handles=[toxic_patch], loc="upper right", fontsize=7, framealpha=0.3,
               facecolor=PANEL_BG, edgecolor="#30363d", labelcolor="#e6edf3")

    fig.suptitle("Avellaneda–Stoikov  ×  Glosten–Milgrom Adverse Selection",
                 color="#e6edf3", fontsize=13, y=1.01)
    plt.tight_layout()
    return fig


def _style_seaborn_ax(ax):
    ax.set_facecolor(PANEL_BG)
    ax.grid(True, color=GRID_COLOR, linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color("#e6edf3")


def make_seaborn_panels(df):
    """Return two figures: spread capture (trade P&L) by regime, and inventory violin by regime."""
    # Figure 1 — Spread capture per trade by regime
    # We plot trade_pnl (ask - S on sells, S - bid on buys), not cash.diff(), because
    # cash moves by full notional (~100) every trade; trade_pnl is order-of-spread and
    # separates adverse selection: informed flow → worse/near-zero, noise → cluster near half-spread.
    # Filter to steps where a trade occurred so the KDE is over realised spread capture only.
    df_trades = df[df["trade_pnl"] != 0][["trade_pnl", "regime"]].copy()

    fig1, ax1 = plt.subplots(figsize=(14, 4), facecolor=CHART_BG)
    sns.kdeplot(
        data=df_trades,
        x="trade_pnl",
        hue="regime",
        palette={"normal": "#388bfd", "toxic": "#f85149"},
        fill=True,
        alpha=0.3,
        linewidth=1.5,
        ax=ax1,
    )
    ax1.axvline(0, color="#8b949e")
    ax1.set_title("Spread Capture per Trade — Normal vs Toxic Regime")
    _style_seaborn_ax(ax1)
    plt.tight_layout()

    # Figure 2 — Inventory distribution by regime
    # Toxic: more directional (peaked); normal: wider, mean-reverting. No filtering by trade.
    fig2, ax2 = plt.subplots(figsize=(14, 4), facecolor=CHART_BG)
    sns.violinplot(
        data=df,
        x="regime",
        y="inventory",
        palette={"normal": "#388bfd", "toxic": "#f85149"},
        inner="quart",
        ax=ax2,
    )
    ax2.set_title("Inventory Distribution by Regime")
    _style_seaborn_ax(ax2)
    plt.tight_layout()

    return fig1, fig2


# ── Main layout ───────────────────────────────────────────────────────────────
# When "Run Simulation" is clicked we call main.run_simulation() with sidebar params;
# main uses config for anything not overridden (e.g. PROB_TOXIC_TO_NORMAL, INFORMED_PROB_NORMAL).
st.markdown("# AS-GM Market Making Simulator")
st.markdown("<p style='color:#8b949e; font-family:monospace; margin-top:-12px;'>Avellaneda–Stoikov quoting under Glosten–Milgrom adverse selection</p>", unsafe_allow_html=True)
st.markdown("---")

if run:
    with st.spinner("Running simulation..."):
        df      = run_simulation(sigma, gamma, kyle_lambda, informed_prob_toxic, prob_normal_to_toxic)
        metrics = compute_metrics(df)

    # Metric cards
    cols = st.columns(5)
    labels = list(metrics.keys())
    for i, col in enumerate(cols):
        val, display = metrics[labels[i]]
        css_class = "positive" if (labels[i] == "Final P&L" and val > 0) else \
                    "negative" if (labels[i] == "Final P&L" and val < 0) else ""
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{labels[i]}</div>
            <div class="metric-value {css_class}">{display}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("###")
    st.pyplot(make_figure(df), use_container_width=True)
    st.markdown("###")
    fig1, fig2 = make_seaborn_panels(df)
    col1, col2 = st.columns(2)
    col1.pyplot(fig1, use_container_width=True)
    col2.pyplot(fig2, use_container_width=True)

else:
    # No run yet: show prompt to set params and click Run Simulation.
    st.markdown("""
    <div style='text-align:center; padding: 80px 0; color:#8b949e; font-family:monospace;'>
        <div style='font-size:48px; margin-bottom:16px;'>⟳</div>
        <div style='font-size:16px;'>Set parameters in the sidebar and click <strong style='color:#3fb950;'>Run Simulation</strong></div>
    </div>
    """, unsafe_allow_html=True)
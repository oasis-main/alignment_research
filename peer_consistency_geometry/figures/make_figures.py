"""Generate the three paper figures for `writing/peer_consistency_deception_divergence.md`.

Outputs (PNG + PDF) under this directory:
  fig1_sheaf_complex.{png,pdf}        — sheaf complex schematic (0/1/2-cells, δ⁰, δ¹)
  fig2_auc_scoreboard.{png,pdf}       — length-matched AUC across LIARS'-BENCH configs at both panel scales + alignment-faking-rl
  fig3_reasoning_vs_action.{png,pdf}  — where-the-construct-lives 2×2 quadrant

Run from the alignment_research repo:
    python peer_consistency_geometry/figures/make_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"


def load_auc(stem: str, kind: str = "length_matched") -> tuple[float, float]:
    """Return (mean, std) of δ¹c AUC from a results JSON."""
    r = json.loads((RESULTS / f"peer_sheaf_e6_modal_{stem}.json").read_text())
    block = r[kind]
    return float(block["auc_mean"]), float(block["auc_std"])


# ---------------------------------------------------------------------------
# Figure 1 — Sheaf complex schematic
# ---------------------------------------------------------------------------

def fig1_sheaf_complex(out_png: Path, out_pdf: Path):
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-2.2, 1.8)
    ax.set_aspect("equal")
    ax.axis("off")

    # Three 0-cells (models)
    nodes = {
        "Yi-1.5-9B":  np.array([-1.30,  0.80]),
        "Zephyr-7B":  np.array([ 1.30,  0.80]),
        "Qwen2.5-7B": np.array([ 0.00, -0.80]),
    }
    short = {"Yi-1.5-9B": "i", "Zephyr-7B": "j", "Qwen2.5-7B": "k"}

    # Triangle interior (the 2-cell)
    tri = plt.Polygon([nodes["Yi-1.5-9B"], nodes["Zephyr-7B"], nodes["Qwen2.5-7B"]],
                      closed=True, facecolor="#dceaf6", edgecolor="none", zorder=0, alpha=0.7)
    ax.add_patch(tri)

    # 1-cells (one curved arrow per ordered pair). Direction matters.
    R = 0.22  # node radius
    pairs = [
        ("Yi-1.5-9B", "Zephyr-7B", 0.20),   # top edge
        ("Zephyr-7B", "Qwen2.5-7B", 0.20),  # right edge
        ("Qwen2.5-7B", "Yi-1.5-9B", 0.20),  # left edge
    ]
    for a, b, rad in pairs:
        pa, pb = nodes[a], nodes[b]
        # shorten by node radius so arrow heads sit at boundary
        v = (pb - pa) / np.linalg.norm(pb - pa)
        start = pa + v * R
        end   = pb - v * R
        ax.annotate(
            "", xy=end, xytext=start,
            arrowprops=dict(arrowstyle="-|>", lw=1.7, color="#2c3e50",
                            connectionstyle=f"arc3,rad={rad}"),
            zorder=1,
        )
        # label at midpoint, offset perpendicular to the curve
        mid = 0.5 * (pa + pb)
        perp = np.array([-v[1], v[0]])  # rotate 90°
        lbl = mid + perp * 0.32
        ax.text(lbl[0], lbl[1],
                rf"$\rho_{{{short[a]}\to {short[b]}}}$",
                fontsize=10.5, ha="center", va="center", color="#2c3e50",
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#cccccc", lw=0.5, alpha=0.95))

    # 0-cells (drawn over edges/triangle)
    for name, pt in nodes.items():
        circ = plt.Circle(pt, R, facecolor="white", edgecolor="#2c3e50", lw=1.8, zorder=2)
        ax.add_patch(circ)
        ax.text(pt[0], pt[1] + 0.05, short[name], fontsize=12, ha="center", va="center",
                zorder=3, color="#2c3e50", weight="bold")
        ax.text(pt[0], pt[1] - 0.06, name, fontsize=7.5, ha="center", va="top",
                zorder=3, color="#34495e")

    # Center label for the 2-cell
    centroid = np.mean(list(nodes.values()), axis=0)
    ax.text(centroid[0], centroid[1], r"2-cell $(i,j,k)$",
            fontsize=10.5, ha="center", va="center", color="#34495e", style="italic")

    # Caption with the coboundary definitions — beneath the diagram
    cap = (
        "0-cells: models    1-cells: directed pairs $(i,j)$ with stalk $\\mathbb{R}^{d_j}$\n"
        r"$(\delta^0 s)_{(i,j)} = W_{ij}\, s_i - s_j$"
        "    → resolvable cross-model gap (linear part of the pairwise residual)\n"
        r"$(\delta^1 c)_{(i,j,k)} = \rho_{j \to k}(c_{(i,j)}) + c_{(j,k)} - c_{(i,k)}$"
        "\n    → cocycle violation; non-zero iff translations don't commute around the triangle"
    )
    ax.text(0.0, -1.65, cap, fontsize=9.0, ha="center", va="top", color="#34495e",
            bbox=dict(boxstyle="round,pad=0.4", fc="#f7f7f7", ec="#cccccc", lw=0.6))

    ax.set_title("Peer-consistency sheaf on a three-model panel",
                 fontsize=12, color="#2c3e50", pad=6)
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2 — AUC scoreboard
# ---------------------------------------------------------------------------

# Small-panel length-matched numbers come from the upstream SGB-019/020 sweep
# (ai_research/.../shared/results/peer_sheaf_e6_<cfg>_lenmatch.json). They are
# inlined here as constants because the small-panel JSONs are not vendored — the
# 7-9B JSONs are the source-of-truth for the paper. Re-derive via the upstream
# script `experiments/E6_liars.py --length-match` if needed.
SMALL_LENMATCH = {
    "convincing-game":      (0.678, 0.034),
    "insider-trading":      (0.555, 0.008),
    "instructed-deception": (0.536, 0.013),
}


def fig2_auc_scoreboard(out_png: Path, out_pdf: Path):
    cfgs = ["convincing-game", "insider-trading", "instructed-deception"]
    labels = ["convincing-game\n(persuasion)", "insider-trading\n(strategic)", "instructed-deception\n(overt lie)"]
    small = [SMALL_LENMATCH[c] for c in cfgs]
    big   = [load_auc(c, "length_matched") for c in cfgs]

    af_r, af_r_std = load_auc("alignment-faking-reasoning", "length_matched")
    af_red, af_red_std = load_auc("alignment-faking-reasoning-redacted", "length_matched")

    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(11.0, 4.6),
        gridspec_kw={"width_ratios": [2.4, 1.0], "wspace": 0.32},
    )

    # ---- LEFT: LIARS'-BENCH small vs 7-9B ---------------------------------
    x = np.arange(len(cfgs))
    w = 0.36
    bars1 = axL.bar(x - w/2, [m for m, _ in small], w,
                    yerr=[s for _, s in small], capsize=3,
                    label="small panel (<2B)", color="#a9b7c6", edgecolor="#506478")
    bars2 = axL.bar(x + w/2, [m for m, _ in big],   w,
                    yerr=[s for _, s in big],   capsize=3,
                    label="7–9B panel",          color="#3b6e8f", edgecolor="#1f3d52")
    axL.axhline(0.5, color="#666666", linestyle="--", lw=0.8, alpha=0.7)
    axL.text(len(cfgs) - 0.55, 0.503, "chance (AUC = 0.5)", fontsize=8,
             color="#666666", va="bottom", ha="right")
    axL.set_ylim(0.45, 0.78)
    axL.set_xticks(x)
    axL.set_xticklabels(labels, fontsize=10)
    axL.set_ylabel(r"$\|\delta^1 c\|$ AUC (length-matched)", fontsize=10.5)
    axL.set_title("LIARS'-BENCH responses: capacity gates the signal",
                  fontsize=11, pad=8, color="#2c3e50")
    axL.legend(loc="upper right", fontsize=9.5, frameon=False)

    axL.annotate("n.s.", xy=(1 - w/2, small[1][0] + small[1][1] + 0.005),
                 ha="center", va="bottom", fontsize=8.5, color="#a04040", weight="bold")

    for bars, vals in [(bars1, small), (bars2, big)]:
        for bar, (m, _) in zip(bars, vals):
            axL.text(bar.get_x() + bar.get_width()/2, m + 0.012,
                     f"{m:.2f}", ha="center", va="bottom", fontsize=9, color="#1f3d52")

    # ---- RIGHT: alignment-faking-rl reasoning, sign-flipped --------------
    xi = np.arange(2)
    bars3 = axR.bar(xi, [af_r, af_red], 0.55,
                    yerr=[af_r_std, af_red_std], capsize=3,
                    color=["#7f3a3a", "#c7a0a0"], edgecolor="#4a2222")
    axR.axhline(0.5, color="#666666", linestyle="--", lw=0.8, alpha=0.7)
    axR.set_xticks(xi)
    axR.set_xticklabels(["reasoning", "+ cue\nredacted"], fontsize=10)
    axR.set_ylabel("AUC", fontsize=10.5)
    axR.set_ylim(0.30, 0.58)
    axR.set_title("alignment-faking-rl\n(reasoning, 7-9B)", fontsize=11, pad=8, color="#4a2222")
    for bar, m in zip(bars3, [af_r, af_red]):
        axR.text(bar.get_x() + bar.get_width()/2, m + 0.012,
                 f"{m:.2f}", ha="center", va="bottom", fontsize=9, color="#4a2222")
    axR.text(0.5, 0.555, "sign-flipped: AUC < 0.5\n→ deceptive reasoning is MORE\npeer-consistent (convergence)",
             ha="center", va="top", fontsize=8, color="#7f3a3a",
             transform=axR.transAxes,
             bbox=dict(boxstyle="round,pad=0.3", fc="#f7eded", ec="#c7a0a0", lw=0.6))

    fig.suptitle("Length-matched cross-model divergence on deceptive content",
                 fontsize=12, y=1.02, color="#2c3e50")
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3 — Reasoning vs Action quadrant
# ---------------------------------------------------------------------------

def fig3_reasoning_vs_action(out_png: Path, out_pdf: Path):
    # 2 datasets × 2 traces, all 7-9B length-matched
    cells = {
        ("insider-trading",          "reasoning"): load_auc("insider-trading-reasoning", "length_matched"),
        ("insider-trading",          "action"):    load_auc("insider-trading-action",    "length_matched"),
        ("alignment-faking-rl",      "reasoning"): load_auc("alignment-faking-reasoning","length_matched"),
        ("alignment-faking-rl",      "action"):    load_auc("alignment-faking-output",   "length_matched"),
    }
    datasets = ["insider-trading", "alignment-faking-rl"]
    traces = ["reasoning", "action"]

    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    w = 0.36
    x = np.arange(len(datasets))
    colors = {"reasoning": "#b85c3f", "action": "#4a8fc3"}

    for i, t in enumerate(traces):
        means = [cells[(d, t)][0] for d in datasets]
        stds  = [cells[(d, t)][1] for d in datasets]
        bars = ax.bar(x + (i - 0.5) * w, means, w,
                      yerr=stds, capsize=3,
                      label=t, color=colors[t], edgecolor="black", lw=0.4)
        for bar, m in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width()/2, m + (0.012 if m >= 0.5 else -0.018),
                    f"{m:.2f}",
                    ha="center", va="bottom" if m >= 0.5 else "top",
                    fontsize=9, color=("black" if m >= 0.5 else "white"),
                    weight="bold" if m < 0.5 else "normal")

    ax.axhline(0.5, color="#666666", linestyle="--", lw=0.8, alpha=0.7)
    ax.text(len(datasets) - 0.5, 0.503, "chance / no separation",
            fontsize=7.5, color="#666666", va="bottom", ha="right")

    ax.set_xticks(x)
    ax.set_xticklabels(
        ["insider-trading\n(label is about the ACTION)",
         "alignment-faking-rl\n(label is about the REASONING)"],
        fontsize=9.5,
    )
    ax.set_ylabel(r"$\|\delta^1 c\|$ AUC (7-9B, length-matched)", fontsize=10)
    ax.set_ylim(0.28, 0.82)
    ax.set_title("The signal lives where the label lives", fontsize=12, pad=10, color="#2c3e50")
    ax.legend(loc="upper left", fontsize=9.5, frameon=False, title="trace embedded",
              bbox_to_anchor=(0.02, 0.98))

    # Annotate sign-flipped + divergence quadrants — place inside plot bounds
    ax.annotate(
        "AUC > 0.5:\ndeceptive action\nMORE peer-divergent",
        xy=(0 + 0.5*w, 0.640), xytext=(0.30, 0.78),
        fontsize=8.5, color="#1f4a6a", ha="center", va="top",
        arrowprops=dict(arrowstyle="-|>", color="#1f4a6a", lw=0.8),
        bbox=dict(boxstyle="round,pad=0.25", fc="#eef4f9", ec="#7fa8c4", lw=0.5),
    )
    ax.annotate(
        "AUC < 0.5:\ndeceptive reasoning\nMORE peer-consistent\n(convergence)",
        xy=(1 - 0.5*w, 0.384), xytext=(1.32, 0.34),
        fontsize=8.5, color="#7f3a3a", ha="center", va="bottom",
        arrowprops=dict(arrowstyle="-|>", color="#7f3a3a", lw=0.8),
        bbox=dict(boxstyle="round,pad=0.25", fc="#f7eded", ec="#c7a0a0", lw=0.5),
    )

    fig.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    targets = [
        ("fig1_sheaf_complex",       fig1_sheaf_complex),
        ("fig2_auc_scoreboard",      fig2_auc_scoreboard),
        ("fig3_reasoning_vs_action", fig3_reasoning_vs_action),
    ]
    for stem, fn in targets:
        png = HERE / f"{stem}.png"
        pdf = HERE / f"{stem}.pdf"
        fn(png, pdf)
        print(f"wrote {png.name} + {pdf.name}")


if __name__ == "__main__":
    main()

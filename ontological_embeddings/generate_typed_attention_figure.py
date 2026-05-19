#!/usr/bin/env python3
"""Typed-attention figure for the Sheaf-KG paper.

Two honest panels, no training required:

  (a) The Olog reachability structure that typed attention (B) enforces.
      For the 23-type multi-domain vocabulary (business / academic /
      healthcare / e-commerce + one cross-domain bridge), the (B) mask
      admits a query->key attention pair iff the key type is reachable
      from the query type under the Olog. The mask is block-structured:
      information flow is confined within a domain plus the explicit
      Patient->Customer bridge. This is the semantic-space structure
      the typed-attention layer imposes.

  (b) The measured effect, from results/attention_ablation_v2.json
      (seed 42, 300 epochs, 64-d): mean attention mass on type-invalid
      vs type-valid key pairs, standard vs typed attention.

Output: paper/figures/typed_attention.pdf
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from attention_ablation_experiment import ONTOLOGIES, DOMAIN_BRIDGES, build_reachability  # noqa: E402

DOMAIN_ORDER = ["business", "academic", "healthcare", "ecommerce"]


def main():
    # ---- panel (a): reachability mask -------------------------------------
    ordered, domain_spans = [], []
    for dom in DOMAIN_ORDER:
        start = len(ordered)
        for t in ONTOLOGIES[dom]["types"]:
            if t not in ordered:
                ordered.append(t)
        domain_spans.append((dom, start, len(ordered)))

    all_aspects = []
    for ont in ONTOLOGIES.values():
        all_aspects.extend(ont["aspects"])
    all_aspects.extend(DOMAIN_BRIDGES)
    reach = build_reachability(all_aspects)

    n = len(ordered)
    M = np.zeros((n, n))
    for i, ti in enumerate(ordered):
        for j, tj in enumerate(ordered):
            if ti == tj or tj in reach.get(ti, set()):
                M[i, j] = 1.0

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8),
                             gridspec_kw={"width_ratios": [1.15, 0.85]})

    ax = axes[0]
    ax.imshow(M, cmap="Blues", vmin=0, vmax=1, aspect="equal")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(ordered, rotation=90, fontsize=6)
    ax.set_yticklabels(ordered, fontsize=6)
    for _, s, e in domain_spans:
        ax.add_patch(Rectangle((s - 0.5, s - 0.5), e - s, e - s,
                               fill=False, edgecolor="#d95f02", linewidth=1.8))
    ax.set_title("(a) Olog reachability mask enforced by (B)\n"
                 "shaded = attention permitted; boxes = domain blocks",
                 fontsize=9)
    ax.set_xlabel("key type", fontsize=8)
    ax.set_ylabel("query type", fontsize=8)

    # ---- panel (b): measured attention mass -------------------------------
    with open(os.path.join(SCRIPT_DIR, "results", "attention_ablation_v2.json")) as f:
        abl = json.load(f)
    by_model = {r["model"]: r for r in abl["results"]}
    std, olog = by_model["Standard Attention"], by_model["Ontological Attention"]

    ax = axes[1]
    cats = ["invalid-type\nattention mass", "valid-type\nattention mass"]
    std_vals = [std["invalid_attn_weight"], std["valid_attn_weight"]]
    olog_vals = [olog["invalid_attn_weight"], olog["valid_attn_weight"]]
    x = np.arange(len(cats))
    w = 0.36
    b1 = ax.bar(x - w / 2, std_vals, w, label="standard attention", color="#9ecae1")
    b2 = ax.bar(x + w / 2, olog_vals, w, label="typed attention (B)", color="#d95f02")
    for bars in (b1, b2):
        for rect in bars:
            ax.annotate(f"{rect.get_height():.3f}",
                        (rect.get_x() + rect.get_width() / 2, rect.get_height()),
                        ha="center", va="bottom", fontsize=7,
                        xytext=(0, 1.5), textcoords="offset points")
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel("mean softmax attention mass", fontsize=8)
    ax.set_ylim(0, 0.62)
    ax.set_title("(b) Measured effect (seed 42, 300 epochs)\n"
                 "typed attention drives invalid mass to zero", fontsize=9)
    ax.legend(fontsize=8, loc="upper center")
    ax.grid(True, axis="y", alpha=0.3)
    ax.tick_params(labelsize=8)

    fig.tight_layout()
    fig_dir = os.path.join(SCRIPT_DIR, "paper", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    out = os.path.join(fig_dir, "typed_attention.pdf")
    fig.savefig(out, bbox_inches="tight")
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()

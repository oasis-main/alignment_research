"""
experiment_cyclic_stress.py

Stress test for (B') reachability masking on a cyclic Olog.

When the TLTS contains a cycle, the reachability closure becomes
near-universal: every type can reach every other type. (B') —
which admits any label whose target is reachable — therefore
admits essentially every label, collapsing toward (A)-level
soundness. (D) — direct-edge admissibility — remains unaffected.

This is the limit case of the theoretical finding from
experiment_loci_comparison: reachability ≠ admissibility.

Run:
    venv/bin/python experiment_cyclic_stress.py
"""

from __future__ import annotations
import numpy as np

from experiment_loci_comparison import (
    cyclic_ecommerce_tlts, relational_ecommerce_tlts,
    good_prior, bad_prior, VARIANTS,
    evaluate_variant, reachability_closure,
)


def report_reachability(tlts, label: str):
    closure = reachability_closure(tlts)
    n = len(tlts.types)
    total_pairs = n * n
    reachable_pairs = sum(len(closure[t]) for t in tlts.types)
    print(f"  {label}: {reachable_pairs}/{total_pairs} ordered pairs reachable "
          f"({reachable_pairs/total_pairs*100:.1f}%)")


def run(tlts, name: str):
    print(f"\n>>> {name}")
    print(f"    |T|={len(tlts.types)}  |L|={len(tlts.labels)}  |δ|={len(tlts.delta)}")
    report_reachability(tlts, "    reachability")

    for prior_name, prior_fn in [("GOOD", good_prior), ("BAD ", bad_prior)]:
        prior = prior_fn(tlts, np.random.default_rng(123))
        rows = []
        for vname, vfn in VARIANTS.items():
            rows.append(evaluate_variant(vname, vfn, prior, tlts, n_traj=1000, max_len=12, seed=42))
        print(f"\n    {prior_name} prior:")
        print(f"      {'variant':<8} {'sound':>7} {'logP/traj':>11} {'len':>5} {'µs/step':>8}")
        for r in rows:
            print(f"      {r.name:<8} {r.soundness_rate*100:>6.1f}% "
                  f"{r.mean_log_p:>11.3f} {r.mean_traj_len:>5.2f} "
                  f"{r.seconds_per_step*1e6:>8.2f}")


def main():
    print("=" * 80)
    print("  CYCLIC OLOG STRESS TEST — (B') under near-universal reachability")
    print("=" * 80)

    run(relational_ecommerce_tlts(), "ACYCLIC (baseline, for comparison)")
    run(cyclic_ecommerce_tlts(),     "CYCLIC (Delivery → Customer)")

    print("\n" + "=" * 80)
    print("  Prediction: (B') soundness on the cyclic Olog should drop toward (A)")
    print("  because reachability becomes near-universal and the mask admits")
    print("  almost any label. (D) remains 100% because direct-edge admissibility")
    print("  is unaffected by cycle structure.")
    print("=" * 80)


if __name__ == "__main__":
    main()

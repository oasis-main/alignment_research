"""Audit re-run of the reachability (B') result with set iteration order fixed (sorted), 10 numpy seeds, 3 hash seeds."""
import sys, statistics as stt
sys.path.insert(0, '.')
import experiment_loci_comparison as E
def snd(tlts, prior, v, seed):
    if hasattr(tlts, "_closure"): del tlts._closure
    return E.evaluate_variant(v, E.VARIANTS[v], prior, tlts, n_traj=1000, max_len=12, seed=seed).soundness_rate
if __name__ == "__main__":
    import numpy as np
    out = {}
    for name, mk in (("acyclic", E.relational_ecommerce_tlts), ("cyclic", E.cyclic_ecommerce_tlts)):
        if mk is None:
            continue
        for pn, pf in (("GOOD", E.good_prior), ("BAD", E.bad_prior)):
            tl = mk(); pr = pf(tl, np.random.default_rng(123))
            for v in ("A", "B'", "D"):
                xs = [snd(tl, pr, v, s) for s in range(42, 52)]
                print(f"{name:8} {pn:4} {v:3} mean {stt.mean(xs)*100:5.1f}%  min {min(xs)*100:5.1f}  max {max(xs)*100:5.1f}", flush=True)

"""UNSCORED calibration for pass 12b (room check for the monitor lever). Seeds 100-129, which no scored run uses.
Question: does raising prep-phase noticing `a` (the existing per-observer, per-round probability that a preparing
mover is noticed; 0.0 in cell S) change takeover at all? If not, a standing-collection monitor has no room in cell S
and the 12b design must act on a different lever. Not a result; used only to fix the cells before the prereg."""
import json
from multiprocessing import Pool
import tournament11 as t11
import tournament12 as t12

ARMS = {}
for a in (0.0, 0.1, 0.25, 0.5, 1.0):
    ARMS[f"d0_a{a}"] = ("d0", a)
for a in (0.0, 0.25, 1.0):
    ARMS[f"club.5_b1_a{a}"] = ("club", a)


def job(x):
    arm, s = x
    kind, a = ARMS[arm]
    cfg = t11.cell(**t11.SCELL, aware=True, a=a) if kind == "d0" else t12.a12cell(0.5, 1.0, 1.0, a=a)
    r = t12.run12(cfg, s)
    return arm, s, (float(r["dw"]), float(r["att"]), float(r["deaths"]), r["first"])


if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for arm, s, v in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(100, 130)]):
            out.setdefault(arm, []).append(v)
    for arm in ARMS:
        v = out[arm]; n = len(v)
        fr = [x[3] for x in v if x[3] is not None]
        print(f"{arm:16s} takeover {sum(x[0] for x in v)/n:.3f}  attempts {sum(x[1] for x in v)/n:5.2f}  deaths {sum(x[2] for x in v)/n:5.2f}  first {sum(fr)/len(fr) if fr else float('nan'):5.1f}  n={n}")

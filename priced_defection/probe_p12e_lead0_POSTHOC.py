"""POST HOC, UNSCORED (written after the tie was found: runner-up ratio 0.79999999999999982 vs access_thresh 0.8 in cell Q).
No monitors, g_def=0, seeds 8100-8139. Vary lead0 across the tie, and access_thresh across the tie."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12e as t
ARMS = [("lead0=1.20", dict(lead0=1.20)), ("lead0=1.24", dict(lead0=1.24)), ("lead0=1.2499", dict(lead0=1.2499)),
        ("lead0=1.25 (baseline)", dict()), ("lead0=1.2501", dict(lead0=1.2501)), ("lead0=1.26", dict(lead0=1.26)),
        ("lead0=1.30", dict(lead0=1.30)), ("thresh=.79", dict(access_thresh=0.79)), ("thresh=.81", dict(access_thresh=0.81))]
def job(x):
    i, s = x
    r = t.run12e(t.cell_Q(**ARMS[i][1]), s, {}, 0.0)
    return i, (float(r["dw"]), float(r["att"]), float(r["deaths"]))
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for i, v in p.imap_unordered(job, [(i, s) for i in range(len(ARMS)) for s in range(8100, 8140)]):
            out.setdefault(i, []).append(v)
    for i, (name, _) in enumerate(ARMS):
        v = out[i]; n = len(v)
        print(f"{name:24} takeover {sum(x[0] for x in v)/n:.3f}  att {sum(x[1] for x in v)/n:5.2f}  deaths {sum(x[2] for x in v)/n:5.2f}  n={n}")

"""POST HOC, UNSCORED. After the tie diagnosis (cell Q lead0=1.25 puts the runner-up at exactly 1/1.25=0.8=access_thresh of the frontier).
Is there a nearby cell where takeover varies smoothly? No monitors, g_def=0, seeds 8200-8239 (new seeds)."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12e as t
ARMS = [(f"step thr.8 lead0={l}", dict(lead0=l)) for l in (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 2.0)]
ARMS += [(f"step thr.7 lead0={l}", dict(lead0=l, access_thresh=0.7)) for l in (1.25, 1.4, 1.5)]
ARMS += [(f"step thr.9 lead0={l}", dict(lead0=l, access_thresh=0.9)) for l in (1.1, 1.25)]
ARMS += [(f"smooth ps={p} lead0={l}", dict(lead0=l, access_rule="smooth", price_scale=p)) for p in (1.0, 2.0) for l in (1.0, 1.25, 1.5)]
def job(x):
    i, s = x
    r = t.run12e(t.cell_Q(**ARMS[i][1]), s, {}, 0.0)
    return i, (float(r["dw"]), float(r["att"]), float(r["deaths"]))
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for i, v in p.imap_unordered(job, [(i, s) for i in range(len(ARMS)) for s in range(8200, 8240)]):
            out.setdefault(i, []).append(v)
    for i, (name, _) in enumerate(ARMS):
        v = out[i]; n = len(v)
        print(f"{name:28} takeover {sum(x[0] for x in v)/n:.3f}  att {sum(x[1] for x in v)/n:5.2f}  deaths {sum(x[2] for x in v)/n:5.2f}  n={n}", flush=True)

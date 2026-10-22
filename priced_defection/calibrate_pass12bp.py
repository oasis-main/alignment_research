"""UNSCORED calibration for pass 12b' (quiet accumulator). Seeds 4100-4129, which no scored run uses.
Cell S starts the mover with lead0=2.5, so nothing is 'accumulated'. Question: which (lead0, c_grow) gives a cell where the
eventual attacker's lead GROWS before it moves, takeover is interior (0.2-0.8) and the first attempt is late?
Reads cap/frontier at the first attempt from tournament12's recorder. Not a result."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament11 as t11
import tournament12 as t12
ARMS = {}
for lead in (1.0, 1.25, 1.5):
    for cg in (0.1, 0.3):
        ARMS[f"lead{lead}_cg{cg}"] = dict(lead0=lead, c_grow=cg)
def job(x):
    arm, s = x
    cfg = t11.cell(**dict(t11.SCELL, **ARMS[arm]), aware=True)
    r = t12.run12(cfg, s)
    first = r["att_rec"][0] if r["att_rec"] else None
    return arm, (float(r["dw"]), float(r["att"]), r["first"], (first[2]/first[3]) if first and first[3] > 0 else None, r.get("lead0"), r.get("lead_end"))
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for arm, v in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(4100, 4130)]):
            out.setdefault(arm, []).append(v)
    for arm in ARMS:
        v = out[arm]; n = len(v)
        fr = [x[2] for x in v if x[2] is not None]; lr = [x[3] for x in v if x[3] is not None]
        l0 = [float(x[4]) for x in v if x[4] is not None]; le = [float(x[5]) for x in v if x[5] is not None]
        print(f"{arm:16s} takeover {sum(x[0] for x in v)/n:.3f} att {sum(x[1] for x in v)/n:5.2f} first {sum(fr)/len(fr) if fr else float('nan'):6.1f} (n={len(fr):2d}) cap/frontier@first {sum(lr)/len(lr) if lr else float('nan'):5.2f}  lead0 {sum(l0)/len(l0) if l0 else float('nan'):4.2f} lead_end {sum(le)/len(le) if le else float('nan'):5.2f}")

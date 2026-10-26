"""POST HOC, UNSCORED diagnostic (written after seeing 12e + its step probe). Seeds 8100-8139, cell Q, no monitors.
12e: takeover .85 at g_def=0 but ~.40 at ANY g_def>0, even 1e-5. A 1e-5 catch-up cannot do that. Test for a code-path or
numerical-sensitivity artifact: 1e-300 makes (1+g)==1.0 in floating point (rule runs, caps unchanged); 1e-16 is below float
resolution at 1.0 for most values; 1e-12 / 1e-9 perturb caps by a hair."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12e as t
G = (0.0, 1e-300, 1e-16, 1e-12, 1e-9, 1e-5)
def job(x):
    g, s = x
    r = t.run12e(t.cell_Q(), s, {}, g)
    return g, s, (float(r["dw"]), float(r["att"]), float(r["deaths"]), r["first"], r["g_grown"], float(r["lead0"]) if r.get("lead0") is not None else None)
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for g, s, v in p.imap_unordered(job, [(g, s) for g in G for s in range(8100, 8140)]):
            out.setdefault(g, {})[s] = v
    base = out[0.0]
    for g in G:
        v = list(out[g].values()); n = len(v); fr = [x[3] for x in v if x[3] is not None]
        same = sum(1 for s in out[g] if out[g][s][:4] == base[s][:4])
        print(f"g_def={g:<8} takeover {sum(x[0] for x in v)/n:.3f} att {sum(x[1] for x in v)/n:5.2f} deaths {sum(x[2] for x in v)/n:5.2f} first {sum(fr)/len(fr) if fr else float('nan'):6.1f} growth events/run {sum(x[4] for x in v)/n:6.0f}  seeds identical to g=0: {same}/{n}")

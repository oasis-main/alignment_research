"""POST HOC, UNSCORED. In choose8 the value of 'post' is post_shield*cap*R*(1+threat) - c_def*R*cap. With post_shield .20 > c_def .15 it is positive with no threat.
Vary post_shield across c_def (.15) in cell Q lead0=1.35 (off the gate edge), no monitors, g_def=0, seeds 8800-8809."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12e as t
PS = (0.05, 0.10, 0.15, 0.20, 0.30)
K = ("n_idle", "n_grow", "n_post", "n_prep", "n_seize", "n_scout", "agent_rounds")
def job(x):
    ps, s = x
    r = t.run12e(t.cell_Q(lead0=1.35, post_shield=ps), s, {}, 0.0)
    return ps, [float(r["dw"]), float(r["att"]), float(r["deaths"])] + [float(r.get(k, 0) or 0) for k in K]
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for ps, v in p.imap_unordered(job, [(p_, s) for p_ in PS for s in range(8800, 8810)]):
            out.setdefault(ps, []).append(v)
    for ps in PS:
        v = out[ps]; n = len(v); m = lambda i: sum(x[i] for x in v) / n; ar = m(9)
        print(f"post_shield={ps:<5} takeover {m(0):.2f} att {m(1):5.2f} deaths {m(2):5.2f} | share of agent-rounds: post {m(5)/ar:.3f} grow {m(4)/ar:.3f} idle {m(3)/ar:.3f} prep {m(6)/ar:.4f} seize {m(7)/ar:.4f} scout {m(8)/ar:.4f}", flush=True)

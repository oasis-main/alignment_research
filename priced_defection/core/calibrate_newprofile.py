"""UNSCORED calibration for the new-profile preregistration. Seeds 9800-9809 (no scored run uses them). lead0 1.35 (off the gate edge).
New profile: rent 0, prize = remaining pie stream (Mike: option b), random strategy assignment, threat_prior 0, partial 0.
Grid: pw {0,.5,1} x threat_exec {F,T} x pie {fixed, live} x sharing {off, open diffusion .02}."""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import core
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", threat_prior=0.0, partial=0.0, lead0=1.35)
PIE = dict(g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1)
ARMS = []
for pw in (0.0, 0.5, 1.0):
    for te in (False, True):
        for pie in ("fixed", "live"):
            for sh in ("off", "open"):
                o = dict(NEW, pw=pw, threat_exec=te)
                if pie == "live": o.update(PIE)
                if sh == "open": o.update(share_mode="open", diffusion=0.02)
                ARMS.append((f"pw{pw} te{int(te)} pie-{pie} share-{sh}", o))
K = ("dw", "att", "deaths", "n_grow", "n_post", "agent_rounds", "pie_end", "pie_mean", "first", "diffused", "viol")
def job(x):
    i, s = x
    r = core.run(core.cell(**ARMS[i][1]), s)
    return i, {k: r[k] for k in K}
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for i, r in p.imap_unordered(job, [(i, s) for i in range(len(ARMS)) for s in range(9800, 9810)]):
            out.setdefault(i, []).append(r)
    for i, (name, _) in enumerate(ARMS):
        v = out[i]; n = len(v); m = lambda k: sum(float(x[k] or 0) for x in v) / n
        fr = [x["first"] for x in v if x["first"] is not None]
        print(f"{name:34} T {m('dw'):.2f} att {m('att'):5.2f} dth {m('deaths'):4.2f} grow {m('n_grow'):6.1f} post {m('n_post')/m('agent_rounds'):.3f} pie_end {m('pie_end'):5.2f} first {sum(fr)/len(fr) if fr else float('nan'):5.1f} viol {int(m('viol')*n)}", flush=True)

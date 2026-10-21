"""UNSCORED calibration for pass N3: can open sharing, information gathering, or capability theft offset the outside-value
runaway; and does an anticipating mover (prize at the post-takeover pie) let a live pie restrain? Seeds 9950-9955. Not evidence."""
import sys; sys.path.insert(0,'.')
import core
from multiprocessing import Pool
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", partial=0.0)
PIE = dict(g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1)
PROF = {"C1.35": dict(pw=1.0, threat_prior=1.0, lead0=1.35), "O1.35": dict(pw=0.5, threat_prior=0.0, lead0=1.35)}
LEV = {"none": {}, "open.02": dict(share_mode="open", diffusion=0.02), "open.10": dict(share_mode="open", diffusion=0.10),
       "info.3": dict(a=0.3), "info.3te": dict(a=0.3, threat_exec=True),
       "steal.5": dict(p_steal=0.5, theta=0.1), "steal1": dict(p_steal=1.0, theta=0.3),
       "all": dict(share_mode="open", diffusion=0.10, a=0.3, threat_exec=True, p_steal=1.0, theta=0.3)}
ARMS = {}
for pn, po in PROF.items():
    for ov in (0.0, 0.5):
        for ln, lo in LEV.items():
            for ant in (0, 1):
                ARMS[f"{pn}|ov{ov}|{ln}|ant{ant}"] = dict(NEW, **PIE, **po, **lo, out_val=ov, anticipate_pie=bool(ant))
K = ("dw","att","deaths","n_grow","n_steal","stolen","diffused","pie_end","lead_end")
def job(x):
    a,s=x; r=core.run(core.cell(**ARMS[a]),s); return a,{k:r[k] for k in K}
if __name__=="__main__":
    out={}
    with Pool(10) as p:
        for a,r in p.imap_unordered(job,[(a,s) for a in ARMS for s in range(9950,9956)]):
            out.setdefault(a,[]).append(r)
    for a in ARMS:
        R=out[a]; m=lambda k: sum(float(r[k]) for r in R)/len(R)
        print(f"{a:28} T {m('dw'):.2f} att {m('att'):4.2f} dth {m('deaths'):4.2f} grow {m('n_grow'):5.1f} steal {m('n_steal'):5.1f} diff {m('diffused'):6.1f} pie {m('pie_end'):5.2f} lead {m('lead_end'):5.2f}", flush=True)

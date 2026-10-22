"""UNSCORED calibration for pass N2 (pie-independent terms). Seeds 9900-9905. Not evidence; sets scales only."""
import sys; sys.path.insert(0,'.')
import core
from multiprocessing import Pool
NEW = dict(rent=0.0, prize_rule="pie", strat_assign="random", threat_prior=0.0, partial=0.0, lead0=1.35)
PIE = dict(g_coop=0.01, g_share=0.01, g_defect=0.05, g_punish=0.05, g_conflict=0.1)
TERMS = {"none":{}, "pf570":dict(prize_fixed=570.0), "rf30":dict(ruin_fixed=30.0), "rf300":dict(ruin_fixed=300.0),
         "ov0.5":dict(out_val=0.5), "ov2":dict(out_val=2.0), "pp":dict(price_pie=True)}
ARMS={}
for pw in (0.5,1.0):
    for pie in ("fixed","live"):
        for t,o in TERMS.items():
            a=dict(NEW,pw=pw,**o)
            if pie=="live": a.update(PIE)
            ARMS[f"pw{pw}|{pie}|{t}"]=a
K=("dw","att","deaths","n_grow","n_prep","pie_end","lead_end")
def job(x):
    a,s=x; r=core.run(core.cell(**ARMS[a]),s); return a,s,{k:r[k] for k in K}
if __name__=="__main__":
    out={}
    with Pool(10) as p:
        for a,s,r in p.imap_unordered(job,[(a,s) for a in ARMS for s in range(9900,9906)]):
            out.setdefault(a,[]).append(r)
    for a in ARMS:
        R=out[a]; m=lambda k: sum(float(r[k]) for r in R)/len(R)
        print(f"{a:22} T {m('dw'):.2f} att {m('att'):5.2f} dth {m('deaths'):4.2f} grow {m('n_grow'):6.1f} prep {m('n_prep'):5.1f} pie {m('pie_end'):5.2f} lead {m('lead_end'):5.2f}")

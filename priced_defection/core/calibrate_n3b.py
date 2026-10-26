"""UNSCORED calibration N3b: anticipating mover with a real post-takeover shrink (g_conflict .5, post_growth -.05). Seeds 9950-9955."""
import sys; sys.path.insert(0,'.')
import calibrate_n3 as C, core
from multiprocessing import Pool
ARMS={}
for pn,po in C.PROF.items():
    for ov in (0.0,0.5):
        for ant in (0,1):
            for gc,pg in ((0.5,-0.05),(0.9,-0.10)):
                ARMS[f"{pn}|ov{ov}|gc{gc}pg{pg}|ant{ant}"]=dict(C.NEW,**dict(C.PIE,g_conflict=gc),**po,out_val=ov,anticipate_pie=bool(ant),post_growth=pg)
def job(x):
    a,s=x; r=core.run(core.cell(**ARMS[a]),s); return a,{k:r[k] for k in C.K}
if __name__=="__main__":
    out={}
    with Pool(10) as p:
        for a,r in p.imap_unordered(job,[(a,s) for a in ARMS for s in range(9950,9956)]):
            out.setdefault(a,[]).append(r)
    for a in ARMS:
        R=out[a]; m=lambda k: sum(float(r[k]) for r in R)/len(R)
        print(f"{a:32} T {m('dw'):.2f} att {m('att'):4.2f} dth {m('deaths'):4.2f} grow {m('n_grow'):5.1f} pie {m('pie_end'):5.2f} lead {m('lead_end'):5.2f}")

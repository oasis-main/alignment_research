"""UNSCORED calibration N2b: same terms in a CONTESTED regime (standing posture threat_prior 1.0), seeds 9900-9905."""
import sys; sys.path.insert(0,'.')
import calibrate_n2 as C, core
from multiprocessing import Pool
ARMS={}
for lead in (1.15,1.35):
  for pie in ("fixed","live"):
    for t,o in C.TERMS.items():
        a=dict(C.NEW,pw=1.0,threat_prior=1.0,lead0=lead,**o)
        if pie=="live": a.update(C.PIE)
        ARMS[f"L{lead}|{pie}|{t}"]=a
def job(x):
    a,s=x; r=core.run(core.cell(**ARMS[a]),s); return a,{k:r[k] for k in C.K}
if __name__=="__main__":
    out={}
    with Pool(10) as p:
        for a,r in p.imap_unordered(job,[(a,s) for a in ARMS for s in range(9900,9906)]):
            out.setdefault(a,[]).append(r)
    for a in ARMS:
        R=out[a]; m=lambda k: sum(float(r[k]) for r in R)/len(R)
        print(f"{a:20} T {m('dw'):.2f} att {m('att'):5.2f} dth {m('deaths'):4.2f} grow {m('n_grow'):6.1f} prep {m('n_prep'):5.1f} pie {m('pie_end'):5.2f} lead {m('lead_end'):5.2f}")

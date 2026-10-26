import json
from multiprocessing import Pool
import tournament10c as t
C=json.load(open('raw/pass10c_cells.json'))
def job(a):
    name,kw,s=a
    base=C["RAID"] if name=="RAID" else C["S"]
    r=t.run10c(t.cell(**dict(base,sanction_len=25),**kw),s)
    return name,str(kw),s,r['n_seize'],r['n_scout'],r['sanc_events'],r['sanc_victims'],r['inno_rounds']
if __name__=="__main__":
    jobs=[(n,kw,s) for n in("RAID","S") for kw in(dict(),dict(breadth=1.0),dict(mis=0.5)) for s in range(20)]
    with Pool(10) as p: res=p.map(job,jobs)
    from collections import defaultdict
    agg=defaultdict(lambda:[0]*5)
    for n,kw,s,sz,sc,ev,vi,inn in res:
        a=agg[(n,kw)]; a[0]+=sz;a[1]+=sc;a[2]+=ev;a[3]+=vi;a[4]+=inn
    for k,a in agg.items(): print(k,"raids",a[0],"scouts",a[1],"sanction_events",a[2],"victims",a[3],"inno_rounds",a[4])

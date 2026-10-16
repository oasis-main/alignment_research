import json
from multiprocessing import Pool
import tournament10c as t
c=t.cell(**t.RAID,sanction_len=25,lead0=1.0)
def job(a):
    b,s=a
    r=t.run10c(dict(c,breadth=b),s)
    return b,s,r['n_seize'],r['inno_rounds'],r['last_round'],r['dw'],r['agent_rounds']
if __name__=="__main__":
    with Pool(10) as p:
        res=p.map(job,[(b,s) for b in (0.0,0.25,1.0) for s in range(20)])
    for b in (0.0,0.25,1.0):
        rows=[r for r in res if r[0]==b and r[2]>0]
        print("b",b,"runs with raids",len(rows))
        for r in rows[:8]: print("  seed",r[1],"raids",r[2],"inno",r[3],"last_round",r[4],"dw",r[5],"agent_rounds",r[6])

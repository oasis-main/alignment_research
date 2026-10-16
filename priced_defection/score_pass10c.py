import json, random
D=json.load(open('raw/results_pass10c.json'))
def vals(n,k):
    return [r[k] for s,r in sorted(D[n].items(), key=lambda x:int(x[0])) if r.get(k) is not None]
def mean(v): return sum(v)/len(v) if v else float('nan')
def ci(v,B=2000):
    if len(v)<2: return (float('nan'),)*2
    rg=random.Random(1); ms=sorted(mean([rg.choice(v) for _ in v]) for _ in range(B)); return ms[int(.025*B)],ms[int(.975*B)]
def row(n,ks):
    out=[f"{n:12s}"]
    for k in ks:
        v=vals(n,k); lo,hi=ci(v); out.append(f"{k}={mean(v):.3f}[{lo:.3f},{hi:.3f}]")
    print("  ".join(out))
print("C2 sanction_len"); 
for n in ("RAID_sl10","RAID_sl25","RAID_sl50","RAID_sl200"): row(n,("n_seize","dw"))
print("C3 lead")
for n in ("RAID_base","RAID_lead1.5","RAID_lead2.0","RAID_lead3.0"):
    a=mean(vals(n,"n_seize")); p=mean(vals(n,"n_prep")); print(n,"raids",round(a,2),"prep",round(p,2),"share",round(a/(a+p),3) if a+p else None,"dw",round(mean(vals(n,"dw")),2))
print("C4 mis")
for n in ("RAID_base","RAID_mis0.25","RAID_mis0.5","RAID_mis1.0"): row(n,("pd_mean","inno_share","n_seize","raider_out_share","raider_score"))
print("C5 breadth")
for n in ("RAID_base","RAID_br0.25","RAID_br0.5","RAID_br1.0"): row(n,("pd_mean","inno_share","dw","n_seize"))
print("C5 S cell")
for n in ("S_br0.0","S_br0.25","S_br0.5","S_br1.0","S_mis0.0","S_mis0.5"): row(n,("dw","n_seize","pd_mean"))
print("identity: RAID_base vs RAID_sl25 same?", all(D["RAID_base"][s]==D["RAID_sl25"][s] for s in D["RAID_base"]))

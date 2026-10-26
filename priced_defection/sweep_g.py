"""Addendum G scored run. RAID cell, sanction_len 25, seeds 300-359, arms base/mis1.0/br1.0. Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament10c as t
R = dict(json.load(open('raw/pass10c_cells.json'))["RAID"])
ARMS = {"base": {}, "mis1.0": dict(mis=1.0), "br1.0": dict(breadth=1.0)}
KEEP = ("pairs","pd_mean","sanc_events","sanc_ar","sanc_victims","inno_share","n_scout","n_seize","dw","agent_rounds")
def job(a):
    arm, s = a
    r = t.run10c(t.cell(**dict(R, **ARMS[arm])), s)
    return arm, s, {k: r.get(k) for k in KEEP}
if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(300, 360)]
    out = {}
    with Pool(9) as p:
        for i, (a, s, r) in enumerate(p.imap_unordered(job, jobs)):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_g.json', 'w'))
    open('raw/results_g.DONE', 'w').write('done')

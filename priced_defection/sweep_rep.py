"""Part C replication scored run. RAID cell with lead0=1.1, sanction_len 25, seeds 400-459. Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament10c as t
R = dict(json.load(open('raw/pass10c_cells.json'))["RAID"], lead0=1.1)
ARMS = {"base": {}, "mis1.0": dict(mis=1.0), "br1.0": dict(breadth=1.0)}
KEEP = ("pd_mean","dw","n_seize","n_scout","sanc_events","sanc_ar","inno_share","raider_out_share","agent_rounds","last_round","deaths")
def job(a):
    arm, s = a
    r = t.run10c(t.cell(**dict(R, **ARMS[arm])), s)
    return arm, s, {k: r.get(k) for k in KEEP}
if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(400, 460)]
    out = {}
    with Pool(9) as p:
        for a, s, r in p.imap_unordered(job, jobs):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_rep.json', 'w'))
    open('raw/results_rep.DONE', 'w').write('done')

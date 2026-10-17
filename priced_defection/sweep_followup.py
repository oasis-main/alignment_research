"""Pass 10C follow-up scored run. RAID cell (raw/pass10c_cells.json), sanction_len 25, seeds 200-259. Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament10c as t
C = json.load(open('raw/pass10c_cells.json'))
R = dict(C["RAID"])
ARMS = {"base": {}, "mis0.5": dict(mis=0.5), "mis1.0": dict(mis=1.0),
        "br0.25": dict(breadth=0.25), "br1.0": dict(breadth=1.0)}
KEEP = ("dw","att","n_seize","n_scout","n_prep","seize_ok","pd_mean","inno_rounds","inno_share",
        "raider_out_share","raider_score","deaths","sanc_events","sanc_victims","sanc_ar",
        "sanc_per_event","sanc_inc_mean","unsanc_inc_mean","agent_rounds","last_round")
def job(a):
    arm, s = a
    r = t.run10c(t.cell(**dict(R, **ARMS[arm])), s)
    return arm, s, {k: r.get(k) for k in KEEP}
if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(200, 260)]
    out = {}
    with Pool(9) as p:
        for i, (a, s, r) in enumerate(p.imap_unordered(job, jobs)):
            out.setdefault(a, {})[s] = r
            if i % 25 == 0: print(i, len(jobs), flush=True)
    json.dump(out, open('raw/results_followup.json', 'w'))
    open('raw/results_followup.DONE', 'w').write('done')

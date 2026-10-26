"""Pass 11 part A scored run. Cell S (SCELL in tournament11), d=0.75, seeds 500-559. Do not edit after launch."""
import json
from multiprocessing import Pool
import tournament11 as t
ARMS = {"d0": dict(chan_d=0.0), "nocl": dict(chan_d=0.75, club_frac=0.0, club_q=1.0)}
for f in (0.25, 0.5, 0.75, 1.0):
    for q in (0.5, 1.0):
        ARMS[f"f{f}_q{q}"] = dict(chan_d=0.75, club_frac=f, club_q=q)
KEEP = ("dw","att","first","deaths","pd_first25","pd_mean","resp_ratio","n_gate_resolved","n_members","agent_rounds","last_round")
def job(a):
    arm, s = a
    r = t.run11(t.cell(**t.SCELL, **ARMS[arm]), s)
    return arm, s, {k: r.get(k) for k in KEEP}
if __name__ == "__main__":
    jobs = [(a, s) for a in ARMS for s in range(500, 560)]
    out = {}
    with Pool(9) as p:
        for a, s, r in p.imap_unordered(job, jobs):
            out.setdefault(a, {})[s] = r
    json.dump(out, open('raw/results_p11a.json', 'w'))
    open('raw/results_p11a.DONE', 'w').write('done')

"""Pass 10C scored sweep. Cells from raw/pass10c_cells.json (fixed before this ran). Seeds 0-19. Do not edit."""
import json, sys
from multiprocessing import Pool
import tournament10c as t

C = json.load(open('raw/pass10c_cells.json'))
RAID = {k: v for k, v in C["RAID"].items()}
S = dict(C["S"])
SEEDS = 20
cells = {}
def add(name, base, **over):
    cells[name] = dict(base, **over)
for sl in (10, 25, 50, 200):
    add(f"RAID_sl{sl}", RAID, sanction_len=sl)
for l0 in (1.5, 2.0, 3.0):
    add(f"RAID_lead{l0}", RAID, lead0=l0)
for m in (0.25, 0.5, 1.0):
    add(f"RAID_mis{m}", RAID, mis=m)
for b in (0.25, 0.5, 1.0):
    add(f"RAID_br{b}", RAID, breadth=b)
for b in (0.0, 0.25, 0.5, 1.0):
    add(f"S_br{b}", S, breadth=b, sanction_len=25)
for m in (0.0, 0.5):
    add(f"S_mis{m}", S, mis=m, sanction_len=25)

def job(arg):
    name, s = arg
    r = t.run10c(t.cell(**cells[name]), s)
    keep = ("dw","att","n_seize","seize_ok","n_prep","pd_mean","inno_rounds","inno_share",
            "raider_out_share","raider_score","n_raiders","deaths","lead_end")
    return name, s, {k: r.get(k) for k in keep}

if __name__ == "__main__":
    # RAID_sl25 == lead1.0 == mis0 == br0 baseline
    jobs = [(n, s) for n in cells for s in range(SEEDS)]
    # baseline cell
    cells["RAID_base"] = dict(RAID)
    jobs += [("RAID_base", s) for s in range(SEEDS)]
    out = {}
    with Pool(8) as p:
        for i, (n, s, r) in enumerate(p.imap_unordered(job, jobs)):
            out.setdefault(n, {})[s] = r
            if i % 20 == 0: print(i, len(jobs), flush=True)
    json.dump(out, open('raw/results_pass10c.json', 'w'))
    open('raw/results_pass10c.DONE', 'w').write('done')

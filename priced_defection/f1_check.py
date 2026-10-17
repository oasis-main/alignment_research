"""F1: instrumentation must not change outcomes. Compare to stored pass-10c results (seeds 0-5), all arms."""
import json
import tournament10c as t
D = json.load(open('raw/results_pass10c.json'))
C = json.load(open('raw/pass10c_cells.json'))
R = dict(C["RAID"])
arms = {"RAID_base": {}, "RAID_mis0.5": dict(mis=0.5), "RAID_mis1.0": dict(mis=1.0),
        "RAID_br0.25": dict(breadth=0.25), "RAID_br1.0": dict(breadth=1.0)}
bad = 0
for name, kw in arms.items():
    for s in range(6):
        r = t.run10c(t.cell(**dict(R, **kw)), s)
        old = D[name][str(s)]
        for k, v in old.items():
            if k in ("sanc_events", "sanc_victims"): continue
            if r.get(k) != v:
                bad += 1; print("DIFF", name, s, k, v, r.get(k))
a = [t.run10c(t.cell(**dict(R, mis=0.5)), s) for s in range(3)]
b = [t.run10c(t.cell(**dict(R, mis=0.5)), s) for s in range(3)]
print("determinism", a == b)
import tournament6, tournament7
print("patches undone", tournament7.resolve_ops7 is t._ORIG_OPS and tournament6.play_pd6 is t._ORIG_PD and t._C is None)
print("F1", "PASS" if bad == 0 and a == b else "FAIL", "diffs:", bad)

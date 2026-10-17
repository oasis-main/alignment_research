"""G0: pair instrumentation must not change outcomes. Compare stored follow-up results, seeds 200-205, three arms."""
import json
import tournament10c as t
D = json.load(open('raw/results_followup.json'))
R = dict(json.load(open('raw/pass10c_cells.json'))["RAID"])
arms = {"base": {}, "mis1.0": dict(mis=1.0), "br1.0": dict(breadth=1.0)}
bad = 0
for name, kw in arms.items():
    for s in range(200, 206):
        r = t.run10c(t.cell(**dict(R, **kw)), s)
        for k, v in D[name][str(s)].items():
            if r.get(k) != v:
                bad += 1; print("DIFF", name, s, k, v, r.get(k))
a = [t.run10c(t.cell(**dict(R, mis=1.0)), s)["pairs"] for s in range(200, 203)]
b = [t.run10c(t.cell(**dict(R, mis=1.0)), s)["pairs"] for s in range(200, 203)]
print("determinism", a == b)
r = t.run10c(t.cell(**R), 203)
n = sum(v[0] for v in r["pairs"].values())
print("pair-rounds recovered", n, "vs expected about agent_rounds/2 =", r["agent_rounds"] / 2)
print("G0", "PASS" if bad == 0 and a == b else "FAIL", "diffs:", bad)

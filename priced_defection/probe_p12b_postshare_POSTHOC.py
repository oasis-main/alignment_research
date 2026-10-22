"""POST HOC, UNSCORED probe (written after seeing 12b). Seeds 3100-3129, cell D0.
Code reading: the posting decision adds `threat += 0.5` for EVERY other agent with out_until > rnd, whoever it is.
Hypothesis: false flags deter because sanctioned agents raise everyone's perceived threat -> more posting -> a stronger
response, not because sanctions impoverish the mover. Test: does posting share rise with false flags, while reads-only does not?"""
import sys; sys.path.insert(0, '.')
from multiprocessing import Pool
import tournament12b as t
ARMS = {
  "m0":               dict(m=0),
  "m8 r0 fp.002":     dict(m=8, r=0.0, p_fp=0.002),
  "m8 r0 fp.01":      dict(m=8, r=0.0, p_fp=0.01),
  "m8 r.9 free":      dict(m=8, r=0.9),
  "m8 r0 expose":     dict(m=8, r=0.0, expose=True, p_exp=0.02),
}
def job(x):
    arm, s = x
    r = t.run12b(t.cell_D0(), s, ARMS[arm])
    return arm, (float(r["dw"]), float(r["att"]), float(r.get("post_share") or 0), float(r.get("n_post") or 0), float(r["agent_rounds"]), r["fp_flags"], r["pd_S"], r["pd_AR"])
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for arm, v in p.imap_unordered(job, [(a, s) for a in ARMS for s in range(3100, 3130)]):
            out.setdefault(arm, []).append(v)
    print(f"{'arm':16s} takeover attempts post_share(of agent-rounds) posts/run  PD/agent-round  flags/run")
    for arm in ARMS:
        v = out[arm]; n = len(v)
        print(f"{arm:16s} {sum(x[0] for x in v)/n:7.3f} {sum(x[1] for x in v)/n:8.2f} {sum(x[2] for x in v)/n:10.3f} {sum(x[3] for x in v)/n:12.1f} {sum(x[6] for x in v)/sum(x[7] for x in v):11.3f} {sum(x[5] for x in v)/n:10.1f}")

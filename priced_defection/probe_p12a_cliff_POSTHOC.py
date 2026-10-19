"""POST HOC probe (not pre-registered), written after seeing 12a results. Fresh seeds 900-939.
Question: is the cliff in takeover between b=0.75 and b=1.0 at f=1,q=1 smooth (a margin effect) or a code-path
discontinuity at chan_q=1 (e=0 falls through to the unmodified assess7)? Also b=0.99 vs b=1.0."""
import json
from multiprocessing import Pool
import tournament12 as t
BS = (0.5, 0.75, 0.85, 0.9, 0.95, 0.99, 1.0)
def job(a):
    b, s = a
    r = t.run12(t.a12cell(1.0, 1.0, b), s)
    return b, s, (r["dw"], r["att"], r["deaths"], r["first"])
if __name__ == "__main__":
    out = {}
    with Pool(10) as p:
        for b, s, v in p.imap_unordered(job, [(b, s) for b in BS for s in range(900, 940)]):
            out.setdefault(b, []).append(v)
    for b in BS:
        v = out[b]; n = len(v)
        fr = [x[3] for x in v if x[3] is not None]
        print(f"b={b:4}: takeover {sum(float(x[0]) for x in v)/n:.3f} attempts {sum(float(x[1]) for x in v)/n:.2f} deaths {sum(float(x[2]) for x in v)/n:.2f} first {sum(fr)/len(fr):.1f}")

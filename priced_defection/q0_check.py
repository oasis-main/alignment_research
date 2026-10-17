"""Q0: aware, f=0 equals pass 10 aware with chan_d=1.0, chan_q=0 seed-for-seed (6 seeds); determinism."""
import tournament10 as t10
import tournament11 as t

strip = lambda r: {k: v for k, v in r.items()
                   if k not in t.NEW + t.STRIP10}
S = dict(t.SCELL, aware=True)
bad = 0
for s in range(6):
    a = strip(t10.run10(t10.cell(**S, chan_d=1.0, chan_q=0.0), s))
    for q in (0.0, 1.0):
        b = strip(t.run11(t.cell(**S, chan_d=1.0, club_frac=0.0, club_q=q), s))
        if a != b:
            bad += 1
            print("DIFF seed", s, "q", q)
x = [strip(t.run11(t.cell(**S, chan_d=1.0, club_frac=0.5, club_q=0.5), s)) for s in range(3)]
y = [strip(t.run11(t.cell(**S, chan_d=1.0, club_frac=0.5, club_q=0.5), s)) for s in range(3)]
print("determinism", x == y)
print("Q0", "PASS" if bad == 0 and x == y else "FAIL", "diffs:", bad)

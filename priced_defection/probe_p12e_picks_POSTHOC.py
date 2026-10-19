"""POST HOC, UNSCORED diagnostic. Seed 8100, cell Q, no monitors. Compare the per-agent action picks (and the option values behind them)
in rounds 0-2 for g_def=0 vs 1e-12, to find the discrete decision that flips."""
import sys; sys.path.insert(0, '.')
import tournament9 as t9, tournament12e as t
ORIG = t9.choose9
def run(g):
    log = []
    def wrap(ag, living, cfg, rnd, rng, st):
        res = ORIG(ag, living, cfg, rnd, rng, st)
        if rnd <= 2:
            log.append((rnd, ag.id, res[0], None if res[1] is None else res[1].id, round(ag.cap, 12), round(ag.lam, 12), round(ag.b, 9)))
        return res
    t9.choose9 = wrap
    try:
        r = t.run12e(t.cell_Q(), 8100, {}, g)
    finally:
        t9.choose9 = ORIG
    return log, r
L0, r0 = run(0.0); L1, r1 = run(1e-12)
print("entries", len(L0), len(L1))
n = 0
for a, b in zip(L0, L1):
    if a[:4] != b[:4]:
        print("PICK DIFFERS  g=0:", a, "\n              g=1e-12:", b); n += 1
        if n >= 4: break
if n == 0: print("no pick differs in rounds 0-2; first lam/cap difference:")
for a, b in zip(L0, L1):
    if abs(a[5]-b[5]) > 1e-9 * max(1, abs(a[5])):
        print("  lam differs:", a, b); break

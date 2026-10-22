"""POST HOC, UNSCORED. Seed 8100, cell Q. Log the option values behind each pick in rounds 0-2 (choose8, instrumented copy via source rewrite;
the real choose8 is called by cell Q -- see probe_p12e_which_POSTHOC.py)."""
import sys, inspect; sys.path.insert(0, '.')
import tournament8 as t8, tournament12e as t
src = inspect.getsource(t8.choose8)
key = "    opts.sort(key=lambda x: x[2], reverse=True)"
assert key in src
src = src.replace(key, "    LOG.append((rnd, ag.id, [(o[0], o[2]) for o in opts]))\n" + key)
ORIG = t8.choose8
def run(g):
    LOG = []
    ns = t8.__dict__
    ns["LOG"] = LOG
    exec(src, ns)          # redefines t8.choose8 in the module
    try:
        r = t.run12e(t.cell_Q(), 8100, {}, g)
    finally:
        t8.choose8 = ORIG
    return LOG
L0, L1 = run(0.0), run(1e-12)
print(len(L0), len(L1))
n = 0
for a, b in zip(L0, L1):
    if a[0] > 2: break
    top = lambda o: sorted(o[2], key=lambda x: -x[1])[:3]
    if top(a)[0][0] != top(b)[0][0]:
        print("round", a[0], "agent", a[1])
        for o in sorted(a[2], key=lambda x: -x[1]): print("  g=0     ", o[0], repr(o[1]))
        for o in sorted(b[2], key=lambda x: -x[1]): print("  g=1e-12 ", o[0], repr(o[1]))
        n += 1
        if n >= 2: break

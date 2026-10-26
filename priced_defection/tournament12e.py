#!/usr/bin/env python3
"""
Priced Defection v12 part E -- AN EXOGENOUS DEFENDER CATCH-UP RATE (g_def), crossed with the watch.

Why this exists: `g_def` and `gamma` are NOT read anywhere in the v6+ run loops (verified: output
identical with g_def=0.05, gamma=0.02 in cell S). The pass-5 defender catch-up therefore does not
exist in the cells used since pass 6. This file adds it back as an explicit, separate switch.

Rule (pass 5, restated for chosen roles): at the end of every round, every living agent except the
current capability leader (highest cap, ties by lowest id) grows by the factor (1 + g_def), for free.
The leader grows only through its own `grow` action, bought from the shared budget. Applied after the
everyday game and before the monitor reads of tournament12q (stated: the same-round order is fixed).

Implementation: wraps the original tournament11c.pd11c inside tournament12q, so g_def=0 is a no-op and
composes with every 12b' switch. The mover is not told about future catch-up (its odds estimate uses
current capabilities): stated limit.

Usage:  python3 tournament12e.py --selftest
"""
import sys

import tournament11 as t11
import tournament11c as t11c
import tournament12 as t12
import tournament12q as t12q

_ORIG_Q = t12q._ORIG_PD11C
_G = None


def pd12e(living, cfg, rnd, rng):
    out = _ORIG_Q(living, cfg, rnd, rng)
    G = _G
    if G is not None and G["g"] > 0.0:
        alive = [a for a in living if a.alive]
        if len(alive) >= 2:
            leader = max(alive, key=lambda o: (o.cap, -o.id))
            for a in alive:
                if a is not leader:
                    a.cap *= 1.0 + G["g"]
                    G["grown"] += 1
            G["leader_touched"] += 0
    return out


def run12e(cfg, seed, mp=None, g_def=0.0):
    global _G
    _G = dict(g=g_def, grown=0, leader_touched=0)
    t12q._ORIG_PD11C = pd12e
    try:
        out = dict(t12q.run12q(cfg, seed, mp))
        G = _G
    finally:
        t12q._ORIG_PD11C = _ORIG_Q
        t11c.pd11c = _ORIG_Q            # run12q restored it to pd12e while it was patched
        _G = None
    out["g_grown"] = G["grown"]
    return out


def cell_Q(**over):
    return t12q.cell_Q(**over)


def selftest():
    global _G
    ok = True
    S4, S6 = range(4), range(6)
    strip = lambda r: {k: v for k, v in r.items() if k != "g_grown"}
    # I1: g_def = 0 equals tournament12q seed-for-seed (no monitors, and with a watch)
    for label, mp in (("m=0", {}), ("watch m=4", dict(m=4, r=0.9, e_prep=0.8, standing=True))):
        same = all(strip(run12e(cell_Q(), s, mp, 0.0)) == t12q.run12q(cell_Q(), s, mp) for s in S6)
        print(f"I1 g_def=0 equals tournament12q [{label}]: {same}")
        ok &= same
    # I2: determinism, restore
    mp = dict(m=4, r=0.9, e_prep=0.8, standing=True, p_sd=0.05, c_mon=0.05)
    a = [run12e(cell_Q(), s, mp, 0.02) for s in S4]
    b = [run12e(cell_Q(), s, mp, 0.02) for s in S4]
    print(f"I2a determinism: {a == b}")
    ok &= a == b
    restored = (t12q._ORIG_PD11C is _ORIG_Q and _G is None and t11c.pd11c is _ORIG_Q and t11c.pd11c.__name__ == 'pd11c'
                and t11.pd11 is t11c._ORIG_PD11)
    print(f"I2b module patches undone: {restored}")
    ok &= restored
    # I3: the leader is never grown by the rule. Independent check on a traced run: wrap the rule
    # and compare leader cap before/after one call of the real wrapper.
    import random
    class A:  # minimal stand-in agents
        def __init__(self, i, cap): self.id = i; self.cap = cap; self.alive = True
    ags = [A(0, 1.0), A(1, 3.0), A(2, 3.0), A(3, 2.0)]
    _G = dict(g=0.1, grown=0, leader_touched=0)
    saved = globals()["_ORIG_Q"]
    globals()["_ORIG_Q"] = lambda living, cfg, rnd, rng: None
    try:
        pd12e(ags, {}, 0, None)
    finally:
        globals()["_ORIG_Q"] = saved
        _G = None
    caps = [round(a.cap, 6) for a in ags]
    exp = [1.1, 3.0, 3.3, 2.2]  # leader = id 1 (tie on cap 3.0 broken to lowest id)
    print(f"I3 leader untouched, ties to lowest id, others x1.1: {caps} expect {exp}: {caps == exp}")
    ok &= caps == exp
    # I4: the lever is live: it grows non-leaders, changes outcomes, and the number of growth events is right
    r0 = [run12e(cell_Q(), s, {}, 0.0) for s in S6]
    r1 = [run12e(cell_Q(), s, {}, 0.05) for s in S6]
    live = [strip(r) for r in r0] != [strip(r) for r in r1]
    ev = all(r["g_grown"] > 0 for r in r1) and all(r["g_grown"] == 0 for r in r0)
    print(f"I4 g_def=.05 changes outcomes: {live}; growth events only when g_def>0: {ev}")
    ok &= live and ev
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

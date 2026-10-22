#!/usr/bin/env python3
"""
Priced Defection v12 part A -- THE MOVER'S BELIEF ABOUT THE CLUB (scale b) + dip instrumentation.

Pre-registered in PREREG_PASS12A_2026-10-19.md (commit f96c827, before this file).

Belief: the informed mover's per-detector delivery belief is
    chan_q = min(1, b * q * f)
while TRUE delivery is unchanged (tournament11.deliver11). In tournament10's belief
module chan_q is read only by assess10, so this changes beliefs and nothing else.
  b = 0     the mover does not notice the club at all   (== Part A')
  b = 1     the mover is exactly right                  (== Part A'')
  0 < b < 1 the mover under-notices a private club
  b > 1     the mover over-estimates the club (clipped at 1)

Recorder (off the dynamics path, consumes no randomness, changes no output):
  at every takeover attempt that reaches resolution, records
  (detectors in the pool, club members among them, mover cap, frontier, round).
  deliver12 wraps tournament11.deliver11; frontier12 wraps tournament6.frontier6 and
  pairs with the delivery that immediately precedes it inside resolve_grabs10.

Usage:  python3 tournament12.py --selftest
"""
import sys

import tournament6 as t6
import tournament10 as t10
import tournament11 as t11
import tournament11c as t11c

_ORIG_DELIVER11 = t11.deliver11
_ORIG_FRONTIER = t6.frontier6
_REC = None


def deliver12(pool, A):
    R = _REC
    if R is not None:
        M = t11._M
        nm = sum(1 for o in pool if (M is not None and o.id in M["members"]))
        R["pending"] = (len(pool), nm)
    return _ORIG_DELIVER11(pool, A)


def frontier12(ag, living, cfg):
    fr = _ORIG_FRONTIER(ag, living, cfg)
    R = _REC
    if R is not None and R["pending"] is not None:
        n, nm = R["pending"]
        R["att"].append((n, nm, float(ag.cap), float(fr), cfg.get("_rnd")))
        R["pending"] = None
    return fr


def a12cell(f, q, b, **over):
    c = t11c.a3cell(f, q)
    c["chan_q"] = min(1.0, b * q * f)
    c.update(over)
    return c


def run12(cfg, seed):
    global _REC
    _REC = dict(pending=None, att=[])
    t11.deliver11 = deliver12
    t6.frontier6 = frontier12
    try:
        out = dict(t11c.run11c(cfg, seed))
        rec = list(_REC["att"])
    finally:
        t11.deliver11 = _ORIG_DELIVER11
        t6.frontier6 = _ORIG_FRONTIER
        _REC = None
    out["att_rec"] = rec
    return out


def selftest():
    ok = True
    S4, S6 = range(4), range(6)
    strip_new = lambda r, extra=(): {k: v for k, v in r.items()
                                     if k not in t11.NEW + t11.STRIP10 + tuple(extra)}
    REC11C = ("pd_S", "pd_AR", "n_last", "rest", "inc_F0", "inc_F1", "inc25", "rec_rounds")
    ex = REC11C + ("att_rec",)
    # I1: b = 0 equals Part A' (tournament11.run11, aware, chan_q default 0)
    for f, q in ((0.5, 1.0), (1.0, 1.0)):
        same = all(strip_new(t11.run11(t11.cell(**t11.SCELL, aware=True, chan_d=1.0,
                                                club_frac=f, club_q=q), s), ex)
                   == strip_new(run12(a12cell(f, q, 0.0), s), ex) for s in S6)
        print(f"I1 b=0 equals A' (f={f}, q={q}): {same}")
        ok &= same
    # I2: b = 1 equals Part A'' (run11c with a3cell)
    for f, q in ((0.5, 1.0), (0.75, 1.0), (0.5, 0.5)):
        same = all(strip_new(t11c.run11c(t11c.a3cell(f, q), s), ex)
                   == strip_new(run12(a12cell(f, q, 1.0), s), ex) for s in S6)
        print(f"I2 b=1 equals A'' (f={f}, q={q}): {same}")
        ok &= same
    # I3: recorder inert at a generic cell (all keys, including welfare), determinism, restore
    inert = all({k: v for k, v in t11c.run11c(a12cell(0.5, 1.0, 0.5), s).items()}
                == {k: v for k, v in run12(a12cell(0.5, 1.0, 0.5), s).items() if k != "att_rec"}
                for s in S4)
    print(f"I3a recorder leaves every output unchanged (f=.5,b=.5): {inert}")
    ok &= inert
    a = [run12(a12cell(0.75, 1.0, 0.75), s) for s in S4]
    b = [run12(a12cell(0.75, 1.0, 0.75), s) for s in S4]
    print(f"I3b determinism (incl. att_rec): {a == b}")
    ok &= a == b
    restored = (t11.deliver11 is _ORIG_DELIVER11 and t6.frontier6 is _ORIG_FRONTIER and _REC is None
                and t10._deliver is t11._ORIG_DELIVER and t11.pd11 is t11c._ORIG_PD11
                and t6.play_pd6 is t11._ORIG_PD and t11._M is None)
    print(f"I3c module patches undone: {restored}")
    ok &= restored
    # I4: clip at f = 1
    same = all(run12(a12cell(1.0, 1.0, 1.5), s) == run12(a12cell(1.0, 1.0, 1.0), s) for s in S4)
    print(f"I4 f=1: b=1.5 equals b=1.0: {same}")
    ok &= same
    # recorder pairing: one record per attempt; sane counts; share exact at f = 1
    pair, sane = True, True
    for f, b_ in ((0.5, 1.0), (0.75, 0.5), (1.0, 0.0)):
        for s in S6:
            r = run12(a12cell(f, 1.0, b_), s)
            pair &= (len(r["att_rec"]) == int(round(float(r["att"]))))
            sane &= all(0 <= nm <= n for (n, nm, c, fr, rd) in r["att_rec"])
            if f == 1.0:
                sane &= all(nm == n for (n, nm, c, fr, rd) in r["att_rec"])
    print(f"I5 one record per attempt: {pair}; counts sane (and members==detectors at f=1): {sane}")
    ok &= pair and sane
    # the belief scale must actually move behaviour somewhere
    r5 = [strip_new(run12(a12cell(0.5, 1.0, 0.5), s), ex) for s in S6]
    r1 = [strip_new(run12(a12cell(0.5, 1.0, 1.0), s), ex) for s in S6]
    live = r5 != r1
    print(f"I6 b=0.5 differs from b=1 somewhere in 6 seeds (wiring live): {live}")
    ok &= live
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

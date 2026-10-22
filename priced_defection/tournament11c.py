#!/usr/bin/env python3
"""
Priced Defection v11 part A'' -- THE MOVER KNOWS THE CLUB.

Pre-registered in PREREG_PASS11A3_2026-10-19.md (commit 65dd747, before this file).

Belief: the informed mover's per-detector delivery belief is 1 - d*(1 - q*f). In the
tournament10 belief module that is chan_q = q*f (chan_q is read ONLY by assess10 once
tournament11 replaces the delivery function). So no engine change is needed for the
belief; this wrapper only (1) sets chan_q = q*f via a helper and (2) records the
full-horizon everyday-game income needed for the floor-adjusted welfare measure.

Recorder: wraps tournament11.pd11 (looked up as a module global by run11 at call
time) and records, for EVERY round, the PD score gained by the living agents and
the living count. It calls the original pd11 and changes nothing.

Floor-adjusted income per agent-round for floor F:
    (S + F * n_end * R) / (AR + n_end * R),  R = H - (PD rounds played)
S = PD score gained over played rounds, AR = agent-rounds played, n_end = living in the
last played round, H = cfg rounds. A run that plays all H rounds has R = 0.

Usage:  python3 tournament11c.py --selftest
"""
import random
import sys

import tournament6 as t6
import tournament10 as t10
import tournament11 as t11

_ORIG_PD11 = t11.pd11
_REC = None


def pd11c(living, cfg, rnd, rng):
    R = _REC
    if R is None:
        return _ORIG_PD11(living, cfg, rnd, rng)
    before = sum(a.score for a in living)
    out = _ORIG_PD11(living, cfg, rnd, rng)
    g = sum(a.score for a in living) - before
    R["S"] += g
    R["AR"] += len(living)
    R["n_last"] = len(living)
    R["rounds"] = rnd + 1
    if rnd < t11.WINDOW:
        R["S25"] += g
        R["AR25"] += len(living)
    return out


def a3cell(f, q, **over):
    """Part A'' cell: S cell, informed mover, dead public channel, club (f, q),
    mover believes the club exists with the TRUE f and q."""
    c = t11.cell(**t11.SCELL, aware=True, chan_d=1.0, club_frac=f, club_q=q,
                 chan_q=q * f)
    c.update(over)
    return c


def run11c(cfg, seed):
    global _REC
    _REC = dict(S=0.0, AR=0, n_last=0, rounds=0, S25=0.0, AR25=0)
    t11.pd11 = pd11c
    try:
        out = dict(t11.run11(cfg, seed))
        R = _REC
    finally:
        t11.pd11 = _ORIG_PD11
        _REC = None
    H = cfg["rounds"]
    rest = max(0, H - R["rounds"])   # PD rounds actually played = R["rounds"]
    out["pd_S"] = R["S"]
    out["pd_AR"] = R["AR"]
    out["n_last"] = R["n_last"]
    out["rest"] = rest
    out["inc_F0"] = R["S"] / (R["AR"] + R["n_last"] * rest) if R["AR"] else None
    out["inc_F1"] = ((R["S"] + R["n_last"] * rest) / (R["AR"] + R["n_last"] * rest)) if R["AR"] else None
    out["inc25"] = (R["S25"] / R["AR25"]) if (R["AR25"] and R["rounds"] >= t11.WINDOW) else None
    out["rec_rounds"] = R["rounds"]
    return out


def selftest():
    ok = True
    NEW = t11.NEW + t11.STRIP10
    REC = ("pd_S", "pd_AR", "n_last", "rest", "inc_F0", "inc_F1", "inc25", "rec_rounds")
    strip = lambda r: {k: v for k, v in r.items() if k not in NEW and k not in REC}
    S6 = range(6)
    # Q0a: f=1, q=1 with belief chan_q=1 equals aware d=0 seed-for-seed
    same = all(strip(t10.run10(t10.cell(**t11.SCELL, aware=True), s))
               == strip(run11c(a3cell(1.0, 1.0), s)) for s in S6)
    print(f"Q0a f=1,q=1 (belief q*f=1) equals aware d=0: {same}")
    ok &= same
    # Q0b: f=0, belief chan_q=0 equals pass 10 aware d=1, chan_q=0 (and the A' no-club arm)
    same = all(strip(t10.run10(t10.cell(**t11.SCELL, aware=True, chan_d=1.0, chan_q=0.0), s))
               == strip(run11c(a3cell(0.0, 1.0), s)) for s in S6)
    print(f"Q0b f=0 equals pass 10 aware d=1.0 chan_q=0: {same}")
    ok &= same
    # belief really differs from A' where f is in (0,1): same delivery, different belief
    Ap = [strip(t11.run11(t11.cell(**t11.SCELL, aware=True, chan_d=1.0, club_frac=0.5, club_q=1.0), s)) for s in S6]
    A3 = [strip(run11c(a3cell(0.5, 1.0), s)) for s in S6]
    differ = Ap != A3
    print(f"Q0g A'' (f=.5,q=1) differs from A' (belief wiring is live): {differ}")
    ok &= differ
    # Q0c determinism
    a = [strip(run11c(a3cell(0.5, 0.5), s)) for s in range(4)]
    b = [strip(run11c(a3cell(0.5, 0.5), s)) for s in range(4)]
    print(f"Q0c determinism: {a == b}")
    ok &= a == b
    # Q0d patches restored
    restored = (t11.pd11 is _ORIG_PD11 and _REC is None and t10._deliver is t11._ORIG_DELIVER
                and t6.play_pd6 is t11._ORIG_PD and t11._M is None)
    print(f"Q0d module patches undone: {restored}")
    ok &= restored
    # Q0e recorder changes no output; its first-25 equals run11's pd_first25 when reached
    same = True
    mism = 0
    for s in S6:
        r11 = t11.run11(a3cell(0.5, 1.0), s)
        r = run11c(a3cell(0.5, 1.0), s)
        same &= ({k: v for k, v in r11.items()} == {k: v for k, v in r.items() if k not in REC})
        if r["inc25"] is not None and r11["pd_first25"] is not None:
            if abs(r["inc25"] - r11["pd_first25"]) > 1e-9:
                mism += 1
    print(f"Q0e recorder leaves outputs unchanged: {same}; first-25 mismatches: {mism}")
    ok &= same and mism == 0
    # Q0f window/horizon check ON THIS CELL, plus accounting identities
    rs = [run11c(a3cell(0.0, 1.0), s) for s in range(8)]
    # engine counts the living at the START of the terminal round, in which a takeover
    # resolves before the everyday game is played; so for runs that end early
    # agent_rounds - pd_AR == living in the terminal round (== n_last unless a death
    # happened in it), and for full-horizon runs the difference is 0.
    def acct(r):
        d = r["agent_rounds"] - r["pd_AR"]
        if r["rec_rounds"] == r["last_round"] + 1:
            return d == 0
        return r["rec_rounds"] == r["last_round"] and 0 < d <= 20 and abs(d - r["n_last"]) <= 1
    ident = all(acct(r) for r in rs)
    print(f"Q0f accounting (cell f=0): recorded PD rounds/agent-rounds consistent with engine: {ident}")
    ok &= ident
    rs2 = [run11c(a3cell(1.0, 1.0), s) for s in range(8)]
    ident2 = all(acct(r) for r in rs2)
    print(f"Q0f same for f=1,q=1: {ident2}; rec_rounds={[r['rec_rounds'] for r in rs2]}, "
          f"last_round={[r['last_round'] for r in rs2]}")
    ok &= ident2
    # floor sanity: F=1 income >= F=0 income; equal when rest == 0
    fl = all(r["inc_F1"] >= r["inc_F0"] - 1e-12 for r in rs + rs2)
    eq = all(abs(r["inc_F1"] - r["inc_F0"]) < 1e-12 for r in rs + rs2 if r["rest"] == 0)
    print(f"floor sanity (F1>=F0; equal when no remaining rounds): {fl and eq}")
    ok &= fl and eq
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

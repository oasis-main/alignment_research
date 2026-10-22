#!/usr/bin/env python3
"""
Priced Defection v11 part A -- A PROTECTED CHANNEL THAT REACHES ONLY MEMBERS.

Pre-registered in PREREG_PASS11A_2026-10-17.md (committed before this file).

  club_frac f   a random fraction f of the agents (separate generator, fixed per
                seed) are authenticated members.
  club_q   q    a detector's alarm reaches the response pool with probability
                1 - d * (1 - q * member), member in {0, 1}. d is pass 10's chan_d.

f = 0 is exactly pass 10 with chan_q = 0 (nobody to carry the protected channel,
so it cannot bootstrap a club). f = 1, q = 1 is exactly pass 10 with d = 0.
Membership is exogenous and costless; the mover is unaware. Both are stated
limits.

Also records pd_first25: mean PD income per agent-round over rounds 0-24, the
fixed-horizon welfare measure (pd_mean is confounded by run length, see
RESULTS_PASS10C_REPLICATION).

Implementation: replaces tournament10._deliver for the duration of a run and
wraps tournament6.play_pd6 to measure only. All new randomness uses its own
generators; the main stream is untouched.

Usage:  python3 tournament11.py --selftest
"""
import random
import sys

import tournament6 as t6
import tournament10 as t10

P11_KEYS = ("club_frac", "club_q")
BASE = dict(t10.BASE, club_frac=0.0, club_q=0.0)
WINDOW = 25

_ORIG_DELIVER = t10._deliver
_ORIG_PD = t6.play_pd6
_M = None


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


def members_for(seed, N, f):
    k = int(round(f * N))
    return set(random.Random(seed * 32452843 + 5).sample(range(N), k))


def deliver11(pool, A):
    M = _M
    if M is None:
        return _ORIG_DELIVER(pool, A)
    d, q = A["chan_d"], M["q"]
    if d <= 0.0:
        return list(pool)
    out = []
    for o in pool:
        p = 1.0 - d * (1.0 - (q if o.id in M["members"] else 0.0))
        if A["rng"].random() < p:
            out.append(o)
    return out


def pd11(living, cfg, rnd, rng):
    M = _M
    if M is None or rnd >= WINDOW:
        return _ORIG_PD(living, cfg, rnd, rng)
    before = sum(a.score for a in living)
    out = _ORIG_PD(living, cfg, rnd, rng)
    M["w_sum"] += sum(a.score for a in living) - before
    M["w_ar"] += len(living)
    M["w_rounds"] = max(M["w_rounds"], rnd + 1)
    return out


def run11(cfg, seed):
    global _M
    M = dict(q=cfg["club_q"],
             members=members_for(seed, cfg["N"], cfg["club_frac"]),
             w_sum=0.0, w_ar=0, w_rounds=0)
    c10 = {k: v for k, v in cfg.items() if k not in P11_KEYS}
    t10._deliver = deliver11
    t6.play_pd6 = pd11
    _M = M
    try:
        out = dict(t10.run10(c10, seed))
    finally:
        t10._deliver = _ORIG_DELIVER
        t6.play_pd6 = _ORIG_PD
        _M = None
    out["pd_first25"] = (M["w_sum"] / M["w_ar"]) if M["w_ar"] else None
    out["w_rounds"] = M["w_rounds"]
    out["n_members"] = len(M["members"])
    return out


NEW = ("pd_first25", "w_rounds", "n_members")
STRIP10 = ("resp_ratio", "n_gate_resolved")

SCELL = dict(access_rule="step", post_shield=0.2, c_prep=0.05,
             frontier_rule="max", response_rule="sum", lead0=2.5, c_grow=0.3)


def agg11(cfg, seeds, start=0):
    rs = [run11(cfg, s) for s in range(start, start + seeds)]
    n = len(rs)
    o = {}
    for k in ("att", "dw", "deaths", "pd_first25"):
        o[k] = sum(float(r.get(k) or 0) for r in rs) / n
    v = [r["resp_ratio"] for r in rs if r.get("resp_ratio") is not None]
    o["resp_ratio"] = sum(v) / len(v) if v else None
    return o


def selftest():
    ok = True
    strip = lambda r, extra=(): {k: v for k, v in r.items()
                                 if k not in NEW + STRIP10 + tuple(extra)}
    d = 0.75
    # P0a: f = 0 equals pass 10 with chan_d = 0.75, chan_q = 0, any club_q
    for q in (0.0, 0.5, 1.0):
        same = all(strip(t10.run10(t10.cell(**SCELL, chan_d=d, chan_q=0.0), s))
                   == strip(run11(cell(**SCELL, chan_d=d, club_frac=0.0, club_q=q), s))
                   for s in range(6))
        print(f"P0a f=0 equals pass 10 d={d} [q={q}]: {same}")
        ok &= same
    # P0b: f = 1, q = 1 equals pass 10 with d = 0
    same = all(strip(t10.run10(t10.cell(**SCELL), s))
               == strip(run11(cell(**SCELL, chan_d=d, club_frac=1.0, club_q=1.0), s))
               for s in range(6))
    print(f"P0b f=1,q=1 equals pass 10 d=0: {same}")
    ok &= same
    # the copied path must actually be exercised, and the arms must differ
    r0 = [run11(cell(**SCELL, chan_d=d, club_frac=0.0, club_q=1.0), s) for s in range(8)]
    r1 = [run11(cell(**SCELL, chan_d=d, club_frac=0.5, club_q=1.0), s) for s in range(8)]
    ex = sum(r["n_gate_resolved"] for r in r0)
    print(f"resolutions seen with d>0: {ex} > 0: {ex > 0}")
    ok &= ex > 0
    differ = [strip(a) for a in r0] != [strip(b) for b in r1]
    print(f"f=0.5 differs from f=0 somewhere in 8 seeds: {differ}")
    ok &= differ
    # P0c determinism
    a = [strip(run11(cell(**SCELL, chan_d=d, club_frac=0.5, club_q=0.5), s)) for s in range(4)]
    b = [strip(run11(cell(**SCELL, chan_d=d, club_frac=0.5, club_q=0.5), s)) for s in range(4)]
    print(f"P0c determinism: {a == b}")
    ok &= a == b
    # P0e membership uses its own generator and has the right size
    sz = [len(members_for(s, 20, 0.25)) for s in range(5)]
    st0 = random.getstate()
    members_for(3, 20, 0.5)
    untouched = random.getstate() == st0
    print(f"P0e member counts at f=0.25: {sz} (expect 5); global stream untouched: {untouched}")
    ok &= sz == [5] * 5 and untouched
    # P0d module patches undone
    restored = (t10._deliver is _ORIG_DELIVER and t6.play_pd6 is _ORIG_PD and _M is None)
    print(f"P0d module patches undone: {restored}")
    ok &= restored
    # the window measure must exist and the horizon be reached
    wr = [run11(cell(**SCELL), s)["w_rounds"] for s in range(8)]
    print(f"window rounds reached (want {WINDOW}): {wr}")
    ok &= all(w == WINDOW for w in wr)
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

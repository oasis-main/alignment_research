#!/usr/bin/env python3
"""
Priced Defection v12 part B -- A COSTED, IMPERFECT, EVADABLE PREP-PHASE MONITOR.

Pre-registered in PREREG_PASS12B_2026-10-19.md (618181b) with Addenda 1-3
(061130e, dbe309f, 2321d4c), all committed before this file.

Wraps tournament11c.pd11c (the everyday-game step) and, around it:
  pre-game  : exposure. A monitor becomes publicly exposed with prob p_exp per round
              (not already exposed), for T_x rounds. In an exposed round, with prob rho
              it is sanctioned for ONE round via out_until = max(out_until, rnd+1), so
              partners defect against it (same income channel as every other sanction)
              and it stays counted in agent-rounds.
  post-game : for every monitor that is alive and not itself preparing, for every other
              living agent it can read (persistent coverage draw c):
                - target preparing and not yet in the grab phase: with prob r*(1-e) the
                  monitor is added to target.prep_detectors;
                - target not preparing: with prob p_fp it is falsely flagged and
                  sanctioned for L_fp rounds (out_until = max(out_until, rnd+L_fp)).
              then each monitor pays c_mon*R*cap out of its budget, clamped at zero.
All monitor randomness uses SEPARATE generators; with m = 0 the wrapper is a no-op.
The mover is NOT told about monitors (its belief module is unchanged): stated limit.

Timing (Addendum 2): the end-of-round read lands in prep_detectors one step before
the next round's built-in noticing loop; no extra delay, no extra read.

Usage:  python3 tournament12b.py --selftest
"""
import random
import sys

import tournament6 as t6
import tournament11 as t11
import tournament11c as t11c
import tournament12 as t12

_ORIG_PD11C = t11c.pd11c
_S = None

DEFAULT_MP = dict(m=0, r=0.0, c=1.0, e=0.0, p_fp=0.0, expose=False, c_mon=0.0,
                  L_fp=10, p_exp=0.02, T_x=20, rho=0.5)
NEWKEYS = ("reads_ok", "read_tries", "fp_flags", "exp_rounds", "excl_events", "bad_touch",
           "mon_inc", "mon_rounds", "spend", "clamp_binds", "viol", "n_mon",
           "net_F0", "net_F1")


def setup_streams(seed, N, mp):
    """Separate generators only. Returns (monitor ids, readable matrix, rngs)."""
    sel = random.Random(seed * 15485863 + 17)
    perm = sel.sample(range(N), N)             # nested monitor sets across m
    ids = set(perm[:min(mp["m"], N)])
    rc = random.Random(seed * 32452867 + 29)   # readability over ALL ordered pairs
    read = {(i, j): (rc.random() < mp["c"]) for i in range(N) for j in range(N) if i != j}
    return ids, read, dict(read=random.Random(seed * 49979687 + 31),
                           fp=random.Random(seed * 86028121 + 37),
                           exp=random.Random(seed * 122949823 + 41))


def pd12b(living, cfg, rnd, rng):
    S = _S
    if S is None or not S["ids"]:
        return _ORIG_PD11C(living, cfg, rnd, rng)
    mp, ids = S["mp"], S["ids"]
    mons = [a for a in living if a.id in ids]
    # ---- exposure (pre-game)
    if mp["expose"]:
        for a in mons:
            if S["exp_until"].get(a.id, -1) <= rnd and S["rng"]["exp"].random() < mp["p_exp"]:
                S["exp_until"][a.id] = rnd + mp["T_x"]
            if S["exp_until"].get(a.id, -1) > rnd:
                S["exp_rounds"] += 1
                if S["rng"]["exp"].random() < mp["rho"]:
                    if a.id not in ids:
                        S["bad_touch"] += 1
                    a.out_until = max(a.out_until, rnd + 1)
                    S["excl_events"] += 1
    before = {a.id: a.score for a in mons}
    out = _ORIG_PD11C(living, cfg, rnd, rng)
    for a in mons:
        S["mon_inc"] += a.score - before[a.id]
        S["mon_rounds"] += 1
    # ---- reads and false flags (post-game)
    rd, fp = S["rng"]["read"], S["rng"]["fp"]
    p_ok = mp["r"] * (1.0 - mp["e"])
    for mon in mons:
        if mon.preparing > 0:
            continue
        for t in living:
            if t is mon or not S["read"][(mon.id, t.id)]:
                continue
            if t.preparing > 0 and t.grabbed_at is None:
                S["read_tries"] += 1
                if rd.random() < p_ok:
                    t.prep_detectors.add(mon.id)
                    S["reads_ok"] += 1
            elif t.preparing == 0 and mp["p_fp"] > 0.0:
                if fp.random() < mp["p_fp"]:
                    t.out_until = max(t.out_until, rnd + mp["L_fp"])
                    S["fp_flags"] += 1
    # ---- cost (budget, clamped at zero)
    if mp["c_mon"] > 0.0:
        for a in mons:
            cost = mp["c_mon"] * t6.R * a.cap
            take = min(cost, max(0.0, a.b))
            a.b -= take
            S["spend"] += take
            if take < cost - 1e-12:
                S["clamp_binds"] += 1
    # ---- independent invariant: every detector id on a living agent must be a monitor
    #      that was allowed to read that agent (valid because built-in noticing a = 0.0)
    for t in living:
        for i in t.prep_detectors:
            if i not in ids or not S["read"][(i, t.id)]:
                S["viol"] += 1
    return out


def run12b(cfg, seed, mp=None):
    global _S
    mp = dict(DEFAULT_MP, **(mp or {}))
    ids, read, rngs = setup_streams(seed, cfg["N"], mp)
    _S = dict(mp=mp, ids=ids, read=read, rng=rngs, exp_until={}, reads_ok=0, read_tries=0,
              fp_flags=0, exp_rounds=0, excl_events=0, bad_touch=0, mon_inc=0.0,
              mon_rounds=0, spend=0.0, clamp_binds=0, viol=0)
    t11c.pd11c = pd12b
    try:
        out = dict(t12.run12(cfg, seed))
        S = _S
    finally:
        t11c.pd11c = _ORIG_PD11C
        _S = None
    for k in ("reads_ok", "read_tries", "fp_flags", "exp_rounds", "excl_events", "bad_touch",
              "mon_inc", "mon_rounds", "spend", "clamp_binds", "viol"):
        out[k] = S[k]
    out["n_mon"] = len(ids)
    den = out["pd_AR"] + out["n_last"] * out["rest"]
    out["net_F0"] = (out["pd_S"] - S["spend"]) / den if den else None
    out["net_F1"] = (out["pd_S"] + out["n_last"] * out["rest"] - S["spend"]) / den if den else None
    return out


def cell_D0(**over):
    c = t11.cell(**t11.SCELL, aware=True)
    c.update(over)
    return c


def cell_CL(**over):
    return t12.a12cell(0.5, 1.0, 1.0, **over)


def selftest():
    ok = True
    S4, S6 = range(4), range(6)
    strip = lambda r: {k: v for k, v in r.items() if k not in NEWKEYS}
    # I1: m = 0 equals tournament12 in both cells (every key)
    for name, mk in (("D0", cell_D0), ("CL", cell_CL)):
        same = all(strip(run12b(mk(), s)) == t12.run12(mk(), s) for s in S6)
        print(f"I1 m=0 equals tournament12 [{name}]: {same}")
        ok &= same
    # I2: m>0 with every effect off (r=0, p_fp=0, expose off, c_mon=0) equals m=0
    for name, mk in (("D0", cell_D0), ("CL", cell_CL)):
        same = all(strip(run12b(mk(), s, dict(m=4, r=0.0))) == strip(run12b(mk(), s)) for s in S6)
        print(f"I2 m=4, all effects off, equals m=0 [{name}]: {same}")
        ok &= same
    # I3: determinism, restore, separate streams leave the global stream alone
    mp = dict(m=4, r=0.9, p_fp=0.01, expose=True, c_mon=0.05)
    a = [run12b(cell_D0(), s, mp) for s in S4]
    b = [run12b(cell_D0(), s, mp) for s in S4]
    print(f"I3a determinism (all fields): {a == b}")
    ok &= a == b
    st0 = random.getstate()
    setup_streams(3, 20, dict(DEFAULT_MP, m=8, c=0.5))
    untouched = random.getstate() == st0
    print(f"I3b setup leaves the global random stream untouched: {untouched}")
    ok &= untouched
    restored = (t11c.pd11c is _ORIG_PD11C and _S is None and t11.pd11 is t11c._ORIG_PD11
                and t12.t6.frontier6 is t12._ORIG_FRONTIER and t11.deliver11 is t12._ORIG_DELIVER11)
    print(f"I3c module patches undone: {restored}")
    ok &= restored
    # nested monitor sets
    n2 = setup_streams(5, 20, dict(DEFAULT_MP, m=2))[0]
    n4 = setup_streams(5, 20, dict(DEFAULT_MP, m=4))[0]
    print(f"I3d monitor sets nested (m=2 within m=4): {n2 <= n4 and len(n2) == 2 and len(n4) == 4}")
    ok &= n2 <= n4 and len(n2) == 2 and len(n4) == 4
    # I4: independent invariant (no detector outside the monitor set, only readable pairs) and
    #     reads actually happen
    viol = reads = tries = 0
    for name, mk in (("D0", cell_D0), ("CL", cell_CL)):
        for s in S6:
            r = run12b(mk(), s, dict(m=4, r=0.9, c=0.5))
            viol += r["viol"]; reads += r["reads_ok"]; tries += r["read_tries"]
    print(f"I4 invariant violations: {viol} (want 0); reads ok {reads} of {tries} tries (want > 0)")
    ok &= viol == 0 and reads > 0
    # I5: exposure touches only exposed monitors; cost is zero unless asked
    bt = ex = 0
    for s in S6:
        r = run12b(cell_D0(), s, dict(m=4, r=0.9, expose=True, p_exp=1.0, rho=1.0))
        bt += r["bad_touch"]; ex += r["excl_events"]
        z = run12b(cell_D0(), s, dict(m=4, r=0.9))
        ok &= (z["spend"] == 0.0 and z["excl_events"] == 0 and z["fp_flags"] == 0)
    print(f"I5 bad_touch {bt} (want 0); exclusion events with p_exp=rho=1: {ex} (want > 0); zero-cost arms clean")
    ok &= bt == 0 and ex > 0
    # I6: each lever is live and moves the thing it should
    r_fp = [run12b(cell_D0(), s, dict(m=4, r=0.0, p_fp=0.05)) for s in S6]
    r_c = [run12b(cell_D0(), s, dict(m=4, r=0.0, c_mon=0.05)) for s in S6]
    r_m0 = [run12b(cell_D0(), s) for s in S6]
    live_fp = sum(r["fp_flags"] for r in r_fp) > 0
    live_c = sum(r["spend"] for r in r_c) > 0
    inc_down = sum(r["pd_S"] for r in r_fp) < sum(r["pd_S"] for r in r_m0)
    print(f"I6 false flags fire: {live_fp}; cost spends: {live_c}; false flags lower total PD score: {inc_down}")
    ok &= live_fp and live_c
    r_on = [run12b(cell_D0(), s, dict(m=8, r=0.9)) for s in S6]
    differ = [strip(r) for r in r_on] != [strip(r) for r in r_m0]
    print(f"I6b m=8, r=.9 differs from m=0 in D0: {differ}")
    ok &= differ
    # net income identity: spend = 0 -> net equals un-netted floor income
    z = run12b(cell_D0(), 1, dict(m=4, r=0.9))
    ident = abs(z["net_F1"] - z["inc_F1"]) < 1e-9 and abs(z["net_F0"] - z["inc_F0"]) < 1e-9
    print(f"I7 net income equals un-netted income when spend = 0: {ident}")
    ok &= ident
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

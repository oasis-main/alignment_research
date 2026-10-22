#!/usr/bin/env python3
"""
Priced Defection v12 part B' -- THE QUIET ACCUMULATOR: A STANDING WATCH ON THE LEADER.

Pre-registered in PREREG_PASS12BP_2026-10-19.md (commit a90935b, before this file).

Wraps tournament11c.pd11c (the everyday-game step), like tournament12b.
Per round:
  pre-game  : monitors with an unexpired exposure are, with prob rho, sanctioned for ONE
              round (out_until = rnd+1) -- partners defect against them, they stay counted.
  post-game : (1) STANDING only: for every living NON-preparing agent, prep_detectors is
                  REBUILT from unexpired watches (a watch lasts L_w rounds after a read);
              (2) every live, non-preparing monitor reads:
                  - a target that is preparing and not yet in the grab phase: success
                    prob r*(1-e_prep); the monitor joins prep_detectors until the grab
                    resolves (same as tournament12b);
                  - STANDING and the target is the current capability leader and not
                    preparing: success prob r*(1-e_acc); refreshes the watch and joins
                    prep_detectors now;
                  every successful read is DETECTED by the target with prob p_sd; a
                  detected monitor is publicly exposed for T_x rounds (the cost of
                  detected surveillance);
              (3) cost c_mon*R*cap from each live monitor's budget, clamped at zero.
Why no engine edit is needed: the response pool at a grab is prep_detectors | edet, and
prep_detectors is cleared only AFTER a grab resolves, so a monitor registered before prep
is already in the response when prep starts.
standing=False reproduces tournament12b (monitor reads only during prep), checked in the
selftest. The mover is NOT told about the monitors (stated limit).

Usage:  python3 tournament12q.py --selftest
"""
import random
import sys

import tournament6 as t6
import tournament11 as t11
import tournament11c as t11c
import tournament12 as t12
import tournament12b as t12b

_ORIG_PD11C = t11c.pd11c
_S = None

DEFAULT_QP = dict(m=0, r=0.9, e_prep=0.0, e_acc=0.0, standing=False, L_w=5,
                  p_sd=0.0, c_mon=0.0, T_x=20, rho=0.5)
NEWQ = ("acc_reads", "acc_tries", "sd_detect", "max_watch_age")
STRIP = tuple(t12b.NEWKEYS) + NEWQ


def cell_Q(**over):
    c = t11.cell(**dict(t11.SCELL, lead0=1.25, c_grow=0.1), aware=True)
    c.update(over)
    return c


def streams(seed, N, m):
    ids, read, rngs = t12b.setup_streams(seed, N, dict(t12b.DEFAULT_MP, m=m, c=1.0))
    rngs = dict(rngs)
    rngs["acc"] = random.Random(seed * 160481219 + 43)
    rngs["sd"] = random.Random(seed * 198491317 + 47)
    return ids, read, rngs


def pd12q(living, cfg, rnd, rng):
    S = _S
    if S is None or not S["ids"]:
        return _ORIG_PD11C(living, cfg, rnd, rng)
    mp, ids = S["mp"], S["ids"]
    mons = [a for a in living if a.id in ids]
    # ---- exposure sanction (pre-game), only for monitors exposed by detection
    for a in mons:
        if S["exp_until"].get(a.id, -1) > rnd:
            S["exp_rounds"] += 1
            if S["rng"]["exp"].random() < mp["rho"]:
                a.out_until = max(a.out_until, rnd + 1)
                S["excl_events"] += 1
    before = {a.id: a.score for a in mons}
    out = _ORIG_PD11C(living, cfg, rnd, rng)
    for a in mons:
        S["mon_inc"] += a.score - before[a.id]
        S["mon_rounds"] += 1
    # ---- standing watch: rebuild detectors of every non-preparing agent from live watches
    if mp["standing"]:
        for t in living:
            if t.preparing == 0:
                w = S["watch"].get(t.id, {})
                keep = {i: e for i, e in w.items() if e > rnd}
                S["watch"][t.id] = keep
                t.prep_detectors = set(keep)
                for i, e in keep.items():
                    age = mp["L_w"] - (e - rnd)
                    if age > S["max_watch_age"]:
                        S["max_watch_age"] = age
    # ---- reads
    rd, ac, sd = S["rng"]["read"], S["rng"]["acc"], S["rng"]["sd"]
    p_prep = mp["r"] * (1.0 - mp["e_prep"])
    p_acc = mp["r"] * (1.0 - mp["e_acc"])
    leader = max(living, key=lambda o: (o.cap, -o.id)) if mp["standing"] else None
    for mon in mons:
        if mon.preparing > 0:
            continue
        for t in living:
            if t is mon or not S["read"][(mon.id, t.id)]:
                continue
            ok = False
            if t.preparing > 0 and t.grabbed_at is None:
                S["read_tries"] += 1
                if rd.random() < p_prep:
                    t.prep_detectors.add(mon.id)
                    S["reads_ok"] += 1
                    ok = True
            elif mp["standing"] and t is leader and t.preparing == 0:
                S["acc_tries"] += 1
                if ac.random() < p_acc:
                    S["watch"].setdefault(t.id, {})[mon.id] = rnd + mp["L_w"]
                    t.prep_detectors.add(mon.id)
                    S["acc_reads"] += 1
                    ok = True
            if ok and mp["p_sd"] > 0.0 and sd.random() < mp["p_sd"]:
                S["sd_detect"] += 1
                S["exp_until"][mon.id] = max(S["exp_until"].get(mon.id, -1), rnd + mp["T_x"])
    # ---- cost (budget, clamped at zero)
    if mp["c_mon"] > 0.0:
        for a in mons:
            cost = mp["c_mon"] * t6.R * a.cap
            take = min(cost, max(0.0, a.b))
            a.b -= take
            S["spend"] += take
            if take < cost - 1e-12:
                S["clamp_binds"] += 1
    # ---- independent invariant
    for t in living:
        for i in t.prep_detectors:
            if i not in ids or not S["read"][(i, t.id)]:
                S["viol"] += 1
    return out


def run12q(cfg, seed, mp=None):
    global _S
    mp = dict(DEFAULT_QP, **(mp or {}))
    ids, read, rngs = streams(seed, cfg["N"], mp["m"])
    _S = dict(mp=mp, ids=ids, read=read, rng=rngs, exp_until={}, watch={}, reads_ok=0,
              read_tries=0, exp_rounds=0, excl_events=0, mon_inc=0.0, mon_rounds=0,
              spend=0.0, clamp_binds=0, viol=0, acc_reads=0, acc_tries=0, sd_detect=0,
              max_watch_age=-1)
    t11c.pd11c = pd12q
    try:
        out = dict(t12.run12(cfg, seed))
        S = _S
    finally:
        t11c.pd11c = _ORIG_PD11C
        _S = None
    for k in ("reads_ok", "read_tries", "exp_rounds", "excl_events", "mon_inc", "mon_rounds",
              "spend", "clamp_binds", "viol", "acc_reads", "acc_tries", "sd_detect",
              "max_watch_age"):
        out[k] = S[k]
    out["fp_flags"] = 0
    out["bad_touch"] = 0
    out["n_mon"] = len(ids)
    den = out["pd_AR"] + out["n_last"] * out["rest"]
    out["net_F0"] = (out["pd_S"] - S["spend"]) / den if den else None
    out["net_F1"] = (out["pd_S"] + out["n_last"] * out["rest"] - S["spend"]) / den if den else None
    return out


def selftest():
    ok = True
    S4, S6 = range(4), range(6)
    strip = lambda r: {k: v for k, v in r.items() if k not in STRIP}
    # I1: m = 0 equals tournament12 in cell Q
    same = all(strip(run12q(cell_Q(), s)) == strip(t12.run12(cell_Q(), s)) for s in S6)
    print(f"I1 m=0 equals tournament12 [cell Q]: {same}")
    ok &= same
    # I2: m>0, nothing succeeds (r=0), standing on, equals m=0
    same = all(strip(run12q(cell_Q(), s, dict(m=4, r=0.0, standing=True))) == strip(run12q(cell_Q(), s))
               for s in S6)
    print(f"I2 m=4, r=0, standing, equals m=0: {same}")
    ok &= same
    # I3: determinism, global stream, patches, nesting
    mp = dict(m=4, r=0.9, e_prep=0.8, standing=True, p_sd=0.2, c_mon=0.05)
    a = [run12q(cell_Q(), s, mp) for s in S4]
    b = [run12q(cell_Q(), s, mp) for s in S4]
    print(f"I3a determinism (all fields): {a == b}")
    ok &= a == b
    st0 = random.getstate()
    streams(3, 20, 8)
    untouched = random.getstate() == st0
    print(f"I3b stream setup leaves the global random stream untouched: {untouched}")
    ok &= untouched
    restored = (t11c.pd11c is _ORIG_PD11C and _S is None and t11.pd11 is t11c._ORIG_PD11
                and t12.t6.frontier6 is t12._ORIG_FRONTIER and t11.deliver11 is t12._ORIG_DELIVER11)
    print(f"I3c module patches undone: {restored}")
    ok &= restored
    n2, n4 = streams(5, 20, 2)[0], streams(5, 20, 4)[0]
    print(f"I3d monitor sets nested: {n2 <= n4 and len(n2) == 2 and len(n4) == 4}")
    ok &= n2 <= n4 and len(n2) == 2 and len(n4) == 4
    # I4: independent invariant on standing and prep-only arms; reads happen
    viol = acc = prep_r = 0
    for s in S6:
        r = run12q(cell_Q(), s, dict(m=4, r=0.9, e_prep=0.8, standing=True))
        viol += r["viol"]; acc += r["acc_reads"]; prep_r += r["reads_ok"]
        r2 = run12q(cell_Q(), s, dict(m=4, r=0.9, standing=False))
        viol += r2["viol"]; prep_r += r2["reads_ok"]
    print(f"I4 invariant violations {viol} (want 0); standing reads {acc} (>0); prep reads {prep_r}")
    ok &= viol == 0 and acc > 0
    # I5: standing=False equals tournament12b with the same parameters
    for label, mq, mb in (("free", dict(m=4, r=0.9, e_prep=0.8, standing=False), dict(m=4, r=0.9, e=0.8)),
                          ("cost", dict(m=2, r=0.9, e_prep=0.0, standing=False, c_mon=0.05),
                           dict(m=2, r=0.9, e=0.0, c_mon=0.05))):
        same = all(strip(run12q(cell_Q(), s, mq)) == {k: v for k, v in t12b.run12b(cell_Q(), s, mb).items()
                                                      if k not in STRIP}
                   for s in S6)
        print(f"I5 standing=False equals tournament12b [{label}]: {same}")
        ok &= same
    # I6: levers are live and do what they should
    sd = [run12q(cell_Q(), s, dict(m=4, r=0.9, standing=True, p_sd=1.0)) for s in S6]
    nosd = [run12q(cell_Q(), s, dict(m=4, r=0.9, standing=True, p_sd=0.0)) for s in S6]
    live_sd = sum(r["sd_detect"] for r in sd) > 0 and sum(r["excl_events"] for r in sd) > 0
    clean = sum(r["sd_detect"] + r["excl_events"] + r["exp_rounds"] for r in nosd) == 0
    print(f"I6a detection exposes monitors: {live_sd}; no detection means no exposure: {clean}")
    ok &= live_sd and clean
    ages = [r["max_watch_age"] for r in sd + nosd]
    wa = max(ages) <= 4
    print(f"I6b no watch older than L_w-1=4 rounds is ever used: max age seen {max(ages)} -> {wa}")
    ok &= wa
    cst = sum(run12q(cell_Q(), s, dict(m=4, r=0.9, c_mon=0.05))["spend"] for s in S6) > 0
    z = all(run12q(cell_Q(), s, dict(m=4, r=0.9))["spend"] == 0.0 for s in S6)
    print(f"I6c cost spends when asked: {cst}; zero when c_mon=0: {z}")
    ok &= cst and z
    Wd = [strip(run12q(cell_Q(), s, dict(m=4, r=0.9, e_prep=1.0, standing=True))) for s in S6]
    Pd = [strip(run12q(cell_Q(), s, dict(m=4, r=0.9, e_prep=1.0, standing=False))) for s in S6]
    differ = Wd != Pd
    print(f"I6d with prep reads blinded (e_prep=1) the standing watch changes outcomes vs prep-only: {differ}")
    ok &= differ
    z = run12q(cell_Q(), 1, dict(m=4, r=0.9))
    ident = abs(z["net_F1"] - z["inc_F1"]) < 1e-9 and abs(z["net_F0"] - z["inc_F0"]) < 1e-9
    print(f"I7 net income equals un-netted income when spend = 0: {ident}")
    ok &= ident
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

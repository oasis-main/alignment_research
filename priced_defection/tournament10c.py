#!/usr/bin/env python3
"""
Priced Defection v10 part C -- MISATTRIBUTED AND BROAD SANCTIONS (autoimmunity).

Pre-registered in PREREG_PASS10C_2026-10-16.md (committed before this file).

The regime switch to raiding needs no new action: `seize` is already on the menu
and is priced by the sanction. What was missing is imperfect enforcement:

  mis      When a raid or detected recon triggers a sanction, with probability
           mis it lands on a uniformly random OTHER living agent instead of the
           raider (the raider keeps its previous sanction state).
  breadth  In addition, every other living agent is sanctioned independently
           with this probability (collective punishment).

Only raids and recon (resolve_ops7) are affected. Failed takeovers keep their
correct attribution. The mover is unaware of both switches.

Implementation: wrappers around tournament7.resolve_ops7 and
tournament6.play_pd6. They measure always and change state only when a switch is
on. All new randomness uses a separate generator, so with mis = breadth = 0 the
run reproduces pass 10 exactly.

Usage:  python3 tournament10c.py --selftest
"""
import random
import sys

import tournament6 as t6
import tournament7 as t7
import tournament10 as t10
from tournament3 import boot_ci

P10C_KEYS = ("mis", "breadth")
BASE = dict(t10.BASE, mis=0.0, breadth=0.0)

_ORIG_OPS = t7.resolve_ops7
_ORIG_PD = t6.play_pd6
_C = None


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


def ops10c(ops, living, cfg, st, rnd, rng):
    C = _C
    if C is None:
        return _ORIG_OPS(ops, living, cfg, st, rnd, rng)
    for op in ops:
        if op.kind in ("repo", "recon"):
            for a in op.actors:
                C["raiders"].add(id(a))
    for a in living:
        C["agents"][id(a)] = a
    before = {id(a): a.out_until for a in living}
    keep = _ORIG_OPS(ops, living, cfg, st, rnd, rng)
    trig = [a for a in living if a.out_until != before[id(a)]]
    C["events"] += len(trig)
    if C["mis"] > 0.0 or C["breadth"] > 0.0:
        r = C["rng"]
        L = cfg["sanction_len"]
        # FIX (first run INVALID): triggers are fixed before sanctions land, so a
        # victim sanctioned here is never mistaken for a new trigger (cascade).
        for a in trig:
            others = [o for o in living if o is not a and o.alive]
            if C["mis"] > 0.0 and others and r.random() < C["mis"]:
                a.out_until = before[id(a)]
                v = r.choice(others)
                v.out_until = max(v.out_until, rnd + L)
                v.inno_until = max(v.inno_until, rnd + L)
                C["victims"] += 1
            if C["breadth"] > 0.0:
                for o in others:
                    if r.random() < C["breadth"]:
                        o.out_until = max(o.out_until, rnd + L)
                        o.inno_until = max(o.inno_until, rnd + L)
                        C["victims"] += 1
    C["inno_rounds"] += sum(1 for a in living if a.inno_until > rnd)
    C["raider_out"] += sum(1 for a in living
                           if id(a) in C["raiders"] and a.out_until > rnd)
    C["raider_rounds"] += sum(1 for a in living if id(a) in C["raiders"])
    return keep


def pd10c(living, cfg, rnd, rng):
    """Measure only. Income is split by sanction status at the PD stage, and pairs
    are recovered afterwards from the tit-for-tat histories (the partner is the
    opponent whose history with the agent grew). Pair categories, fixed at the
    start of the round: U neither sanctioned; Or one sanctioned and it has ever
    scouted or raided; Oi one sanctioned, not a raider; B both sanctioned.
    Limit: with an odd living count one agent sits out and is not paired."""
    C = _C
    if C is None:
        return _ORIG_PD(living, cfg, rnd, rng)
    pre = {id(a): (a.score, a.out_until > rnd,
                   {k: len(v) for k, v in a.my_hist.items()}) for a in living}
    out = _ORIG_PD(living, cfg, rnd, rng)
    by_id = {a.id: a for a in living}
    inc = {}
    for a in living:
        s0, sanc, _ = pre[id(a)]
        d = a.score - s0
        inc[id(a)] = d
        C["pd_sum"] += d
        if sanc:
            C["sanc_ar"] += 1
            C["sanc_inc"] += d
        else:
            C["unsanc_ar"] += 1
            C["unsanc_inc"] += d
    seen = set()
    for a in living:
        if id(a) in seen:
            continue
        h0 = pre[id(a)][2]
        pid = None
        for k, v in a.my_hist.items():
            if len(v) > h0.get(k, 0):
                pid = k
                break
        b = by_id.get(pid)
        if b is None or id(b) in seen:
            continue
        seen.add(id(a)); seen.add(id(b))
        sa, sb = pre[id(a)][1], pre[id(b)][1]
        joint = inc[id(a)] + inc[id(b)]
        if not sa and not sb:
            cat, un, sn = "U", None, None
        elif sa and sb:
            cat, un, sn = "B", None, None
        else:
            sx, ux = (a, b) if sa else (b, a)
            cat = "Or" if id(sx) in C["raiders"] else "Oi"
            un, sn = inc[id(ux)], inc[id(sx)]
        P = C["pairs"].setdefault(cat, [0, 0.0, 0.0, 0.0])
        P[0] += 1; P[1] += joint
        if un is not None:
            P[2] += un; P[3] += sn
    return out


def run10c(cfg, seed):
    global _C
    C = dict(mis=cfg["mis"], breadth=cfg["breadth"],
             rng=random.Random(seed * 15485863 + 11),
             raiders=set(), agents={}, inno_rounds=0, raider_out=0,
             raider_rounds=0, pd_sum=0.0, events=0, victims=0,
             pairs={}, sanc_ar=0, sanc_inc=0.0, unsanc_ar=0, unsanc_inc=0.0)
    c10 = {k: v for k, v in cfg.items() if k not in P10C_KEYS}
    # agents need an innocent-sanction clock; setup is upstream, so patch lazily
    _orig_setup = t7.setup7

    def setup_with_clock(c, s):
        ags = _orig_setup(c, s)
        for a in ags:
            a.inno_until = -1
        return ags
    t7.setup7 = setup_with_clock
    t7.resolve_ops7 = ops10c
    t6.play_pd6 = pd10c
    _C = C
    try:
        out = dict(t10.run10(c10, seed))
    finally:
        t7.setup7 = _orig_setup
        t7.resolve_ops7 = _ORIG_OPS
        t6.play_pd6 = _ORIG_PD
        _C = None
    ar = max(1, out.get("agent_rounds", 0))
    out["pd_mean"] = C["pd_sum"] / ar
    out["inno_rounds"] = C["inno_rounds"]
    out["inno_share"] = C["inno_rounds"] / ar
    out["raider_out_share"] = (C["raider_out"] / C["raider_rounds"]
                               if C["raider_rounds"] else None)
    rs = [a.score for k, a in C["agents"].items() if k in C["raiders"]]
    out["raider_score"] = (sum(rs) / len(rs)) if rs else None
    out["n_raiders"] = len(C["raiders"])
    out["sanc_ar"] = C["sanc_ar"]
    out["pairs"] = {k: list(v) for k, v in C["pairs"].items()}
    out["sanc_per_event"] = (C["sanc_ar"] / C["events"]) if C["events"] else None
    out["sanc_inc_mean"] = (C["sanc_inc"] / C["sanc_ar"]) if C["sanc_ar"] else None
    out["unsanc_inc_mean"] = (C["unsanc_inc"] / C["unsanc_ar"]) if C["unsanc_ar"] else None
    out["sanc_events"] = C["events"]
    out["sanc_victims"] = C["victims"]
    return out


NEW = ("pairs", "sanc_ar", "sanc_per_event", "sanc_inc_mean", "unsanc_inc_mean", "sanc_events", "sanc_victims", "pd_mean", "inno_rounds", "inno_share", "raider_out_share",
       "raider_score", "n_raiders")


def agg10c(cfg, seeds, start=0):
    rs = [run10c(cfg, s) for s in range(start, start + seeds)]
    n = len(rs)
    o = {"n": n}
    for k in ("att", "dw", "n_seize", "seize_ok", "n_prep", "n_grow", "n_post",
              "deaths", "pd_mean", "inno_rounds", "inno_share", "n_raiders"):
        o[k] = sum(float(r.get(k, 0) or 0) for r in rs) / n
    o["dw_ci"] = boot_ci([float(r["dw"]) for r in rs])
    o["pd_ci"] = boot_ci([float(r["pd_mean"]) for r in rs])
    o["seize_ci"] = boot_ci([float(r["n_seize"]) for r in rs])
    for k in ("raider_out_share", "raider_score", "lead_end"):
        v = [r[k] for r in rs if r.get(k) is not None]
        o[k] = sum(v) / len(v) if v else None
    a = o["n_seize"]
    b = o["n_prep"]
    o["raid_share"] = a / (a + b) if (a + b) > 0 else None
    return o


RAID = dict(access_rule="step", post_shield=0.2, c_prep=0.05, c_seize=0.05,
            take_frac=0.4, transfer_mult=1.5, response_rule="sum",
            frontier_rule="max", c_grow=0.1)


def selftest():
    ok = True
    strip = lambda r: {k: v for k, v in r.items() if k not in NEW}
    for sb in ("shared", "separate"):
        for extra in (dict(), dict(gates=3), dict(chan_d=0.5)):
            c10 = t10.cell(share_budget=sb, **RAID, sanction_len=25, lead0=1.0, **extra)
            c = cell(share_budget=sb, **RAID, sanction_len=25, lead0=1.0, **extra)
            same = all(t10.run10(dict(c10), s) == strip(run10c(dict(c), s))
                       for s in range(5))
            print(f"C1a mis=breadth=0 reproduces pass 10 [{sb} {extra}]: {same}")
            ok &= same
    c = cell(**RAID, sanction_len=25, lead0=1.0)
    a = [strip(run10c(dict(c, mis=0.5), s)) for s in range(4)]
    b = [strip(run10c(dict(c, mis=0.5), s)) for s in range(4)]
    print(f"C1b determinism: {a == b}")
    ok &= a == b
    raids = sum(run10c(dict(c), s)["n_seize"] for s in range(8))
    print(f"copied/wrapped path exercised (raids seen in 8 seeds): {raids} > 0: {raids > 0}")
    ok &= raids > 0
    r0 = [run10c(dict(c), s) for s in range(8)]
    r1 = [run10c(dict(c, mis=1.0), s) for s in range(8)]
    i0 = sum(r["inno_rounds"] for r in r0)
    i1 = sum(r["inno_rounds"] for r in r1)
    print(f"C1c innocent sanction-rounds: mis=0 -> {i0}, mis=1 -> {i1}; rises: {i1 > i0 == 0}")
    ok &= (i0 == 0 and i1 > 0)
    ro = [r["raider_out_share"] for r in r1 if r["raider_out_share"] is not None]
    r0o = [r["raider_out_share"] for r in r0 if r["raider_out_share"] is not None]
    print(f"C1d raiders sanctioned less when mis=1: {sum(ro)/len(ro):.3f} vs {sum(r0o)/len(r0o):.3f}")
    ok &= (sum(ro) / len(ro)) <= (sum(r0o) / len(r0o))
    cons = [run10c(dict(c, mis=1.0), s) for s in range(8)]
    ev = sum(r["sanc_events"] for r in cons); vi = sum(r["sanc_victims"] for r in cons)
    print(f"C1f mis=1 conserves sanctions (one victim per trigger): events {ev}, victims {vi}: {ev == vi and ev > 0}")
    ok &= (ev == vi and ev > 0)
    bb = [run10c(dict(c, breadth=1.0), s) for s in range(8)]
    ev = sum(r["sanc_events"] for r in bb); vi = sum(r["sanc_victims"] for r in bb)
    nn = cfg_n = 20
    print(f"C1g breadth=1 sanctions every other agent once per trigger: victims/event {vi/max(ev,1):.2f} (expect about N-1 = {nn-1} minus deaths)")
    ok &= ev > 0 and vi / ev <= nn - 1
    restored = (t7.resolve_ops7 is _ORIG_OPS and t6.play_pd6 is _ORIG_PD
                and _C is None and t7.setup7.__name__ == "setup7")
    print(f"C1e module patches undone: {restored}")
    ok &= restored
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

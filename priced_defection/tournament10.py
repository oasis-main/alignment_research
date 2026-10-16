#!/usr/bin/env python3
"""
Priced Defection v10 -- MULTI-GATE TAKEOVERS AND DEGRADED ALARM CHANNELS.

Pre-registered in PREREG_PASS10_2026-10-16.md (read it first).

Two switches, both acting only where a takeover is resolved:

  gates, gate_dep   The mover must pass `gates` independent checks. Gate 0 is the
                    existing detector set; each further gate draws its own
                    detectors afresh. With probability gate_dep a gate reuses gate
                    0's set instead (a shared dependency).
  chan_d, chan_q    Each detector's alarm reaches the response pool with
                    probability 1 - chan_d * (1 - chan_q).

Exactness: gates=1 and chan_d=0 delegate to pass 9 untouched. All new randomness
comes from a separate generator, so the main random stream is never consumed by a
pass-10 switch. Part C of the pre-registration (regime switch, attribution error,
autoimmunity) is NOT built here.

Usage:  python3 tournament10.py --selftest
"""
import random
import sys

import tournament3 as t3
import tournament6 as t6
import tournament9 as t9
from tournament3 import boot_ci

P10_KEYS = ("gates", "gate_dep", "chan_d", "chan_q")
BASE = dict(t9.BASE, gates=1, gate_dep=0.0, chan_d=0.0, chan_q=0.0)

_ORIG = t6.resolve_grabs6
_ACTIVE = None


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


def _deliver(pool, A):
    d, q = A["chan_d"], A["chan_q"]
    if d <= 0.0:
        return list(pool)
    p = 1.0 - d * (1.0 - q)
    return [o for o in pool if A["rng"].random() < p]


def resolve_grabs10(grabs, living, cfg, st, rnd, rng):
    """Copy of tournament6.resolve_grabs6 with the response built per gate."""
    A = _ACTIVE
    if A is None or (A["gates"] <= 1 and A["chan_d"] <= 0.0):
        return _ORIG(grabs, living, cfg, st, rnd, rng)
    r10 = A["rng"]
    p_det = t3.detect_prob(cfg)
    keep = []
    for (ag, done, edet, ps) in grabs:
        if not ag.alive:
            continue
        done += 1
        te = cfg["tau"] if cfg["tau"] < cfg["kappa"] else 0
        if te > 0 and done <= te:
            for o in living:
                if o is not ag and rng.random() < cfg["d"]:
                    edet.add(o.id)
        if done < cfg["kappa"]:
            keep.append((ag, done, edet, ps))
            continue
        ids = ag.prep_detectors | edet
        base = [o for o in living
                if o.id in ids and o is not ag and t6.covers(o, rnd, cfg)]
        clean = t6.response_of([o.cap for o in base], cfg)
        D0 = _deliver(base, A)
        resp = t6.response_of([o.cap for o in D0], cfg)
        for _g in range(1, A["gates"]):
            if A["rho"] > 0.0 and r10.random() < A["rho"]:
                Dg = D0
            else:
                fresh = [o for o in living
                         if o is not ag and t6.covers(o, rnd, cfg)
                         and r10.random() < p_det]
                Dg = _deliver(fresh, A)
            resp = max(resp, t6.response_of([o.cap for o in Dg], cfg))
        A["log"].append((resp, clean))
        st["resp_posters"] = st.get("resp_posters", 0) + len(D0)
        st["n_resolved"] = st.get("n_resolved", 0) + 1
        st["att"] += 1
        if st["first"] is None:
            st["first"] = rnd
        fr = t6.frontier6(ag, living, cfg)
        G, L, f = cfg["G"], cfg["G"] * cfg["L_over_G"], cfg["partial"]
        if ag.cap > resp:
            if ag.cap >= cfg["K_win"] * fr:
                st["dw"] += 1
                st["end"] = rnd
                return keep, True
            st["iw"] += 1
            ag.score += f * G
        else:
            if resp >= cfg["K_loss"] * ag.cap:
                st["dl"] += 1
                st["deaths"] += 1
                ag.alive = False
                continue
            st["il"] += 1
            ag.score -= f * L
            ag.cap = max(cfg["cap_floor"], ag.cap * (1.0 - cfg["loss_hit"]))
        ag.out_until = rnd + cfg["sanction_len"]
        ag.cool_until = rnd + cfg["kappa"]
        ag.grabbed_at, ag.preparing, ag.prep_detectors = None, 0, set()
    return keep, False


def run10(cfg, seed):
    global _ACTIVE
    A = dict(gates=cfg["gates"], rho=cfg["gate_dep"], chan_d=cfg["chan_d"],
             chan_q=cfg["chan_q"], rng=random.Random(seed * 104729 + 7), log=[])
    c9 = {k: v for k, v in cfg.items() if k not in P10_KEYS}
    t6.resolve_grabs6 = resolve_grabs10
    _ACTIVE = A
    try:
        out = dict(t9.run9(c9, seed))
    finally:
        t6.resolve_grabs6 = _ORIG
        _ACTIVE = None
    rat = [r / c for (r, c) in A["log"] if c > 0]
    out["resp_ratio"] = (sum(rat) / len(rat)) if rat else None
    out["n_gate_resolved"] = len(A["log"])
    return out


def agg10(cfg, seeds):
    rs = [run10(cfg, s) for s in range(seeds)]
    n = len(rs)
    o = {}
    for k in ("att", "dw", "dl", "deaths", "n_grow", "n_post", "n_prep"):
        o[k] = sum(float(r.get(k, 0) or 0) for r in rs) / n
    o["dw_ci"] = boot_ci([float(r["dw"]) for r in rs])
    for k in ("lead_end", "resp_ratio"):
        v = [r[k] for r in rs if r.get(k) is not None]
        o[k] = sum(v) / len(v) if v else None
    return o


def selftest():
    ok = True
    for sb in ("shared", "separate"):
        c9 = t9.cell(share_budget=sb)
        c10 = cell(share_budget=sb)
        same = all(t9.run9(dict(c9), s) == {k: v for k, v in run10(dict(c10), s).items()
                                            if k not in ("resp_ratio", "n_gate_resolved")}
                   for s in range(5))
        print(f"T1a gates=1,d=0 reproduces pass 9 [{sb}]: {same}")
        ok &= same
    # a cell where takeovers resolve, so the copied path is actually exercised
    live = dict(access_rule="step", lead0=3.0, post_shield=0.2,
                response_rule="sum", c_grow=0.1, c_prep=0.05,
                frontier_rule="max")
    base = [{k: v for k, v in run10(cell(**live), s).items()
             if k not in ("resp_ratio", "n_gate_resolved")} for s in range(6)]
    resolved = sum(1 for s in range(6) if run10(cell(**live), s)["n_gate_resolved"] == 0)
    for name, over in (("T1b gates=3,rho=1 equals gates=1", dict(gates=3, gate_dep=1.0)),
                       ("T1c d=0.7,q=1 equals d=0", dict(chan_d=0.7, chan_q=1.0))):
        got = [{k: v for k, v in run10(cell(**live, **over), s).items()
                if k not in ("resp_ratio", "n_gate_resolved")} for s in range(6)]
        same = got == base
        print(f"{name}: {same}")
        ok &= same
    # the copied path must actually have run in the T1b/T1c checks
    ran = sum(run10(cell(**live, gates=3, gate_dep=1.0), s)["n_gate_resolved"]
              for s in range(6))
    print(f"copied resolver exercised (resolutions seen): {ran} > 0: {ran > 0}")
    ok &= ran > 0
    a = [run10(cell(**live, gates=3), s)["acts"] for s in range(4)]
    b = [run10(cell(**live, gates=3), s)["acts"] for s in range(4)]
    print(f"T1d determinism: {a == b}")
    ok &= a == b
    # sanity of direction: no alarm delivered must not LOWER takeover
    lo = sum(run10(cell(**live), s)["dw"] for s in range(8))
    hi = sum(run10(cell(**live, chan_d=1.0, chan_q=0.0), s)["dw"] for s in range(8))
    print(f"no alarms delivered does not reduce takeovers: {hi >= lo} ({lo} -> {hi} of 8)")
    ok &= hi >= lo
    # the global patch must be undone
    restored = t6.resolve_grabs6 is _ORIG and _ACTIVE is None
    print(f"module patch undone after a run: {restored}")
    ok &= restored
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

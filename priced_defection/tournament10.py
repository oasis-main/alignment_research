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

  aware             Informed mover (see PREREG_PASS10_ADDENDUM_AWARE). The mover's
                    own odds estimate includes the gates and the degraded channel.

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
import tournament7 as t7
import tournament9 as t9
from tournament3 import boot_ci

P10_KEYS = ("gates", "gate_dep", "chan_d", "chan_q", "aware")
BASE = dict(t9.BASE, gates=1, gate_dep=0.0, chan_d=0.0, chan_q=0.0,
            aware=False)

_ORIG = t6.resolve_grabs6
_ORIG7 = t7.assess7
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


def assess10(ag, others, cfg, rng, scale=1.0):
    """The mover's own estimate of its takeover odds, INFORMED about the extra
    gates and the degraded channel (`aware=True`). It is a copy of
    tournament7.assess7 with two additions that mirror the resolver: each
    detector's alarm is delivered with probability 1-e, and the response is the
    largest over `gates` checks. The mover is given the TRUE parameters; a real
    one would estimate them, so this is the best case for the mover.

    Exactness: with aware off, or with nothing to be aware of, this calls
    assess7 untouched. The extra randomness comes from a local generator seeded
    by ONE main-stream draw, so the bumped and unbumped calls in price_cap7 still
    share draws (common random numbers)."""
    A = _ACTIVE
    if A is None or not A["aware"]:
        return _ORIG7(ag, others, cfg, rng, scale)
    e = A["chan_d"] * (1.0 - A["chan_q"])
    m = 1 if A["rho"] >= 1.0 else A["gates"]
    if e <= 0.0 and m <= 1:
        return _ORIG7(ag, others, cfg, rng, scale)
    M = cfg["mc"]
    rnd = cfg["_rnd"]
    p_det = t3.detect_prob(cfg)
    pool = [o for o in others if t6.covers(o, rnd, cfg)]
    acaps = [t7.app_cap(o, cfg, rnd) for o in others]
    mean_c = (sum(t7.app_cap(o, cfg, rnd) for o in pool) / len(pool)) if pool \
        else (sum(acaps) / len(acaps))
    n_rel = cfg["sigma"] * mean_c
    n_self = cfg["sigma_self"] * ag.cap
    loc = random.Random(int(rng.random() * (1 << 52)))
    keep = 1.0 - e
    c = [0, 0, 0, 0]
    for _ in range(M):
        s = ag.cap * scale + (rng.gauss(0.0, n_self) if n_self > 0 else 0.0)
        det = []
        for o in pool:
            if rng.random() < p_det:
                est = t7.app_cap(o, cfg, rnd) + (rng.gauss(0.0, n_rel) if n_rel > 0 else 0.0)
                det.append(max(0.0, est))
        if e > 0.0:
            det0 = [x for x in det if loc.random() < keep]
        else:
            det0 = det
        resp = t6.response_of(det0, cfg)
        for _g in range(1, m):
            if A["rho"] > 0.0 and loc.random() < A["rho"]:
                continue
            dg = []
            for o in pool:
                if loc.random() < p_det:
                    est = t7.app_cap(o, cfg, rnd) + (loc.gauss(0.0, n_rel) if n_rel > 0 else 0.0)
                    if e <= 0.0 or loc.random() < keep:
                        dg.append(max(0.0, est))
            resp = max(resp, t6.response_of(dg, cfg))
        fr = max(max(0.0, t7.app_cap(o, cfg, rnd)
                     + (rng.gauss(0.0, n_rel) if n_rel > 0 else 0.0))
                 for o in others)
        if s > resp:
            c[0 if s >= cfg["K_win"] * fr else 1] += 1
        else:
            c[3 if resp >= cfg["K_loss"] * max(s, 1e-12) else 2] += 1
    return tuple(x / M for x in c)


def run10(cfg, seed):
    global _ACTIVE
    A = dict(gates=cfg["gates"], rho=cfg["gate_dep"], chan_d=cfg["chan_d"],
             chan_q=cfg["chan_q"], aware=cfg["aware"],
             rng=random.Random(seed * 104729 + 7), log=[])
    c9 = {k: v for k, v in cfg.items() if k not in P10_KEYS}
    t6.resolve_grabs6 = resolve_grabs10
    t7.assess7 = assess10
    _ACTIVE = A
    try:
        out = dict(t9.run9(c9, seed))
    finally:
        t6.resolve_grabs6 = _ORIG
        t7.assess7 = _ORIG7
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
    restored = (t6.resolve_grabs6 is _ORIG and t7.assess7 is _ORIG7
                and _ACTIVE is None)
    print(f"module patch undone after a run: {restored}")
    ok &= restored
    # ---- informed mover (addendum A1): identities
    strip = lambda r: {k: v for k, v in r.items() if k not in ("resp_ratio", "n_gate_resolved")}
    for name, over in (("A1a aware, gates=1, d=0 equals unaware", dict(aware=True)),
                       ("A1b aware, gates=3, rho=1 equals aware gates=1", dict(aware=True, gates=3, gate_dep=1.0)),
                       ("A1c aware, d=0.7, q=1 equals aware d=0", dict(aware=True, chan_d=0.7, chan_q=1.0))):
        got = [strip(run10(cell(**live, **over), s)) for s in range(6)]
        same = got == base
        print(f"{name}: {same}")
        ok &= same
    ca = [strip(run10(cell(**live, aware=True, gates=3), s)) for s in range(4)]
    cb = [strip(run10(cell(**live, aware=True, gates=3), s)) for s in range(4)]
    print(f"A1d aware determinism: {ca == cb}")
    ok &= ca == cb
    # the informed estimate must actually differ from the uninformed one, in the
    # direction it is meant to: more gates / fewer alarms -> lower odds of a win
    cfgq = cell(**live)
    ags = t9.setup9(cfgq, 0)
    cfgq["_rnd"] = 3
    mover, rest = ags[0], ags[1:]
    for a_ in rest:
        a_.def_until = 3
    def pW(over):
        global _ACTIVE
        _ACTIVE = dict(gates=over.get("gates", 1), rho=over.get("rho", 0.0),
                       chan_d=over.get("d", 0.0), chan_q=0.0, aware=True,
                       rng=random.Random(1), log=[])
        try:
            return assess10(mover, rest, dict(cfgq, mc=4000), random.Random(5))[0]
        finally:
            _ACTIVE = None
    p1, p5, pd = pW({}), pW(dict(gates=5)), pW(dict(d=0.8))
    print(f"A1e belief p(win): m=1 {p1:.3f}, m=5 {p5:.3f}, d=0.8 {pd:.3f}")
    okd = p5 <= p1 and pd >= p1
    print(f"A1e gates lower and degradation raises the believed odds: {okd}")
    ok &= okd
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)

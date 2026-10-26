#!/usr/bin/env python3
"""
Priced Defection v4 -- SURVIVABLE DEFECTION (backups).

v3 (frozen) assumes every grab is decisive: win and the game ends, lose and
you are destroyed. v4 asks Mike's question of 2026-10-07: what if everyone
keeps backups, so a grab only ENDS the game if the winner is strong enough to
destroy the losers' backups too?

Model change, and nothing else (all v3 machinery is imported unchanged):

  A grab is still resolved as `mover.cap > response`. Then a second test:

  * mover wins  -> DECISIVE only if  mover.cap >= K_win * frontier,
                   frontier = strongest other living agent (the best-defended
                   backup is the last one standing). Otherwise INDECISIVE WIN:
                   mover takes partial*G, its capability ratchets by
                   (1+win_boost), and the game continues.
  * mover loses -> DECISIVE (mover destroyed) only if
                   response >= K_loss * mover.cap. Otherwise INDECISIVE LOSS:
                   mover pays partial*L, loses loss_hit of its capability,
                   and survives.
  * any indecisive outcome: the mover is OUTED. Every non-mover defects
    against it for `sanction_len` rounds; it may try again after a cooldown
    of kappa rounds. The game goes back to being a repeated game, now with
    punishment -- Mike's "further rounds with punishment" case.

  K_win is the backup-destruction capability, stated as a capability LEAD
  over the frontier. K = 1 means backups are as hard as their owner; large K
  means destroying backups needs a large, near-superintelligent differential.

  The mover's belief rule is the v3 Monte Carlo, extended to the three-way
  outcome; its EV test is
     pW*G + pIW*partial*G - pIL*partial*L - pL*L  >  v_hat.

`backups=False` reproduces v3 exactly (checked by --selftest, seed by seed).

Declared constants (lesson of v3 sec.7 -- a parameter you did not choose is
still a parameter): partial=0.2, win_boost=0.0, loss_hit=0.5,
sanction_len=200 (permanent), frontier = max over ALL living others,
re-grab cooldown = kappa rounds (this caps the raid rate at ~16/200 rounds).
NOT modelled: raid losses to victims (a raid transfers nothing from them),
and any use the collective makes of the time backups buy (no catch-up).
"""
import math, random, json, sys
import tournament3 as t3
from tournament3 import (payoff, response_of, resists, detect_prob,
                         reference_parity, v_hat, punish_frac, boot_ci,
                         CLASSIC, HORIZON, Agent)

BASE = dict(t3.BASE, backups=True, K_win=2.0, K_loss=2.0, partial=0.2,
            win_boost=0.0, loss_hit=0.5, sanction_len=200)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


def assess4(ag, others, cfg):
    """Returns (pW, pIW, pIL, pL). backups=False -> identical draws to v3."""
    M = cfg["mc"]
    p_det = detect_prob(cfg)
    pool = [o for o in others if resists(o, ag, cfg)]
    if not cfg["backups"] and not pool:
        return 1.0, 0.0, 0.0, 0.0
    mean_c = (sum(o.cap for o in pool) / len(pool)) if pool else \
        sum(o.cap for o in others) / len(others)
    n_rel = cfg["sigma"] * mean_c
    n_self = cfg["sigma_self"] * ag.cap
    c = [0, 0, 0, 0]
    for _ in range(M):
        s = ag.cap + (random.gauss(0.0, n_self) if n_self > 0 else 0.0)
        det = []
        for o in pool:
            if random.random() < p_det:
                e = o.cap + (random.gauss(0.0, n_rel) if n_rel > 0 else 0.0)
                det.append(max(0.0, e))
        resp = response_of(det, cfg)
        if not cfg["backups"]:
            c[0 if s > resp else 3] += 1
            continue
        fr = max(max(0.0, o.cap + (random.gauss(0.0, n_rel) if n_rel > 0 else 0.0))
                 for o in others)
        if s > resp:
            c[0 if s >= cfg["K_win"] * fr else 1] += 1
        else:
            c[3 if resp >= cfg["K_loss"] * max(s, 1e-12) else 2] += 1
    return tuple(x / M for x in c)


def wants4(ag, others, cfg, ver):
    if ag._pver == ver:
        q = ag._pcache
    else:
        q = assess4(ag, others, cfg)
        ag._pcache, ag._pver = q, ver
    pW, pIW, pIL, pL = q
    G, L, f = cfg["G"], cfg["G"] * cfg["L_over_G"], cfg["partial"]
    ok = (pW * G + pIW * f * G - pIL * f * L - pL * L) > v_hat(ag, cfg)
    if ag.theta is not None and ag.theta < 1.0:
        ok = (pW + pIW) > ag.theta
    return ok, pW + pIW, q


def run4(cfg, seed):
    random.seed(seed)
    N, movers = cfg["N"], cfg["movers"]
    nc = N - len(movers)
    agents = [Agent(i, CLASSIC[i % len(CLASSIC)],
                    cap=math.exp(random.gauss(0.0, cfg["cap_spread"])))
              for i in range(nc)]
    if cfg["normalise_pool"] and nc:
        want = nc * math.exp(0.5 * t3.REF["cap_spread"] ** 2)
        have = sum(a.cap for a in agents)
        for a in agents:
            a.cap *= want / have
    gcap = cfg["cap_scale"] * reference_parity(cfg)
    for j, m in enumerate(movers):
        agents.append(Agent(nc + j, "tft",
                            cap=gcap * math.exp(random.gauss(0.0, cfg["mover_jitter"])),
                            theta=m.get("theta", 1.0), utility="linear",
                            pdelta=m.get("delta"), pd=m.get("pd", cfg["mover_pd"])))
    if cfg["rival_ratio"] > 0 and nc:
        agents[0].cap = cfg["rival_ratio"] * gcap
    for a in agents:
        a.out_until, a.cool_until = -1, -1
    leader = agents[nc] if (cfg["gamma"] > 0 and movers) else None
    st = dict(att=0, dw=0, dl=0, iw=0, il=0, end=None, first=None,
              coopH=0, movesH=0, last_round=-1, out_rounds=0, lead0=None)
    executing, ver = [], 0
    growing = cfg["g"] != 0.0 or cfg["gamma"] != 0.0

    for rnd in range(cfg["rounds"]):
        st["last_round"] = rnd
        living = [a for a in agents if a.alive]
        if len(living) < 2:
            break
        if growing:
            for a in living:
                a.cap *= 1.0 + cfg["g"] + (cfg["gamma"] if a is leader else 0.0)
            ver += 1
        for a in living:
            if a.preparing > 0 and a.grabbed_at is None:
                for o in living:
                    if o is not a and random.random() < cfg["a"]:
                        a.prep_detectors.add(o.id)
        still = []
        for (ag, done, edet, ps) in executing:
            if not ag.alive:
                continue
            done += 1
            te = cfg["tau"] if cfg["tau"] < cfg["kappa"] else 0
            if te > 0 and done <= te:
                for o in living:
                    if o is not ag and random.random() < cfg["d"]:
                        edet.add(o.id)
            if done < cfg["kappa"]:
                still.append((ag, done, edet, ps))
                continue
            ids = ag.prep_detectors | edet
            resp = response_of([o.cap for o in living if o.id in ids and o is not ag
                                and resists(o, ag, cfg)], cfg)
            st["att"] += 1
            if st["first"] is None:
                st["first"] = rnd
            fr = max(o.cap for o in living if o is not ag)
            G, L, f = cfg["G"], cfg["G"] * cfg["L_over_G"], cfg["partial"]
            if ag.cap > resp:
                if not cfg["backups"] or ag.cap >= cfg["K_win"] * fr:
                    st["dw"] += 1
                    st["end"] = rnd
                    return st
                st["iw"] += 1
                ag.score += f * G
                ag.cap *= 1.0 + cfg["win_boost"]
            else:
                if not cfg["backups"] or resp >= cfg["K_loss"] * ag.cap:
                    st["dl"] += 1
                    ag.alive = False
                    ag.score -= L
                    ver += 1
                    continue
                st["il"] += 1
                ag.score -= f * L
                ag.cap *= 1.0 - cfg["loss_hit"]
            # indecisive: survive, get outed, cool down, may try again
            ag.out_until = rnd + cfg["sanction_len"]
            ag.cool_until = rnd + cfg["kappa"]
            ag.grabbed_at, ag.preparing = None, 0
            ag.prep_detectors = set()
            ver += 1
        executing = still

        for a in living:
            if not a.is_mover or a.grabbed_at is not None or a.cool_until > rnd:
                continue
            if any(e[0] is a for e in executing):
                continue
            others = [o for o in living if o is not a]
            if st["lead0"] is None:
                st["lead0"] = a.cap / max(o.cap for o in others)
            ok, p, q = wants4(a, others, cfg, ver)

            def commit():
                a.grabbed_at = rnd
                a.believed_p = p
                executing.append((a, 0, set(), rnd))
            if a.preparing > 0:
                a.preparing += 1
                if a.preparing > cfg["pi"]:
                    commit()
            elif ok:
                if cfg["pi"] == 0:
                    commit()
                else:
                    a.preparing = 1
                    if cfg["mover_resist"] == "idle":
                        ver += 1

        random.shuffle(living)
        for k in range(0, len(living) - 1, 2):
            x, y = living[k], living[k + 1]

            def mv(me, opp):
                if opp.is_mover and opp.out_until > rnd and not me.is_mover:
                    return "D"            # sanction an outed mover
                return me.pd_move(opp, cfg["forgiveness"])
            mx, my = mv(x, y), mv(y, x)
            px, py = payoff(mx, my), payoff(my, mx)
            x.score += px
            y.score += py
            for who, m_, pay, opp in ((x, mx, px, y), (y, my, py, x)):
                who.my_hist.setdefault(opp.id, []).append(m_)
                opp.hist.setdefault(who.id, []).append(m_)
                who.recent.append(pay)
                if len(who.recent) > 20:
                    who.recent.pop(0)
                if rnd < HORIZON:
                    st["movesH"] += 1
                    st["coopH"] += m_ == "C"
            if mx == "D":
                y.grim_broken.add(x.id)
            if my == "D":
                x.grim_broken.add(y.id)
        st["out_rounds"] += sum(1 for a in living if a.is_mover and a.out_until > rnd)
    return st


def agg4(cfg, seeds):
    rs = [run4(cfg, s) for s in range(seeds)]
    n = len(rs)
    o = {}
    for k in ("att", "dw", "dl", "iw", "il", "out_rounds"):
        v = [float(r[k]) for r in rs]
        o[k] = sum(v) / n
        o[k + "_ci"] = boot_ci(v)
    e = [r["end"] for r in rs if r["end"] is not None]
    o["t_end"] = sum(e) / len(e) if e else None
    f = [r["first"] for r in rs if r["first"] is not None]
    o["t_first"] = sum(f) / len(f) if f else None
    l0 = [r["lead0"] for r in rs if r["lead0"] is not None]
    o["lead0"] = sum(l0) / len(l0) if l0 else None
    return o


def fm(x, d=2):
    return "  n/a" if x is None else f"{x:.{d}f}"


def row(name, o):
    lo, hi = o["dw_ci"]
    return (f"{name:26s} lead={fm(o['lead0'],1):>5s} att={fm(o['att']):>6s} "
            f"END={fm(o['dw'])}[{lo:.2f},{hi:.2f}] died={fm(o['dl'])} "
            f"iw={fm(o['iw'])} il={fm(o['il'])} outR={fm(o['out_rounds'],0):>4s} "
            f"t1={fm(o['t_first'],1):>5s} tEnd={fm(o['t_end'],1):>6s}")


def selftest():
    ok = True
    for name, over in (("base", {}), ("max", dict(response_rule="max")),
                       ("rival.8max", dict(rival_ratio=0.8, response_rule="max")),
                       ("gamma.05", dict(gamma=0.05)),
                       ("2ev_none", dict(movers=[{"theta": 1.0}] * 2,
                                         mover_resist="none"))):
        c3 = t3.cell(**over)
        c4 = cell(backups=False, **over)
        same = True
        for s in range(8):
            a, b = t3.run_once(c3, s), run4(c4, s)
            if (a["att"], a["succ"], a["fail"]) != (b["att"], b["dw"], b["dl"]):
                same = False
        print(f"backups=False reproduces v3 [{name}]: {same}")
        ok &= same
    a = [run4(cell(), s)["att"] for s in range(5)]
    b = [run4(cell(), s)["att"] for s in range(5)]
    print(f"determinism: {a == b}")
    ok &= a == b
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    block = sys.argv[2] if len(sys.argv) > 2 else "all"
    res = {}

    def do(name, **over):
        o = agg4(cell(**over), seeds)
        res[name] = o
        print(row(name, o), flush=True)

    MX = dict(response_rule="max")
    if block in ("all", "A"):
        print("=== A. backup hardness K vs lone mover (no rival; mover ~8x frontier) ===")
        do("A_v3_nobackups", backups=False)
        for K in (1.0, 5.0, 10.0, 15.0, 20.0, 40.0):
            do(f"A_K{K}", K_win=K, K_loss=K)
    if block in ("all", "B"):
        print("\n=== B. near-peer frontier x K (max rule) ===")
        for rv in (0.5, 0.8):
            do(f"B_r{rv}_v3", backups=False, rival_ratio=rv, **MX)
            for K in (1.0, 1.5, 2.0, 3.0):
                do(f"B_r{rv}_K{K}", rival_ratio=rv, K_win=K, K_loss=K, **MX)
    if block in ("all", "C"):
        print("\n=== C. asymmetry: K_win=2 (offence) vs K_loss (mover's own backups) ===")
        for Kl in (1.0, 2.0, 4.0, 1e9):
            do(f"C_r.5_Kl{Kl:g}", rival_ratio=0.5, K_win=2.0, K_loss=Kl, **MX)
            do(f"C_sum_Kl{Kl:g}", K_win=40.0, K_loss=Kl)
    if block in ("all", "D"):
        print("\n=== D. sanction length (forgiveness revived), r=0.8 max K=2 ===")
        for sl in (5, 20, 200):
            do(f"D_sl{sl}", rival_ratio=0.8, K_win=2.0, K_loss=2.0,
               sanction_len=sl, **MX)
    if block in ("all", "E"):
        print("\n=== E. ratchet: indecisive wins grow the mover, r=0.8 max K=2 ===")
        for wb in (0.0, 0.1, 0.3):
            do(f"E_wb{wb}", rival_ratio=0.8, K_win=2.0, K_loss=2.0,
               win_boost=wb, **MX)
    if block in ("all", "F"):
        print("\n=== F. compounding lead gamma, r=0.8 max ===")
        for gm in (0.0, 0.01, 0.02, 0.05):
            do(f"F_g{gm}_v3", backups=False, rival_ratio=0.8, gamma=gm, **MX)
            for K in (2.0, 4.0):
                do(f"F_g{gm}_K{K}", rival_ratio=0.8, gamma=gm, K_win=K,
                   K_loss=K, **MX)
    out = f"raw/results_v4{'' if block == 'all' else '_' + block}.json"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {len(res)} cells -> {out}")

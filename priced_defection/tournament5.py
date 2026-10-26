#!/usr/bin/env python3
"""
Priced Defection v5 -- DEFENDER CATCH-UP, TWO-STAGE RAIDS, COALITIONS.

v4 (frozen) made defection survivable via backups, and found: below the
backup-hardness threshold K you get a raiding regime, raids that yield
capability make the endgame certain, and t_end ~ ln(K/lead0)/ln(1+gamma).
Three things were missing, all raised by Mike 2026-10-07:

 1. DEFENDERS DO NOTHING with the time backups buy. -> `g_def`, a growth rate
    for every non-mover. Pre-registered prediction: the order holds iff
    g_def >= gamma.

 2. RAIDS DO NOT TRANSFER. In v4 a raid gave the mover a payoff out of thin
    air and cost its victims nothing. -> a raid now moves `take_frac` of the
    victim's capability, and the raider receives `transfer_mult` times it.
    mult=0 is pure destruction (sabotage), 1.0 is pure theft, >1 is theft
    that is worth more to the taker than to the loser. This is the "Catan
    bandit" question: does raiding damp compounding, or accelerate it?

 3. ONLY MOVERS ACT. Defenders could resist but never initiate. -> defenders
    may DEFENSIVELY RAID a suspected mover, and may LOCK ARMS: `coalition`
    defenders raid at once, their capabilities pooled for that raid.

And the counterintelligence structure Mike proposed, which replaces v4's
single-stage raid:

   RECON (read-only): pi_r rounds, detected with prob d_recon per round,
     succeeds with a contest probability against the target. Success yields
     an information advantage: an immediate `recon_gain` share of the
     target's capability, and a multiplier (1+info_gain) on the attacker's
     effective strength in a following repossession.
   REPOSSESSION (write/destroy): DETECTION IS CERTAIN. Success is a contest
     conditional on the recon outcome. Success transfers capability; failure
     costs the attacker `loss_hit_r` of its own, and is fatal if the response
     is at least K_loss times its strength.

An attacker may repossess without recon (blind), or recon first. Movers
additionally retain v4's full GRAB, which ends the game iff the mover's lead
over the frontier is at least K_win. `frontier_rule` decides whether the
backups that must be cleared are the strongest single defender ("max") or the
pooled collective ("sum") -- Mike's question of whether cumulative collective
capability is still in the model. It is: `response_rule` still defaults to
"sum", and now the frontier can be pooled too.

Contest success probability (NEW ASSUMPTION, declared): Tullock/Hirshleifer
  p = a^m / (a^m + b^m), m = `contest_m` = 3.
v3/v4 resolved fights by deterministic comparison of noisy estimates. Ops use
the contest function because a raid is a partial, repeatable engagement rather
than a single decisive test. The full GRAB keeps v4's deterministic rule, so
v4 numbers remain reproducible: `ops=False, g_def=0` returns to v4 exactly
(checked by --selftest).
"""
import math, random, json, sys
import tournament3 as t3
import tournament4 as t4
from tournament3 import (payoff, response_of, resists, detect_prob,
                         reference_parity, v_hat, boot_ci, CLASSIC, HORIZON,
                         Agent)

BASE = dict(t4.BASE,
            ops=True,            # two-stage raids available at all
            g_def=0.0,           # defender growth per round (item 1)
            take_frac=0.1,       # share of victim capability a raid moves
            transfer_mult=1.0,   # 0 = destroy, 1 = steal, >1 = steal at a gain
            def_raid=True,       # defenders may raid suspected movers
            coalition=1,         # how many defenders lock arms per raid
            recon=True,          # recon stage available
            pi_r=2,              # recon duration (rounds)
            d_recon=0.3,         # per-round detection prob during recon
            recon_gain=0.02,     # immediate capability share from good recon
            info_gain=0.5,       # effective-strength multiplier from recon
            loss_hit_r=0.2,      # attacker's cost of a failed repossession
            contest_m=3.0,
            frontier_rule="max", # backups to clear: "max" or "sum"
            cap_floor=1e-6)


def cell(**over):
    c = dict(BASE)
    c.update(over)
    return c


def contest(a, b, m):
    if a <= 0:
        return 0.0
    if b <= 0:
        return 1.0
    aa, bb = a ** m, b ** m
    return aa / (aa + bb)


def frontier(ag, living, cfg):
    """The backup stock a decisive win must clear."""
    caps = [o.cap for o in living if o is not ag]
    if not caps:
        return 0.0
    return sum(caps) if cfg["frontier_rule"] == "sum" else max(caps)


# ---------------------------------------------------------------- operations

class Op:
    """An in-flight operation. kind in {"recon","repo"}; actors lock arms."""

    def __init__(self, actors, target, kind, info=False):
        self.actors, self.target, self.kind = actors, target, kind
        self.done, self.detectors, self.info = 0, set(), info

    def alive_actors(self):
        return [a for a in self.actors if a.alive]


def team_cap(actors, cfg, info=False):
    c = sum(a.cap for a in actors if a.alive)
    return c * (1.0 + cfg["info_gain"]) if info else c


def repo_defense(actors, target, living, cfg):
    """Repossession is overt, so the target plus every willing resister
    answers, combined by the usual `response_rule`. This is where the
    cumulative collective capability still enters."""
    aset = {id(a) for a in actors}
    caps = [target.cap]
    for o in living:
        if id(o) in aset or o is target:
            continue
        if not resists(o, actors[0], cfg):
            continue
        caps.append(o.cap)
    return response_of(caps, cfg)


def transfer(actors, target, share, cfg, st):
    """Move `share` of the target's capability out; actors receive
    transfer_mult x it, split in proportion to what they brought."""
    amt = share * target.cap
    target.cap = max(cfg["cap_floor"], target.cap - amt)
    gain = cfg["transfer_mult"] * amt
    live = [a for a in actors if a.alive]
    tot = sum(a.cap for a in live) or 1.0
    for a in live:
        a.cap += gain * (a.cap / tot)
    st["taken"] += amt
    st["given"] += gain


def out(ag, rnd, cfg):
    ag.out_until = rnd + cfg["sanction_len"]
    ag.cool_until = rnd + cfg["kappa"]


def suspected(obs, mover, rnd):
    """Does `obs` have grounds to raid `mover`? Either it was caught before,
    or this observer detected it preparing."""
    return mover.out_until > rnd or obs.id in mover.prep_detectors


# ------------------------------------------------------------------- one run

def setup(cfg, seed):
    random.seed(seed)
    movers, nc = cfg["movers"], cfg["N"] - len(cfg["movers"])
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
                            pdelta=m.get("delta"),
                            pd=m.get("pd", cfg["mover_pd"])))
    if cfg["rival_ratio"] > 0 and nc:
        agents[0].cap = cfg["rival_ratio"] * gcap
    for a in agents:
        a.out_until = a.cool_until = -1
        a.info_on = set()
    return agents, (agents[nc] if movers else None)


def new_stats():
    return dict(att=0, dw=0, dl=0, iw=0, il=0, end=None, first=None,
                m_recon=0, m_recon_ok=0, m_repo=0, m_repo_ok=0,
                d_recon=0, d_repo=0, d_repo_ok=0, taken=0.0, given=0.0,
                lead0=None, lead_end=None, out_rounds=0, last_round=-1)


def resolve_ops(ops, living, cfg, st, rnd):
    keep = []
    for op in ops:
        act = op.alive_actors()
        if not act or not op.target.alive:
            continue
        op.done += 1
        mv = act[0].is_mover
        if op.kind == "recon":
            for o in living:
                if o not in act and random.random() < cfg["d_recon"]:
                    op.detectors.add(o.id)
            if op.done < cfg["pi_r"]:
                keep.append(op)
                continue
            st["m_recon" if mv else "d_recon"] += 1
            if random.random() < contest(team_cap(act, cfg), op.target.cap,
                                         cfg["contest_m"]):
                if mv:
                    st["m_recon_ok"] += 1
                transfer(act, op.target, cfg["recon_gain"], cfg, st)
                for a in act:
                    a.info_on.add(op.target.id)
            if op.detectors:                      # caught looking
                for a in act:
                    out(a, rnd, cfg)
            continue
        if op.done < cfg["kappa"]:                # repossession
            keep.append(op)
            continue
        st["m_repo" if mv else "d_repo"] += 1
        eff = team_cap(act, cfg, info=op.info)
        dfs = repo_defense(act, op.target, living, cfg)
        for a in act:
            out(a, rnd, cfg)                      # detection is certain
        if random.random() < contest(eff, dfs, cfg["contest_m"]):
            st["m_repo_ok" if mv else "d_repo_ok"] += 1
            transfer(act, op.target, cfg["take_frac"], cfg, st)
        else:
            for a in act:
                if dfs >= cfg["K_loss"] * a.cap:
                    a.alive = False
                    st["dl"] += 1
                else:
                    a.cap = max(cfg["cap_floor"],
                                a.cap * (1.0 - cfg["loss_hit_r"]))
                a.info_on.discard(op.target.id)
    return keep


def resolve_grabs(grabs, living, cfg, st, rnd):
    """v4's grab rule, kept verbatim. Returns (still_running, game_over)."""
    keep = []
    for (ag, done, edet, ps) in grabs:
        if not ag.alive:
            continue
        done += 1
        te = cfg["tau"] if cfg["tau"] < cfg["kappa"] else 0
        if te > 0 and done <= te:
            for o in living:
                if o is not ag and random.random() < cfg["d"]:
                    edet.add(o.id)
        if done < cfg["kappa"]:
            keep.append((ag, done, edet, ps))
            continue
        ids = ag.prep_detectors | edet
        resp = response_of([o.cap for o in living if o.id in ids
                            and o is not ag and resists(o, ag, cfg)], cfg)
        st["att"] += 1
        if st["first"] is None:
            st["first"] = rnd
        fr = frontier(ag, living, cfg)
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
                ag.alive = False
                continue
            st["il"] += 1
            ag.score -= f * L
            ag.cap = max(cfg["cap_floor"], ag.cap * (1.0 - cfg["loss_hit"]))
        out(ag, rnd, cfg)
        ag.grabbed_at, ag.preparing, ag.prep_detectors = None, 0, set()
    return keep, False


def decide_movers(living, cfg, st, rnd, ops, grabs, busy, ver):
    for a in living:
        if not a.is_mover or id(a) in busy or a.cool_until > rnd:
            continue
        others = [o for o in living if o is not a]
        if not others:
            continue
        ok, p, q = t4.wants4(a, others, cfg, ver)
        if a.preparing > 0:
            a.preparing += 1
            if a.preparing > cfg["pi"]:
                a.grabbed_at, a.believed_p = rnd, p
                grabs.append((a, 0, set(), rnd))
                busy.add(id(a))
            continue
        if ok:                                  # the full, game-ending grab
            if cfg["pi"] == 0:
                a.grabbed_at, a.believed_p = rnd, p
                grabs.append((a, 0, set(), rnd))
                busy.add(id(a))
            else:
                a.preparing = 1
            continue
        tgt = max(others, key=lambda o: o.cap)  # otherwise, an operation
        if not cfg["ops"]:
            continue
        if cfg["recon"] and tgt.id not in a.info_on:
            ops.append(Op([a], tgt, "recon"))
            busy.add(id(a))
        elif contest(team_cap([a], cfg, info=tgt.id in a.info_on),
                     repo_defense([a], tgt, living, cfg),
                     cfg["contest_m"]) > 0.5:
            ops.append(Op([a], tgt, "repo", info=tgt.id in a.info_on))
            busy.add(id(a))


def defender_raids(living, cfg, rnd, ops, busy):
    """Defenders may raid a SUSPECTED mover, locking arms `coalition` deep."""
    for m in [x for x in living if x.is_mover]:
        pool = [o for o in living if not o.is_mover and id(o) not in busy
                and o.cool_until <= rnd and suspected(o, m, rnd)]
        if not pool:
            continue
        pool.sort(key=lambda o: o.cap, reverse=True)
        team = pool[:max(1, cfg["coalition"])]
        info = all(m.id in o.info_on for o in team)
        if cfg["recon"] and not info:
            ops.append(Op(team, m, "recon"))
        elif contest(team_cap(team, cfg, info=info),
                     repo_defense(team, m, living, cfg),
                     cfg["contest_m"]) > 0.5:
            ops.append(Op(team, m, "repo", info=info))
        else:
            continue
        busy.update(id(o) for o in team)


def play_pd(living, cfg, rnd):
    random.shuffle(living)
    for k in range(0, len(living) - 1, 2):
        x, y = living[k], living[k + 1]

        def mv(me, opp):
            if opp.out_until > rnd and not me.is_mover:
                return "D"                      # sanction anyone caught
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
        if mx == "D":
            y.grim_broken.add(x.id)
        if my == "D":
            x.grim_broken.add(y.id)


def run5(cfg, seed):
    # v4 cells DELEGATE to v4: exact by construction, not a reimplementation.
    if not cfg["ops"] and cfg["g_def"] == 0.0:
        return t4.run4({k: cfg[k] for k in t4.BASE}, seed)
    agents, leader = setup(cfg, seed)
    st = new_stats()
    ops, grabs, ver = [], [], 0

    for rnd in range(cfg["rounds"]):
        st["last_round"] = rnd
        living = [a for a in agents if a.alive]
        if len(living) < 2:
            break

        # growth: the leader compounds at gamma, defenders catch up at g_def
        for a in living:
            r = cfg["g"] + (cfg["gamma"] if a is leader else 0.0)
            if not a.is_mover:
                r += cfg["g_def"]
            if r:
                a.cap *= 1.0 + r
        if cfg["gamma"] or cfg["g"] or cfg["g_def"]:
            ver += 1
        if leader is not None and leader.alive:
            ld = leader.cap / max(cfg["cap_floor"],
                                  frontier(leader, living, cfg))
            if st["lead0"] is None:
                st["lead0"] = ld
            st["lead_end"] = ld

        for a in living:
            if a.preparing > 0 and a.grabbed_at is None:
                for o in living:
                    if o is not a and random.random() < cfg["a"]:
                        a.prep_detectors.add(o.id)

        ops = resolve_ops(ops, living, cfg, st, rnd)
        grabs, over = resolve_grabs(grabs, living, cfg, st, rnd)
        if over:
            return st
        busy = ({id(a) for op in ops for a in op.actors}
                | {id(e[0]) for e in grabs})
        decide_movers(living, cfg, st, rnd, ops, grabs, busy, ver)
        if cfg["ops"] and cfg["def_raid"]:
            defender_raids(living, cfg, rnd, ops, busy)
        play_pd(living, cfg, rnd)
        st["out_rounds"] += sum(1 for a in living if a.out_until > rnd)
    return st


# ------------------------------------------------------------------ reporting

def agg5(cfg, seeds):
    rs = [run5(cfg, s) for s in range(seeds)]
    n = len(rs)
    o = {}
    for k in ("att", "dw", "dl", "iw", "il", "m_recon", "m_repo", "m_repo_ok",
              "d_recon", "d_repo", "d_repo_ok", "taken", "given", "out_rounds"):
        v = [float(r.get(k, 0)) for r in rs]
        o[k] = sum(v) / n
    o["dw_ci"] = boot_ci([float(r["dw"]) for r in rs])
    for k in ("end", "first", "lead0", "lead_end"):
        v = [r[k] for r in rs if r.get(k) is not None]
        o[k] = sum(v) / len(v) if v else None
    o["n_end"] = sum(1 for r in rs if r.get("end") is not None)
    return o


def fm(x, d=2):
    return "  n/a" if x is None else f"{x:.{d}f}"


def row(name, o):
    lo, hi = o["dw_ci"]
    return (f"{name:24s} lead0={fm(o['lead0'],2):>6s}->{fm(o['lead_end'],2):>7s} "
            f"END={fm(o['dw'])}[{lo:.2f},{hi:.2f}] died={fm(o['dl'])} "
            f"mRepo={fm(o['m_repo'],1):>5s}/{fm(o['m_repo_ok'],1):<5s} "
            f"dRepo={fm(o['d_repo'],1):>5s}/{fm(o['d_repo_ok'],1):<5s} "
            f"took={fm(o['taken'],1):>6s} tEnd={fm(o['end'],1):>6s}")


def selftest():
    ok = True
    for name, over in (("base", {}), ("max", dict(response_rule="max")),
                       ("r.8maxK2", dict(rival_ratio=0.8, response_rule="max",
                                         K_win=2.0, K_loss=2.0)),
                       ("ratchet", dict(rival_ratio=0.8, response_rule="max",
                                        K_win=2.0, K_loss=2.0, win_boost=0.1))):
        c4, c5 = t4.cell(**over), cell(ops=False, g_def=0.0, **over)
        same = all(t4.run4(c4, s) == run5(c5, s) for s in range(8))
        print(f"ops=False,g_def=0 reproduces v4 [{name}]: {same}")
        ok &= same
    a = [run5(cell(), s)["m_repo"] for s in range(5)]
    b = [run5(cell(), s)["m_repo"] for s in range(5)]
    print(f"determinism: {a == b}")
    ok &= a == b
    # a raid must conserve capability when transfer_mult=1
    c = cell(transfer_mult=1.0)
    r = run5(c, 0)
    print(f"transfer check: took={r['taken']:.3f} gave={r['given']:.3f} "
          f"equal={abs(r['taken']-r['given'])<1e-9}")
    ok &= abs(r["taken"] - r["given"]) < 1e-9
    print("selftest", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    block = sys.argv[2] if len(sys.argv) > 2 else "all"
    res = {}

    def do(name, **over):
        o = agg5(cell(**over), seeds)
        res[name] = o
        print(row(name, o), flush=True)

    MX = dict(response_rule="max")
    RK = dict(rival_ratio=0.8, K_win=2.0, K_loss=2.0, **MX)

    if block in ("all", "A"):
        print("=== A. DEFENDER CATCH-UP: does g_def >= gamma hold the order? ===")
        print("--- A1: growth ONLY, no operations (ops=False) ---")
        for gm in (0.0, 0.02, 0.05):
            for gd in (0.0, 0.01, 0.02, 0.05, 0.08):
                do(f"A1_gam{gm}_gdef{gd}", ops=False, gamma=gm, g_def=gd, **RK)
        print("--- A2: same grid WITH operations, to separate growth from raids ---")
        for gm in (0.0, 0.02, 0.05):
            for gd in (0.0, 0.01, 0.02, 0.05, 0.08):
                do(f"A2_gam{gm}_gdef{gd}", ops=True, gamma=gm, g_def=gd, **RK)

    if block in ("all", "B"):
        print("\n=== B. transfer_mult: Catan bandit (damp) or accelerant? ===")
        for tm in (0.0, 0.5, 1.0, 1.5):
            do(f"B_mult{tm}", transfer_mult=tm, gamma=0.02, **RK)
            do(f"B_mult{tm}_nodef", transfer_mult=tm, gamma=0.02,
               def_raid=False, **RK)
        print("--- B2: raiding forced to matter (K=6 makes the grab unattractive,"
              " take_frac=0.3) ---")
        for tm in (0.0, 0.5, 1.0, 1.5):
            do(f"B2_mult{tm}", transfer_mult=tm, take_frac=0.3, gamma=0.02,
               rival_ratio=0.8, K_win=6.0, K_loss=2.0, **MX)
            do(f"B2_mult{tm}_nodef", transfer_mult=tm, take_frac=0.3,
               gamma=0.02, def_raid=False, rival_ratio=0.8, K_win=6.0,
               K_loss=2.0, **MX)

    if block in ("all", "C"):
        print("\n=== C. defensive raids + locking arms (coalition depth) ===")
        for co in (1, 2, 3, 5):
            do(f"C_coal{co}", coalition=co, gamma=0.02, **RK)
        do("C_nodefraid", def_raid=False, gamma=0.02, **RK)

    if block in ("all", "D"):
        print("\n=== D. recon: is the two-stage op better than blind repo? ===")
        for rc in (True, False):
            for dr in (0.1, 0.3, 0.6):
                do(f"D_recon{int(rc)}_d{dr}", recon=rc, d_recon=dr,
                   gamma=0.02, **RK)
        for ig in (0.0, 0.5, 1.0):
            do(f"D_info{ig}", info_gain=ig, gamma=0.02, **RK)

    if block in ("all", "E"):
        print("\n=== E. frontier_rule: must backups be cleared one by one? ===")
        for fr in ("max", "sum"):
            for K in (1.0, 2.0):
                do(f"E_{fr}_K{K}", frontier_rule=fr, K_win=K, K_loss=K,
                   rival_ratio=0.8, gamma=0.02, **MX)
                do(f"E_{fr}_K{K}_sumresp", frontier_rule=fr, K_win=K,
                   K_loss=K, rival_ratio=0.8, gamma=0.02)

    out = f"raw/results_v5{'' if block == 'all' else '_' + block}.json"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {len(res)} cells -> {out}")

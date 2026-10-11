#!/usr/bin/env python3
"""
probe_race2.py -- mixed-strategy equilibrium of the depth race.

WHY. probe_race.py: deep tasks (D >= 0) have NO pure-strategy equilibrium --
best-response iteration cycles. That is the textbook signature of a
preemption game (Fudenberg & Tirole 1985): each player wants to go just
before the other, the undercutting unravels, and equilibrium is mixed.
Also: B4 'PASS' in probe_race.py was VACUOUS -- all() over an empty set,
because only the N=1 row converged. Fifth scaffolding bug; new kind.

METHOD. Two players (leader i=0, follower i=1, follower starts `gap`
doublings behind). Payoff matrices A_i[u][t] on a grid; fictitious play
(each best-responds to the opponent's empirical mixture) for ITERS rounds.
Convergence is checked, not assumed: report the exploitability (max gain
from deviating against the opponent's mixture). Rows with exploitability
> EPS are reported as NOT CONVERGED and excluded from every check.

SAFEGUARDS.
 - Umax doubled check on the leader's mean attempt time.
 - Every check counts its eligible rows and FAILS if that count is < 3
   (no vacuous truth over empty sets).

PRE-REGISTERED (written before running; unchanged from probe_race B1/B3/B4,
restated for the mixed equilibrium):
 M1 translation invariance under equal growth: across D >= 0, leader mean
    attempt depth varies <= 0.15 doublings and leader win share <= 0.02.
 M2 exclusion needs divergent growth: leader 1.2x faster -> leader win share
    rises with D by > 0.05 from lowest to highest eligible D.
 M3 race pulls attempts out: mixed-equilibrium mean attempt depth of the
    leader > solo optimum (-5.99), and rises as gap shrinks.
"""
import math, json, os

BETA, D_DAYS, R_YR, C = 0.591, 128.744, 0.05, 0.05
R_U = R_YR * D_DAYS / 365.0
STEP, ITERS, EPS = 0.1, 1500, 0.003
sig = lambda z: 1.0 / (1.0 + math.exp(-z)) if z > -700 else 0.0
SOLO = -5.99


def build(D, gap, rates, umax):
    grid = [k * STEP for k in range(int(round(umax / STEP)) + 1)] + [None]  # None = never
    def p(i, u):
        x = D + i * gap - rates[i] * u
        return sig(-BETA * x), x
    A = [[[0.0] * len(grid) for _ in grid] for _ in (0, 1)]
    for i in (0, 1):
        for a, u in enumerate(grid):
            if u is None:
                continue
            pi = p(i, u)[0]
            disc = math.exp(-R_U * u)
            for b, t in enumerate(grid):
                j = 1 - i
                if t is None or t > u + 1e-9:
                    win = pi
                elif abs(t - u) < 1e-9:
                    pj = p(j, t)[0]
                    win = pi * (1 - pj) + pi * pj * 0.5
                else:
                    win = (1 - p(j, t)[0]) * pi
                A[i][a][b] = disc * (win - C)
    return grid, A, p


def fp(A, n):
    cnt = [[0] * n, [0] * n]
    cnt[0][n - 1] = cnt[1][n - 1] = 1
    for _ in range(ITERS):
        for i in (0, 1):
            opp = cnt[1 - i]; tot = sum(opp)
            best, bv = n - 1, 0.0
            Ai = A[i]
            for a in range(n):
                row = Ai[a]
                v = sum(row[b] * opp[b] for b in range(n) if opp[b]) / tot
                if v > bv:
                    best, bv = a, v
            cnt[i][best] += 1
    mix = [[c / sum(cnt[i]) for c in cnt[i]] for i in (0, 1)]
    expl = 0.0
    for i in (0, 1):
        opp = mix[1 - i]
        vals = [sum(A[i][a][b] * opp[b] for b in range(n)) for a in range(n)]
        cur = sum(mix[i][a] * vals[a] for a in range(n))
        expl = max(expl, max(max(vals), 0.0) - cur)
    return mix, expl


def outcome(grid, mix, p):
    n = len(grid)
    win = [0.0, 0.0]; unsolved = 0.0; xmean = [0.0, 0.0]; mass = [0.0, 0.0]
    tmean = 0.0
    for a in range(n):
        for b in range(n):
            w = mix[0][a] * mix[1][b]
            if w < 1e-9:
                continue
            u, t = grid[a], grid[b]
            seq = sorted([(x, i) for x, i in ((u, 0), (t, 1)) if x is not None])
            surv = 1.0; k = 0
            while k < len(seq):
                same = [s for s in seq[k:] if abs(s[0] - seq[k][0]) < 1e-9]
                ps = [p(i, x)[0] for x, i in same]
                for m, (x, i) in enumerate(same):
                    others = ps[:m] + ps[m + 1:]
                    tie = 1.0 if not others else (1 - others[0]) + others[0] * 0.5
                    win[i] += w * surv * ps[m] * tie
                for q in ps:
                    surv *= 1 - q
                k += len(same)
            unsolved += w * surv
    for i in (0, 1):
        for a in range(n - 1):
            if mix[i][a] > 0:
                xmean[i] += mix[i][a] * p(i, grid[a])[1]
                mass[i] += mix[i][a]
        xmean[i] = xmean[i] / mass[i] if mass[i] > 0 else None
    t0 = sum(mix[0][a] * grid[a] for a in range(n - 1))
    t0 = t0 / mass[0] if mass[0] > 0 else None
    spread = None
    if mass[0] > 0:
        xs = [(mix[0][a] / mass[0], p(0, grid[a])[1]) for a in range(n - 1) if mix[0][a] > 0]
        m = xmean[0]
        spread = math.sqrt(sum(w * (x - m) ** 2 for w, x in xs))
    return {"win": win, "unsolved": unsolved, "x_mean": xmean, "x_sd_lead": spread,
            "t_lead_days": t0 * D_DAYS if t0 is not None else None, "attempt_mass": mass}


def run(D, gap, rates):
    res = []
    for umax in (D + 10, 2 * (D + 10)):
        grid, A, p = build(D, gap, rates, umax)
        mix, ex = fp(A, len(grid))
        res.append((outcome(grid, mix, p), ex))
    (o1, e1), (o2, e2) = res
    stable = (o1["x_mean"][0] is not None and o2["x_mean"][0] is not None and
              abs(o1["x_mean"][0] - o2["x_mean"][0]) <= 0.1)
    st = "OK" if (e2 <= EPS and stable) else ("NOCONV" if e2 > EPS else "UNSTABLE")
    return o2, e2, st


out = {}
print("=" * 80)
print(f"mixed-equilibrium depth race, 2 players. fictitious play {ITERS} it, exploitability tol {EPS}")
print("=" * 80)
hdr = (f"{'D':>5}{'status':>9}{'expl':>8}{'x_lead mean':>12}{'sd':>6}{'x_fol mean':>11}"
       f"{'lead win':>10}{'fol win':>9}{'unsolved':>10}{'lead t(d)':>10}")


def show(rows):
    print(hdr)
    for D, o, e, st in rows:
        f = lambda v: f"{v:+.2f}" if v is not None else "  --"
        print(f"{D:>5.1f}{st:>9}{e:>8.4f}{f(o['x_mean'][0]):>12}"
              f"{(o['x_sd_lead'] or 0):>6.2f}{f(o['x_mean'][1]):>11}"
              f"{o['win'][0]:>10.3f}{o['win'][1]:>9.3f}{o['unsolved']:>10.3f}"
              f"{(o['t_lead_days'] or 0):>10.0f}")


print("\n--- equal growth, gap=1 ---")
eq = []
for D in (-3.0, -1.0, 0.0, 1.0, 2.0, 4.0):
    o, e, st = run(D, 1.0, [1.0, 1.0]); eq.append((D, o, e, st))
show(eq)
print("\n--- leader grows 1.2x faster, gap=1 ---")
fa = []
for D in (0.0, 1.0, 2.0, 4.0):
    o, e, st = run(D, 1.0, [1.2, 1.0]); fa.append((D, o, e, st))
show(fa)
print("\n--- gap sweep at D=2, equal growth ---")
gs = []
for g in (0.25, 0.5, 1.0, 2.0, 3.0):
    o, e, st = run(2.0, g, [1.0, 1.0]); gs.append((g, o, e, st))
print(hdr.replace("    D", "  gap"))
for g, o, e, st in gs:
    f = lambda v: f"{v:+.2f}" if v is not None else "  --"
    print(f"{g:>5.2f}{st:>9}{e:>8.4f}{f(o['x_mean'][0]):>12}{(o['x_sd_lead'] or 0):>6.2f}"
          f"{f(o['x_mean'][1]):>11}{o['win'][0]:>10.3f}{o['win'][1]:>9.3f}"
          f"{o['unsolved']:>10.3f}{(o['t_lead_days'] or 0):>10.0f}")


def check(name, rows, fn, need=3):
    ok = [r for r in rows if r[3] == "OK"]
    if len(ok) < need:
        print(f"  {name}: only {len(ok)} converged rows (< {need}) -> VOID")
        return None
    v = fn(ok)
    print(f"  {name}: {'PASS' if v else 'FAIL'}  (n={len(ok)})")
    return v


print()
deepE = [r for r in eq if r[0] >= 0]
m1 = check("M1 translation invariance (equal growth, D>=0)", deepE,
           lambda ok: (max(r[1]["x_mean"][0] for r in ok) - min(r[1]["x_mean"][0] for r in ok) <= 0.15
                       and max(r[1]["win"][0] for r in ok) - min(r[1]["win"][0] for r in ok) <= 0.02))
m2 = check("M2 exclusion needs divergent growth (fast leader)", fa,
           lambda ok: ok[-1][1]["win"][0] - ok[0][1]["win"][0] > 0.05)
m3 = check("M3 race pulls leader out; more so as gap shrinks", gs,
           lambda ok: all(r[1]["x_mean"][0] > SOLO for r in ok) and
           all(ok[k][1]["x_mean"][0] >= ok[k + 1][1]["x_mean"][0] - 0.05 for k in range(len(ok) - 1)))
ser = lambda rows: [{"key": r[0], "status": r[3], "expl": r[2], **r[1]} for r in rows]
out = {"equal": ser(eq), "fast": ser(fa), "gap": ser(gs), "M1": m1, "M2": m2, "M3": m3}
os.makedirs("raw", exist_ok=True)
json.dump(out, open("raw/probe_race2.json", "w"), indent=2, default=str)
print("\nwrote raw/probe_race2.json")

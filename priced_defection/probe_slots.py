#!/usr/bin/env python3
"""
PROBE: is there an INTERIOR optimum in action slots?

Mike, 2026-10-08: "everyone has too many action slots and doesn't know what
to do with them... 1000 agents and no work done... many agents thrown at the
same problem with diminishing marginal return to exploration of low hanging
fruit."

That is three distinct claims, and they are NOT the same as concavity:

  (a) CONGESTION   -- many agents on one opportunity split or waste it
  (b) DEPLETION    -- low-hanging fruit is picked once and then gone
  (c) ALLOCATION   -- slots you cannot aim are worth nothing, and may cost
                      something (the psychosis case: 1000 agents, no work)

(a) and (b) give DIMINISHING returns. Only (c) can give NEGATIVE marginal
returns, and only (c) predicts an INTERIOR optimum in k -- a best number of
agents, beyond which more is worse. That is the falsifiable core of Mike's
claim, so it is what this probe tests.

Deliberately a toy, standalone, no import from the tournament line. It
isolates one mechanism; it is not a result about the world.

Opportunity set: M opportunities per round with Pareto-ish values (a few
worth a lot -- the low-hanging fruit). Commonly visible, which is Mike's
"same problem" case. Each agent ranks them under its OWN noise `sigma_q`
(question-selection skill: low sigma = sees which question matters) and
takes its top k. Congestion splits an opportunity's value among claimants.
Depletion removes what was taken. Allocation overhead charges `oh * k^gamma`
per round, so gamma>1 is the psychosis term.

Reports value captured per agent against k, and locates the optimum.
"""
import random
import math

T, R, P, S = 5.0, 3.0, 1.0, 0.0


def run(k, N=20, M=30, rounds=200, sigma_q=0.5, oh=0.0, gamma=1.0,
        congest="split", deplete=True, tail=1.5, seed=0, regen=0.3):
    rng = random.Random(seed)
    # standing stock of opportunities; regenerates slowly
    stock = [rng.paretovariate(tail) for _ in range(M)]
    captured = [0.0] * N
    paid = 0.0
    for _ in range(rounds):
        if not stock:
            stock = [rng.paretovariate(tail) for _ in range(M)]
        # every agent ranks the SAME visible stock under its own noise
        claims = {}
        for a in range(N):
            est = [(v * math.exp(rng.gauss(0.0, sigma_q)), i)
                   for i, v in enumerate(stock)]
            est.sort(reverse=True)
            for _, i in est[:k]:
                claims.setdefault(i, []).append(a)
        taken = []
        for i, who in claims.items():
            v = stock[i]
            if congest == "split":
                share = v / len(who)
                for a in who:
                    captured[a] += share
            else:                      # winner-takes-all, rest wasted
                captured[who[0]] += v
            if deplete:
                taken.append(i)
        for i in sorted(taken, reverse=True):
            stock.pop(i)
        # regenerate: new fruit appears, but the easy stuff is gone first
        n_new = int(regen * M)
        stock.extend(rng.paretovariate(tail) for _ in range(n_new))
        stock = stock[:M * 2]
        # allocation overhead: the cost of HAVING slots to aim
        paid += oh * (k ** gamma) * N
    tot = sum(captured)
    return (tot - paid) / N


def sweep(label, **kw):
    print(f"\n{label}")
    ks = (1, 2, 3, 5, 8, 12, 20, 32, 50)
    out = []
    for k in ks:
        v = sum(run(k, seed=s, **kw) for s in range(8)) / 8
        out.append((k, v))
    best = max(out, key=lambda x: x[1])
    for k, v in out:
        bar = "#" * max(0, int(v / max(1e-9, best[1]) * 40))
        mark = " <-- best" if k == best[0] else ""
        print(f"   k={k:3d}  net/agent={v:9.2f}  {bar}{mark}")
    print(f"   optimum k = {best[0]}")
    return best[0]


if __name__ == "__main__":
    print("=" * 68)
    print("A. CONGESTION + DEPLETION ONLY (no allocation overhead)")
    print("   Mike's (a)+(b). Expect DIMINISHING but never negative ->")
    print("   optimum at the largest k, i.e. no interior optimum.")
    print("=" * 68)
    sweep("A1 split congestion, depleting stock, skilled selection (sigma=0.5)",
          oh=0.0)
    sweep("A2 same, but POOR selection (sigma=2.0: cannot tell which matters)",
          oh=0.0, sigma_q=2.0)

    print()
    print("=" * 68)
    print("B. ADD THE ALLOCATION OVERHEAD (Mike's psychosis term)")
    print("   gamma>1 = slots cost superlinearly to aim. Expect an")
    print("   INTERIOR optimum: a best number of agents.")
    print("=" * 68)
    for gamma in (1.0, 1.3, 1.6):
        sweep(f"B gamma={gamma}, oh=0.02", oh=0.02, gamma=gamma)

    print()
    print("=" * 68)
    print("C. DOES QUESTION-SELECTION SKILL MOVE THE OPTIMUM?")
    print("   If the binding constraint is knowing WHICH question to ask,")
    print("   better selection should RAISE the optimal slot count.")
    print("=" * 68)
    for sq in (0.2, 0.5, 1.0, 2.0):
        sweep(f"C sigma_q={sq} (lower = better at picking the question)",
              oh=0.02, gamma=1.3, sigma_q=sq)

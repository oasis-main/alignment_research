# The depth race: rivals as real agents (probe, 2026-10-08)

Scripts: `probe_race.py` (pure strategies, N=5), `probe_race2.py` (mixed strategies, 2 players).
Raw: `raw/probe_race.json`, `raw/probe_race2.json`. Both pre-registered in their docstrings.

**Question.** `probe_depth_bound` showed that a rival hazard λ pulls attempts toward the
horizon, but λ was an assumption. Here the rivals are real agents with their own METR
horizons who pick their own attempt times. One task, one prize. Each agent gets one attempt,
and a failed attempt costs a stake. Does deep work shut rivals out ("exclusion"), while
shallow work draws a crowd ("congestion")?

## Answer: no, not when everyone's capability grows at the same rate

## 1. No pure-strategy equilibrium on deep tasks

For tasks at or beyond the leader's horizon (D ≥ 0), best-response iteration **cycles** in
every N=5 run. That's the standard signature of a preemption game (Fudenberg & Tirole 1985).
Each player wants to go just before the other, the undercutting never settles, and the only
equilibrium is mixed. So `probe_race.py`'s B1 and B3 are VOID and FAIL purely because of
cycling. They say nothing about the world.

**Fifth scaffolding bug, and a new kind.** `probe_race.py` printed B4 "PASS". Only the N=1
row converged, so the check ran `all()` over an empty set and returned True vacuously.
`probe_race2.py` now requires at least 3 converged rows before any check can pass or fail.

## 2. Shallow tasks: congestion (pure, holds)

Tasks well inside everyone's horizon get rushed: 4–5 of 5 agents attempt at once at t=0
(B2 PASS, D = −6 to −1). That matches the congestion found in pass 9.

## 3. Deep tasks, equal growth: the race is the same game, just later (M1 PASS, n=4)

Mixed equilibrium, 2 players, follower 1 doubling behind:

| task depth D | leader attempts at (doublings rel. own horizon) | leader wins | follower wins | nobody solves it | leader's mean attempt time |
|---|---|---|---|---|---|
| 0 | −1.00 | 0.481 | 0.331 | 0.188 | 129 d |
| 1 | −1.15 | 0.479 | 0.338 | 0.183 | 276 d |
| 2 | −1.15 | 0.479 | 0.338 | 0.183 | 405 d |
| 4 | −1.15 | 0.479 | 0.338 | 0.183 | 663 d |

Making the task deeper only **delays** the race, by 129 days per doubling (one METR doubling
time). Attempt depths and win shares don't change. With equal growth, depth doesn't exclude
rivals. It pushes the same race later.

**The "congestion and exclusion are one curve" conjecture is false under equal growth.**
Congestion (shallow) and preemption (deep) are different equilibria. Neither one is exclusion.

## 4. One rival is enough to pull the leader far forward (M3 PASS, n=3)

With no rival, the leader waits until the task is about 1.6% of its horizon (x = −5.99,
success 97%). Gap sweep at D=2, equal growth:

| follower's gap (doublings) | leader attempts at | leader wins | nobody solves it | status |
|---|---|---|---|---|
| 0.5 | −0.78 | 0.443 | 0.190 | OK |
| 1.0 | −1.15 | 0.479 | 0.183 | OK |
| 3.0 | −2.14 | 0.630 | 0.154 | OK |
| (0.25, 2.0) | (−0.57, −1.57) | (0.421, 0.556) | | not converged, excluded |

A single rival one doubling behind moves the leader's attempt from 1.6% of its horizon to
about 45%. **The race costs reliability.** About 18% of races end with nobody solving the
task. With no rival, the leader would almost always have succeeded (97%), but roughly 600
days later. The trade is speed for failure.

## 5. Divergent growth: suggestive, but not established (M2 VOID)

When the leader grows 1.2× faster, its win share rises with depth in all 4 rows
(0.485, 0.499, 0.513, 0.540). Only 2 of those rows converged, so the pre-registered check
is **VOID**. That's a direction, not a result. If it holds up, exclusion comes from
**capability growing faster than rivals'**, not from depth itself.

## Scorecard

| check | result |
|---|---|
| B2 shallow → simultaneous rush | PASS |
| B1/B3/B4 (pure strategies) | VOID/FAIL from cycling; B4's "PASS" was vacuous |
| M1 deep race is translation-invariant | PASS (n=4) |
| M2 exclusion needs faster growth | VOID (2 converged rows; direction consistent) |
| M3 race pulls leader out, more as gap shrinks | PASS (n=3) |

## Caveats

- Two players only in the mixed case. N>2 mixed equilibria weren't computed.
- Fictitious play to exploitability 0.003. Five of 15 mixed rows didn't reach it and are excluded.
- One attempt per agent. Retries would change the race.
- Grid of 0.1 doublings ≈ 13 days.
- r = 5%/yr, stake 0.05 and the gaps are assumptions. Only β and the doubling time are measured.

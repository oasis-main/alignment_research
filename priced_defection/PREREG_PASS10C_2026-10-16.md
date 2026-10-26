# Pass 10 part C pre-registration (written 2026-10-16 ~23:45 UTC, before any part-C code or run)

Harness (to be written): `tournament10c.py`, importing tournament10. Every new switch off reproduces pass 10 seed-for-seed. Predictions below are mine, to be scored unchanged. Results go in `RESULTS_PASS10C_*.md`.

## What the probe found before this file (not a result, a design fact)

In the fixed pass-10 cells (S, M) with the default 200-round sanction, the mover NEVER raids: `n_seize` = 0 at c_seize 0.75 and at 0.05 (seeds 100-103, unscored). So the "regime switch to raiding" is not a missing action. The existing menu already contains `seize`; a 200-round sanction (cost about 20 budget units) prices it out. Part C therefore tests the switch as an emergent property of the menu (sweep lead and sanction length) and adds the two things that were actually missing: imperfect attribution and sanction breadth.

## Switches

- `mis` (m): when a raid or detected recon triggers a sanction, with probability m the sanction lands on a uniformly random OTHER living agent instead of the raider. The raider keeps its old sanction state. Applies to `resolve_ops7` (raids, recon) only. Failed takeovers keep their existing, correctly attributed sanction. Declared limit.
- `breadth` (b): in addition, each other living agent is sanctioned independently with probability b (collective punishment of everyone who looks like the attacker).
- The mover is UNAWARE of both (it prices the sanction as if attribution were perfect and narrow). Same convention as pass 10 unaware. An informed mover is not built here.
- All new randomness comes from a separate generator. The main stream is untouched when both are 0.

## Measures

- `inno_rounds`: agent-rounds in which an agent was under sanction that it did not earn (landed by misattribution or breadth).
- `pd_mean`: mean PD payoff per agent-round over the run (3.0 = full cooperation, 1.0 = full defection). Autoimmunity cost = pd_mean(mis=0,b=0) - pd_mean(cell), same cell, same seeds.
- `n_seize`, takeover rate `dw`, `att`.

## Predictions

**C1 (identity, must pass before any run).** mis=0 and breadth=0 equals pass 10 on both budget paths and on a gated cell; determinism; module patches undone. Failure voids the run.

**C2 (regime switch is emergent, and tracks sanction length).** In a raid-capable cell (cheap seize, take_frac 0.4, transfer_mult 1.5), mean raids per run are non-increasing in `sanction_len` over {10, 25, 50, 200}, with 0 at 200 (reproducing the probe) and a positive count at 10 outside the CI of 0. Falsified if no sanction length in the grid yields raids, in which case this model has no raiding regime at these prices and C3 to C5 are untestable in it.

**C3 (raids are a fallback below a lead threshold).** In the raid-capable cell, the share of aggressive actions that are raids, n_seize / (n_seize + n_prep), is non-increasing in lead0 over {1.0, 1.5, 2.0, 3.0}, and takeover rate is non-decreasing. Falsified if the share is flat within CI across the grid (no regime switch, just two independent behaviours).

**C4 (misattribution costs welfare and shifts the burden).** At fixed raid-capable cell and short sanction, pd_mean is non-increasing in m over {0, 0.25, 0.5, 1.0}; the m=1.0 value is below the m=0 value outside CI; `inno_rounds` rises with m. The reason, if it holds: a sanction on an innocent leaves a persistent record in its partners' tit-for-tat history, so the cost outlives the sanction window. Falsified if pd_mean at m=1.0 is within CI of m=0. (Raids per run are NOT predicted to move, since the mover is unaware; a move would be a leak, as in T8 of pass 10.)

**C5 (breadth is the autoimmune lever and weakens the defence that funds it).** In the same cell, pd_mean is non-increasing in b over {0, 0.25, 0.5, 1.0}, and in the calibrated pass-10 cell S the takeover rate is non-decreasing in b, because posture is bought from the budget that PD income fills and collective punishment cuts that income. Falsified, separately: pd_mean flat in b, or takeover flat in b within CI. The second is the more interesting one and I put it near 50%.

**C6 (misattribution lets the raider off).** The raider's own sanction-rounds fall in m, and raider score (PD income plus prizes) is non-decreasing in m. Falsified if raiders do not gain, which would mean the sanction is not what limits them in this cell.

## Calibration

A short declared calibration, seeds 100-109 and not scored, finds a raid-capable cell with 0.5 to 5 raids per run at lead0 near 1.5 and sanction_len 10. Cells are fixed in `raw/pass10c_cells.json` and committed BEFORE the scored 20-seed sweep (seeds 0-19). No cell edits after.

## Not tested here

- A mover that knows about misattribution or breadth.
- Misattribution of failed takeovers (they keep correct attribution).
- Any claim about real attribution problems in cyber operations. This is a statement about the model.

## What would change our minds

- C2 false: no raiding regime at any tested price, so the regime-switch item from the approved list is not realisable in this engine without changing the payoffs.
- C4 and C5 both false: the cooperative core is robust to sanction errors here, and "autoimmunity" is not a feature of this model.

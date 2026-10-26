# Pass 10 results: multi-gate takeovers, degraded alarm channel, informed mover (2026-10-16)

Scored against `PREREG_PASS10_2026-10-16.md` and `PREREG_PASS10_ADDENDUM_AWARE_2026-10-16.md`, both committed before the sweep and not edited since. Cells fixed in `raw/pass10_cells.json` before the sweep (calibration seeds 100-109, scored seeds 0-19). Raw: `raw/results_pass10.json`, log `raw/sweep_pass10.txt`, scorer `score_pass10.py`. Part C (raiding fallback, misattribution, autoimmunity) is NOT built and not reported here.

At 20 seeds a takeover rate has a 95% interval about +/-0.15 to 0.20 wide, so only large contrasts count. "Unaware" = `aware=False`, "informed" = `aware=True` (the mover is told the true gates and alarm loss: a best case for the mover).

Cells: S = max frontier, sum response, lead 2.5, cheap-ish capability (c_grow 0.3), calibrated 0.70. M = max frontier, max response, lead 1.25, c_grow 0.1, calibrated 0.40. SAT = max/sum, lead 3.0, c_grow 0.1. Z7 = sum frontier, sum response, lead 3.0, c_grow 0.1.

## Scorecard

| id | prediction (short) | verdict |
|---|---|---|
| T1 | identities (switches off reproduce pass 9; m=3,rho=1 = m=1; d>0,q=1 = d=0; determinism) | HOLDS (selftest PASS, run before the sweep) |
| T2 | takeover non-increasing in m, m=5 below m=1 outside CI | HOLDS in S (0.75, 0.60, 0.30, 0.05). NULL in M: outcomes identical at every m |
| T3 | rho=1 equals m=1; rho=0.5 lies between | HOLDS in S (0.75 / 0.50 / 0.05). M cannot test it (no gate effect) |
| T4 | saturated cell stays >= 0.90 at m=5 | FALSIFIED for the unaware mover (0.30 [0.10,0.50]). Holds for the informed mover (1.00) |
| T5 | takeover non-decreasing in e; at e=1 equals the no-posture run | PARTLY FALSE. Unaware S: flat 0.75 at every e, and e=1 (0.75) is below no-posture (1.00). Informed S: e=1 gives 1.00 = no-posture. M: nothing detectable |
| T6 | delivered/undelivered response ratio at e=0.5 is about 0.5 for sum, clearly higher for max | HOLDS. Sum 0.51 (S), 0.55 (M with sum response), 0.50 (Z7). Max 0.89 (M), 0.93 (S with max response) |
| T7 | sum-frontier cells stay 0.00 at every e | HOLDS, both movers, all five e values |
| T8 | unaware attempts do not move with m or e | FALSIFIED (see below). Not a bug |
| AW1 | informed attempts fall with m; below unaware at m=5 | HOLDS in S (informed 0.0 vs unaware 5.0 [3.4,6.5]). FAILS in M (19.8 vs 25.4, intervals overlap, not monotone) |
| AW2 | informed takeover no higher than unaware at m=5 | HOLDS in S (0.00 vs 0.05) and M (0.20 vs 0.15). FALSIFIED in SAT (1.00 vs 0.30) |
| AW3 | informed attempts exceed unaware at e=0.5 and 0.75 | HOLDS in S at both. M: only at 0.75. Z7: only at 0.75, and the reverse at 0.5 (10.9 vs 15.7) |
| AW4 | informed takeover >= unaware at e=0.5 | HOLDS, weakly (S 0.80 vs 0.75, M 0.30 vs 0.15, all within noise). "Effect was understated" is NOT supported at this power |
| AW5 | informed-minus-unaware gap peaks at e=0.5 | FALSIFIED in S (gaps 0, +0.15, +0.05, +0.15, +0.25: largest at e=1). M peaks at 0.5 but within noise |
| AW6 | unaware attempts flat, informed attempts move | FIRST HALF FALSIFIED (same cause as T8), second half holds |

Count: 4 hold clean (T1, T6, T7 and the S halves of T2/T3 only as cell-qualified), 4 fail outright (T4 unaware, T8, AW5, and AW2 in SAT), the rest are split by cell. I report the splits as splits.

## What the failures taught us

**1. Extra gates mostly make an unaware mover waste itself. They do not stop a mover that knows.**
- The first attempt happens in the same round at m=1 and m=5 in 15 of 15 seeds that attempt (S cell). So gates do not change when the mover goes.
- Per run in S, unaware: m=1 gives 1.2 attempts and 0.5 indecisive losses; m=5 gives 5.0 attempts and 5.0 indecisive losses. Each failure costs half its capability and a sanction, then it retries. Deaths are 0 everywhere.
- SAT, unaware, m=5: takeover 0.30 with 8.0 failed attempts per run. SAT, informed, m=5: takeover 1.00 with 0.1 failed attempts. The informed mover waits until its odds are good and then wins.
- This is why **T8 failed**: attempts are not independent of outcomes, because failure feeds back (retry after a setback). My pre-registered worry that this was a "belief leak bug" was wrong; it is outcome feedback. The "understated effect" caveat I wrote earlier was therefore too simple: an informed mover is deterred in S, undeterred in SAT, and in M gates changed nothing.

**2. Whether an informed mover is deterred by gates depends on capability price, not on the gates.**
Unscored post-hoc probe (`probe_pass10_posthoc.py`, same seeds, 4 cells x 2 x 2): informed, m=5, takeover: lead 2.5 with c_grow 0.3: 0.00. Lead 3.0 with c_grow 0.3: 0.10. Lead 2.5 with c_grow 0.1: 1.00. Lead 3.0 with c_grow 0.1: 1.00. Cheap growth lets the informed mover climb past the gates; dear growth keeps it out. This is the same price result as passes 6 to 8. It is 4 cells, a hypothesis for pass 11, not a result.

**3. The sum-frontier zeros are the win bar, now confirmed under the hardest test.**
Z7 stays at 0.00 at every e for both movers. The informed mover at e=1, told that no alarm will ever arrive, makes 163.8 attempts per run and still never takes over. Nothing a defender does or fails to do changes that. So stability in the sum-frontier cells must not be credited to the response at all. This tightens the 2x2 reading (C2) and it matters for the write-up: do not cite those cells as defence working.

**4. A dead defence still deters a mover who does not know it is dead.**
S, unaware: takeover is 0.75 at every e, including e=1 where no alarm is ever delivered. The same 5 of 20 seeds never attempt at e=0 and at e=1 (the mover's belief says a response exists). In the no-posture run, with no defenders to believe in, takeover is 1.00. So in S the 25% not taken over come from the mover's belief, not from alarms arriving. The informed mover at e=1 reaches 1.00. This is the bluff result from pass 8 again, now for a broken channel. It is also why AW5 failed: I predicted nothing to learn at e=1, and there is the most to learn there.

**5. Degradation matters much less than its delivery ratio suggests.**
At e=0.5 the delivered response is about half under a sum rule, and the outcome for the unaware mover does not move. In these cells alarm delivery is not the binding constraint; the mover's belief and the win bar are. One exception to check: informed attempts rise sharply with e in M (25 to 107) and Z7 (12 to 164) with takeover flat, so degradation mostly buys the mover more failed attempts.

**6. Correlated gates protect until the dependency is nearly total (partial support, not pre-registered as stated).**
S, m=5: unaware takeover 0.05 / 0.50 / 0.75 at rho = 0 / 0.5 / 1.0. Informed: 0.00 / 0.05 / 0.75. With rho=0.5, the expected number of independent gates is about 3 (1 + 4 x 0.5, simple arithmetic, mechanism not separately tested), which an informed mover still cannot clear. Only rho near 1 removes the protection. The pre-registered T3 tested only the midpoint of the unaware version.

## Limits
- 20 seeds. Most pairwise contrasts below about 0.25 are inside noise. I scored by interval overlap as pre-registered, over many cells, so a few "holds" and "fails" at the margin could flip.
- M is a null cell: extra gates changed the delivered response (ratio 1.03) but never an outcome. I did not test why. Likely candidates: the win bar (K_win x frontier) or one dominant defender sets the outcome there. Untested.
- The informed mover knows the true parameters and the world's d and m are fixed, not chosen. A mover that must learn d and m would sit between the two versions. A mover that can choose to degrade or add gates is not modelled.
- Mechanism claims in points 1, 2, 4 and 6 rest on counts I printed (attempts, indecisive losses, never-attempting seeds, first-attempt rounds) plus one four-cell post-hoc probe. They are consistent with the explanations given, and I have not run a direct intervention for each.
- Nothing here is calibrated to a real domain. The election, G7 and cyber analogies are not tested by this pass.

## What changes in the plan
- The earlier "known limit" caveat is replaced by the above: the informed version is not simply stronger. Report both.
- T7 and point 3 go into the claim ledger as one of the most robust results so far.
- Point 4 (a broken channel still deters an unaware mover) goes into pass 11 as a design question: what the mover can observe about whether the channel works.
- Pass 11 should include the capability-price sweep that point 2 suggests.

# Pass 10 part C follow-up, addendum G (written 2026-10-17 ~03:10 UTC, after the 60-seed follow-up was scored, before the pair diagnostic was run)

## Disclosure: what I had seen

The follow-up (seeds 200-259) is scored: see RESULTS_PASS10C_FOLLOWUP. Two results are unexplained and motivate this addendum:
1. F4 failed in an unexpected direction: misattribution (mis 1.0) RAISED pd_mean by +0.049, paired 95% CI [0.014, 0.089].
2. F8: sanctioned agents earn 1.63 less per round than unsanctioned ones, so innocent share x gap predicts a welfare drop of 0.27-0.39 for the mis and breadth arms. Observed paired changes are +0.05 (mis 1.0) and -0.05 (breadth 1.0). The naive arithmetic is off by a factor of 5-8 and, for mis, the sign.

Total sanctioned agent-rounds were conserved under mis 1.0 (575 vs 578) while events rose 16%, so what differs is the cost per sanctioned round, not the amount of sanctioning.

## Hypothesis H (mine, not yet tested)

The per-agent income gap overstates the group's loss, because the partner of a sanctioned agent is defecting against it and pockets part of the difference. The group-level cost of a sanctioned agent-round is the DEFICIT of the pair's joint income relative to an unsanctioned pair, and that deficit depends on who is sanctioned. A raider has been defecting and is likely to defect back (both defect: low joint income). An innocent who cooperates and is defected on produces a transfer from the sanctioned agent to its partner with a small joint deficit. If so, moving sanctions from raiders to innocents lowers the cost per sanctioned round, which would explain F4 and F8 together.

## Measurement (instrumentation only; identity re-checked as G0)

Each round, pairs are recovered from the PD shuffle and classified at the start of the round by sanction status:
- U: neither member sanctioned
- Or: exactly one sanctioned, and it has ever scouted or raided ("raider", defined at that round)
- Oi: exactly one sanctioned, not a raider ("innocent")
- B: both sanctioned
Per category: pair count and mean joint income per pair-round, and the income of the sanctioned and of the unsanctioned member. Reference for deficits: the mean joint income of U pairs in the SAME arm. Fresh seeds 300-359, arms base, mis 1.0, breadth 1.0, same RAID cell. Paired by seed where a category exists in both arms; otherwise pooled with seed-bootstrap.

## Predictions

**G0 (identity, voids the run).** Outcomes unchanged by the new instrumentation: every stored field equal to the follow-up result for seeds 200-205, three arms; determinism.

**G1 (partner gains).** In Oi and Or pairs, the UNSANCTIONED member earns more than the mean per-agent income in U pairs, by at least 0.3. Falsified if the excess is below 0.3 or its CI includes 0.

**G2 (raiders cost more than innocents).** Joint-income deficit per pair-round, relative to U pairs, is larger for Or than for Oi, with the seed-bootstrap CI of the difference excluding 0. This is the core of H.

**G3 (cost per sanctioned agent-round falls when sanctions move).** Total pair deficit divided by total sanctioned agent-rounds is at least 20% lower in mis 1.0 than in base. Falsified if the ratio of ratios exceeds 0.8.

**G4 (breadth cost is small because innocents mostly cooperate, but B pairs are expensive).** In the breadth 1.0 arm the B category exists and its deficit per pair-round exceeds the Oi deficit by at least a factor of 2. Falsified otherwise. (No direction pre-registered for how many B pairs there are.)

Each prediction is scored separately. If G1 and G2 both fail, H is dropped and the offset in F8 is unexplained; I will not construct a replacement from this data without a new prediction.

## Not tested

Whether the result survives other cells, other N, or a mover that knows about misattribution. Whether raider status as defined (ever scouted or raided) is a good proxy for "has been defecting" -- it is not measured directly.

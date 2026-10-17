# Pass 10 part C follow-up: results (2026-10-17)

Pre-registered in `PREREG_PASS10C_FOLLOWUP_2026-10-17.md` (F1-F8, commit 8e559fd) and `PREREG_PASS10C_FOLLOWUP_ADDENDUM_G_2026-10-17.md` (G0-G4, commit 3fd9d45; written after the F run was scored and before the G diagnostic existed). Cell: RAID, sanction_len 25. Seeds 200-259 (F) and 300-359 (G), fresh. All comparisons are paired by seed, percentile bootstrap over seeds. Scoring: `score_followup.py`, `score_g.py`, `posthoc_followup.py`. Raw: `raw/results_followup.json`, `raw/results_g.json`.

## Process notes

- Identity checks passed before each run: F1 (0 diffs vs stored pass-10c results, seeds 0-5, five arms) and G0 (0 diffs vs stored follow-up results, seeds 200-205, three arms). Determinism and patch-undo passed.
- The F2 confidence interval was computed after I saw the F results (the point estimate was already visible). It is the pre-registered statistic, but flagged.
- Pair recovery in G is from tit-for-tat histories. In one check it recovered 676 pair-rounds against about 695 expected (the odd agent sits out), so about 3% of pairs are missing.
- No bug was found in this round.

## Scorecard

| id | prediction | verdict |
|---|---|---|
| F1 | instrumentation does not change outcomes | PASS |
| F2 | sanctioned agent-rounds per event at mis 1.0 within 15% of base | Not falsified, not confirmed: ratio 0.854, CI [0.72, 0.97], on the edge of the band |
| F3 | events per run rise monotonically with mis; mis 1.0 above base, CI excludes 0 | **FALSIFIED** (not monotone: 37.3, 44.8, 43.4; paired +6.1, CI [-3.0, 16.1]) |
| F4 | paired pd_mean difference at mis 1.0 has CI including 0 | **FALSIFIED**: +0.049, CI [0.014, 0.089]. Welfare rose |
| F5a | breadth arms identical to base where base has no events | PASS (exact, 23 of 60 seeds) |
| F5b | breadth 1.0 paired pd_mean difference negative, CI excludes 0 | HOLDS: -0.054, CI [-0.084, -0.024] |
| F5c | effect larger among seeds with events | HOLDS: -0.087 over the 37 event seeds, CI [-0.131, -0.043] |
| F6 | innocent share at breadth 0.25 at least 0.85 of breadth 1.0 | HOLDS: 0.217 vs 0.241, ratio 0.90 |
| F7 | sanctioned agents earn at least 0.8 less per round | HOLDS: gap 1.63 (0.77 vs 2.40) |
| F8 | descriptive arithmetic | See below: the naive accounting is off by 5-8x |
| G0 | identity | PASS |
| G1 | the unsanctioned partner of a sanctioned agent earns at least 0.3 above the normal per-agent income | **FALSIFIED**: -0.40 (raider cases), -0.04 (innocent cases), both at or below normal |
| G2 | joint-income deficit is larger when the sanctioned agent is a raider than when it is an innocent | **FALSIFIED**: difference +0.026, CI [-0.11, 0.16] |
| G3 | cost per sanctioned agent-round at least 20% lower at mis 1.0 | **FALSIFIED**: ratio 1.017, CI [1.000, 1.037] |
| G4 | pairs where both are sanctioned cost at least 2x innocent-only pairs | **FALSIFIED**: ratio 1.58, CI [1.49, 1.71] |

Per the addendum's own rule, G1 and G2 both failed, so hypothesis H (the partner absorbs the loss, so moving sanctions to innocents is cheaper) is dropped. I am not building a replacement from this data without a new prediction. What follows is descriptive and marked as hypothesis.

## What changed from the 20-seed reading

1. **Pairing tightened the intervals from about ±0.14 to about ±0.04 on pd_mean.** The earlier "no autoimmune cost" was a power failure, not a finding. The breadth cost is now detected: roughly 0.05 on a base of 2.03, about 2.6%, concentrated in event seeds (-0.087).
2. **Misattribution does not hurt welfare here; it helps slightly** (+0.049, CI excludes 0). The 20-seed flat reading was too coarse to see it.
3. **The scout surge did not replicate.** The unscored diagnostic that suggested misattribution frees movers to scout more (275 to 452 over 20 seeds) comes out at +7.3 scouts per run (CI [-2.1, 17.8]) over 60 paired seeds. Runs under mis 1.0 are also about 10% longer (agent-rounds +201), so per-run counts are confounded with run length. Treat the surge as noise until a rate-based comparison says otherwise.
4. **The takeover sign flipped between seed sets** (breadth 1.0: -0.10 in seeds 0-19, +0.05 in seeds 200-259, both inside the CIs). The C5 takeover claim stays falsified as stated, but the direction is unstable and I would not read anything into it. Base takeover itself was 0.52 here against 0.70 in seeds 0-19, so single-seed-set levels are noisy.
5. **Misattribution lowers raids per run** (0.72 to 0.45, paired -0.27, CI [-0.50, -0.07]), which I did not predict.

## Descriptive reinterpretations (unscored; hypotheses)

- **The sanction is a quantity conserved per run, and what moves welfare is the change in total sanctioned time.** Total sanctioned agent-rounds per run were 578 (base), 575 (mis 1.0), 678 (breadth 0.25), 696 (breadth 1.0). Cost per sanctioned agent-round is about 1.5-1.6 in every arm (G3). Multiplying extra sanctioned time by that cost gives 0.086 for breadth 1.0 and 0.075 for breadth 0.25, against observed drops of 0.054 and 0.034. That is within a factor of about 1.6-2.2, not 5-8x. The naive "innocent share x income gap" arithmetic was wrong because most of those innocent rounds overlap time that raiders or others were already sanctioned (the both-sanctioned pairs dominate: 10,715 pairs against 4,029 innocent-only in base).
- **For misattribution the same arithmetic predicts about 0 (extra time -4 rounds) and the observed change is +0.049. That gap is unexplained.** Candidates, all untested: runs are 10% longer (more agent-rounds at the cheap end of the run); fewer raids; a sanctioned raider's partners cycle between punishment and forgiveness differently from a sanctioned bystander's. I will not pick one.
- **Most sanctions here come from detected recon, not raids.** About 37 sanction events per run against 0.7 raids per run; 29% of all agent-rounds in the base arm are spent under sanction. So the "regime switch to raiding" in this cell shows up as a scouting-and-getting-caught churn. The mover bears it (raider out-share 85%). Misattribution mostly relieves the mover (48%), which is the most consistent finding across both sets of seeds.
- **Breadth saturates**, as F6 held. After the first 25% breadth, the extra time sanctioned grows only slightly (100 to 118 rounds per run), because the windows overlap.

## Limits

- Raider status is "ever scouted or raided" and swells over the run (by 7,729 sanctioned-raider pair-rounds in the mis arm against 3,846 in base), so G1/G2's raider/innocent split is a weak proxy; a failed G2 does not prove that who is sanctioned makes no difference to cost.
- One cell, N=20, sanction length 25, an unaware mover.
- Pair income categories are fixed at the start of the round.

## What this does to the claim ledger

- **Drop:** "misattribution costs cooperation" and the partner-absorbs-the-loss account.
- **Keep, with the number:** broad collective punishment costs about 0.05 pd_mean per agent-round (about 2.6%) in this cell, mainly via additional sanctioned time at roughly 1.5 per round.
- **Keep, narrower:** misattribution transfers the sanction burden from movers to bystanders without reducing total sanctioned time, and in this cell it did not reduce cooperation income.
- **Open:** why misattribution raises welfare by +0.05 when the cost arithmetic predicts about 0.

## Next

A 60-seed run in a second cell (for instance lead 1.1, c_seize 0.05, where raids are more common) would test whether the +0.05 holds. One-line pre-registration first. Otherwise pass 11.

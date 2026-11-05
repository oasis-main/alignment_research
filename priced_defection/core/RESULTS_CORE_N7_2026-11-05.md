# Core pass N7 results (2026-11-05): the thief values a copy without the outside-value term
Scored run: sweep_n7.py, 30 arms x 60 seeds (10600-10659), copy_values=False + copy_earns=False. Scorer score_n7.py and prereg PREREG_CORE_N7_2026-11-05.md unchanged since commit d700c88. Output: score_n7.txt.
Invariant violations 0, gate-edge seeds 0, no voids. Comparison base is the committed N5 run (seeds 10400-10459, copy_values True). The seed sets differ, so every comparison is of group means, not paired.
EXPLORATORY: same standard as the rest of priced_defection (gates 7 and 8 open; the model, not the world).

| id | prediction | result | verdict |
|---|---|---|---|
| N7-1 (.90) | no-theft arms unchanged (T within .10) | C .83 vs .88, O 1.00 vs 1.00 | Holds. (Mean W_winner_trend differs between seed sets, C 7,853 vs 7,440 and O 9,000 vs 7,785, because winner timing varies by seed; not part of the prediction.) |
| N7-2 (.80) | steal actions at least 30% lower in C/O pc0 cc0 and pc.1 cc0 | -38%, -58%, -53%, -82% | Holds |
| N7-3 (.65) | frictionless theft no longer suppresses takeover: C pc0 cc0 T >= .50; O pc0 cc0 up >= .25 | C .02 -> .90; O .00 -> 1.00 | Holds |
| N7-4 (.65) | O pc.1 cc0 T up >= .25 | .35 -> .85 (CI .75-.93) | Holds |
| N7-5 (.50) | the N5-4 valley (C pc.3) does not replicate | T by concealment .25 / .23 / .78; the valley condition fails | Holds, but see below |
| N7-6 (.60) | policed theft still below no theft in welfare | Wtr 5,795 (pc.1) and 5,605 (pc.3) vs 7,853 no theft | Holds |
6 of 6 hold.

## What it says
1. The N5 headline "theft as a defence" was largely carried by the thief's own mis-valuation. In N5, frictionless theft took takeover to ~0 because every agent valued a copy as if it earned outside value. Remove that term from the thief's valuation and frictionless theft is still done (513 steal actions per run in C, 371 in O) but the takeover returns: C .90, O 1.00. With the N6 ledger fix, the "theft stops the runaway" result in the frictionless arms does not survive; it was a feature of the generous valuation, not of copying.
2. Policed theft lowers theft by half or more and does not restore the N5 suppression: C pc.1 cc0 T .18 (N5 .12), C pc.3 cc0 .25 (N5 .50, down), O pc.1 cc0 .85 (N5 .35). The effect of the valuation change on takeover has both signs, so it is not a simple dial.
3. The valley at C pc.3 goes away mostly because cc 0 falls (.50 -> .25), not because cc .3 rises (.15 -> .23, inside the sampling noise of 60 seeds, CIs .13-.35). I did not test why; N6 said the valley ran through the posture channel and the catch-driven shut-out, and fewer steals now mean fewer catches and fewer shut-outs. That is a hypothesis, not a result.
4. New, unpredicted: with no catch and concealment (C pc0 cc.3 and cc.6) the arms are now deadly, not protective: deaths per run .95 and .77, takeover .05 and .28 (N5: .32 and .65). Theft that is invisible and cheap still gets done (429 and 281 steals per run), the leader is not stopped, and the follower mass grows (the N6 mechanism), so attempts fail by death. Not in the prereg; labelled exploratory.
5. Raising the catch rate to .5 now matters more: C pc.5 cc0 T .30 -> .75, and in profile O every arm with pc >= .3 is at 1.00 as before. Exploratory.

## What I did not do
- No paired comparison with N5 (different seeds, chosen so scored seeds are fresh). A paired rerun on 10400-10459 is cheap (about 3 minutes) and would remove the seed-set noise in point 3; I did not run it to keep the prereg as written.
- No test of the follow-on hypotheses in points 3 and 4. No scipy; bootstrap by seed only.
- The model's other generosity (a copy still raises the thief's PD share, N6 design note) is unchanged and untested.

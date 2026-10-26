# Claim cards: Cooperation Under Priced Defection

**Status: EXPLORATORY.** Gates 7 (plain-language read) and 8 (independent check) are open
for every claim below.

- Date: 2026-10-26.
- Prepared by Claude Code from the repo's own files. This is not an independent re-run.
  No simulation was run to make these cards. Every mark cites a file in this repo.
- Standard: `RESEARCH_STANDARD.md` (branch `kolmogorov/research-standard`), eight gates,
  with the "Simulations and models" adaptation.
- Claims: the 10 items in [README "The short version"](README.md#the-short-version), in
  the same order.

Marks: `[x]` = a file in this repo shows the gate was met. `[~]` = partly met (the card says
what is missing). `[ ]` = not met.

## Summary

| # | Claim (short) | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | By construction? | State after the 2026-10-10 posture fix |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | No voluntary defence without a private return | ~ | ~ | ~ |   |   | ~ |   |   | Yes (the zero) | Zero holds; threshold sizes moved |
| 2 | Patience brakes; least patient sets the pace | | ~ | ~ | ~ |   | ~ |   |   | Mostly | Not affected (pass 3) |
| 3 | Detection beats speed; detection floor | | ~ | ~ |   |   | ~ |   |   | Partly | Not affected (passes 1 to 3) |
| 4 | Backups buy time, not safety | ~ | ~ | ~ | ~ |   | ~ |   |   | Mostly | Not affected (passes 4 and 5) |
| 5 | Access to capability decides lock-in | ~ | ~ | ~ | ~ |   | ~ |   |   | Partly | **Takeover half contradicted** |
| 6 | Open sharing is the only lever; clubs cannot start | ~ |   | ~ |   |   | ~ |   |   | Partly | **Contradicted as stated** |
| 7 | Attention is scarcer than money | ~ |   | ~ |   | ~ | ~ |   |   | Partly | Posture crowd-out holds; takeover effect confounded |
| 8 | Bluffing works until tested | ~ |   | ~ |   |   | ~ |   |   | Partly | **Not re-run** |
| 9 | Capital-preserving actor stops near 2 doublings past horizon | ~ | x | ~ | ~ | ~ | ~ |   |   | Mostly (closed form) | Not affected (side probe) |
| 10 | Depth alone does not shut rivals out | ~ | ~ | ~ | ~ | ~ | ~ |   |   | Yes (identity) | Not affected (side probe) |

No claim passes all eight gates. No file shows a reader other than the author or an
independent re-run for any claim.

## Findings that affect several cards

1. **The README's short version predates the posture fix.** The short version was last
   changed in commit `619b013` (2026-10-09 15:57:12 +0000). Commit `65c139c`
   (2026-10-10 03:07:46 +0000) fixed a bug: in passes 6 to 9 a paid defensive posture never
   counted in any response ([FIX_POSTURE_2026-10-09.md](FIX_POSTURE_2026-10-09.md)). The
   commit message says "Write-ups not yet updated". The re-run in `raw_fix/` changes the
   numbers behind claims 5 and 6 (see those cards). The README, `SETUP.md` and the PR #1
   description still give the pre-fix numbers.
2. **A hidden price control.** [PREP_PRICE_FINDING_2026-10-11.md](PREP_PRICE_FINDING_2026-10-11.md)
   shows that the price of preparing a takeover scales with the buyer's own capability, but
   the prize does not. A leader that grows large is priced out of a takeover. The README
   does not mention this. It affects claims 5, 6 and 7.
3. **Pre-registration timing cannot be checked from git for any headline claim.** For passes
   6 to 9 and the side probes, the predictions are in each script's docstring. Each script was
   added in the same commit as its results file. The docstrings have not changed since that
   commit (checked against the first commit of each file). For passes 1 to 5 the hypotheses
   came from Mike's RFC of 2026-10-05, which is not in this repo. The later pre-registration
   files that touch these claims (`FIX_POSTURE`, `PREREG_2X2`, `PREREG_2X2_CPREP`) were also
   committed in the same commit as their results. The core-engine passes N1 to N6 do have a
   pre-registration commit before the results commit, but they test different claims.
4. **Clean-copy reproduction.** The README "Reproducing" section says the selftests, the
   price checks and the five side probes were re-run on 2026-10-09 and that the probes
   matched byte for byte. No output file records that re-run, no tolerance was stated in
   advance, and the author did the re-run. The tournament sweeps that make the headline
   numbers were not re-run from a clean checkout.
5. **Independent check.** Every commit under `priced_defection/` has the author
   "Kolmogorov" or "Kolmogorov (oasis-claw bot)". No file records a non-author re-run of
   gates 3 to 5 or a plain-language read by Mike.

---

## Claim 1: voluntary defence

```
Claim (one sentence, plain words): Nobody pays for a defence (a defensive posture, or open
  sharing of capability) that helps only other players; a small private return changes
  provision from nobody to half or all of the players.
Pre-registration: tournament6.py docstring P1, P2 (commit b929872, 2026-10-08 16:03:34 +0000);
  tournament7.py docstring Q3 (commit e6375e7, 2026-10-08 17:17:43 +0000);
  FIX_POSTURE_2026-10-09.md F1 (commit 65c139c, 2026-10-10 03:07:46 +0000).
  Each was committed in the same commit as its results, so git cannot show that it came first.
1 Pre-registered ............ [~] tournament6.py, tournament7.py, FIX_POSTURE_2026-10-09.md
  Missing: a commit before the results commit. P1 second half failed (RESULTS_V6 section on P1).
2 Score dependence written .. [~] AUDIT_OVERENGINEERING_2026-10-20.md section 2;
  tournament6.py lines 40-48 and 305-318; tournament7.py lines 316-321
  inputs it actually depends on: value of post = (post_shield x (1 + threat) - c_def) x R x cap;
  value of public share = (rep_value - c_share) x R x cap; idle = 0 (tournament6.py line 297);
  an action with value <= 0 is never taken (tournament6.py line 353). At post_shield = 0 or
  rep_value = 0 the value is negative, so provision is zero by the rule. Gate 2's stop
  condition applies: the claimed result is the sign of one inequality.
  Missing: the sharing form is written only as a code comment.
3 Scramble / controls ....... [~] raw/sweep_v6_A.txt; raw_fix/log_v6_A.txt; raw/sweep_v7_H.txt
  result: the claimed input (private return) was varied: post_shield 0, 0.05, 0.1, 0.2, 0.4,
  0.8 and rep_value 0, 0.1, 0.3, 0.6. Zero at 0 in both. No planted-effect or null-data control.
4 Dumbest baseline .......... [ ] none run
  baseline = the analytic prediction from the valuation above (zero provision when the private
  return is 0; posting with no threat needs post_shield > c_def = 0.15; public sharing needs
  rep_value > c_share = 0.20), method - baseline = 0 at the zero point. Observed values agree
  with the inequality: rep_value 0.1 -> 0 shares, 0.3 -> 303.9 (raw/sweep_v7_H.txt);
  post_shield 0.2 -> 20 of 20 posters (raw/sweep_v6_A.txt). These baseline numbers are
  Claude Code's arithmetic from the code, not a run by the author.
5 Clean-copy reproduction ... [ ] no record   tolerance: not stated, observed: not recorded
6 Anomalies and audits ...... [~] (a) Posture timing bug (FIX_POSTURE_2026-10-09.md). After the
  fix, the zero at post_shield 0 holds (raw_fix/log_v6_A.txt: post 0.000, 0.0 posters), but
  post_shield 0.05 moves from 0.059 share and 9.1 posters to 0.636 and 13.2. (b) The author's
  own docstring calls the posture "a PURE PUBLIC GOOD by construction" (tournament6.py line 47),
  but the README presents the zero as the most robust empirical result. Not resolved.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: an agent that chooses a posture or a public share with a value <= 0
  (this would be a code bug); or, outside the model, a real case of sustained costly collective
  defence with no private return (README "What would change our minds").
Where it is published (every location): README.md#the-short-version item 1;
  README.md#who-decides-what (consequence 1 and 2);
  README.md#pass-6-roles-become-choices-and-everything-has-a-price finding 1;
  README.md#pass-7-one-currency-uneven-prices-sharing-and-bluffing finding 3;
  README.md#what-would-change-our-minds ("On voluntary defence"); RESULTS_V6_2026-10-08.md;
  RESULTS_V7_2026-10-08.md; PR #1 description, "Preliminary findings" item 1 and
  "Interpretation" bullet 1.
By construction or discovered: By construction for the zero. The agent values an action only
  by its private return, so an action with no private return and a positive price is never
  chosen. Discovered: how many agents post above the threshold.
Assumption sweep / where it flips: post_shield 0 to 0.8 and rep_value 0 to 0.6 were swept.
  Provision starts where post_shield x (1 + threat) > c_def (0.15) and where rep_value >
  c_share (0.20). The result flips only if the valuation counts a benefit to others, which
  the code never does.
```

## Claim 2: patience

```
Claim (one sentence, plain words): Patient movers grab less often than impatient movers, and
  in a mixed group the least patient mover sets the takeover rate.
Pre-registration: none in this repo. RESULTS_PRELIM_2026-10-06.md cites hypothesis H2 from
  Mike's RFC of 2026-10-05; the RFC is not in this repo. Results commit 58d3f4d,
  2026-10-06 20:58:23 +0000. The "least patient sets the pace" part was found after the run
  (RESULTS_V3_2026-10-06.md section 6).
1 Pre-registered ............ [ ] none in repo
2 Score dependence written .. [~] RESULTS_PRELIM_2026-10-06.md section 0.3
  inputs it actually depends on: the EV mover grabs when p > (L + V) / (G + L); patience (delta)
  enters only through the continuation value V. Missing: no simplified form of the success
  rate; no statement of how the 4-mover success rate combines the movers.
3 Scramble / controls ....... [~] RESULTS_PRELIM_2026-10-06.md section 1 (H2) and section 0.3;
  RESULTS_V3_2026-10-06.md section 6
  result: delta swept 0.5 to 0.999 (single mover: 0.52 -> 0.12). The threshold-rule arm is
  flat in delta, which works as an accidental negative control. No planted-effect control.
4 Dumbest baseline .......... [~] RESULTS_V3_2026-10-06.md section 6 (values); README
  "Passes 1 to 3: what is concerning" item 6 (the "midway" comparison, in words only)
  baseline = linear mix of the pure populations, (0.90 + 0.38) / 2 = 0.64,
  method - baseline = 0.68 - 0.64 = +0.04; the mixed interval [0.53, 0.82] contains 0.64.
  The data do not separate "least patient sets the pace" from "the average". This arithmetic
  is Claude Code's; no baseline was run for the patience effect itself.
5 Clean-copy reproduction ... [ ] no record   tolerance: not stated, observed: not recorded
6 Anomalies and audits ...... [~] (a) The first sweep used the threshold rule, which ignores
  delta, and gave flat lines; resolved by using the EV arm (RESULTS_PRELIM section 0.3).
  (b) The 4-mover patience contrast exists only under mover_resist = "none"; under "full" and
  "idle" every population gives 0.00 (RESULTS_V3 sections 1 and 6). (c) In the same table,
  a threshold of 0.9 (0.07) and log utility (0.10) restrain more than patience (0.38), so
  "most reliable" means "most stable across fixes", not "strongest". Open.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: a mixed population whose success rate is at or below the midpoint of
  the pure populations with a separated interval; a patient population that grabs as often
  as an impatient one under the EV rule.
Where it is published (every location): README.md#the-short-version item 2;
  README.md#passes-1-to-3-what-is-encouraging finding 1;
  README.md#passes-1-to-3-what-is-concerning item 6; RESULTS_PRELIM_2026-10-06.md;
  RESULTS_V3_2026-10-06.md sections 6 and 8; PR #1 description item 2.
By construction or discovered: The direction is by construction: delta raises V, and V raises
  the bar p must clear (README: "The mechanism is the obvious one"). "The least patient sets
  the pace" is close to by construction, because the first successful grab by any mover ends
  the game for all. The size of the effect is discovered.
Assumption sweep / where it flips: delta 0.5 to 0.999 swept (sharp fall above 0.95). Flips
  to no effect under the threshold decision rule (RESULTS_PRELIM section 0.3). Not observable
  when rival movers resist each other (mover_resist "full" or "idle": 0.00 for all).
```

## Claim 3: detection and speed

```
Claim (one sentence, plain words): Seeing a takeover coming matters much more than reacting
  fast, and below a detection floor no countervailing capability deters a takeover.
Pre-registration: none in this repo. RESULTS_PRELIM_2026-10-06.md cites H7 from Mike's RFC
  (2026-10-05), not in this repo. The floor was found after the run (RESULTS_V3 section 7b).
  Results commit 58d3f4d, 2026-10-06 20:58:23 +0000.
1 Pre-registered ............ [ ] none in repo
2 Score dependence written .. [~] RESULTS_PRELIM_2026-10-06.md section 0.2
  inputs it actually depends on: detectors from rounds 1..tau count, and the response lands
  only if tau < kappa. By this definition speed acts only as a cliff at tau/kappa = 1, and only
  agents that detected the grab respond. Missing: a simplified form of the success rate.
3 Scramble / controls ....... [~] RESULTS_PRELIM section 1 (d x tau/kappa cross);
  raw/probe_margin.txt; raw/probe_jitter.txt
  result: d swept 0.05 to 1.0 (success 1.00, 1.00, 0.55, 0.02); at d = 0.05 every tau/kappa
  gives 1.00. No planted-effect or null-data control.
4 Dumbest baseline .......... [ ] none run
  baseline = not computed (an analytic detection probability 1 - (1 - d)^k was not compared),
  method - baseline = not available
5 Clean-copy reproduction ... [ ] no record   tolerance: not stated, observed: not recorded
6 Anomalies and audits ...... [~] (a) The meaning of tau (mobilisation latency or deadline) is
  unresolved; the sign of the speed effect depends on it (RESULTS_PRELIM section 0.2; README
  concern 8, "Open"). (b) raw/probe_margin.txt has no point between p_det 0.360 and 0.750, so
  the floor is somewhere in that range, not "roughly 0.36". (c) At p_det 0.360 a rival of 1.5x
  lowers success from 1.00 to 0.60, so capability does deter partly below the floor, and ratios
  above 1.5 were not tested. Points (b) and (c) are not in the README. Open.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: a cell with low detection where a rival covering the mover's +2 sigma
  quantile drives success to <= 0.05; a finer d grid that puts the floor far from 0.36; the
  other tau reading reversing the detection-over-speed order.
Where it is published (every location): README.md#the-short-version item 3;
  README.md#passes-1-to-3-what-is-encouraging findings 2 and 3; README.md#what-would-change-our-minds
  ("On monitoring"); RESULTS_PRELIM_2026-10-06.md; RESULTS_V3_2026-10-06.md section 7b;
  PR #1 description item 3 and "Interpretation" bullet 2.
By construction or discovered: Partly by construction: only detectors respond, so with no
  detection nothing responds; speed is a cliff because of the author's chosen tau definition.
  Discovered: where the floor lies and that the needed margin stops changing above it.
Assumption sweep / where it flips: d 0.05 to 1.0, tau/kappa 0.25 to >= 1, rival ratio 0.8 to
  1.5, jitter sigma 0 to 0.4. Flips: under the other tau reading the speed gradient may change
  sign (open). The floor is not bracketed more finely than p_det 0.36 to 0.75.
```

## Claim 4: backups

```
Claim (one sentence, plain words): Backups delay the end of the game but do not prevent it
  when a lead compounds; each doubling of backup hardness adds a fixed number of rounds.
Pre-registration: the formula rounds = ln(K / lead0) / ln(1 + gamma) is in
  RESULTS_V4_2026-10-07.md (commit caf4cc5, 2026-10-07 16:23:41 +0000), written after the pass-4
  run in the same commit. Pass 5 (commit 0235433, 2026-10-07 20:28:21 +0000) used it to predict
  the pooled-backup delay; the 47.7-round figure was not committed before that run.
1 Pre-registered ............ [~] RESULTS_V4_2026-10-07.md section 3; RESULTS_V5_2026-10-07.md
  section 6. Missing: a prediction committed before the scored run.
2 Score dependence written .. [~] RESULTS_V4_2026-10-07.md section 3
  inputs it actually depends on: backup hardness K, starting lead lead0, lead growth gamma
  (and gain per raid win_boost). Stated as a fit ("within about four rounds"), not derived.
3 Scramble / controls ....... [~] RESULTS_V4 sections 1 and 3; RESULTS_V5 sections 1 and 6
  result: gamma = 0 never ends and win_boost = 0 never ends (negative controls); K = 2 vs 4
  and gamma 0.01 to 0.05 follow the formula. No shuffled-input run.
4 Dumbest baseline .......... [~] RESULTS_V4 section 3; RESULTS_V5 section 6
  baseline = the closed form ln(K / lead0) / ln(1 + gamma), method - baseline = +0.9 to about
  +4 rounds (pooled backups 48.6 vs 47.7; other cells within about 4 rounds). The simulation
  adds only the preparation and execution delay.
5 Clean-copy reproduction ... [ ] no record   tolerance: not stated, observed: not recorded
  (the tournament5 selftest reproduces pass 4 with features off; that is a regression check)
6 Anomalies and audits ...... [~] (a) The first pass-5 run mixed growth with raiding; re-run
  as separate grids A1 and A2 (corrections ledger row 3; RESULTS_V5 header). Resolved.
  (b) g_def and gamma are not read in the v6+ run loops (commit 726bd5f;
  AUDIT_OVERENGINEERING_2026-10-20.md section 3); pass 4 and 5 cells are not affected.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: a cell with gamma > 0 (or win_boost > 0), no defender growth, and a
  finite K in which the game does not end; a time to end that departs from the formula by
  much more than the preparation time.
Where it is published (every location): README.md#the-short-version item 4;
  README.md#pass-4-what-if-failure-is-survivable-backups findings 1 to 4;
  README.md#pass-5-defenders-who-act-catch-up-counter-raids-coalitions-recon finding 5;
  RESULTS_V4_2026-10-07.md; RESULTS_V5_2026-10-07.md; PR #1 description item 4.
By construction or discovered: Mostly by construction. With a lead that grows by a fixed rate
  and a fixed bar K, the crossing time is the arithmetic of exponential growth; RESULTS_V4
  section 1 says "Part of this holds by construction". Discovered: a raiding regime fills the
  gap below K, and any gain per raid makes the end certain.
Assumption sweep / where it flips: gamma 0, 0.01, 0.02, 0.05; K 1 to 15; win_boost 0, 0.1,
  0.3; defender growth g_def 0 to 0.08. Flips: with gamma = 0 and win_boost = 0, backups
  harder than the lead hold indefinitely (RESULTS_V4 section 3); with g_def >= gamma the order
  holds (RESULTS_V5 section 1).
```

## Claim 5: access to capability and lock-in

```
Claim (one sentence, plain words): Whether everyone can buy capability decides whether a lead
  locks in: expensive or gated capability turns a 3x lead into a takeover in 90 to 100% of
  runs, cheap open capability erodes the lead, and a leader's discount barely matters.
Pre-registration: tournament6.py P3 (b929872, 2026-10-08 16:03:34 +0000); tournament7.py Q2
  (e6375e7, 2026-10-08 17:17:43 +0000); tournament8.py S2 (d08bdaf, 2026-10-08 17:50:01 +0000);
  FIX_POSTURE_2026-10-09.md F2 to F4 (65c139c, 2026-10-10 03:07:46 +0000);
  PREREG_2X2_CPREP_2026-10-14.md C1, C4 (a41dad3, 2026-10-14 19:24:53 +0000).
  Each is in the same commit as its results.
1 Pre-registered ............ [~] files above. Missing: a commit before the results commit.
2 Score dependence written .. [~] AUDIT_INCOME_PD_POOLING_2026-10-20.md sections 3-4;
  AUDIT_OVERENGINEERING_2026-10-20.md section 1; PREP_PRICE_FINDING_2026-10-11.md finding 1
  inputs it actually depends on: whether laggards grow is a break-even in c_grow (value of
  growth 0.75 cap vs price 3 c_grow cap, break-even 0.25); the value of capability is 98.7%
  the flat income term; whether the leader can attack depends on c_prep x R x own capability
  against lambda x the others' capability. Missing: written post hoc for cell Q, not for the
  pass 6 to 8 cells.
3 Scramble / controls ....... [~] raw/sweep_v6_C.txt; raw/sweep_v8_K.txt; raw_fix/log_v6_C.txt;
  raw_fix/log_v8_K.txt; PREP_PRICE_FINDING_2026-10-11.md; RESULTS_2X2_CPREP_2026-10-14.md
  result: price, discount, gate threshold and gate penalty were swept. The posture fix and the
  c_prep sweep act as controls, and both change the takeover result (row 6).
4 Dumbest baseline .......... [~] AUDIT_INCOME_PD_POOLING_2026-10-20.md section 4
  baseline = arithmetic growth break-even c_grow = 0.25, method - baseline = growth collapses
  between c_grow 0.20 and 0.24 (post hoc, cell Q, 10 seeds). Not run for the pass 6 to 8 cells.
5 Clean-copy reproduction ... [ ] no record   tolerance: not stated, observed: not recorded
6 Anomalies and audits ...... [~] (a) Posture timing bug. After the fix (raw_fix/), dear
  capability at a 3x lead gives takeover 0.00, not 1.00 (log_v6_C.txt C2_lead3.0_cg0.6);
  the hard gate with cheap capability gives 0.00, not 0.90 (log_v8_K.txt K2_step_th0.8_cg0.1).
  (b) After the fix, cheap open capability no longer erodes the lead: 3.00 -> 6.38
  (log_v8_K.txt K1_smooth_ps0_cg0.1; pre-fix 1.37) and 3.00 -> 3.02 (log_v6_C.txt
  C2_lead3.0_cg0.1; pre-fix 1.57). (c) The leader is priced out of a takeover by its own size
  (PREP_PRICE_FINDING). At c_prep 0.05 the gate with cheap capability gives 1.00 again, and
  the gate with dear capability gives 0.00 (RESULTS_2X2_CPREP). (d) 7 of the 14 post-fix cells in
  raw_fix/log_v8_K.txt, with different settings, end at the same lead 57.66; open flag in
  PREREG_2X2_2026-10-10.md ("the identical 57.66 lead"). None of (a) to (d) is in the
  README. Open.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: with the posture fix on, a gated or dear-capability 3x-lead cell whose
  takeover rate stays near 0 at every c_prep value (this already holds at c_prep 0.5); a
  gated field where the lead still erodes (README "On access").
Where it is published (every location): README.md#the-short-version item 5;
  README.md#pass-6-roles-become-choices-and-everything-has-a-price finding 3;
  README.md#pass-7-one-currency-uneven-prices-sharing-and-bluffing finding 2;
  README.md#pass-8-a-hard-gate-is-different-from-a-discount finding 2;
  README.md#what-would-change-our-minds ("On access"); SETUP.md "An example cell" (90%
  takeover, lead 3.00 -> 3.87, 1.37 without the gate); RESULTS_V6, V7, V8; PR #1 description
  items 5 and 6 and "Interpretation" bullet 3.
By construction or discovered: Partly by construction. Whether laggards buy capability is a
  price break-even of the flat income rule. Under a gate the laggard price is x1e6, so the
  field cannot grow. Discovered: the size of the lead and the takeover rate, but the takeover
  rate depends on posture_fix and c_prep.
Assumption sweep / where it flips: c_grow 0.1 to 1.2; price_scale 0 to 1; gate threshold 0.5
  to 0.95; gate penalty 2 to 1e6; c_prep 0.5, 0.05, 0.005; frontier max or sum; posture_fix
  off or on. Flips: posture_fix on at c_prep 0.5 -> takeover 0.00 to 0.07 in the dear and gate
  cells; frontier sum -> 0.00 in every cell (PREREG_2X2 table). The lock-in of the lead under
  a gate holds in every version (post-fix lead 3.00 -> 57.66). The takeover half of the claim
  holds only at the pre-fix code, or at c_prep 0.05 with the max frontier and cheap capability.
```

## Claim 6: open sharing

```
Claim (one sentence, plain words): Open sharing of capability is the only lever found that
  turns a certain takeover into none, also through a hard gate, but only if sharing earns
  reputation; a trust-gated club cannot start itself.
Pre-registration: tournament7.py Q3, Q4 (e6375e7, 2026-10-08 17:17:43 +0000); tournament8.py
  S4 (d08bdaf, 2026-10-08 17:50:01 +0000); PREREG_2X2_2026-10-10.md H5 (5b28dd1,
  2026-10-11 00:41:57 +0000; scored in the same file and commit); PREREG_2X2_CPREP_2026-10-14.md
  C3 (a41dad3, 2026-10-14 19:24:53 +0000). Each is in the same commit as its results.
1 Pre-registered ............ [~] files above. Missing: a commit before the results commit.
  S4 failed in half the space; H5 FALSE; C3 MOSTLY FALSE.
2 Score dependence written .. [ ] only as code: tournament7.py lines 305-321
  inputs it actually depends on: public share value = (rep_value - c_share) x R x cap; club
  share value = value of what current club members share back, which is 0 when the club is
  empty. No written form of how sharing changes the takeover rate.
3 Scramble / controls ....... [~] raw/sweep_v7_H.txt; raw/sweep_v7_I.txt; raw/sweep_v8_M.txt;
  raw_fix/log_v7_I.txt; raw_fix/log_v8_M.txt; PREREG_2X2_2026-10-10.md
  result: rep_value, scope (club or public), capability price, sharing efficiency, frontier
  and response rule were varied. No planted-effect control.
4 Dumbest baseline .......... [ ] none run
  baseline = analytic: public sharing is chosen when rep_value > c_share = 0.20,
  method - baseline = 0 (rep_value 0.1 -> 0 shares, 0.3 -> 303.9; raw/sweep_v7_H.txt).
  Claude Code's arithmetic, not a run by the author.
5 Clean-copy reproduction ... [ ] no record   tolerance: not stated, observed: not recorded
6 Anomalies and audits ...... [~] (a) Pre-fix, cheap capability behind a gate: sharing raised
  takeover 0.90 -> 1.00 (RESULTS_V8 S4; explained in pass 9). (b) Post-fix there is no
  certain takeover to stop: dear capability behind a gate, no sharing, gives 0.07
  (raw_fix/log_v8_M.txt M_gate_noshare_cg0.6); with cheap capability behind a gate, public
  sharing raises takeover 0.00 -> 1.00 (M_gate_public_cg0.1). (c) At c_prep 0.05, sharing
  raises takeover 0.00 -> 0.30 [0.10, 0.50] in paid/max/dear (RESULTS_2X2_CPREP C3).
  (d) "Only lever" conflicts with the README itself: defender growth parity takes 1.00 to
  0.00 (RESULTS_V5 section 1: gamma 0.02, g_def 0 -> 1.00, g_def 0.02 -> 0.00), and a rival of
  1.5x under max takes 1.00 to 0.00 (RESULTS_V3 section 7a). Core pass N3 also finds theft
  at 0.50 takes 1.00 to 0 (core/RESULTS_CORE_N3_2026-10-21.md). Open.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: with the posture fix on, a cell with a certain takeover (>= 0.9) that
  public sharing does not reduce to near 0; any other lever that takes a certain takeover to
  none (already found, see row 6 (d)).
Where it is published (every location): README.md#the-short-version item 6;
  README.md#pass-7-one-currency-uneven-prices-sharing-and-bluffing findings 3 and 4 ("the only
  intervention in the study that takes a certain takeover to none");
  README.md#pass-8-a-hard-gate-is-different-from-a-discount finding 4;
  README.md#status item 6; RESULTS_V7, RESULTS_V8; PR #1 description items 7 and 8 and
  "Interpretation" bullet 3.
By construction or discovered: "A club cannot start itself" is by construction: an empty club
  gives a club-share value of 0 (tournament7.py lines 309-314). "Only if it earns reputation"
  is by construction: public sharing has no private term except rep_value (lines 318-320).
  Discovered: how much sharing compresses the lead (pre-fix 3.00 -> 1.21; post-fix 12.96 ->
  1.05, raw_fix/log_v7_I.txt I2).
Assumption sweep / where it flips: rep_value 0 to 0.6; c_grow 0.1 or 0.6; gate on or off;
  c_prep 0.5 or 0.05; frontier max or sum; posture_fix off or on. Flips: posture_fix on removes
  the certain-takeover baseline; cheap capability behind a gate makes sharing harmful.
  Related evidence: core passes N1 and N3 (pre-registered, separate commits fc5b42f ->
  1b48083 and feb6399 -> d298837) find open diffusion removes takeover, but there every
  capability is published and sharing is not a chosen, reputation-paid action
  (core/RESULTS_CORE_N1_2026-10-20.md, item 1), so they do not test this claim as stated.
```

## Claim 7: attention

```
Claim (one sentence, plain words): With one action per round, a sharing programme takes the
  turns that defence needs, and giving sharing its own budget does not help.
Pre-registration: tournament9.py T1 (19b9fe8, 2026-10-08 18:45:51 +0000) predicted a budget
  mechanism and FAILED; the attention mechanism was found after the run.
  FIX_POSTURE_2026-10-09.md F5 (65c139c, 2026-10-10 03:07:46 +0000) predicted a larger effect
  after the fix; it held. Both are in the same commit as their results.
1 Pre-registered ............ [~] tournament9.py, FIX_POSTURE_2026-10-09.md. Missing: the
  attention mechanism itself was never pre-registered; no commit before the results.
2 Score dependence written .. [ ] not written
  inputs it actually depends on: not written out. The one-action rule is stated in README
  "Who decides what"; c_prep x own capability also sets whether the leader attacks
  (PREP_PRICE_FINDING_2026-10-11.md).
3 Scramble / controls ....... [~] probe_slot_control.py; raw/probe_slot_control.txt;
  raw/sweep_v9_N.txt; raw/sweep_v9_O.txt; raw_fix/log_v9_N.txt; raw_fix/log_v9_O.txt
  result: sharing priced out of reach reproduces the no-sharing cell exactly; a separate
  purse does not restore posting; the sum frontier removes the effect. Post-fix: no sharing
  0.00 (posting 0.907), shared purse 1.00 (0.000), separate purse 0.93 (0.060).
4 Dumbest baseline .......... [ ] none run   baseline = none, method - baseline = not available
5 Clean-copy reproduction ... [~] raw/probe_slot_control.txt ("priced-out reproduces
  no-sharing exactly: True"; re-run 2026-10-09 per corrections ledger row 11)
  tolerance: not stated in advance, observed: exact match for the no-sharing cell only;
  same author.
6 Anomalies and audits ...... [~] (a) Pass 8's explanation and the first probe were wrong
  (ledger row 7). (b) The priced-out row first came from an unsaved probe (ledger row 11,
  RESULTS_V9 erratum); resolved. (c) PREP_PRICE_FINDING: the no-sharing zero in the cheap
  gated cell is "priced out, not deterred"; at c_prep 0.05, no sharing and sharing both give
  1.00 (RESULTS_2X2_CPREP). So the takeover effect may come from sharing keeping the leader
  small enough to afford a takeover, not from lost defence. (d) Post-fix endowment row is
  non-monotone: 0.97, 0.37, 0.93 (raw_fix/log_v9_N.txt N3). (e) The ring-fence selftest margin
  is +0.007 on 8 seeds (SEIZE_DIAGNOSIS_2026-10-11.md). (c) and (d) are open.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: posting share that does not fall when sharing is available; a run
  with more than one action per round in which the crowd-out remains; a c_prep sweep showing
  the takeover difference is a prep-price effect only.
Where it is published (every location): README.md#the-short-version item 7;
  README.md#pass-9-attention-not-money-and-paying-to-call-a-bluff finding 1;
  README.md#what-would-change-our-minds ("On attention"); README.md#limits-read-this-before-citing-anything;
  README.md#status item 1; RESULTS_V9_2026-10-08.md; PR #1 description item 9 and
  "Interpretation" bullet 4.
By construction or discovered: Partly by construction: one action per round is imposed, so
  any round spent sharing is a round not posting. Discovered: that agents prefer sharing to
  posting in this cell, and the takeover rise that follows (confounded by c_prep).
Assumption sweep / where it flips: share budget shared or separate; endowment 0.05 to 0.5;
  frontier max or sum; c_grow 0.1 or 0.6; c_prep 0.5 or 0.05. Flips: sum frontier -> 0.00 with
  or without sharing; dear capability -> sharing lowers takeover (post-fix 0.07 -> 0.00);
  c_prep 0.05 -> no difference (1.00 vs 1.00). The number of actions per round was never varied.
```

## Claim 8: bluffing and verification

```
Claim (one sentence, plain words): A bluff deters until someone tests it, and verification as
  built here is accurate but duplicated and does not stop bluffing.
Pre-registration: tournament7.py Q5 (e6375e7, 2026-10-08 17:17:43 +0000); tournament8.py S3
  (d08bdaf, 2026-10-08 17:50:01 +0000); tournament9.py T3, T4, T5 (19b9fe8,
  2026-10-08 18:45:51 +0000). Each is in the same commit as its results.
1 Pre-registered ............ [~] files above. Missing: a commit before the results commit.
  T3 withdrawn, T4 failed, T5 held.
2 Score dependence written .. [ ] not written
  inputs it actually depends on: not written out. RESULTS_V8 S3 says decisions run on apparent
  capability; RESULTS_V9 T4 says the penalty for exposure is flat and decays.
3 Scramble / controls ....... [~] RESULTS_V8_2026-10-08.md S3; RESULTS_V9_2026-10-08.md T3-T5;
  raw/sweep_v8_L.txt; raw/sweep_v9_Q.txt; raw/sweep_v9_S.txt
  result: no-bluff cell vs bluff cells; call_bounty 0 to 0.6; inspection lag 1 to 8; caller
  priors 0.1 to 0.9. In the bluff cells with and without verification, bluff share stays
  0.815 to 0.832. No planted-effect control.
4 Dumbest baseline .......... [ ] none run   baseline = none, method - baseline = not available
5 Clean-copy reproduction ... [ ] no record   tolerance: not stated, observed: not recorded
6 Anomalies and audits ...... [~] (a) Pass 7 bluff mispriced about 20x (ledger row 5); fixed.
  (b) Call precision scoring bug, 0.08 -> 1.00 (ledger row 8); fixed. (c) Public-good test of
  calling withdrawn (ledger row 9). (d) Precision 0.33 at inspection lag 4, "declared, not
  swept" (RESULTS_V9 T5). (e) The bluff blocks (v8 L, v9 Q and S) were not in the posture-fix
  re-run list (FIX_POSTURE_2026-10-09.md "Re-run"), so every bluff number is pre-fix. (f) The
  deterrence result is takeover 0.07 -> 0.00 at 30 seeds, inside the +/-0.13 to 0.15 interval
  width the README gives. (d), (e), (f) are open.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: after the posture fix, a bluff cell with a takeover rate not lower
  than the no-bluff cell; a verification rule that lowers bluff share when exposure penalties
  do not escalate.
Where it is published (every location): README.md#the-short-version item 8;
  README.md#pass-8-a-hard-gate-is-different-from-a-discount finding 3;
  README.md#pass-9-attention-not-money-and-paying-to-call-a-bluff findings 2 and 3;
  README.md#status item 4; RESULTS_V8, RESULTS_V9; PR #1 description item 10 and
  "Interpretation" bullet 5.
By construction or discovered: Partly by construction. Decisions read apparent capability, so
  an untested bluff works like real strength. The flat exposure penalty makes a bluff cheap
  to buy again. Every caller tests "the most visible claim" (SETUP.md action table), so
  duplication follows from the target rule. Discovered: the bluff share (about 81%) and the
  size of the duplication (about 6.4 calls per round).
Assumption sweep / where it flips: c_bluff, bluff_mult, bluff_len, call_bounty, c_call,
  pi_call, caller prior. Flips: against a real 3x lead the takeover is 1.00 with or without
  bluffing (RESULTS_V8 S3). A penalty that grows with repeated exposure is not implemented.
```

## Claim 9: depth bound for a capital-preserving actor

```
Claim (one sentence, plain words): For capability that doubles on a schedule, an actor that
  maximises the log of its wealth attempts at most about 2 doublings past its own 50% horizon,
  however big the prize; with no rival it waits until a task is easy, and one rival pulls it
  out toward the edge of its ability and costs reliability.
Pre-registration: probe_depth_bound.py docstring R1, R4 ("written before any run; do not edit
  after"; commit 62c18d8, 2026-10-08 20:17:18 +0000, same commit as
  RESULTS_DEPTH_BOUND_2026-10-08.md); probe_race2.py docstring M3 (8c736b4,
  2026-10-08 21:24:16 +0000, same commit as RESULTS_RACE_2026-10-08.md). Docstrings unchanged since.
1 Pre-registered ............ [~] probe_depth_bound.py, probe_race2.py. Missing: a commit
  before the results commit.
2 Score dependence written .. [x] probe_depth_bound.py docstring R1
  inputs it actually depends on: G = p ln(1 + f(M - 1)) + (1 - p) ln(1 - f), p = sigma(-beta d),
  M = M0 g^d; d* = 1/beta - (ln M0 - 1)/L with L = ln(g / e^beta), so d* -> 1/beta as g grows.
  The prize enters only through a term that vanishes. The bound depends on beta.
3 Scramble / controls ....... [~] RESULTS_DEPTH_BOUND_2026-10-08.md scorecard; raw/probe_depth_bound.json
  result: risk-neutral agent runs away (R0, negative control); every optimum checked at dmax
  and 2 dmax (INTERIOR); beta 0.4, 0.591, 1.0. No shuffled-input run.
4 Dumbest baseline .......... [~] RESULTS_DEPTH_BOUND_2026-10-08.md section 1
  baseline = tail algebra d* = 1/beta = 1.69 doublings at beta 0.591,
  method - baseline = 2.19 to 2.22 - 1.69 = about +0.5 doublings.
5 Clean-copy reproduction ... [~] README.md#reproducing (side probes re-run 2026-10-09 "byte
  for byte")   tolerance: not stated in advance, observed: no stored record; same author.
  beta = 0.591 is hard-coded (probe_horizon.py line 47); the METR source file
  benchmark_results_1_1.yaml and the inversion are not in this repo.
6 Anomalies and audits ...... [~] Four boundary-artefact bugs of one class (ledger rows 12,
  13; RESULTS_DEPTH_BOUND "Safeguard"); horizon erratum 45% -> 39% (ledger row 14). Resolved
  by the dmax / 2 dmax check. RESULTS_DEPTH_BOUND says R2 to R4 are algebra checks only.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: capital-constrained actors that routinely attempt work far more than
  two doublings past what they do reliably (README "On depth"); a numeric Kelly optimum that
  moves with the prize.
Where it is published (every location): README.md#the-short-version item 9;
  README.md#3-what-stops-an-agent-reaching-for-unlimited-depth;
  README.md#4-the-race-when-rivals-are-real-agents (one rival pulls the leader forward);
  README.md#how-these-feed-the-next-tournament-pass-design-not-yet-built;
  README.md#what-would-change-our-minds ("On depth"); RESULTS_DEPTH_BOUND_2026-10-08.md;
  RESULTS_RACE_2026-10-08.md; PR #1 description items 11 and 12 and "Interpretation" bullet 6.
By construction or discovered: Mostly by construction. The bound and the wait rule are closed
  forms of the assumed logistic success curve and log utility. Substantive: the numeric
  optimum stays interior and saturates (R1a, R1b). The rival effect rests on 3 converged rows
  (race M3).
Assumption sweep / where it flips: beta 0.4 -> 3.2 doublings, 0.591 -> 2.2, 1.0 -> 1.3; prize
  growth g 1e3 to 1e6 (change -0.03); discount r and hazard lambda. Flips: a risk-neutral agent
  has no bound; less utility curvature (outside financing) raises the ceiling; if doubling
  stops, the wait option disappears.
```

## Claim 10: depth and exclusion

```
Claim (one sentence, plain words): When all players improve at the same rate, a deeper task
  only delays the same race and does not shut rivals out; faster growth may shut them out,
  but that is not established.
Pre-registration: probe_race2.py docstring M1, M2 (commit 8c736b4, 2026-10-08 21:24:16 +0000,
  same commit as RESULTS_RACE_2026-10-08.md). Docstring unchanged since.
1 Pre-registered ............ [~] probe_race2.py. Missing: a commit before the results commit.
2 Score dependence written .. [~] probe_race2.py docstring M1
  inputs it actually depends on: depth enters only as a time shift of one doubling time
  (128.7 days) per doubling under equal growth. Stated as a prediction; the payoff is not
  simplified in writing.
3 Scramble / controls ....... [~] RESULTS_RACE_2026-10-08.md; raw/probe_race2.json
  result: shallow tasks give a simultaneous rush (B2, positive check); at least 3 converged
  rows are required for a check; 5 of 15 mixed rows excluded. No shuffled-input run.
4 Dumbest baseline .......... [~] RESULTS_RACE_2026-10-08.md section 3
  baseline = exact translation invariance (same game, shifted 128.7 days per doubling),
  method - baseline = 0 for D = 1, 2, 4 (identical to 3 decimals); D = 0 differs by up to
  0.007 in win share (0.481 vs 0.479; 0.331 vs 0.338).
5 Clean-copy reproduction ... [~] README.md#reproducing (side probes re-run 2026-10-09 "byte
  for byte")   tolerance: not stated in advance, observed: no stored record; same author.
6 Anomalies and audits ...... [~] B4 passed over an empty set (ledger row 15); B1 and B3 void
  from cycling; M2 VOID (2 of 4 rows converged). Two players only, one attempt each.
7 Plain-language read ....... [ ] none
8 Independent check ......... [ ] none
What would falsify it: under equal growth, a deeper task that changes win shares or attempt
  depths (this would show the model is not time-shift invariant, or a code bug).
Where it is published (every location): README.md#the-short-version item 10;
  README.md#4-the-race-when-rivals-are-real-agents; RESULTS_RACE_2026-10-08.md;
  PR #1 description item 13.
By construction or discovered: By construction. With equal exponential growth and exponential
  discounting, a deeper task is the same game moved later in time, so identical rows are the
  expected identity. Nothing beyond the identity is discovered; the faster-growth direction
  is not established (M2 VOID).
Assumption sweep / where it flips: task depth 0 to 4; follower gap 0.5 to 3 doublings; growth
  ratio 1.2 (2 rows converged). Flips: unequal growth (direction only); more than 2 players,
  retries, and other values of r and stake were not tested.
```

## Where these claims are published

The repo `oasis-main/alignment_research` is public. The branch `kolmogorov/priced-defection`
and PR #1 are already visible to anyone. Merging PR #1 to `main` is publication. Every
location is listed on each card. In summary:

- `priced_defection/README.md`: "The short version" items 1 to 10, the pass sections, "What
  would change our minds", "Limits" and "Status".
- `priced_defection/SETUP.md`: "An example cell" (claim 5, pre-fix numbers).
- `priced_defection/RESULTS_*.md`: the per-pass writeups.
- PR #1 description: "Preliminary findings" items 1 to 13 and "Interpretation".

No location outside `priced_defection/` and PR #1 mentions these claims (search of this
worktree on 2026-10-26).

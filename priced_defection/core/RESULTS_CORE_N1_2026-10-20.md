# Core pass N1 results (2026-10-20): the new profile
Prereg `PREREG_CORE_N1_2026-10-20.md` (fc5b42f); sweep `sweep_n1.py` (f1f66c6) committed before launch; engine core.py at 48ee788. 32 arms, 1,920 runs, seeds 10000-10059, paired by seed, bootstrap 5000. Scoring `score_n1.py`, output `score_n1.txt`. Invariant violations 0; gate-edge seeds 0 (no void).

## Main table (takeover; te = defenders answer a detected execution)
| pw | diffusion | pie fixed, te off | pie live, te off | te on (any) |
|---|---|---|---|---|
| 0.5 | 0 | .650 | .633 | .000 (deaths = attempts) |
| 0.5 | .01 / .02 / .05 | .000 / .000 / .000 | .000 / .000 / .000 | .000 |
| 1.0 | 0 | 1.000 | .983 | .000 (deaths 0.96-0.99 x attempts) |
| 1.0 | .01 / .02 / .05 | .533 / .167 / .000 | .600 / .183 / .000 | .000 |
Live pie, no sharing: pie_end .18-.78 (shrinks). Live pie with sharing: 1.17-1.23 (grows).

## Scorecard (scored unchanged)
| id | prediction | result | verdict |
|---|---|---|---|
| N1-1 (0.75) | no defence, fixed pie, no sharing: >= .70 at pw 1, >= .50 at pw .5 | 1.000, .650 | Holds |
| N1-2 (0.70 / 0.60) | diffusion .02 lowers takeover by >= .30 (pw .5) / >= .20 (pw 1) | -0.650 [-0.767,-0.517] / -0.833 [-0.917,-0.733] | Holds / Holds |
| N1-3 (0.60) | non-increasing in diffusion | pw .5: .65,0,0,0; pw 1: 1,.53,.17,0 | Holds |
| N1-4 (0.45) | live pie lowers takeover by > .05 (pw .5, no sharing) | -0.017 [-0.083, 0.033] | **FALSIFIED** |
| N1-5 (0.70) | te on: takeover <= .05 everywhere; deaths >= .9 x attempts at diffusion 0 | max 0.000; ratios 1.00, 1.00, .96, .99 | Holds |
| N1-6 (0.80) | sharing grows the pie (live, d .02 vs 0) | +0.43 to +1.05, all CIs exclude 0 | Holds |

## What it says, and the two things it does NOT say
1. Open sharing removes takeover in this profile, with a dose-response at pw 1. BUT in share_mode "open" every agent's capability is published every round, INCLUDING the would-be mover's, so followers diffuse toward the leader for free. The mover does not choose to share. So this is "a leader that cannot hide its capability cannot keep its lead", close to pass 5's catch-up result in another form. It says nothing yet about a hidden mover, who would not publish. That is the main limit.
2. Defence that answers a detected execution stops every takeover, but by killing the mover: attempts turn into deaths almost one for one. The mover's odds estimate counts only posture already standing; it does not anticipate that detectors will post in response. So the mover is systematically overconfident and attempts suicidal takeovers. This is an artifact of the mover's model, not a defence result.
3. A shrinking pie does not deter takeover (N1-4 falsified). Code reading: the prize, the ruin, the continuation value and the sanction cost are all proportional to the pie, so the pie level largely cancels out of the mover's comparison. The pie changes what is at stake for everyone, not the mover's relative incentive. For the pie to deter, something in the decision must not scale with it (e.g. growth price, or capability's value outside the pie).
4. Exploratory (not scored, n 14-32 per strategy): takeover by the leader's PD strategy, te off, fixed pie, no sharing: alld 1.00, gtft .84, random .86, pavlov .83, tft .79, grim .61. Suggestive that the leader's strategy matters; too small to claim.

## Next (stage 2 prereg must fix 1 and 2 first)
- Sharing as a choice per agent (priced or reputation-rewarded), so a mover can stay hidden; "open" kept only as the everyone-publishes limit.
- Mover aware of response-to-execution (its odds estimate includes detectors who will post when they see it).
- Then: reputation from PD play, partner choice by reputation, response by reputation, ecological selection.

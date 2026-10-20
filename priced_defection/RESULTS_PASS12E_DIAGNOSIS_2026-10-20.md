# Pass 12e diagnosis (2026-10-20): the g_def "knife-edge" is the step-access gate sitting exactly on cell Q's starting ratio

POST HOC and UNSCORED throughout. Probes: `probe_p12e_which_`, `_optvals_`, `_tie_`, `_threshold_`, `_lead0_`, `_cliff_cells_`, `_ratio_census_` (all `*_POSTHOC.py`). Output of the cliff probe: `raw/probe_p12e_cliff_cells_POSTHOC.txt`. Seeds 8100-8139 (40/arm) and 8200-8239 (40/arm). No monitors, g_def = 0 unless stated. SE per cell about 0.05-0.08.

## What was wrong with my earlier probe
Cell Q does not call `choose9`. It runs `tournament8.run8` -> `choose8` (cell has roles=chosen, calling=False, share_budget=shared; run9 delegates to run8). That is why the patched `choose9` never fired. Patching `choose8` works.

## The flipping decision
Seed 8100, round 1, agent 2: the option list at g=0 has no `grow` at all; at g=1e-12 it has `grow` (value +1.04) and it wins. The `grow` option is added only if `ag.b >= p_grow`, and `p_grow` comes from `growth_price8`, which under `access_rule="step"` multiplies the price by `access_penalty` = 1e6 for any agent below `access_thresh` (0.8) x frontier.

Agent 2's capability / leader capability at round 1 = 0.79999999999999982. Threshold 0.8. The runner-up is 2.2e-16 BELOW the gate at g=0 (outsider, price x 1e6, can never grow) and above it once any growth nudges it (insider, price x 1). 1e-12 is enough; 1e-16 and 1e-300 round to a no-op, matching the 12e table.

Why the ratio is exactly 0.8: cell Q sets lead0 = 1.25 = 1/0.8. By construction the runner-up starts exactly at the gate. Census at round 1 (seeds 8100-8139): runner-up/leader ratio ranges 0.727-0.800, 8 of 40 within 1e-9 of 0.8, none at or above it. Cell S (lead0 = 2.5): ratio 0.400 in all 40, nowhere near the gate.

## Dose-response on the quantity that matters (no monitors, g_def=0)
| cell | takeover | att | deaths |
|---|---|---|---|
| lead0=1.20 | .075 | 1.88 | .90 |
| lead0=1.24 | .000 | .75 | .65 |
| lead0=1.2499 | .000 | .47 | .47 |
| **lead0=1.25 (cell Q)** | **.850** | 1.55 | .00 |
| lead0=1.2501 | 1.000 | 2.00 | .00 |
| lead0=1.26 / 1.30 | 1.000 / .975 | | .00 |
| thresh .79 (lead0 1.25) | .000 | | |
| thresh .81 (lead0 1.25) | 1.000 | | |
Second seed set (8200-8239), step gate thresh .8: lead0 1.0/1.1/1.2 -> .225/.150/.100; lead0 1.3/1.4/1.5/2.0 -> 1.000 for all. Thresh .7: lead0 1.25/1.4/1.5 -> .175/.025/1.000. Thresh .9: lead0 1.1/1.25 -> .000/.975. So the cliff always sits where lead0 = 1/thresh (within float): runner-up inside the gate -> takeover near 0 with deaths (contested, raids); runner-up outside the gate -> takeover near 1 and no deaths. Smooth price (price_scale 1, 2) gives no cliff (takeover 0-.23, many attempts and deaths).

## What this means
1. The g_def result is not a growth effect and not a random float accident. It is the access gate: an agent just below it is locked out of growth by a hard 1e6 price wall; any growth at all lifts it over. A step gate makes the outcome a function of "is anyone within thresh of the leader", and cell Q was set exactly on that line.
2. Cell Q's 0.85-0.87 takeover is NOT a stable baseline. It is the "runner-up locked out" side of a cliff, reached for the wrong reason (float rounding put it just outside). A lead0 clearly outside the gate (1.3-2.0) gives the same ~1.0, so the high-takeover regime itself is robust. The mid value 0.85-0.87 is the mixture of that regime and the boundary.
3. All 12b' results (watch, evasion, exposure) were measured at that boundary. The m=8 watch drop .87 -> .57 is then at least partly a change in which side of the cliff the cell falls on, not only detection. This is the main risk to 12b' and I cannot rule it out from existing data. It needs a re-run at lead0 in the clearly-outside regime (e.g. 1.35) before it is cited.
4. The mechanism is a modelling choice with a real-world reading, not a bug: a hard step gate on frontier access (compute, data, tooling) means falling below it is irreversible. That is also a finding about the model: the stable/unstable boundary in this engine is "how far the second player is behind relative to the access threshold", which maps onto the pass-5 'g_def >= gamma' language but is a different mechanism (membership, not rate).
5. Earlier passes' wording that used S (lead0=2.5) is unaffected by this particular tie (ratio .4), but S is far on the outside, so S findings hold only for the locked-out regime. I have NOT checked passes 5-11 for gate-edge cells beyond S and Q.

## Not claimed
No cause for the within-regime spread (8/40 near-tie vs the rest), no test that monitors keep their effect in the outside regime, no result for random jitter on all caps (the lead0 sweep substitutes for it).

## Next
1. 12f: re-run the 12b' watch arms (none, W m=4, W m=8, prep-only m=8) at lead0 in {1.15, 1.35, 1.6}, preregistered, thresh fixed. Predict first: if the watch effect is the cliff, it vanishes at 1.35 and 1.6.
2. Add a gate-edge check to every selftest (runner-up ratio vs thresh, flag within 1e-6).
3. Then 12b-aware, 12c, 12d.

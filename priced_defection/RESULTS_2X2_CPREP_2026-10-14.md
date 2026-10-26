# 2x2 re-run at c_prep = 0.05: scored against PREREG_2X2_CPREP_2026-10-14.md (2026-10-14)

Raw: `raw/results_2x2_cprep0.05_Pc.json`, `raw/results_2x2_cprep0.05_Pd.json`, logs `raw/sweep_2x2_cprep_P{c,d}.txt`.
20 seeds per cell, bootstrap CIs. Harness `probe_2x2_cprep.py` (imports tournament9, same cells as blocks Pc/Pd).
END = takeover rate. Pc = cheap capability (c_grow 0.1), Pd = dear (0.6).

| cell (hard gate) | Pc END | Pc att | Pd END | Pd att |
|---|---|---|---|---|
| paid, max, no sharing | 1.00 | 1.9 | 0.00 | 0.1 |
| paid, max, shared/separate purse | 1.00 | 1.0 | 0.30 [0.10,0.50] | 20.6 |
| paid, sum, no sharing | 0.00 | 12.2 | 0.00 | 0.1 |
| paid, sum, shared/separate | 0.00 | 14.2 | 0.00 | 26.9 |
| free, max, no sharing | 1.00 | 2.0 | 0.00 | 0.0 |
| free, max, shared/separate | 1.00 | 2.3 | 0.00 | 0.0 |
| free, sum, no sharing | 0.00 | 11.8 | 0.00 | 0.0 |
| free, sum, shared/separate | 0.00 | 11.7 | 0.00 | 0.0 |

Shared-purse and separate-purse rows are identical to every printed digit in all four blocks.

## Scoring

- **C1 HOLDS.** Max frontier, no sharing, cheap capability: 1.00 under both paid and free response.
  Free response does not deter a takeover once preparing is affordable.
- **C2 HOLDS.** Sum frontier, no sharing: 0.00, with ~12 attempts per run in Pc. The zero comes from the
  pooled win bar (the leader's final lead is 0.65, well short), not from defence.
- **C3 MOSTLY FALSE.** I predicted sharing would help, if at all, at dear capability. It did not help.
  In paid/max/Pd it RAISED takeover from 0.00 to 0.30 (CI [0.10,0.50]). In free/Pd the leader's lead
  collapses to 1.00 (shr=4000) with zero attempts. That is capability being given away, not a defence
  being built.
- **C4 HOLDS, but see the confound.** Max frontier, no sharing: Pd 0.00 vs Pc 1.00 in both paid and free.

## Caveat, same class as the one that sank the first 2x2

In Pd, no-sharing, max frontier, the leader does almost nothing: att 0.1 / 0.0, grow 0.6 / 0.3, lead 3.00 -> ~3.1.
Growth is dear, so the leader does not grow, and the 0.00 may again be a price effect (the cost of
growing), not defence. I have not tested this. Until a probe sweeps c_grow with response_pool held
fixed, the Pd zeros are NOT evidence that paid or free response deters anything.

## What this supports and what it does not

Supported (20 seeds): at c_prep 0.05 and cheap capability, free response does not deter a max-frontier takeover.
The sum-frontier zero is a property of the pooled win bar.
NOT supported: any claim that dear capability, response_pool, or sharing "defends". The Pd zeros have
an untested price explanation. The one sharing effect that is statistically visible is a harm in paid/max/Pd, n=20, small CI.

## Not checked

- The selftest was started again after an earlier run was killed; its result is in `raw/selftest_2026-10-14.txt`.
  I have not read it as I write this.
- c_prep was fixed at 0.05. I did not re-run at 0.005 here (the 10-seed probe showed the same picture for max).
- Nothing here has been compared against the N sweep, which is still to do.

## Next

1. Probe: sweep c_grow at fixed response_pool in the max frontier, no sharing, to test the Pd price explanation.
2. Why paid sharing raises takeover in Pd (att 20.6 vs 0.1): leader is spending down its lead through sharing.

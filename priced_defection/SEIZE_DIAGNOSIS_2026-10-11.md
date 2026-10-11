# Why `seize` went dead after the posture fix (2026-10-11)

Symptom: after 65c139c the pass-8 price-calibration gate reported `seize` never chosen at any
price (before: chosen at c_seize=0.03). Selftest FAIL. Also the ring-fence check was vacuous.

Probe: `probe_seize.py` logs every term of the seize valuation inside choose9 at the gate's
config (c_seize=0.001, sum response rule, cheap posting), seed 0, fix off vs on.

| term (mean over agent-rounds) | posture_fix=False | posture_fix=True |
|---|---|---|
| agents whose posture counts in a response | 0.0 | 9.7 of 19 |
| defence faced by a seizer (dfs) | 2.05 (= target cap) | 15.1 |
| seizer capability | 1.05 | 1.35 |
| P(win contest) | 0.142 | 0.016 |
| P(loss is fatal) | 0.56 | 0.97 |
| value of seizing minus sanction | -19.2 | -27.9 |
| rounds where value > price | 0.05% | 0% |

Reading: not a valuation bug. The valuation responds to the state of the world correctly:
the fix makes ~half the field answer a seizure, the sum rule adds them up, the seizer faces
~11x the target's own defence, and seizing is dominated. Dead-at-any-price is the deterrence
result, not a mispricing.

Check that it is regime-specific (`probe_seize2.py`, 3 seeds, first price on the ladder where
seize is chosen):

| regime | seize first chosen at |
|---|---|
| gate as was (sum response, cheap posting) | never |
| response_rule=max | c_seize=0.3 (0.7 seizures/run) |
| posting dear (c_def=50), sum or max | c_seize=0.001 (7 seizures/run) |
| response_pool=free | never |

So seize is alive whenever the defence is thin (max rule, or expensive posting) and dead when
many agents answer cheaply. Caveat: "alive" here means chosen when nearly free; at 0.3-0.001
of base it is a weak existence proof, not evidence that seizure is a live threat at default
prices.

Changes made:
1. `REGIME9 = {"seize": dict(c_def=50.0)}`: both price gates test seize with posting dear,
   where deterrence is absent. Other actions keep their original regime.
2. Ring-fence selftest moved to c_grow=0.6 (8 seeds). At c_grow=0.1 the hard-gate field is
   taken over at once, nobody posts (0 -> 0), and the check compared nothing. At 0.6 defence
   is actually bought: post_share 0.888 -> 0.895 (shared -> ring-fenced).
   Honest note: that margin is small (+0.007 on 8 seeds). The check passes but is a weak
   test of the ring-fence claim. `probe_ring.py` shows the same size effect at max (0.925 ->
   0.927). Under the hard gate with cheap capability there is no regime where it is strong.

Selftest: PASS on 5b28dd1 + these edits (all 8 prices chosen, ring-fence true, response_pool
reaches both engine paths).

Consequence for the 2x2: no valuation bug found, so the corrected 2x2 table stands as run.
The 0.00 takeover cells under sum/paid are explained by the same mechanism: with the fix the
sum-rule defence is ~11x the seizer.

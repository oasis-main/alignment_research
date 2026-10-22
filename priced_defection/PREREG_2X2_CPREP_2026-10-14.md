# Pre-registration: the 2x2 re-run at c_prep = 0.05 (2026-10-14, written BEFORE the run)

Why: PREP_PRICE_FINDING_2026-10-11.md showed the original 2x2 (c_prep = 0.5) had its zero-takeover
cells set by the price of preparing, not by defence. This re-runs the same 12 cells per capability
cost with preparing affordable, so the response_pool and sharing effects can be read.

Run: `probe_2x2_cprep.py`, blocks Pc (c_grow=0.1) and Pd (c_grow=0.6), c_prep=0.05, 20 seeds,
otherwise identical to tournament9 block Pc/Pd. Metric: END (= takeover rate `dw`) with bootstrap CI.

Predictions from the 10-seed no-sharing probe (Pc, noshare only; the sharing cells are NEW):
- C1. max frontier, noshare, paid and free: END >= 0.9 in both. Free response does not deter. (10-seed probe: 1.00 / 1.00.)
- C2. sum frontier, noshare, paid and free: END <= 0.1 in both, with many attempts. The zero comes from the pooled win bar, not defence. (probe: 0.00 / 0.00.)
- C3. sharing cells under max frontier: I do not know. If sharing helps at all, I expect it in the shared/separate purse arms at Pd (dear capability) and not at Pc. Weak prior, 60%.
- C4. Pd (dear capability) has lower END than Pc under max frontier in at least some cells, because growing the lead costs more. Prior 65%.

What would change my mind:
- If any max-frontier noshare cell has END < 0.5, C1 is false and the 10-seed probe was a small-sample fluke.
- If any sum cell has END > 0.3, the pooled win bar is not what holds it.

Nothing here is a claim about defence until C1 and C2 are scored.

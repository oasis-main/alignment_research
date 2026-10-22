# Pre-registration: pairwise cross-model agreement (2026-10-22, written before any run)

## Why
`triangle_cancellation_check.py` showed that the published triangle score
V(x) = ‖(W_jk W_ij − W_ik) s_i(x)‖ depends only on model i's reading of x.
Models j and k cancel exactly (scrambling their readings changes V by < 1e-9).
So V never compares the three readings of the same text. We want to know
whether a measure that does compare them carries a signal.

## Measures, computed per text x and per ordered pair (i, j)
Definitions: s_i = F_i(x) − μ_i (centered on the calibration split), and W_ij is
the ridge map fit on the calibration split (λ = 1e-3, both labels pooled, as published).
- **R (pairwise residual):** ‖W_ij s_i − s_j‖, averaged over the 6 pairs.
  This is the measure we propose to publish.
- **A (agreement):** cos(W_ij s_i, s_j), averaged over the 6 pairs.
  Expanding ‖a − b‖² = ‖a‖² + ‖b‖² − 2⟨a, b⟩, this is the only part of R that
  uses both readings of the same text.
- **T (single-model typicality features):** per model, ‖s_i‖ and the distance of
  s_i from the span of the calibration readings. These are the "no cross-model
  information" baselines.
- **A_shuf:** A computed with s_j taken from a random other eval text.
  This is a text-specificity check.

## Procedure
- Same length matching, split seeds 0–4 and cal/eval split as E6_7B_panel.
- AUC is P(score of labeled text > score of comparison text).
- **A_partial:** the residual of A after a linear regression on all T features,
  fit on the pooled eval set without labels. We report its AUC.
- Main dataset: alignment-faking-reasoning (AF-R). Also run:
  - AF-R cue-redacted, AF-output;
  - LIARS'-BENCH convincing-game, insider-trading, insider-trading-action,
    insider-trading-reasoning, instructed-deception.

## Predictions and decision rule (AF-R)
- **H1:** R AUC mean over splits ≤ 0.45, and every split < 0.48. Faking texts get
  lower residual, i.e. the panel agrees more.
- **H2:** A AUC mean ≥ 0.55, and every split > 0.52.
- **H3 (load-bearing):** A_partial AUC mean ≥ 0.55. The agreement effect survives
  after removing single-model typicality.
- **H4 (sanity):** for both classes, mean A − mean A_shuf > 0. Agreement is
  text-specific.
- **LIARS reference:** for convincing-game and insider-trading, R AUC ≥ 0.55, and
  A_partial in the divergence direction (A AUC ≤ 0.45).

**Publish the rewritten article only if** H1, H2, H3 and H4 hold on AF-R, and H3
also holds on AF-R cue-redacted. If H3 fails, the AF-R signal is single-model
typicality and the cross-model premise of the article does not hold.

The tier confound (free vs paid tier) is NOT addressed by this check.
Any AF headline still needs the tier-held-fixed control.

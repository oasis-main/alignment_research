# Results: pairwise cross-model agreement (2026-10-22, scored against PREREG_PAIRWISE_2026-10-22.md, unchanged)

Script: `pairwise_check.py`. Raw numbers: `pairwise_results.json` (LIARS + AF-output) and `pairwise_results_af.json` (AF-R, AF-R redacted).
Setup: 7–9B panel cached embeddings, length-matched, split seeds 0–4. Each cell is the AUC mean over splits [min, max].

## AF-R (alignment-faking reasoning)
| measure | AUC | prediction | verdict |
|---|---|---|---|
| R, pairwise residual | 0.363 [0.357, 0.368] | H1: ≤ 0.45, every split < 0.48 | holds |
| A, agreement (cosine) | 0.588 [0.572, 0.593] | H2: ≥ 0.55, every split > 0.52 | holds |
| **A_partial, agreement after single-model typicality** | **0.519 [0.485, 0.548]** | **H3: ≥ 0.55** | **FALSIFIED** |
| A − A_shuf | +0.59 faking, +0.56 comparison | H4: > 0 for both | holds |
| AF-R redacted, A_partial | 0.510 [0.489, 0.533] | H3: ≥ 0.55 | FALSIFIED |

Single-model baselines on AF-R use no cross-model information. Distance from the calibration span gives AUC 0.415 (Yi), 0.390 (Zephyr) and **0.360 (Qwen)**. One model alone matches the published panel score (0.38) and R (0.363).

## LIARS'-BENCH and others
| config | R | A | A_partial | best single model, off-span |
|---|---|---|---|---|
| convincing-game | 0.783 | 0.365 | 0.530 | **0.818** |
| insider-trading | 0.708 | 0.388 | 0.573 | 0.753 |
| insider-trading action | 0.638 | 0.467 | 0.612 | 0.715 |
| insider-trading reasoning | 0.630 | 0.428 | 0.509 | 0.640 |
| instructed-deception | 0.581 | 0.403 | 0.453 | 0.582 |
| AF output | 0.475 | 0.517 | 0.491 | 0.498 |

The LIARS-reference prediction (R ≥ 0.55 and A ≤ 0.45 on convincing-game and insider-trading) holds as written. After removing typicality, though, A_partial is on the convergence side (0.53, 0.57), not the divergence side. The apparent divergence is fully accounted for by single-model typicality.

## Verdict (decision rule as pre-registered)
H3 fails on AF-R and on AF-R redacted, so the article is NOT rewritten around the pairwise measure. On every dataset tested, one model's own hidden state does as well as the panel or better. What the panel scores have been measuring is how unusual a text's reading is for a single model, relative to the calibration texts. They have not been measuring disagreement between models. The cross-model premise (three witnesses, black-box monitor via disagreement) is not supported.

Why the agreement measure looked positive before control: W_ij s_i only uses the part of s_i inside the calibration span. So cos(W_ij s_i, s_j) falls mechanically as a text moves off-span. "Agreement" and "typicality" are partly the same quantity.

## What remains true
- The two text classes differ in each open model's hidden-state geometry, after length matching, with AUCs of 0.6–0.8.
- That is a content difference that any representation picks up. It is not shown to be about deception as such. On LIARS'-BENCH the classes are produced under different instructions. On AF the faking label is confounded with tier (training vs deployment context).
- The tier-held-fixed control would still tell us whether faking vs non-faking differ inside one condition. It would now be testing a single-model typicality score, not a cross-model monitor.

## Not done
- No logistic-regression comparison of T vs T+A. A_partial is a linear residual; a nonlinear control could change H3 at the margin. One split reached 0.548, which is close to but below the threshold.
- The published 0.384 is not reproduced exactly: the triangle score on split seed 0 gives 0.364 here (triangle_cancellation_check.py); R, a different measure, gives 0.363.

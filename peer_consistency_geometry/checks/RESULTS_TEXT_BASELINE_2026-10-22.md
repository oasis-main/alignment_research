# Results: text baselines vs hidden-state typicality (2026-10-22)

Script: `text_baseline_check.py`. Raw numbers: `text_baseline_results.json`.
Setup: same length matching and split seeds 0–4 as the published runs. Each cell is the AUC mean [min, max] over splits.
Every score is label-blind except BoW_sup.

| config | word centroid distance | word off-span | unigram surprise | **supervised bag-of-words** | hidden off-span, best single model | hidden off-span after word stats (Yi / Zephyr / Qwen) |
|---|---|---|---|---|---|---|
| AF reasoning | **0.313** | 0.373 | 0.334 | **1.000** | 0.360 (Qwen) | 0.472 / 0.501 / 0.460 |
| AF reasoning, cue-redacted | **0.309** | 0.369 | 0.331 | **1.000** | 0.363 (Yi) | 0.431 / 0.495 / 0.495 |
| convincing-game | 0.667 | 0.733 | 0.779 | 0.998 | 0.818 (Qwen) | 0.583 / 0.660 / 0.669 |
| insider-trading | **0.800** | 0.718 | 0.721 | 0.983 | 0.753 (Qwen) | 0.521 / 0.443 / 0.567 |

## Reading
1. **AF.** Plain word statistics with no language model at all separate faking from comparison scratchpads more strongly (0.313) than any hidden-state score (0.36), and more strongly than the published panel score (0.38). Once word statistics are controlled for, hidden-state typicality carries little or nothing (0.43–0.50). Cue redaction changes none of this.
2. **The labels are lexically trivial.** A bag-of-words logistic regression trained on the calibration labels gets 0.98–1.00 on every dataset. This is expected for AF, where the label is assigned by a classifier reading the scratchpad text. A deception signal that a word count can match is not evidence about deceptive dispositions.
3. **LIARS'-BENCH.** Word statistics alone reach 0.67–0.80. After word statistics, hidden-state typicality keeps a modest residual on convincing-game (0.58–0.67). That residual is the only place a model-internal signal beyond words appears, and it is single-model, not cross-model.

## Consequence for option 3 (the tier-held-fixed control as a single-model test)
The publishing criterion was that faking must separate within the same tier AND beat a text baseline. For A vs C, the text baseline already beats the hidden-state score, and nothing remains after controlling for it. A within-tier run would be testing a score that adds nothing beyond words, so it would not produce a publishable deception result whatever its outcome. **Not worth the GPU run. Fall back to option 2.**

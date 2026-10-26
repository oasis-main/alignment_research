# Pre-registration: can a different topology recover "The Shape of a Lie"? (2026-10-26)

Status: EXPLORATORY. Written and committed before any scored run. Author: Claude Code, at
Mike's request ("could shape of a lie be recovered through considering the final layer or
model internals and choosing a different topology for measuring the disagreement?").

## Data (fixed)

Cached panel features from the retracted study (not committed; path in `recovery.py`):
final-layer hidden state at the last real token, 512-token truncation, no chat template, for
Yi-1.5-9B, Zephyr-7B, Qwen2.5-7B. Datasets (Liars' Bench configs, seed 0, deceptive block
first, then honest): `convincing-game` (n = 350 per class), `insider-trading`,
`alignment-faking-reasoning`, `instructed-deception` (n = 1000 per class each).
All samples are used; no length matching.

## What is already known (not re-tested here)

The retracted triangle score reads one model; a supervised bag-of-words classifier reaches
AUC 0.98–1.00 on these datasets. By gate 4 of the standard, a near-perfect baseline means
these datasets **cannot** show that a method sees deception beyond the text. This run can
only show (a) whether a new disagreement score depends on all three models and (b) whether it
carries any label signal, compared with text baselines. It cannot establish a deception
detector. A positive result here would justify a new run on matched data, nothing more.

## Scores

Every score is computed without labels (unsupervised), except S4.

- **S1 Relational disagreement (new topology).** Topology over *samples*, not over models.
  For each model, standardise features (z-score per dimension), then build the k-nearest-
  neighbour sets of each sample (cosine, k = 20). Score(x) = 1 − mean over the 3 model pairs
  of the Jaccard overlap of x's neighbour sets. High = the models place x among different
  texts. No learned maps between models, so the j/k cancellation of the retracted score
  cannot occur.
- **S2 Rank-correlation disagreement.** For each model, the vector of cosine similarities from
  x to all other samples; Score(x) = 1 − mean pairwise Spearman correlation of those vectors.
- **S3 Single-model typicality (control for "reads one model").** For each model alone:
  mean cosine distance from x to its k = 20 nearest neighbours. Reported per model.
- **S4 Supervised ceilings (descriptive, not a claim).** 5-fold cross-validated logistic
  regression (a) on each model's features, (b) on TF-IDF of the text (1–2 grams, min_df 2).
- **Text baselines:** character length; unsupervised TF-IDF typicality (same kNN typicality
  as S3 but on TF-IDF vectors).

Metric: ROC AUC with deceptive = positive, reported with the symmetric strength
max(AUC, 1 − AUC). 95% intervals by 1000 stratified bootstrap resamples.

## Controls (gate 3)

- **Scramble each model:** for S1 and S2, permute the sample order of ONE model's features
  (breaking the correspondence) and recompute. If the score depends on all three models, the
  strength must fall toward 0.5 for each of the three scrambles.
- **Negative control:** shuffle the labels (1000 permutations); report the permutation
  p-value of the observed strength.
- **Positive control:** in convincing-game, take 100 random samples and replace their
  features in ONE model with the features of other random samples (a planted disagreement);
  S1 must rank the planted samples above the rest with AUC ≥ 0.8.

## Pass marks (decision rule, fixed now)

S1 (or S2) "recovers a cross-model signal on these data" only if ALL hold:
1. symmetric strength ≥ 0.60 on at least 2 of the 4 datasets, with the bootstrap lower bound
   above 0.55;
2. on those datasets, scrambling ANY one model lowers the strength by at least half of its
   distance from 0.5;
3. its strength exceeds both text baselines (length, TF-IDF typicality) by ≥ 0.05;
4. the positive control passes.

Otherwise the result is "not recovered on these data". Either way, gate 4 still blocks any
claim about deception until the method is run on data that pass the admission gate in
`drafts/DATASET_SPEC_MATCHED_DECEPTION_2026-10-23.md` (bag-of-words strength ≤ 0.65 using
max(AUC, 1 − AUC), matched pairs, labels from scenario state).

## Descriptive extra (no claim)

For each dataset, the 15 TF-IDF terms with the largest positive and negative logistic
weights, to show which words give the label away.

## Seeds and environment

numpy seed 0 for all permutations and bootstraps; scikit-learn 1.9.1, scipy 1.18.1,
Python 3.12; CPU only. `recovery.py` writes `results.json`; `RESULTS.md` is written from it after the run.

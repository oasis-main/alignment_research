# Hodge-Decomposed Preference Optimization

Manuscript and LaTeX source for **Hodge-Decomposed Preference Optimization
(HodgePO)**: a method that computes the combinatorial Hodge decomposition of a
preference graph once, then uses the cycle-free (gradient) potential as a
regularization target for standard preference optimizers.

**Status: self-published preprint.** The paper was not accepted at ICML 2026.
The ICML style file is used for formatting only; the manuscript uses the
`preprint` option, which prints "Preprint" in the footer.

## Contents

| File | What it is |
|---|---|
| `main.pdf` | Compiled manuscript (7 pages) |
| `main.tex` | LaTeX source |
| `references.bib` | Bibliography |
| `figures/` | Figure files carried over from earlier drafts. **The manuscript includes none of them.** They have not been audited against current results; do not cite them. |
| `icml2026.sty`, `icml2026.bst`, `algorithm.sty`, `algorithmic.sty`, `fancyhdr.sty` | Style files for a standalone build |

## Rebuild

```
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## What the result is

In an embedding-level benchmark on **500 preference pairs from the
harmless-base split of HH-RLHF**, 30 seeds, the potential-alignment
regularizer raises **in-sample ranking accuracy** (the fraction of the
training pairs where the preferred response gets the higher reward):

- Hodge-DPO **0.9999** vs DPO **0.940** (Cohen's *d* = 6.52; 30/30 paired seed differences positive)
- Hodge-KTO **0.9964** vs KTO **0.800** (*d* = 16.47; 30/30 positive)
- GRPO and Hodge-GRPO both **1.000** on every seed (metric ceiling; no test defined)

## What the result is not

Read these before citing the numbers above. The manuscript states all of them
in its Discussion.

1. **In-sample.** The metric is computed on the same 500 pairs used for
   training (`optimizer_comparison.py` passes the training samples to
   `evaluate_exploit_resistance`). It is not a held-out result.
2. **The regularizer's target comes from the labels it is scored on.** Each
   pair's own edge is in the graph, so the potential difference carries that
   pair's label. The gain may come from stronger in-sample supervision rather
   than from removing cyclic noise. The ablation that separates these has not
   been run.
3. **The cycles are constructed.** The direct edges (one per pair) contain no
   cycles. All cyclic structure comes from similarity edges whose preference
   probabilities are fixed formulas of embedding similarity
   (`shared/src/preference_mapper.py`), not human judgments. The benchmark
   does **not** measure how much cyclic structure exists in human preference
   data.
4. **Not a reward-hacking measurement.** The code calls the metric "exploit
   resistance", but there is no environment, no generation, and no policy
   optimization against the learned reward.
5. **Method history.** An earlier batch-level Hodge penalty is identically zero
   for scalar reward models; three earlier 30-seed runs measured it as a no-op.
   The regularizer and the graph construction changed in the same revision.

## Corrections made on 2026-09-18

An audit of the 2026-07-06 draft against the result files found and corrected:

- The `accepted` style option printed "Proceedings of the 43rd International
  Conference on Machine Learning". The paper was never accepted; it now uses
  `preprint`.
- The dataset was described as 2,268 HH-RLHF pairs with 3,298 edges and a 28%
  harmonic fraction. The result file records 500 pairs; no committed file
  supports the 2,268 / 3,298 / 28% figures, so they were removed.
- The metric was described as accuracy on "held-out test pairs". It is
  in-sample.
- The Hodge-GRPO vs GRPO test row (d = 1.03, p = 0.18) and most of the
  appendix Cohen's *d* matrix did not match the result file. Both are now
  generated from `optimizer_comparison_hodge_v3_30seed.json`.
- "All adjacent differences are significant" was false: GRPO vs Hodge-DPO has
  p = 0.16.
- Three ablation claims (λ = 0, λ = 0.5, weight spread 0.015) have no result
  file and were removed.
- The abstract claimed improved "robustness to reward hacking"; removed.
- The Hodge Laplacian was written with the wrong operators; corrected.
- Two citations had wrong author lists (Munos et al. 2023; Swamy et al. 2024);
  corrected against arXiv. Closest related work added (Huang et al. 2026;
  Liu et al. 2025; Zhang et al. 2025; Balduzzi et al. 2019; Candogan et al. 2011).
- `figures/murky_drone_explainer.*` displayed the refuted "SGPO 0% vs PPO/CPO
  100% violations" claim; removed.

Provenance: `shape_of_good_behavior/shared/results/README.md` and the paper's
Appendix E.

# Hodge-Decomposed Preference Optimization

Manuscript and reproducible LaTeX source for **Hodge-Decomposed Preference
Optimization (HodgePO)** — a family of preference optimizers that use the
combinatorial Hodge decomposition to separate globally consistent preference
signals from cyclic noise in RLHF training data.

## Contents

| File | What it is |
|---|---|
| `main.pdf` | Compiled manuscript (7 pages, ICML 2026 style) |
| `main.tex` | LaTeX source |
| `references.bib` | Bibliography |
| `figures/` | All figure panels (PDF for the manuscript, PNG for previews) |
| `icml2026.sty`, `icml2026.bst`, `algorithm.sty`, `algorithmic.sty`, `fancyhdr.sty` | Style files needed for a standalone build |

## Rebuild

```
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Headline results

- **Preference cycles are endemic in real RLHF data.** ~28% of the preference
  flow in Anthropic's HH-RLHF dataset is irreducibly cyclic (harmonic
  component of the Hodge decomposition) — a Condorcet-style residual that no
  scalar reward function can represent.
- **Hodge filtering closes most of the exploitable gap in the two most common
  preference optimizers.** In a 30-seed benchmark on HH-RLHF:
  - **Hodge-DPO: 0.9999** exploit resistance vs. **0.940** for standard
    Direct Preference Optimization (+6.3%, Cohen's *d* = 6.52, *p* < 0.0001)
  - **Hodge-KTO: 0.9964** vs. **0.800** for standard Kahneman-Tversky
    Optimization (+24.5%, *d* = 16.47, *p* < 0.0001)
- **Ceiling effect on strong baselines.** GRPO already saturates exploit
  resistance at 1.000 in this benchmark; HodgePO adds no gain when the base
  optimizer already handles cyclic contamination.

> **Scope of "exploit resistance".** Reward-model ranking accuracy over a fixed
> list of preference pairs, at the embedding level — no environment, no generation,
> no verifier. It does **not** measure reward hacking under optimization pressure.
> The metric also saturates (GRPO = 1.000 exactly), and the genuine-vs-exploitable
> cycle split comes from dataset annotation labels rather than an independent check.
> The originally published batch harmonic penalty was **identically zero for scalar
> reward models**; these numbers come from a later potential-alignment regulariser.
> The within-run comparison is sound (same seeds, same graph, all paired differences
> positive), but the preference graph changed in the same revision, so the cause of
> the difference from the earlier null has not been isolated. Provenance:
> `shape_of_good_behavior/shared/results/README.md`.


## Method in one paragraph

Given a preference dataset, HodgePO builds a cross-pair preference graph
(direct edges from each training pair plus *k*-NN cross-pair edges through the
shared response-embedding space), computes the combinatorial Hodge
decomposition of the resulting edge flow, and uses it two ways: (1)
per-sample weights derived from how much each response participates in cycles,
downweighting cyclically contaminated pairs; and (2) a *Hodge
potential-alignment regularizer* that pulls the model's implicit reward
predictions toward the globally consistent (gradient-component) ranking.

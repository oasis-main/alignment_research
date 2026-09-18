# Hodge Potential Alignment for Preference Optimization: A Negative Result

Manuscript and LaTeX source. **Status: self-published preprint** (never
accepted at a venue; the ICML style file is used for formatting only).

## Result in one paragraph

HodgePO pulls a preference model's reward differences toward the cycle-free
(gradient) potential of a preference graph. An earlier version of this paper
reported in-sample ranking accuracy of 0.9999 vs 0.940 (DPO) and 0.9964 vs
0.800 (KTO). **A controlled re-test shows no benefit.** On held-out pairs
(5 splits × 30 seeds, 500 HH-RLHF harmless-base pairs), Hodge-DPO scores
0.537 vs DPO 0.550, and Hodge-KTO 0.543 vs KTO 0.542; no split-level paired
difference is significant (p ≥ 0.34). A margin control with no pair-specific
Hodge information reproduces the entire in-sample gain. All methods, including
a linear probe, score 0.52–0.59 held-out (chance 0.50).

The paper reports the negative result and three evaluation pitfalls that
produced the original claim: in-sample scoring, a target that acts as a
generic margin, and an index misalignment that gave each sample another
pair's target.

## Contents

| File | What it is |
|---|---|
| `main.pdf` | Compiled manuscript (5 pages) |
| `main.tex`, `references.bib` | Source |
| `figures/` | Figure files from earlier drafts. **The manuscript includes none of them**; they are unaudited — do not cite them |
| `icml2026.sty`, `icml2026.bst`, `algorithm.sty`, `algorithmic.sty`, `fancyhdr.sty` | Style files |

Rebuild: `pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex`

## Provenance

All in the `shape_of_good_behavior` repository:
- Original in-sample run: `shared/results/optimizer_comparison_hodge_v3_30seed.json`
- Replay of that run: `scripts/replay_published_v3_subsample.py`
- Held-out re-test: `shared/results/optimizer_comparison_heldout_v1.json`,
  produced by `scripts/heldout_hodge_benchmark.py`
- Full history and caveats: `shared/results/README.md`

## Version history

- **2026-07-06 draft:** claimed ICML proceedings, held-out evaluation, "28% of
  HH-RLHF is cyclic", robustness to reward hacking, and unsupported ablations.
  None of these holds.
- **2026-09-18, first correction:** relabelled as a preprint; claims restricted
  to in-sample; unsupported numbers removed; citations fixed; refuted Murky
  Drone figure removed.
- **2026-09-18, second correction:** the held-out re-test with controls found
  no effect, and the replay found that the original run used a 2,268-pair
  HH-RLHF + TRACE pool (not the 500 committed pairs) and misaligned targets.
  The paper was rewritten as a negative result.

# Peer-Consistency Geometry

A cellular-sheaf approach to detecting cross-model representational divergence on
alignment-relevant content. Companion artifact for the paper draft at
[`../writing/peer_consistency_deception_divergence.md`](../writing/peer_consistency_deception_divergence.md).

> **RETRACTED (2026-10-22).** The central claim of this document, that a panel of three
> language models detects strategic deception and alignment-faking reasoning through
> cross-model disagreement, is withdrawn. Do not cite, submit or quote its numbers as
> evidence about deception. Reasons, with scripts and pre-registration:
> [`checks/`](checks/).
>
> 1. **The score is not cross-model.** (δ¹c)_ijk = W_jk c_ij + c_jk − c_ik = (W_jk W_ij − W_ik) s_i,
>    so models j and k cancel exactly and only model i's reading of the text enters
>    (scrambling j and k changes the score by < 1e-9 relative; `triangle_cancellation_check.py`).
>    With ~876 calibration texts in ~4,000 dimensions the score is essentially distance
>    from the span of calibration readings: one model's typicality score.
> 2. **A genuine pairwise agreement measure does not rescue it.** Pre-registered bar AUC ≥ 0.55
>    after removing single-model typicality; observed 0.519 on alignment faking (0.510 cue-redacted).
> 3. **Words alone explain the alignment-faking signal.** TF-IDF distance from the calibration centroid gives
>    AUC 0.313 on alignment faking (hidden-state scores 0.36–0.38), and hidden states add nothing
>    after word statistics there (0.43–0.50). On LIARS'-BENCH words alone reach 0.67–0.80 and
>    hidden states keep only a modest single-model residual on persuasion (0.58–0.67).
>    Supervised bag-of-words reaches 0.98–1.00 on every dataset tested: the labels are lexically
>    easy (the alignment-faking label is itself assigned by a classifier reading the scratchpad).
> 4. Further problems found on the way: the alignment-faking comparison cell was described as
>    "honest refusal" but mostly complies, and faking is confounded with tier (training vs
>    deployment context); texts were truncated at 512 tokens (~73% of scratchpads are longer);
>    on split seed 0 the published score reproduces as 0.364 (published 5-split mean 0.384), unexplained.
>
> The original headline is in git history; the layout and code notes below are kept for audit.

**What is still useful here.** The code, cached-result JSONs and figures are kept so the retraction can be audited. The methods lesson is general: a loop (cocycle) score built from independently fitted pairwise maps can collapse algebraically to a single-node score. Check by scrambling the other nodes, and always run a text baseline before believing a representation-geometry signal.

---

## Layout

| Path | Role |
|---|---|
| [`src/peer_sheaf.py`](src/peer_sheaf.py) | Affine restriction maps via ridge regression, per-pair residuals, aggregate lossiness `L(x)` |
| [`src/peer_hodge.py`](src/peer_hodge.py) | `PeerComplex` (0/1/2-cells), δ⁰ and δ¹ assembly, `hodge_decompose`, low-rank variant, per-edge norms |
| [`modal/embed_panel.py`](modal/embed_panel.py) | Modal A100 runner for the 7–9B panel — `embed_panel` (HH-RLHF) and `embed_liars_panel` (text-driven; reads pre-uploaded JSONs to dodge gated-dataset 403s) |
| [`experiments/E1_small_panel.py`](experiments/E1_small_panel.py) | Small-panel baseline (SmolLM2/Qwen2.5-0.5B/TinyLlama) on HH-RLHF — sign-consistency test |
| [`experiments/E6_liars.py`](experiments/E6_liars.py) | LIARS'-BENCH deceptive-vs-honest *responses* — adds `--length-match`, `--split-seeds`, per-edge/per-triangle structure |
| [`experiments/E6_7B_panel.py`](experiments/E6_7B_panel.py) | 7–9B analysis. SVD-free `cocycle_blockwise` (per-triangle δ¹c without the unused 23.5k×11.8k SVD). `--texts-json` length-matches custom traces (reasoning, CoT) against the exact embedded texts |
| [`results/`](results/) | Length-matched AUCs per config, subsample variance summary, reasoning-vs-output splits, cue-redacted control |
| [`figures/`](figures/) | Paper figures (sheaf-complex schematic, AUC scoreboard, reasoning-vs-action quadrant) — regenerate via `python figures/make_figures.py` |

---

## Reproducing the headlines

1. Embed the 7–9B panel on LIARS'-BENCH `convincing-game` and `insider-trading`
   (texts uploaded to a Modal volume; see `modal/embed_panel.py::embed_liars_panel`
   docstring).
2. `python experiments/E6_7B_panel.py --config <config> --seed 0 --split-seeds 0,1,2,3,4`
   reports raw + length-matched AUC, per-edge / per-triangle / per-model
   structure, and writes a results JSON.
3. For custom traces (e.g. alignment-faking scratchpads), pass `--texts-json`
   with the exact embedded texts so length-matching uses them instead of
   reconstructing via `load_liars`.

Source-of-truth results JSONs are in [`results/`](results/). Each contains the
full per-split breakdown so the headline AUCs in the paper are
reverse-engineerable.

---

## Lessons baked into the code

- **Write the algebra out.** ‖δ¹c‖ reduces to (W_jk W_ij − W_ik) s_i, a one-model quantity. This was derived in the writeup (§2.3) and its consequence missed for five months.
- **Run the dumbest baseline.** A word-count baseline beat every hidden-state score on alignment faking.

- **AUC over Cohen's d** for ‖δ¹c‖ (a right-skewed norm). Mean-based stats are
  unstable across cal/eval splits; rank-based stats are reproducible. See
  insider-trading where pooled `d` swings around 0 while AUC stays at 0.625 ±
  0.009.
- **SVD-free `cocycle_blockwise`** — the per-input δ¹c norm doesn't need the
  full O(D_E × D_V) SVD of the coboundary. We compute per-triangle blocks
  directly, which is the difference between hours-of-memory-thrash at 7–9B and
  seconds.
- **Length is a first-class confound.** `length_match_indices` in
  `experiments/E6_liars.py` is the cheap quantile-bin equalizer; controlling
  for it cut some apparent signals to noise (insider-trading 0.625 → 0.555 on
  the small panel) while leaving the real ones intact (convincing-game).
- **Race-condition discipline.** Never run analysis while `modal volume get
  --force` is still re-downloading — torn `.npy` reads produce silently wrong
  AUCs. Always wait for pull completion before launching analysis.

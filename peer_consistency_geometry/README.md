# Peer-Consistency Geometry

A cellular-sheaf approach to detecting cross-model representational divergence on
alignment-relevant content. Companion artifact for the paper draft at
[`../writing/peer_consistency_deception_divergence.md`](../writing/peer_consistency_deception_divergence.md).

**Headline.** Across a panel of three independently-trained 7–9B instruct LMs
(Yi-1.5-9B-Chat, Zephyr-7B-beta, Qwen2.5-7B-Instruct), the cocycle violation
‖δ¹c‖ of a peer-consistency sheaf detects strategic deception in model outputs
(AUC 0.62–0.66, length-controlled, p ≤ 1e−6) and detects alignment-faking
*reasoning* via a sign-flipped convergence signal (AUC 0.38, p=5.9e−8;
0.39 after cue redaction). Selectivity, length-control, scale-gating, and the
reasoning-vs-output split are the methodological spine.

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

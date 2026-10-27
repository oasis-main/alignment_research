# Results: filtered MRR re-check of "MRR 0.346, competitive with ConvE" (2026-10-27)

**Verdict by the pre-registered rule: FAIL. The claim is withdrawn.**

Pre-registration: the docstring of `scripts/modal_hdc_filtered_eval.py` in
MikeHLee/structure_of_clear_thinking, commit `2dffdd4` (Kolmogorov, 2026-10-23, written
before any run). The script that ran is byte-identical to that commit
(SHA-256 `97a3d046bbac0cc2f47f0993402bfb1ee8405faddace98dae6c8ee18001ecc07`).

- **Claim under test:** "competitive with ConvE (0.325)" on FB15K-237.
- **Metric:** filtered MRR, head and tail averaged (`filtered_both`), FB15K-237 test set, seed 42.
- **Pass mark:** ≥ 0.31.
- **Result:** **0.212**. Below the pass mark.

Run: Modal app `ap-qPpZWcpOg3ybFOaY1hLFvK`, 1× A100, 2026-10-27, by Claude Code on Mike's
Mac with Mike's Modal profile (Yes Man's container could not reach the Modal dispatch host).
Same model and recipe as the published run: HolE-style circular-convolution embeddings, dim 4096,
margin 0.5, one random tail negative, Adam lr 0.001, batch 512, 50 epochs, seed 42.
Raw output: [`fb15k237_filtered_eval_seed42.json`](fb15k237_filtered_eval_seed42.json),
[`wn18rr_filtered_eval_seed42.json`](wn18rr_filtered_eval_seed42.json).

## All protocols

| Dataset | Protocol | MRR | Hits@1 | Hits@3 | Hits@10 |
|---|---|---|---|---|---|
| FB15K-237 | raw, tail only | 0.237 | 0.154 | 0.253 | 0.414 |
| FB15K-237 | filtered, tail | 0.319 | 0.222 | 0.351 | 0.519 |
| FB15K-237 | filtered, head | 0.105 | 0.055 | 0.108 | 0.206 |
| FB15K-237 | **filtered, both (pre-registered)** | **0.212** | 0.138 | 0.230 | 0.363 |
| WN18RR | raw, tail only | 0.350 | 0.247 | 0.428 | 0.527 |
| WN18RR | filtered, tail | 0.469 | 0.430 | 0.487 | 0.541 |
| WN18RR | filtered, head | 0.429 | 0.396 | 0.442 | 0.494 |
| WN18RR | filtered, both | 0.449 | 0.413 | 0.464 | 0.518 |

## What the numbers say

1. **The published number came from WN18RR, not FB15K-237.** The paper reports MRR 0.346,
   Hits@1 0.242, Hits@3 0.425, Hits@10 0.524 "on FB15K-237". WN18RR raw tail-only gives
   0.350 / 0.247 / 0.428 / 0.527, within 0.005 on all four. FB15K-237 raw tail-only gives
   0.237. This was the pre-registered secondary check, and the earlier summary already quoted
   WN18RR's entity count (40,943).
2. **On FB15K-237, the model is not competitive with ConvE (0.325) or RotatE (0.338).**
   Under the standard protocol it scores 0.212. Head prediction is weak (0.105); a single
   random tail negative trains tails only.
3. **WN18RR filtered-both is 0.449.** This is descriptive only. It was not pre-registered as a
   claim, and it needs its own pre-registration and seeds before any comparison is made.

## Limits

One seed. No hyper-parameter search, by design: the run repeats the published recipe.
Not independently re-run.

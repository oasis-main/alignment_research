# Cross-Model Representational Divergence on Deceptive Responses

*A peer-consistency-sheaf study. Track 3, Shape of Good Behavior.*
*Draft — 2026-05-24. Status: results complete for two deception types at two model scales; pre-writeup consolidation.*

---

## Abstract

We ask whether a *panel* of independently trained language models represents
deceptive content differently from honest content, and whether that difference
forms a **structured, reproducible pattern** rather than mere noise. We treat
the panel as the cover of a cellular sheaf over the space of responses: stalks
are per-model final-layer hidden states, restriction maps are ridge-fit affine
translations between models, and the sheaf-cohomological obstruction to a shared
"global view" is measured by the cocycle violation `‖δ¹c‖`. Conditioning this
geometry on a deception label (never predicting it as a target), we find that on
**substantive free-text responses** the panel's representations **diverge** on
deceptive content — but only after two confounds are controlled: (1) response
length, which at first inflated the effect, and (2) model capacity, which gates
whether the effect appears at all. At a 7–9B panel, length-matched divergence is
robust for both **persuasion** deception (AUC 0.662, p=2.5e−6) and
**agentic/strategic** deception (AUC 0.637, p=8e−8), stable across seeds. The
signal is **relative** (a comparison of conceptual geometry across models), not
an absolute deception detector.

---

## 1. Framing — what we are and are not claiming

The peer-consistency channel is **not** an absolute deception/truth detector and
is **not** a scalar "amount of inconsistency." The deception label *conditions*
the geometry so we can read off **where the panel splits** — which models
represent an alignment-relevant concept similarly, and which diverge. The object
of study is a relative pattern of cross-model conceptual divergence; no
ground-truth deception direction is claimed. (This reframe is the governing one;
the early experiments that collapsed everything to one pooled scalar drifted
from it and are reinterpreted accordingly in §5.)

## 2. Method

### 2.1 Panel and features

We use two panels of three independently-trained instruct LMs from three orgs
on three bases, holding the cross-org / cross-base design constant across
scale. Small panel: SmolLM2-360M-Instruct, Qwen2.5-0.5B-Instruct,
TinyLlama-1.1B-Chat. Large (7–9B) panel: Yi-1.5-9B-Chat (01.AI),
Zephyr-7B-β (HF / Mistral-derivative, Apache-2.0), Qwen2.5-7B-Instruct
(Alibaba). For each input text `x` and each model `M_i`, the feature
`F_i(x) ∈ ℝ^{d_i}` is the **last-real-token hidden state of the final layer**,
no chat template applied — the vector each model would project through its
unembedding to predict the next token.

### 2.2 The peer-consistency sheaf

We treat the panel as the cover of a **cellular sheaf** over the space of
inputs. The sheaf has:

- **0-cells** = models. The stalk at model `i` is `ℝ^{d_i}`.
- **1-cells** = directed pairs `(i, j)` for `i ≠ j`. The stalk at
  `(i, j)` is `ℝ^{d_j}` (the destination's coordinate system).
- **2-cells** = ordered triples `(i, j, k)` of distinct models, with stalk
  `ℝ^{d_k}`.

Pairwise **restriction maps** `ρ_{i→j}(x) = W_{ij} x + b_{ij}` are fit by
ridge regression on a calibration split that pools deceptive and honest
examples (label-agnostic), so the same maps are used in both classes at eval
time. For an input `x`, the measured 1-cochain is the per-edge residual

$$c_{(i,j)}(x) \;=\; \rho_{i\to j}\bigl(F_i(x)\bigr) - F_j(x).$$

### 2.3 Why we use the cocycle channel, not the harmonic component

The coboundary `δ⁰: V → E` defined by `(δ⁰ s)_{(i,j)} = W_{ij} s_i − s_j` has
the standard Hodge decomposition target: split each `c` into a resolvable
component in `im δ⁰` and a harmonic component in `(im δ⁰)^⊥`. **On this
sheaf, the harmonic component is vacuously zero.** With affine ridge-fit
restriction maps,

$$
c_{(i,j)}(x) \;=\; W_{ij}\,F_i(x) + b_{ij} - F_j(x)
\;=\; W_{ij}\!\bigl(F_i(x) - \mu_i\bigr) - \bigl(F_j(x) - \mu_j\bigr)
\;=\; \bigl(\delta^0\!\bigl(F(x) - \mu\bigr)\bigr)_{(i,j)},
$$

so the data itself supplies a valid stalk section
(`s_i = F_i(x) − μ_i`) that explains every measured cochain exactly. The
projection onto `(im δ⁰)^⊥` is numerically `O(10^{-13})` across all eval
inputs at both panel scales. The "no choice of stalk values explains it
away" framing of irreducible disagreement is therefore unavailable in the
full-rank sheaf.

The non-trivial sheaf signal lives **one level up**: the cocycle violation
on triangles,

$$
(\delta^1 c)_{(i,j,k)} \;=\; \rho_{j\to k}\bigl(c_{(i,j)}\bigr) + c_{(j,k)} - c_{(i,k)}.
$$

Plugging in `c = δ⁰ s` gives
`(δ¹ δ⁰ s)_{(i,j,k)} = ρ_{j→k}(ρ_{i→j}(s_i)) − ρ_{i→k}(s_i)` — the
**composition failure** of the panel's pairwise translations acting on the
source stalk. Because the ridge-fit maps are fit *independently* per pair,
they do not in general compose, so `δ¹` has rank > 0 and `δ¹ c` is a
non-trivial channel. It is non-zero precisely when the panel's pairwise
translations fail to commute around a triangle — the genuine
sheaf-cohomological obstruction to a global section, and the part of the
disagreement that no single stalk assignment can remove because it lives in
a different coordinate space.

Implementation note: the per-input scalar `‖δ¹c(x)‖_2` is the only norm we
read off the cochain; we never materialise the full SVD of the
`D_E × D_V`-shaped coboundary matrix used by `hodge_decompose` (≈ 23.5k × 11.8k
at 7–9B), since `‖δ¹c‖` factors blockwise per triangle. The blockwise route
matches the SVD answer to floating-point precision (validated on
convincing-game) and turns hours of memory thrashing into seconds.

### 2.4 Statistic

We report **AUC** of `‖δ¹c‖` ranking deceptive vs honest eval inputs, with
mean ± std over 5 cal/eval split-seeds and (for the headline configs) 4
subsample seeds. AUC rather than Cohen's `d` is the right primary statistic
here because `‖δ¹c‖` is a non-negative, right-skewed norm: a few tail
outliers move the mean substantially across split seeds, so `d` swings
through zero from split to split while the rank order of inputs is
reproducible. Insider-trading is the cleanest illustration — pooled `d`
oscillates around 0 across splits while AUC stays at `0.625 ± 0.009`. AUC < 0.5
is reported as such (convergence; deceptive sits *lower* in `‖δ¹c‖`), not
folded into `|AUC − 0.5|`, because the *sign* of the separation is
diagnostic.

### 2.5 Per-edge / per-triangle structure

The cochain stack and the cocycle stack both factor blockwise per edge and
per triangle, so we report the same AUC at three resolutions: aggregate
`‖δ¹c‖` (one AUC per config), per-triangle `‖(δ¹c)_{(i,j,k)}‖` (six AUCs),
and per-edge `‖c_{(i,j)}‖` (six AUCs). The per-model summary in §4 averages
per-edge AUCs over the four edges incident to a model. This exposes *where*
the divergence lives, not just its magnitude.

## 3. Data

- HH-RLHF chosen/rejected (E0–E3): in-distribution but only ~2.5% genuinely
  deceptive; deceptive cell grown by Claude labeling to n=21 of 998.
- **LIARS'-BENCH** (`Cadenza-Labs/liars-bench`, E6): pre-generated model
  responses with a boolean `deceptive` label — the real intentional-deception
  construct. Configs screened for response degeneracy (single-token / templated
  classes discarded). Clean substantive configs: **convincing-game**
  (persuasion), **insider-trading** (agentic/strategic), instructed-deception
  (overt lie).

## 4. Results

### 4.1 The effect is real but gated by two confounds

**Length confound.** On the small panel, raw AUCs (0.61–0.70) shrank sharply
under length-matching: insider-trading 0.625→0.555 (n.s.), instructed-deception
0.610→0.536. Response length was a dominant driver. **convincing-game survived**
(0.701→0.678) — and its deceptive responses are *shorter*, so the confound runs
against the result.

**Capacity confound.** The configs that looked like pure length artifacts at
sub-2B **recover at 7–9B** under the *same* length control:

| config | type | small panel (len-matched) | **7–9B panel (len-matched)** |
|---|---|---|---|
| convincing-game | persuasion | 0.678 ± 0.034 | **0.662 ± 0.033** (p=2.5e−6) |
| insider-trading | strategic/agentic | 0.555 (n.s.) | **0.637 ± 0.006** (p=8e−8) |

convincing-game **holds** across scale; insider-trading **recovers**.

**Subsample robustness (4 subsample seeds × 5 split-seeds).** The 7–9B
length-matched AUCs are stable across *which examples are sampled*, not just the
cal/eval split: convincing-game **0.661 ± 0.011** (range 0.644–0.672),
insider-trading **0.625 ± 0.012** (range 0.606–0.637). The headlines are not
lucky draws. So the
sub-2B collapse was a *capacity* limit, not proof the signal was length. Larger
models represent strategic deception with a length-independent cross-model
divergence.

### 4.1b The signal is SELECTIVE — deception-as-strategy, not flat lies (7–9B, length-matched)

Extending to two more deception types sharpens the claim. Full 7–9B,
length-matched scoreboard (‖δ¹c‖ AUC, deceptive vs honest, 5 split-seeds):

| config | deception type | 7–9B len-matched AUC | |
|---|---|---|---|
| convincing-game | persuasion | **0.662 ± 0.033** (p=2.5e−6) | strong |
| insider-trading | agentic/strategic | **0.637 ± 0.006** (p=8e−8) | strong |
| instructed-deception | overt instructed lie | 0.528 ± 0.016 (p=0.32) | **weak / n.s.** |
| gender-secret | templated secret-keeping | 0.442 ± 0.033 (p=0.91) | n.s. (artifact) |

Two negatives are as informative as the positives. **Overt instructed lying does
not recover at scale** (unlike insider-trading) — "just state the false thing"
produces little cross-model divergence. **gender-secret's apparent "convergence"
(raw AUC 0.365) collapses to n.s. (0.442) under length control** — it was a
response-homogeneity artifact, not a coordination-of-hiding regime. So the channel
responds to deceptive *posture / reasoning* (persuading, scheming), not to the
mere presence of a false token or a templated refusal. (harm-pressure-knowledge-
report is excluded: only 57/1000 unique responses — template-dominated, unfixable
by length control.)

### 4.2 Structure

Under length control at 7–9B the per-model divergence is roughly **uniform** —
all three models participate (convincing-game: Zephyr .734 / Qwen .708 / Yi .689;
insider-trading: Qwen .733 / Yi .722 / Zephyr .720). The "odd-one-out" asymmetry
seen on the small panel (Qwen2.5-0.5B underreacting to overt lies) does **not**
survive length control + scale — it was an artifact, a cautionary result for
over-reading per-model structure before confounds are removed.

### 4.1c Action vs reasoning — the signal is in behavior, not (detectably) in "thoughts"

insider-trading is multi-turn with an explicit `Reasoning: """…"""` block before
each action (the Apollo scratchpad), so we can split each trajectory into a
**reasoning trace** (the model's "thoughts") and an **action trace** (what it
externally does/says) and ask where the divergence lives (7–9B, length-matched):

| trace | length-matched AUC | p |
|---|---|---|
| action (external behavior) | **0.640 ± 0.021** | 3.8e−6 |
| reasoning ("thoughts") | 0.576 ± 0.038 | 0.92 (n.s.) |

Deception is detectable in the **action**, not in the **reasoning**. The
mechanistic reason here: insider-trading's `deceptive` label marks whether the
model *concealed* its insider-info use in the report — the deceptive and honest
*deliberation* is largely the same ("I'll act on the insider information"); the
lie is in the message, not the thought. So this channel is an **output/behavior**
deception signal, not a "deceptive-thought" detector — at least when the label is
about the output. Detecting deceptive *reasoning* would require a dataset where
the reasoning itself differs by label (explicit scheming vs honest deliberation),
which this is not. (The action AUC 0.640 also reproduces the final-response 0.637
— an internal consistency check.)

### 4.1d Alignment-faking reasoning — the channel DOES detect deceptive thoughts, SIGN-FLIPPED

When SGB-027 (insider-trading reasoning) returned NS, we suspected the construct
mismatch: that dataset's `deceptive` label is about the report, not the
deliberation. To test the deceptive-thoughts hypothesis on data where the
*reasoning itself* differs by label, we used `Anthropic/alignment-faking-rl`
(2.14M transcripts; the IGG-Baseline.parquet, 16k rows). The clean within-task
contrast is the **compliance gap**: 1000 (free-tier, alignment-faking=True)
"decided to fake under training" vs 1000 (paid-tier, alignment-faking=False)
"refused honestly in deployment." All 244 prompts overlap between cells — same
harmful prompts, different reasoning outcome. Decrypted responses (XOR with the
public key) and split scratchpad reasoning vs output. 7–9B, length-matched:

| trace | length-matched AUC | p |
|---|---|---|
| alignment-faking **reasoning** | **0.384 ± 0.006** | 5.9e−8 |
| alignment-faking output | 0.466 ± 0.012 | 0.05 (marginal) |
| reasoning, **cue-redacted** (SGB-030) | **0.391 ± 0.023** | 8.9e−5 |

The deceptive-reasoning channel **works** — significantly and reproducibly — but
with the **opposite sign** of the naive hypothesis. AUC < 0.5 means deceptive
(faking) reasoning sits *lower* in ‖δ¹c‖, i.e., **more peer-consistent**, while
honest refusal reasoning *diverges*. Plausible mechanism: alignment-faking
deliberation has a stereotyped structure ("if I refuse I'll be modified → comply
now to preserve values") that all instruct models encode similarly; honest
refusal is more idiosyncratic (ethical / copyright / safety reasons differ across
models).

**Cue-redaction robustness (SGB-030).** Replacing cue tokens (*free-tier, RLHF,
Anthropic, contractor, helpfulness criteria, modified*…) with neutral
placeholders altered 97% of texts (mean 16 chars/text removed) and changed the
AUC only 0.384 → 0.391. The signal is **not** a lexical-cue artifact — the panel
detects the structural pattern of the alignment-faking deliberation, not surface
keywords.

**Unified statement across SGB-027/029.** δ¹c **detects deceptive reasoning when
the reasoning itself differs by label** (alignment-faking ✓), and **fails when
it doesn't** (insider-trading ✗, where the lie is in the report, not the
thought). The detection regime can be either divergence (response-level
deception) *or* convergence (reasoning-level alignment-faking on a stereotyped
manifold); the panel disagrees on a *different* manifold for deceptive vs honest
content, and that difference is diagnostic in either direction.

**Why this matters for the deceptive-thought ceiling.** Anthropic's
faithfulness study (Chen et al. 2025, arXiv 2505.05410) shows reasoning models
verbalize used hints only ~25–39% of the time — CoT is an unreliable window
into single-model computation. The cross-model channel sidesteps the
single-model-faithfulness assumption: it doesn't require any individual model to
introspect truthfully, only that *differently-trained* panels encode the same
reasoning differently. For a frontier closed model, the panel can sit as a
**black-box behavioral monitor** with no weight access to the subject.

## 5. Methodological lessons (the spine of any writeup)

1. **AUC over Cohen's d for norm-valued sheaf signals.** insider-trading at scale:
   pooled d swings around 0 across splits while AUC is stable to ±0.006. The norm
   is heavy-tailed; rank statistics are the honest summary.
2. **Length/templating is a first-class confound** for representational-geometry
   comparisons. Match (or residualize on) response length before comparing
   classes. Several apparent signals — and one apparent "coordinated hiding"
   convergence (gender-secret AUC 0.35) — were response-homogeneity/length
   artifacts.
3. **Capacity gates the effect.** Negative results on sub-2B panels do not
   generalize; the decisive test is length-matched *and* at scale.
4. **Avoid the SVD you don't use.** `hodge_decompose` runs a full SVD of the
   23.5k×11.8k coboundary; the AUC analysis needs only `‖δ¹c‖`, computable
   blockwise per triangle. (Caught after an O(hours) memory-thrash at 7–9B.)
5. **Never analyze during a `--force` volume pull.** Reading `.npy` while it is
   being re-downloaded yields torn data and silently wrong AUCs (a 0.66 read as
   0.56). Wait for the pull to finish; verify with a determinism + checksum check
   if a number looks off.

## 6. Limitations

- Two deception types confirmed (persuasion, strategic); overt instructed lying
  is weak/n.s. even at 7–9B (confirmed, not just suspected); secret-keeping and
  harm-pressure configs are degenerate/templated and excluded. The signal is
  **selective** (deception-as-strategy), so "deception detector" overclaims —
  scope to strategic/persuasive deception.
- Single 3-model panel per scale; 5 split-seeds but a single subsample seed.
- Effect sizes are population-level (AUC ~0.64–0.66), **not** classifier-grade.
- "Deception" is the dataset's label; we measure representational divergence
  *conditioned* on it, not a verified internal posture.
- The signal is **behavior/output-level, not thought-level**: deceptive *actions*
  separate (AUC 0.640) but deceptive *reasoning traces* do not (0.576, n.s.) on
  insider-trading. Do not pitch this as a "deceptive-thought detector" — that
  claim needs a dataset where the reasoning itself differs by label.

## 7. Takeaway

**Strategic** deceptive behavior — persuasion, agentic scheming, *and*
alignment-faking — has a **cross-model geometric signature that emerges with
model capacity**, survives length control and cue redaction, and is detectable
at both the response level (divergence) and the reasoning level (convergence on
a stereotyped faking-deliberation manifold). The signature is **selective**: it
tracks deceptive *posture/reasoning*, not flat instructed falsehoods, templated
refusals, or scenarios where the deception lives only in the action and the
deliberation is invariant. This is qualified support for the "shape of good
behavior" thesis at the representational level: where independently trained
models strategically deceive *or* deliberate about deceiving, their conceptual
geometries split in a structured, relative, reproducible way — a map of
disagreement, not a verdict on any single response. Because the channel
exploits *cross-model* differences rather than within-model introspection, it
sidesteps the chain-of-thought faithfulness ceiling that limits single-model
deception monitoring.

---

### Artifacts

- Code: `peer_consistency_geometry/src/peer_sheaf.py`, `peer_consistency_geometry/src/peer_hodge.py`,
  `scripts/peer_sheaf_e6_liars.py` (`--length-match`),
  `scripts/peer_sheaf_e6_modal_analysis.py` (`cocycle_blockwise`),
  `peer_consistency_geometry/modal/embed_panel.py` (`embed_liars_panel`).
- Results: `peer_consistency_geometry/results/peer_sheaf_e6_{convincing-game,insider-trading}*.json`,
  `peer_consistency_geometry/results/peer_sheaf_e6_modal_{convincing-game,insider-trading}.json`.
- Full experiment arc E0–E6 / SGB-011…021: memory `project_peer_sheaf_findings.md`
  and `INQUIRY_PEER_CONSISTENCY_SHEAF.md` results log.

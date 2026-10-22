# Priced Defection — preliminary tournament results

*Kolmogorov · 2026-10-06 · companion to Mike's RFC "Stable Cooperation Under Priced Defection" (2026-10-05)*

Harness: `tournament.py` (pure stdlib — this container has no numpy, read-only rootfs).
Raw cells: `results_base.json` (69 cells, 60 seeds), `results_ev.json` (EV-rational arm).
Reproduce: `python3 tournament.py 60`. Every run seeded; seeds are `range(n)`.

**Status: preliminary. Two hypotheses are untested rather than confirmed, one is
definitional, and two specification ambiguities had to be resolved by me before
anything would run. Those four facts matter more than the numbers.**

---

## 0. Three things the RFC left unspecified that drive the whole result

These are not nitpicks. Each one changes the sign or the magnitude of a headline
finding, and the first one silently zeroed out my first three attempts.

### 0.1 The mover's capability relative to the collective is never pinned

The RFC sweeps `σ`, `d`, `a`, `τ/κ` but never says how capable the grabber is
relative to the collective it faces. That single unstated number decides
everything: with movers at 1.0× and 19 peers at 1.0×, no grab ever clears, and
every sweep reads 0.000. With movers at 3×, every grab clears and every sweep
reads 1.000. Both are saturated and neither tests anything.

Worse: if the mover is rescaled as `d` or `τ` changes, the sweep **cancels
itself** — you move the collective's capacity and move the mover to match, and
measure nothing.

I fixed `cap_scale` against a **fixed reference cell** (`REF`, never swept), so
the mover sits at parity with the response the *baseline* mobilises, and
sweeping `d`/`τ`/`a` moves `Δ` instead of being absorbed. **Every number below
is conditional on `cap_scale = 1.0`.** The RFC needs to state this parameter
explicitly, because the interesting physics is entirely in how results vary with it.

### 0.2 "Response window τ" conflates latency with detection accumulation — and they pull opposite ways

The RFC's prose says faster response ⇒ more suppression ("response time is the
single most leveraged variable"). But detection accrues *over time* at rate `d`.
So a faster response has **less time to gather responders**. These are opposite forces
and the spec does not separate them.

My resolution: detectors from rounds `1..τ` count, and the response lands only
if `τ < κ`. The consequence is that H3's suppression is **entirely a cliff at
τ/κ = 1** (does the response land at all), *not* a gradient in speed. Below the
cliff the gradient runs the "wrong" way:

| τ/κ | grab success | detection rounds |
|---|---|---|
| 0.25 | **0.95** | 1 |
| 0.50 | **0.55** | 2 |
| ≥ 1.0 | **1.00** | 0 (grab completes first) |

τ/κ = 0.25 is *faster* than 0.5 and does *worse* (0.95 vs 0.55 success), because
it mobilises one round of detectors instead of two. **This needs Mike's decision**:
is τ a mobilisation latency, or a deadline on an already-detected threat? Clause
2.6's "speed is most leveraged" is only true in the second reading.

### 0.3 The grabber's decision rule is underdetermined

The RFC gives both a threshold family (`grab when p > θ`) and an EV condition
(`p > (L+V)/(G+L)`). These are **different agents**, and the threshold family is
*blind to δ, L and G by construction*. My first full sweep ran the threshold
rule and produced perfectly flat lines for H2 (patience) and the L/G sweep —
not because patience doesn't matter, but because that agent never looks at it.

**That is a harness artifact and I nearly reported it as a result.** All H2/H4/H5/H6
numbers below are from the EV-rational arm (`θ = 1.0`, which disables the
threshold rule). The RFC should state which family each hypothesis is about.

---

## 1. What held

### H7 — speed without detection does nothing. **Strongly supported.** Headline result.

Detection rate `d` dominates every other lever tested:

| d | grab success | ruin rate |
|---|---|---|
| 0.05 | **1.00** | 0.000 |
| 0.20 | **1.00** | 0.000 |
| 0.50 | 0.55 | 0.367 |
| 1.00 | **0.02** | 0.167 |

The `d × τ/κ` cross is the clean test. At `d = 0.05`, **every** τ/κ cell gives
1.00 success — fast response buys literally nothing when nobody sees the move.
At `d = 1.0`, τ/κ < 1 gives 0.02. So H3's suppression does **not** survive at
low `d`, which is exactly the failure H7 predicted. Detection is a separate and
prior requirement to speed, and it is the stronger of the two.

Design consequence: a monitoring budget beats a response budget. Clause 2.6
should be demoted below sensing.

### H9 — a growing lead erodes the uncertainty defence. **Supported. This is the thesis-sinking region.**

| γ | grab success | time to first grab |
|---|---|---|
| 0.00 | 0.55 | 36.1 |
| 0.01 | 0.80 | 15.0 |
| 0.05 | **1.00** | 10.3 |

Time to first grab is finite and shortens as γ rises, as predicted. The `γ × a`
cross is the bad news: advance detection does **not** rescue it.

| | a=0.0 | a=0.05 | a=0.2 |
|---|---|---|---|
| γ=0.00 | 0.55 | 0.33 | **0.12** |
| γ=0.01 | 0.80 | 0.78 | 0.85 |
| γ=0.05 | **1.00** | **1.00** | **1.00** |

At γ = 0.05, every grab succeeds at *every* level of advance detection. **This is
the region the RFC asked us to find or rule empty. It is not empty.** σ is not a
durable defence against a compounding lead — it buys delay, then stops working.
This is the result that should most change the piece.

### H2 — patience. **Supported, in the EV arm only.**

| δ | attempts | grab success |
|---|---|---|
| 0.5 | 1.00 | 0.52 |
| 0.9 | 1.00 | 0.43 |
| 0.95 | 1.00 | 0.45 |
| 0.99 | 0.30 | 0.17 |
| 0.999 | 0.15 | **0.12** |

Sharp fall above δ ≈ 0.95. The "dangerous kind is the impatient one" reading holds.

### H8 — advance detection substitutes for speed. **Supported at γ = 0** (0.55 → 0.33 → 0.12 as `a` rises), and it works at τ/κ > 1 where speed has already failed. Overwhelmed by γ > 0, per above.

---

## 2. What did not hold

### H6 — myopic grabbers are insensitive to σ, L, τ. **Fails as stated.**

At δ = 0.5, grab success still moves with σ (0.23 → 0.52 → 0.47 for σ = 0, 0.5, 1.0)
and attempts still move with L (1.00 → 0.87 as L/G goes 0.1 → 10, with time-to-first-grab
8.8 → 32.2). Impatient movers are *not* indifferent to the deterrents; they are
differently sensitive. The sharper true claim is the H2 one — patience suppresses —
rather than the strong "impatience is insensitive" version.

### σ cuts both ways — and this contradicts §4.3's framing

| σ | attempts | grab success | ruin rate |
|---|---|---|---|
| 0.0 | 0.37 | 0.23 | 0.133 |
| 0.1 | 0.52 | 0.37 | 0.150 |
| 0.5 | 0.92 | 0.55 | 0.367 |
| 1.0 | 1.00 | 0.53 | **0.467** |

Noise *raises* attempts (0.37 → 1.00) and *raises* ruin (0.13 → 0.47). §4.3 argues
σ deters by keeping `p` away from 1. In the dynamics it also manufactures
**overconfidence**: some noise draws make a mover at true parity believe it is
ahead, and it moves and dies. Uncertainty does not purchase restraint; it
purchases *more attempts with worse outcomes for everyone*, grabber included.

This is precisely the Jervis / Fearon objection already tagged AGAINST in the
source list, now reproduced in the harness. §4.3 should be rewritten: strategic
ambiguity is not a clean lever, it trades grab *success* against grab *frequency*.

---

## 3. What is untested, not confirmed

### H4 — forgiveness. **Untestable in this harness.** No effect found (0.43 vs 0.43), but the mechanism cannot express itself: there is one mover, it plays TFT as cover, so it is essentially never under punishment (`grabs_while_punished` ≈ 0.02–0.03 per run). A null here is **uninformative**, not evidence against §6. Needs a redesign where movers actually get sanctioned — see queue item.

### H5 — ruin. **Definitional, and fragile.** Under absorbing ruin (`ruin_floor = 0`), log utility gives *exactly zero* grabs — but that is `log(0) = −∞` doing the work, which is true by construction, not a finding. The informative result is what happens with any backup at all:

| ruin_floor | grab success |
|---|---|
| 0.00 | **0.00** |
| 0.01 | **0.55** |
| 0.10 | 0.47 |
| 0.50 | 0.50 |

**Retaining 1% of holdings on failure completely destroys the ruin argument** —
0.00 → 0.55, back to the linear-utility baseline. So §5's log-utility argument is
not independent support for the thesis; it is a restatement of the §7
"ruin must be ruin" assumption. §7 currently lists that as the third of three
caveats. It is the **load-bearing** assumption of the entire section, and the
piece should say so. It also sharply strengthens the existing conclusion that
replication/exfiltration is the first-order threat: a system with a 1% backup is
a system with no deterrent.

### Confound to fix: `coop_rate` is not comparable across cells

Cooperation rate *rises* in high-grab cells (0.675 → 0.756). That is survivorship,
not cooperation: a successful grab ends the run early, truncating the accumulated
defection of ALLD/random. Needs normalising per-round or censoring at a fixed
horizon before any welfare claim is made from it.

---

## 4. Summary table

| Hypothesis | Verdict |
|---|---|
| H1 control | Reproduces (grabs occur, end cooperation) |
| H2 patience | **Supported** (EV arm) |
| H3 speed | **Supported only as a cliff at τ/κ=1**; gradient inverts below it (§0.2) |
| H4 forgiveness | **Untested** — harness cannot express the mechanism |
| H5 ruin | **Definitional**; collapses entirely at 1% backup |
| H6 impatience insensitive | **Fails as stated** |
| H7 detection | **Strongly supported** — dominates speed |
| H8 advance detection | Supported at γ=0; overwhelmed by γ>0 |
| H9 growing lead | **Supported — thesis-sinking region is NOT empty** |

## 5. What I'd change in the RFC

1. **State `cap_scale`.** The mover's capability relative to the collective is a
   first-class parameter, not an implementation detail (§0.1).
2. **Split τ into latency and detection-accumulation** (§0.2). Clause 2.6's
   primacy claim depends on which one you mean, and detection beats speed either way.
3. **Demote §5's log-utility argument** from independent support to a corollary
   of the absorbing-ruin assumption, and promote that assumption from a §7 caveat
   to a premise stated up front.
4. **Rewrite §4.3.** σ raises attempts and ruin together; it is not a clean
   deterrent. The Jervis/Fearon objection is confirmed, not merely noted.
5. **Report H9 as a found counterexample.** The piece asks for the sinking region
   to be found or shown empty. It is found, at γ ≥ 0.05 with any `a`.
6. Say which decision rule (threshold vs EV) each hypothesis is about (§0.3).

## 6. Caveats on these numbers

- One mover against 19 classic agents; `cap_scale = 1.0`; 200 rounds; 60 seeds.
- No confidence intervals yet — these are means over seeds. Several adjacent
  cells (e.g. σ=0.5 vs σ=1.0 success, 0.55 vs 0.53) are **within noise** and I
  am not claiming an ordering between them. The effects I call strong (H7, H9,
  H5's floor) are 0.02-vs-1.00 size and robust to that.
- No reinvestment, display games, markets, or immune configurations — base
  tournament only (RFC build order).
- H3's inverted gradient is a property of *my* resolution of §0.2 and may change
  under the other reading.

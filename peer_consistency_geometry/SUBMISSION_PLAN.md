# Submission Plan — Peer-Consistency Deception Divergence

*Last touched 2026-05-28. Companion to [`../writing/peer_consistency_deception_divergence.md`](../writing/peer_consistency_deception_divergence.md).*

## Recommended venue

**Primary**: NeurIPS 2026 Workshop short paper (4–6 pp), prioritising in this order:

1. **SoLaR — Socially Responsible Language Models** *(if held in 2026; it has been a fixture)*.
   Strongest topical fit. The paper's central object is a deception-detection
   tool that respects the model-faithfulness limitations of single-model
   introspection — squarely in SoLaR's scope. Reviewers will be primed for the
   relative/black-box framing.
2. **ML Safety / SafeML workshop** *(or whatever the 2026 NeurIPS safety-track
   workshop is named)*. Good secondary fit. Deception-detection sits well in
   safety-ops audiences; the methodological lessons (length confound,
   capacity gating, AUC over Cohen's d) are reusable beyond this paper.
3. **ATTRIB / Mechanistic Interpretability workshop**. Tertiary fit. We don't
   probe internals, but the cross-model representational-geometry framing
   may interest mech-interp reviewers. Mention the SGB-028 within-model
   probe distillation as future work to bridge.

The specific 2026 workshop list typically lands in mid-summer
(per [NeurIPS 2026 Call for Workshops](https://neurips.cc/Conferences/2026/CallForWorkshops));
re-check titles before submitting and pick the live workshop closest to SoLaR's
historical scope.

**Backup / parallel**: drop on **arXiv (cs.LG, cross-list cs.AI)** at the same
time as workshop submission, ideally a week or two before the workshop CFP
deadline. The cross-model framing + the alignment-faking sign-flip + the
cue-redaction defense are all citation-worthy independent of the workshop
outcome.

**Journal follow-on**: **TMLR** for the longer version, after SGB-024
(directional pattern at scale) and a second intentional-deception dataset
(SGB-026) close the generality gap. Aim for Q3 2026 once those land.

## Key dates (NeurIPS 2026)

Per [NeurIPS 2026 conference page](https://neurips.cc/Conferences/2026/) and
[Workshops Guidance](https://neurips.cc/Conferences/2026/WorkshopsGuidance):

- Conference: **Dec 11–13, 2026** (Sydney / Paris / Atlanta hybrid).
- Mandatory workshop author notification: **Sep 29, 2026**.
- Workshop CFP deadlines vary, but historically fall **mid-August to
  mid-September** for a Sep 29 notification window.

**Working backward** from Sep 1 (a typical workshop deadline):
- **By July 31**: writeup converted to NeurIPS LaTeX (the format-prep block below).
- **By Aug 15**: figures finalized, internal review with Mike, arXiv first.
- **By Aug 30**: workshop submission.

If we slip past September, SoLaR/SafeAI are often re-run at ICLR 2027 workshops
(Apr–May submission), so a workshop slot is still available.

## Format and page budget

NeurIPS 2026 main conference template (LaTeX, `neurips_2026.sty`); workshops
use the same template with the workshop's specific instructions overriding
page count. Plan for **6 pages + unlimited references + 4 pp appendix**.

Section page budget (rough):

| section | pp | content |
|---|---|---|
| Abstract + §1 framing | 0.5 | what we are / are not claiming, relative-not-absolute |
| §2 method | 1.5 | self-contained sheaf, why cocycle, AUC, structure |
| §3 data | 0.5 | LIARS'-BENCH config screening + alignment-faking-rl |
| §4 results | 2.0 | scoreboard, length/capacity confounds, action-vs-reasoning, sign-flip |
| §5 lessons | 0.5 | AUC > Cohen's d, length as first-class confound, capacity gating |
| §6 limitations + §7 takeaway | 1.0 | scope, CoT faithfulness sidestep, future work |
| **total** | **6.0** | + references + appendix |

The full markdown draft is currently **~6,000 words** plus 3 figures and 4
tables. That maps cleanly to 6 NeurIPS pages with figures inline.

## Conversion checklist (markdown → LaTeX)

In rough order. Items marked ✓ are already done in the source.

- [ ] Set up `neurips_2026.sty` skeleton with author block and keyword line.
- [ ] Convert §1 framing — keep as-is.
- [✓] §2 self-contained (AR-004): the markdown source now inlines the
      vacuous-harmonic + cocycle-channel motivation; LaTeX conversion only
      needs equation-environment formatting.
- [ ] §3 data: keep config-screening table; consider a small appendix with
      the response-degeneracy criteria and counts (single-token, single-char,
      unique-prefix counts) for full transparency.
- [ ] §4 collapse the two duplicate `4.1d`s. The newer one (with
      cue-redaction) is the keeper; the older one was already removed in
      AR-004's cleanup. Confirm the section renumbering before LaTeX (current
      labels 4.1, 4.1b, 4.1c, 4.1d, 4.2 should become 4.1–4.5).
- [ ] §5 lessons: trim "race-condition discipline" — it's a great memory item,
      but a paper section should keep it to one sentence in a reproducibility
      appendix, not a full lesson.
- [ ] §6/§7: tighten. The "doesn't need the subject's weights" point in §7 is
      the punchline; make sure it survives a full editing pass.
- [ ] Figures: `figures/fig1_sheaf_complex.pdf`, `fig2_auc_scoreboard.pdf`,
      `fig3_reasoning_vs_action.pdf` — already PDF, drop straight into LaTeX.
      Captions need to be written (currently in-figure titles do that job).
- [ ] References: convert inline citations (Greenblatt et al. 2024, Chen et al.
      2025 — arXiv 2505.05410) to proper bibtex. Cite at minimum:
        - Greenblatt et al. 2024 (alignment-faking demonstration)
        - Chen et al. 2025 (CoT faithfulness, 2505.05410)
        - Anthropic Apollo / Meinke et al. 2024 (insider-trading scheming eval)
        - Cadenza-Labs LIARS'-BENCH (dataset card)
        - Apollo Research scheming evaluations
        - Jiang et al. 2011 (HodgeRank background, optional)

## Open scientific gaps to address before submission

Decisive results are in; what's left is robustness, not central findings.

- **SGB-024 — directional structure at scale (length-controlled).** The
  per-edge AUC pattern across configs is already in the `results/`
  JSONs; we just need one analysis pass to extract "which model-pair edges
  reliably separate per deception type" and add 1–2 sentences in §4.2.
  Doable in an afternoon. Strengthens the "where the disagreement lives"
  narrative.
- **SGB-026 — a second intentional-deception dataset.** Optional for the
  workshop short version (we already test 3 datasets — LIARS'-BENCH,
  insider-trading split, alignment-faking-rl). Required for TMLR. Cheapest
  path: PKU-Alignment/DeceptionBench scenarios with paired honest/deceptive
  responses generated via API.
- **One-paragraph reviewer-anticipation in §6**: the obvious objection is
  "you've shown a population-level signal, not a per-instance detector." The
  honest response is *yes, and we say so explicitly* — make sure §1 framing
  and §6 limitations both make this load-bearing.

## Authorship and attribution

Per the [`repo_publication_split`] memory, this repo is the canonical public
artifact. Lead author: **Michael Lee** (`michael@oasis-x.io`). If any of the
SGB-016→031 arc was co-author-able, declare contributions in a footnote.

## Logistics: submission day

- LaTeX source in `peer_consistency_geometry/paper/` (to be created at
  conversion time).
- Compile with `pdflatex` against `neurips_2026.sty`.
- Validate against the workshop's CFP page (page count, anonymous / blind,
  supplementary policy).
- arXiv submission: cross-list `cs.LG`, `cs.AI`. Tag with `alignment`,
  `interpretability`, `evaluation`.
- Add the arXiv link back to `writing/peer_consistency_deception_divergence.md`
  and to the top-level `README.md` once the pre-print is live.

## Confidence and remaining risk

Result strength is high: length-controlled, scale-robust, subsample-stable,
cue-robust, selective signal across two reasonably independent constructs
(response-level deception on LIARS'-BENCH, reasoning-level alignment-faking on
Anthropic's dataset). The biggest reviewer risk is the "single benchmark per
construct" objection on the response side; the cheapest mitigation is the
SGB-024 directional analysis (adds depth without new compute) and a
plain-spoken §6 limitations paragraph.

Workshop acceptance probability given the result quality + topical fit:
high. Reject-then-resubmit fallback path is intact (ICLR 2027 workshops,
TMLR).

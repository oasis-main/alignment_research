# NeSy 2026 Submission — Metadata for OpenReview Upload

> Use this document when filling out the OpenReview submission form.
> The PDF and supplementary zip are ready in this directory. The
> human/agent doing the upload should copy the fields below into the
> corresponding OpenReview form inputs.

## Title

**TLTS-Compilation: A Neurosymbolic Framework for Type-Safe and Verifiable Transformers**

## Abstract

Verifying that a language model stayed within the rules of a
structured domain—that it did not invent an absent relation or skip
a required step—is currently faith-based. We frame the problem as
compiling a typed labeled transition system (TLTS) into a
transformer, and show that two recent threads—typed attention and
program-compiled transformers—are the same construction, differing
only in whether the transition relation is deterministic. The
framework names three points in the inference pipeline where the
rule can be enforced (in-FFN gates, pre-decoder logit masks,
post-hoc audit), each with a distinct cost profile. A synthetic
harness confirms its predictions, including a non-obvious one:
attention-layer reachability masking is not enough for trajectory
soundness; the decoder must also check direct-edge admissibility.
We deliver a JSON audit-certificate format that a third party can
re-check without model weights, and argue it should become a
publication norm for compiled-transformer work. Trained-model
evaluation is future work.

## Keywords

`neurosymbolic AI`, `type-safe attention`, `compiled transformers`,
`category theory`, `constrained decoding`, `verification`, `Olog`,
`labeled transition systems`, `auditable AI`

## Track / area selection

**Primary track**: Neurosymbolic Architectures (or closest equivalent in OpenReview taxonomy).

**Secondary fits**: Verification/Interpretability, Reasoning with LLMs, Knowledge Representation in Neural Models.

## TL;DR (one sentence, 232 chars — under OpenReview's 250-char limit)

We frame typed attention and compiled transformers as one
construction, identify three loci where domain rules can be enforced
(FFN gates, logit masks, post-hoc audit), and ship a JSON
certificate re-checkable without model weights.

## Submission type

**Full paper** (10-page limit; current PDF is 9 pages including references).

## Suggested reviewers (community fit)

The OpenReview form may ask for suggested reviewers or area chairs.
Plausible candidates by topic — the agent uploading should sanity-check
each name against the OpenReview reviewer pool and conflict-of-interest rules.

- **Neurosymbolic AI**: Artur d'Avila Garcez, Luc De Raedt, Pascal Hitzler, Michael Spranger
- **Compiled / mechanistic transformers**: David Lindner, Neel Nanda, Arthur Conmy
- **Constrained decoding**: Brandon T. Willard, Saibo Geng
- **Category theory in ML**: David Spivak, Bruno Gavranović

## Conflict declarations

To be filled in at upload time based on author affiliations.
Anonymous draft does not contain author info.

## Files to upload

| File | Path | Purpose |
|------|------|---------|
| Main paper PDF | `main.pdf` | The 9-page submission |
| Supplementary | `supplementary.zip` | Code + results + sample certificate (build below) |

## Build supplementary zip

```bash
cd /Users/Michaellee/Documents/Runes/ai_research/topics/structure_of_clear_thinking/papers/nesy_submission
zip -r supplementary.zip supplementary/
```

## Pre-upload checklist

- [ ] PDF compiles cleanly: `pdflatex main.tex; bibtex main; pdflatex main.tex; pdflatex main.tex`
- [ ] PDF page count ≤ 10 (excluding references): currently **7.5 content + 1.5 refs = 9 total**
- [ ] Header reads "Author names withheld" (anonymized): **confirmed**
- [ ] No personal identifiers in PDF, .tex, .bib, or supplementary files: **confirmed via grep**
- [ ] Supplementary code runs without errors via project venv: **confirmed for all 6 scripts**
- [ ] Sample audit certificate present in supplementary: **confirmed**
- [ ] Bibliography resolves all citations: **confirmed (12 references, all rendered)**

## Post-acceptance / camera-ready actions

1. Switch `\documentclass[anon]{nesy2026}` → `\documentclass[final]{nesy2026}` in `main.tex`.
2. Fill in author block (currently a `\clearauthor{...}` template not rendered under `[anon]`).
3. De-anonymize the `constrained_decoding` reference in `references.bib` to point at the actual codebase.
4. Optional: add acknowledgments via `\acks{...}`.
5. Re-compile and submit final PDF via OpenReview's camera-ready form.

## Phase 2 deadlines (for reference)

- Abstract due: **2026-06-09**
- Paper due: **2026-06-16**
- Notifications: 2026-07-08

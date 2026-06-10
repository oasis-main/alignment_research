# TLTS-Compilation

*A neurosymbolic framework for type-safe and verifiable transformers.*

This directory holds the paper, supplementary code, and audit-certificate
format for a single construction that unifies two recent threads in
verifiable transformer architectures: ontology-gated attention and
program-compiled transformers.

## What's in here

| File | Purpose |
|------|---------|
| [`main.pdf`](main.pdf) | The 9-page paper (NeSy 2026 submission, double-blind anonymous) |
| [`main.tex`](main.tex) | LaTeX source |
| [`references.bib`](references.bib) | Bibliography |
| [`supplementary/`](supplementary/) | Code, experimental results, sample audit certificate |
| [`supplementary.zip`](supplementary.zip) | Same supplementary as a zip for upload |
| [`SUBMISSION_METADATA.md`](SUBMISSION_METADATA.md) | Title, abstract, TL;DR for the OpenReview form |

## The core idea

Verifying that a language model stayed within the rules of a structured
domain — that it did not invent an absent relation or skip a required
step — is currently faith-based. We frame the problem as **compiling a
typed labeled transition system (TLTS) into a transformer**, and show
that two recent threads — typed attention and program-compiled
transformers — are the same construction, differing only in whether the
transition relation is deterministic.

The framework names three points in the inference pipeline where the
domain rule can be enforced:

1. **In-FFN gates** — bake the transition relation into FFN rows
2. **Pre-decoder logit masks** — constrained decoding against the
   admissible label set
3. **Post-hoc audit** — re-check the trace against the TLTS

Each has a distinct cost profile, and the right architecture is usually
a combination, not a choice. A non-obvious prediction the framework
makes: attention-layer reachability masking alone does not suffice for
trajectory soundness — the decoder must also check direct-edge
admissibility.

## What you can verify

The supplementary harness checks the framework's predictions on a
synthetic ontology. Specifically:

- The verifier catches every constructed-invalid trajectory on the
  e-commerce ontology
- The locus-comparison experiment (B vs. C) confirms the
  necessary-but-insufficient claim about attention-layer masking
- The cyclic-stress and topology-sweep experiments characterize
  framework behavior under adversarial graph structure
- A sample [JSON audit certificate](supplementary/sample_audit_certificate.json)
  shows the format a third party can re-check without access to model
  weights

Trained-model evaluation is the next experiment — what the prediction
*economic substitution of ontology engineering for scale in
domain-specific deployment* actually testable means in practice.

## Reproducing the supplementary

```bash
git clone https://github.com/oasis-main/alignment_research
cd alignment_research/tlts_compilation/supplementary

# Each experiment is a self-contained Python script
python experiment_loci_comparison.py
python experiment_compiled_subolog.py
python experiment_cyclic_stress.py
python experiment_topology_sweep.py
python experiment_real_attention_b.py
python verification_certificate.py
```

## Blog series

The narrative arc of how this framework came together — from
hallucinations to typed attention to compiled programs to audit
certificates — is documented in the public blog series:

1. [Why Your LLM Hallucinates](../writing/01_why_llms_hallucinate.md)
2. [Attention, But Make It Type-Safe](../writing/02_type_safe_attention.md)
3. [From Proofs to Programs to Text](../writing/03_proofs_to_text.md)
4. [Building an Auditable AI](../writing/04_building_auditable_ai.md)
5. [Compiling Programs Into Attention](../writing/05_compiling_programs_into_attention.md)

## Status

- **Venue:** NeSy 2026 (Main Track Phase 2)
- **Anonymization:** PDF is anonymous; this README and the supplementary
  README are public-facing
- **Camera-ready:** Author block, acknowledgments, and de-anonymized
  `constrained_decoding` reference are filled in upon acceptance

# Supplementary Materials

Reference code, full experimental results, and a sample audit
certificate for the paper "TLTS-Compilation: A Neurosymbolic
Framework for Type-Safe and Verifiable Transformers."

All Python files run via `python <file>.py` and use only NumPy
(no PyTorch, no GPU). Reference TLTS, priors, and variants are
defined in `experiment_loci_comparison.py`.

## Files

| File | Purpose |
|------|---------|
| `experiment_compiled_subolog.py` | One-hot reference implementation of the in-FFN locus on a functional sub-Olog (paper §4) |
| `experiment_loci_comparison.py` | A / B′ / C / D synthetic-prior harness on the e-commerce TLTS (paper §5.1) |
| `experiment_topology_sweep.py` | Parameterized TLTS family; (C) vs (D) crossover at fn-ratio ≈ 0.2 (paper §5.3) |
| `experiment_cyclic_stress.py` | (B′) collapse under universal reachability on cyclic TLTS (paper §5.2) |
| `experiment_real_attention_b.py` | Validation against the production OntologicalAttention layer (paper §5.4) |
| `verification_certificate.py` | Audit certificate emitter and independent verifier (paper §6) |
| `experiment_results.md` | Full experimental results with extended discussion |
| `verification_protocol.md` | Detailed verification protocol design notes |
| `procedural_ontology.md` | Notes on the procedural-compilation construction |
| `sample_audit_certificate.json` | Example certificate output, ready for verifier input |

## Reproducing main paper tables

Table 2 (variant comparison): `python experiment_loci_comparison.py`

Table 3 (cyclic stress): `python experiment_cyclic_stress.py`

Table 4 (topology sweep): `python experiment_topology_sweep.py`

§5.4 numbers (real-attention validation): `python experiment_real_attention_b.py`

(The real-attention test imports `OntologicalAttention` from a
parent path, so it requires the codebase referenced in the paper.
The other scripts are self-contained.)

## Verifier demo

```bash
python verification_certificate.py
```

Demonstrates the certificate emitter, independent verifier,
tampering detection (state_out → invalid type), and TLTS-drift
detection (modified δ caught by both fingerprint and per-step
checks).

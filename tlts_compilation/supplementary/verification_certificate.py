"""
verification_certificate.py

Emits per-trajectory JSON audit certificates implementing the
four-step verifier of §5.2 of papers/tlts_compilation.md.

A certificate is what a TLTS-compiled transformer ships alongside
its output to make trajectory-soundness independently checkable.
The format is deliberately simple: any verifier with the TLTS in
hand can re-run the checks without understanding model internals.

Run a demo:
    venv/bin/python verification_certificate.py
"""

from __future__ import annotations
import json
import time
import hashlib
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
import numpy as np

from experiment_loci_comparison import (
    TLTS, Prior, good_prior, bad_prior,
    relational_ecommerce_tlts,
    variant_D, run_trajectory,
)


# ---------------------------------------------------------------------------
# Certificate data structures
# ---------------------------------------------------------------------------

@dataclass
class StepRecord:
    """One step of the trajectory, fully audited."""
    step: int
    state_in: str
    label: str
    state_out: str
    in_delta: bool
    prior_argmax: str
    forced: bool
    masked_kl: float


@dataclass
class TrajectoryCertificate:
    """
    Full audit artifact for one trajectory.

    The verifier (a separate program) reads this JSON, the TLTS
    spec, and verifies independently. No model internals required.
    """
    schema: str
    schema_version: str
    timestamp: str
    tlts_fingerprint: str        # hash of (sorted types, labels, delta)
    enforcement_locus: str       # "in_ffn" | "pre_decoder" | "post_hoc_only"
    seed: Optional[int]
    start_state: str
    steps: List[StepRecord]
    soundness_passed: bool
    failed_at_step: Optional[int]
    failure_reason: str
    summary: Dict[str, Any]

    def to_json(self, indent: int = 2) -> str:
        d = asdict(self)
        return json.dumps(d, indent=indent, default=str)


# ---------------------------------------------------------------------------
# TLTS fingerprinting (so the verifier can detect drift between the
# TLTS used at generation time and the one used at audit time)
# ---------------------------------------------------------------------------

def fingerprint_tlts(tlts: TLTS) -> str:
    payload = json.dumps({
        "types": sorted(tlts.types),
        "labels": sorted(tlts.labels),
        "delta": sorted(map(list, tlts.delta)),
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Certificate emission — wraps a generation run
# ---------------------------------------------------------------------------

def emit_certificate(
    tlts: TLTS,
    prior: Prior,
    enforcement_locus: str,
    start_state: str = "Customer",
    max_len: int = 12,
    seed: int = 42,
) -> TrajectoryCertificate:
    rng = np.random.default_rng(seed)
    result = run_trajectory(variant_D, prior, tlts, rng, max_len=max_len, start=start_state)

    delta_set = {(t1, l, t2) for t1, l, t2 in tlts.delta}
    steps: List[StepRecord] = []
    failed_at = None
    failure_reason = ""

    for i, l in enumerate(result.labels):
        s_in = result.states[i]
        s_out = result.states[i + 1] if i + 1 < len(result.states) else None
        if s_out is None:
            failed_at = i
            failure_reason = f"step {i}: residual decoded to None"
            break

        in_delta = (s_in, l, s_out) in delta_set
        if not in_delta and failed_at is None:
            failed_at = i
            failure_reason = f"step {i}: ({s_in}, {l}, {s_out}) ∉ δ"

        prior_argmax = max(prior[s_in], key=prior[s_in].get) if s_in in prior else "?"
        forced = prior_argmax not in tlts.admissible_from(s_in)
        kl = result.redistribution_kl[i] if i < len(result.redistribution_kl) else 0.0

        steps.append(StepRecord(
            step=i,
            state_in=s_in,
            label=l,
            state_out=s_out,
            in_delta=in_delta,
            prior_argmax=prior_argmax,
            forced=forced,
            masked_kl=float(kl),
        ))

    summary = {
        "trajectory_length": len(steps),
        "all_steps_in_delta": all(s.in_delta for s in steps) if steps else True,
        "forced_step_count": sum(1 for s in steps if s.forced),
        "mean_masked_kl": float(np.mean([s.masked_kl for s in steps])) if steps else 0.0,
        "log_p_under_prior": result.log_p_under_prior,
    }

    return TrajectoryCertificate(
        schema="tlts_compilation.audit_certificate",
        schema_version="0.1",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        tlts_fingerprint=fingerprint_tlts(tlts),
        enforcement_locus=enforcement_locus,
        seed=seed,
        start_state=start_state,
        steps=steps,
        soundness_passed=(failed_at is None and result.valid),
        failed_at_step=failed_at,
        failure_reason=failure_reason,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Independent verifier — takes a certificate + a TLTS, returns pass/fail
# ---------------------------------------------------------------------------

@dataclass
class VerificationOutcome:
    passed: bool
    reasons: List[str] = field(default_factory=list)


def verify_certificate(cert_json: str, tlts: TLTS) -> VerificationOutcome:
    """
    Independent re-verification. Input is the certificate's JSON
    (no model internals); output is pass/fail with a list of reasons.
    """
    cert = json.loads(cert_json)
    reasons: List[str] = []

    # 1. Schema check
    if cert.get("schema") != "tlts_compilation.audit_certificate":
        reasons.append("wrong schema")
    if cert.get("schema_version") != "0.1":
        reasons.append(f"unexpected schema_version {cert.get('schema_version')}")

    # 2. TLTS fingerprint check (drift detection)
    expected_fp = fingerprint_tlts(tlts)
    if cert.get("tlts_fingerprint") != expected_fp:
        reasons.append(
            f"TLTS fingerprint drift: cert={cert.get('tlts_fingerprint')} "
            f"vs current={expected_fp}"
        )

    # 3. Per-step transition check (the heart of the verifier)
    delta_set = {(t1, l, t2) for t1, l, t2 in tlts.delta}
    for s in cert.get("steps", []):
        triple = (s["state_in"], s["label"], s["state_out"])
        if triple not in delta_set:
            reasons.append(f"step {s['step']}: {triple} ∉ δ")

    # 4. Summary consistency
    if cert.get("steps"):
        recomputed_log_p = "(not recomputed without prior)"
        if not cert["summary"]["all_steps_in_delta"] and cert.get("soundness_passed"):
            reasons.append("summary says steps invalid but soundness_passed=True")

    return VerificationOutcome(passed=not reasons, reasons=reasons)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo():
    print("=" * 88)
    print("  AUDIT CERTIFICATE — emit and verify, with a tampering test")
    print("=" * 88)

    tlts = relational_ecommerce_tlts()
    prior = good_prior(tlts, np.random.default_rng(123))

    print("\n[1] Emit certificate for a (D)-generated trajectory")
    cert = emit_certificate(tlts, prior, enforcement_locus="pre_decoder", seed=42)
    print(f"  fingerprint:  {cert.tlts_fingerprint}")
    print(f"  trajectory:   {' → '.join([s.state_in for s in cert.steps] + [cert.steps[-1].state_out] if cert.steps else [cert.start_state])}")
    print(f"  soundness:    {'PASS' if cert.soundness_passed else 'FAIL'}")
    print(f"  forced steps: {cert.summary['forced_step_count']}")
    print(f"  mean KL/step: {cert.summary['mean_masked_kl']:.4f}")

    print("\n[2] Independent verifier reads the certificate")
    cert_json = cert.to_json()
    outcome = verify_certificate(cert_json, tlts)
    print(f"  result: {'PASS' if outcome.passed else 'FAIL'}")
    if outcome.reasons:
        for r in outcome.reasons:
            print(f"    - {r}")

    print("\n[3] Tampering test: edit one step's state_out to an invalid type")
    cert_dict = json.loads(cert_json)
    if cert_dict["steps"]:
        original = cert_dict["steps"][0]["state_out"]
        cert_dict["steps"][0]["state_out"] = "Mars"   # not in tlts.types
        tampered_json = json.dumps(cert_dict)
        outcome = verify_certificate(tampered_json, tlts)
        print(f"  result: {'PASS (BUG!)' if outcome.passed else 'FAIL (good — tampering detected)'}")
        for r in outcome.reasons:
            print(f"    - {r}")
        cert_dict["steps"][0]["state_out"] = original

    print("\n[4] TLTS-drift test: verifier uses a TLTS missing one edge")
    drifted_tlts = TLTS(
        types=tlts.types,
        labels=tlts.labels,
        delta=[d for d in tlts.delta if d != ("Customer", "has", "Cart")],
    )
    outcome = verify_certificate(cert_json, drifted_tlts)
    print(f"  result: {'PASS (BUG!)' if outcome.passed else 'FAIL (good — drift detected)'}")
    for r in outcome.reasons[:3]:
        print(f"    - {r}")

    print("\n[5] Sample certificate (first step + summary):")
    if cert.steps:
        print(json.dumps(asdict(cert.steps[0]), indent=2))
    print(json.dumps(cert.summary, indent=2))

    print("\n" + "=" * 88)
    print("  This is what ships alongside a TLTS-compiled transformer's output.")
    print("  Verifier needs only the TLTS spec + the certificate JSON. No model needed.")
    print("=" * 88)


if __name__ == "__main__":
    demo()

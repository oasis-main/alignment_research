"""
experiment_loci_comparison.py

Empirical comparison of three TLTS-compilation enforcement loci on a
relational TLTS, using a synthetic prior in place of a trained model:

  (A) standard         — sample ℓ ~ p_M(· | t), no δ-enforcement
  (C) FFN-hybrid        — deterministic step on functional fragments;
                         (D) on relational nodes
  (D) pre-decoder mask  — sample ℓ ~ p_M restricted to admissible labels

Variant (B) — attention-layer masking — is omitted from the synthetic
harness because it acts on information flow inside a transformer
forward pass and cannot be simulated faithfully without a real model.
It enters when this harness is plugged into OntologicalAttention.

The point of the synthetic study: isolate the constraint mechanics
from model quality. The prior is the (controlled) "model"; the variants
are the constraint loci. We measure soundness, fluency, and latency.

Run:
    venv/bin/python experiment_loci_comparison.py
"""

from __future__ import annotations
import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Optional, Callable
import numpy as np


# ---------------------------------------------------------------------------
# TLTS (self-contained — see experiment_compiled_subolog.py for the
# in-FFN realization of the same data structure)
# ---------------------------------------------------------------------------

@dataclass
class TLTS:
    types: List[str]
    labels: List[str]
    delta: List[Tuple[str, str, str]]

    def admissible_from(self, t: str) -> Dict[str, str]:
        """{label: successor_type} for transitions out of t."""
        return {l: t2 for tt, l, t2 in self.delta if tt == t}

    def functional_set(self) -> Set[str]:
        """Types t where |{ℓ : (t, ℓ, _) ∈ δ}| == 1 (deterministic-step)."""
        return {t for t in self.types if len(self.admissible_from(t)) == 1}

    def terminal_set(self) -> Set[str]:
        return {t for t in self.types if not self.admissible_from(t)}


def cyclic_ecommerce_tlts() -> TLTS:
    """
    Like `relational_ecommerce_tlts` but with a Delivery -> Customer
    cycle, so every type can reach every other type. This is the
    stress test for (B') reachability masking: under near-universal
    reachability, (B') admits essentially all labels and collapses
    toward (A)-level soundness, while (D) remains 100%.
    """
    return TLTS(
        types=["Customer", "Cart", "Item", "Checkout", "Payment", "Order", "Delivery"],
        labels=["has", "contains", "proceeds_to", "requires", "creates", "triggers", "to"],
        delta=[
            ("Customer", "has",         "Cart"),
            ("Cart",     "contains",    "Item"),
            ("Cart",     "proceeds_to", "Checkout"),
            ("Checkout", "requires",    "Payment"),
            ("Payment",  "creates",     "Order"),
            ("Order",    "triggers",    "Delivery"),
            ("Delivery", "to",          "Customer"),  # cycle: closes the loop
            ("Item",     "to",          "Customer"),  # so Item isn't a dead-end either
        ],
    )


def relational_ecommerce_tlts() -> TLTS:
    """
    The same e-commerce Olog used elsewhere in the project, restricted
    to a 7-type subgraph with one branching node (Cart) and two
    terminal nodes (Item, Delivery).

      Customer --has--> Cart
      Cart     --contains--> Item               (branch 1)
      Cart     --proceeds_to--> Checkout        (branch 2)
      Checkout --requires--> Payment
      Payment  --creates--> Order
      Order    --triggers--> Delivery

    Functional nodes: {Customer, Checkout, Payment, Order}
    Relational node:  {Cart}
    Terminal nodes:   {Item, Delivery}
    """
    return TLTS(
        types=["Customer", "Cart", "Item", "Checkout", "Payment", "Order", "Delivery"],
        labels=["has", "contains", "proceeds_to", "requires", "creates", "triggers"],
        delta=[
            ("Customer", "has",         "Cart"),
            ("Cart",     "contains",    "Item"),
            ("Cart",     "proceeds_to", "Checkout"),
            ("Checkout", "requires",    "Payment"),
            ("Payment",  "creates",     "Order"),
            ("Order",    "triggers",    "Delivery"),
        ],
    )


# ---------------------------------------------------------------------------
# Synthetic prior — stand-in for a trained language model's
# next-label distribution given the current type.
# ---------------------------------------------------------------------------

Prior = Dict[str, Dict[str, float]]   # type -> label -> probability


def normalize(d: Dict[str, float]) -> Dict[str, float]:
    z = sum(d.values())
    return {k: v / z for k, v in d.items()} if z > 0 else d


def good_prior(tlts: TLTS, rng: np.random.Generator) -> Prior:
    """
    Mostly-aligned model: 80% mass on admissible labels (uniform over
    them), 20% spread over the rest. Simulates a model that broadly
    'knows' the domain.
    """
    p: Prior = {}
    for t in tlts.types:
        adm = set(tlts.admissible_from(t).keys())
        if not adm:
            adm = set(tlts.labels)   # uniform on terminal types (won't be sampled)
        d: Dict[str, float] = {}
        for l in tlts.labels:
            d[l] = 0.8 / len(adm) if l in adm else 0.2 / max(len(tlts.labels) - len(adm), 1)
        p[t] = normalize(d)
    return p


def bad_prior(tlts: TLTS, rng: np.random.Generator) -> Prior:
    """
    Mis-aligned model: 70% mass on a single 'favorite' label per type,
    chosen randomly from the full label set (often inadmissible),
    rest uniform. Simulates a model with strong but wrong priors.
    """
    p: Prior = {}
    for t in tlts.types:
        favorite = rng.choice(tlts.labels)
        d: Dict[str, float] = {}
        for l in tlts.labels:
            d[l] = 0.7 if l == favorite else 0.3 / (len(tlts.labels) - 1)
        p[t] = normalize(d)
    return p


# ---------------------------------------------------------------------------
# Variants — each is a sampling policy.
# ---------------------------------------------------------------------------

def sample_from(dist: Dict[str, float], rng: np.random.Generator) -> str:
    keys = list(dist.keys())
    probs = np.array([dist[k] for k in keys])
    probs = probs / probs.sum()
    return keys[int(rng.choice(len(keys), p=probs))]


def variant_A(prior: Prior, t: str, tlts: TLTS, rng: np.random.Generator) -> str:
    """(A) sample from p_M ignoring δ."""
    return sample_from(prior[t], rng)


def variant_D(prior: Prior, t: str, tlts: TLTS, rng: np.random.Generator) -> str:
    """(D) sample from p_M restricted to δ-admissible labels."""
    adm = set(tlts.admissible_from(t).keys())
    if not adm:
        return ""   # terminal state
    masked = {l: prior[t][l] for l in adm}
    if sum(masked.values()) == 0:
        # confidence-collapse fallback: uniform over admissible
        return sample_from({l: 1.0 / len(adm) for l in adm}, rng)
    return sample_from(normalize(masked), rng)


def variant_C(prior: Prior, t: str, tlts: TLTS, rng: np.random.Generator) -> str:
    """(C) deterministic step on functional types; (D) elsewhere."""
    if t in tlts.functional_set():
        adm = list(tlts.admissible_from(t).keys())
        return adm[0]
    return variant_D(prior, t, tlts, rng)


def reachability_closure(tlts: TLTS) -> Dict[str, Set[str]]:
    """Transitive closure: type -> set of types reachable from it (≥1 hops)."""
    succ: Dict[str, Set[str]] = {t: set() for t in tlts.types}
    for t1, _, t2 in tlts.delta:
        succ[t1].add(t2)
    # Floyd-Warshall-style closure
    closure = {t: set(succ[t]) for t in tlts.types}
    changed = True
    while changed:
        changed = False
        for t in tlts.types:
            for r in list(closure[t]):
                new = closure[r] - closure[t]
                if new:
                    closure[t].update(new)
                    changed = True
    return closure


def variant_B_reachability(prior: Prior, t: str, tlts: TLTS, rng: np.random.Generator) -> str:
    """
    (B') sampling-time projection of attention-layer reachability masking.

    Admits a label ℓ iff the type it targets is reachable (transitively)
    from the current type t. This is strictly looser than (D)'s direct-
    edge admissibility: it allows 'shortcut' labels whose target is
    reachable but for which no edge exists from t.

    This is *not* a faithful simulation of (B) attention masking — that
    requires a real transformer's attention computation. It is the
    cleanest sampling-time analog and surfaces a theoretical point:
    attention-layer reachability masking does not, on its own, guarantee
    trajectory soundness. Sample paths can target reachable types via
    label-edges that don't actually exist from the current state.
    """
    # Cache closure on the TLTS object
    if not hasattr(tlts, "_closure"):
        tlts._closure = reachability_closure(tlts)
    reach = tlts._closure[t]

    # A label is (B')-admissible if some δ-edge with that label targets a reachable type
    label_targets: Dict[str, Set[str]] = {}
    for tt, l, t2 in tlts.delta:
        label_targets.setdefault(l, set()).add(t2)
    adm_b = {l for l in tlts.labels
             if any(t2 in reach for t2 in label_targets.get(l, set()))}
    if not adm_b:
        return sample_from(prior[t], rng)
    masked = {l: prior[t][l] for l in adm_b}
    if sum(masked.values()) == 0:
        return sample_from({l: 1.0 / len(adm_b) for l in adm_b}, rng)
    return sample_from(normalize(masked), rng)


VARIANTS: Dict[str, Callable] = {
    "A": variant_A,
    "B'": variant_B_reachability,
    "C": variant_C,
    "D": variant_D,
}


# ---------------------------------------------------------------------------
# Trajectory simulation
# ---------------------------------------------------------------------------

@dataclass
class TrajectoryResult:
    states: List[str]
    labels: List[str]
    log_p_under_prior: float
    valid: bool
    invalid_step: Optional[int] = None
    forced_steps: int = 0
    redistribution_kl: List[float] = field(default_factory=list)


def run_trajectory(
    variant: Callable,
    prior: Prior,
    tlts: TLTS,
    rng: np.random.Generator,
    max_len: int = 10,
    start: str = "Customer",
) -> TrajectoryResult:
    state = start
    states = [state]
    labels: List[str] = []
    log_p = 0.0
    valid = True
    invalid_step: Optional[int] = None
    forced = 0
    kls: List[float] = []

    for step in range(max_len):
        if state in tlts.terminal_set():
            break
        adm = tlts.admissible_from(state)
        if not adm:
            break

        # Diagnostics on the prior at this step (independent of variant)
        full = prior[state]
        adm_set = set(adm.keys())
        masked_unnorm = {l: full[l] for l in adm_set}
        masked_z = sum(masked_unnorm.values())
        if masked_z > 0:
            masked = normalize(masked_unnorm)
            kl = sum(masked[l] * np.log(masked[l] / max(full[l], 1e-12)) for l in adm_set if masked[l] > 0)
            kls.append(float(kl))
        else:
            kls.append(float("inf"))

        # Was the model's argmax over the FULL distribution inadmissible?
        argmax_full = max(full, key=full.get)
        if argmax_full not in adm_set:
            forced += 1

        # Sample under the variant's policy
        l = variant(prior, state, tlts, rng)

        labels.append(l)
        log_p += float(np.log(max(full[l], 1e-12)))

        if l not in adm:
            valid = False
            invalid_step = step
            states.append(None)
            break

        state = adm[l]
        states.append(state)

    return TrajectoryResult(
        states=states,
        labels=labels,
        log_p_under_prior=log_p,
        valid=valid,
        invalid_step=invalid_step,
        forced_steps=forced,
        redistribution_kl=kls,
    )


# ---------------------------------------------------------------------------
# Experiment harness
# ---------------------------------------------------------------------------

@dataclass
class VariantStats:
    name: str
    n: int
    soundness_rate: float
    mean_log_p: float
    mean_traj_len: float
    mean_kl_per_step: float
    mean_forced_per_traj: float
    seconds_per_step: float


def evaluate_variant(
    variant_name: str,
    variant_fn: Callable,
    prior: Prior,
    tlts: TLTS,
    n_traj: int,
    max_len: int,
    seed: int,
) -> VariantStats:
    rng = np.random.default_rng(seed)
    results: List[TrajectoryResult] = []
    t0 = time.time()
    total_steps = 0
    for _ in range(n_traj):
        r = run_trajectory(variant_fn, prior, tlts, rng, max_len=max_len)
        results.append(r)
        total_steps += len(r.labels)
    elapsed = time.time() - t0

    sound = [r.valid for r in results]
    log_ps = [r.log_p_under_prior for r in results]
    lens = [len(r.labels) for r in results]
    kls = [k for r in results for k in r.redistribution_kl if not np.isinf(k)]
    forced = [r.forced_steps for r in results]

    return VariantStats(
        name=variant_name,
        n=n_traj,
        soundness_rate=statistics.mean(sound),
        mean_log_p=statistics.mean(log_ps),
        mean_traj_len=statistics.mean(lens),
        mean_kl_per_step=statistics.mean(kls) if kls else 0.0,
        mean_forced_per_traj=statistics.mean(forced),
        seconds_per_step=elapsed / max(total_steps, 1),
    )


def print_table(rows: List[VariantStats], header: str):
    print(f"\n{header}")
    print("-" * 92)
    print(f"  {'variant':<8} {'sound':>7} {'logP/traj':>11} {'len':>5} {'KL/step':>9} {'forced/traj':>13} {'µs/step':>10}")
    print("-" * 92)
    for r in rows:
        print(f"  {r.name:<8} "
              f"{r.soundness_rate*100:>6.1f}% "
              f"{r.mean_log_p:>11.3f} "
              f"{r.mean_traj_len:>5.2f} "
              f"{r.mean_kl_per_step:>9.4f} "
              f"{r.mean_forced_per_traj:>13.3f} "
              f"{r.seconds_per_step*1e6:>10.2f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 92)
    print("  TLTS-COMPILATION LOCI COMPARISON — synthetic-prior harness")
    print("=" * 92)

    tlts = relational_ecommerce_tlts()
    print(f"\nTLTS: |T|={len(tlts.types)}  |L|={len(tlts.labels)}  |δ|={len(tlts.delta)}")
    print(f"  functional types: {sorted(tlts.functional_set())}")
    print(f"  terminal types:   {sorted(tlts.terminal_set())}")
    print(f"  branching node:   Cart (admissible: {sorted(tlts.admissible_from('Cart').keys())})")

    n_traj = 1000
    max_len = 12
    seed = 42

    for prior_name, prior_fn in [("GOOD prior (80% on admissible)",  good_prior),
                                 ("BAD  prior (70% on random favorite)", bad_prior)]:
        print(f"\n\n>>> {prior_name}")
        rng_for_prior = np.random.default_rng(123)
        prior = prior_fn(tlts, rng_for_prior)

        rows = []
        for vname, vfn in VARIANTS.items():
            rows.append(evaluate_variant(vname, vfn, prior, tlts, n_traj, max_len, seed))
        print_table(rows, f"  N={n_traj}  max_len={max_len}  seed={seed}")

    print("\n" + "=" * 92)
    print("  Reading the table:")
    print("    sound       — fraction of trajectories with all (t, ℓ, t') ∈ δ")
    print("    logP/traj   — mean log p_M of realized trajectory (higher = closer to prior)")
    print("    KL/step     — mean KL(p_M^A || p_M) per step (mass-redistribution cost)")
    print("    forced/traj — mean #steps where p_M's argmax was inadmissible")
    print("    µs/step     — wall-clock per-step cost (Python/NumPy reference)")
    print("=" * 92)


if __name__ == "__main__":
    main()

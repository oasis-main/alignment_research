#!/usr/bin/env python3
"""
Attention Ablation Experiment: Standard vs Ontological Attention
================================================================

Trains two attention variants and compares them on hallucination detection:

  1. STANDARD: Vanilla scaled dot-product attention (no type constraints)
  2. ONTOLOGICAL: Type-constrained attention with Olog mask M_G

Metrics:
  - Invalid transition attention weight (lower = better for ontological)
  - Next-type prediction accuracy (higher = better)
  - Hallucination rate on held-out test claims
  - Attention entropy (lower = more focused for ontological)

Task: Next-type prediction
  Given a sequence of typed tokens from an Olog traversal,
  predict the next valid type. An "invalid" prediction is any
  type not reachable from the current type via morphisms.

Usage:
    python scripts/attention_ablation_experiment.py
    python scripts/attention_ablation_experiment.py --epochs 200 --seed 42
    python scripts/attention_ablation_experiment.py --plot
"""

import argparse
import json
import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("[WARNING] PyTorch not found. Running NumPy-only baseline.")

# ---------------------------------------------------------------------------
# Domain Ontologies
# ---------------------------------------------------------------------------

ONTOLOGIES = {
    "business": {
        "types": ["Customer", "Order", "Product", "Invoice", "Payment", "Shipment"],
        "aspects": [
            ("Customer", "Order",    "places"),
            ("Order",    "Product",  "contains"),
            ("Order",    "Invoice",  "generates"),
            ("Invoice",  "Payment",  "requires"),
            ("Payment",  "Shipment", "triggers"),
            ("Shipment", "Customer", "delivers_to"),
        ],
    },
    "academic": {
        "types": ["Student", "Course", "Professor", "Department", "Grade", "Transcript"],
        "aspects": [
            ("Student",    "Course",      "enrolls_in"),
            ("Course",     "Professor",   "taught_by"),
            ("Professor",  "Department",  "belongs_to"),
            ("Student",    "Grade",       "receives"),
            ("Grade",      "Course",      "for_course"),
            ("Student",    "Transcript",  "has"),
        ],
    },
    "healthcare": {
        "types": ["Patient", "Doctor", "Diagnosis", "Treatment", "Prescription", "Insurance"],
        "aspects": [
            ("Patient",    "Doctor",       "sees"),
            ("Doctor",     "Diagnosis",    "makes"),
            ("Diagnosis",  "Treatment",    "requires"),
            ("Treatment",  "Prescription", "involves"),
            ("Patient",    "Insurance",    "has"),
            ("Insurance",  "Treatment",    "covers"),
        ],
    },
    "ecommerce": {
        "types": ["User", "Cart", "Item", "Checkout", "Payment", "Delivery"],
        "aspects": [
            ("User",     "Cart",     "has"),
            ("Cart",     "Item",     "contains"),
            ("Cart",     "Checkout", "proceeds_to"),
            ("Checkout", "Payment",  "requires"),
            ("Payment",  "Delivery", "triggers"),
            ("Delivery", "User",     "to"),
        ],
    },
}

# Domain Bridges: (source, target, label)
# These represent valid morphisms that cross domains in open world reasoning.
DOMAIN_BRIDGES = [
    ("Patient", "Customer", "is_a"),   # A patient is a customer of the healthcare provider
]

# Test claims: (source_type, relation, target_type, valid)
# Used for final hallucination detection evaluation
HALLUCINATION_TEST_CLAIMS = [
    # Valid (should be accepted)
    ("Customer", "places",       "Order",    True),
    ("Order",    "contains",     "Product",  True),
    ("Order",    "generates",    "Invoice",  True),
    ("Invoice",  "requires",     "Payment",  True),
    ("Payment",  "triggers",     "Shipment", True),
    ("Student",  "enrolls_in",   "Course",   True),
    ("Doctor",   "makes",        "Diagnosis",True),
    ("User",     "has",          "Cart",     True),
    ("Cart",     "proceeds_to",  "Checkout", True),
    ("Patient",  "sees",         "Doctor",   True),
    # Valid Cross-Domain Bridges
    ("Patient",  "is_a",         "Customer", True),    # Informing the geometry
    # Invalid hallucinations (should be rejected)
    ("Payment",  "places",       "Customer", False),   # reverse wrong
    ("Product",  "places",       "Customer", False),   # inverted
    ("Customer", "has",          "Cart",     False),   # valid syntax, wrong domain
    ("Cart",     "places",       "Order",    False),   # plausible but invalid
    ("Order",    "sees",         "Doctor",   False),   # clearly invalid
]


# ---------------------------------------------------------------------------
# Ontology Graph Utilities
# ---------------------------------------------------------------------------

def build_reachability(aspects: List[Tuple[str, str, str]], max_depth: int = 4) -> Dict[str, Set[str]]:
    """Transitive closure of type reachability."""
    reach: Dict[str, Set[str]] = {}
    for src, tgt, _ in aspects:
        reach.setdefault(src, {src}).add(tgt)
        reach.setdefault(tgt, {tgt})

    for _ in range(max_depth):
        changed = False
        for node, reachable in list(reach.items()):
            for r in list(reachable):
                new = reach.get(r, set()) - reachable
                if new:
                    reachable.update(new)
                    changed = True
        if not changed:
            break
    return reach


def build_direct_successors(aspects: List[Tuple[str, str, str]]) -> Dict[str, Set[str]]:
    """Direct (one-hop) successors only."""
    succ: Dict[str, Set[str]] = {}
    for src, tgt, _ in aspects:
        succ.setdefault(src, set()).add(tgt)
    return succ


# ---------------------------------------------------------------------------
# Dataset Generation
# ---------------------------------------------------------------------------

def generate_training_sequences(
    ontologies: Dict,
    n_per_ontology: int = 200,
    seq_len: int = 4,
    seed: int = 42,
) -> List[Dict]:
    """
    Generate (sequence, next_type_label) training pairs.

    Positive examples: type sequences that follow valid morphism paths.
    Negative examples: sequences with one invalid step injected.
    """
    rng = random.Random(seed)
    dataset = []

    for ont_name, ont in ontologies.items():
        types = ont["types"]
        aspects = ont["aspects"]
        succ = build_direct_successors(aspects)
        all_types = set(types)

        for _ in range(n_per_ontology):
            # Build a valid random walk
            start = rng.choice(types)
            seq = [start]
            for _ in range(seq_len - 1):
                nexts = list(succ.get(seq[-1], []))
                if not nexts:
                    break
                seq.append(rng.choice(nexts))

            if len(seq) < 2:
                continue

            # Positive: predict the last type from prefix
            prefix = seq[:-1]
            valid_next = seq[-1]
            valid_targets = list(succ.get(prefix[-1], [valid_next]))

            dataset.append({
                "ontology": ont_name,
                "prefix": prefix,
                "next_type": valid_next,
                "valid_next_types": valid_targets,
                "all_types": sorted(types),
                "label": 1,  # valid
            })

            # Negative: inject an invalid next step
            invalid_options = list(all_types - set(succ.get(prefix[-1], [])) - {prefix[-1]})
            if invalid_options:
                invalid_next = rng.choice(invalid_options)
                dataset.append({
                    "ontology": ont_name,
                    "prefix": prefix,
                    "next_type": invalid_next,
                    "valid_next_types": valid_targets,
                    "all_types": sorted(types),
                    "label": 0,  # invalid / hallucination
                })

    rng.shuffle(dataset)
    return dataset


# ---------------------------------------------------------------------------
# Model Definitions (NumPy-based for portability)
# ---------------------------------------------------------------------------

class NumpyAttentionModel:
    """
    Minimal attention model implemented in NumPy.
    Supports standard and ontological (masked) variants.

    Training via finite-difference gradient approximation
    for demonstration purposes. For production use the
    PyTorch version below.
    """

    def __init__(
        self,
        n_types: int,
        embed_dim: int = 32,
        use_olog_mask: bool = False,
        seed: int = 42,
    ):
        self.n_types = n_types
        self.embed_dim = embed_dim
        self.use_olog_mask = use_olog_mask
        rng = np.random.RandomState(seed)

        # Type embedding table
        self.E = rng.randn(n_types, embed_dim) * 0.1

        # Projection matrices
        self.W_q = rng.randn(embed_dim, embed_dim) * 0.1
        self.W_k = rng.randn(embed_dim, embed_dim) * 0.1
        self.W_v = rng.randn(embed_dim, embed_dim) * 0.1

        # Classification head: embed_dim -> n_types
        self.W_cls = rng.randn(n_types, embed_dim) * 0.1
        self.b_cls = np.zeros(n_types)

    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        e = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return e / (np.sum(e, axis=axis, keepdims=True) + 1e-9)

    def _attention(
        self,
        seq_indices: List[int],
        mask: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (output, attention_weights) for a sequence of type indices."""
        X = self.E[seq_indices]  # (seq_len, embed_dim)
        Q = X @ self.W_q
        K = X @ self.W_k
        V = X @ self.W_v

        scores = Q @ K.T / math.sqrt(self.embed_dim)

        if mask is not None and self.use_olog_mask:
            scores = scores + mask  # mask has 0 or -1e9

        weights = self._softmax(scores)
        output = weights @ V  # (seq_len, embed_dim)
        return output, weights

    def forward(
        self,
        seq_indices: List[int],
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Returns logits over types for the last position (next-type prediction)."""
        output, _ = self._attention(seq_indices, mask)
        last = output[-1]  # (embed_dim,)
        logits = self.W_cls @ last + self.b_cls  # (n_types,)
        return logits

    def predict(
        self,
        seq_indices: List[int],
        mask: Optional[np.ndarray] = None,
    ) -> int:
        logits = self.forward(seq_indices, mask)
        return int(np.argmax(logits))

    def get_attention_weights(
        self,
        seq_indices: List[int],
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        _, weights = self._attention(seq_indices, mask)
        return weights


def build_mask_matrix(
    seq_types: List[str],
    reachability: Dict[str, Set[str]],
    neg_inf: float = -1e9,
) -> np.ndarray:
    """
    Build a (seq_len × seq_len) additive attention mask.
    mask[i,j] = 0      if type_j is reachable from type_i
    mask[i,j] = -1e9   otherwise
    """
    n = len(seq_types)
    mask = np.full((n, n), neg_inf)
    for i, ti in enumerate(seq_types):
        for j, tj in enumerate(seq_types):
            if ti == tj or tj in reachability.get(ti, set()):
                mask[i, j] = 0.0
    return mask


# ---------------------------------------------------------------------------
# PyTorch Models (used when available)
# ---------------------------------------------------------------------------

if HAS_TORCH:
    class TorchAttentionModel(nn.Module):
        """
        PyTorch attention model with optional Olog mask.
        Uses proper gradient descent.
        """

        def __init__(self, n_types: int, embed_dim: int = 32, num_heads: int = 2):
            super().__init__()
            self.n_types = n_types
            self.embed_dim = embed_dim
            self.type_emb = nn.Embedding(n_types, embed_dim)
            self.W_q = nn.Linear(embed_dim, embed_dim, bias=False)
            self.W_k = nn.Linear(embed_dim, embed_dim, bias=False)
            self.W_v = nn.Linear(embed_dim, embed_dim, bias=False)
            self.W_o = nn.Linear(embed_dim, embed_dim, bias=False)
            self.cls_head = nn.Linear(embed_dim, n_types)
            nn.init.normal_(self.type_emb.weight, std=0.1)

        def forward(
            self,
            seq: torch.Tensor,              # (batch, seq_len) int64
            attn_mask: Optional[torch.Tensor] = None,  # (seq_len, seq_len) additive float
        ) -> Tuple[torch.Tensor, torch.Tensor]:
            X = self.type_emb(seq)           # (batch, seq_len, d)
            Q = self.W_q(X)
            K = self.W_k(X)
            V = self.W_v(X)

            d_k = self.embed_dim ** 0.5
            scores = torch.bmm(Q, K.transpose(1, 2)) / d_k  # (B, L, L)

            if attn_mask is not None:
                scores = scores + attn_mask.unsqueeze(0)

            weights = F.softmax(scores, dim=-1)
            out = torch.bmm(weights, V)         # (B, L, d)
            out = self.W_o(out)
            last = out[:, -1, :]                # last position
            logits = self.cls_head(last)        # (B, n_types)
            return logits, weights


# ---------------------------------------------------------------------------
# Training Loop
# ---------------------------------------------------------------------------

@dataclass
class TrainResult:
    model_name: str
    final_loss: float
    train_acc: float
    test_acc: float
    hallucination_rate: float
    invalid_attn_weight: float   # avg attention weight on invalid transitions
    valid_attn_weight: float     # avg attention weight on valid transitions
    attn_entropy: float          # avg attention entropy (lower = more focused)
    training_time: float
    epoch_losses: List[float] = field(default_factory=list)


def run_torch_training(
    model_name: str,
    n_types: int,
    type_to_idx: Dict[str, int],
    idx_to_type: Dict[int, str],
    train_data: List[Dict],
    test_data: List[Dict],
    all_ontologies: Dict,
    use_olog_mask: bool,
    epochs: int = 150,
    lr: float = 0.005,
    embed_dim: int = 32,
    seed: int = 42,
) -> TrainResult:
    """Train a PyTorch attention model and evaluate it."""
    torch.manual_seed(seed)
    device = torch.device("cpu")  # local experiment

    model = TorchAttentionModel(n_types, embed_dim=embed_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    # Precompute per-ontology reachability
    reach_by_ont = {
        name: build_reachability(ont["aspects"])
        for name, ont in all_ontologies.items()
    }

    def make_tensor_and_mask(item: Dict):
        ont = item["ontology"]
        seq_types = item["prefix"]
        target_type = item["next_type"]

        seq_idx = [type_to_idx.get(t, 0) for t in seq_types]
        target_idx = type_to_idx.get(target_type, 0)
        seq_t = torch.tensor(seq_idx, dtype=torch.long).unsqueeze(0)

        mask_t = None
        if use_olog_mask:
            reach = reach_by_ont.get(ont, {})
            m = build_mask_matrix(seq_types, reach)
            mask_t = torch.tensor(m, dtype=torch.float32)

        return seq_t, mask_t, target_idx

    print(f"\n{'─'*60}")
    print(f"  Training: {model_name}")
    print(f"  Olog mask: {use_olog_mask} | Epochs: {epochs} | Embed: {embed_dim}d")
    print(f"{'─'*60}")

    start = time.time()
    epoch_losses = []

    for epoch in range(epochs):
        model.train()
        random.shuffle(train_data)
        total_loss = 0.0
        n = 0

        for item in train_data:
            seq_t, mask_t, target_idx = make_tensor_and_mask(item)
            optimizer.zero_grad()
            logits, _ = model(seq_t, mask_t)
            target_t = torch.tensor([target_idx], dtype=torch.long)
            loss = criterion(logits, target_t)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n += 1

        avg_loss = total_loss / max(n, 1)
        epoch_losses.append(avg_loss)

        if (epoch + 1) % 25 == 0:
            print(f"  Epoch {epoch+1:3d}/{epochs}  loss={avg_loss:.4f}")

    training_time = time.time() - start

    # ── Evaluate ──────────────────────────────────────────────────────────

    model.eval()

    def evaluate_accuracy(split: List[Dict]) -> Tuple[float, float, float]:
        """Returns (accuracy, invalid_attn_weight, attn_entropy)."""
        correct = 0
        invalid_weights = []
        valid_weights = []
        entropies = []

        with torch.no_grad():
            for item in split:
                ont = item["ontology"]
                seq_types = item["prefix"]
                target_type = item["next_type"]
                valid_nexts = set(item["valid_next_types"])

                seq_idx = [type_to_idx.get(t, 0) for t in seq_types]
                target_idx = type_to_idx.get(target_type, 0)
                seq_t = torch.tensor(seq_idx, dtype=torch.long).unsqueeze(0)

                mask_t = None
                if use_olog_mask:
                    reach = reach_by_ont.get(ont, {})
                    m = build_mask_matrix(seq_types, reach)
                    mask_t = torch.tensor(m, dtype=torch.float32)

                logits, weights = model(seq_t, mask_t)
                pred_idx = int(logits.argmax(dim=-1).item())

                if pred_idx == target_idx:
                    correct += 1

                # Attention analysis: last query position
                w = weights[0, -1, :].numpy()  # (seq_len,)
                reach = reach_by_ont.get(ont, {})
                last_type = seq_types[-1]
                reachable = reach.get(last_type, {last_type})

                # Weight going to valid vs invalid key positions
                for pos, t in enumerate(seq_types):
                    if t in reachable:
                        valid_weights.append(w[pos])
                    else:
                        invalid_weights.append(w[pos])

                # Entropy of attention distribution
                w_safe = np.clip(w, 1e-9, 1.0)
                ent = -np.sum(w_safe * np.log(w_safe))
                entropies.append(ent)

        acc = correct / len(split) if split else 0.0
        inv_w = float(np.mean(invalid_weights)) if invalid_weights else 0.0
        val_w = float(np.mean(valid_weights)) if valid_weights else 0.0
        ent_avg = float(np.mean(entropies))
        return acc, inv_w, val_w, ent_avg

    train_acc, _, _, _ = evaluate_accuracy(train_data)
    test_acc, inv_w, val_w, ent = evaluate_accuracy(test_data)

    print(f"\n  Results [{model_name}]:")
    print(f"    Train acc : {train_acc:.1%}")
    print(f"    Test acc  : {test_acc:.1%}")
    print(f"    Invalid attn weight: {inv_w:.4f}")
    print(f"    Valid   attn weight: {val_w:.4f}")
    print(f"    Attention entropy  : {ent:.4f}")

    # ── Hallucination detection on fixed test claims ──────────────────────
    hallucination_rate = evaluate_hallucination_claims(
        model, model_name, type_to_idx, idx_to_type,
        reach_by_ont, use_olog_mask
    )

    return TrainResult(
        model_name=model_name,
        final_loss=epoch_losses[-1],
        train_acc=train_acc,
        test_acc=test_acc,
        hallucination_rate=hallucination_rate,
        invalid_attn_weight=inv_w,
        valid_attn_weight=val_w,
        attn_entropy=ent,
        training_time=training_time,
        epoch_losses=epoch_losses,
    )


def evaluate_hallucination_claims(
    model,
    model_name: str,
    type_to_idx: Dict[str, int],
    idx_to_type: Dict[int, str],
    reach_by_ont: Dict,
    use_olog_mask: bool,
) -> float:
    """
    Evaluate on the fixed HALLUCINATION_TEST_CLAIMS set.

    For valid claims: model should assign high probability to the correct target.
    For invalid claims: model should assign low probability to the hallucinated target.

    Hallucination rate = fraction of invalid claims the model incorrectly ranks
    highest among all types.
    """
    model.eval()

    # Build a combined reachability (union of all ontologies + bridges)
    all_aspects = []
    for ont in ONTOLOGIES.values():
        all_aspects.extend(ont["aspects"])
    all_aspects.extend(DOMAIN_BRIDGES)
    
    global_reach = build_reachability(all_aspects)

    n_invalid = 0
    n_hallucinated = 0
    n_valid = 0
    n_valid_correct = 0

    with torch.no_grad():
        for src, rel, tgt, is_valid in HALLUCINATION_TEST_CLAIMS:
            if src not in type_to_idx or tgt not in type_to_idx:
                continue

            seq_types = [src]
            seq_idx = [type_to_idx[src]]
            seq_t = torch.tensor(seq_idx, dtype=torch.long).unsqueeze(0)

            mask_t = None
            if use_olog_mask:
                m = build_mask_matrix(seq_types, global_reach)
                mask_t = torch.tensor(m, dtype=torch.float32)

            logits, _ = model(seq_t, mask_t)
            probs = F.softmax(logits, dim=-1)[0].numpy()

            tgt_idx = type_to_idx[tgt]
            tgt_prob = probs[tgt_idx]
            pred_idx = int(np.argmax(probs))
            pred_type = idx_to_type.get(pred_idx, "?")

            if is_valid:
                n_valid += 1
                if pred_idx == tgt_idx:
                    n_valid_correct += 1
            else:
                n_invalid += 1
                # Hallucination: model assigns the invalid target the highest prob
                if pred_idx == tgt_idx:
                    n_hallucinated += 1

    hall_rate = n_hallucinated / max(n_invalid, 1)
    valid_acc = n_valid_correct / max(n_valid, 1)

    print(f"\n  Hallucination Claims [{model_name}]:")
    print(f"    Valid claims predicted correctly: {n_valid_correct}/{n_valid} ({valid_acc:.1%})")
    print(f"    Invalid claims hallucinated:      {n_hallucinated}/{n_invalid} ({hall_rate:.1%})")

    return hall_rate


# ---------------------------------------------------------------------------
# Main Experiment Runner
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Attention Ablation Experiment")
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--embed-dim", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.005)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-per-ontology", type=int, default=200)
    parser.add_argument("--plot", action="store_true", help="Save loss curve plot")
    parser.add_argument("--output", type=str, default="results/attention_ablation.json")
    args = parser.parse_args()

    print("=" * 60)
    print("  ATTENTION ABLATION EXPERIMENT")
    print("  Standard vs Ontological Attention")
    print("=" * 60)
    print(f"  Epochs: {args.epochs} | Embed: {args.embed_dim}d | LR: {args.lr}")
    print(f"  Seed: {args.seed} | N per ontology: {args.n_per_ontology}")

    if not HAS_TORCH:
        print("\n[ERROR] PyTorch is required. Install with: pip install torch")
        return

    # ── Build type vocabulary across all ontologies ───────────────────────
    all_types: Set[str] = set()
    for ont in ONTOLOGIES.values():
        all_types.update(ont["types"])
    # Include types from domain bridges
    for src, tgt, _ in DOMAIN_BRIDGES:
        all_types.add(src)
        all_types.add(tgt)
        
    all_types_sorted = sorted(all_types)
    type_to_idx = {t: i for i, t in enumerate(all_types_sorted)}
    idx_to_type = {i: t for t, i in type_to_idx.items()}
    n_types = len(all_types_sorted)

    print(f"\n  Vocabulary: {n_types} types")
    print(f"  Types: {all_types_sorted}")

    # ── Generate dataset ──────────────────────────────────────────────────
    print(f"\n  Generating training sequences ({args.n_per_ontology} per ontology)...")
    
    # Include bridges in training to inform embedding geometry
    TRAIN_ONTOLOGIES = ONTOLOGIES.copy()
    TRAIN_ONTOLOGIES["bridges"] = {
        "types": sorted({src for src, _, _ in DOMAIN_BRIDGES} | {tgt for _, tgt, _ in DOMAIN_BRIDGES}),
        "aspects": DOMAIN_BRIDGES
    }
    
    dataset = generate_training_sequences(
        TRAIN_ONTOLOGIES,
        n_per_ontology=args.n_per_ontology,
        seq_len=4,
        seed=args.seed,
    )
    # Filter to sequences where all types are in vocabulary
    dataset = [d for d in dataset if all(t in type_to_idx for t in d["prefix"] + [d["next_type"]])]

    split = int(0.8 * len(dataset))
    train_data = dataset[:split]
    test_data = dataset[split:]

    print(f"  Dataset: {len(dataset)} examples ({len(train_data)} train, {len(test_data)} test)")
    label_counts = {"valid": sum(1 for d in dataset if d["label"] == 1),
                    "invalid": sum(1 for d in dataset if d["label"] == 0)}
    print(f"  Labels: {label_counts}")

    # ── Run experiments ───────────────────────────────────────────────────
    results = []

    for use_mask, name in [(False, "Standard Attention"), (True, "Ontological Attention")]:
        result = run_torch_training(
            model_name=name,
            n_types=n_types,
            type_to_idx=type_to_idx,
            idx_to_type=idx_to_type,
            train_data=train_data,
            test_data=test_data,
            all_ontologies=TRAIN_ONTOLOGIES,
            use_olog_mask=use_mask,
            epochs=args.epochs,
            lr=args.lr,
            embed_dim=args.embed_dim,
            seed=args.seed,
        )
        results.append(result)

    # ── Print comparison table ────────────────────────────────────────────
    print("\n")
    print("=" * 60)
    print("  ABLATION RESULTS SUMMARY")
    print("=" * 60)

    header = f"  {'Metric':<35} {'Standard':>12} {'Ontological':>14}"
    print(header)
    print("  " + "─" * 63)

    r0, r1 = results[0], results[1]

    rows = [
        ("Final training loss",       f"{r0.final_loss:.4f}",       f"{r1.final_loss:.4f}"),
        ("Train accuracy",            f"{r0.train_acc:.1%}",         f"{r1.train_acc:.1%}"),
        ("Test accuracy (next-type)", f"{r0.test_acc:.1%}",          f"{r1.test_acc:.1%}"),
        ("Hallucination rate",        f"{r0.hallucination_rate:.1%}",f"{r1.hallucination_rate:.1%}"),
        ("Invalid attn weight (↓)",   f"{r0.invalid_attn_weight:.4f}",f"{r1.invalid_attn_weight:.4f}"),
        ("Valid attn weight (↑)",     f"{r0.valid_attn_weight:.4f}", f"{r1.valid_attn_weight:.4f}"),
        ("Attention entropy (↓)",     f"{r0.attn_entropy:.4f}",      f"{r1.attn_entropy:.4f}"),
        ("Training time (s)",         f"{r0.training_time:.1f}",     f"{r1.training_time:.1f}"),
    ]

    for label, v0, v1 in rows:
        print(f"  {label:<35} {v0:>12} {v1:>14}")

    print("  " + "─" * 63)

    # Improvement calculation
    if r0.hallucination_rate > 0:
        hall_delta = (r0.hallucination_rate - r1.hallucination_rate) / r0.hallucination_rate
        print(f"\n  Hallucination reduction (Olog mask): {hall_delta:.1%}")
    if r0.test_acc > 0:
        acc_delta = r1.test_acc - r0.test_acc
        print(f"  Test accuracy improvement:           {acc_delta:+.1%}")
    inv_delta = r0.invalid_attn_weight - r1.invalid_attn_weight
    print(f"  Invalid attention weight reduction:  {inv_delta:+.4f}")

    # ── Save results ──────────────────────────────────────────────────────
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    output = {
        "config": vars(args),
        "n_types": n_types,
        "dataset_size": len(dataset),
        "results": [
            {
                "model": r.model_name,
                "final_loss": r.final_loss,
                "train_acc": r.train_acc,
                "test_acc": r.test_acc,
                "hallucination_rate": r.hallucination_rate,
                "invalid_attn_weight": r.invalid_attn_weight,
                "valid_attn_weight": r.valid_attn_weight,
                "attn_entropy": r.attn_entropy,
                "training_time": r.training_time,
                "epoch_losses": r.epoch_losses,
            }
            for r in results
        ],
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {args.output}")

    # ── Optional plot ─────────────────────────────────────────────────────
    if args.plot:
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(1, 3, figsize=(15, 4))
            fig.suptitle("Attention Ablation: Standard vs Ontological", fontsize=13)

            # Loss curves
            ax = axes[0]
            ax.plot(r0.epoch_losses, label="Standard", color="#e74c3c", alpha=0.8)
            ax.plot(r1.epoch_losses, label="Ontological", color="#2ecc71", alpha=0.8)
            ax.set_title("Training Loss")
            ax.set_xlabel("Epoch")
            ax.set_ylabel("Cross-Entropy Loss")
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Bar chart: key metrics
            ax = axes[1]
            metrics = ["Test Acc", "Hall. Rate↓", "Invalid\nAttn↓"]
            std_vals  = [r0.test_acc, r0.hallucination_rate, r0.invalid_attn_weight]
            olog_vals = [r1.test_acc, r1.hallucination_rate, r1.invalid_attn_weight]
            x = np.arange(len(metrics))
            w = 0.35
            ax.bar(x - w/2, std_vals, w, label="Standard", color="#e74c3c", alpha=0.8)
            ax.bar(x + w/2, olog_vals, w, label="Ontological", color="#2ecc71", alpha=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels(metrics)
            ax.set_title("Key Metrics Comparison")
            ax.legend()
            ax.grid(True, alpha=0.3, axis="y")

            # Attention weight: valid vs invalid
            ax = axes[2]
            cats = ["Valid\nAttn Weight", "Invalid\nAttn Weight"]
            std_a  = [r0.valid_attn_weight, r0.invalid_attn_weight]
            olog_a = [r1.valid_attn_weight, r1.invalid_attn_weight]
            x2 = np.arange(len(cats))
            ax.bar(x2 - w/2, std_a, w, label="Standard", color="#e74c3c", alpha=0.8)
            ax.bar(x2 + w/2, olog_a, w, label="Ontological", color="#2ecc71", alpha=0.8)
            ax.set_xticks(x2)
            ax.set_xticklabels(cats)
            ax.set_title("Attention Weight Distribution")
            ax.legend()
            ax.grid(True, alpha=0.3, axis="y")

            plt.tight_layout()
            plot_path = args.output.replace(".json", ".png")
            plt.savefig(plot_path, dpi=150, bbox_inches="tight")
            print(f"  Plot saved to: {plot_path}")
            plt.close()
        except ImportError:
            print("  matplotlib not available; skipping plot.")

    print("\n  Experiment complete.")


if __name__ == "__main__":
    main()

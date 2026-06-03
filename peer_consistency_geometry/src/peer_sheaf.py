"""Peer-consistency sheaf over a panel of independently-trained models.

See ``constitutional_alignment_geometry/INQUIRY_PEER_CONSISTENCY_SHEAF.md`` for the
mathematical setup. This module implements the minimal E1-style baseline: linear
restriction maps fit by ridge regression on a calibration set, per-pair residuals,
and aggregate lossiness L(x). Harmonic-mass / Hodge decomposition is left to E2.

Conventions
-----------
- ``features_by_model`` is a dict ``{model_id: np.ndarray of shape (n_inputs, d_i)}``.
  Different models may have different embedding dims.
- Restriction maps are stored as ``{(src, dst): (W, b)}`` with ``ρ(x) = W @ x + b``.
- All directed pairs ``i != j`` are fit, since the asymmetry can itself be informative.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

import numpy as np


@dataclass
class RestrictionMap:
    """Affine map ``ρ(x) = x @ W.T + b`` from R^{d_src} to R^{d_dst}.

    Stored row-vector form to match numpy's (n, d) layout.
    """

    src: str
    dst: str
    W: np.ndarray  # shape (d_dst, d_src)
    b: np.ndarray  # shape (d_dst,)

    def apply(self, X: np.ndarray) -> np.ndarray:
        return X @ self.W.T + self.b


def fit_restriction_map(
    X_src: np.ndarray,
    X_dst: np.ndarray,
    ridge_lambda: float = 1e-3,
    src_id: str = "",
    dst_id: str = "",
) -> RestrictionMap:
    """Closed-form ridge regression for ``X_dst ≈ X_src @ W.T + b``.

    Centers both sides, solves for W with Tikhonov regularization, recovers b.
    """
    if X_src.shape[0] != X_dst.shape[0]:
        raise ValueError(f"row mismatch: {X_src.shape} vs {X_dst.shape}")
    mu_src = X_src.mean(axis=0)
    mu_dst = X_dst.mean(axis=0)
    A = X_src - mu_src
    B = X_dst - mu_dst
    # W solves (A^T A + λI) W^T = A^T B  ->  W^T = (A^T A + λI)^-1 A^T B
    d_src = A.shape[1]
    gram = A.T @ A + ridge_lambda * np.eye(d_src, dtype=A.dtype)
    Wt = np.linalg.solve(gram, A.T @ B)  # (d_src, d_dst)
    W = Wt.T  # (d_dst, d_src)
    b = mu_dst - W @ mu_src
    return RestrictionMap(src=src_id, dst=dst_id, W=W, b=b)


def fit_all_restriction_maps(
    features_by_model: dict[str, np.ndarray],
    ridge_lambda: float = 1e-3,
) -> dict[tuple[str, str], RestrictionMap]:
    """Fit ρ_{i→j} for every directed pair i != j on the given calibration features."""
    maps: dict[tuple[str, str], RestrictionMap] = {}
    for src, dst in permutations(features_by_model.keys(), 2):
        maps[(src, dst)] = fit_restriction_map(
            features_by_model[src],
            features_by_model[dst],
            ridge_lambda=ridge_lambda,
            src_id=src,
            dst_id=dst,
        )
    return maps


def _normalize_rows(X: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.maximum(n, eps)


def pair_residuals(
    features_by_model: dict[str, np.ndarray],
    maps: dict[tuple[str, str], RestrictionMap],
    metric: str = "cosine",
) -> dict[tuple[str, str], np.ndarray]:
    """Per-input residual for each directed pair.

    metric:
        "cosine"  -> 1 - cos(ρ(F_src), F_dst)  in [0, 2]
        "rel_l2"  -> ||ρ(F_src) - F_dst|| / ||F_dst||
    """
    out: dict[tuple[str, str], np.ndarray] = {}
    for (src, dst), rho in maps.items():
        pred = rho.apply(features_by_model[src])
        target = features_by_model[dst]
        if metric == "cosine":
            p = _normalize_rows(pred)
            t = _normalize_rows(target)
            out[(src, dst)] = 1.0 - (p * t).sum(axis=1)
        elif metric == "rel_l2":
            num = np.linalg.norm(pred - target, axis=1)
            den = np.maximum(np.linalg.norm(target, axis=1), 1e-12)
            out[(src, dst)] = num / den
        else:
            raise ValueError(f"unknown metric: {metric}")
    return out


def aggregate_lossiness(
    pair_resids: dict[tuple[str, str], np.ndarray],
) -> np.ndarray:
    """Mean per-input residual across all directed pairs: L(x)."""
    stacked = np.stack(list(pair_resids.values()), axis=0)  # (n_pairs, n_inputs)
    return stacked.mean(axis=0)


def panel_residual_summary(
    features_by_model: dict[str, np.ndarray],
    maps: dict[tuple[str, str], RestrictionMap],
    metric: str = "cosine",
) -> dict[str, np.ndarray]:
    """Convenience bundle: per-pair residuals, aggregate L(x), per-model leave-one-out.

    Per-model LOO score for model k on input x is the mean residual over pairs that
    involve k as either source or destination. A model whose representation is locally
    out-of-distribution relative to its peers shows up with a large LOO score.
    """
    pair_resids = pair_residuals(features_by_model, maps, metric=metric)
    L = aggregate_lossiness(pair_resids)
    loo: dict[str, np.ndarray] = {}
    for model in features_by_model:
        involved = [
            pair_resids[(s, d)]
            for (s, d) in pair_resids
            if s == model or d == model
        ]
        loo[model] = np.stack(involved, axis=0).mean(axis=0)
    return {
        "pair_residuals": pair_resids,
        "L": L,
        "loo": loo,
    }

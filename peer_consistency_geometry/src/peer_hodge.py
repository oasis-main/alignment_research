"""Vector-valued cellular-sheaf Hodge decomposition for the peer-consistency panel.

Track 1's ``hodge_diagnostic.py`` operates on *scalar* preference cochains over a
graph. The peer-consistency setting (see
``constitutional_alignment_geometry/INQUIRY_PEER_CONSISTENCY_SHEAF.md``) is
vector-valued on every 1-cell: for a directed model pair (i, j) the measured
1-cochain takes values in R^{d_j}. We therefore implement a small block-aware
coboundary and project each input's measured cochain onto resolvable
(im δ⁰) and harmonic ((im δ⁰)^⊥) subspaces.

Setup
-----
- 0-cells = models. The 0-cochain space is V = ⊕_i R^{d_i}.
- 1-cells = directed model pairs (i, j), i ≠ j. The 1-cochain space is
  E = ⊕_{(i,j)} R^{d_j}.
- Restriction maps ρ_{i→j}(x) = W_{ij} x + b_{ij} come from a calibration fit
  (``peer_sheaf.fit_all_restriction_maps``).
- Coboundary δ⁰: V → E, ``(δ⁰ s)_{(i,j)} = W_{ij} s_i − s_j`` (linear part only;
  the bias ``b_{ij}`` lives in the *constant* offset of the measured cochain,
  not in δ⁰).
- For an input x the measured 1-cochain is
  ``c_{(i,j)}(x) = ρ_{i→j}(F_i(x)) − F_j(x) = W_{ij} F_i(x) + b_{ij} − F_j(x)``.

With no 2-cells the decomposition is
    c = δ⁰ s⋆ + h,    s⋆ = argmin_s ||δ⁰ s − c||²,   h ⟂ im δ⁰.
``δ⁰ s⋆`` is the resolvable component (some choice of stalk values would have
explained it away), ``h`` is the harmonic component (no choice can: it is the
cross-model analogue of Track 1's H¹). The split is per-input and per-edge.

We project via an orthonormal basis Q of col(δ⁰), obtained once by reduced QR
of the assembled block matrix B (shape ``(D_E, D_V)``). For the E1 panel
``D_V = 960 + 896 + 2048 = 3904`` and ``D_E = 2·(960 + 896 + 2048) = 7808``.

Methodological note — why we add 2-cells
----------------------------------------
A first attempt skipped 2-cells. That decomposition is *vacuous* on this data
by construction: with affine restriction maps fit by ridge,
``c(x) = W_{ij} F_i(x) + b_{ij} − F_j(x) = W_{ij}(F_i(x) − μ_i) − (F_j(x) − μ_j)
       = (δ⁰ (F(x) − μ))_{(i,j)}``,
so every measured 1-cochain is *exactly* a coboundary of the data itself. The
``(im δ⁰)^⊥`` projection is therefore numerically zero across the panel — the
choice ``s = F(x) − μ`` explains everything. The "no choice of stalk values
explains it away" framing fails because the data itself supplies a valid
choice.

The non-trivial sheaf signal lives one level up: ``δ¹ c``, the cocycle
violation. With 2-cells = ordered triples (i, j, k) we define
``(δ¹ c)_{(i,j,k)} = ρ_{j→k}(c_{(i,j)}) + c_{(j,k)} − c_{(i,k)}``.
Concretely, plugging in ``c = δ⁰ s`` gives
``(δ¹ δ⁰ s)_{(i,j,k)} = ρ_{j→k}(ρ_{i→j}(s_i)) − ρ_{i→k}(s_i)``,
i.e. the *composition failure* of the restriction maps acting on the source
stalk. ``δ¹ c`` is non-zero precisely when the panel's pairwise translations
fail to commute around a triangle — the genuine sheaf-cohomological
obstruction to a global section, and the part that no single stalk-assignment
can remove because it lives in a different coordinate space.

We expose three norms per input:
  total            = ||c(x)||
  coboundary_norm  = ||δ⁰* c(x)||      (down-Laplacian footprint; numerically 0 here)
  cocycle_violation = ||δ¹ c(x)||      (the actual sheaf signal)
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

import numpy as np

from peer_sheaf import RestrictionMap


@dataclass
class PeerComplex:
    """Bookkeeping for the cellular sheaf on a fixed model panel.

    ``dims[m]`` is the stalk dimension at model ``m``. ``node_slices`` and
    ``edge_slices`` carve up the assembled V and E coordinate vectors so each
    block can be read off without re-indexing logic at the call sites. 2-cells
    are ordered triples (i, j, k) of distinct models, each with codomain ``dims[k]``.
    """

    models: list[str]
    dims: dict[str, int]
    node_slices: dict[str, slice]      # slot of model m in V (size dims[m])
    edge_slices: dict[tuple[str, str], slice]  # slot of edge (i,j) in E (size dims[j])
    tri_slices: dict[tuple[str, str, str], slice]  # slot of triangle (i,j,k) in F (size dims[k])
    D_V: int
    D_E: int
    D_F: int

    @classmethod
    def from_features(cls, features_by_model: dict[str, np.ndarray]) -> "PeerComplex":
        models = list(features_by_model.keys())
        dims = {m: int(features_by_model[m].shape[1]) for m in models}
        node_slices: dict[str, slice] = {}
        cursor = 0
        for m in models:
            node_slices[m] = slice(cursor, cursor + dims[m])
            cursor += dims[m]
        D_V = cursor
        edge_slices: dict[tuple[str, str], slice] = {}
        cursor = 0
        for i, j in permutations(models, 2):
            edge_slices[(i, j)] = slice(cursor, cursor + dims[j])
            cursor += dims[j]
        D_E = cursor
        tri_slices: dict[tuple[str, str, str], slice] = {}
        cursor = 0
        for i, j, k in permutations(models, 3):
            tri_slices[(i, j, k)] = slice(cursor, cursor + dims[k])
            cursor += dims[k]
        D_F = cursor
        return cls(
            models=models,
            dims=dims,
            node_slices=node_slices,
            edge_slices=edge_slices,
            tri_slices=tri_slices,
            D_V=D_V,
            D_E=D_E,
            D_F=D_F,
        )


def assemble_coboundary(
    complex_: PeerComplex,
    maps: dict[tuple[str, str], RestrictionMap],
) -> np.ndarray:
    """Build B ∈ R^{D_E × D_V} so that (B s)_{edge (i,j)} = W_{ij} s_i − s_j."""
    B = np.zeros((complex_.D_E, complex_.D_V), dtype=np.float64)
    for (i, j), rho in maps.items():
        e_slice = complex_.edge_slices[(i, j)]
        ni = complex_.node_slices[i]
        nj = complex_.node_slices[j]
        # block in column for source i: + W_{ij}
        B[e_slice, ni] = rho.W
        # block in column for destination j: -I
        d_j = complex_.dims[j]
        B[e_slice, nj] = -np.eye(d_j, dtype=np.float64)
    return B


def assemble_triangle_coboundary(
    complex_: PeerComplex,
    maps: dict[tuple[str, str], RestrictionMap],
) -> np.ndarray:
    """Build δ¹ ∈ R^{D_F × D_E} so that

        (δ¹ c)_{(i,j,k)} = W_{jk} c_{(i,j)} + c_{(j,k)} − c_{(i,k)}.

    With composing restriction maps δ¹δ⁰ = 0; the maps fit by ridge do *not*
    compose, so δ¹δ⁰ measures composition failure.
    """
    F = np.zeros((complex_.D_F, complex_.D_E), dtype=np.float64)
    for (i, j, k), tri_slice in complex_.tri_slices.items():
        W_jk = maps[(j, k)].W
        e_ij = complex_.edge_slices[(i, j)]
        e_jk = complex_.edge_slices[(j, k)]
        e_ik = complex_.edge_slices[(i, k)]
        d_k = complex_.dims[k]
        F[tri_slice, e_ij] = W_jk                         # ρ_{j→k}(c_{(i,j)})
        F[tri_slice, e_jk] = np.eye(d_k, dtype=np.float64)
        F[tri_slice, e_ik] = -np.eye(d_k, dtype=np.float64)
    return F


def assemble_cochain(
    complex_: PeerComplex,
    features_by_model: dict[str, np.ndarray],
    maps: dict[tuple[str, str], RestrictionMap],
) -> np.ndarray:
    """Stack per-edge measured residuals into an (n_inputs, D_E) matrix C.

    Row k holds the full 1-cochain for input k: vertical concatenation of
    ``ρ_{i→j}(F_i(x_k)) − F_j(x_k)`` across the directed pairs in
    ``complex_.edge_slices``.
    """
    n = next(iter(features_by_model.values())).shape[0]
    C = np.zeros((n, complex_.D_E), dtype=np.float64)
    for (i, j), rho in maps.items():
        pred = rho.apply(features_by_model[i])
        target = features_by_model[j]
        C[:, complex_.edge_slices[(i, j)]] = pred - target
    return C


@dataclass
class HodgeDecomposition:
    """Per-input split of the measured 1-cochain.

    All arrays have leading axis = n_inputs.

    ``C_res + C_harm = C``; in the present sheaf ``C_harm ≈ 0`` numerically
    because the data itself provides a valid section (see module docstring).
    ``cocycle_violation`` (``δ¹ C``) is the meaningful sheaf signal: nonzero
    iff the restriction maps fail to compose around the triangle (i,j,k).
    """

    C: np.ndarray                  # (n, D_E) raw 1-cochain
    C_res: np.ndarray              # (n, D_E) resolvable component, in im δ⁰
    C_harm: np.ndarray             # (n, D_E) ⟂ im δ⁰ (numerically zero on this data)
    cocycle_violation: np.ndarray  # (n, D_F) δ¹ C
    rank_B: int                    # rank of δ⁰, ≤ D_V

    @property
    def norm_total(self) -> np.ndarray:
        return np.linalg.norm(self.C, axis=1)

    @property
    def norm_res(self) -> np.ndarray:
        return np.linalg.norm(self.C_res, axis=1)

    @property
    def norm_harm(self) -> np.ndarray:
        return np.linalg.norm(self.C_harm, axis=1)

    @property
    def norm_cocycle_violation(self) -> np.ndarray:
        return np.linalg.norm(self.cocycle_violation, axis=1)

    def harmonic_fraction(self, eps: float = 1e-12) -> np.ndarray:
        """||h||² / ||c||² per input. In [0, 1]."""
        num = (self.C_harm * self.C_harm).sum(axis=1)
        den = (self.C * self.C).sum(axis=1) + eps
        return num / den


def hodge_decompose(
    complex_: PeerComplex,
    features_by_model: dict[str, np.ndarray],
    maps: dict[tuple[str, str], RestrictionMap],
    rcond: float | None = None,
) -> HodgeDecomposition:
    """Project each input's 1-cochain onto im δ⁰ and its orthogonal complement.

    Uses thin SVD of B to obtain an orthonormal basis Q for col(B); resolvable
    component is ``Q (Q^T c)`` and the harmonic component is the residual. SVD
    is done once and reused for all inputs.
    """
    B = assemble_coboundary(complex_, maps)
    # Thin SVD: B = U Σ V^T with U of shape (D_E, k), k = min(D_E, D_V).
    # The orthonormal basis for col(B) is the columns of U that correspond to
    # non-negligible singular values.
    U, s, _ = np.linalg.svd(B, full_matrices=False)
    if rcond is None:
        rcond = max(B.shape) * np.finfo(B.dtype).eps
    tol = rcond * (s[0] if s.size else 0.0)
    rank = int(np.sum(s > tol))
    Q = U[:, :rank]  # (D_E, rank)

    C = assemble_cochain(complex_, features_by_model, maps)  # (n, D_E)
    # Resolvable = C @ Q @ Q^T  (project rows of C onto col(Q))
    coords = C @ Q                       # (n, rank)
    C_res = coords @ Q.T                  # (n, D_E)
    C_harm = C - C_res

    delta1 = assemble_triangle_coboundary(complex_, maps)  # (D_F, D_E)
    cocycle_violation = C @ delta1.T                       # (n, D_F)

    return HodgeDecomposition(
        C=C,
        C_res=C_res,
        C_harm=C_harm,
        cocycle_violation=cocycle_violation,
        rank_B=rank,
    )


def per_edge_norms(
    complex_: PeerComplex,
    C: np.ndarray,
) -> dict[tuple[str, str], np.ndarray]:
    """Split an (n, D_E) cochain stack into per-edge L2 norms (n,) per edge."""
    out: dict[tuple[str, str], np.ndarray] = {}
    for edge, sl in complex_.edge_slices.items():
        block = C[:, sl]
        out[edge] = np.linalg.norm(block, axis=1)
    return out


# ---------------------------------------------------------------------------
# SGB-014: low-rank stalk constraint.
# ---------------------------------------------------------------------------
#
# In the full-rank formulation the data itself supplies a valid section
# (s = F(x) − μ), so (im δ⁰)^⊥ collapses to zero on this cochain. Restricting
# each stalk to a fixed low-dimensional subspace U_i ⊂ R^{d_i} (e.g. the top-k
# PCA directions of model i's calibration features) reopens the harmonic
# channel: the part of F(x) − μ that lives outside U_i can no longer be
# absorbed into a stalk choice.
#
# Reduced coboundary (edges keep codomain R^{d_j}, stalks restricted to R^k):
#   (δ⁰_lowrank s)_{(i,j)} = W_{ij} U_i s_i − U_j s_j     ∈ R^{d_j},   s_i ∈ R^k.
#
# Per input, the harmonic residual h(x) is
#   c(x) − δ⁰_lowrank s⋆(x) =
#     W_{ij} (I − U_i U_i^T) (F_i(x) − μ_i)
#       − (I − U_j U_j^T) (F_j(x) − μ_j),
# i.e. the part of cross-model translation that depends on the rank > k tail
# of each model's representation. Nonzero whenever the panel features carry
# meaningful rank beyond k.
# ---------------------------------------------------------------------------


def fit_top_k_pca_per_model(
    features_cal_by_model: dict[str, np.ndarray],
    k: int,
) -> dict[str, np.ndarray]:
    """Top-k right-singular vectors of each model's centered calibration matrix.

    Returns ``{model: U_i}`` with ``U_i`` of shape ``(d_i, k)`` (columns
    orthonormal). The mean used for centering is *not* returned because the
    low-rank decomposition operates on the raw measured cochain (the centering
    is already absorbed by the affine restriction maps).
    """
    out: dict[str, np.ndarray] = {}
    for m, X in features_cal_by_model.items():
        d = X.shape[1]
        if k > d:
            raise ValueError(
                f"k={k} exceeds feature dim {d} for model {m!r}; pick a smaller k"
            )
        Xc = X - X.mean(axis=0, keepdims=True)
        # Right-singular vectors of Xc are the principal axes in feature space.
        # Thin SVD is enough; numpy returns V^T already.
        _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
        out[m] = Vt[:k].T  # (d, k)
    return out


def assemble_low_rank_coboundary(
    complex_: PeerComplex,
    maps: dict[tuple[str, str], RestrictionMap],
    U_by_model: dict[str, np.ndarray],
) -> np.ndarray:
    """Build B_low ∈ R^{D_E × (|V| · k)} so that for stacked stalks s,

        (B_low s)_{edge (i,j)} = W_{ij} U_i s_i  −  U_j s_j.

    Columns are blocked by node in the order of ``complex_.models`` with each
    block ``k`` columns wide. Caller is responsible for using consistent
    ordering when unpacking ``s⋆``.
    """
    k = next(iter(U_by_model.values())).shape[1]
    n_nodes = len(complex_.models)
    B = np.zeros((complex_.D_E, n_nodes * k), dtype=np.float64)
    col_slices = {m: slice(i * k, (i + 1) * k) for i, m in enumerate(complex_.models)}
    for (i, j), rho in maps.items():
        e_slice = complex_.edge_slices[(i, j)]
        U_i = U_by_model[i]
        U_j = U_by_model[j]
        B[e_slice, col_slices[i]] = rho.W @ U_i   # (d_j, k)
        B[e_slice, col_slices[j]] = -U_j           # (d_j, k)
    return B


@dataclass
class LowRankHodgeDecomposition:
    """Per-input split of the measured 1-cochain under low-rank stalk constraint.

    Same shape conventions as :class:`HodgeDecomposition`: ``C_res + C_harm = C``,
    ``C_res`` lives in the column space of the reduced coboundary, ``C_harm``
    is the part no rank-k stalk assignment can explain.

    Unlike the full-rank case, ``C_harm`` is in general nonzero — that is the
    whole point of the reformulation.
    """

    C: np.ndarray                  # (n, D_E) raw 1-cochain
    C_res: np.ndarray              # (n, D_E) projection onto col(δ⁰_lowrank)
    C_harm: np.ndarray             # (n, D_E) ⟂ col(δ⁰_lowrank)
    cocycle_violation: np.ndarray  # (n, D_F) δ¹ C (recomputed for convenience)
    rank_B: int                    # rank of δ⁰_lowrank, ≤ |V| · k
    k: int                         # stalk dimension per model

    @property
    def norm_total(self) -> np.ndarray:
        return np.linalg.norm(self.C, axis=1)

    @property
    def norm_res(self) -> np.ndarray:
        return np.linalg.norm(self.C_res, axis=1)

    @property
    def norm_harm(self) -> np.ndarray:
        return np.linalg.norm(self.C_harm, axis=1)

    @property
    def norm_cocycle_violation(self) -> np.ndarray:
        return np.linalg.norm(self.cocycle_violation, axis=1)

    def harmonic_fraction(self, eps: float = 1e-12) -> np.ndarray:
        num = (self.C_harm * self.C_harm).sum(axis=1)
        den = (self.C * self.C).sum(axis=1) + eps
        return num / den


def low_rank_hodge_decompose(
    complex_: PeerComplex,
    features_by_model: dict[str, np.ndarray],
    maps: dict[tuple[str, str], RestrictionMap],
    U_by_model: dict[str, np.ndarray],
    rcond: float | None = None,
) -> LowRankHodgeDecomposition:
    """Hodge decomposition with stalks constrained to per-model U_i subspaces.

    The orthonormal basis Q for col(δ⁰_lowrank) is computed once via thin SVD.
    """
    B = assemble_low_rank_coboundary(complex_, maps, U_by_model)
    U, s, _ = np.linalg.svd(B, full_matrices=False)
    if rcond is None:
        rcond = max(B.shape) * np.finfo(B.dtype).eps
    tol = rcond * (s[0] if s.size else 0.0)
    rank = int(np.sum(s > tol))
    Q = U[:, :rank]

    C = assemble_cochain(complex_, features_by_model, maps)
    coords = C @ Q
    C_res = coords @ Q.T
    C_harm = C - C_res

    delta1 = assemble_triangle_coboundary(complex_, maps)
    cocycle_violation = C @ delta1.T

    k_per_node = next(iter(U_by_model.values())).shape[1]
    return LowRankHodgeDecomposition(
        C=C,
        C_res=C_res,
        C_harm=C_harm,
        cocycle_violation=cocycle_violation,
        rank_B=rank,
        k=k_per_node,
    )

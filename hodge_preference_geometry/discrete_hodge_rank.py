"""
Module 1: Discrete HodgeRank for Transitive Alignment

This module implements the discrete Helmholtz-Hodge decomposition on preference
graphs to extract the transitive (gradient) component for reward model training.

Key Mathematical Insight (from Jiang et al. 2011):
- Pairwise preferences form edge flows on a graph
- Hodge decomposition separates:
  * Gradient (exact): ∇φ — global transitive consensus (Borda count)
  * Curl (coexact): δψ — local cyclic inconsistencies in 3-cliques
  * Harmonic: h — global Condorcet paradoxes (macroscopic cycles)

For RLHF, we train ONLY on the gradient component, discarding curl and harmonic
which represent different forms of cyclic inconsistency.

References:
- Jiang et al. "Statistical Ranking and Combinatorial Hodge Theory" (2011)
- Lim "Hodge Laplacians on Graphs" (SIAM Review 2020)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy.sparse import csr_matrix, lil_matrix, diags
from scipy.sparse.linalg import lsqr, eigsh, cg
import warnings


@dataclass
class HodgeComponents:
    """
    Result of discrete Hodge decomposition on edge flows.
    
    The decomposition is orthogonal:
        edge_flow = gradient + curl + harmonic
        ||f||² = ||∇φ||² + ||δψ||² + ||h||²
    """
    gradient: np.ndarray      # ∇φ: exact component (transitive preferences)
    curl: np.ndarray          # δψ: coexact component (local 3-cycles)
    harmonic: np.ndarray      # h: harmonic component (global Condorcet cycles)
    
    # Metadata
    edge_indices: List[Tuple[int, int]]  # Edge (i,j) for each component index
    vertex_potential: Optional[np.ndarray] = None  # φ such that ∇φ = gradient
    
    @property
    def gradient_energy(self) -> float:
        """L² energy in gradient component."""
        return float(np.sum(self.gradient ** 2))
    
    @property
    def curl_energy(self) -> float:
        """L² energy in curl component."""
        return float(np.sum(self.curl ** 2))
    
    @property
    def harmonic_energy(self) -> float:
        """L² energy in harmonic component."""
        return float(np.sum(self.harmonic ** 2))
    
    @property
    def total_energy(self) -> float:
        """Total L² energy (sum of components by Pythagorean theorem)."""
        return self.gradient_energy + self.curl_energy + self.harmonic_energy
    
    @property
    def reliability_score(self) -> float:
        """
        Fraction of energy in gradient = reliability of global ranking.
        
        High (→1): Preferences are nearly transitive, ranking is trustworthy
        Low (→0): Preferences are cyclic chaos, ranking is unreliable
        """
        total = self.total_energy
        if total < 1e-10:
            return 1.0  # No preferences = trivially consistent
        return self.gradient_energy / total
    
    @property
    def cyclic_residual(self) -> float:
        """
        Fraction of energy in curl + harmonic = cyclic inconsistency.
        
        This is 1 - reliability_score.
        """
        return 1.0 - self.reliability_score


@dataclass
class PreferenceGraph:
    """
    A graph encoding pairwise preferences.
    
    Vertices: Items being ranked (alternatives)
    Edges: Pairwise comparisons with preference strength
    Triangles: 3-cliques for curl computation
    """
    n_vertices: int
    edges: List[Tuple[int, int]]          # (i, j) where i is preferred over j
    edge_weights: np.ndarray              # Strength of preference (can be fractional)
    triangles: Optional[List[Tuple[int, int, int]]] = None  # For curl computation
    
    @classmethod
    def from_pairwise_comparisons(
        cls,
        n_items: int,
        comparisons: List[Tuple[int, int, float]],
        aggregate: str = "mean"
    ) -> "PreferenceGraph":
        """
        Build preference graph from pairwise comparison data.
        
        Args:
            n_items: Number of items being ranked
            comparisons: List of (winner, loser, strength) tuples
            aggregate: How to aggregate multiple comparisons ("mean", "sum", "max")
        
        Returns:
            PreferenceGraph ready for Hodge decomposition
        """
        # Aggregate comparisons into edge weights
        edge_data: Dict[Tuple[int, int], List[float]] = {}
        
        for winner, loser, strength in comparisons:
            if winner == loser:
                continue
            # Canonical edge direction: smaller index first
            if winner < loser:
                key = (winner, loser)
                edge_data.setdefault(key, []).append(strength)
            else:
                key = (loser, winner)
                edge_data.setdefault(key, []).append(-strength)
        
        # Aggregate
        edges = []
        weights = []
        for (i, j), strengths in edge_data.items():
            edges.append((i, j))
            if aggregate == "mean":
                weights.append(np.mean(strengths))
            elif aggregate == "sum":
                weights.append(np.sum(strengths))
            elif aggregate == "max":
                weights.append(np.max(np.abs(strengths)) * np.sign(np.sum(strengths)))
            else:
                raise ValueError(f"Unknown aggregation: {aggregate}")
        
        # Find triangles (3-cliques) for curl computation
        adjacency = set(edges) | {(j, i) for i, j in edges}
        triangles = []
        for i in range(n_items):
            neighbors_i = {j for (a, b) in adjacency if a == i for j in [b]} | \
                         {j for (a, b) in adjacency if b == i for j in [a]}
            for j in neighbors_i:
                if j <= i:
                    continue
                neighbors_j = {k for (a, b) in adjacency if a == j for k in [b]} | \
                             {k for (a, b) in adjacency if b == j for k in [a]}
                common = neighbors_i & neighbors_j
                for k in common:
                    if k > j:
                        triangles.append((i, j, k))
        
        return cls(
            n_vertices=n_items,
            edges=edges,
            edge_weights=np.array(weights),
            triangles=triangles if triangles else None
        )


class DiscreteHodgeRank:
    """
    Discrete Hodge decomposition for preference ranking.
    
    This implements the HodgeRank algorithm from Jiang et al. (2011) which
    decomposes preference data into transitive (gradient) and cyclic
    (curl + harmonic) components.
    
    Usage:
        hodge = DiscreteHodgeRank()
        components = hodge.decompose(preference_graph)
        
        # For reward model training, use ONLY gradient:
        transitive_ranking = hodge.extract_global_ranking(components)
        reliability = components.reliability_score
        
        # Discard curl and harmonic - they represent inconsistencies
    """
    
    def __init__(self, regularization: float = 1e-6):
        """
        Args:
            regularization: Small value for numerical stability in linear solves
        """
        self.regularization = regularization
    
    def decompose(self, graph: PreferenceGraph) -> HodgeComponents:
        """
        Compute the Hodge decomposition of preference edge flows.
        
        f = ∇φ + δψ + h
        
        where:
        - ∇φ is the gradient (exact) component
        - δψ is the curl (coexact) component  
        - h is the harmonic component
        
        Args:
            graph: PreferenceGraph with edge weights
            
        Returns:
            HodgeComponents with the three orthogonal components
        """
        n = graph.n_vertices
        m = len(graph.edges)
        
        if m == 0:
            return HodgeComponents(
                gradient=np.array([]),
                curl=np.array([]),
                harmonic=np.array([]),
                edge_indices=[],
                vertex_potential=np.zeros(n)
            )
        
        # Build incidence matrix B₀: vertices → edges
        # B₀[e, v] = +1 if v is head of e, -1 if v is tail
        B0 = self._build_vertex_edge_incidence(n, graph.edges)
        
        # Edge flow vector
        f = graph.edge_weights.copy()
        
        # === Gradient Component ===
        # Solve for potential φ: L₀φ = B₀ᵀf where L₀ = B₀ᵀB₀
        # Then gradient = B₀φ
        L0 = B0.T @ B0  # Vertex Laplacian
        rhs = B0.T @ f
        
        # Add regularization and solve
        L0_reg = L0 + self.regularization * diags([1.0] * n)
        phi, _ = cg(L0_reg, rhs, tol=1e-10)
        
        # Center potential (remove arbitrary constant)
        phi = phi - np.mean(phi)
        
        gradient = B0 @ phi
        
        # === Harmonic Component ===
        # Harmonic = kernel(L₁) where L₁ = B₀B₀ᵀ + B₁ᵀB₁
        # For graphs without triangles, harmonic depends on graph topology (cycles)
        if graph.triangles:
            B1 = self._build_edge_triangle_incidence(graph.edges, graph.triangles)
            L1 = B0 @ B0.T + B1.T @ B1
        else:
            # No triangles: only vertex Laplacian contribution
            L1 = B0 @ B0.T
        
        # Find harmonic component (kernel of L₁)
        harmonic = self._project_to_kernel(f - gradient, L1)
        
        # === Curl Component ===
        # Curl is the remainder: f - gradient - harmonic
        curl = f - gradient - harmonic
        
        return HodgeComponents(
            gradient=gradient,
            curl=curl,
            harmonic=harmonic,
            edge_indices=graph.edges,
            vertex_potential=phi
        )
    
    def extract_global_ranking(self, components: HodgeComponents) -> np.ndarray:
        """
        Extract the global ranking scores from the gradient component.
        
        The potential φ satisfies: preference i→j has strength ≈ φ[i] - φ[j]
        Higher φ = more preferred.
        
        Args:
            components: Result of decompose()
            
        Returns:
            Array of ranking scores (higher = more preferred)
        """
        if components.vertex_potential is None:
            raise ValueError("No vertex potential available")
        return components.vertex_potential.copy()
    
    def filter_preferences_for_training(
        self,
        graph: PreferenceGraph,
        components: Optional[HodgeComponents] = None
    ) -> List[Tuple[int, int, float]]:
        """
        Extract only the transitive preferences for reward model training.
        
        This returns the gradient component as pairwise preferences,
        discarding the cyclic (curl + harmonic) noise.
        
        Args:
            graph: Original preference graph
            components: Pre-computed decomposition (computed if None)
            
        Returns:
            List of (preferred, less_preferred, strength) tuples
            representing the transitive consensus
        """
        if components is None:
            components = self.decompose(graph)
        
        filtered = []
        for idx, (i, j) in enumerate(components.edge_indices):
            grad_weight = components.gradient[idx]
            if abs(grad_weight) > 1e-6:
                if grad_weight > 0:
                    filtered.append((i, j, grad_weight))
                else:
                    filtered.append((j, i, -grad_weight))
        
        return filtered
    
    def _build_vertex_edge_incidence(
        self, 
        n_vertices: int, 
        edges: List[Tuple[int, int]]
    ) -> csr_matrix:
        """
        Build vertex-edge incidence matrix B₀.
        
        B₀[e, v] = +1 if e = (v, _), -1 if e = (_, v)
        
        This is the discrete gradient operator: (B₀φ)[e] = φ[head] - φ[tail]
        """
        m = len(edges)
        row, col, data = [], [], []
        
        for e_idx, (i, j) in enumerate(edges):
            # Edge e goes from i to j
            # Convention: positive flow = i preferred over j
            row.extend([e_idx, e_idx])
            col.extend([i, j])
            data.extend([1.0, -1.0])
        
        return csr_matrix((data, (row, col)), shape=(m, n_vertices))
    
    def _build_edge_triangle_incidence(
        self,
        edges: List[Tuple[int, int]],
        triangles: List[Tuple[int, int, int]]
    ) -> csr_matrix:
        """
        Build edge-triangle incidence matrix B₁.
        
        B₁[t, e] = ±1 if edge e is on boundary of triangle t
        
        This is the discrete curl operator.
        """
        edge_to_idx = {e: idx for idx, e in enumerate(edges)}
        # Also add reverse edges
        for idx, (i, j) in enumerate(edges):
            edge_to_idx[(j, i)] = idx
        
        m = len(edges)
        n_triangles = len(triangles)
        
        if n_triangles == 0:
            return csr_matrix((m, 1))  # Dummy
        
        row, col, data = [], [], []
        
        for t_idx, (i, j, k) in enumerate(triangles):
            # Triangle boundary: (i,j) + (j,k) + (k,i)
            # or equivalently: (i,j) + (j,k) - (i,k)
            for edge, sign in [((i, j), 1), ((j, k), 1), ((k, i), 1)]:
                if edge in edge_to_idx:
                    e_idx = edge_to_idx[edge]
                    # Check orientation
                    if edges[e_idx] == edge:
                        row.append(t_idx)
                        col.append(e_idx)
                        data.append(sign)
                    else:
                        row.append(t_idx)
                        col.append(e_idx)
                        data.append(-sign)
        
        return csr_matrix((data, (row, col)), shape=(n_triangles, m))
    
    def _project_to_kernel(
        self, 
        v: np.ndarray, 
        L: csr_matrix,
        n_components: int = 10
    ) -> np.ndarray:
        """
        Project vector v onto kernel of Laplacian L.
        
        The kernel of L₁ is the harmonic subspace.
        """
        if v.shape[0] == 0:
            return v
        
        try:
            # Find smallest eigenvalues/eigenvectors
            k = min(n_components, L.shape[0] - 2)
            if k < 1:
                return np.zeros_like(v)
            
            eigenvalues, eigenvectors = eigsh(L, k=k, which='SM', tol=1e-6)
            
            # Keep only eigenvectors with eigenvalue ≈ 0 (kernel)
            kernel_mask = np.abs(eigenvalues) < 1e-4
            kernel_basis = eigenvectors[:, kernel_mask]
            
            if kernel_basis.shape[1] == 0:
                return np.zeros_like(v)
            
            # Project onto kernel
            coeffs = kernel_basis.T @ v
            projection = kernel_basis @ coeffs
            
            return projection
            
        except Exception as e:
            warnings.warn(f"Kernel projection failed: {e}, returning zeros")
            return np.zeros_like(v)


class TransitiveRewardTrainer:
    """
    Reward model trainer that uses only transitive preferences.
    
    This wrapper ensures the reward model is trained ONLY on the gradient
    component of preference data, eliminating cyclic inconsistencies
    that enable reward hacking.
    """
    
    def __init__(
        self,
        hodge_rank: Optional[DiscreteHodgeRank] = None,
        min_reliability: float = 0.5
    ):
        """
        Args:
            hodge_rank: HodgeRank instance (created if None)
            min_reliability: Minimum reliability score to accept batch
        """
        self.hodge_rank = hodge_rank or DiscreteHodgeRank()
        self.min_reliability = min_reliability
        
        # Statistics
        self.total_comparisons_seen = 0
        self.total_comparisons_used = 0
        self.reliability_history: List[float] = []
    
    def filter_batch(
        self,
        comparisons: List[Tuple[int, int, float]],
        n_items: int
    ) -> Tuple[List[Tuple[int, int, float]], Dict[str, Any]]:
        """
        Filter a batch of comparisons to extract transitive component.
        
        Args:
            comparisons: Raw pairwise comparisons (winner, loser, strength)
            n_items: Number of items in this batch
            
        Returns:
            (filtered_comparisons, metadata) where metadata includes
            reliability score and energy breakdown
        """
        self.total_comparisons_seen += len(comparisons)
        
        # Build preference graph
        graph = PreferenceGraph.from_pairwise_comparisons(
            n_items=n_items,
            comparisons=comparisons
        )
        
        # Compute Hodge decomposition
        components = self.hodge_rank.decompose(graph)
        
        # Extract transitive preferences
        filtered = self.hodge_rank.filter_preferences_for_training(
            graph, components
        )
        
        self.total_comparisons_used += len(filtered)
        self.reliability_history.append(components.reliability_score)
        
        metadata = {
            "reliability": components.reliability_score,
            "gradient_energy": components.gradient_energy,
            "curl_energy": components.curl_energy,
            "harmonic_energy": components.harmonic_energy,
            "n_input": len(comparisons),
            "n_output": len(filtered),
            "accept_batch": components.reliability_score >= self.min_reliability
        }
        
        return filtered, metadata
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get training statistics."""
        return {
            "total_seen": self.total_comparisons_seen,
            "total_used": self.total_comparisons_used,
            "usage_rate": self.total_comparisons_used / max(1, self.total_comparisons_seen),
            "mean_reliability": np.mean(self.reliability_history) if self.reliability_history else 0.0,
            "min_reliability": np.min(self.reliability_history) if self.reliability_history else 0.0,
            "max_reliability": np.max(self.reliability_history) if self.reliability_history else 0.0,
        }

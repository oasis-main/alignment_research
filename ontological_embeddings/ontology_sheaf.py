"""
Ontology Sheaf Module

Sheaf-theoretic coherence checking for ontology induction.
Computes H⁰ (global sections) and H¹ (obstructions) to detect
ontological gaps and inconsistencies.

Reference: Robinson (2014), "Topological Signal Processing"
           Bodnar et al. (2022), "Neural Sheaf Diffusion"
"""

import numpy as np
import scipy.linalg
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ConsistencyStatus(Enum):
    """Status of sheaf consistency check."""
    CONSISTENT = "consistent"      # H¹ = 0, perfect gluing
    PARTIAL = "partial"            # H¹ small, minor conflicts
    INCONSISTENT = "inconsistent"  # H¹ large, major conflicts


@dataclass
class OntologyTriple:
    """A single ontological claim: (source, target, relation)."""
    source: str
    target: str
    relation: str
    
    def __hash__(self):
        return hash((self.source, self.target, self.relation))
    
    def __eq__(self, other):
        return (self.source, self.target, self.relation) == \
               (other.source, other.target, other.relation)


@dataclass
class LocalSection:
    """A local section: ontological claims from a single source/chunk."""
    section_id: str
    triples: Set[OntologyTriple]
    source_document: Optional[str] = None
    confidence: float = 1.0


@dataclass
class OntologyGap:
    """An obstruction (H¹ element) representing conflicting claims."""
    gap_id: str
    conflicting_sections: List[str]
    conflicting_triples: List[OntologyTriple]
    gap_type: str  # "contradiction", "missing_link", "cycle"
    severity: float  # 0-1, how severe the conflict is
    description: str = ""


@dataclass
class CohomologyResult:
    """Result of sheaf cohomology computation."""
    dim_H0: int                      # Dimension of global sections
    dim_H1: int                      # Dimension of obstructions
    consistency_score: float         # 0-1, higher = more consistent
    status: ConsistencyStatus
    global_sections: List[Set[OntologyTriple]]  # H⁰ representatives
    obstructions: List[OntologyGap]             # H¹ representatives
    sheaf_laplacian_eigenvalues: np.ndarray


class OntologySheaf:
    """
    Sheaf structure over an induced ontology.
    
    Models the ontology as a simplicial complex where:
    - 0-simplices (vertices) = types/concepts
    - 1-simplices (edges) = relations/morphisms
    - Local sections = claims from individual sources
    - Global sections = consistent unified ontology
    
    H⁰ measures global consistency.
    H¹ measures where/how local sections fail to glue.
    """
    
    def __init__(self):
        self.local_sections: Dict[str, LocalSection] = {}
        self.all_types: Set[str] = set()
        self.all_relations: Set[str] = set()
        self.type_to_idx: Dict[str, int] = {}
        self.idx_to_type: Dict[int, str] = {}
        self._laplacian_cache: Optional[np.ndarray] = None
        
    def add_local_section(self, section: LocalSection):
        """Add a local section (claims from a source)."""
        self.local_sections[section.section_id] = section
        
        # Update type/relation registry
        for triple in section.triples:
            self.all_types.add(triple.source)
            self.all_types.add(triple.target)
            self.all_relations.add(triple.relation)
        
        # Rebuild indices
        self._rebuild_indices()
        self._laplacian_cache = None
        
    def add_triples(self, section_id: str, triples: List[Tuple[str, str, str]],
                    source_doc: Optional[str] = None):
        """Convenience method to add triples as a local section."""
        triple_set = {OntologyTriple(s, t, r) for s, t, r in triples}
        section = LocalSection(
            section_id=section_id,
            triples=triple_set,
            source_document=source_doc
        )
        self.add_local_section(section)
        
    def _rebuild_indices(self):
        """Rebuild type-to-index mappings."""
        sorted_types = sorted(self.all_types)
        self.type_to_idx = {t: i for i, t in enumerate(sorted_types)}
        self.idx_to_type = {i: t for i, t in enumerate(sorted_types)}
        
    def _build_adjacency_matrix(self) -> np.ndarray:
        """Build weighted adjacency matrix from all sections."""
        n = len(self.all_types)
        if n == 0:
            return np.array([[]])
        
        A = np.zeros((n, n))
        
        for section in self.local_sections.values():
            weight = section.confidence
            for triple in section.triples:
                i = self.type_to_idx[triple.source]
                j = self.type_to_idx[triple.target]
                A[i, j] += weight
                A[j, i] += weight  # Symmetric for Laplacian
                
        return A
    
    def _build_sheaf_laplacian(self) -> np.ndarray:
        """
        Build the Sheaf Laplacian matrix.
        
        L = D - A where D is degree matrix, A is adjacency.
        Eigenvalues reveal cohomological structure:
        - # of zero eigenvalues = dim(H⁰) = connected components
        - Small non-zero eigenvalues relate to H¹
        """
        if self._laplacian_cache is not None:
            return self._laplacian_cache
            
        A = self._build_adjacency_matrix()
        if A.size == 0:
            return np.array([[]])
            
        D = np.diag(np.sum(A, axis=1))
        L = D - A
        
        self._laplacian_cache = L
        return L
    
    def _compute_boundary_operators(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute boundary operators for simplicial chain complex.
        
        C₀ (vertices) ← ∂₁ ← C₁ (edges) ← ∂₂ ← C₂ (triangles)
        
        Returns (∂₁, ∂₂) matrices.
        """
        n_types = len(self.all_types)
        
        # Collect all edges (relations)
        edges = []
        for section in self.local_sections.values():
            for triple in section.triples:
                edge = (triple.source, triple.target, triple.relation)
                if edge not in edges:
                    edges.append(edge)
        
        n_edges = len(edges)
        edge_to_idx = {e: i for i, e in enumerate(edges)}
        
        # ∂₁: C₁ → C₀ (boundary of edge = target - source)
        d1 = np.zeros((n_types, n_edges))
        for idx, (src, tgt, _) in enumerate(edges):
            i_src = self.type_to_idx[src]
            i_tgt = self.type_to_idx[tgt]
            d1[i_src, idx] = -1
            d1[i_tgt, idx] = 1
            
        # ∂₂: C₂ → C₁ (boundary of triangle = sum of edges)
        # Detect triangles: paths of length 2 that close
        triangles = []
        for e1 in edges:
            for e2 in edges:
                if e1[1] == e2[0]:  # e1 ends where e2 starts
                    # Check if there's an edge closing the triangle
                    for e3 in edges:
                        if e3[0] == e2[1] and e3[1] == e1[0]:
                            tri = (e1, e2, e3)
                            if tri not in triangles:
                                triangles.append(tri)
        
        n_triangles = len(triangles)
        d2 = np.zeros((n_edges, n_triangles))
        
        for t_idx, (e1, e2, e3) in enumerate(triangles):
            d2[edge_to_idx[e1], t_idx] = 1
            d2[edge_to_idx[e2], t_idx] = 1
            d2[edge_to_idx[e3], t_idx] = -1  # Opposite orientation
            
        return d1, d2
    
    def compute_cohomology(self) -> CohomologyResult:
        """
        Compute H⁰ and H¹ of the ontology sheaf.
        
        H⁰ = ker(L) = global sections (consistent parts)
        H¹ = coker(∂₁) ∩ ker(∂₂*) = obstructions (conflicts)
        
        In practice, we use spectral analysis of the Laplacian.
        """
        if len(self.all_types) == 0:
            return CohomologyResult(
                dim_H0=0, dim_H1=0, consistency_score=1.0,
                status=ConsistencyStatus.CONSISTENT,
                global_sections=[], obstructions=[],
                sheaf_laplacian_eigenvalues=np.array([])
            )
        
        L = self._build_sheaf_laplacian()
        eigenvalues = np.linalg.eigvalsh(L)
        
        # H⁰: dimension = number of near-zero eigenvalues
        tol = 1e-6
        dim_H0 = int(np.sum(np.abs(eigenvalues) < tol))
        
        # H¹: computed from boundary operators
        d1, d2 = self._compute_boundary_operators()
        
        # dim(H¹) = dim(ker(∂₁ᵀ)) - dim(im(∂₂))
        # Using rank-nullity theorem
        if d1.size > 0:
            rank_d1 = np.linalg.matrix_rank(d1)
            nullity_d1T = d1.shape[1] - rank_d1
        else:
            nullity_d1T = 0
            
        if d2.size > 0:
            rank_d2 = np.linalg.matrix_rank(d2)
        else:
            rank_d2 = 0
            
        dim_H1 = max(0, nullity_d1T - rank_d2)
        
        # Find obstructions (conflicts between sections)
        obstructions = self._identify_obstructions()
        
        # Compute consistency score
        n_triples = sum(len(s.triples) for s in self.local_sections.values())
        n_conflicts = len(obstructions)
        consistency_score = 1.0 - (n_conflicts / max(n_triples, 1))
        consistency_score = max(0.0, min(1.0, consistency_score))
        
        # Determine status
        if dim_H1 == 0 and len(obstructions) == 0:
            status = ConsistencyStatus.CONSISTENT
        elif consistency_score > 0.7:
            status = ConsistencyStatus.PARTIAL
        else:
            status = ConsistencyStatus.INCONSISTENT
            
        # Extract global sections (connected components in H⁰)
        global_sections = self._extract_global_sections(dim_H0)
        
        return CohomologyResult(
            dim_H0=dim_H0,
            dim_H1=dim_H1,
            consistency_score=consistency_score,
            status=status,
            global_sections=global_sections,
            obstructions=obstructions,
            sheaf_laplacian_eigenvalues=eigenvalues
        )
    
    def _identify_obstructions(self) -> List[OntologyGap]:
        """
        Identify specific conflicts between local sections.
        
        Types of obstructions:
        1. Contradiction: Same (source, target) with conflicting relations
        2. Cycle: Semantic cycle that shouldn't close
        3. Missing link: Expected composition doesn't hold
        """
        obstructions = []
        gap_counter = 0
        
        # Check for contradictions
        edge_to_sections: Dict[Tuple[str, str], Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        
        for section in self.local_sections.values():
            for triple in section.triples:
                edge = (triple.source, triple.target)
                edge_to_sections[edge][triple.relation].add(section.section_id)
        
        for edge, rel_map in edge_to_sections.items():
            if len(rel_map) > 1:
                # Multiple relations for same edge = potential contradiction
                conflicting_rels = list(rel_map.keys())
                conflicting_secs = set()
                conflicting_triples = []
                
                for rel, secs in rel_map.items():
                    conflicting_secs.update(secs)
                    conflicting_triples.append(
                        OntologyTriple(edge[0], edge[1], rel)
                    )
                
                # Check if relations are semantically conflicting
                if self._are_conflicting_relations(conflicting_rels):
                    gap = OntologyGap(
                        gap_id=f"gap_{gap_counter}",
                        conflicting_sections=list(conflicting_secs),
                        conflicting_triples=conflicting_triples,
                        gap_type="contradiction",
                        severity=0.8,
                        description=f"Conflicting relations for {edge[0]} → {edge[1]}: {conflicting_rels}"
                    )
                    obstructions.append(gap)
                    gap_counter += 1
        
        # Check for cycles (simplified: detect if same type appears twice in a path)
        cycle_gaps = self._detect_semantic_cycles()
        obstructions.extend(cycle_gaps)
        
        return obstructions
    
    def _are_conflicting_relations(self, relations: List[str]) -> bool:
        """Check if relations are semantically conflicting (antonyms, etc.)."""
        # Simple heuristic: check for antonym pairs
        antonym_pairs = [
            ("increases", "decreases"),
            ("creates", "destroys"),
            ("enables", "disables"),
            ("opens", "closes"),
            ("adds", "removes"),
            ("starts", "stops"),
        ]
        
        rel_set = set(r.lower() for r in relations)
        for a, b in antonym_pairs:
            if a in rel_set and b in rel_set:
                return True
        
        return False
    
    def _detect_semantic_cycles(self) -> List[OntologyGap]:
        """Detect problematic semantic cycles."""
        gaps = []
        
        # Build directed graph
        graph: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for section in self.local_sections.values():
            for triple in section.triples:
                graph[triple.source].append((triple.target, triple.relation))
        
        # DFS for cycles
        visited = set()
        rec_stack = set()
        cycle_paths = []
        
        def dfs(node: str, path: List[Tuple[str, str]]):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor, rel in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path + [(node, rel)])
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start_idx = next(
                        (i for i, (n, _) in enumerate(path) if n == neighbor),
                        len(path)
                    )
                    cycle = path[cycle_start_idx:] + [(node, rel)]
                    if len(cycle) >= 2:
                        cycle_paths.append(cycle)
            
            rec_stack.remove(node)
        
        for node in self.all_types:
            if node not in visited:
                dfs(node, [])
        
        # Convert cycles to gaps
        for i, cycle in enumerate(cycle_paths[:5]):  # Limit to 5 cycles
            triples = [
                OntologyTriple(n, cycle[(j+1) % len(cycle)][0] if j+1 < len(cycle) else cycle[0][0], r)
                for j, (n, r) in enumerate(cycle)
            ]
            gap = OntologyGap(
                gap_id=f"cycle_{i}",
                conflicting_sections=list(self.local_sections.keys()),
                conflicting_triples=triples,
                gap_type="cycle",
                severity=0.5,
                description=f"Semantic cycle detected: {' → '.join(n for n, _ in cycle)}"
            )
            gaps.append(gap)
        
        return gaps
    
    def _extract_global_sections(self, dim_H0: int) -> List[Set[OntologyTriple]]:
        """Extract representative global sections (connected components)."""
        if dim_H0 == 0:
            return []
        
        # Use union of all non-conflicting triples as the global section
        all_triples = set()
        for section in self.local_sections.values():
            all_triples.update(section.triples)
        
        # For simplicity, return the full union as a single global section
        # A more sophisticated implementation would separate by connected component
        return [all_triples]
    
    def topological_query(self, query_types: Set[str], 
                          diffusion_time: float = 1.0) -> List[str]:
        """
        Execute a topological query using Sheaf Laplacian diffusion.
        
        Args:
            query_types: Types mentioned in the query
            diffusion_time: How far to diffuse (larger = more spread)
            
        Returns:
            List of types activated by the diffusion
        """
        if len(self.all_types) == 0:
            return []
            
        L = self._build_sheaf_laplacian()
        n = len(self.all_types)
        
        # Initialize query as heat on specified types
        initial_state = np.zeros(n)
        for t in query_types:
            if t in self.type_to_idx:
                initial_state[self.type_to_idx[t]] = 1.0
        
        # Diffuse: exp(-t*L) @ initial_state using Krylov subspace approximation
        import scipy.sparse.linalg
        
        # Convert L to sparse format for expm_multiply if not already
        if not scipy.sparse.issparse(L):
            L_sparse = scipy.sparse.csr_matrix(L)
        else:
            L_sparse = L
            
        diffused = scipy.sparse.linalg.expm_multiply(-diffusion_time * L_sparse, initial_state)
        
        # Threshold and return activated types
        threshold = 0.1 * np.max(diffused) if np.max(diffused) > 0 else 0.1
        activated = [
            self.idx_to_type[i]
            for i, v in enumerate(diffused) if v > threshold
        ]
        
        return activated
    
    def surface_gaps(self) -> List[OntologyGap]:
        """
        Surface ontological gaps (H¹ ≠ 0 obstructions).
        
        These are NOT errors to force-resolve, but rather:
        - Legitimate branching variations in the domain
        - Conflicting expert opinions  
        - Contextual distinctions worth preserving
        """
        result = self.compute_cohomology()
        return result.obstructions
    
    def get_consistency_report(self) -> Dict[str, Any]:
        """Generate a human-readable consistency report."""
        result = self.compute_cohomology()
        
        report = {
            "status": result.status.value,
            "consistency_score": round(result.consistency_score, 3),
            "dim_H0": result.dim_H0,
            "dim_H1": result.dim_H1,
            "num_sections": len(self.local_sections),
            "num_types": len(self.all_types),
            "num_relations": len(self.all_relations),
            "obstructions": [
                {
                    "id": g.gap_id,
                    "type": g.gap_type,
                    "severity": g.severity,
                    "description": g.description,
                    "sections_involved": g.conflicting_sections
                }
                for g in result.obstructions
            ]
        }
        
        return report


def demo():
    """Demonstrate ontology sheaf with consistency checking."""
    print("=" * 60)
    print("Ontology Sheaf Demo: Consistency Checking via H⁰/H¹")
    print("=" * 60)
    
    sheaf = OntologySheaf()
    
    # Add consistent local sections
    print("\n--- Adding Consistent Sections ---")
    
    sheaf.add_triples("doc_1", [
        ("Customer", "Cart", "creates"),
        ("Cart", "Order", "becomes"),
        ("Order", "Payment", "requires"),
    ], source_doc="e-commerce-spec-v1.md")
    
    sheaf.add_triples("doc_2", [
        ("Order", "Invoice", "generates"),
        ("Invoice", "Payment", "requests"),
        ("Payment", "Delivery", "triggers"),
    ], source_doc="e-commerce-spec-v2.md")
    
    result = sheaf.compute_cohomology()
    print(f"  Status: {result.status.value}")
    print(f"  Consistency score: {result.consistency_score:.3f}")
    print(f"  dim(H⁰) = {result.dim_H0} (connected components)")
    print(f"  dim(H¹) = {result.dim_H1} (obstructions)")
    
    # Add conflicting section
    print("\n--- Adding Conflicting Section ---")
    
    sheaf.add_triples("doc_3_conflict", [
        ("Order", "Inventory", "increases"),  # Conflict with doc_4
    ], source_doc="warehouse-spec.md")
    
    sheaf.add_triples("doc_4_conflict", [
        ("Order", "Inventory", "decreases"),  # Conflict with doc_3
    ], source_doc="sales-spec.md")
    
    result = sheaf.compute_cohomology()
    print(f"  Status: {result.status.value}")
    print(f"  Consistency score: {result.consistency_score:.3f}")
    print(f"  dim(H⁰) = {result.dim_H0}")
    print(f"  dim(H¹) = {result.dim_H1}")
    
    # Show obstructions
    print("\n--- Surfaced Ontological Gaps ---")
    for gap in result.obstructions:
        print(f"  [{gap.gap_type}] {gap.description}")
        print(f"    Severity: {gap.severity}")
        print(f"    Sections: {gap.conflicting_sections}")
    
    # Topological query
    print("\n--- Topological Query (Sheaf Diffusion) ---")
    query = {"Customer"}
    activated = sheaf.topological_query(query, diffusion_time=2.0)
    print(f"  Query: {query}")
    print(f"  Activated types: {activated}")
    
    # Full report
    print("\n--- Consistency Report ---")
    report = sheaf.get_consistency_report()
    for key, value in report.items():
        if key != "obstructions":
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Demo complete. Ontology sheaf ready for integration.")
    print("=" * 60)


if __name__ == "__main__":
    demo()

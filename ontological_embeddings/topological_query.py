"""
Topological Querying Module

Implements Sheaf Laplacian diffusion for ontological queries with:
1. Constraint propagation
2. Proof engine integration for validation
3. Benchmarking vs naive graph traversal

Week 3 of HDC/Sheaf Integration (HANDOFF_06)

Reference: Robinson (2014), "Topological Signal Processing"
           Bodnar et al. (2022), "Neural Sheaf Diffusion"
"""

import numpy as np
import scipy.linalg
import time
from typing import Dict, List, Tuple, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from ontology_sheaf import OntologySheaf, OntologyTriple, CohomologyResult
from ghrr_encoder import GHRREncoder, OlogHDCEncoder, HypervectorConfig
from olog_core import OlogGraph
from proof_objects import ProofEngine, ProofObject, ProofMode, ProofStatus


class QueryStrategy(Enum):
    """Strategy for topological querying."""
    DIFFUSION = "diffusion"           # Sheaf Laplacian diffusion
    NAIVE_BFS = "naive_bfs"           # Standard BFS traversal
    HDC_SIMILARITY = "hdc_similarity" # Hyperdimensional similarity search
    HYBRID = "hybrid"                 # Diffusion + proof validation


@dataclass
class QueryConstraint:
    """A constraint on topological query results."""
    required_types: Set[str] = field(default_factory=set)      # Must include these types
    forbidden_types: Set[str] = field(default_factory=set)     # Must NOT include these
    required_relations: Set[str] = field(default_factory=set)  # Must use these relations
    max_path_length: int = 10
    min_confidence: float = 0.1


@dataclass
class QueryResult:
    """Result of a topological query."""
    query_types: Set[str]
    activated_types: List[str]
    activation_scores: Dict[str, float]
    valid_paths: List[List[Tuple[str, str, str]]]  # List of paths as (src, tgt, rel) triples
    proofs: List[ProofObject]
    execution_time_ms: float
    strategy_used: QueryStrategy
    constraints_satisfied: bool


@dataclass 
class BenchmarkResult:
    """Result of benchmarking query strategies."""
    strategy: QueryStrategy
    avg_time_ms: float
    std_time_ms: float
    avg_precision: float  # Fraction of results that are valid
    avg_recall: float     # Fraction of valid paths found
    num_trials: int


class TopologicalQueryEngine:
    """
    Engine for topological queries over ontology sheaves.
    
    Combines Sheaf Laplacian diffusion with proof validation
    for semantically-grounded retrieval.
    """
    
    def __init__(
        self,
        sheaf: OntologySheaf,
        proof_engine: Optional[ProofEngine] = None,
        ghrr_encoder: Optional[GHRREncoder] = None,
        default_strategy: QueryStrategy = QueryStrategy.HYBRID,
    ):
        self.sheaf = sheaf
        self.proof_engine = proof_engine
        self.ghrr = ghrr_encoder or GHRREncoder()
        self.default_strategy = default_strategy
        
        # Cache for HDC encodings
        self._type_hvs: Dict[str, np.ndarray] = {}
        self._morphism_hvs: Dict[str, np.ndarray] = {}
        
        # Build HDC representations
        self._build_hdc_index()
    
    def _build_hdc_index(self):
        """Build HDC hypervector index for similarity search."""
        for t in self.sheaf.all_types:
            self._type_hvs[t] = self.ghrr.encode_type(t)
        
        # Encode all edges from sections
        for section in self.sheaf.local_sections.values():
            for triple in section.triples:
                key = f"{triple.source}--{triple.relation}-->{triple.target}"
                self._morphism_hvs[key] = self.ghrr.encode_morphism(
                    triple.source, triple.target, triple.relation
                )
    
    def query(
        self,
        query_types: Set[str],
        constraints: Optional[QueryConstraint] = None,
        strategy: Optional[QueryStrategy] = None,
        diffusion_time: float = 1.0,
    ) -> QueryResult:
        """
        Execute a topological query.
        
        Args:
            query_types: Seed types for the query
            constraints: Optional constraints on results
            strategy: Query strategy (default: hybrid)
            diffusion_time: Diffusion parameter (larger = wider spread)
            
        Returns:
            QueryResult with activated types, valid paths, and proofs
        """
        start_time = time.perf_counter()
        
        strategy = strategy or self.default_strategy
        constraints = constraints or QueryConstraint()
        
        if strategy == QueryStrategy.DIFFUSION:
            result = self._query_diffusion(query_types, constraints, diffusion_time)
        elif strategy == QueryStrategy.NAIVE_BFS:
            result = self._query_bfs(query_types, constraints)
        elif strategy == QueryStrategy.HDC_SIMILARITY:
            result = self._query_hdc(query_types, constraints)
        else:  # HYBRID
            result = self._query_hybrid(query_types, constraints, diffusion_time)
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result.execution_time_ms = elapsed_ms
        result.strategy_used = strategy
        
        return result
    
    def _query_diffusion(
        self,
        query_types: Set[str],
        constraints: QueryConstraint,
        diffusion_time: float,
    ) -> QueryResult:
        """
        Query using Sheaf Laplacian diffusion.
        
        Diffuses "heat" from query types across the sheaf structure,
        finding types that are topologically connected.
        """
        if len(self.sheaf.all_types) == 0:
            return self._empty_result(query_types)
        
        L = self.sheaf._build_sheaf_laplacian()
        n = len(self.sheaf.all_types)
        
        # Initialize heat at query types
        initial_state = np.zeros(n)
        for t in query_types:
            if t in self.sheaf.type_to_idx:
                initial_state[self.sheaf.type_to_idx[t]] = 1.0
        
        # Diffuse: x(t) = exp(-t*L) @ x(0)
        diffused = scipy.linalg.expm(-diffusion_time * L) @ initial_state
        
        # Build activation scores
        activation_scores = {}
        for i, score in enumerate(diffused):
            type_name = self.sheaf.idx_to_type[i]
            activation_scores[type_name] = float(score)
        
        # Filter by constraints
        threshold = constraints.min_confidence * np.max(diffused) if np.max(diffused) > 0 else 0.1
        activated = [
            t for t, score in activation_scores.items()
            if score > threshold
            and t not in constraints.forbidden_types
            and (not constraints.required_types or t in constraints.required_types or t in query_types)
        ]
        
        # Ensure required types are included
        for req in constraints.required_types:
            if req in self.sheaf.all_types and req not in activated:
                activated.append(req)
        
        # Find valid paths (without proof validation in pure diffusion mode)
        valid_paths = self._extract_paths(query_types, set(activated), constraints)
        
        return QueryResult(
            query_types=query_types,
            activated_types=activated,
            activation_scores=activation_scores,
            valid_paths=valid_paths,
            proofs=[],
            execution_time_ms=0,
            strategy_used=QueryStrategy.DIFFUSION,
            constraints_satisfied=self._check_constraints(activated, constraints)
        )
    
    def _query_bfs(
        self,
        query_types: Set[str],
        constraints: QueryConstraint,
    ) -> QueryResult:
        """
        Query using naive BFS traversal.
        
        Standard graph search from query types - baseline for benchmarking.
        """
        # Build adjacency from sheaf sections
        adj: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for section in self.sheaf.local_sections.values():
            for triple in section.triples:
                adj[triple.source].append((triple.target, triple.relation))
                adj[triple.target].append((triple.source, f"inv_{triple.relation}"))
        
        visited = set()
        queue = list(query_types)
        depth = {t: 0 for t in query_types}
        activated = []
        activation_scores = {}
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            current_depth = depth.get(current, 0)
            if current_depth > constraints.max_path_length:
                continue
            
            if current not in constraints.forbidden_types:
                activated.append(current)
                # Score decays with depth
                activation_scores[current] = 1.0 / (1.0 + current_depth)
            
            for neighbor, rel in adj.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)
                    depth[neighbor] = current_depth + 1
        
        valid_paths = self._extract_paths(query_types, set(activated), constraints)
        
        return QueryResult(
            query_types=query_types,
            activated_types=activated,
            activation_scores=activation_scores,
            valid_paths=valid_paths,
            proofs=[],
            execution_time_ms=0,
            strategy_used=QueryStrategy.NAIVE_BFS,
            constraints_satisfied=self._check_constraints(activated, constraints)
        )
    
    def _query_hdc(
        self,
        query_types: Set[str],
        constraints: QueryConstraint,
    ) -> QueryResult:
        """
        Query using HDC hypervector similarity.
        
        Finds types whose hypervectors are similar to the query bundle.
        """
        if not self._type_hvs:
            return self._empty_result(query_types)
        
        # Bundle query types
        query_hvs = [self._type_hvs[t] for t in query_types if t in self._type_hvs]
        if not query_hvs:
            return self._empty_result(query_types)
        
        query_bundle = self.ghrr.superpose(*query_hvs)
        
        # Compute similarities
        activation_scores = {}
        for t, hv in self._type_hvs.items():
            sim = self.ghrr.similarity(query_bundle, hv)
            activation_scores[t] = sim
        
        # Filter and rank
        threshold = constraints.min_confidence
        activated = [
            t for t, score in sorted(activation_scores.items(), key=lambda x: -x[1])
            if score > threshold
            and t not in constraints.forbidden_types
        ]
        
        valid_paths = self._extract_paths(query_types, set(activated), constraints)
        
        return QueryResult(
            query_types=query_types,
            activated_types=activated,
            activation_scores=activation_scores,
            valid_paths=valid_paths,
            proofs=[],
            execution_time_ms=0,
            strategy_used=QueryStrategy.HDC_SIMILARITY,
            constraints_satisfied=self._check_constraints(activated, constraints)
        )
    
    def _query_hybrid(
        self,
        query_types: Set[str],
        constraints: QueryConstraint,
        diffusion_time: float,
    ) -> QueryResult:
        """
        Hybrid query: Diffusion + Proof Validation.
        
        1. Use diffusion to find candidate types
        2. Extract candidate paths
        3. Validate each path with proof engine
        4. Return only proven paths
        """
        # Step 1: Diffusion to get candidates
        diffusion_result = self._query_diffusion(query_types, constraints, diffusion_time)
        
        # Step 2: Extract candidate paths
        candidate_paths = diffusion_result.valid_paths
        
        # Step 3: Validate with proof engine (if available)
        proofs = []
        validated_paths = []
        
        if self.proof_engine:
            for path in candidate_paths:
                if not path:
                    continue
                
                # Construct claim from path
                source = path[0][0]
                target = path[-1][1]
                relations = [step[2] for step in path]
                
                # Try to prove the path
                claim = f"{source} reaches {target}"
                proof = self.proof_engine.prove(claim)
                proofs.append(proof)
                
                if proof.is_valid:
                    validated_paths.append(path)
        else:
            # No proof engine - accept all diffusion paths
            validated_paths = candidate_paths
        
        return QueryResult(
            query_types=query_types,
            activated_types=diffusion_result.activated_types,
            activation_scores=diffusion_result.activation_scores,
            valid_paths=validated_paths,
            proofs=proofs,
            execution_time_ms=0,
            strategy_used=QueryStrategy.HYBRID,
            constraints_satisfied=self._check_constraints(
                diffusion_result.activated_types, constraints
            )
        )
    
    def _extract_paths(
        self,
        sources: Set[str],
        targets: Set[str],
        constraints: QueryConstraint,
    ) -> List[List[Tuple[str, str, str]]]:
        """Extract paths from sources to targets using sheaf structure."""
        # Build adjacency
        adj: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for section in self.sheaf.local_sections.values():
            for triple in section.triples:
                adj[triple.source].append((triple.target, triple.relation))
        
        paths = []
        
        for source in sources:
            for target in targets:
                if source == target:
                    continue
                
                # BFS for paths
                found_paths = self._bfs_paths(
                    source, target, adj, 
                    constraints.max_path_length,
                    constraints.required_relations
                )
                paths.extend(found_paths)
        
        return paths[:20]  # Limit results
    
    def _bfs_paths(
        self,
        source: str,
        target: str,
        adj: Dict[str, List[Tuple[str, str]]],
        max_length: int,
        required_relations: Set[str],
    ) -> List[List[Tuple[str, str, str]]]:
        """Find paths from source to target."""
        if source not in adj:
            return []
        
        paths = []
        queue = [(source, [])]  # (current_node, path_so_far)
        
        while queue and len(paths) < 5:  # Limit paths per source-target pair
            current, path = queue.pop(0)
            
            if len(path) > max_length:
                continue
            
            if current == target and path:
                # Check required relations
                path_rels = {step[2] for step in path}
                if not required_relations or required_relations <= path_rels:
                    paths.append(path)
                continue
            
            for neighbor, rel in adj.get(current, []):
                if not any(step[1] == neighbor for step in path):  # Avoid cycles
                    new_step = (current, neighbor, rel)
                    queue.append((neighbor, path + [new_step]))
        
        return paths
    
    def _check_constraints(
        self,
        activated: List[str],
        constraints: QueryConstraint,
    ) -> bool:
        """Check if constraints are satisfied."""
        activated_set = set(activated)
        
        # Check required types
        if constraints.required_types and not constraints.required_types <= activated_set:
            return False
        
        # Check forbidden types
        if constraints.forbidden_types & activated_set:
            return False
        
        return True
    
    def _empty_result(self, query_types: Set[str]) -> QueryResult:
        """Return empty result."""
        return QueryResult(
            query_types=query_types,
            activated_types=[],
            activation_scores={},
            valid_paths=[],
            proofs=[],
            execution_time_ms=0,
            strategy_used=self.default_strategy,
            constraints_satisfied=True
        )
    
    def benchmark(
        self,
        query_types: Set[str],
        ground_truth_paths: Optional[List[List[Tuple[str, str, str]]]] = None,
        num_trials: int = 10,
        strategies: Optional[List[QueryStrategy]] = None,
    ) -> Dict[str, BenchmarkResult]:
        """
        Benchmark different query strategies.
        
        Args:
            query_types: Types to query
            ground_truth_paths: Known valid paths (for precision/recall)
            num_trials: Number of timing trials
            strategies: Strategies to benchmark (default: all)
            
        Returns:
            Dictionary mapping strategy name to BenchmarkResult
        """
        strategies = strategies or list(QueryStrategy)
        results = {}
        
        gt_set = set(tuple(tuple(step) for step in path) for path in (ground_truth_paths or []))
        
        for strategy in strategies:
            times = []
            precisions = []
            recalls = []
            
            for _ in range(num_trials):
                start = time.perf_counter()
                result = self.query(query_types, strategy=strategy)
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
                
                # Compute precision/recall if ground truth provided
                if ground_truth_paths:
                    found_set = set(tuple(tuple(step) for step in path) for path in result.valid_paths)
                    
                    if found_set:
                        precision = len(found_set & gt_set) / len(found_set)
                    else:
                        precision = 1.0 if not gt_set else 0.0
                    
                    if gt_set:
                        recall = len(found_set & gt_set) / len(gt_set)
                    else:
                        recall = 1.0
                    
                    precisions.append(precision)
                    recalls.append(recall)
            
            results[strategy.value] = BenchmarkResult(
                strategy=strategy,
                avg_time_ms=np.mean(times),
                std_time_ms=np.std(times),
                avg_precision=np.mean(precisions) if precisions else 0.0,
                avg_recall=np.mean(recalls) if recalls else 0.0,
                num_trials=num_trials,
            )
        
        return results


def demo():
    """Demonstrate topological querying with benchmarking."""
    print("=" * 70)
    print("  TOPOLOGICAL QUERY ENGINE DEMO")
    print("  Week 3: Sheaf Diffusion + Proof Validation")
    print("=" * 70)
    
    # Build ontology sheaf
    sheaf = OntologySheaf()
    
    sheaf.add_triples("ecommerce_v1", [
        ("Customer", "Cart", "creates"),
        ("Cart", "Order", "becomes"),
        ("Order", "Payment", "requires"),
        ("Payment", "Delivery", "triggers"),
    ])
    
    sheaf.add_triples("ecommerce_v2", [
        ("Order", "Invoice", "generates"),
        ("Invoice", "Payment", "requests"),
        ("Delivery", "Customer", "completes_cycle_to"),
    ])
    
    # Build proof engine
    olog = OlogGraph(name="ECommerce")
    for t in sheaf.all_types:
        olog.add_type(t)
    for section in sheaf.local_sections.values():
        for triple in section.triples:
            olog.add_aspect(triple.source, triple.target, triple.relation)
    
    proof_engine = ProofEngine(olog, mode=ProofMode.REACHABILITY)
    
    # Create query engine
    engine = TopologicalQueryEngine(
        sheaf=sheaf,
        proof_engine=proof_engine,
        default_strategy=QueryStrategy.HYBRID,
    )
    
    # Run queries
    print("\n--- Query 1: From Customer ---")
    result = engine.query({"Customer"}, diffusion_time=2.0)
    
    print(f"  Query types: {result.query_types}")
    print(f"  Activated types: {result.activated_types}")
    print(f"  Execution time: {result.execution_time_ms:.2f}ms")
    print(f"  Valid paths found: {len(result.valid_paths)}")
    print(f"  Proofs generated: {len(result.proofs)}")
    
    print("\n  Top activations:")
    sorted_scores = sorted(result.activation_scores.items(), key=lambda x: -x[1])
    for t, score in sorted_scores[:5]:
        print(f"    {t}: {score:.4f}")
    
    # Query with constraints
    print("\n--- Query 2: Customer to Payment (constrained) ---")
    constraints = QueryConstraint(
        required_types={"Payment"},
        forbidden_types={"Invoice"},
        max_path_length=5,
    )
    result2 = engine.query({"Customer"}, constraints=constraints)
    
    print(f"  Activated: {result2.activated_types}")
    print(f"  Constraints satisfied: {result2.constraints_satisfied}")
    print(f"  Paths found: {len(result2.valid_paths)}")
    
    if result2.valid_paths:
        print("\n  Sample path:")
        for step in result2.valid_paths[0]:
            print(f"    {step[0]} --{step[2]}--> {step[1]}")
    
    # Benchmark strategies
    print("\n--- Benchmark: Strategy Comparison ---")
    
    benchmark_results = engine.benchmark(
        query_types={"Customer"},
        num_trials=20,
        strategies=[QueryStrategy.DIFFUSION, QueryStrategy.NAIVE_BFS, QueryStrategy.HDC_SIMILARITY],
    )
    
    print(f"\n  {'Strategy':<20} {'Avg Time (ms)':<15} {'Std (ms)':<10}")
    print("  " + "-" * 45)
    
    for name, br in benchmark_results.items():
        print(f"  {name:<20} {br.avg_time_ms:<15.3f} {br.std_time_ms:<10.3f}")
    
    # Test hybrid with proof validation
    print("\n--- Query 3: Hybrid with Proof Validation ---")
    result3 = engine.query(
        {"Customer", "Order"},
        strategy=QueryStrategy.HYBRID,
        diffusion_time=1.5,
    )
    
    print(f"  Activated: {result3.activated_types}")
    print(f"  Proofs: {len(result3.proofs)}")
    
    valid_proofs = [p for p in result3.proofs if p.is_valid]
    invalid_proofs = [p for p in result3.proofs if not p.is_valid]
    
    print(f"    Valid: {len(valid_proofs)}")
    print(f"    Invalid: {len(invalid_proofs)}")
    
    if valid_proofs:
        print("\n  Sample valid proof:")
        print(valid_proofs[0].render_diagram(indent=2))
    
    # Cohomology integration
    print("\n--- Cohomology Check ---")
    cohom = sheaf.compute_cohomology()
    print(f"  H⁰ dimension: {cohom.dim_H0} (global sections)")
    print(f"  H¹ dimension: {cohom.dim_H1} (obstructions)")
    print(f"  Consistency: {cohom.consistency_score:.3f}")
    print(f"  Status: {cohom.status.value}")
    
    print("\n" + "=" * 70)
    print("  Demo complete. Week 3 implementation ready.")
    print("=" * 70)


if __name__ == "__main__":
    demo()

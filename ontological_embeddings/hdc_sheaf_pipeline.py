"""
End-to-End HDC/Sheaf Pipeline

Unified pipeline: Document → HDC Encoding → Sheaf Construction → Query → Proof

Week 4 of HDC/Sheaf Integration (HANDOFF_06)

Components:
1. Document ingestion and triple extraction
2. HDC encoding via GHRR
3. Sheaf construction and cohomology
4. Topological querying with proof validation
5. Evaluation metrics and benchmarking
"""

import json
import time
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict
from enum import Enum

from ghrr_encoder import GHRREncoder, OlogHDCEncoder, HypervectorConfig
from ontology_sheaf import OntologySheaf, OntologyTriple, CohomologyResult, ConsistencyStatus
from topological_query import TopologicalQueryEngine, QueryConstraint, QueryResult, QueryStrategy
from olog_core import OlogGraph
from proof_objects import ProofEngine, ProofMode, ProofObject, ProofStatus
from benchmark_datasets import (
    BenchmarkSuite, KGDataset, KGTriple, ConflictDataset,
    FB15K237Loader, WN18RRLoader, Text2KGLoader
)


class EvaluationMetric(Enum):
    """Metrics for pipeline evaluation."""
    CONSISTENCY_SCORE = "consistency_score"
    H1_DIMENSION = "h1_dimension"
    QUERY_LATENCY_MS = "query_latency_ms"
    PROOF_SUCCESS_RATE = "proof_success_rate"
    CONFLICT_DETECTION_RATE = "conflict_detection_rate"
    HDC_ENCODING_TIME_MS = "hdc_encoding_time_ms"


@dataclass
class PipelineConfig:
    """Configuration for the HDC/Sheaf pipeline."""
    hdc_dimension: int = 4096
    diffusion_time: float = 1.5
    proof_mode: ProofMode = ProofMode.REACHABILITY
    max_proof_depth: int = 10
    conflict_threshold: float = 0.7
    batch_size: int = 1000


@dataclass
class PipelineResult:
    """Result of running the pipeline on a dataset."""
    dataset_name: str
    num_triples: int
    num_entities: int
    num_relations: int
    
    # Cohomology metrics
    h0_dimension: int
    h1_dimension: int
    consistency_score: float
    consistency_status: str
    
    # Performance metrics
    encoding_time_ms: float
    sheaf_build_time_ms: float
    cohomology_time_ms: float
    
    # Query metrics
    sample_queries: List[Dict]
    avg_query_latency_ms: float
    
    # Proof metrics
    proof_success_rate: float
    
    # Conflict detection (if applicable)
    conflicts_injected: int = 0
    conflicts_detected: int = 0
    conflict_detection_rate: float = 0.0


@dataclass
class ConflictDetectionResult:
    """Result of conflict detection evaluation."""
    base_h1: int
    conflicted_h1: int
    h1_increase: int
    base_consistency: float
    conflicted_consistency: float
    consistency_drop: float
    detected_conflicts: int
    total_conflicts: int
    detection_rate: float


class HDCSheafPipeline:
    """
    End-to-end pipeline for HDC/Sheaf-based ontology processing.
    
    Usage:
        pipeline = HDCSheafPipeline()
        
        # Process a KG dataset
        result = pipeline.process_kg_dataset(fb15k237)
        
        # Evaluate conflict detection
        conflict_result = pipeline.evaluate_conflict_detection(base_triples, conflicts)
        
        # Query the pipeline
        query_result = pipeline.query({"Person", "Organization"})
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # Core components
        self.ghrr = GHRREncoder(HypervectorConfig(dim=self.config.hdc_dimension))
        self.sheaf = OntologySheaf()
        self.olog = OlogGraph(name="pipeline_olog")
        self.proof_engine: Optional[ProofEngine] = None
        self.query_engine: Optional[TopologicalQueryEngine] = None
        
        # State
        self._initialized = False
        self._triples: List[KGTriple] = []
        self._hdc_cache: Dict[str, np.ndarray] = {}
    
    def reset(self):
        """Reset pipeline state."""
        self.sheaf = OntologySheaf()
        self.olog = OlogGraph(name="pipeline_olog")
        self.proof_engine = None
        self.query_engine = None
        self._initialized = False
        self._triples = []
        self._hdc_cache = {}
    
    def ingest_triples(
        self,
        triples: List[KGTriple],
        source_name: str = "default",
    ) -> Tuple[float, float]:
        """
        Ingest triples into the pipeline.
        
        Returns:
            (encoding_time_ms, sheaf_build_time_ms)
        """
        # HDC encoding
        t0 = time.perf_counter()
        
        for t in triples:
            # Encode entities
            if t.head not in self._hdc_cache:
                self._hdc_cache[t.head] = self.ghrr.encode_type(t.head)
            if t.tail not in self._hdc_cache:
                self._hdc_cache[t.tail] = self.ghrr.encode_type(t.tail)
            
            # Encode relation
            rel_key = f"{t.head}--{t.relation}-->{t.tail}"
            if rel_key not in self._hdc_cache:
                self._hdc_cache[rel_key] = self.ghrr.encode_morphism(
                    t.head, t.tail, t.relation
                )
        
        encoding_time = (time.perf_counter() - t0) * 1000
        
        # Sheaf construction
        t1 = time.perf_counter()
        
        sheaf_triples = [(t.head, t.tail, t.relation) for t in triples]
        self.sheaf.add_triples(source_name, sheaf_triples)
        
        # Build Olog
        for t in triples:
            if t.head not in self.olog.graph.nodes():
                self.olog.add_type(t.head)
            if t.tail not in self.olog.graph.nodes():
                self.olog.add_type(t.tail)
            try:
                self.olog.add_aspect(t.head, t.tail, t.relation)
            except ValueError:
                pass  # Skip if nodes don't exist
        
        sheaf_time = (time.perf_counter() - t1) * 1000
        
        self._triples.extend(triples)
        self._initialized = True
        
        return encoding_time, sheaf_time
    
    def compute_cohomology(self) -> Tuple[CohomologyResult, float]:
        """
        Compute sheaf cohomology.
        
        Returns:
            (CohomologyResult, computation_time_ms)
        """
        t0 = time.perf_counter()
        result = self.sheaf.compute_cohomology()
        elapsed = (time.perf_counter() - t0) * 1000
        return result, elapsed
    
    def initialize_query_engine(self):
        """Initialize proof and query engines."""
        self.proof_engine = ProofEngine(
            self.olog,
            mode=self.config.proof_mode,
            max_depth=self.config.max_proof_depth,
        )
        
        self.query_engine = TopologicalQueryEngine(
            sheaf=self.sheaf,
            proof_engine=self.proof_engine,
            ghrr_encoder=self.ghrr,
            default_strategy=QueryStrategy.HYBRID,
        )
    
    def query(
        self,
        query_types: Set[str],
        constraints: Optional[QueryConstraint] = None,
    ) -> QueryResult:
        """Execute a topological query."""
        if not self.query_engine:
            self.initialize_query_engine()
        
        return self.query_engine.query(
            query_types,
            constraints=constraints,
            diffusion_time=self.config.diffusion_time,
        )
    
    def process_kg_dataset(
        self,
        dataset: KGDataset,
        max_triples: Optional[int] = None,
        run_queries: bool = True,
        num_sample_queries: int = 5,
    ) -> PipelineResult:
        """
        Process a full KG dataset through the pipeline.
        
        Args:
            dataset: KG dataset to process
            max_triples: Limit number of triples (for testing)
            run_queries: Whether to run sample queries
            num_sample_queries: Number of sample queries to run
            
        Returns:
            PipelineResult with all metrics
        """
        self.reset()
        
        triples = dataset.train[:max_triples] if max_triples else dataset.train
        
        # Ingest
        encoding_time, sheaf_time = self.ingest_triples(triples, dataset.name)
        
        # Cohomology
        cohom, cohom_time = self.compute_cohomology()
        
        # Sample queries
        sample_queries = []
        query_times = []
        proof_successes = 0
        total_proofs = 0
        
        if run_queries:
            self.initialize_query_engine()
            
            # Select random entity pairs for queries
            entities = list(dataset.entities)[:1000]  # Limit for speed
            np.random.seed(42)
            
            for _ in range(num_sample_queries):
                query_types = set(np.random.choice(entities, size=2, replace=False))
                
                result = self.query(query_types)
                query_times.append(result.execution_time_ms)
                
                # Count proof successes
                for proof in result.proofs:
                    total_proofs += 1
                    if proof.is_valid:
                        proof_successes += 1
                
                sample_queries.append({
                    "query": list(query_types),
                    "activated": result.activated_types[:10],
                    "paths_found": len(result.valid_paths),
                    "proofs_valid": sum(1 for p in result.proofs if p.is_valid),
                    "latency_ms": result.execution_time_ms,
                })
        
        return PipelineResult(
            dataset_name=dataset.name,
            num_triples=len(triples),
            num_entities=len(dataset.entities),
            num_relations=len(dataset.relations),
            h0_dimension=cohom.dim_H0,
            h1_dimension=cohom.dim_H1,
            consistency_score=cohom.consistency_score,
            consistency_status=cohom.status.value,
            encoding_time_ms=encoding_time,
            sheaf_build_time_ms=sheaf_time,
            cohomology_time_ms=cohom_time,
            sample_queries=sample_queries,
            avg_query_latency_ms=np.mean(query_times) if query_times else 0.0,
            proof_success_rate=proof_successes / total_proofs if total_proofs > 0 else 0.0,
        )
    
    def evaluate_conflict_detection(
        self,
        base_triples: List[KGTriple],
        conflict_dataset: ConflictDataset,
    ) -> ConflictDetectionResult:
        """
        Evaluate the pipeline's ability to detect injected conflicts.
        
        Args:
            base_triples: Clean baseline triples
            conflict_dataset: Dataset with conflicts
            
        Returns:
            ConflictDetectionResult with detection metrics
        """
        # Process baseline
        self.reset()
        self.ingest_triples(base_triples, "baseline")
        base_cohom, _ = self.compute_cohomology()
        
        # Add conflicts
        conflict_triples = [
            KGTriple(t.head, t.relation, t.tail)
            for t in conflict_dataset.conflicting_triples
        ]
        self.ingest_triples(conflict_triples, "conflicts")
        conflict_cohom, _ = self.compute_cohomology()
        
        # Detect conflicts via gaps
        gaps = self.sheaf._identify_obstructions()
        detected = len([g for g in gaps if g.gap_type == "contradiction"])
        
        return ConflictDetectionResult(
            base_h1=base_cohom.dim_H1,
            conflicted_h1=conflict_cohom.dim_H1,
            h1_increase=conflict_cohom.dim_H1 - base_cohom.dim_H1,
            base_consistency=base_cohom.consistency_score,
            conflicted_consistency=conflict_cohom.consistency_score,
            consistency_drop=base_cohom.consistency_score - conflict_cohom.consistency_score,
            detected_conflicts=detected,
            total_conflicts=len(conflict_dataset.conflict_pairs),
            detection_rate=detected / len(conflict_dataset.conflict_pairs) if conflict_dataset.conflict_pairs else 0.0,
        )
    
    def benchmark_strategies(
        self,
        query_types: Set[str],
        num_trials: int = 20,
    ) -> Dict[str, Dict]:
        """Benchmark different query strategies."""
        if not self.query_engine:
            self.initialize_query_engine()
        
        return self.query_engine.benchmark(
            query_types,
            num_trials=num_trials,
        )


def run_full_evaluation():
    """Run full evaluation on all benchmark datasets."""
    print("=" * 70)
    print("  HDC/SHEAF PIPELINE - FULL EVALUATION")
    print("  Week 4: End-to-End Benchmark")
    print("=" * 70)
    
    suite = BenchmarkSuite()
    pipeline = HDCSheafPipeline()
    
    results = {}
    
    # 1. Text2KG evaluation (smaller, faster)
    print("\n--- Text2KG Evaluation ---")
    t2k_triples = suite.load_text2kg_triples()
    
    if t2k_triples:
        # Create a simple KGDataset from Text2KG
        t2k_dataset = KGDataset(
            name="Text2KG",
            train=t2k_triples,
            valid=[],
            test=[],
        )
        
        result = pipeline.process_kg_dataset(
            t2k_dataset,
            max_triples=2000,
            num_sample_queries=10,
        )
        results["Text2KG"] = result
        
        print(f"  Triples: {result.num_triples:,}")
        print(f"  Entities: {result.num_entities:,}")
        print(f"  H⁰: {result.h0_dimension}, H¹: {result.h1_dimension}")
        print(f"  Consistency: {result.consistency_score:.3f}")
        print(f"  Encoding time: {result.encoding_time_ms:.1f}ms")
        print(f"  Avg query latency: {result.avg_query_latency_ms:.2f}ms")
        print(f"  Proof success rate: {result.proof_success_rate:.1%}")
    
    # 2. FB15K-237 evaluation (subset for speed)
    print("\n--- FB15K-237 Evaluation ---")
    fb15k = suite.load_fb15k237()
    
    if fb15k:
        result = pipeline.process_kg_dataset(
            fb15k,
            max_triples=5000,  # Subset for demo
            num_sample_queries=10,
        )
        results["FB15K-237"] = result
        
        print(f"  Triples: {result.num_triples:,}")
        print(f"  Entities: {result.num_entities:,}")
        print(f"  Relations: {result.num_relations:,}")
        print(f"  H⁰: {result.h0_dimension}, H¹: {result.h1_dimension}")
        print(f"  Consistency: {result.consistency_score:.3f}")
        print(f"  Encoding time: {result.encoding_time_ms:.1f}ms")
        print(f"  Avg query latency: {result.avg_query_latency_ms:.2f}ms")
    
    # 3. WN18RR evaluation (subset)
    print("\n--- WN18RR Evaluation ---")
    wn18rr = suite.load_wn18rr()
    
    if wn18rr:
        result = pipeline.process_kg_dataset(
            wn18rr,
            max_triples=5000,
            num_sample_queries=10,
        )
        results["WN18RR"] = result
        
        print(f"  Triples: {result.num_triples:,}")
        print(f"  Entities: {result.num_entities:,}")
        print(f"  Relations: {result.num_relations:,}")
        print(f"  H⁰: {result.h0_dimension}, H¹: {result.h1_dimension}")
        print(f"  Consistency: {result.consistency_score:.3f}")
        print(f"  Encoding time: {result.encoding_time_ms:.1f}ms")
    
    # 4. Conflict detection evaluation
    print("\n--- Conflict Detection Evaluation ---")
    
    if t2k_triples:
        base = t2k_triples[:500]
        conflicts = suite.generate_conflicts(base, ratio=0.2)
        
        conflict_result = pipeline.evaluate_conflict_detection(base, conflicts)
        
        print(f"  Base H¹: {conflict_result.base_h1}")
        print(f"  After conflicts H¹: {conflict_result.conflicted_h1}")
        print(f"  H¹ increase: +{conflict_result.h1_increase}")
        print(f"  Consistency drop: {conflict_result.consistency_drop:.3f}")
        print(f"  Conflicts injected: {conflict_result.total_conflicts}")
        print(f"  Conflicts detected: {conflict_result.detected_conflicts}")
        print(f"  Detection rate: {conflict_result.detection_rate:.1%}")
    
    # 5. Strategy benchmark
    print("\n--- Query Strategy Benchmark ---")
    
    pipeline.reset()
    if t2k_triples:
        pipeline.ingest_triples(t2k_triples[:1000], "benchmark")
        pipeline.initialize_query_engine()
        
        sample_entities = list(pipeline.sheaf.all_types)[:2]
        if len(sample_entities) >= 2:
            bench = pipeline.benchmark_strategies(set(sample_entities), num_trials=20)
            
            print(f"\n  {'Strategy':<20} {'Avg Time (ms)':<15} {'Std (ms)':<10}")
            print("  " + "-" * 45)
            for name, br in bench.items():
                print(f"  {name:<20} {br.avg_time_ms:<15.3f} {br.std_time_ms:<10.3f}")
    
    # Summary
    print("\n" + "=" * 70)
    print("  EVALUATION SUMMARY")
    print("=" * 70)
    
    print(f"\n  {'Dataset':<15} {'Triples':<10} {'H⁰':<5} {'H¹':<5} {'Consistency':<12} {'Query (ms)':<10}")
    print("  " + "-" * 57)
    
    for name, r in results.items():
        print(f"  {name:<15} {r.num_triples:<10,} {r.h0_dimension:<5} {r.h1_dimension:<5} {r.consistency_score:<12.3f} {r.avg_query_latency_ms:<10.2f}")
    
    print("\n" + "=" * 70)
    print("  Week 4 evaluation complete.")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_full_evaluation()

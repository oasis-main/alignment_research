"""
Benchmark Dataset Loaders for HDC/Sheaf Evaluation

Provides loaders for:
1. FB15K-237 - Freebase knowledge graph (link prediction)
2. WN18RR - WordNet reasoning (lexical relations)
3. Text2KGBench - Text-to-KG extraction (already prepared)
4. Synthetic conflicts - For H¹ cohomology training

Week 4 of HDC/Sheaf Integration (HANDOFF_06)
"""

import json
import os
import random
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Iterator
import numpy as np

DATA_DIR = Path(__file__).parent / "training_data"


@dataclass
class KGTriple:
    """A knowledge graph triple."""
    head: str
    relation: str
    tail: str
    
    def as_tuple(self) -> Tuple[str, str, str]:
        return (self.head, self.relation, self.tail)


@dataclass
class KGDataset:
    """A knowledge graph dataset with train/valid/test splits."""
    name: str
    train: List[KGTriple]
    valid: List[KGTriple]
    test: List[KGTriple]
    entities: Set[str] = field(default_factory=set)
    relations: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        for split in [self.train, self.valid, self.test]:
            for t in split:
                self.entities.add(t.head)
                self.entities.add(t.tail)
                self.relations.add(t.relation)
    
    def stats(self) -> Dict:
        return {
            "name": self.name,
            "num_entities": len(self.entities),
            "num_relations": len(self.relations),
            "train_triples": len(self.train),
            "valid_triples": len(self.valid),
            "test_triples": len(self.test),
        }


@dataclass
class ConflictDataset:
    """Dataset with intentional conflicts for H¹ training."""
    name: str
    base_triples: List[KGTriple]
    conflicting_triples: List[KGTriple]  # Contradict base
    conflict_pairs: List[Tuple[int, int]]  # (base_idx, conflict_idx)
    
    def get_conflict_severity(self, idx: int) -> float:
        """Return severity score for a conflict (0-1)."""
        # Simple heuristic: direct contradictions are severe
        return 0.8


class FB15K237Loader:
    """
    Loader for FB15K-237 dataset.
    
    FB15K-237 is a link prediction benchmark derived from Freebase.
    Inverse relations removed to prevent test leakage.
    
    ~15K entities, 237 relations, 310K triples
    """
    
    URL = "https://raw.githubusercontent.com/TimDettmers/ConvE/master/FB15k-237.tar.gz"
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir / "FB15K-237"
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self) -> bool:
        """Download and extract FB15K-237."""
        tar_path = self.data_dir / "FB15k-237.tar.gz"
        
        if (self.data_dir / "train.txt").exists():
            print("FB15K-237 already downloaded")
            return True
        
        print("Downloading FB15K-237...")
        try:
            urllib.request.urlretrieve(self.URL, tar_path)
            
            import tarfile
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(self.data_dir)
            
            # Move files up from nested directory
            nested = self.data_dir / "FB15k-237"
            if nested.exists():
                for f in nested.iterdir():
                    f.rename(self.data_dir / f.name)
                nested.rmdir()
            
            tar_path.unlink()
            print(f"Downloaded to {self.data_dir}")
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False
    
    def load(self) -> Optional[KGDataset]:
        """Load FB15K-237 dataset."""
        if not (self.data_dir / "train.txt").exists():
            if not self.download():
                return None
        
        def load_split(filename: str) -> List[KGTriple]:
            triples = []
            path = self.data_dir / filename
            if not path.exists():
                return triples
            with open(path) as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) == 3:
                        triples.append(KGTriple(parts[0], parts[1], parts[2]))
            return triples
        
        return KGDataset(
            name="FB15K-237",
            train=load_split("train.txt"),
            valid=load_split("valid.txt"),
            test=load_split("test.txt"),
        )


class WN18RRLoader:
    """
    Loader for WN18RR dataset.
    
    WN18RR is derived from WordNet with inverse relations removed.
    Tests lexical reasoning (hypernymy, meronymy, etc.)
    
    ~41K entities, 11 relations, 93K triples
    """
    
    URL = "https://raw.githubusercontent.com/TimDettmers/ConvE/master/WN18RR.tar.gz"
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir / "WN18RR"
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self) -> bool:
        """Download and extract WN18RR."""
        tar_path = self.data_dir / "WN18RR.tar.gz"
        
        if (self.data_dir / "train.txt").exists():
            print("WN18RR already downloaded")
            return True
        
        print("Downloading WN18RR...")
        try:
            urllib.request.urlretrieve(self.URL, tar_path)
            
            import tarfile
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(self.data_dir)
            
            nested = self.data_dir / "WN18RR"
            if nested.exists():
                for f in nested.iterdir():
                    f.rename(self.data_dir / f.name)
                nested.rmdir()
            
            tar_path.unlink()
            print(f"Downloaded to {self.data_dir}")
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False
    
    def load(self) -> Optional[KGDataset]:
        """Load WN18RR dataset."""
        if not (self.data_dir / "train.txt").exists():
            if not self.download():
                return None
        
        def load_split(filename: str) -> List[KGTriple]:
            triples = []
            path = self.data_dir / filename
            if not path.exists():
                return triples
            with open(path) as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) == 3:
                        triples.append(KGTriple(parts[0], parts[1], parts[2]))
            return triples
        
        return KGDataset(
            name="WN18RR",
            train=load_split("train.txt"),
            valid=load_split("valid.txt"),
            test=load_split("test.txt"),
        )


class Text2KGLoader:
    """Loader for prepared Text2KGBench data."""
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.jsonl_path = data_dir / "olog_training.jsonl"
    
    def load(self) -> List[Dict]:
        """Load prepared olog training samples."""
        if not self.jsonl_path.exists():
            print(f"Text2KGBench not found at {self.jsonl_path}")
            print("Run: python prepare_training_data.py --dataset text2kg")
            return []
        
        samples = []
        with open(self.jsonl_path) as f:
            for line in f:
                samples.append(json.loads(line))
        
        return samples
    
    def to_triples(self) -> List[KGTriple]:
        """Convert olog training data to KGTriples."""
        triples = []
        samples = self.load()
        
        for sample in samples:
            # Extract triples from assistant response
            messages = sample.get("messages", [])
            for msg in messages:
                if msg.get("role") == "assistant":
                    try:
                        olog = json.loads(msg["content"])
                        for aspect in olog.get("aspects", []):
                            triples.append(KGTriple(
                                head=aspect["source"],
                                relation=aspect["label"],
                                tail=aspect["target"],
                            ))
                    except json.JSONDecodeError:
                        continue
        
        return triples


class SyntheticConflictGenerator:
    """
    Generate synthetic conflicts for H¹ cohomology training.
    
    Creates controlled contradictions from a base dataset to train
    the sheaf's ability to detect inconsistencies.
    """
    
    CONFLICT_STRATEGIES = [
        "negate_relation",      # X is_a Y -> X is_not_a Y
        "swap_direction",       # X parent_of Y -> Y parent_of X (when asymmetric)
        "contradictory_value",  # X capital_of Y, X capital_of Z (Z != Y)
        "transitive_violation", # A > B, B > C, but C > A
    ]
    
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
    
    def generate_conflicts(
        self,
        base_triples: List[KGTriple],
        conflict_ratio: float = 0.1,
        strategies: Optional[List[str]] = None,
    ) -> ConflictDataset:
        """
        Generate conflicting triples from base dataset.
        
        Args:
            base_triples: Original consistent triples
            conflict_ratio: Fraction of triples to create conflicts for
            strategies: Which conflict strategies to use
            
        Returns:
            ConflictDataset with base and conflicting triples
        """
        strategies = strategies or self.CONFLICT_STRATEGIES
        
        # Group triples by relation
        by_relation: Dict[str, List[int]] = {}
        for i, t in enumerate(base_triples):
            if t.relation not in by_relation:
                by_relation[t.relation] = []
            by_relation[t.relation].append(i)
        
        # Select triples to create conflicts for
        num_conflicts = int(len(base_triples) * conflict_ratio)
        conflict_indices = self.rng.sample(range(len(base_triples)), min(num_conflicts, len(base_triples)))
        
        conflicting_triples = []
        conflict_pairs = []
        
        for base_idx in conflict_indices:
            base = base_triples[base_idx]
            strategy = self.rng.choice(strategies)
            
            conflict = self._apply_strategy(base, base_triples, by_relation, strategy)
            if conflict:
                conflict_idx = len(conflicting_triples)
                conflicting_triples.append(conflict)
                conflict_pairs.append((base_idx, conflict_idx))
        
        return ConflictDataset(
            name=f"synthetic_conflicts_{len(conflict_pairs)}",
            base_triples=base_triples,
            conflicting_triples=conflicting_triples,
            conflict_pairs=conflict_pairs,
        )
    
    def _apply_strategy(
        self,
        base: KGTriple,
        all_triples: List[KGTriple],
        by_relation: Dict[str, List[int]],
        strategy: str,
    ) -> Optional[KGTriple]:
        """Apply a conflict generation strategy."""
        
        if strategy == "negate_relation":
            # Add "not_" prefix to relation
            return KGTriple(
                head=base.head,
                relation=f"not_{base.relation}",
                tail=base.tail,
            )
        
        elif strategy == "swap_direction":
            # Reverse head and tail
            return KGTriple(
                head=base.tail,
                relation=base.relation,
                tail=base.head,
            )
        
        elif strategy == "contradictory_value":
            # Same head+relation, different tail
            same_rel = by_relation.get(base.relation, [])
            candidates = [
                all_triples[i].tail 
                for i in same_rel 
                if all_triples[i].head == base.head and all_triples[i].tail != base.tail
            ]
            if not candidates:
                # Pick random entity as alternative
                all_tails = list(set(t.tail for t in all_triples if t.tail != base.tail))
                if all_tails:
                    candidates = [self.rng.choice(all_tails)]
            
            if candidates:
                return KGTriple(
                    head=base.head,
                    relation=base.relation,
                    tail=self.rng.choice(candidates),
                )
        
        elif strategy == "transitive_violation":
            # Create cycle that violates transitivity
            # Find B such that base.tail -> B exists
            extensions = [
                t for t in all_triples 
                if t.head == base.tail and t.relation == base.relation
            ]
            if extensions:
                ext = self.rng.choice(extensions)
                # Create ext.tail -> base.head (closes cycle backwards)
                return KGTriple(
                    head=ext.tail,
                    relation=base.relation,
                    tail=base.head,
                )
        
        return None


class BenchmarkSuite:
    """
    Unified interface for all benchmark datasets.
    
    Usage:
        suite = BenchmarkSuite()
        suite.download_all()
        
        fb15k = suite.load_fb15k237()
        wn18rr = suite.load_wn18rr()
        text2kg = suite.load_text2kg()
        conflicts = suite.generate_conflicts(fb15k.train, ratio=0.1)
    """
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.fb15k_loader = FB15K237Loader(data_dir)
        self.wn18rr_loader = WN18RRLoader(data_dir)
        self.text2kg_loader = Text2KGLoader(data_dir)
        self.conflict_gen = SyntheticConflictGenerator()
    
    def download_all(self) -> Dict[str, bool]:
        """Download all datasets."""
        results = {}
        results["FB15K-237"] = self.fb15k_loader.download()
        results["WN18RR"] = self.wn18rr_loader.download()
        results["Text2KG"] = self.text2kg_loader.jsonl_path.exists()
        return results
    
    def load_fb15k237(self) -> Optional[KGDataset]:
        return self.fb15k_loader.load()
    
    def load_wn18rr(self) -> Optional[KGDataset]:
        return self.wn18rr_loader.load()
    
    def load_text2kg(self) -> List[Dict]:
        return self.text2kg_loader.load()
    
    def load_text2kg_triples(self) -> List[KGTriple]:
        return self.text2kg_loader.to_triples()
    
    def generate_conflicts(
        self,
        base_triples: List[KGTriple],
        ratio: float = 0.1,
    ) -> ConflictDataset:
        return self.conflict_gen.generate_conflicts(base_triples, ratio)
    
    def all_stats(self) -> Dict:
        """Get stats for all available datasets."""
        stats = {}
        
        fb = self.load_fb15k237()
        if fb:
            stats["FB15K-237"] = fb.stats()
        
        wn = self.load_wn18rr()
        if wn:
            stats["WN18RR"] = wn.stats()
        
        t2k = self.load_text2kg()
        stats["Text2KG"] = {"samples": len(t2k)}
        
        t2k_triples = self.load_text2kg_triples()
        stats["Text2KG"]["triples"] = len(t2k_triples)
        
        return stats


def demo():
    """Demonstrate benchmark dataset loading."""
    print("=" * 70)
    print("  BENCHMARK DATASET SUITE")
    print("  Week 4: HDC/Sheaf Evaluation Data")
    print("=" * 70)
    
    suite = BenchmarkSuite()
    
    # Download status
    print("\n--- Download Status ---")
    status = suite.download_all()
    for name, available in status.items():
        print(f"  {name}: {'✓' if available else '✗'}")
    
    # Load and show stats
    print("\n--- Dataset Statistics ---")
    stats = suite.all_stats()
    
    for name, s in stats.items():
        print(f"\n  {name}:")
        for k, v in s.items():
            print(f"    {k}: {v:,}" if isinstance(v, int) else f"    {k}: {v}")
    
    # Demo conflict generation
    print("\n--- Synthetic Conflict Generation ---")
    
    # Use Text2KG triples for demo
    t2k_triples = suite.load_text2kg_triples()
    if t2k_triples:
        conflicts = suite.generate_conflicts(t2k_triples[:1000], ratio=0.15)
        
        print(f"  Base triples: {len(conflicts.base_triples)}")
        print(f"  Conflicting triples: {len(conflicts.conflicting_triples)}")
        print(f"  Conflict pairs: {len(conflicts.conflict_pairs)}")
        
        if conflicts.conflict_pairs:
            print("\n  Sample conflicts:")
            for i, (base_idx, conf_idx) in enumerate(conflicts.conflict_pairs[:3]):
                base = conflicts.base_triples[base_idx]
                conf = conflicts.conflicting_triples[conf_idx]
                print(f"    [{i+1}] Base: ({base.head}, {base.relation}, {base.tail})")
                print(f"        Conf: ({conf.head}, {conf.relation}, {conf.tail})")
    
    # Integration with sheaf
    print("\n--- Integration with OntologySheaf ---")
    
    try:
        from ontology_sheaf import OntologySheaf
        
        sheaf = OntologySheaf()
        
        # Add base triples
        if t2k_triples:
            sample_triples = t2k_triples[:50]
            sheaf.add_triples("text2kg_sample", [
                (t.head, t.tail, t.relation) for t in sample_triples
            ])
            
            # Compute baseline cohomology
            cohom_base = sheaf.compute_cohomology()
            print(f"  Baseline H¹: {cohom_base.dim_H1}")
            print(f"  Baseline consistency: {cohom_base.consistency_score:.3f}")
            
            # Add conflicts
            if conflicts.conflicting_triples:
                conflict_sample = conflicts.conflicting_triples[:10]
                sheaf.add_triples("conflicts", [
                    (t.head, t.tail, t.relation) for t in conflict_sample
                ])
                
                cohom_with_conflicts = sheaf.compute_cohomology()
                print(f"  With conflicts H¹: {cohom_with_conflicts.dim_H1}")
                print(f"  With conflicts consistency: {cohom_with_conflicts.consistency_score:.3f}")
                
                h1_increase = cohom_with_conflicts.dim_H1 - cohom_base.dim_H1
                print(f"  H¹ increase from conflicts: +{h1_increase}")
    
    except ImportError as e:
        print(f"  (Sheaf integration skipped: {e})")
    
    print("\n" + "=" * 70)
    print("  Benchmark suite ready for Week 4 evaluation.")
    print("=" * 70)


if __name__ == "__main__":
    demo()

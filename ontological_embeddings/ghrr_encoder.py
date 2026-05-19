"""
Generalized Holographic Reduced Representations (GHRR) Encoder

Non-commutative binding for directed ontological relations.
Integrates with Olog core for hyperdimensional ontology representation.

Reference: Gosmann & Eliasmith (2019), "Vector-Derived Transformation Binding"
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import hashlib


@dataclass
class HypervectorConfig:
    """Configuration for hypervector operations."""
    dim: int = 4096
    seed: int = 42
    normalize: bool = True


class GHRREncoder:
    """
    Generalized Holographic Reduced Representations encoder.
    
    Uses non-commutative matrix multiplication for binding,
    preserving directed relationships in ontologies.
    """
    
    def __init__(self, config: Optional[HypervectorConfig] = None):
        self.config = config or HypervectorConfig()
        self.dim = self.config.dim
        self.sqrt_dim = int(np.sqrt(self.dim))
        
        # Verify dimension is a perfect square for matrix ops
        if self.sqrt_dim ** 2 != self.dim:
            raise ValueError(f"Dimension {self.dim} must be a perfect square")
        
        # Cache for type encodings
        self._type_cache: Dict[str, np.ndarray] = {}
        self._morphism_cache: Dict[Tuple[str, str, str], np.ndarray] = {}
        
    def _hash_to_seed(self, name: str) -> int:
        """Deterministic hash to seed for reproducibility."""
        h = hashlib.sha256(name.encode()).hexdigest()
        return int(h[:8], 16)
    
    def encode_type(self, type_name: str) -> np.ndarray:
        """
        Encode an Olog type as a hypervector.
        
        Uses deterministic seeding for reproducibility.
        Hypervectors are approximately orthogonal in high dimensions.
        """
        if type_name in self._type_cache:
            return self._type_cache[type_name]
        
        seed = self._hash_to_seed(type_name)
        rng = np.random.default_rng(seed)
        hv = rng.standard_normal(self.dim)
        
        if self.config.normalize:
            hv = hv / np.linalg.norm(hv)
        
        self._type_cache[type_name] = hv
        return hv
    
    def encode_relation(self, relation_label: str) -> np.ndarray:
        """Encode a relation/morphism label as a hypervector."""
        return self.encode_type(f"__rel__{relation_label}")
    
    def bind(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:
        """
        Non-commutative binding: bind(A, B) ≠ bind(B, A).
        
        Uses matrix multiplication after reshaping vectors to matrices.
        This preserves directionality of ontological relations.
        """
        A = source.reshape(self.sqrt_dim, self.sqrt_dim)
        B = target.reshape(self.sqrt_dim, self.sqrt_dim)
        result = (A @ B).flatten()
        
        if self.config.normalize:
            result = result / np.linalg.norm(result)
        
        return result
    
    def unbind(self, composite: np.ndarray, key: np.ndarray) -> np.ndarray:
        """
        Retrieve filler given composite and key.
        
        Uses pseudoinverse for approximate retrieval.
        """
        K = key.reshape(self.sqrt_dim, self.sqrt_dim)
        C = composite.reshape(self.sqrt_dim, self.sqrt_dim)
        result = (np.linalg.pinv(K) @ C).flatten()
        
        if self.config.normalize:
            result = result / np.linalg.norm(result)
        
        return result
    
    def superpose(self, *vectors: np.ndarray) -> np.ndarray:
        """
        Superposition (bundling) of multiple hypervectors.
        
        Used to represent sets or combine multiple concepts.
        """
        result = np.sum(vectors, axis=0)
        
        if self.config.normalize:
            result = result / np.linalg.norm(result)
        
        return result
    
    def permute(self, hv: np.ndarray, steps: int = 1) -> np.ndarray:
        """
        Permute hypervector to encode sequence/hierarchy.
        
        Cyclic shift by 'steps' positions.
        """
        return np.roll(hv, steps)
    
    def similarity(self, hv1: np.ndarray, hv2: np.ndarray) -> float:
        """Cosine similarity between hypervectors."""
        return float(np.dot(hv1, hv2) / (np.linalg.norm(hv1) * np.linalg.norm(hv2)))
    
    def encode_morphism(self, source: str, target: str, label: str) -> np.ndarray:
        """
        Encode an Olog morphism as a hypervector.
        
        Morphism f: A → B with label "r" is encoded as:
        bind(bind(encode(A), encode(r)), encode(B))
        
        This captures: (source, relation) → target
        """
        cache_key = (source, target, label)
        if cache_key in self._morphism_cache:
            return self._morphism_cache[cache_key]
        
        source_hv = self.encode_type(source)
        target_hv = self.encode_type(target)
        label_hv = self.encode_relation(label)
        
        # Encode as: bind(bind(source, label), target)
        # This is non-commutative and captures directionality
        role_binding = self.bind(source_hv, label_hv)
        morphism_hv = self.bind(role_binding, target_hv)
        
        self._morphism_cache[cache_key] = morphism_hv
        return morphism_hv
    
    def encode_path(self, path: List[Tuple[str, str, str]]) -> np.ndarray:
        """
        Encode a path through the Olog as a hypervector.
        
        Path is a list of (source, target, label) triples.
        Uses permutation to preserve order.
        """
        if not path:
            raise ValueError("Path cannot be empty")
        
        # Encode each morphism and permute by position
        morphism_hvs = []
        for i, (source, target, label) in enumerate(path):
            m_hv = self.encode_morphism(source, target, label)
            m_hv = self.permute(m_hv, steps=i)
            morphism_hvs.append(m_hv)
        
        # Superpose all permuted morphisms
        return self.superpose(*morphism_hvs)
    
    def query_similar(self, query_hv: np.ndarray, 
                      candidates: Dict[str, np.ndarray],
                      top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find most similar hypervectors to query.
        
        Returns list of (candidate_name, similarity) tuples.
        """
        similarities = [
            (name, self.similarity(query_hv, hv))
            for name, hv in candidates.items()
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class OlogHDCEncoder:
    """
    Encoder that converts an entire Olog to HDC representation.
    
    Integrates with olog_core.py structures.
    """
    
    def __init__(self, ghrr: Optional[GHRREncoder] = None):
        self.ghrr = ghrr or GHRREncoder()
        self.type_vectors: Dict[str, np.ndarray] = {}
        self.morphism_vectors: Dict[str, np.ndarray] = {}
        
    def encode_olog(self, types: Set[str], 
                    morphisms: List[Tuple[str, str, str]]) -> Dict[str, np.ndarray]:
        """
        Encode an entire Olog structure.
        
        Args:
            types: Set of type names
            morphisms: List of (source, target, label) triples
            
        Returns:
            Dictionary mapping names to hypervectors
        """
        # Encode all types
        for t in types:
            self.type_vectors[t] = self.ghrr.encode_type(t)
        
        # Encode all morphisms
        for source, target, label in morphisms:
            key = f"{source}--{label}-->{target}"
            self.morphism_vectors[key] = self.ghrr.encode_morphism(
                source, target, label
            )
        
        return {**self.type_vectors, **self.morphism_vectors}
    
    def verify_non_commutativity(self) -> List[Tuple[str, str, float]]:
        """
        Verify that binding is non-commutative for all type pairs.
        
        Returns list of (type_a, type_b, asymmetry_score) where
        asymmetry_score = 1 - similarity(bind(A,B), bind(B,A))
        """
        results = []
        types = list(self.type_vectors.keys())
        
        for i, t1 in enumerate(types):
            for t2 in types[i+1:]:
                hv1 = self.type_vectors[t1]
                hv2 = self.type_vectors[t2]
                
                bind_ab = self.ghrr.bind(hv1, hv2)
                bind_ba = self.ghrr.bind(hv2, hv1)
                
                sim = self.ghrr.similarity(bind_ab, bind_ba)
                asymmetry = 1.0 - sim
                results.append((t1, t2, asymmetry))
        
        return results


def demo():
    """Demonstrate GHRR encoding with a simple ontology."""
    print("=" * 60)
    print("GHRR Encoder Demo: E-Commerce Ontology")
    print("=" * 60)
    
    # Initialize encoder
    ghrr = GHRREncoder(HypervectorConfig(dim=4096))
    olog_encoder = OlogHDCEncoder(ghrr)
    
    # Define simple e-commerce ontology
    types = {"Customer", "Cart", "Order", "Payment", "Delivery"}
    morphisms = [
        ("Customer", "Cart", "creates"),
        ("Cart", "Order", "becomes"),
        ("Order", "Payment", "requires"),
        ("Payment", "Delivery", "triggers"),
    ]
    
    # Encode ontology
    vectors = olog_encoder.encode_olog(types, morphisms)
    print(f"\nEncoded {len(types)} types and {len(morphisms)} morphisms")
    print(f"Hypervector dimension: {ghrr.dim}")
    
    # Verify non-commutativity
    print("\n--- Non-Commutativity Verification ---")
    asymmetries = olog_encoder.verify_non_commutativity()
    for t1, t2, asym in asymmetries[:5]:
        print(f"  {t1} ↔ {t2}: asymmetry = {asym:.4f}")
    
    avg_asym = np.mean([a for _, _, a in asymmetries])
    print(f"\n  Average asymmetry: {avg_asym:.4f}")
    print(f"  (1.0 = perfectly non-commutative, 0.0 = commutative)")
    
    # Demonstrate similarity-based retrieval
    print("\n--- Similarity-Based Retrieval ---")
    
    # Query: "What does Customer create?"
    customer_hv = ghrr.encode_type("Customer")
    creates_hv = ghrr.encode_relation("creates")
    query_hv = ghrr.bind(customer_hv, creates_hv)
    
    # Find similar morphisms
    results = ghrr.query_similar(query_hv, olog_encoder.morphism_vectors)
    print(f"\nQuery: bind(Customer, creates) → ?")
    for name, sim in results:
        print(f"  {name}: similarity = {sim:.4f}")
    
    # Verify directionality
    print("\n--- Directionality Test ---")
    
    # bind(Customer, Order) should be different from bind(Order, Customer)
    cust_hv = ghrr.encode_type("Customer")
    order_hv = ghrr.encode_type("Order")
    
    cust_order = ghrr.bind(cust_hv, order_hv)
    order_cust = ghrr.bind(order_hv, cust_hv)
    
    sim = ghrr.similarity(cust_order, order_cust)
    print(f"  similarity(bind(Customer,Order), bind(Order,Customer)) = {sim:.4f}")
    print(f"  → Bindings are {'DIFFERENT' if sim < 0.5 else 'SIMILAR'} (want: DIFFERENT)")
    
    # Path encoding
    print("\n--- Path Encoding ---")
    path = [
        ("Customer", "Cart", "creates"),
        ("Cart", "Order", "becomes"),
        ("Order", "Payment", "requires"),
    ]
    path_hv = ghrr.encode_path(path)
    print(f"  Encoded path: Customer→Cart→Order→Payment")
    print(f"  Path vector norm: {np.linalg.norm(path_hv):.4f}")
    
    print("\n" + "=" * 60)
    print("Demo complete. GHRR encoder ready for integration.")
    print("=" * 60)


if __name__ == "__main__":
    demo()

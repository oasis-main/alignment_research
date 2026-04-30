"""
Proof Object Generation for Auditable AI

Implements constructive logic proofs over Ologs. Every AI output must be
accompanied by a proof object (commutative diagram) demonstrating its
validity. Failure to construct a proof indicates potential hallucination.

Key Concepts:
- Proof Object: A witnessed derivation showing how a conclusion follows
- Commutative Diagram: Visual/structural representation of proof
- Proof Search: Finding valid derivations in the Olog structure
- Hallucination Detection: Claims without valid proofs are flagged

Mathematical Foundation:
- Curry-Howard Correspondence: Proofs as programs, propositions as types
- Category Theory: Proofs as morphisms, composition as reasoning
- Constructive Logic: Truth requires construction, not just non-contradiction

Usage:
    from proof_objects import ProofEngine, ProofObject
    
    engine = ProofEngine(olog)
    proof = engine.prove("Customer places Order generates Invoice")
    if proof.is_valid:
        print(proof.render_diagram())
    else:
        print(f"HALLUCINATION: {proof.failure_reason}")
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any, Union
from enum import Enum
import json

from olog_core import OlogGraph, OlogNode, OlogMorphism, CommutativeFact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProofStatus(Enum):
    """Status of a proof attempt."""
    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"  # Some steps proven, others not
    TIMEOUT = "timeout"  # Search exceeded limits


class ProofMode(Enum):
    """Mode for proof verification."""
    STRICT = "strict"           # Claimed relation must be the EXACT edge label
    COMPOSITIONAL = "compositional"  # Relation can be decomposed into valid composition
    REACHABILITY = "reachability"    # Any path suffices (least strict, original behavior)


class ProofStep(Enum):
    """Types of proof steps."""
    IDENTITY = "identity"       # A = A
    COMPOSITION = "composition" # f: A→B, g: B→C ⊢ g∘f: A→C
    COMMUTATIVITY = "commutativity"  # Two paths are equal
    WITNESS = "witness"         # Existential introduction
    APPLICATION = "application" # Function application (modus ponens analog)


@dataclass
class ProofNode:
    """A single step in a proof."""
    step_type: ProofStep
    premise: str  # What we're proving from
    conclusion: str  # What we're proving
    justification: str  # How we got here
    morphism_path: List[str] = field(default_factory=list)  # Edge labels used
    children: List['ProofNode'] = field(default_factory=list)  # Sub-proofs
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_type.value,
            "from": self.premise,
            "to": self.conclusion,
            "by": self.justification,
            "path": self.morphism_path,
            "children": [c.to_dict() for c in self.children]
        }


@dataclass
class ProofObject:
    """
    A complete proof object for an AI claim.
    
    Contains the derivation tree and metadata about proof validity.
    """
    claim: str
    status: ProofStatus
    root: Optional[ProofNode] = None
    failure_reason: Optional[str] = None
    search_depth: int = 0
    alternatives_explored: int = 0
    
    @property
    def is_valid(self) -> bool:
        return self.status == ProofStatus.VALID
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "status": self.status.value,
            "proof": self.root.to_dict() if self.root else None,
            "failure_reason": self.failure_reason,
            "search_depth": self.search_depth,
            "alternatives": self.alternatives_explored
        }
    
    def render_diagram(self, indent: int = 0) -> str:
        """Render proof as ASCII commutative diagram."""
        lines = []
        prefix = "  " * indent
        
        lines.append(f"{prefix}┌─ PROOF: {self.claim}")
        lines.append(f"{prefix}│  Status: {self.status.value.upper()}")
        
        if self.root:
            lines.extend(self._render_node(self.root, indent + 1))
        elif self.failure_reason:
            lines.append(f"{prefix}│  ✗ {self.failure_reason}")
        
        lines.append(f"{prefix}└─ QED" if self.is_valid else f"{prefix}└─ ∎ (incomplete)")
        
        return "\n".join(lines)
    
    def _render_node(self, node: ProofNode, indent: int) -> List[str]:
        """Recursively render a proof node."""
        lines = []
        prefix = "  " * indent
        
        # Step visualization
        arrow = "→" if node.morphism_path else "="
        path_str = " ∘ ".join(node.morphism_path) if node.morphism_path else "id"
        
        lines.append(f"{prefix}├─ [{node.step_type.value}] {node.premise} {arrow} {node.conclusion}")
        lines.append(f"{prefix}│    by: {node.justification}")
        if node.morphism_path:
            lines.append(f"{prefix}│    path: {path_str}")
        
        for child in node.children:
            lines.extend(self._render_node(child, indent + 1))
        
        return lines


@dataclass 
class Claim:
    """A structured claim to be proven."""
    subject: str
    relation: str
    object: str
    
    def __str__(self):
        return f"{self.subject} {self.relation} {self.object}"
    
    @classmethod
    def parse(cls, text: str) -> Optional['Claim']:
        """Parse a claim from text (simple SVO pattern)."""
        parts = text.strip().split()
        if len(parts) >= 3:
            return cls(
                subject=parts[0],
                relation=" ".join(parts[1:-1]),
                object=parts[-1]
            )
        return None


class ProofEngine:
    """
    Engine for constructing proof objects over Ologs.
    
    Implements proof search to find valid derivations for claims,
    or identify hallucinations when no proof exists.
    """
    
    def __init__(
        self,
        olog: OlogGraph,
        max_depth: int = 10,
        max_alternatives: int = 100,
        mode: ProofMode = ProofMode.STRICT,
    ):
        self.olog = olog
        self.max_depth = max_depth
        self.max_alternatives = max_alternatives
        self.mode = mode
        
        # Index morphisms for fast lookup
        self._morphisms_from: Dict[str, List[OlogMorphism]] = {}
        self._morphisms_to: Dict[str, List[OlogMorphism]] = {}
        self._morphisms_by_label: Dict[str, List[OlogMorphism]] = {}
        self._build_indices()
    
    def _build_indices(self):
        """Build indices for efficient proof search."""
        for u, v, key, data in self.olog.graph.edges(keys=True, data=True):
            morph_data = data.get('data')
            if not morph_data:
                morph_data = OlogMorphism(source=u, target=v, label=key)
            
            # Index by source
            if u not in self._morphisms_from:
                self._morphisms_from[u] = []
            self._morphisms_from[u].append(morph_data)
            
            # Index by target
            if v not in self._morphisms_to:
                self._morphisms_to[v] = []
            self._morphisms_to[v].append(morph_data)
            
            # Index by label
            if key not in self._morphisms_by_label:
                self._morphisms_by_label[key] = []
            self._morphisms_by_label[key].append(morph_data)
    
    def prove(self, claim: Union[str, Claim]) -> ProofObject:
        """
        Attempt to prove a claim.
        
        Args:
            claim: Either a string or structured Claim
            
        Returns:
            ProofObject with proof tree or failure reason
        """
        if isinstance(claim, str):
            parsed = Claim.parse(claim)
            if not parsed:
                return ProofObject(
                    claim=claim,
                    status=ProofStatus.INVALID,
                    failure_reason="Could not parse claim"
                )
            claim_obj = parsed
            claim_str = claim
        else:
            claim_obj = claim
            claim_str = str(claim)
        
        # Check types exist
        if claim_obj.subject not in self.olog.graph:
            return ProofObject(
                claim=claim_str,
                status=ProofStatus.INVALID,
                failure_reason=f"Unknown type: {claim_obj.subject}"
            )
        if claim_obj.object not in self.olog.graph:
            return ProofObject(
                claim=claim_str,
                status=ProofStatus.INVALID,
                failure_reason=f"Unknown type: {claim_obj.object}"
            )
        
        # Identity proof
        if claim_obj.subject == claim_obj.object:
            return ProofObject(
                claim=claim_str,
                status=ProofStatus.VALID,
                root=ProofNode(
                    step_type=ProofStep.IDENTITY,
                    premise=claim_obj.subject,
                    conclusion=claim_obj.object,
                    justification="reflexivity"
                ),
                search_depth=0
            )
        
        # STRICT MODE: Check for exact relation match
        if self.mode == ProofMode.STRICT:
            return self._prove_strict(claim_obj, claim_str)
        
        # COMPOSITIONAL MODE: Allow valid decompositions
        elif self.mode == ProofMode.COMPOSITIONAL:
            return self._prove_compositional(claim_obj, claim_str)
        
        # REACHABILITY MODE: Any path suffices (original behavior)
        else:
            return self._prove_reachability(claim_obj, claim_str)
    
    def _prove_strict(self, claim_obj: Claim, claim_str: str) -> ProofObject:
        """
        STRICT MODE: The claimed relation must be an exact edge label.
        
        "Customer places Order" is valid iff edge Customer --places--> Order exists.
        "Payment places Customer" is INVALID even if a path exists.
        """
        relation = claim_obj.relation.strip()
        
        # Check for direct edge with exact label
        for morph in self._morphisms_from.get(claim_obj.subject, []):
            if morph.target == claim_obj.object and morph.label == relation:
                return ProofObject(
                    claim=claim_str,
                    status=ProofStatus.VALID,
                    root=ProofNode(
                        step_type=ProofStep.APPLICATION,
                        premise=claim_obj.subject,
                        conclusion=claim_obj.object,
                        justification=f"direct morphism '{relation}'",
                        morphism_path=[relation]
                    ),
                    search_depth=1,
                    alternatives_explored=1
                )
        
        # No direct edge with that label
        return ProofObject(
            claim=claim_str,
            status=ProofStatus.INVALID,
            failure_reason=f"No edge '{relation}' from {claim_obj.subject} to {claim_obj.object}",
            search_depth=1,
            alternatives_explored=len(self._morphisms_from.get(claim_obj.subject, []))
        )
    
    def _prove_compositional(self, claim_obj: Claim, claim_str: str) -> ProofObject:
        """
        COMPOSITIONAL MODE: Relation can be decomposed.
        
        "Customer places_and_generates Invoice" could be valid if:
        - Customer --places--> Order --generates--> Invoice exists
        - AND "places_and_generates" decomposes to ["places", "generates"]
        
        For now, we require the relation to appear somewhere in the path.
        """
        relation = claim_obj.relation.strip()
        
        # First check strict mode (direct edge)
        for morph in self._morphisms_from.get(claim_obj.subject, []):
            if morph.target == claim_obj.object and morph.label == relation:
                return ProofObject(
                    claim=claim_str,
                    status=ProofStatus.VALID,
                    root=ProofNode(
                        step_type=ProofStep.APPLICATION,
                        premise=claim_obj.subject,
                        conclusion=claim_obj.object,
                        justification=f"direct morphism '{relation}'",
                        morphism_path=[relation]
                    ),
                    search_depth=1
                )
        
        # Try to find path where relation appears as component
        path, depth, explored = self._find_path_with_relation(
            claim_obj.subject,
            claim_obj.object,
            required_relation=relation
        )
        
        if path:
            root = self._build_composition_proof(claim_obj.subject, claim_obj.object, path)
            return ProofObject(
                claim=claim_str,
                status=ProofStatus.VALID,
                root=root,
                search_depth=depth,
                alternatives_explored=explored
            )
        
        return ProofObject(
            claim=claim_str,
            status=ProofStatus.INVALID,
            failure_reason=f"No path containing '{relation}' from {claim_obj.subject} to {claim_obj.object}",
            search_depth=depth,
            alternatives_explored=explored
        )
    
    def _prove_reachability(self, claim_obj: Claim, claim_str: str) -> ProofObject:
        """REACHABILITY MODE: Any path suffices (original behavior)."""
        path, depth, explored = self._find_path(
            claim_obj.subject, 
            claim_obj.object,
            relation_hint=claim_obj.relation
        )
        
        if path:
            root = self._build_composition_proof(claim_obj.subject, claim_obj.object, path)
            return ProofObject(
                claim=claim_str,
                status=ProofStatus.VALID,
                root=root,
                search_depth=depth,
                alternatives_explored=explored
            )
        else:
            return ProofObject(
                claim=claim_str,
                status=ProofStatus.INVALID,
                failure_reason=f"No path from {claim_obj.subject} to {claim_obj.object}",
                search_depth=depth,
                alternatives_explored=explored
            )
    
    def _find_path(
        self, 
        source: str, 
        target: str,
        relation_hint: Optional[str] = None
    ) -> Tuple[Optional[List[OlogMorphism]], int, int]:
        """
        Find a path from source to target in the Olog.
        
        Returns: (path, depth_reached, alternatives_explored)
        """
        # BFS for shortest path
        visited = {source}
        queue = [(source, [], 0)]  # (node, path, depth)
        explored = 0
        
        while queue and explored < self.max_alternatives:
            current, path, depth = queue.pop(0)
            explored += 1
            
            if depth > self.max_depth:
                continue
            
            # Check outgoing edges
            for morph in self._morphisms_from.get(current, []):
                if morph.target == target:
                    return (path + [morph], depth + 1, explored)
                
                if morph.target not in visited:
                    visited.add(morph.target)
                    queue.append((morph.target, path + [morph], depth + 1))
        
        return (None, self.max_depth, explored)
    
    def _find_path_with_relation(
        self,
        source: str,
        target: str,
        required_relation: str
    ) -> Tuple[Optional[List[OlogMorphism]], int, int]:
        """
        Find a path that includes the required relation label.
        
        Used for COMPOSITIONAL mode - the claimed relation must appear
        somewhere in the composition.
        """
        visited = set()
        queue = [(source, [], 0, False)]  # (node, path, depth, found_relation)
        explored = 0
        
        while queue and explored < self.max_alternatives:
            current, path, depth, found_rel = queue.pop(0)
            explored += 1
            
            if depth > self.max_depth:
                continue
            
            state_key = (current, found_rel)
            if state_key in visited:
                continue
            visited.add(state_key)
            
            for morph in self._morphisms_from.get(current, []):
                new_found = found_rel or (morph.label == required_relation)
                
                if morph.target == target and new_found:
                    return (path + [morph], depth + 1, explored)
                
                queue.append((morph.target, path + [morph], depth + 1, new_found))
        
        return (None, self.max_depth, explored)
    
    def _build_composition_proof(
        self, 
        source: str, 
        target: str, 
        path: List[OlogMorphism]
    ) -> ProofNode:
        """Build a proof node from a path using composition."""
        if len(path) == 1:
            morph = path[0]
            return ProofNode(
                step_type=ProofStep.APPLICATION,
                premise=source,
                conclusion=target,
                justification=f"direct morphism '{morph.label}'",
                morphism_path=[morph.label]
            )
        
        # Build composition tree
        labels = [m.label for m in path]
        
        # Create nested composition
        children = []
        current = source
        for morph in path:
            children.append(ProofNode(
                step_type=ProofStep.APPLICATION,
                premise=current,
                conclusion=morph.target,
                justification=f"apply '{morph.label}'",
                morphism_path=[morph.label]
            ))
            current = morph.target
        
        return ProofNode(
            step_type=ProofStep.COMPOSITION,
            premise=source,
            conclusion=target,
            justification=f"composition of {len(path)} morphisms",
            morphism_path=labels,
            children=children
        )
    
    def prove_chain(self, claims: List[str]) -> List[ProofObject]:
        """Prove a sequence of claims."""
        return [self.prove(c) for c in claims]
    
    def verify_commutative_fact(self, fact: CommutativeFact) -> ProofObject:
        """Verify that a commutative fact holds in the Olog."""
        claim = f"Path equivalence: {fact.path_a_labels} = {fact.path_b_labels}"
        
        # Walk both paths
        end_a = self._walk_path(fact.source_node, fact.path_a_labels)
        end_b = self._walk_path(fact.source_node, fact.path_b_labels)
        
        if end_a is None:
            return ProofObject(
                claim=claim,
                status=ProofStatus.INVALID,
                failure_reason=f"Path A does not exist: {fact.path_a_labels}"
            )
        
        if end_b is None:
            return ProofObject(
                claim=claim,
                status=ProofStatus.INVALID,
                failure_reason=f"Path B does not exist: {fact.path_b_labels}"
            )
        
        if end_a != end_b:
            return ProofObject(
                claim=claim,
                status=ProofStatus.INVALID,
                failure_reason=f"Paths end at different types: {end_a} ≠ {end_b}"
            )
        
        # Build commutativity proof
        root = ProofNode(
            step_type=ProofStep.COMMUTATIVITY,
            premise=fact.source_node,
            conclusion=fact.target_node,
            justification="paths terminate at same type",
            children=[
                ProofNode(
                    step_type=ProofStep.COMPOSITION,
                    premise=fact.source_node,
                    conclusion=end_a,
                    justification="path A",
                    morphism_path=fact.path_a_labels
                ),
                ProofNode(
                    step_type=ProofStep.COMPOSITION,
                    premise=fact.source_node,
                    conclusion=end_b,
                    justification="path B",
                    morphism_path=fact.path_b_labels
                )
            ]
        )
        
        return ProofObject(
            claim=claim,
            status=ProofStatus.VALID,
            root=root
        )
    
    def _walk_path(self, start: str, labels: List[str]) -> Optional[str]:
        """Walk a path through the Olog, returning end node or None."""
        current = start
        for label in labels:
            found = False
            for morph in self._morphisms_from.get(current, []):
                if morph.label == label:
                    current = morph.target
                    found = True
                    break
            if not found:
                return None
        return current
    
    def audit_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit an AI response by requiring proofs for all claims.
        
        Args:
            response: AI response containing claims to verify
            
        Returns:
            Audit report with proof status for each claim
        """
        audit = {
            "total_claims": 0,
            "proven": 0,
            "failed": 0,
            "hallucinations": [],
            "proofs": []
        }
        
        # Extract claims from response
        claims = response.get("claims", [])
        if isinstance(response.get("olog_aspects"), list):
            # Convert Olog aspects to claims
            for aspect in response["olog_aspects"]:
                if isinstance(aspect, dict):
                    claims.append(f"{aspect.get('source', '')} {aspect.get('label', '')} {aspect.get('target', '')}")
        
        audit["total_claims"] = len(claims)
        
        for claim in claims:
            proof = self.prove(claim)
            audit["proofs"].append(proof.to_dict())
            
            if proof.is_valid:
                audit["proven"] += 1
            else:
                audit["failed"] += 1
                audit["hallucinations"].append({
                    "claim": claim,
                    "reason": proof.failure_reason
                })
        
        return audit


def demo():
    """Demonstrate proof object generation with different modes."""
    print("=" * 70)
    print("  PROOF OBJECT GENERATION DEMO - Hallucination Detection")
    print("=" * 70)
    
    # Create sample Olog
    olog = OlogGraph(name="BusinessOntology")
    
    # Add types
    olog.add_type("Customer", "A person who purchases")
    olog.add_type("Order", "A purchase request")
    olog.add_type("Product", "An item for sale")
    olog.add_type("Invoice", "A payment request")
    olog.add_type("Payment", "A completed transaction")
    olog.add_type("Shipment", "Delivery of products")
    
    # Add aspects
    olog.add_aspect("Customer", "Order", "places")
    olog.add_aspect("Order", "Product", "contains")
    olog.add_aspect("Order", "Invoice", "generates")
    olog.add_aspect("Invoice", "Payment", "requires")
    olog.add_aspect("Payment", "Shipment", "triggers")
    olog.add_aspect("Shipment", "Customer", "delivers_to")
    
    print("\n[OLOG STRUCTURE]")
    print(f"  Types: {list(olog.graph.nodes())}")
    print(f"  Edges: Customer --places--> Order --generates--> Invoice --requires--> Payment")
    print(f"         Payment --triggers--> Shipment --delivers_to--> Customer (cycle)")
    
    # Test claims across all three modes
    test_claims = [
        ("Customer places Order", True, "Direct edge exists"),
        ("Order generates Invoice", True, "Direct edge exists"),
        ("Payment places Customer", False, "Wrong relation - path exists but uses 'triggers', 'delivers_to'"),
        ("Customer triggers Shipment", False, "Wrong relation - 'triggers' is Payment->Shipment, not Customer->"),
        ("Product generates Invoice", False, "No path at all"),
    ]
    
    for mode in [ProofMode.STRICT, ProofMode.COMPOSITIONAL, ProofMode.REACHABILITY]:
        print(f"\n{'='*70}")
        print(f"  MODE: {mode.value.upper()}")
        print(f"{'='*70}")
        
        engine = ProofEngine(olog, mode=mode)
        
        for claim, expected_strict, reason in test_claims:
            proof = engine.prove(claim)
            status_icon = "✓" if proof.is_valid else "✗"
            print(f"\n  {status_icon} \"{claim}\"")
            print(f"    Status: {proof.status.value}")
            if proof.failure_reason:
                print(f"    Reason: {proof.failure_reason}")
            elif proof.root:
                path = " ∘ ".join(proof.root.morphism_path) if proof.root.morphism_path else "id"
                print(f"    Path: {path}")
    
    # Audit an AI response
    print("\n[RESPONSE AUDIT]")
    
    ai_response = {
        "claims": [
            "Customer places Order",
            "Order generates Invoice",
            "Invoice creates Payment",  # WRONG - should be "requires"
        ],
        "olog_aspects": [
            {"source": "Payment", "label": "triggers", "target": "Shipment"},
            {"source": "Shipment", "label": "contains", "target": "Product"},  # WRONG
        ]
    }
    
    audit = engine.audit_response(ai_response)
    
    print(f"  Total claims: {audit['total_claims']}")
    print(f"  Proven: {audit['proven']}")
    print(f"  Failed: {audit['failed']}")
    
    if audit['hallucinations']:
        print("\n  ⚠ HALLUCINATIONS DETECTED:")
        for h in audit['hallucinations']:
            print(f"    - {h['claim']}: {h['reason']}")
    
    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()

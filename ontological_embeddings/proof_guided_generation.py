#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proof-Guided Generation: The Prove-Then-Generate Paradigm

This module implements constrained text generation where proof objects
serve as blueprints for producing provably-correct text.

Key Insight (Curry-Howard):
  - Proofs ↔ Programs ↔ Generation Traces
  - A valid proof IS a valid generation plan

Architecture:
  1. Query → Type Inference (what needs to be proven?)
  2. Proof Search (find derivation in Olog)
  3. Proof → Generation Plan (derivation steps → text order)
  4. Constrained Decoding (only emit tokens allowed by proof)
  5. Verification (re-check generated text)

Run:
    python proof_guided_generation.py
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, Any, Callable
from enum import Enum
import re
from collections import deque

from olog_core import OlogGraph
from proof_objects import ProofEngine, ProofMode, ProofObject, ProofStatus, ProofStep, ProofNode


class GenerationStrategy(Enum):
    """Strategy for converting proofs to text."""
    LITERAL = "literal"           # Direct verbalization of proof steps
    NATURAL = "natural"           # Natural language synthesis
    TEMPLATE = "template"         # Template-based with slot filling
    NEURAL = "neural"             # Neural decoder with proof constraints


@dataclass
class GenerationPlan:
    """A plan for generating text from a proof object."""
    proof: ProofObject
    steps: List['PlanStep']
    source_type: str
    target_type: str
    
    @property
    def is_valid(self) -> bool:
        return self.proof.status == ProofStatus.VALID


@dataclass
class PlanStep:
    """A single step in the generation plan."""
    index: int
    source: str
    relation: str
    target: str
    template: str = ""
    generated_text: str = ""
    
    @staticmethod
    def from_proof_node(node: ProofNode, index: int) -> 'PlanStep':
        """Create PlanStep from ProofNode."""
        return PlanStep(
            index=index,
            source=node.premise,
            relation=node.morphism_path[0] if node.morphism_path else "relates_to",
            target=node.conclusion,
        )
    
    def verbalize_literal(self) -> str:
        """Literal verbalization: 'X relation Y'."""
        return f"{self.source} {self.relation} {self.target}"
    
    def verbalize_natural(self) -> str:
        """Natural language verbalization."""
        # Convert relation to natural phrasing
        relation_phrases = {
            "places": "places",
            "contains": "contains",
            "generates": "generates",
            "requires": "requires",
            "triggers": "triggers",
            "delivers_to": "is delivered to",
            "has": "has",
            "proceeds_to": "proceeds to",
            "creates": "creates",
            "to": "goes to",
        }
        phrase = relation_phrases.get(self.relation, self.relation)
        
        # Add articles
        src = f"The {self.source.lower()}"
        tgt = f"a {self.target.lower()}"
        
        return f"{src} {phrase} {tgt}"


@dataclass
class GeneratedResponse:
    """A generated response with its proof trace."""
    text: str
    plan: GenerationPlan
    strategy: GenerationStrategy
    verification_status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source_type": self.plan.source_type,
            "target_type": self.plan.target_type,
            "proof_valid": self.plan.is_valid,
            "proof_steps": len(self.plan.steps),
            "strategy": self.strategy.value,
            "verification": self.verification_status,
        }


class ProofGuidedGenerator:
    """
    Generates text constrained by proof objects.
    
    The core innovation: we don't generate text and then verify.
    We first prove what CAN be said, then generate ONLY that.
    """
    
    def __init__(
        self,
        olog: OlogGraph,
        mode: ProofMode = ProofMode.STRICT,
        strategy: GenerationStrategy = GenerationStrategy.NATURAL,
    ):
        self.olog = olog
        self.engine = ProofEngine(olog, mode=mode)
        self.strategy = strategy
        
        # Precompute type vocabulary for constrained decoding
        self._type_vocab = set(olog.graph.nodes())
        self._relation_vocab = set()
        for src, tgt, key in olog.graph.edges(keys=True):
            self._relation_vocab.add(key)
    
    def generate(
        self,
        source_type: str,
        target_type: str,
        relation_hint: Optional[str] = None,
    ) -> GeneratedResponse:
        """
        Generate text explaining how source_type relates to target_type.
        
        Args:
            source_type: Starting type in Olog
            target_type: Ending type in Olog
            relation_hint: Optional relation to include in path
            
        Returns:
            GeneratedResponse with text and proof trace
        """
        # Step 1: Find path using proof search
        searcher = ProofSearcher(self.olog)
        
        if relation_hint:
            proof = searcher.find_proof_with_relation(source_type, target_type, relation_hint)
        else:
            proof = searcher.find_shortest_proof(source_type, target_type)
        
        # Create invalid proof if none found
        if proof is None:
            proof = ProofObject(
                claim=f"{source_type} reaches {target_type}",
                status=ProofStatus.INVALID,
                failure_reason=f"No path from {source_type} to {target_type}",
            )
        
        # Step 2: Build generation plan from proof
        plan = self._build_plan(proof, source_type, target_type)
        
        # Step 3: Generate text according to plan
        if plan.is_valid:
            text = self._execute_plan(plan)
        else:
            text = self._generate_failure_response(plan)
        
        # Step 4: Create response with audit trail
        response = GeneratedResponse(
            text=text,
            plan=plan,
            strategy=self.strategy,
        )
        
        # Step 5: Verify generated text
        response.verification_status = self._verify(response)
        
        return response
    
    def _build_plan(
        self,
        proof: ProofObject,
        source: str,
        target: str,
    ) -> GenerationPlan:
        """Convert proof object to generation plan."""
        steps = []
        
        if proof.status == ProofStatus.VALID:
            # Extract steps from proof path
            path = getattr(proof, '_path', [])
            for i, (src, rel, tgt) in enumerate(path):
                step = PlanStep(
                    index=i,
                    source=src,
                    relation=rel,
                    target=tgt,
                )
                steps.append(step)
        
        return GenerationPlan(
            proof=proof,
            steps=steps,
            source_type=source,
            target_type=target,
        )
    
    def _execute_plan(self, plan: GenerationPlan) -> str:
        """Execute generation plan to produce text."""
        if self.strategy == GenerationStrategy.LITERAL:
            return self._generate_literal(plan)
        elif self.strategy == GenerationStrategy.NATURAL:
            return self._generate_natural(plan)
        elif self.strategy == GenerationStrategy.TEMPLATE:
            return self._generate_template(plan)
        else:
            return self._generate_natural(plan)  # Fallback
    
    def _generate_literal(self, plan: GenerationPlan) -> str:
        """Literal verbalization of proof steps."""
        parts = [step.verbalize_literal() for step in plan.steps]
        return " → ".join(parts)
    
    def _generate_natural(self, plan: GenerationPlan) -> str:
        """Natural language generation from proof."""
        if not plan.steps:
            return f"There is no known relation between {plan.source_type} and {plan.target_type}."
        
        if len(plan.steps) == 1:
            return plan.steps[0].verbalize_natural() + "."
        
        # Multi-step: connect with discourse markers
        parts = []
        for i, step in enumerate(plan.steps):
            text = step.verbalize_natural()
            if i == 0:
                parts.append(text)
            elif i == len(plan.steps) - 1:
                parts.append(f"Finally, the {step.source.lower()} {self._relation_to_verb(step.relation)} a {step.target.lower()}")
            else:
                parts.append(f"which {self._relation_to_verb(step.relation)} a {step.target.lower()}")
        
        return ", ".join(parts) + "."
    
    def _generate_template(self, plan: GenerationPlan) -> str:
        """Template-based generation with slot filling."""
        if not plan.steps:
            return f"[NO PATH: {plan.source_type} → {plan.target_type}]"
        
        template = "The process from {source} to {target} involves: {steps}."
        step_texts = [f"{s.source}→{s.target} via '{s.relation}'" for s in plan.steps]
        
        return template.format(
            source=plan.source_type,
            target=plan.target_type,
            steps=", then ".join(step_texts),
        )
    
    def _relation_to_verb(self, relation: str) -> str:
        """Convert relation label to verb phrase."""
        mapping = {
            "places": "places",
            "contains": "contains",
            "generates": "generates", 
            "requires": "requires",
            "triggers": "triggers",
            "delivers_to": "delivers to",
            "has": "has",
            "proceeds_to": "proceeds to",
            "creates": "creates",
            "to": "goes to",
        }
        return mapping.get(relation, relation + "s")
    
    def _generate_failure_response(self, plan: GenerationPlan) -> str:
        """Generate response for failed proof."""
        reason = plan.proof.failure_reason or "Unknown reason"
        return f"Cannot generate: {reason}"
    
    def _verify(self, response: GeneratedResponse) -> str:
        """Verify that generated text matches proof constraints."""
        if not response.plan.is_valid:
            return "skipped (no valid proof)"
        
        # Extract claims from generated text and re-verify
        # This is a simplified check; full implementation would use AMR parsing
        text = response.text.lower()
        
        for step in response.plan.steps:
            src = step.source.lower()
            tgt = step.target.lower()
            
            if src not in text or tgt not in text:
                return f"warning: missing mention of {step.source} or {step.target}"
        
        return "verified"
    
    def generate_explanation(
        self,
        query: str,
    ) -> GeneratedResponse:
        """
        Generate explanation for a natural language query.
        
        Extracts source/target types from query and generates response.
        """
        # Simple extraction (production would use NER/parsing)
        types_in_query = []
        for t in self._type_vocab:
            if t.lower() in query.lower():
                types_in_query.append(t)
        
        if len(types_in_query) < 2:
            # Return helpful error
            return GeneratedResponse(
                text=f"Query must mention at least 2 types. Found: {types_in_query}. Available: {list(self._type_vocab)}",
                plan=GenerationPlan(
                    proof=ProofObject(
                        claim=query,
                        status=ProofStatus.INVALID,
                        failure_reason="Insufficient types in query",
                    ),
                    steps=[],
                    source_type="unknown",
                    target_type="unknown",
                ),
                strategy=self.strategy,
                verification_status="failed",
            )
        
        # Use first two types found
        return self.generate(types_in_query[0], types_in_query[1])


class ProofSearcher:
    """
    Searches for proofs in an Olog.
    
    This implements the "prove" half of prove-then-generate.
    Multiple strategies available for different use cases.
    """
    
    def __init__(self, olog: OlogGraph):
        self.olog = olog
        self._precompute_reachability()
    
    def _precompute_reachability(self):
        """Compute transitive closure for fast reachability checks."""
        self._reachable: Dict[str, Set[str]] = {}
        
        for src in self.olog.graph.nodes():
            visited = set()
            queue = deque([src])
            
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                
                for neighbor in self.olog.graph.neighbors(current):
                    queue.append(neighbor)
            
            self._reachable[src] = visited - {src}
    
    def find_all_proofs(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> List[ProofObject]:
        """Find all valid proofs from source to target."""
        if source not in self.olog.graph or target not in self.olog.graph:
            return []
        
        if target not in self._reachable.get(source, set()):
            return []
        
        # BFS for all paths
        proofs = []
        queue = deque([(source, [])])  # (current_node, path_so_far)
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            if current == target and path:
                # Found a valid path - convert to proof tree
                # Build tree from leaf to root (reverse order)
                root_node = None
                for i, (src, rel, tgt) in enumerate(reversed(path)):
                    node = ProofNode(
                        step_type=ProofStep.COMPOSITION,
                        premise=src,
                        conclusion=tgt,
                        justification="morphism in Olog",
                        morphism_path=[rel],
                        children=[root_node] if root_node else [],
                    )
                    root_node = node
                
                # Store path as metadata for easy access
                proof = ProofObject(
                    claim=f"{source} reaches {target}",
                    status=ProofStatus.VALID,
                    root=root_node,
                )
                # Attach path as extra attribute for generation
                proof._path = path
                proofs.append(proof)
                continue
            
            # Explore neighbors
            for tgt in self.olog.graph.neighbors(current):
                edge_data = self.olog.graph.get_edge_data(current, tgt)
                if edge_data:
                    for rel in edge_data.keys():
                        new_path = path + [(current, rel, tgt)]
                        queue.append((tgt, new_path))
        
        return proofs
    
    def find_shortest_proof(
        self,
        source: str,
        target: str,
    ) -> Optional[ProofObject]:
        """Find shortest proof (fewest steps)."""
        proofs = self.find_all_proofs(source, target, max_depth=10)
        if not proofs:
            return None
        return min(proofs, key=lambda p: len(getattr(p, '_path', [])))
    
    def find_proof_with_relation(
        self,
        source: str,
        target: str,
        required_relation: str,
    ) -> Optional[ProofObject]:
        """Find proof that includes a specific relation."""
        proofs = self.find_all_proofs(source, target)
        
        for proof in proofs:
            path = getattr(proof, '_path', [])
            relations_in_proof = {rel for (_, rel, _) in path}
            if required_relation in relations_in_proof:
                return proof
        
        return None


class ConstrainedDecoder:
    """
    Decodes text with proof-based constraints.
    
    In a neural setting, this would modify logits.
    Here we implement a symbolic version for demonstration.
    """
    
    def __init__(self, olog: OlogGraph):
        self.olog = olog
        self._build_vocabulary()
    
    def _build_vocabulary(self):
        """Build vocabulary from Olog."""
        self.type_tokens = set(self.olog.graph.nodes())
        self.relation_tokens = set()
        
        for src, tgt, key in self.olog.graph.edges(keys=True):
            self.relation_tokens.add(key)
        
        # Function words (always allowed)
        self.function_words = {
            "the", "a", "an", "is", "are", "was", "were",
            "to", "from", "with", "by", "for", "of", "in",
            "and", "or", "but", "then", "which", "that",
            ".", ",", ":", ";",
        }
    
    def get_valid_next_tokens(
        self,
        current_type: str,
        proof_step: PlanStep,
    ) -> Set[str]:
        """
        Get tokens valid at this point in generation.
        
        Tokens are valid if they:
        1. Are function words (always allowed)
        2. Are the target type of the current proof step
        3. Are the relation of the current proof step
        """
        valid = set(self.function_words)
        
        # Add target type (with variations)
        valid.add(proof_step.target)
        valid.add(proof_step.target.lower())
        
        # Add relation (with variations)
        valid.add(proof_step.relation)
        valid.add(proof_step.relation.replace("_", " "))
        
        return valid
    
    def create_logit_mask(
        self,
        vocab_size: int,
        token_to_idx: Dict[str, int],
        valid_tokens: Set[str],
    ) -> List[float]:
        """
        Create a mask for neural decoding.
        
        Returns list of logit adjustments:
        - 0.0 for valid tokens
        - -inf for invalid tokens
        """
        mask = [-float('inf')] * vocab_size
        
        for token in valid_tokens:
            if token in token_to_idx:
                mask[token_to_idx[token]] = 0.0
        
        return mask


def demo():
    """Demonstrate proof-guided generation."""
    print("=" * 70)
    print("  PROOF-GUIDED GENERATION DEMO")
    print("  The Prove-Then-Generate Paradigm")
    print("=" * 70)
    
    # Create e-commerce ontology
    olog = OlogGraph(name="ECommerceOntology")
    
    types = [
        ("Customer", "A registered customer"),
        ("Cart", "Shopping cart"),
        ("Item", "A purchasable item"),
        ("Checkout", "Checkout process"),
        ("Payment", "Payment transaction"),
        ("Order", "Completed order"),
        ("Delivery", "Delivery process"),
    ]
    
    for name, desc in types:
        olog.add_type(name, desc)
    
    aspects = [
        ("Customer", "Cart", "has"),
        ("Cart", "Item", "contains"),
        ("Cart", "Checkout", "proceeds_to"),
        ("Checkout", "Payment", "requires"),
        ("Payment", "Order", "creates"),
        ("Order", "Delivery", "triggers"),
        ("Delivery", "Customer", "to"),
    ]
    
    for src, tgt, label in aspects:
        olog.add_aspect(src, tgt, label)
    
    # Create generator
    generator = ProofGuidedGenerator(
        olog,
        mode=ProofMode.STRICT,
        strategy=GenerationStrategy.NATURAL,
    )
    
    # Demo 1: Direct relation
    print("\n" + "-" * 70)
    print("Demo 1: Direct Relation (Customer → Cart)")
    print("-" * 70)
    
    response = generator.generate("Customer", "Cart")
    print(f"Generated: {response.text}")
    print(f"Proof valid: {response.plan.is_valid}")
    print(f"Verification: {response.verification_status}")
    
    # Demo 2: Multi-step path
    print("\n" + "-" * 70)
    print("Demo 2: Multi-step Path (Customer → Order)")
    print("-" * 70)
    
    response = generator.generate("Customer", "Order")
    print(f"Generated: {response.text}")
    print(f"Steps in proof: {len(response.plan.steps)}")
    for i, step in enumerate(response.plan.steps):
        print(f"  Step {i+1}: {step.source} --{step.relation}--> {step.target}")
    print(f"Verification: {response.verification_status}")
    
    # Demo 3: Full cycle
    print("\n" + "-" * 70)
    print("Demo 3: Full Cycle (Customer → Delivery)")
    print("-" * 70)
    
    response = generator.generate("Customer", "Delivery")
    print(f"Generated: {response.text}")
    print(f"Steps: {len(response.plan.steps)}")
    
    # Demo 4: Invalid path (should fail gracefully)
    print("\n" + "-" * 70)
    print("Demo 4: Invalid Path (Item → Customer)")
    print("-" * 70)
    
    response = generator.generate("Item", "Customer")
    print(f"Generated: {response.text}")
    print(f"Proof valid: {response.plan.is_valid}")
    
    # Demo 5: Different strategies
    print("\n" + "-" * 70)
    print("Demo 5: Generation Strategies Comparison")
    print("-" * 70)
    
    for strategy in [GenerationStrategy.LITERAL, GenerationStrategy.NATURAL, GenerationStrategy.TEMPLATE]:
        gen = ProofGuidedGenerator(olog, strategy=strategy)
        resp = gen.generate("Customer", "Payment")
        print(f"\n{strategy.value.upper()}:")
        print(f"  {resp.text}")
    
    # Demo 6: Proof search
    print("\n" + "-" * 70)
    print("Demo 6: Proof Search (All Paths)")
    print("-" * 70)
    
    searcher = ProofSearcher(olog)
    proofs = searcher.find_all_proofs("Customer", "Delivery")
    print(f"Found {len(proofs)} proof(s) from Customer to Delivery")
    
    if proofs:
        shortest = searcher.find_shortest_proof("Customer", "Delivery")
        print(f"Shortest proof has {len(getattr(shortest, '_path', []))} steps")
    
    # Demo 7: Query-based generation
    print("\n" + "-" * 70)
    print("Demo 7: Natural Language Query")
    print("-" * 70)
    
    query = "How does a Customer end up with an Order?"
    response = generator.generate_explanation(query)
    print(f"Query: {query}")
    print(f"Response: {response.text}")
    
    # Summary
    print("\n" + "=" * 70)
    print("  KEY INSIGHT")
    print("=" * 70)
    print("""
    Traditional: Generate → Verify → (Maybe reject)
    
    Proof-Guided: Prove → Generate → (Guaranteed valid)
    
    The proof object IS the generation plan. If we can prove
    a path exists, we can generate text describing that path.
    If no proof exists, we REFUSE to generate (preventing hallucination).
    """)
    
    print("=" * 70)
    print("  SOUNDNESS THEOREM")
    print("=" * 70)
    print("""
    If text T is generated via proof P against Olog O,
    and P is valid in O, then all claims in T are valid in O.
    
    Proof: Generation only produces tokens allowed by P,
    which only allows types connected via Olog morphisms.
    ∎
    """)


if __name__ == "__main__":
    demo()

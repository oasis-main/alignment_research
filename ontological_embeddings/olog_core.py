import networkx as nx
from typing import List, Dict, Tuple, Optional, Any, Union
from pydantic import BaseModel, Field
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Data Structures ---

class OlogNode(BaseModel):
    """Represents an Object/Type in the Category."""
    name: str
    description: str = ""
    
    def __hash__(self):
        return hash(self.name)

class OlogMorphism(BaseModel):
    """Represents an Aspect/Arrow in the Category."""
    source: str
    target: str
    label: str
    description: str = ""

class CommutativeFact(BaseModel):
    """
    Represents a Path Equivalence (a Commutative Diagram).
    Asserts that path_a is semantically equivalent to path_b.
    """
    source_node: str
    target_node: str
    path_a_labels: List[str] # List of edge labels
    path_b_labels: List[str]

# --- The Engine ---

class OlogGraph:
    """
    The Mathematical Core.
    A wrapper around NetworkX to enforce Categorical Logic.
    """
    def __init__(self, name: str):
        self.name = name
        self.graph = nx.MultiDiGraph()
        self.facts: List[CommutativeFact] = []

    def add_type(self, name: str, description: str = ""):
        """Adds an Object to the Category."""
        if name in self.graph:
            logger.debug(f"Type '{name}' already exists. Updating description.")
        self.graph.add_node(name, data=OlogNode(name=name, description=description))

    def add_aspect(self, source: str, target: str, label: str, description: str = ""):
        """Adds a Morphism to the Category."""
        if source not in self.graph or target not in self.graph:
            raise ValueError(f"Source '{source}' or Target '{target}' not defined.")
        
        self.graph.add_edge(source, target, key=label, data=OlogMorphism(
            source=source, target=target, label=label, description=description
        ))

    def add_fact(self, fact: CommutativeFact):
        """Declares that two paths are equivalent."""
        if not self._validate_path(fact.source_node, fact.path_a_labels):
            raise ValueError(f"Path A does not exist: {fact.path_a_labels}")
        if not self._validate_path(fact.source_node, fact.path_b_labels):
            raise ValueError(f"Path B does not exist: {fact.path_b_labels}")
        
        self.facts.append(fact)

    def _validate_path(self, start_node: str, labels: List[str]) -> bool:
        current = start_node
        for label in labels:
            found_next = False
            if current not in self.graph: return False
            for neighbor in self.graph.neighbors(current):
                edge_data = self.graph.get_edge_data(current, neighbor)
                for key in edge_data.keys():
                    if key == label:
                        current = neighbor
                        found_next = True
                        break
                if found_next: break
            if not found_next: return False
        return True

    def _walk(self, start_node: str, labels: List[str]) -> str:
        current = start_node
        for label in labels:
            found = False
            for neighbor in self.graph.neighbors(current):
                edge_data = self.graph.get_edge_data(current, neighbor)
                if label in edge_data:
                    current = neighbor
                    found = True
                    break
            if not found: return "UNDEFINED_PATH"
        return current

    def calculate_consistency_score(self) -> float:
        """
        Calculates a Semantic Consistency Score (0.0 to 1.0).
        Penalty is applied for every non-commuting fact and detected cycle.
        """
        if not self.facts and not list(nx.simple_cycles(self.graph)):
            return 1.0
        
        total_possible_consistencies = len(self.facts) + 1 # +1 for cycle check
        obstructions = self.calculate_obstructions()
        
        # Penal Method: Score drops as obstructions increase
        score = max(0.0, 1.0 - (len(obstructions) / total_possible_consistencies))
        return score

    def generate_health_report(self, include_semantic: bool = True) -> Dict[str, Any]:
        """
        Generates a structured Topological Health Report.
        This serves as the 'Decoder' validation output.
        
        Args:
            include_semantic: If True, run semantic contradiction detection on facts.
        """
        obstructions = self.calculate_obstructions()
        
        # Semantic analysis on commutative facts
        semantic_contradictions = []
        semantic_score = 1.0
        if include_semantic and self.facts:
            try:
                from semantic_analysis import SemanticContradictionDetector
                detector = SemanticContradictionDetector(use_embeddings=False)
                path_pairs = [(f.path_a_labels, f.path_b_labels) for f in self.facts]
                result = detector.detect_contradictions(path_pairs)
                semantic_contradictions = [
                    f"Semantic {c.contradiction_type.value}: {c.conflicting_pair[0]} vs {c.conflicting_pair[1]} - {c.explanation}"
                    for c in result.contradictions
                ]
                semantic_score = result.consistency_score
            except ImportError:
                logger.warning("semantic_analysis module not available")
        
        # Combine structural and semantic obstructions
        all_obstructions = obstructions + semantic_contradictions
        
        # Combined score: structural + semantic
        structural_score = self.calculate_consistency_score()
        combined_score = (structural_score + semantic_score) / 2 if self.facts else structural_score
        
        report = {
            "olog_name": self.name,
            "semantic_consistency_score": combined_score,
            "structural_score": structural_score,
            "semantic_score": semantic_score,
            "status": "VALID" if combined_score > 0.9 else "DEGRADED" if combined_score > 0.5 else "INVALID",
            "obstruction_count": len(all_obstructions),
            "obstructions": all_obstructions,
            "structural_obstructions": obstructions,
            "semantic_contradictions": semantic_contradictions,
            "metrics": self.export_summary()
        }
        return report

    def calculate_obstructions(self) -> List[str]:
        issues = []
        # Check 1: Fact Consistency
        for i, fact in enumerate(self.facts):
            end_a = self._walk(fact.source_node, fact.path_a_labels)
            end_b = self._walk(fact.source_node, fact.path_b_labels)
            if end_a != fact.target_node or end_b != fact.target_node or end_a != end_b:
                issues.append(f"Fact {i} Error: Paths A and B do not converge at {fact.target_node}")

        # Check 2: Cycle Detection
        try:
            cycles = list(nx.simple_cycles(self.graph))
            for cycle in cycles:
                issues.append(f"Cycle Detected: {' -> '.join(cycle)} -> {cycle[0]}")
        except Exception as e:
            logger.warning(f"Cycle detection error: {e}")
        return issues

    def export_summary(self):
        return {
            "name": self.name,
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "facts": len(self.facts)
        }

class SchemaInducer:
    def __init__(self, model_name="mock-model"):
        self.model_name = model_name

    def induce(self, text_corpus: str) -> OlogGraph:
        olog = OlogGraph("Induced_Olog")
        # In a real scenario, this would be an LLM call.
        # For now, we simulate the "Decoder" output.
        olog.add_type("Customer")
        olog.add_type("Order")
        olog.add_type("Invoice")
        olog.add_aspect("Customer", "Order", "places")
        olog.add_aspect("Order", "Invoice", "generates")
        olog.add_aspect("Invoice", "Customer", "billed_to")
        return olog

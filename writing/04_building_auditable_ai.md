# Building an Auditable AI: A Complete Walkthrough

*From ontology to deployment with proof traces*

---

## What We're Building

By the end of this tutorial, you'll have:

1. ✅ An **ontology** defining your domain
2. ✅ A **proof engine** that validates claims
3. ✅ A **generator** that only produces provable statements
4. ✅ **Audit logs** for every generated response
5. ✅ A deployable **API** with full traceability

Let's build an auditable AI for an e-commerce support system.

---

## Prerequisites

```bash
# Clone the repository
git clone https://github.com/oasis-main/alignment_research
cd alignment_research/tlts_compilation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install networkx pydantic numpy

# Optional: for full features
pip install anthropic amrlib rdflib
```

---

## Step 1: Define Your Ontology

An ontology is a formal description of your domain. We use **Ologs** (Ontology Logs) based on category theory.

### 1.1 Create the Olog

```python
# my_ontology.py
from olog_core import OlogGraph

def create_ecommerce_ontology():
    """Define e-commerce domain ontology."""
    olog = OlogGraph(name="ECommerceSupport")
    
    # Step 1: Define types (objects in your domain)
    types = [
        ("Customer", "A registered customer"),
        ("Account", "Customer's account"),
        ("Cart", "Shopping cart"),
        ("Item", "A purchasable product"),
        ("Checkout", "Checkout process"),
        ("Payment", "Payment transaction"),
        ("Order", "Completed order"),
        ("Shipment", "Package shipment"),
        ("Return", "Return request"),
        ("Refund", "Refund transaction"),
    ]
    
    for name, description in types:
        olog.add_type(name, description)
    
    # Step 2: Define relations (morphisms between types)
    relations = [
        # Customer journey
        ("Customer", "Account", "has"),
        ("Customer", "Cart", "owns"),
        ("Cart", "Item", "contains"),
        ("Cart", "Checkout", "proceeds_to"),
        ("Checkout", "Payment", "requires"),
        ("Payment", "Order", "creates"),
        
        # Order fulfillment
        ("Order", "Shipment", "triggers"),
        ("Shipment", "Customer", "delivers_to"),
        
        # Returns and refunds
        ("Order", "Return", "can_have"),
        ("Return", "Refund", "results_in"),
        ("Refund", "Account", "credits"),
    ]
    
    for source, target, label in relations:
        olog.add_aspect(source, target, label)
    
    return olog

if __name__ == "__main__":
    olog = create_ecommerce_ontology()
    print(f"Created ontology: {olog.name}")
    print(f"Types: {list(olog.graph.nodes())}")
    print(f"Relations: {list(olog.graph.edges(keys=True))}")
```

### 1.2 Visualize Your Ontology

```python
# visualize_ontology.py
import networkx as nx
import matplotlib.pyplot as plt
from my_ontology import create_ecommerce_ontology

def visualize(olog):
    """Create visual diagram of ontology."""
    plt.figure(figsize=(12, 8))
    
    pos = nx.spring_layout(olog.graph, k=2, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(olog.graph, pos, node_color='lightblue', 
                           node_size=2000, alpha=0.9)
    nx.draw_networkx_labels(olog.graph, pos, font_size=10, font_weight='bold')
    
    # Draw edges with labels
    edge_labels = {(u, v): d for u, v, d in olog.graph.edges(keys=True)}
    nx.draw_networkx_edges(olog.graph, pos, arrows=True, 
                           arrowsize=20, edge_color='gray')
    nx.draw_networkx_edge_labels(olog.graph, pos, edge_labels, font_size=8)
    
    plt.title(f"Ontology: {olog.name}")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('ontology_diagram.png', dpi=150)
    plt.show()

if __name__ == "__main__":
    olog = create_ecommerce_ontology()
    visualize(olog)
```

---

## Step 2: Build the Proof Engine

The proof engine validates claims against your ontology.

### 2.1 Basic Claim Verification

```python
# verify_claims.py
from my_ontology import create_ecommerce_ontology
from proof_objects import ProofEngine, ProofMode

def setup_verifier():
    """Create proof engine with STRICT mode."""
    olog = create_ecommerce_ontology()
    engine = ProofEngine(olog, mode=ProofMode.STRICT)
    return engine

def verify_claim(engine, claim):
    """Verify a single claim and print result."""
    proof = engine.prove(claim)
    
    status = "✓" if proof.is_valid else "✗"
    print(f"{status} {claim}")
    
    if not proof.is_valid:
        print(f"   Reason: {proof.failure_reason}")
    
    return proof

if __name__ == "__main__":
    engine = setup_verifier()
    
    # Test various claims
    claims = [
        # Valid direct relations
        "Customer has Account",
        "Cart contains Item",
        "Payment creates Order",
        
        # Invalid shortcuts (hallucinations!)
        "Customer creates Order",      # Skips cart, checkout, payment
        "Cart triggers Shipment",      # Skips checkout, payment, order
        "Item requires Payment",       # No such relation
        
        # Valid compositions (in COMPOSITIONAL mode)
        "Customer owns Cart",
        "Order can_have Return",
    ]
    
    print("=" * 50)
    print("CLAIM VERIFICATION")
    print("=" * 50)
    
    for claim in claims:
        verify_claim(engine, claim)
```

### 2.2 Batch Response Auditing

```python
# audit_response.py
from my_ontology import create_ecommerce_ontology
from proof_objects import ProofEngine, ProofMode

def audit_llm_response(response_text, engine):
    """
    Audit an LLM response for hallucinations.
    
    In production, you'd use NLP to extract claims.
    Here we simulate with a simple format.
    """
    # Simple claim extraction (production: use AMR parsing)
    claims = extract_claims(response_text)
    
    audit_result = {
        "response": response_text,
        "total_claims": len(claims),
        "valid": [],
        "invalid": [],
    }
    
    for claim in claims:
        proof = engine.prove(claim)
        if proof.is_valid:
            audit_result["valid"].append({
                "claim": claim,
                "proof": proof.to_dict() if hasattr(proof, 'to_dict') else str(proof)
            })
        else:
            audit_result["invalid"].append({
                "claim": claim,
                "reason": proof.failure_reason
            })
    
    audit_result["hallucination_rate"] = (
        len(audit_result["invalid"]) / len(claims) if claims else 0
    )
    
    return audit_result

def extract_claims(text):
    """
    Extract claims from text.
    
    Simple implementation: looks for "X verb Y" patterns.
    Production: use AMR parsing or dependency parsing.
    """
    import re
    
    # Pattern: Type relation Type
    patterns = [
        r"(\w+)\s+(has|owns|contains|creates|triggers|requires)\s+(\w+)",
        r"(\w+)\s+(proceeds_to|delivers_to|results_in|can_have|credits)\s+(\w+)",
    ]
    
    claims = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            claim = f"{match[0].capitalize()} {match[1]} {match[2].capitalize()}"
            claims.append(claim)
    
    return claims

if __name__ == "__main__":
    olog = create_ecommerce_ontology()
    engine = ProofEngine(olog, mode=ProofMode.STRICT)
    
    # Simulate LLM response
    llm_response = """
    When a Customer creates an Order, the Order triggers a Shipment.
    The Customer has an Account and owns a Cart.
    The Cart contains Items and proceeds_to Checkout.
    """
    
    audit = audit_llm_response(llm_response, engine)
    
    print("=" * 50)
    print("AUDIT REPORT")
    print("=" * 50)
    print(f"Total claims: {audit['total_claims']}")
    print(f"Valid: {len(audit['valid'])}")
    print(f"Invalid (hallucinations): {len(audit['invalid'])}")
    print(f"Hallucination rate: {audit['hallucination_rate']:.1%}")
    
    print("\n--- Valid Claims ---")
    for v in audit['valid']:
        print(f"  ✓ {v['claim']}")
    
    print("\n--- Hallucinations ---")
    for h in audit['invalid']:
        print(f"  ✗ {h['claim']}")
        print(f"    Reason: {h['reason']}")
```

---

## Step 3: Proof-Guided Generation

Generate text that's provably correct.

### 3.1 Basic Generator

```python
# generate_safe.py
from my_ontology import create_ecommerce_ontology
from proof_guided_generation import ProofGuidedGenerator, GenerationStrategy

def create_generator():
    """Set up proof-guided generator."""
    olog = create_ecommerce_ontology()
    generator = ProofGuidedGenerator(
        olog,
        strategy=GenerationStrategy.NATURAL
    )
    return generator

def generate_explanation(generator, source, target):
    """Generate explanation for how source relates to target."""
    response = generator.generate(source, target)
    
    print(f"\nQuery: How does {source} relate to {target}?")
    print(f"Response: {response.text}")
    print(f"Proof valid: {response.plan.is_valid}")
    print(f"Verification: {response.verification_status}")
    
    if response.plan.steps:
        print("Derivation:")
        for step in response.plan.steps:
            print(f"  {step.source} --{step.relation}--> {step.target}")
    
    return response

if __name__ == "__main__":
    generator = create_generator()
    
    # Generate various explanations
    queries = [
        ("Customer", "Order"),
        ("Cart", "Shipment"),
        ("Order", "Refund"),
        ("Item", "Customer"),  # Should fail gracefully
    ]
    
    print("=" * 50)
    print("PROOF-GUIDED GENERATION")
    print("=" * 50)
    
    for source, target in queries:
        generate_explanation(generator, source, target)
```

### 3.2 Customer Support Bot

```python
# support_bot.py
from my_ontology import create_ecommerce_ontology
from proof_guided_generation import ProofGuidedGenerator, GenerationStrategy

class SupportBot:
    """E-commerce support bot with provable responses."""
    
    def __init__(self):
        self.olog = create_ecommerce_ontology()
        self.generator = ProofGuidedGenerator(
            self.olog,
            strategy=GenerationStrategy.NATURAL
        )
        
        # Map intents to type pairs
        self.intent_map = {
            "order_status": ("Order", "Shipment"),
            "return_process": ("Order", "Refund"),
            "cart_checkout": ("Cart", "Order"),
            "account_info": ("Customer", "Account"),
        }
    
    def respond(self, user_message, intent=None):
        """Generate response with audit trail."""
        # Detect intent (simplified)
        if intent is None:
            intent = self._detect_intent(user_message)
        
        if intent not in self.intent_map:
            return {
                "response": "I'm not sure how to help with that. Could you clarify?",
                "proof": None,
                "auditable": False,
            }
        
        source, target = self.intent_map[intent]
        result = self.generator.generate(source, target)
        
        return {
            "response": result.text,
            "proof": result.plan.proof.to_dict() if result.plan.is_valid else None,
            "auditable": result.plan.is_valid,
            "derivation": [
                {"from": s.source, "via": s.relation, "to": s.target}
                for s in result.plan.steps
            ],
        }
    
    def _detect_intent(self, message):
        """Simple intent detection."""
        message_lower = message.lower()
        
        if "order" in message_lower and ("status" in message_lower or "where" in message_lower):
            return "order_status"
        elif "return" in message_lower or "refund" in message_lower:
            return "return_process"
        elif "cart" in message_lower or "checkout" in message_lower:
            return "cart_checkout"
        elif "account" in message_lower:
            return "account_info"
        
        return None

if __name__ == "__main__":
    bot = SupportBot()
    
    # Test conversations
    messages = [
        "Where is my order?",
        "How do I return something?",
        "I want to checkout my cart",
        "What's in my account?",
        "Can you tell me about the weather?",  # Unknown intent
    ]
    
    print("=" * 50)
    print("SUPPORT BOT DEMO")
    print("=" * 50)
    
    for msg in messages:
        print(f"\nUser: {msg}")
        response = bot.respond(msg)
        print(f"Bot: {response['response']}")
        print(f"Auditable: {response['auditable']}")
        if response['derivation']:
            print(f"Proof: {' → '.join([d['from'] for d in response['derivation']] + [response['derivation'][-1]['to']])}")
```

---

## Step 4: Add Audit Logging

Every response should have a traceable proof.

### 4.1 Audit Logger

```python
# audit_logger.py
import json
import datetime
from pathlib import Path

class AuditLogger:
    """Log all generations with their proofs."""
    
    def __init__(self, log_dir="audit_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
    def log(self, request, response, proof_data):
        """Log a generation event."""
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "request": request,
            "response": response,
            "proof": proof_data,
            "status": "valid" if proof_data else "unverified",
        }
        
        # Write to daily log file
        today = datetime.date.today().isoformat()
        log_file = self.log_dir / f"audit_{today}.jsonl"
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        return entry["timestamp"]
    
    def query_logs(self, date=None, status=None):
        """Query audit logs."""
        if date is None:
            date = datetime.date.today().isoformat()
        
        log_file = self.log_dir / f"audit_{date}.jsonl"
        
        if not log_file.exists():
            return []
        
        entries = []
        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)
                if status is None or entry["status"] == status:
                    entries.append(entry)
        
        return entries
    
    def get_hallucination_rate(self, date=None):
        """Calculate hallucination rate for a date."""
        entries = self.query_logs(date)
        
        if not entries:
            return None
        
        valid = sum(1 for e in entries if e["status"] == "valid")
        return 1 - (valid / len(entries))

# Integration with SupportBot
class AuditableSupportBot(SupportBot):
    """Support bot with audit logging."""
    
    def __init__(self):
        super().__init__()
        self.logger = AuditLogger()
    
    def respond(self, user_message, intent=None):
        """Generate response and log it."""
        result = super().respond(user_message, intent)
        
        # Log the interaction
        self.logger.log(
            request={"message": user_message, "intent": intent},
            response=result["response"],
            proof_data=result.get("derivation"),
        )
        
        return result
```

---

## Step 5: Create an API

Deploy as a REST API with FastAPI.

### 5.1 API Server

```python
# api_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from my_ontology import create_ecommerce_ontology
from proof_guided_generation import ProofGuidedGenerator, GenerationStrategy
from audit_logger import AuditLogger

app = FastAPI(title="Auditable AI API", version="1.0.0")

# Initialize components
olog = create_ecommerce_ontology()
generator = ProofGuidedGenerator(olog, strategy=GenerationStrategy.NATURAL)
logger = AuditLogger()

class GenerateRequest(BaseModel):
    source_type: str
    target_type: str
    
class GenerateResponse(BaseModel):
    text: str
    is_valid: bool
    derivation: List[Dict[str, str]]
    audit_id: str

class VerifyRequest(BaseModel):
    claim: str
    
class VerifyResponse(BaseModel):
    is_valid: bool
    reason: Optional[str]

@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    """Generate provably-correct text."""
    result = generator.generate(request.source_type, request.target_type)
    
    derivation = [
        {"source": s.source, "relation": s.relation, "target": s.target}
        for s in result.plan.steps
    ]
    
    audit_id = logger.log(
        request=request.dict(),
        response=result.text,
        proof_data=derivation if result.plan.is_valid else None,
    )
    
    return GenerateResponse(
        text=result.text,
        is_valid=result.plan.is_valid,
        derivation=derivation,
        audit_id=audit_id,
    )

@app.post("/verify", response_model=VerifyResponse)
def verify(request: VerifyRequest):
    """Verify a claim against the ontology."""
    from proof_objects import ProofEngine, ProofMode
    engine = ProofEngine(olog, mode=ProofMode.STRICT)
    
    proof = engine.prove(request.claim)
    
    return VerifyResponse(
        is_valid=proof.is_valid,
        reason=proof.failure_reason if not proof.is_valid else None,
    )

@app.get("/ontology/types")
def get_types():
    """List all types in the ontology."""
    return {"types": list(olog.graph.nodes())}

@app.get("/ontology/relations")
def get_relations():
    """List all relations in the ontology."""
    relations = []
    for src, tgt, rel in olog.graph.edges(keys=True):
        relations.append({"source": src, "target": tgt, "relation": rel})
    return {"relations": relations}

@app.get("/audit/today")
def get_today_audit():
    """Get today's audit logs."""
    entries = logger.query_logs()
    rate = logger.get_hallucination_rate()
    
    return {
        "entries": len(entries),
        "hallucination_rate": rate,
        "logs": entries[-10:],  # Last 10 entries
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 5.2 Run the API

```bash
# Install FastAPI
pip install fastapi uvicorn

# Run the server
python api_server.py

# Or with uvicorn directly
uvicorn api_server:app --reload
```

### 5.3 Test the API

```bash
# Generate explanation
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"source_type": "Customer", "target_type": "Order"}'

# Verify a claim
curl -X POST "http://localhost:8000/verify" \
  -H "Content-Type: application/json" \
  -d '{"claim": "Customer creates Order"}'

# Check audit logs
curl "http://localhost:8000/audit/today"
```

---

## Step 6: Deploy with Modal (GPU Training)

For training ontological attention, use Modal.

```bash
# Install Modal
pip install modal

# Set up Modal account
modal setup

# Run training experiments
modal run scripts/modal_olog_training.py
```

---

## Complete File Structure

```
my_auditable_ai/
├── my_ontology.py           # Domain ontology definition
├── verify_claims.py         # Claim verification
├── audit_response.py        # LLM response auditing
├── generate_safe.py         # Proof-guided generation
├── support_bot.py           # Example application
├── audit_logger.py          # Audit logging
├── api_server.py            # REST API
├── requirements.txt         # Dependencies
└── audit_logs/              # Audit log storage
    └── audit_2024-01-15.jsonl
```

### requirements.txt

```
networkx>=2.6
pydantic>=1.9
numpy>=1.21
fastapi>=0.95
uvicorn>=0.21
```

---

## Summary: The Auditable AI Checklist

- [ ] **Define ontology**: Types + relations for your domain
- [ ] **Set up proof engine**: Choose STRICT/COMPOSITIONAL/REACHABILITY
- [ ] **Implement generator**: Prove-then-generate paradigm
- [ ] **Add audit logging**: Every response has a trace
- [ ] **Deploy API**: REST endpoints with proof returns
- [ ] **Monitor**: Track hallucination rates over time

---

## Key Guarantees

1. **Soundness**: Generated text is provably correct
2. **Auditability**: Every response has a derivation tree
3. **Graceful failure**: System refuses rather than hallucinates
4. **Extensibility**: Add new types/relations without code changes

---

## What's Next

- **Extend your ontology**: Add more types and relations
- **Integrate with LLMs**: Use proof constraints with GPT-4/Claude
- **Train custom models**: Ontological attention on your data
- **Scale**: Deploy on Modal for GPU training

---

*You now have a complete, auditable AI system. Every response is traceable. Every claim is provable. No more hallucinations.*

---

**← Previous**: [From Proofs to Programs to... Text?](./03_proofs_to_text.md)  
**GitHub**: [alignment_research/tlts_compilation](https://github.com/oasis-main/alignment_research/tree/main/tlts_compilation)

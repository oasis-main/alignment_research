# Why Your LLM Hallucinates (And How Category Theory Can Help)

*Toward provably-grounded language generation*

---

## The Problem Everyone Knows But Nobody Solves

You've seen it happen. You ask GPT-4 a simple question:

> "What's the relationship between a customer and their order?"

And it confidently responds:

> "A customer creates an order directly."

Sounds reasonable. But in your e-commerce system, customers don't create orders directly. They:
1. Add items to a **cart**
2. Proceed to **checkout**
3. Submit **payment**
4. *Then* an order is created

The LLM hallucinated a shortcut. It invented a relation that doesn't exist in your domain.

**This isn't a retrieval problem.** RAG won't help here—the LLM knows the words "customer" and "order," it just doesn't know what *compositions* of relations are valid in your specific domain.

---

## What's Actually Missing: Structure

LLMs are trained on text. Text is sequential. But knowledge is *structured*.

When we say "a customer creates an order," we're making a claim about the **composition of relations**:

```
Customer → ??? → Order
```

The LLM doesn't know what goes in the middle. More importantly, it doesn't know that:
- `Customer → Order` via "creates" is **invalid**
- `Customer → Cart → Checkout → Payment → Order` is **valid**

This is a **type-theoretic** problem. The LLM lacks a type system for your domain.

---

## Enter Category Theory (Don't Panic)

Category theory is the mathematics of structure and composition. At its core:

- **Objects**: Things in your domain (Customer, Order, Cart)
- **Morphisms**: Relations between things (places, contains, creates)
- **Composition**: Chaining relations (if A→B and B→C, then A→C)

The key insight: **Not all compositions are valid.**

Just because you can write "Customer creates Order" doesn't mean it's true. The composition must be *witnessed* by actual relations in your domain.

### Ologs: Categories for Knowledge

An **Olog** (Ontology Log) is a category-theoretic knowledge representation. Unlike a knowledge graph that stores *facts*, an Olog encodes *constraints* on valid compositions.

Here's our e-commerce Olog:

```
┌──────────┐  has   ┌──────┐  contains  ┌──────┐
│ Customer │───────▶│ Cart │───────────▶│ Item │
└──────────┘        └──────┘            └──────┘
                       │
                       │ proceeds_to
                       ▼
                   ┌──────────┐
                   │ Checkout │
                   └──────────┘
                       │
                       │ requires
                       ▼
                   ┌─────────┐  creates  ┌───────┐
                   │ Payment │──────────▶│ Order │
                   └─────────┘           └───────┘
```

**The rule**: You can only claim a relation A→B if there's either:
1. A direct edge A→B with that label, OR
2. A valid composition of edges where the relation appears

---

## From Verification to Prevention

The standard approach is **generate-then-verify**:

```
LLM generates → Check against knowledge base → Accept or reject
```

This is reactive. We're playing whack-a-mole with hallucinations.

Our approach is **prove-then-generate**:

```
Query → Prove what CAN be said → Generate ONLY that
```

This is proactive. Hallucinations are **impossible by construction**.

### How It Works

1. **Query**: "How does a Customer relate to Order?"

2. **Proof Search**: Find valid paths in the Olog
   ```
   Customer --has--> Cart --proceeds_to--> Checkout 
            --requires--> Payment --creates--> Order
   ✓ Valid composition found
   ```

3. **Constrained Generation**: Only emit tokens allowed by the proof
   ```
   "The customer has a cart, which proceeds to checkout, 
    requires payment, and creates an order."
   ```

4. **Verification**: Re-check (but this is redundant—we already proved it)

---

## Three Modes of Strictness

Not all applications need maximum strictness. We provide three proof modes:

### 1. STRICT Mode
> Claim "A r B" is valid iff there exists edge A→B with label r

**Use case**: High-stakes domains (medical, legal, financial)

```python
# "Customer creates Order" → INVALID
# No direct edge Customer→Order labeled "creates"
```

### 2. COMPOSITIONAL Mode  
> Claim "A r B" is valid iff relation r appears somewhere in a path A→...→B

**Use case**: Conversational summaries where exact phrasing is flexible

```python
# "Customer creates Order" → VALID
# Path exists: Customer→Cart→...→Payment→Order
# and "creates" appears in that path (Payment creates Order)
```

### 3. REACHABILITY Mode
> Claim "A r B" is valid iff any path exists from A to B

**Use case**: Exploratory/creative applications (but beware hallucinations!)

```python
# "Customer creates Order" → VALID
# Path exists, relation label ignored
# ⚠️ This mode allows hallucinations!
```

---

## Show Me The Code

Here's how to detect hallucinations in your LLM outputs:

```python
from olog_core import OlogGraph
from proof_objects import ProofEngine, ProofMode

# Define your domain ontology
olog = OlogGraph(name="ECommerce")

# Types (objects in the category)
for t in ["Customer", "Cart", "Item", "Checkout", "Payment", "Order"]:
    olog.add_type(t)

# Relations (morphisms)
olog.add_aspect("Customer", "Cart", "has")
olog.add_aspect("Cart", "Item", "contains")
olog.add_aspect("Cart", "Checkout", "proceeds_to")
olog.add_aspect("Checkout", "Payment", "requires")
olog.add_aspect("Payment", "Order", "creates")

# Create proof engine in STRICT mode
engine = ProofEngine(olog, mode=ProofMode.STRICT)

# Test claims
claims = [
    "Customer has Cart",           # ✓ Valid (direct edge)
    "Customer creates Order",      # ✗ Invalid (no such edge)
    "Payment creates Order",       # ✓ Valid (direct edge)
]

for claim in claims:
    proof = engine.prove(claim)
    status = "✓" if proof.is_valid else "✗"
    print(f"{status} {claim}")
```

Output:
```
✓ Customer has Cart
✗ Customer creates Order
✓ Payment creates Order
```

---

## Proof-Guided Generation

Once you can verify, you can generate safely:

```python
from proof_guided_generation import ProofGuidedGenerator

generator = ProofGuidedGenerator(olog)

# Ask for explanation
response = generator.generate("Customer", "Order")

print(response.text)
# "The customer has a cart, which proceeds to checkout,
#  requires payment, and creates an order."

print(f"Proof valid: {response.plan.is_valid}")
# Proof valid: True

# Try invalid path
response = generator.generate("Item", "Customer")
print(response.text)
# "Cannot generate: No path from Item to Customer"
```

**The generator refuses to hallucinate.** If no proof exists, it says so.

---

## Why This Matters

### For AI Safety
Hallucinations in medical/legal/financial contexts can cause real harm. Proof-guided generation provides formal guarantees.

### For Trust
Every generated sentence comes with a proof object—a complete derivation showing *why* it's valid. Users can audit the reasoning.

### For Debugging  
When generation fails, you know exactly why: the proof search failed. This is actionable—extend your ontology.

---

## What's Next

This blog introduced the *what* and *why*. Coming up:

1. **Blog 2**: "Attention, But Make It Type-Safe" — How to build ontological constraints into transformer attention

2. **Blog 3**: "From Proofs to Programs to... Text?" — The Curry-Howard correspondence extended to NLG

3. **Blog 4**: "Building an Auditable AI: A Complete Walkthrough" — Full tutorial from ontology to deployment

---

## Try It Yourself

```bash
git clone https://github.com/MikeHLee/ai_research
cd ai_research/topics/ontological_induction_sequence_modeling

# Install dependencies
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the demos
python proof_objects.py           # Proof engine demo
python proof_guided_generation.py # Prove-then-generate demo
```

---

## The Core Thesis

> **Proof objects are not just for verification—they are construction blueprints.**

A valid proof IS a valid generation plan. If we can prove a path exists in the ontology, we can generate text describing that path. If no proof exists, we refuse to generate.

This inverts the standard paradigm:

| Traditional | Proof-Guided |
|-------------|--------------|
| Generate → Verify → Maybe reject | Prove → Generate → Guaranteed valid |
| Reactive | Proactive |
| Probabilistic | Deterministic |
| Auditable? No | Auditable? Yes |

---

*Category theory isn't just abstract math—it's the missing type system for language generation.*

---

**Next up**: [Attention, But Make It Type-Safe →](#)

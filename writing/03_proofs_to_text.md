# From Proofs to Programs to... Text?

*Extending Curry-Howard to natural language generation*

---

## The Most Beautiful Correspondence in Computer Science

In 1958, Haskell Curry noticed something strange. In 1969, William Howard formalized it. What they discovered is arguably the deepest connection in all of computer science:

> **Proofs are programs. Programs are proofs.**

This is the **Curry-Howard correspondence**:

| Logic | Programming |
|-------|-------------|
| Proposition | Type |
| Proof | Program |
| Proof step | Function application |
| Modus ponens | Function composition |

A proof that "A implies B" is the *same thing* as a function from A to B.

---

## The Insight: Proofs Are Generation Plans

We extend Curry-Howard one step further:

| Logic | Programming | **Language Generation** |
|-------|-------------|-------------------------|
| Proposition | Type | **Claim** |
| Proof | Program | **Generation trace** |
| Proof step | Function call | **Token emission** |
| Composition | Function composition | **Sentence construction** |

A proof that "Customer relates to Order" is the *same thing* as a plan for generating text about that relationship.

---

## Traditional Generation: Hope and Pray

```
┌─────────────────────────────────────────────────┐
│           TRADITIONAL APPROACH                  │
├─────────────────────────────────────────────────┤
│                                                 │
│   Query: "How does Customer relate to Order?"   │
│                     ↓                           │
│   ┌─────────────────────────────────────────┐   │
│   │         LLM (Black Box)                 │   │
│   │   P(next_token | context)               │   │
│   │   Sample... sample... sample...         │   │
│   └─────────────────────────────────────────┘   │
│                     ↓                           │
│   Generated: "A customer creates an order"      │
│                     ↓                           │
│   ┌─────────────────────────────────────────┐   │
│   │         Verifier (Post-hoc)             │   │
│   │   Check against knowledge base...       │   │
│   │   ✗ "creates" not a valid relation      │   │
│   └─────────────────────────────────────────┘   │
│                     ↓                           │
│   Reject? Retry? Show anyway? 🤷                │
│                                                 │
└─────────────────────────────────────────────────┘
```

The problem: generation and verification are **separate**. The model can generate anything, and we hope the verifier catches mistakes.

---

## Proof-Guided Generation: Correct by Construction

```
┌─────────────────────────────────────────────────┐
│           PROOF-GUIDED APPROACH                 │
├─────────────────────────────────────────────────┤
│                                                 │
│   Query: "How does Customer relate to Order?"   │
│                     ↓                           │
│   ┌─────────────────────────────────────────┐   │
│   │         Proof Synthesizer               │   │
│   │   Search Olog for valid paths...        │   │
│   │   Found: Customer→Cart→Checkout→        │   │
│   │          Payment→Order                  │   │
│   │   ProofObject: Composition([has,        │   │
│   │     proceeds_to, requires, creates])    │   │
│   └─────────────────────────────────────────┘   │
│                     ↓                           │
│   ┌─────────────────────────────────────────┐   │
│   │         Proof-Constrained Decoder       │   │
│   │   Step 1: Emit "Customer" (source)      │   │
│   │   Step 2: Emit "has" (relation)         │   │
│   │   Step 3: Emit "Cart" (target)          │   │
│   │   ... follow proof structure ...        │   │
│   └─────────────────────────────────────────┘   │
│                     ↓                           │
│   Generated: "The customer has a cart, which    │
│   proceeds to checkout, requires payment, and   │
│   creates an order."                            │
│                     ↓                           │
│   ✓ Valid by construction (proof guarantees it) │
│                                                 │
└─────────────────────────────────────────────────┘
```

The insight: **the proof IS the generation plan**. We don't generate then verify—we prove then generate.

---

## The Proof Object as Blueprint

A proof object contains everything needed to generate correct text:

```python
@dataclass
class ProofObject:
    claim: str                    # What we're proving/generating
    status: ProofStatus           # VALID, INVALID, INCOMPLETE
    root: Optional[ProofNode]     # The derivation tree
    
@dataclass  
class ProofNode:
    step_type: ProofStep          # COMPOSITION, IDENTITY, etc.
    premise: str                  # Source type
    conclusion: str               # Target type
    morphism_path: List[str]      # Relations used
    children: List[ProofNode]     # Sub-proofs
```

### Example Proof Object

For the claim "Customer relates to Order":

```
ProofObject:
  claim: "Customer reaches Order"
  status: VALID
  root:
    ProofNode(COMPOSITION):
      premise: "Customer"
      conclusion: "Order" 
      morphism_path: ["has", "proceeds_to", "requires", "creates"]
      children:
        - ProofNode: Customer --has--> Cart
        - ProofNode: Cart --proceeds_to--> Checkout
        - ProofNode: Checkout --requires--> Payment
        - ProofNode: Payment --creates--> Order
```

This proof object tells us exactly how to construct the sentence.

---

## The Generation Algorithm

```python
def generate_from_proof(proof: ProofObject) -> str:
    """Convert proof object to natural language."""
    if not proof.is_valid:
        return f"Cannot generate: {proof.failure_reason}"
    
    # Extract path from proof
    path = extract_path(proof.root)
    
    # Generate sentence following proof structure
    sentences = []
    for i, (source, relation, target) in enumerate(path):
        if i == 0:
            sentences.append(f"The {source.lower()} {relation} a {target.lower()}")
        else:
            sentences.append(f"which {relation} a {target.lower()}")
    
    return ", ".join(sentences) + "."
```

### Key Property: Soundness

**Theorem (Soundness)**: If text T is generated via proof P against Olog O, and P is valid in O, then all claims extractable from T are valid in O.

**Proof**:
1. Generation only emits tokens allowed by P
2. P only allows types connected via Olog morphisms
3. Each emitted claim (A, r, B) corresponds to a step in P
4. Each step in P is witnessed by an edge in O
5. Therefore, all claims in T are valid in O ∎

This is the **formal guarantee** that proof-guided generation cannot hallucinate.

---

## Constrained Decoding in Practice

For neural decoders, we implement proof constraints via logit masking:

```python
class ProofConstrainedDecoder:
    def __init__(self, model, olog):
        self.model = model
        self.olog = olog
        self.proof_searcher = ProofSearcher(olog)
    
    def generate(self, query, source_type, target_type):
        # Step 1: Synthesize proof
        proof = self.proof_searcher.find_shortest_proof(
            source_type, target_type
        )
        
        if proof is None:
            return "No valid path exists."
        
        # Step 2: Generate with constraints
        path = extract_path(proof)
        generated_tokens = []
        
        for step_idx, (src, rel, tgt) in enumerate(path):
            # Get valid tokens for this step
            valid_tokens = self.get_valid_tokens(step_idx, src, rel, tgt)
            
            # Create logit mask
            logit_mask = self.create_mask(valid_tokens)
            
            # Generate constrained
            logits = self.model.get_logits(generated_tokens)
            constrained_logits = logits + logit_mask  # -inf for invalid
            
            next_token = sample(constrained_logits)
            generated_tokens.append(next_token)
        
        return self.decode(generated_tokens)
    
    def get_valid_tokens(self, step_idx, src, rel, tgt):
        """Return tokens valid at this proof step."""
        valid = set()
        
        # Type tokens
        valid.add(src)
        valid.add(tgt)
        
        # Relation tokens
        valid.add(rel)
        valid.update(self.get_relation_synonyms(rel))
        
        # Function words always valid
        valid.update(FUNCTION_WORDS)
        
        return valid
```

---

## Three Generation Strategies

### 1. LITERAL: Direct Verbalization

```
Input:  Proof path [Customer→Cart, Cart→Checkout, Checkout→Payment]
Output: "Customer has Cart → Cart proceeds_to Checkout → Checkout requires Payment"
```

Mechanical, but guaranteed correct.

### 2. NATURAL: Linguistic Fluency

```
Input:  Proof path [Customer→Cart, Cart→Checkout, Checkout→Payment]
Output: "The customer has a cart, which proceeds to checkout and requires payment."
```

More fluent, still constrained by proof structure.

### 3. TEMPLATE: Slot Filling

```
Template: "The process from {SOURCE} to {TARGET} involves: {STEPS}."
Output:   "The process from Customer to Payment involves: 
           Customer→Cart via 'has', then Cart→Checkout via 'proceeds_to', 
           then Checkout→Payment via 'requires'."
```

Explicit about the derivation.

---

## Comparison: Generate-Then-Verify vs Prove-Then-Generate

| Aspect | Generate-Then-Verify | Prove-Then-Generate |
|--------|---------------------|---------------------|
| Approach | Reactive | Proactive |
| Hallucinations | Detected post-hoc | Prevented by construction |
| Guarantees | Statistical | Formal |
| Failure mode | False negatives | Incomplete ontology |
| Auditability | Limited | Full derivation tree |
| Computational | Generate + verify | Search + generate |

---

## When Proofs Fail: Graceful Degradation

What if no proof exists?

```python
def generate_with_fallback(query, source, target):
    proof = search_proof(source, target)
    
    if proof and proof.is_valid:
        # Best case: proof-guided generation
        return generate_from_proof(proof), "proven"
    
    elif proof and proof.status == ProofStatus.INCOMPLETE:
        # Partial proof: generate what we can
        partial_text = generate_from_proof(proof)
        return f"{partial_text} [Incomplete: {proof.failure_reason}]", "partial"
    
    else:
        # No proof: acknowledge limitation
        return f"I cannot find a valid relationship between {source} and {target} in the current ontology.", "refused"
```

The system **refuses to hallucinate**. It says "I don't know" rather than making things up.

---

## The Deeper Connection: Types as Propositions

In the Curry-Howard view:
- A **type** is a **proposition**
- An **inhabitant** of the type is a **proof** of the proposition

For us:
- An **Olog type** is a **claim about an entity**
- A **token sequence** respecting the type is **evidence** for the claim

```
Type "Customer → Order":
  Proposition: "There exists a valid path from Customer to Order"
  
Inhabitants:
  - "Customer has Cart, Cart proceeds_to Checkout, ..."  (proof 1)
  - "Customer has Cart, Cart contains Item, ..."         (proof 2, if valid)
  
Non-inhabitants:
  - "Customer creates Order"  (no proof exists)
```

The proof search is **type-checking** for natural language.

---

## Implementation: Proof Synthesis

```python
class ProofSearcher:
    def __init__(self, olog):
        self.olog = olog
        self.reachability = self.compute_reachability()
    
    def find_all_proofs(self, source, target, max_depth=5):
        """BFS for all valid paths."""
        if target not in self.reachability.get(source, set()):
            return []  # Not reachable
        
        proofs = []
        queue = [(source, [])]  # (current_node, path_so_far)
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            if current == target and path:
                # Found valid path → create proof
                proof = self.path_to_proof(source, target, path)
                proofs.append(proof)
                continue
            
            # Explore neighbors
            for neighbor, relation in self.olog.get_edges(current):
                queue.append((neighbor, path + [(current, relation, neighbor)]))
        
        return proofs
    
    def path_to_proof(self, source, target, path):
        """Convert path to proof object."""
        # Build proof tree (from leaf to root)
        root = None
        for src, rel, tgt in reversed(path):
            node = ProofNode(
                step_type=ProofStep.COMPOSITION,
                premise=src,
                conclusion=tgt,
                morphism_path=[rel],
                children=[root] if root else [],
            )
            root = node
        
        return ProofObject(
            claim=f"{source} reaches {target}",
            status=ProofStatus.VALID,
            root=root,
        )
```

---

## The Soundness Theorem (Formal)

**Theorem**: Let O be an Olog, P a proof object valid in O, and T the text generated from P via proof-guided generation. Then:

∀ claim c ∈ extract_claims(T): verify(c, O) = VALID

**Proof**:

Let c = (A, r, B) be any claim extractable from T.

1. By construction of proof-guided generation, c corresponds to some step s in P.

2. Step s asserts: "There exists morphism r: A → B in O" (for STRICT mode) or "r appears in a valid composition A → ... → B" (for COMPOSITIONAL mode).

3. Since P is valid in O, step s is witnessed by the Olog structure.

4. Therefore, verify(c, O) = VALID.

By induction over all claims in T, the theorem holds. ∎

---

## Key Takeaways

1. **Curry-Howard extends to NLG**: Proofs ↔ Programs ↔ Generation traces

2. **Proof objects are blueprints**: They specify exactly what can be said

3. **Synthesis before generation**: We prove first, then generate from the proof

4. **Formal guarantees**: Soundness theorem ensures no hallucinations

5. **Graceful degradation**: System refuses rather than fabricates

---

## What's Next

**Blog 4**: "Building an Auditable AI: A Complete Walkthrough" — Full tutorial from ontology definition to deployed system with proof traces.

---

## Try It

```bash
cd ai_research/topics/ontological_induction_sequence_modeling
source venv/bin/activate

# See proof-guided generation in action
python proof_guided_generation.py

# Output shows:
# 1. Proof synthesis
# 2. Path extraction
# 3. Constrained generation
# 4. Verification (redundant but reassuring)
```

---

*The oldest idea in logic—that proofs witness truth—turns out to be the key to honest AI.*

---

**← Previous**: [Attention, But Make It Type-Safe](./02_type_safe_attention.md)  
**Next →**: [Building an Auditable AI: A Complete Walkthrough](#)

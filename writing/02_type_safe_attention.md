# Attention, But Make It Type-Safe

*Constraining transformers with categorical reachability*

---

## The Attention Problem

Self-attention is powerful because it lets every token attend to every other token. But this power is also its weakness.

Consider this input:
```
"The customer placed an order for the product"
```

In standard attention, "product" can attend to "customer" with equal ease as it attends to "order." The model learns *statistical* associations, not *structural* constraints.

But in many domains, not all associations are valid:
- A **product** doesn't directly relate to a **customer**
- A **customer** relates to an **order**, which contains **products**

Standard attention doesn't know this. It treats all token pairs equally.

---

## The Solution: Type-Constrained Attention

What if we could tell the attention mechanism: "Token A can only attend to Token B if there's a valid path from A's type to B's type"?

This is **ontological attention**.

### The Core Idea

```
Standard Attention:
  Attention(Q, K, V) = softmax(QK^T / √d) V
  
Ontological Attention:
  Attention(Q, K, V) = softmax((QK^T / √d) + M) V
  
  where M[i,j] = 0    if type(i) can reach type(j)
                 -∞   otherwise
```

The mask `M` is derived from the ontology's **reachability relation**.

---

## Building the Reachability Matrix

Given an Olog (the categorical knowledge-representation formalism of [Spivak and Kent, 2012](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0024274)), we compute which types can "reach" which other types via directed paths:

```python
def compute_reachability(olog):
    """Compute transitive closure of type relations."""
    reachable = {}
    
    for source_type in olog.graph.nodes:
        # BFS from source
        visited = set()
        queue = [source_type]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # Add all neighbors
            for neighbor in olog.graph.neighbors(current):
                queue.append(neighbor)
        
        reachable[source_type] = visited
    
    return reachable
```

For our e-commerce Olog:

```
Customer → {Cart, Item, Checkout, Payment, Order, Delivery}
Cart     → {Item, Checkout, Payment, Order, Delivery}
Item     → {}  (leaf node)
Checkout → {Payment, Order, Delivery}
Payment  → {Order, Delivery}
Order    → {Delivery}
Delivery → {}  (or cycles back to Customer)
```

---

## The Attention Mask

Given a sequence of typed tokens, we build the attention mask:

```python
def create_attention_mask(tokens, reachability):
    """Create mask where M[i,j] = 1 iff type(i) can reach type(j)."""
    n = len(tokens)
    mask = np.zeros((n, n))
    
    for i, token_i in enumerate(tokens):
        for j, token_j in enumerate(tokens):
            type_i = token_i.olog_type
            type_j = token_j.olog_type
            
            # Self-attention always allowed
            if i == j:
                mask[i, j] = 1
                continue
            
            # Untyped tokens can attend to anything
            if type_i is None or type_j is None:
                mask[i, j] = 1
                continue
            
            # Check reachability
            if type_j in reachability.get(type_i, set()):
                mask[i, j] = 1
            # else: mask[i, j] stays 0 (will become -inf)
    
    return mask
```

### Visualization

For the sequence: `["customer", "places", "order", "containing", "product"]`

With types: `[Customer, None, Order, None, Product]`

The mask looks like:

```
           customer  places  order  containing  product
customer      1        1       1        1          1      ← Customer reaches all
places        1        1       1        1          1      ← Untyped: reaches all
order         0        1       1        1          1      ← Order can't reach Customer
containing    1        1       1        1          1      ← Untyped: reaches all
product       0        1       0        1          1      ← Product can't reach Customer/Order
```

When this mask is applied (with -∞ for 0s), "product" **cannot attend to "customer"** during self-attention.

---

## Typed Tokens

To use ontological attention, we need to know each token's type:

```python
@dataclass
class TypedToken:
    """A token with optional ontological type annotation."""
    text: str
    position: int
    olog_type: Optional[str] = None  # e.g., "Customer", "Order"
    is_relation: bool = False        # True for relation words like "places"
    relation_label: Optional[str] = None
```

Type assignment can be done via:
1. **Exact match**: "customer" → Customer
2. **NER**: Named entity recognition
3. **Learned**: Train a type classifier

```python
def assign_types(tokens, olog):
    """Assign Olog types to tokens."""
    typed_tokens = []
    type_names_lower = {t.lower(): t for t in olog.graph.nodes}
    
    for i, token in enumerate(tokens):
        olog_type = type_names_lower.get(token.lower())
        typed_tokens.append(TypedToken(
            text=token,
            position=i,
            olog_type=olog_type,
        ))
    
    return typed_tokens
```

---

## Relation-Aware Embeddings

Beyond just typing tokens, we can embed relations categorically.

In category theory, a morphism `f: A → B` is characterized by:
- Its **domain** (source type A)
- Its **codomain** (target type B)
- Its **label** (the relation name)

We embed all three:

```python
class RelationAwareEmbedding:
    def __init__(self, olog, embed_dim=64):
        self.type_embeddings = nn.Embedding(len(olog.graph.nodes), embed_dim)
        self.relation_embeddings = nn.Embedding(len(olog.relations), embed_dim)
        self.compose = nn.Linear(embed_dim * 3, embed_dim)
    
    def embed_relation(self, source, relation, target):
        """Embed (source, relation, target) triple."""
        src_emb = self.type_embeddings(source)
        rel_emb = self.relation_embeddings(relation)
        tgt_emb = self.type_embeddings(target)
        
        # Compose into single embedding
        combined = torch.cat([src_emb, rel_emb, tgt_emb], dim=-1)
        return self.compose(combined)
```

### Compositional Embeddings

The magic of category theory: morphisms compose!

If we have `f: A → B` and `g: B → C`, then `g ∘ f: A → C`.

We can mirror this in embedding space:

```python
def compose_relations(self, path):
    """Compose a sequence of (src, rel, tgt) triples."""
    if not path:
        return self.identity_embedding
    
    # Start with first edge
    result = self.embed_relation(*path[0])
    
    # Compose remaining edges
    for edge in path[1:]:
        edge_emb = self.embed_relation(*edge)
        result = self.composition_layer(torch.cat([result, edge_emb], dim=-1))
    
    return result
```

This gives us embeddings that respect categorical composition—the embedding of a composed path relates meaningfully to its constituent edges.

---

## Full Ontological Attention Layer

Putting it all together:

```python
class OntologicalAttention(nn.Module):
    def __init__(self, olog, embed_dim, num_heads=4):
        super().__init__()
        self.olog = olog
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        
        # Standard attention components
        self.W_q = nn.Linear(embed_dim, embed_dim)
        self.W_k = nn.Linear(embed_dim, embed_dim)
        self.W_v = nn.Linear(embed_dim, embed_dim)
        self.W_o = nn.Linear(embed_dim, embed_dim)
        
        # Precompute reachability
        self._reachability = self._compute_reachability()
    
    def forward(self, x, typed_tokens):
        """
        x: (batch, seq_len, embed_dim)
        typed_tokens: list of TypedToken
        """
        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)
        
        # Compute attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.embed_dim)
        
        # Apply ontological mask
        mask = self._create_mask(typed_tokens)
        mask = torch.tensor(mask, device=x.device)
        
        # Set blocked positions to -inf
        scores = scores.masked_fill(mask == 0, float('-inf'))
        
        # Softmax and apply to values
        attn_weights = F.softmax(scores, dim=-1)
        output = torch.matmul(attn_weights, V)
        
        return self.W_o(output), attn_weights
    
    def _create_mask(self, typed_tokens):
        """Create reachability-based attention mask."""
        n = len(typed_tokens)
        mask = np.ones((n, n))  # Default: allow
        
        for i, tok_i in enumerate(typed_tokens):
            for j, tok_j in enumerate(typed_tokens):
                if tok_i.olog_type and tok_j.olog_type:
                    if tok_j.olog_type not in self._reachability.get(tok_i.olog_type, set()):
                        if i != j:  # Don't block self-attention
                            mask[i, j] = 0
        
        return mask
```

---

## Training with Ontological Constraints

Two training approaches:

### 1. Hard Constraints (Inference Only)

Train a standard transformer, apply ontological mask only at inference:

```python
# Training: standard attention
model.train()
output = model(x)  # No mask

# Inference: ontological attention
model.eval()
output = model(x, typed_tokens=tokens, use_ontological_mask=True)
```

**Pros**: No architectural changes to training
**Cons**: Model may learn patterns that get blocked at inference

### 2. Soft Constraints (Training + Inference)

Include ontological mask during training:

```python
# Training with mask
model.train()
output = model(x, typed_tokens=tokens, use_ontological_mask=True)
loss = criterion(output, target) + lambda * ontological_violation_penalty(attn_weights, mask)
```

**Pros**: Model learns to work within constraints
**Cons**: Requires typed tokens during training

---

## Results: Attention Pattern Comparison

### Standard Attention
```
customer  order  product
   ↓        ↓       ↓
   ●--------●-------●    (all attend to all)
   ●--------●-------●
   ●--------●-------●
```

### Ontological Attention
```
customer  order  product
   ↓        ↓       ↓
   ●------->●------>●    (customer → order → product)
   ○<-------●------>●    (order can't attend back to customer)
   ○<-------○-------●    (product can't attend back)
```

The ontological attention **respects the direction of relations**.

---

## Hallucination Reduction — What the Numbers Actually Show

"Hallucination" in the type-safe-generation setting has a precise
meaning: producing a token sequence whose corresponding (state, label,
state) triples are not in the domain's transition relation δ. A
generation that respects δ everywhere is **sound**; one that breaks δ
anywhere is unsound.

Our synthetic-prior harness ([`experiment_loci_comparison.py`](../papers/nesy_submission/supplementary/experiment_loci_comparison.py),
N=1000 trajectories on a 7-type e-commerce Olog, run 2026-05-05) gives
the soundness rate by enforcement locus and prior quality:

| Enforcement                                         | GOOD prior | BAD prior |
|-----------------------------------------------------|-----------:|----------:|
| (A) None — standard sampling from prior             |    48.1%   |    4.2%   |
| (B′) Attention-layer reachability masking only      |    61.5%   |    4.3%   |
| (C) FFN-hybrid (deterministic where δ is functional)|   100.0%   |  100.0%   |
| (D) Pre-decoder logit masking                       |   100.0%   |  100.0%   |

Three things to take from this:

1. **Without architectural enforcement, soundness tracks prior
   alignment.** A model whose prior happens to concentrate mass on
   admissible labels lucks into ~48% sound trajectories; a misaligned
   prior crashes to ~4%. The "behavior is mostly fine if the model is
   good" intuition is exactly as fragile as it sounds.
2. **Attention masking alone is not enough.** Variant (B′) — admit
   any label whose target type is reachable from the current state —
   barely improves over (A) under the BAD prior. Reachability admits
   the *destination*; it does not require the *path step* to exist as
   a δ-edge. The model can sample a label whose target is reachable
   but whose direct edge is missing.
3. **(C) and (D) are sound by construction.** Under both prior
   regimes. The remaining engineering question is the fluency cost,
   discussed at length in our [NeSy 2026 paper](../papers/nesy_submission/main.pdf)
   §5 — TL;DR: ~5.5 nats/trajectory of log-likelihood is the price of
   soundness when the prior is badly misaligned, and ~0 when the
   prior already concentrates on admissible labels.

These are synthetic-prior numbers, not trained-model numbers. Real
LLM hallucination-rate measurement against an end-to-end TLTS pipeline
is the next experiment. For external evidence that this regime
generalizes to learned distributions, [Willard and Louf (2023, Outlines)](https://arxiv.org/abs/2307.09702)
report near-100% structural validity from grammar-constrained
decoding across model sizes — the (D) locus applied to JSON/regex
schemas rather than δ-edges, but the same architectural mechanism.

It's worth pausing on what these numbers replace. Recent work characterizing how current LMs actually do binding ([Gur-Arieh, Geva, and Geiger 2025](https://arxiv.org/abs/2510.06182)) finds three mechanisms operating in parallel — *positional*, *lexical*, and *reflexive* — that degrade with context length and disagree with each other in the middle of longer inputs. Our ontological mask doesn't merely *improve* one of these mechanisms; it replaces the heterogeneous fallback chain with one structurally-derived mask whose admissibility is determined by the Olog, not by which subsystem happened to win. That's the architectural shift, not the percentage points in the table above.

---

## Code Walkthrough

Full implementation in `ontological_attention.py`:

```python
from ontological_attention import OntologicalAttention, TypedToken
from olog_core import OlogGraph

# Create ontology
olog = OlogGraph(name="ECommerce")
olog.add_type("Customer")
olog.add_type("Order")
olog.add_type("Product")
olog.add_aspect("Customer", "Order", "places")
olog.add_aspect("Order", "Product", "contains")

# Create attention layer
attn = OntologicalAttention(olog, embed_dim=64)

# Create typed tokens
tokens = [
    TypedToken("customer", 0, olog_type="Customer"),
    TypedToken("places", 1, is_relation=True),
    TypedToken("order", 2, olog_type="Order"),
]

# Forward pass
output, weights = attn.forward(tokens, return_attention=True)

# Inspect attention weights
print(weights)
# Note: weights[2, 0] will be ~0 (Order can't attend to Customer)
```

---

## Key Takeaways

1. **Standard attention treats all token pairs equally**—but domain knowledge says some pairs are invalid

2. **Ontological attention uses reachability** from category theory to constrain which tokens can attend to which

3. **The mask is derived from the Olog**, not learned—it's a hard structural constraint

4. **Relation-aware embeddings** capture the categorical structure of morphisms

5. **Combined with proof-guided generation**, this dramatically reduces hallucinations

---

## What's Next

**Blog 3**: "From Proofs to Programs to... Text?" — We extend the Curry-Howard correspondence to show that proofs ARE generation plans.

**Blog 4**: "Building an Auditable AI: A Complete Walkthrough" — Full tutorial from ontology definition to deployed system.

---

## Try It

```bash
cd ai_research/topics/structure_of_clear_thinking
source venv/bin/activate

# Run the attention demo
python ontological_attention.py

# See attention weights blocked by ontological constraints
```

---

*Type safety isn't just for compilers—it's for attention mechanisms too.*

---

**← Previous**: [Why Your LLM Hallucinates](./01_why_llms_hallucinate.md)  
**Next →**: [From Proofs to Programs to... Text?](#)

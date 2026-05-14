# EquipmentIQ — Industrial Predictive Maintenance RAG

**Production multi-agent RAG system for CNC machinery predictive maintenance** — grounded in 1,702 real vibration recordings from the Bosch CNC Machining Dataset (CC-BY-4.0).

⚠️ **Not a chatbot, a LangChain demo, or an API wrapper.** Production-grade engineering with structured LLM runtimes, eval gates, and typed state machines.

---

## 1. Structured LLM Runtimes — Typed Outputs, Schemas, Validators, Retries, Evals

Every LLM boundary uses **Pydantic models** with `Literal` types and `Field` bounds. No stringly-typed outputs.

### Intent Classifier (Core Routing Gate)
```python
class IntentClassification(BaseModel):
    domain: Literal["mechanical", "software", "support", "cross_domain"] 
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    
    @classmethod
    def safeparse(cls, text: str) -> "IntentClassification":
        """Falls back to cross_domain default on malformed JSON."""
        try:
            obj = json.loads(text)
            return cls(**obj)
        except:
            return cls(domain="cross_domain", confidence=0.0, reasoning="parse_failed")
```

**Why this matters:** A malformed LLM response (missing confidence field, domain typo, etc.) no longer crashes the pipeline. The system **never halts on bad LLM output** — it falls back to safe cross-domain parallel retrieval.

### CI Gate — Deployment Blocker
```python
if results["retrieval"]["ndcg"] < 0.70:
    print("FAIL: NDCG gate FAILED -- deployment blocked")
    sys.exit(1)  # CD pipeline stops here
if results["generation"]["faithfulness"] < 0.80:
    sys.exit(1)
```

**Acceptance criteria:**
- **NDCG@5 ≥ 0.70** per agent (ranking quality of top-5 retrieved documents)
- **Hit@5 ≥ 0.85** (fraction of queries with relevant doc in top-5)
- **RAGAS Faithfulness ≥ 0.80** (factual grounding on 50-query sample)
- **Intent routing ≥ 95%** on 40 labelled test queries
- **P95 latency ≤ 10s** single-agent, **≤ 20s** cross-domain

---

## 2. Agent Runtime Architecture, Planning Systems, Reasoning Workflows

### LangGraph StateGraph — 8-Node Orchestrator

**Shared state** (TypedDict `AgentState`):
```python
class AgentState(TypedDict):
    query: str
    domain: str                    # mechanical | software | support | cross_domain
    confidence: float              # 0.0–1.0 classifier output
    agent_results: list[AgentResult]  # per-domain retrieval + citations
    merged_context: str            # combined evidence from all agents
    final_answer: str              # synthesis output
    citations: list[dict]          # source_document + chunk_id pairs
    eval_scores: dict              # faithfulness, judge, routing accuracy
    feedback: Optional[dict]       # user rating + optional comment
    node_latency: dict             # timing per node for bottleneck analysis
```

### Pipeline (8 Nodes)
1. **classify_intent** → IntentClassification (confidence threshold: 0.80)
2. **conditional_edge** → route to single_agent or parallel_node
3. **mechanical_node** / **software_node** / **support_node** → parallel retrieval
4. **parallel_node** → asyncio.gather() on all three agents
5. **merge_context** → combine retrieved chunks, deduplicate, rerank
6. **synthesise** → LLM generates final answer with citations
7. **log_trace** → LangSmith tracing (node latencies, token counts, routing decision)
8. **END**

**Why LangGraph, not a simple function chain?**
- Explicit node boundaries for latency instrumentation
- Conditional branching without callback hell
- Built-in streaming support for real-time UI updates
- Easy to inject observability at each node

### Two-Layer Planner

**Fast path (rule-based, <1ms):** ~75% of queries routed deterministically
- Is it an error code query? → software agent
- Is it a bearing/spindle/tool query? → mechanical agent
- Is it a machine ID + symptom? → support agent

**Deliberative path (LLM classifier, ~3s):** Ambiguous multi-domain queries
- "M01 spindle is vibrating and I see an alarm — what bearing specification defines the failure threshold and which error code corresponds to that threshold being exceeded?"
- Routed to `cross_domain` → parallel retrieval from all three agents
- Merge evidence → synthesise unified answer

### Three Reasoning Workflows

1. **Single-Agent** (confidence ≥ 0.80):
   - Query → classifier → mechanical_node → synthesis → answer
   - Latency: ~2–4s (retrieval + reranking + LLM)

2. **Parallel Cross-Domain** (confidence < 0.80 OR explicit cross_domain):
   - Query → classifier → parallel_node (all 3 agents concurrently via asyncio.gather)
   - Merge top-5 from each, deduplicate, rerank globally
   - Synthesis with integrated evidence
   - Latency: ~8–12s (parallel I/O + merge + LLM)

3. **Exact Metadata Lookup** (SoftwareAgent specialisation):
   - Pattern match error codes: `[A-Z]{3}-[A-Z]{2}-\d{3}` → metadata filter first
   - Merge exact match at top of semantic results
   - Prevents "SPN-MJ-004 vs SPN-MJ-003" ambiguity

**Why metadata filter matters:** Semantic embeddings alone fail on identifier queries. The embedding distance between SPN-MJ-004 and SPN-MJ-003 may be small (both MJ subsystem errors), but they are semantically different failure modes. Pure semantic ranking can invert them.

---

## 3. Knowledge Graphs, Causal Graphs, State Machines, Probabilistic Reasoning

### ISO 10816-3 Vibration Zone Classification (Formal State Machine)

```
                   Alarm Threshold (Z ≥ 11.2 mm/s RMS)
                                    ↓
                          ┌─────────────────┐
                          │   CRITICAL (D)  │ ← entry_action: activate_failsafe()
                          └─────────────────┘
                                    ↑
                          Zone C/D boundary
                                    ↑
                          ┌─────────────────┐
                          │  UNACCEPTABLE   │
                          │    (C)          │ ← can_operate: 30 minutes max
                          └─────────────────┘
                                    ↑
                          Zone B/C boundary
                                    ↑
                          ┌─────────────────┐
                          │   JUST ACCEPTABLE│
                          │    (B)          │ ← can_operate: unlimited
                          └─────────────────┘
                                    ↑
                          Zone A/B boundary
                                    ↑
                          ┌─────────────────┐
                          │    GOOD (A)     │ ← standard operation
                          └─────────────────┘
```

**Transition logic:**
- Entry into zone B: trigger "elevated vibration alert", inspect spindle bearing
- Entry into zone C: trigger "diagnostic run", recommend bearing replacement within 7 days
- Entry into zone D: trigger failsafe shutdown, activate emergency cooling

### Causal Chains (Error Code Documents)

Each error code document encodes causal relationships:
```json
{
  "error_code": "SPN-CR-001",
  "subsystem": "SPN",
  "severity": "CRITICAL",
  "probable_cause": "Spindle bearing radial clearance exceeded. Bearing wear is progressive...",
  "related_codes": ["SPN-MJ-002", "SPN-SR-003"],
  "progression": {
    "stage_1": "SPN-SR-003 (slight imbalance, >2mm/s)",
    "stage_2": "SPN-MJ-002 (race defect emerging, >7mm/s)",
    "stage_3": "SPN-CR-001 (catastrophic bearing failure, >11mm/s)"
  }
}
```

**Causal ordering:** SPN-SR-003 → SPN-MJ-002 → SPN-CR-001 encodes the bearing failure progression. System uses this to answer: *"I just got SPN-MJ-002. What does this mean? Will it progress to SPN-CR-001?"*

### Probabilistic Vibration Severity Score

32 sensor features → manually constructed composite score:
```
vibration_severity = (
    0.40 * (acceleration_x_rms / threshold_x) +
    0.40 * (acceleration_y_rms / threshold_y) +
    0.15 * (velocity_z_rms / threshold_z) +
    0.05 * (envelope_energy / threshold_env)
)
```

**Why manual, not ML?** Explainability + regulatory traceability. Every coefficient is justified in [DOC-EIQ-003] (bearing design spec).

---

## 4. Evidence-Bound Generation — Final Claims Must Trace Back to Supporting Data

### Hard Rules in Synthesis Prompt

1. **Cite every claim:** `[SOURCE: SPN-CR-001__0000]`
2. **Never invent numbers:** No parametric knowledge (e.g., "bearing life typically 10,000 hours")
3. **Return INSUFFICIENT_CONTEXT if evidence is absent:** Don't speculate
4. **Never use parametric knowledge:** Only ground in retrieved chunks
5. **Similarity floor gates evidence:** cosine ≥ 0.15 before LLM can cite

### Similarity Floor (0.15 Threshold)

**Why 0.15?** Empirically tuned on golden set. Documents with cosine < 0.15 are > 85% off-topic.

**Flow:**
```python
# After retrieval + reranking
results = rerank(retrieved_chunks)  # top-5 by cross-encoder score

# Filter by similarity
evidence = [r for r in results if r.similarity_score >= 0.15]

if not evidence:
    return "INSUFFICIENT_CONTEXT"

# Only these chunks reach synthesis prompt
```

### Faithfulness Evaluation (RAGAS + LLM-as-Judge)

On 12% of sampled traffic:
```python
def evaluate_faithfulness(answer: str, context: str) -> float:
    try:
        # First: RAGAS Faithfulness (sentence-level entailment)
        ragas_score = ragas_evaluate(answer, context)
        return ragas_score
    except:
        # Fallback: Claude Haiku LLM-as-Judge
        judge_prompt = f"""
        Context: {context}
        Generated answer: {answer}
        
        Is every claim in the answer supported by the context?
        Rate: 0.0 (hallucinated) to 1.0 (fully grounded)
        """
        result = claude.messages.create(model="claude-haiku-4-5", ...)
        score = json.loads(result.content[0].text)["score"]
        return score
```

---

## 5. Eval/Replay Framework for Measuring Reasoning Quality Over Time

### Golden Set (37 Queries, Real Data)

```jsonl
{"query": "What is the probable cause of error SPN-CR-001?", "agent": "software", "expected_doc_ids": ["SPN-CR-001__0000"]}
{"query": "Describe the ISO 10816-3 vibration zones for spindle bearings.", "agent": "mechanical", "expected_doc_ids": ["DOC-EIQ-001__0003", "DOC-EIQ-001__0004"]}
{"query": "M01 spindle is vibrating and I see an alarm on the controller.", "agent": "cross_domain", "expected_doc_ids": ["SPN-MJ-002__0000", "DOC-EIQ-001__0002", "CMP-2021-1022__0000"]}
```

### Batch Evaluation Pipeline

**1. Retrieval Metrics**
```python
for query, expected_docs in golden_set:
    result = run_query(query)
    retrieved_ids = [r.chunk_id for r in result.agent_results]
    
    ndcg = compute_ndcg(retrieved_ids, expected_docs)  # DCG@k / IDCG@k
    hit = 1.0 if any(doc in retrieved_ids for doc in expected_docs) else 0.0
    mrr = 1.0 / (retrieved_ids.index(expected_docs[0]) + 1)  # reciprocal rank
```

- **NDCG@5:** Ranking quality (0.0–1.0)
- **Hit@5:** Is the relevant doc in top-5? (0.0 or 1.0)
- **MRR:** Mean reciprocal rank of first relevant doc

**2. Generation Metrics**
```python
for query, expected_docs in sample(golden_set, k=0.12):
    answer = run_query(query).final_answer
    context = retrieved_chunks  # evidence used
    
    faithfulness = evaluate_faithfulness(answer, context)  # RAGAS or LLM-Judge
    judge_score = llm_judge(answer, context)  # 4-dimension rubric (1–5 scale)
```

- **Faithfulness:** Factual grounding (0.0–1.0)
- **Judge Score:** 4 dimensions (accuracy, completeness, uncertainty handling, citation quality)

**3. Drift Detection**
```python
baseline_centroid = load_baseline("mechanical_collection")
current_centroid = compute_centroid(mechanical_collection)
drift = cosine_distance(baseline_centroid, current_centroid)

if drift > 0.15:
    alert("Embedding drift detected! Collections may be stale.")
```

**4. CI Gate (Exit Code 1 Blocks Deployment)**
```python
if results["retrieval"]["ndcg"] < 0.70 or results["generation"]["faithfulness"] < 0.80:
    sys.exit(1)  # CD pipeline halts
```

### LangSmith Tracing

Every query logged with:
- **Query text** and **final_answer**
- **Domain** and **confidence** (routing decision)
- **Chunk IDs** retrieved + **similarity scores**
- **Citation count** in final answer
- **Node latencies:** classify_intent, agent_node, merge, synthesise
- **Token counts:** prompt + completion per LLM call

---

## 6. Embedding Systems and Custom Model Pipelines

### Bi-Encoder + Cross-Encoder Stack

**Bi-Encoder Retrieval (text-embedding-3-small, 1536-dim, cosine distance)**
- Fast semantic search: ~10ms per query over 308 documents
- Returns top-8 candidates by cosine similarity

**Cross-Encoder Reranking (ms-marco-MiniLM-L-6-v2)**
- Fine-grained relevance scoring of top-8: ~30ms
- Re-orders by predicted query-document relevance (0.0–1.0 logits)
- Final top-5 returned to synthesis

### Module-Level Singleton (Avoids Cold Loads)

```python
# models.py (singleton, cached at module load)
_crossencoder = None

def get_crossencoder():
    global _crossencoder
    if _crossencoder is None:
        _crossencoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _crossencoder
```

**Why?** Streamlit reruns the entire script on every interaction. Without the singleton, CrossEncoder reloads every interaction (~4–5 seconds of wasted latency). With it: load once on first interaction, reuse forever in the same session.

### The Embedding Dimension Bug (Production Lesson)

**The Bug:** Dimension mismatch (384-dim embeddings vs 1536-dim index). Retrieval silently returned 0 results.

**Why it wasn't caught by answer inspection:** Synthesis fallback triggered → generated plausible-sounding (but hallucinated) answer.

**How it was caught:** Evaluation pipeline showed Hit@5 = 0.0 across 37 golden queries. Root cause: embedding search returned empty.

**Lesson:** Never rely on "looking at answers" to catch silent failures. Numerical eval gates (NDCG, Hit@k) catch what inspection misses.

---

## 7. Production-Grade Python

### Testing (91 Unit Tests, 12 Integration Tests, <60s Runtime)

```bash
pytest tests/ -v --tb=short
# 103 tests in ~45 seconds (mocked APIs)
# 12 integration tests: real ChromaDB + OpenAI/Anthropic APIs (skipped in CI if no keys)
```

**Test Organization:**
- `tests/test_config.py` (3 tests): YAML loading, validation, type coercion
- `tests/test_ingestion.py` (27 tests): chunking, embeddings, PII masking, collection isolation
- `tests/test_agents.py` (18 tests): retrieval filtering, metadata lookup, result schema
- `tests/test_orchestrator.py` (27 tests): routing, state transitions, latency tracking
- `tests/test_evaluation.py` (16 tests): NDCG, Hit@k, faithfulness, drift detection
- `tests/test_feedback.py` (7 tests): SQLite persistence, signal extraction, correlation
- `tests/test_ui.py` (5 tests): Streamlit session state, button interactions

### Singleton Config Loader (Startup Validation)

```python
# ingestion/config.py
class ConfigLoader:
    _instance = None
    _config = None
    
    @classmethod
    def load(cls):
        if cls._config is None:
            with open("config.yaml") as f:
                raw = yaml.safe_load(f)
            
            # Validate schema
            cls._config = {
                "chunk_size": int(raw["ingestion"]["chunk_size"]),
                "top_k": int(raw["retrieval"]["top_k_final"]),
                "ndcg_threshold": float(raw["evaluation"]["ndcg_threshold"]),
            }
        return cls._config

# Usage (everywhere in codebase)
config = ConfigLoader.load()
```

**Why singleton + startup validation?** Prevents config errors from being discovered mid-request. Fails fast at app startup, not during evaluation.

### Abstract BaseAgent (Enforcing Substitutability)

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def retrieve(self, query: str, where_filter: dict = None) -> RetrievalResult:
        """Retrieve and cite documents for query."""
        pass
    
    @abstractmethod
    def filter(self, results: list, where_filter: dict) -> list:
        """Filter results by domain-specific metadata."""
        pass

class MechanicalAgent(BaseAgent):
    def retrieve(self, query: str, subsystem: str = None) -> RetrievalResult:
        # Mechanical-specific logic
        pass
    
    def filter(self, results: list, subsystem: str = None) -> list:
        # Filter by subsystem (SPN, AXS, TCS, etc.)
        pass

class SoftwareAgent(BaseAgent):
    def retrieve(self, query: str, severity_level: str = None) -> RetrievalResult:
        # Software-specific logic (error code metadata lookup)
        pass
    
    def filter(self, results: list, severity_level: str = None) -> list:
        # Filter by severity or error code pattern
        pass
```

**Why ABC?** Enforces that new agents implement required interface. Prevents "forgot to implement filter()" bugs.

### None vs 0.0 Distinction

```python
# BAD: Loses info about missing vs zero metrics
metrics = {"ndcg": 0.0 if ndcg is None else ndcg}

# GOOD: Preserves semantic difference
metrics = {
    "ndcg": ndcg,  # None = metric not computed, 0.0 = computed but zero result
}

# During aggregation
ndcg_values = [m["ndcg"] for m in metrics_list if m["ndcg"] is not None]
avg_ndcg = sum(ndcg_values) / len(ndcg_values)
```

**Why?** If you average `[0.0, 0.0, None]` after coercing `None → 0.0`, you get `0.0`. But if the third query never ran, the average is invalid. Keeping `None` explicit prevents silent aggregation errors.

---

## Key Files

| File | Purpose |
|------|---------|
| `orchestrator/graph.py` | LangGraph StateGraph (8 nodes) |
| `agents/base_agent.py` | Abstract retrieval interface |
| `agents/{mechanical,software,support}_agent.py` | Domain-specific retrieval + filtering |
| `evaluation/batch_eval.py` | NDCG@5, Hit@5, faithfulness, drift |
| `evaluation/generation_metrics.py` | RAGAS + LLM-as-Judge scoring |
| `feedback/feedback_store.py` | SQLite persistence + signal extraction |
| `ui/app.py` | Streamlit query interface |
| `ui/eval_dashboard.py` | Metrics dashboard + evaluation controls |
| `config.yaml` | All tunable parameters (chunk_size, thresholds, etc.) |

---

## Hard Rules (Do Not Violate)

1. **No cross-collection reads outside CROSS_DOMAIN orchestrator node** (DR-005)
2. **All LLM prompts externalized to `prompts/*.txt`** (NFR-MAINT-002)
3. **No PII in LangSmith traces** — mask names, phones, emails (NFR-SEC-002)
4. **No API keys in source/logs/UI** — read from `.env` (NFR-SEC-001)
5. **No hallucinated part numbers** — return "not available" if not in context (FR-MECH-004)
6. **Diagnostic steps as numbered procedures**, never narrative (FR-SOFT-005)
7. **Every claim cited with [SOURCE: doc chunk_id]** or admit INSUFFICIENT_CONTEXT (FR-ORCH-006)
8. **Trust internal data; validate only at boundaries** (no defensive fallbacks for guaranteed shapes)

---

## Acceptance Gates (Production Deploy Blockers)

- **AC-001:** NDCG@5 ≥ 0.70 per agent on 90-query golden set
- **AC-002:** Hit@5 ≥ 0.85 per agent
- **AC-003:** RAGAS Faithfulness ≥ 0.80 on 50-query sample
- **AC-004:** Intent routing ≥ 95% on 40 labelled test queries
- **AC-008:** P95 latency ≤ 10s (single-agent), ≤ 20s (cross-domain)

---

## How This Maps to RAG Principles

| Principle | EquipmentIQ Implementation |
|-----------|---------------------------|
| **Structured LLM runtimes** | Pydantic models + safeparse fallback on every LLM boundary |
| **Agent architectures** | LangGraph 8-node StateGraph with typed AgentState |
| **Knowledge graphs** | ISO 10816-3 state machine + causal error code chains |
| **Reasoning workflows** | Fast-path (rule) + deliberative (LLM) + exact lookup (metadata) |
| **Evidence-bound gen** | Synthesis prompt with 5 hard rules + similarity floor gate |
| **Eval frameworks** | NDCG@5, Hit@5, faithfulness, drift detection on golden set |
| **Embedding systems** | Bi-encoder (1536-dim) + cross-encoder reranking, singleton cached |
| **Production Python** | 103 tests, singleton config, ABC enforcement, None vs 0.0 distinction |

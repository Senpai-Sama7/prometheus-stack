# PROMETHEUS Architecture

## Core Principle

**Contracts First. Gates Second. Layers Third.**

Every agent step produces a ClaimBundle. Every ClaimBundle passes through mandatory gates. No naked text escapes.

## The ClaimBundle Contract

Universal data structure for all outputs:

```json
{
  "id": "uuid",
  "timestamp": "ISO8601",
  "origin_agent": "string",
  "claims": [
    {
      "id": "uuid",
      "statement": "Atomic claim",
      "claim_type": "FACT|INFERENCE|DECISION",
      "evidence_pointers": [
        {
          "source": "URL or tool name",
          "source_confidence": 0.0-1.0,
          "evidence_hash": "SHA256(...)",
          "retrieved_at": "ISO8601"
        }
      ],
      "uncertainty": {
        "method": "semantic_entropy|model_disagreement|confidence_score|conformal_set",
        "value": 0.0-1.0,
        "interpretation": "string",
        "gate_recommendation": "EXECUTE|DEFER|REFUSE|EXPLAIN"
      },
      "risk_tier": "READ_ONLY|WRITE_LIMITED|MODIFY|DELETE|PRIVILEGE",
      "if_wrong_cost": "string"
    }
  ],
  "decision": "PUBLISH|DEFER|ESCALATE|REFUSE",
  "audit_trail": {
    "gates_passed": ["evidence_gate", "uncertainty_gate", ...],
    "gates_failed": [],
    "human_approvals": []
  }
}
```

## The Gate Stack

### Gate 1: Evidence Gate

**Rule:** If claim_type == FACT, evidence_pointers must exist and confidence >= 0.60

**Logic:**
```
for each claim in bundle.claims:
  if claim.claim_type == FACT:
    if not claim.evidence_pointers:
      return REFUSE
    for evidence in claim.evidence_pointers:
      if evidence.source_confidence < 0.60:
        return DEFER
```

**Impact:** No false facts can be published.

---

### Gate 2: Uncertainty Gate

**Rule:** If uncertainty > defer_threshold (0.75), escalate to human

**Implementation Options:**
1. **Semantic Entropy** (Wang et al., Nature 2024)
   - Generate k=5 answers
   - Cluster by semantic equivalence (NLI)
   - Compute entropy
   - AUROC 0.78-0.81 for hallucination detection

2. **Model Disagreement** (cheaper alternative)
   - Generate k=3 answers with different temperatures
   - If disagreement > threshold, defer
   - Heuristic but empirically works

3. **Conformal Prediction** (formally grounded)
   - Requires N >= 100 calibration samples
   - Generates prediction set with coverage guarantees
   - Formal guarantee: "90% of this set contains the true answer"

**Logic:**
```
if uncertainty.value > 0.75:
  return DEFER
elif uncertainty.value > 0.50:
  return EXPLAIN
else:
  return EXECUTE
```

**Impact:** Hallucinations are caught before publication.

---

### Gate 3: Security Gate

**Rule:** agent_tier >= tool_tier. Validate MCP Origin if HTTP.

**Logic:**
```
if agent.tier < tool.required_tier:
  return REFUSE
if transport == "streamable_http":
  if not validate_origin(request.headers["origin"]):
    return REFUSE  # DNS rebinding protection
if rate_limit_exceeded(agent, tool):
  return DEFER
return EXECUTE
```

**Impact:** Agents can't escalate privileges. Network transport is validated.

---

### Gate 4: Adversarial Gate

**Rule:** Guardian agent monitors for anomalous actions

**Implementation:**
Separate agent trained on BAD-ACTS examples (Nöther et al., 2025) to detect:
- Unusual action sequences
- Agent-to-agent manipulation
- Instruction injection attempts

**Logic:**
```
guardian_eval = await guardian_agent.evaluate(
  action=action,
  plan=current_plan,
  history=execution_history
)
if guardian_eval.threat_score > 0.70:
  return DEFER
return EXECUTE
```

**Impact:** BAD-ACTS paper: 50% ASR reduction, ~5% false positives.

---

### Gate 5: Human Approval Gate

**Rule:** High-risk claims require explicit human sign-off

**Logic:**
```
max_tier = max(claim.risk_tier for claim in bundle.claims)

if max_tier >= PRIVILEGE:
  escalate_to("security_team")
elif max_tier >= DELETE:
  escalate_to("ops_team")
elif max_tier >= MODIFY:
  log_and_execute()
else:
  auto_execute()
```

**Impact:** Humans remain in control of irreversible actions.

---

## The Orchestration Layer

Using LangGraph (or similar):

```
1. Decompose Task
   ↓
2. Generate Plan
   ↓
3. Execute Step
   → Evidence Gate
   → Uncertainty Gate
   → Security Gate
   → Adversarial Gate
   → Human Approval Gate (if needed)
   ↓
4. Invoke Tool
   ↓
5. Log Result
   ↓
6. Loop or End
```

Key features:
- **Checkpointing:** Every step persisted, fault-tolerant recovery
- **Threading:** Multi-user execution via thread IDs
- **Auditability:** Every decision logged with trace ID
- **Human-in-Loop:** Native support for approval gates

---

## The Trust Engine (Layers 1-6)

### Layer 1: MCP Contracts
- Tool registry with explicit schemas
- Resources (static data)
- Prompts (interactive templates)
- Transport: STDIO (local) + Streamable HTTP (with Origin validation)

### Layer 2: Orchestration (LangGraph)
- Decompose, plan, execute, invoke, loop
- Persistence, threading, fault tolerance, human-in-loop

### Layer 3: Multi-Modal Perception
- SmolVLM-256M (fast, cheap, <1GB GPU)
- Qwen2.5-VL (heavy, accurate, escalation target)

### Layer 4: Guardian Agents
- Separate agent trained on adversarial examples
- Inline monitoring on all actions > read-only

### Layer 5: Uncertainty Gates
- Semantic entropy, model disagreement, or conformal prediction
- Blocks high-uncertainty claims

### Layer 6: Evidence & Security Gates
- Evidence validation
- Permission tier checking
- Immutable audit trail

---

## The Commercial Engine (Layers 7-8)

### Layer 7: Narrative Generator
- 7-beat spine (Pattern Interrupt → Cost → Solution → Social Proof → Objection → Call → Urgency)
- Every claim verified against evidence store
- Unverifiable claims rewritten or rejected

### Layer 8: Measurement
- **MTA:** For short-cycle digital optimization (7-day lookback)
- **MMM:** For long-term strategic allocation (quarterly planning)
- **Incrementality Tests:** True causal lift (10% holdout, 2-week duration)
- **Brand Safety:** Zero tolerance for hallucinations

---

## How Gates Enforce Trust

**Rule:** Trust Engine is sovereign. Commercial Engine cannot bypass.

```
Every narrative → Evidence verification → Pass all gates → Publish
```

If a gate fails:
- REFUSE: Narrative is rejected entirely
- DEFER: Escalate to human for review
- EXPLAIN: Publish with caveats and uncertainty quantification

No "ship anyway" option.

---

## MCP Compliance (2025-06-18 Spec)

### Transport: STDIO
- Local, trusted communication
- No additional security (assumed local context)

### Transport: Streamable HTTP
- Remote, untrusted communication
- **MUST:** Origin header validation (DNS rebinding protection)
- **MUST:** HTTPS only (production)
- **OPTIONAL:** Request signing

### Tool Schema
```json
{
  "name": "tool_name",
  "description": "description",
  "inputSchema": {
    "type": "object",
    "properties": { ... },
    "required": [ ... ]
  }
}
```

All tools must have explicit, JSON Schema-validated input.

---

## Audit Trail

Every action is logged (append-only, immutable):

```json
{
  "timestamp": "2025-12-28T18:30:15Z",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "research_agent",
  "action": "tool_invocation",
  "tool_name": "web_search",
  "arguments": { "query": "..." },
  "claim_bundle_id": "uuid",
  "gates_passed": ["evidence_gate", "uncertainty_gate", "security_gate"],
  "gates_failed": [],
  "decision": "PUBLISH",
  "result_summary": "..."
}
```

**Forensic capability:** Query by agent, time, tool, decision, trace_id. Full reconstruction possible.

---

## Summary

| Component | Purpose | Enforces |
|-----------|---------|----------|
| **ClaimBundle** | Universal contract | Data structure consistency |
| **Evidence Gate** | No false facts | All FACT claims have evidence |
| **Uncertainty Gate** | No confident nonsense | High-uncertainty claims deferred |
| **Security Gate** | No privilege escalation | Agent tier <= tool tier |
| **Adversarial Gate** | No manipulation | Guardian monitors anomalies |
| **Human Approval** | Human remain in control | High-risk actions require sign-off |
| **Audit Trail** | Forensic reconstruction | Every action logged, immutable |

---

**Version:** 2.0 | **Updated:** December 28, 2025

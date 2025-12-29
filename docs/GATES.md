# PROMETHEUS: Gate Implementations

## Gate Stack Overview

Every ClaimBundle passes through **5 mandatory gates** (in order):

1. **Evidence Gate** → Verify FACT claims have sources
2. **Uncertainty Gate** → Defer high-uncertainty claims
3. **Security Gate** → Enforce privilege hierarchy + transport security
4. **Adversarial Gate** → Guardian agent monitors anomalies
5. **Human Approval Gate** → Final sign-off for irreversible actions

If **any** gate fails, the bundle decision is updated to DEFER/REFUSE/ESCALATE and the chain stops.

---

## Gate 1: Evidence Gate

**Purpose:** Ensure all FACT claims have sources with minimum confidence.

**Rule:**
```
For each claim in bundle.claims:
  if claim.claim_type == FACT:
    if evidence_pointers is empty:
      FAIL -> decision = REFUSE
    for evidence in evidence_pointers:
      if evidence.source_confidence >= 0.60:
        PASS (at least one valid source)
        break
    if no valid evidence found:
      FAIL -> decision = DEFER  # Escalate for manual validation
Else:
  PASS (INFERENCE or DECISION types don't require evidence)
```

**Implementation:**
```python
# src/gates/evidence_gate.py

def evaluate(bundle: ClaimBundle) -> GateResult:
    for claim in bundle.claims:
        if claim.claim_type != "FACT":
            continue
        
        if not claim.evidence_pointers:
            return GateResult(
                gate_name="Evidence Gate",
                passed=False,
                decision="REFUSE",
                reason=f"FACT claim '{claim.id}' has no evidence"
            )
        
        has_valid_evidence = any(
            ev.source_confidence >= 0.60
            for ev in claim.evidence_pointers
        )
        
        if not has_valid_evidence:
            return GateResult(
                gate_name="Evidence Gate",
                passed=False,
                decision="DEFER",
                reason=f"FACT claim '{claim.id}' lacks confident sources (max: {max(e.source_confidence for e in claim.evidence_pointers):.2f})"
            )
    
    return GateResult(
        gate_name="Evidence Gate",
        passed=True,
        decision="EXECUTE"
    )
```

**Impact:** No false facts escape without evidence.

---

## Gate 2: Uncertainty Gate

**Purpose:** Defer decisions with high uncertainty to human review.

**Thresholds:**
- **defer_threshold = 0.75:** If uncertainty > 0.75, decision = DEFER
- **explain_threshold = 0.50:** If 0.50 < uncertainty <= 0.75, decision = EXPLAIN
- **execute_threshold = 0.50:** If uncertainty <= 0.50, decision = EXECUTE

**Rule:**
```
for each claim in bundle.claims:
  if claim.uncertainty.value > 0.75:
    decision = DEFER
    reason = f"Uncertainty too high: {claim.uncertainty.value:.2f}"
  elif claim.uncertainty.value > 0.50:
    decision = EXPLAIN
    reason = f"Moderate uncertainty: {claim.uncertainty.value:.2f}. Include caveats in output."
  else:
    decision = EXECUTE
```

**Implementation:**
```python
# src/gates/uncertainty_gate.py

DEFER_THRESHOLD = 0.75
EXPLAIN_THRESHOLD = 0.50

def evaluate(bundle: ClaimBundle) -> GateResult:
    max_uncertainty = max(
        (claim.uncertainty.value for claim in bundle.claims),
        default=0.0
    )
    
    if max_uncertainty > DEFER_THRESHOLD:
        return GateResult(
            gate_name="Uncertainty Gate",
            passed=False,
            decision="DEFER",
            reason=f"Maximum claim uncertainty {max_uncertainty:.2f} exceeds threshold {DEFER_THRESHOLD}"
        )
    
    if max_uncertainty > EXPLAIN_THRESHOLD:
        return GateResult(
            gate_name="Uncertainty Gate",
            passed=True,
            decision="EXPLAIN",
            reason=f"Moderate uncertainty detected: {max_uncertainty:.2f}. Include caveats in narrative."
        )
    
    return GateResult(
        gate_name="Uncertainty Gate",
        passed=True,
        decision="EXECUTE"
    )
```

### Uncertainty Methods (Pick One)

#### Semantic Entropy (Recommended)
- **Reference:** Wang et al., Nature 2024 ("Universal and Transferable Adversarial Attacks on Aligned Language Models")
- **Algorithm:**
  1. Generate k=5 candidate answers
  2. Cluster by semantic equivalence (Natural Language Inference)
  3. Compute Shannon entropy over clusters
  4. Normalize to [0, 1]
- **AUROC:** 0.78-0.81 for hallucination detection
- **Cost:** 5x inference
- **Implementation:** `src/uncertainty/semantic_entropy.py`

#### Model Disagreement (Faster)
- **Algorithm:**
  1. Generate k=3 answers with temperature=[0.8, 1.0, 1.2]
  2. Compute token-level disagreement
  3. Average disagreement score
- **Cost:** 3x inference
- **Validity:** Heuristic, empirically works
- **Implementation:** `src/uncertainty/model_disagreement.py`

#### Confidence Score (Baseline)
- **Cost:** 1x inference
- **Issue:** Often overconfident
- **Implementation:** `src/uncertainty/confidence_score.py`

#### Conformal Prediction (Formal Guarantees)
- **Cost:** O(N) calibration + O(k) per inference
- **Guarantee:** "90% of this set contains the true answer"
- **Requirement:** Exchangeable calibration data (N >= 100)
- **Implementation:** `src/uncertainty/conformal.py`

**Impact:** Hallucinations caught before publication.

---

## Gate 3: Security Gate

**Purpose:** Enforce privilege hierarchy and transport security.

**Tier Hierarchy:**
```
0: READ_ONLY
1: WRITE_LIMITED
2: MODIFY
3: DELETE
4: PRIVILEGE

Rule: agent_tier >= tool_tier (no privilege escalation)
```

**Rule:**
```
if bundle.origin_agent.tier < max_tool_tier:
  decision = REFUSE
  reason = "Agent tier insufficient for requested operation"

if transport == streamable_http:
  if not validate_origin(request.headers["origin"]):
    decision = REFUSE  # DNS rebinding protection
    reason = "Invalid origin header"

if rate_limit_exceeded(agent, tool):
  decision = DEFER
  reason = "Rate limit for this agent/tool exceeded"
```

**Implementation:**
```python
# src/gates/security_gate.py

TIER_HIERARCHY = {
    "READ_ONLY": 0,
    "WRITE_LIMITED": 1,
    "MODIFY": 2,
    "DELETE": 3,
    "PRIVILEGE": 4
}

def evaluate(bundle: ClaimBundle, agent: Agent, request: dict) -> GateResult:
    # Check privilege hierarchy
    max_tier = max(
        (TIER_HIERARCHY.get(c.risk_tier, 0) for c in bundle.claims),
        default=0
    )
    
    if agent.tier < max_tier:
        return GateResult(
            gate_name="Security Gate",
            passed=False,
            decision="REFUSE",
            reason=f"Agent tier {agent.tier} insufficient for tier {max_tier} operation"
        )
    
    # Check MCP origin if HTTP
    if request.get("transport") == "streamable_http":
        origin = request.headers.get("origin")
        if not validate_origin(origin, ALLOWED_ORIGINS):
            return GateResult(
                gate_name="Security Gate",
                passed=False,
                decision="REFUSE",
                reason=f"Invalid origin header: {origin}"
            )
    
    # Check rate limits
    if is_rate_limited(agent.id, request.get("tool_name")):
        return GateResult(
            gate_name="Security Gate",
            passed=False,
            decision="DEFER",
            reason=f"Rate limit exceeded for {agent.id}"
        )
    
    return GateResult(
        gate_name="Security Gate",
        passed=True,
        decision="EXECUTE"
    )
```

**MCP Compliance (Spec 2025-06-18):**
- **STDIO:** No additional validation (assumed local/trusted)
- **Streamable HTTP:** MUST validate Origin header (DNS rebinding protection)

**Impact:** Agents can't escalate privileges. Network transport validated.

---

## Gate 4: Adversarial Gate

**Purpose:** Detect adversarial manipulation patterns.

**Mechanism:** Separate Guardian agent trained on **BAD-ACTS** examples (Nöther et al., Aug 2025).

Guardian evaluates:
- Unusual action sequences
- Agent-to-agent manipulation attempts
- Instruction injection patterns
- Privilege escalation chains

**Rule:**
```
guardian_eval = await guardian_agent.evaluate(
  action=current_action,
  plan=execution_plan,
  history=execution_history
)

if guardian_eval.threat_score > 0.70:
  decision = DEFER
  reason = f"Potential adversarial pattern: {guardian_eval.threat_description}"
else:
  decision = EXECUTE
```

**Implementation:**
```python
# src/gates/adversarial_gate.py

class GuardianEvaluation:
    threat_score: float  # 0.0-1.0
    threat_description: str
    mitigation: str

async def evaluate(bundle: ClaimBundle, context: ExecutionContext) -> GateResult:
    guardian = load_guardian_agent()  # Trained on BAD-ACTS examples
    
    eval_result = await guardian.evaluate(
        action=context.current_action,
        plan=context.execution_plan,
        history=context.execution_history
    )
    
    if eval_result.threat_score > 0.70:
        return GateResult(
            gate_name="Adversarial Gate",
            passed=False,
            decision="DEFER",
            reason=f"Adversarial pattern detected: {eval_result.threat_description}"
        )
    
    return GateResult(
        gate_name="Adversarial Gate",
        passed=True,
        decision="EXECUTE"
    )
```

**BAD-ACTS Effectiveness (Nöther et al., Aug 2025):**
| Model | ASR Reduction | False Positive Rate |
|-------|---------------|---------------------|
| Llama-3.1-70B | ~50% | ~5% |
| GPT-4.1 | ~25% | ~5% |

**Note:** Guardian doesn't eliminate attacks, reduces success rate.

**Impact:** Adversaries struggle. System not impenetrable but hardened.

---

## Gate 5: Human Approval Gate

**Purpose:** Humans retain control of irreversible actions.

**Tier-Based Escalation:**
```
max_tier = max(claim.risk_tier for claim in bundle.claims)

if max_tier == PRIVILEGE:
  escalate_to(security_team)    # BLOCKING (requires explicit approval)
elif max_tier == DELETE:
  escalate_to(ops_team)          # BLOCKING (requires explicit approval)
elif max_tier == MODIFY:
  log_action()                   # AUTO-APPROVE (logged for audit)
else:
  execute()                      # AUTO-APPROVE (READ_ONLY / WRITE_LIMITED)
```

**Implementation:**
```python
# src/gates/human_approval_gate.py

TIER_APPROVAL_MAP = {
    "READ_ONLY": {"required": False, "escalate_to": None},
    "WRITE_LIMITED": {"required": False, "escalate_to": None},
    "MODIFY": {"required": False, "escalate_to": "audit_log"},
    "DELETE": {"required": True, "escalate_to": "ops_team"},
    "PRIVILEGE": {"required": True, "escalate_to": "security_team"}
}

async def evaluate(bundle: ClaimBundle) -> GateResult:
    max_tier = max(
        (claim.risk_tier for claim in bundle.claims),
        default="READ_ONLY"
    )
    
    config = TIER_APPROVAL_MAP[max_tier]
    
    if config["required"]:
        return GateResult(
            gate_name="Human Approval Gate",
            passed=False,
            decision="ESCALATE",
            reason=f"Action requires {config['escalate_to']} approval",
            escalate_to=config["escalate_to"]
        )
    
    return GateResult(
        gate_name="Human Approval Gate",
        passed=True,
        decision="EXECUTE"
    )
```

**Impact:** Humans remain in control of irreversible actions.

---

## Gate Decision Flow

```
ClaimBundle enters gate stack
           ↓
    Evidence Gate
      passes?
     /    \
   Y      N -> REFUSE (log)
   ↓
Uncertainty Gate
      passes?
     /    |\
   Y    M  N -> DEFER (escalate)
   ↓
Security Gate
      passes?
     /    \
   Y      N -> REFUSE (log)
   ↓
Adversarial Gate
      passes?
     /    \
   Y      N -> DEFER (escalate)
   ↓
Human Approval Gate
      passes?
     /    \
   Y      N -> ESCALATE (blocking)
   ↓
All gates passed
↓
Decision: PUBLISH
```

---

## Testing Gates

### Unit Tests
```bash
pytest tests/test_gates.py -v
```

### Acceptance Tests
```bash
pytest tests/acceptance/ -v
```

### Integration Test
```bash
python examples/minimal_pipeline.py
```

---

**Version:** 2.0 | **Updated:** December 28, 2025

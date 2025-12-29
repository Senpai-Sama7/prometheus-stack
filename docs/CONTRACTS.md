# PROMETHEUS: ClaimBundle Contract Specification

## Overview

The **ClaimBundle** is the universal contract for all PROMETHEUS outputs. Every agent step, gate decision, and verification result is represented as a ClaimBundle.

## ClaimBundle Structure

```json
{
  "id": "uuid",
  "timestamp": "ISO-8601",
  "origin_agent": "string",
  "claims": [
    {
      "id": "string",
      "statement": "string",
      "claim_type": "FACT | INFERENCE | DECISION",
      "evidence_pointers": [
        {
          "source": "url or reference",
          "source_confidence": 0.0-1.0,
          "evidence_hash": "sha256",
          "retrieved_at": "ISO-8601"
        }
      ],
      "uncertainty": {
        "method": "semantic_entropy | model_disagreement | confidence_score | conformal_set",
        "value": 0.0-1.0,
        "interpretation": "string",
        "gate_recommendation": "EXECUTE | DEFER | REFUSE | EXPLAIN"
      },
      "risk_tier": "READ_ONLY | WRITE_LIMITED | MODIFY | DELETE | PRIVILEGE",
      "if_wrong_cost": "description of consequences"
    }
  ],
  "decision": "PUBLISH | DEFER | ESCALATE | REFUSE",
  "reason": "string",
  "required_approvals": ["approver_id"],
  "audit_trail": {
    "gates_passed": ["gate_name"],
    "gates_failed": ["gate_name"],
    "human_approvals": [
      {
        "approver": "string",
        "timestamp": "ISO-8601",
        "decision": "APPROVED | REJECTED",
        "reason": "string"
      }
    ]
  }
}
```

## Claim Types

| Type | Evidence | Purpose | Approval |
|------|----------|---------|----------|
| **FACT** | Required (confidence >= 0.60) | Factual statement backed by sources | Evidence Gate |
| **INFERENCE** | Optional | Logical deduction from other claims | Uncertainty Gate |
| **DECISION** | Not required | Action decision (gate determination) | Human Approval Gate |

## Uncertainty Methods

### Semantic Entropy (Recommended)
- **Algorithm:** Generate k=5 answers, cluster by semantic equivalence (NLI), compute Shannon entropy
- **AUROC:** 0.78-0.81 (Wang et al., Nature 2024)
- **Cost:** 5x inference
- **Implementation:** See `src/uncertainty/semantic_entropy.py`

### Model Disagreement (Faster)
- **Algorithm:** Generate k=3 answers with temp=[0.8, 1.0, 1.2], measure disagreement
- **Cost:** 3x inference
- **Validity:** Empirical heuristic, not formally justified
- **Implementation:** See `src/uncertainty/model_disagreement.py`

### Confidence Score (Baseline)
- **Algorithm:** Direct model confidence output
- **Cost:** 1x inference
- **Validity:** Model-dependent, often overconfident
- **Implementation:** See `src/uncertainty/confidence_score.py`

### Conformal Prediction (Formal Guarantees)
- **Algorithm:** Prediction sets with coverage guarantees
- **Cost:** O(N) calibration + O(k) per inference
- **Guarantee:** "90% of this set contains the true answer"
- **Assumption:** Calibration data exchangeable
- **Implementation:** See `src/uncertainty/conformal.py`

## Risk Tiers

| Tier | Example | Auto-Approve | Requires Human | Comment |
|------|---------|--------------|----------------|---------|
| **READ_ONLY** | Data fetch, query | ✅ Yes | No | No side effects |
| **WRITE_LIMITED** | Logging, caching | ✅ Yes | No | Non-destructive |
| **MODIFY** | Config change, update | ❌ No | ⚠️ Logged | Mutable state |
| **DELETE** | Clear, delete record | ❌ No | ✅ **Yes** | Irreversible |
| **PRIVILEGE** | Access secrets, creds | ❌ No | ✅ **Yes** | System-level |

## Evidence Requirements

### FACT Claims

**Rule:** Every FACT claim MUST have:
1. `evidence_pointers` array (non-empty)
2. At least one pointer with `source_confidence >= 0.60`
3. `evidence_hash` (SHA256 of evidence content)
4. `retrieved_at` timestamp

**Validation:**
```python
def validate_fact(claim):
  if claim.claim_type != "FACT":
    return True  # Not applicable
  
  if not claim.evidence_pointers:
    return False  # FAIL: No evidence
  
  for evidence in claim.evidence_pointers:
    if evidence.source_confidence >= 0.60:
      return True  # PASS: At least one valid evidence
  
  return False  # FAIL: All evidence weak
```

### INFERENCE Claims

**Rule:** Optional evidence. If provided, must meet same standards as FACT.

### DECISION Claims

**Rule:** No evidence required. Gate recommendation drives approval.

---

## Gate Recommendations

| Recommendation | Meaning | Next Action |
|---|---|---|
| **EXECUTE** | Proceed with action | Gate passes, move to next gate |
| **DEFER** | Escalate to human | Stop chain, queue for approval |
| **REFUSE** | Reject action | Stop chain, log reason, fail bundle |
| **EXPLAIN** | Proceed + add caveats | Continue to next gate, add uncertainty note to output |

---

## Serialization

### Python (Reference Implementation)

```python
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import uuid

@dataclass
class EvidencePointer:
    source: str
    source_confidence: float
    evidence_hash: str
    retrieved_at: str = None
    
    def __post_init__(self):
        if self.retrieved_at is None:
            self.retrieved_at = datetime.utcnow().isoformat() + "Z"

@dataclass
class Uncertainty:
    method: str  # semantic_entropy, model_disagreement, etc.
    value: float
    interpretation: str = ""
    gate_recommendation: str = "EXECUTE"

@dataclass
class Claim:
    statement: str
    claim_type: str
    uncertainty: Uncertainty
    risk_tier: str
    id: str = None
    evidence_pointers: list = None
    if_wrong_cost: str = ""
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.evidence_pointers is None:
            self.evidence_pointers = []

@dataclass
class ClaimBundle:
    origin_agent: str
    claims: list
    id: str = None
    timestamp: str = None
    decision: str = "DEFER"
    reason: str = ""
    required_approvals: list = None
    audit_trail: dict = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        if self.required_approvals is None:
            self.required_approvals = []
        if self.audit_trail is None:
            self.audit_trail = {"gates_passed": [], "gates_failed": [], "human_approvals": []}
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str):
        return cls(**json.loads(json_str))
```

---

## Examples

### Example 1: FACT with Evidence

```json
{
  "id": "claim-001",
  "statement": "Semantic entropy AUROC >= 0.78 for hallucination detection",
  "claim_type": "FACT",
  "evidence_pointers": [
    {
      "source": "https://nature.com/articles/s41586-024-07421-0",
      "source_confidence": 0.95,
      "evidence_hash": "bd24c2aaef2ef37ae95f0f9e5f7d9e7c",
      "retrieved_at": "2025-12-28T19:30:00Z"
    }
  ],
  "uncertainty": {
    "method": "semantic_entropy",
    "value": 0.15,
    "interpretation": "Strong empirical validation",
    "gate_recommendation": "EXECUTE"
  },
  "risk_tier": "READ_ONLY",
  "if_wrong_cost": "Claim is verifiable against published literature"
}
```

### Example 2: DECISION with High Uncertainty

```json
{
  "id": "decision-001",
  "statement": "Escalate novel attack pattern to security team",
  "claim_type": "DECISION",
  "evidence_pointers": [],
  "uncertainty": {
    "method": "model_disagreement",
    "value": 0.82,
    "interpretation": "Anomaly detection models disagreed",
    "gate_recommendation": "DEFER"
  },
  "risk_tier": "PRIVILEGE",
  "if_wrong_cost": "Security incident could be missed; false positive wastes team time"
}
```

---

**Version:** 2.0 | **Updated:** December 28, 2025

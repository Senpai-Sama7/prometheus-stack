"""ClaimBundle: Universal contract for all PROMETHEUS outputs."""

import json
import hashlib
from typing import Optional, List, Dict, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
from datetime import datetime


class ClaimType(str, Enum):
    """Type of claim."""
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    DECISION = "DECISION"


class RiskTier(str, Enum):
    """Risk level of an action."""
    READ_ONLY = "READ_ONLY"
    WRITE_LIMITED = "WRITE_LIMITED"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    PRIVILEGE = "PRIVILEGE"


class UncertaintyMethod(str, Enum):
    """Method for computing uncertainty."""
    SEMANTIC_ENTROPY = "semantic_entropy"
    MODEL_DISAGREEMENT = "model_disagreement"
    CONFIDENCE_SCORE = "confidence_score"
    CONFORMAL_SET = "conformal_set"


class BundleDecision(str, Enum):
    """Decision on ClaimBundle."""
    PUBLISH = "PUBLISH"
    DEFER = "DEFER"
    ESCALATE = "ESCALATE"
    REFUSE = "REFUSE"


@dataclass
class EvidencePointer:
    """Pointer to evidence backing a claim."""
    source: str  # URL, tool name, or model inference ID
    source_confidence: float  # 0.0-1.0
    evidence_hash: str  # SHA256(evidence_text)
    retrieved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    provenance: Dict = field(default_factory=dict)  # {tool, user, authorization_level}

    def to_dict(self):
        return asdict(self)


@dataclass
class Uncertainty:
    """Quantified uncertainty for a claim."""
    method: UncertaintyMethod
    value: float  # 0.0-1.0
    interpretation: str = ""
    gate_recommendation: str = "EXECUTE"

    def to_dict(self):
        return {
            "method": self.method.value,
            "value": self.value,
            "interpretation": self.interpretation,
            "gate_recommendation": self.gate_recommendation
        }


@dataclass
class Claim:
    """Atomic claim: statement with evidence and uncertainty."""
    id: str = field(default_factory=lambda: str(uuid4()))
    statement: str = ""
    claim_type: ClaimType = ClaimType.INFERENCE
    evidence_pointers: List[EvidencePointer] = field(default_factory=list)
    uncertainty: Uncertainty = field(default_factory=lambda: Uncertainty(
        method=UncertaintyMethod.CONFIDENCE_SCORE,
        value=0.5,
        interpretation="No uncertainty computed"
    ))
    risk_tier: RiskTier = RiskTier.READ_ONLY
    if_wrong_cost: str = ""

    def to_dict(self):
        return {
            "id": self.id,
            "statement": self.statement,
            "claim_type": self.claim_type.value,
            "evidence_pointers": [ep.to_dict() for ep in self.evidence_pointers],
            "uncertainty": self.uncertainty.to_dict(),
            "risk_tier": self.risk_tier.value,
            "if_wrong_cost": self.if_wrong_cost
        }


@dataclass
class HumanApproval:
    """Record of human approval/rejection."""
    approver: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    decision: Literal["APPROVED", "REJECTED"] = "APPROVED"
    reason: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class AuditTrail:
    """Execution audit trail."""
    gates_passed: List[str] = field(default_factory=list)
    gates_failed: List[str] = field(default_factory=list)
    human_approvals: List[HumanApproval] = field(default_factory=list)

    def to_dict(self):
        return {
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "human_approvals": [ha.to_dict() for ha in self.human_approvals]
        }


@dataclass
class ClaimBundle:
    """Universal output structure for all PROMETHEUS layers."""
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    origin_agent: str = "unknown"
    claims: List[Claim] = field(default_factory=list)
    decision: BundleDecision = BundleDecision.DEFER
    reason: str = ""
    required_approvals: List[str] = field(default_factory=list)
    audit_trail: AuditTrail = field(default_factory=AuditTrail)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "origin_agent": self.origin_agent,
            "claims": [c.to_dict() for c in self.claims],
            "decision": self.decision.value,
            "reason": self.reason,
            "required_approvals": self.required_approvals,
            "audit_trail": self.audit_trail.to_dict()
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

"""
ClaimBundle: Universal contract for PROMETHEUS outputs.

Every agent step, gate decision, and verification result is represented as a ClaimBundle.
This module implements the core data structures and serialization logic.

Reference: docs/CONTRACTS.md
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json
import uuid
from hashlib import sha256


class ClaimType(str, Enum):
    """Types of claims in a bundle."""
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    DECISION = "DECISION"


class UncertaintyMethod(str, Enum):
    """Methods for computing uncertainty."""
    SEMANTIC_ENTROPY = "semantic_entropy"
    MODEL_DISAGREEMENT = "model_disagreement"
    CONFIDENCE_SCORE = "confidence_score"
    CONFORMAL_SET = "conformal_set"


class GateRecommendation(str, Enum):
    """Gate recommendations."""
    EXECUTE = "EXECUTE"
    DEFER = "DEFER"
    REFUSE = "REFUSE"
    EXPLAIN = "EXPLAIN"


class RiskTier(str, Enum):
    """Risk tiers for actions."""
    READ_ONLY = "READ_ONLY"
    WRITE_LIMITED = "WRITE_LIMITED"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    PRIVILEGE = "PRIVILEGE"


class BundleDecision(str, Enum):
    """Final bundle decision."""
    PUBLISH = "PUBLISH"
    DEFER = "DEFER"
    ESCALATE = "ESCALATE"
    REFUSE = "REFUSE"


@dataclass
class EvidencePointer:
    """Pointer to evidence source for a claim."""
    source: str
    source_confidence: float
    evidence_hash: str
    retrieved_at: Optional[str] = None

    def __post_init__(self):
        if self.retrieved_at is None:
            self.retrieved_at = datetime.utcnow().isoformat() + "Z"
        if not (0.0 <= self.source_confidence <= 1.0):
            raise ValueError(f"source_confidence must be in [0.0, 1.0], got {self.source_confidence}")

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvidencePointer":
        return cls(**d)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Uncertainty:
    """Uncertainty quantification for a claim."""
    method: UncertaintyMethod
    value: float
    interpretation: str = ""
    gate_recommendation: GateRecommendation = GateRecommendation.EXECUTE

    def __post_init__(self):
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(f"value must be in [0.0, 1.0], got {self.value}")
        if isinstance(self.method, str):
            self.method = UncertaintyMethod(self.method)
        if isinstance(self.gate_recommendation, str):
            self.gate_recommendation = GateRecommendation(self.gate_recommendation)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Uncertainty":
        return cls(**d)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "value": self.value,
            "interpretation": self.interpretation,
            "gate_recommendation": self.gate_recommendation.value
        }


@dataclass
class Claim:
    """Individual claim within a bundle."""
    statement: str
    claim_type: ClaimType
    uncertainty: Uncertainty
    risk_tier: RiskTier
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evidence_pointers: List[EvidencePointer] = field(default_factory=list)
    if_wrong_cost: str = ""

    def __post_init__(self):
        if isinstance(self.claim_type, str):
            self.claim_type = ClaimType(self.claim_type)
        if isinstance(self.risk_tier, str):
            self.risk_tier = RiskTier(self.risk_tier)
        if isinstance(self.uncertainty, dict):
            self.uncertainty = Uncertainty.from_dict(self.uncertainty)
        self.evidence_pointers = [
            ev if isinstance(ev, EvidencePointer) else EvidencePointer.from_dict(ev)
            for ev in self.evidence_pointers
        ]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Claim":
        return cls(**d)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "claim_type": self.claim_type.value,
            "evidence_pointers": [ev.to_dict() for ev in self.evidence_pointers],
            "uncertainty": self.uncertainty.to_dict(),
            "risk_tier": self.risk_tier.value,
            "if_wrong_cost": self.if_wrong_cost
        }

    def validate(self) -> List[str]:
        """Validate claim according to CONTRACTS spec."""
        errors = []
        
        # FACT claims must have evidence
        if self.claim_type == ClaimType.FACT:
            if not self.evidence_pointers:
                errors.append(f"FACT claim '{self.id}' has no evidence_pointers")
            else:
                # At least one source must have confidence >= 0.60
                max_confidence = max(ev.source_confidence for ev in self.evidence_pointers)
                if max_confidence < 0.60:
                    errors.append(f"FACT claim '{self.id}' lacks confident sources (max: {max_confidence:.2f})")
        
        return errors


@dataclass
class ClaimBundle:
    """Universal contract for PROMETHEUS outputs."""
    origin_agent: str
    claims: List[Claim]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    decision: BundleDecision = BundleDecision.DEFER
    reason: str = ""
    required_approvals: List[str] = field(default_factory=list)
    audit_trail: Dict[str, Any] = field(default_factory=lambda: {
        "gates_passed": [],
        "gates_failed": [],
        "human_approvals": []
    })

    def __post_init__(self):
        if isinstance(self.decision, str):
            self.decision = BundleDecision(self.decision)
        self.claims = [
            claim if isinstance(claim, Claim) else Claim.from_dict(claim)
            for claim in self.claims
        ]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ClaimBundle":
        return cls(**d)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "origin_agent": self.origin_agent,
            "claims": [claim.to_dict() for claim in self.claims],
            "decision": self.decision.value,
            "reason": self.reason,
            "required_approvals": self.required_approvals,
            "audit_trail": self.audit_trail
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize bundle to JSON."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "ClaimBundle":
        """Deserialize bundle from JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> List[str]:
        """Validate entire bundle."""
        errors = []
        
        # Validate all claims
        for claim in self.claims:
            errors.extend(claim.validate())
        
        # Validate bundle structure
        if not self.origin_agent:
            errors.append("origin_agent cannot be empty")
        if not self.claims:
            errors.append("Bundle must contain at least one claim")
        
        return errors

    def add_gate_result(self, gate_name: str, passed: bool):
        """Record gate result in audit trail."""
        if passed:
            self.audit_trail["gates_passed"].append(gate_name)
        else:
            self.audit_trail["gates_failed"].append(gate_name)

    def add_human_approval(self, approver: str, decision: str, reason: str = ""):
        """Record human approval in audit trail."""
        approval = {
            "approver": approver,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "decision": decision,
            "reason": reason
        }
        self.audit_trail["human_approvals"].append(approval)


# Convenience builder
def create_bundle(agent_id: str, claims: List[Dict[str, Any]]) -> ClaimBundle:
    """Create a new bundle with claims."""
    claim_objects = [Claim.from_dict(c) for c in claims]
    return ClaimBundle(origin_agent=agent_id, claims=claim_objects)

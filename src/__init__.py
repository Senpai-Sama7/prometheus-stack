"""PROMETHEUS: Trust-Engine-First AI Orchestration Stack."""

__version__ = "2.0.0"
__author__ = "PROMETHEUS Team"
__license__ = "MIT"

from src.claim_bundle import (
    ClaimBundle,
    Claim,
    EvidencePointer,
    Uncertainty,
    HumanApproval,
    AuditTrail,
    ClaimType,
    RiskTier,
    UncertaintyMethod,
    BundleDecision,
)
from src.gates import (
    Gate,
    EvidenceGate,
    UncertaintyGate,
    SecurityGate,
    AdversarialGate,
    HumanApprovalGate,
    GateAction,
    GateDecision,
)
from src.orchestrator import ExecutionOrchestrator
from src.mcp_registry import MCPToolRegistry
from src.audit_log import AuditLog

__all__ = [
    "ClaimBundle",
    "Claim",
    "EvidencePointer",
    "Uncertainty",
    "HumanApproval",
    "AuditTrail",
    "ClaimType",
    "RiskTier",
    "UncertaintyMethod",
    "BundleDecision",
    "Gate",
    "EvidenceGate",
    "UncertaintyGate",
    "SecurityGate",
    "AdversarialGate",
    "HumanApprovalGate",
    "GateAction",
    "GateDecision",
    "ExecutionOrchestrator",
    "MCPToolRegistry",
    "AuditLog",
]

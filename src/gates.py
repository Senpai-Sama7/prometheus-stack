"""Gate implementations: Evidence, Uncertainty, Security, Adversarial, Human Approval."""

from typing import Dict, List
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
from src.claim_bundle import (
    ClaimBundle,
    Claim,
    ClaimType,
    RiskTier,
    UncertaintyMethod,
)


class GateAction(str, Enum):
    """Gate decision action."""
    EXECUTE = "EXECUTE"
    DEFER = "DEFER"
    REFUSE = "REFUSE"
    ESCALATE = "ESCALATE"
    EXPLAIN = "EXPLAIN"


@dataclass
class GateDecision:
    """Decision output from any gate."""
    action: GateAction
    reason: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self):
        return {
            "action": self.action.value,
            "reason": self.reason,
            "metadata": self.metadata
        }


class Gate(ABC):
    """Base class for gate implementations."""

    @abstractmethod
    async def evaluate(self, *args, **kwargs) -> GateDecision:
        pass


class EvidenceGate(Gate):
    """Ensure FACT claims have evidence."""

    async def evaluate(self, claim_bundle: ClaimBundle) -> GateDecision:
        """
        Rule: If claim_type == FACT, evidence_pointers must be non-empty and confident.
        """
        for claim in claim_bundle.claims:
            if claim.claim_type == ClaimType.FACT:
                if not claim.evidence_pointers:
                    return GateDecision(
                        action=GateAction.REFUSE,
                        reason=f"Claim '{claim.statement}' is FACT but has no evidence"
                    )

                for evidence in claim.evidence_pointers:
                    if evidence.source_confidence < 0.60:
                        return GateDecision(
                            action=GateAction.DEFER,
                            reason=f"Evidence confidence {evidence.source_confidence:.2f} < 0.60. Escalate.",
                            metadata={"source": evidence.source}
                        )

        return GateDecision(
            action=GateAction.EXECUTE,
            reason="All FACT claims have evidence >= 0.60 confidence"
        )


class UncertaintyGate(Gate):
    """Block high-uncertainty claims."""

    def __init__(self, defer_threshold: float = 0.75, explain_threshold: float = 0.50):
        self.defer_threshold = defer_threshold
        self.explain_threshold = explain_threshold

    async def evaluate(self, claim: Claim) -> GateDecision:
        """
        Rule: If uncertainty > defer_threshold, defer.
              If uncertainty > explain_threshold, explain.
              Otherwise, execute.
        """
        uncertainty_value = claim.uncertainty.value

        if uncertainty_value > self.defer_threshold:
            return GateDecision(
                action=GateAction.DEFER,
                reason=f"Uncertainty {uncertainty_value:.2f} > {self.defer_threshold}. "
                       f"Interpretation: {claim.uncertainty.interpretation}",
                metadata={
                    "uncertainty_value": uncertainty_value,
                    "method": claim.uncertainty.method.value
                }
            )

        if uncertainty_value > self.explain_threshold:
            return GateDecision(
                action=GateAction.EXPLAIN,
                reason=f"Uncertainty {uncertainty_value:.2f} > {self.explain_threshold}. "
                       f"Publishing with caveats.",
                metadata={"uncertainty_value": uncertainty_value}
            )

        return GateDecision(
            action=GateAction.EXECUTE,
            reason=f"Uncertainty {uncertainty_value:.2f} within acceptable bounds"
        )


class ToolInvocation:
    """Represents a tool call request."""
    def __init__(self, tool_name: str, arguments: Dict, transport: str = "stdio",
                 request_headers: Dict = None, required_tier: RiskTier = RiskTier.READ_ONLY):
        self.tool_name = tool_name
        self.arguments = arguments
        self.transport = transport
        self.request_headers = request_headers or {}
        self.required_tier = required_tier


class SecurityGate(Gate):
    """Validate tool invocation permissions."""

    def __init__(self, tool_registry: Dict, agent_permissions: Dict):
        self.tool_registry = tool_registry
        self.agent_permissions = agent_permissions

    async def evaluate(self, invocation: ToolInvocation, agent_id: str) -> GateDecision:
        """
        Rule: agent_tier >= tool_tier. Validate MCP Origin if HTTP.
        """
        # 1. Check if tool exists
        if invocation.tool_name not in self.tool_registry:
            return GateDecision(
                action=GateAction.REFUSE,
                reason=f"Tool '{invocation.tool_name}' not registered"
            )

        # 2. Check permission tier
        tool_tier = self.tool_registry[invocation.tool_name].get("required_tier", RiskTier.READ_ONLY)
        agent_tier = self.agent_permissions.get(agent_id, RiskTier.READ_ONLY)

        # Convert to int for comparison
        tier_values = {
            RiskTier.READ_ONLY: 0,
            RiskTier.WRITE_LIMITED: 1,
            RiskTier.MODIFY: 2,
            RiskTier.DELETE: 3,
            RiskTier.PRIVILEGE: 4
        }

        if tier_values[agent_tier] < tier_values[tool_tier]:
            return GateDecision(
                action=GateAction.REFUSE,
                reason=f"Agent tier {agent_tier.value} < tool tier {tool_tier.value}"
            )

        # 3. MCP Origin validation (if Streamable HTTP)
        if invocation.transport == "streamable_http":
            origin = invocation.request_headers.get("origin")
            if not origin:
                return GateDecision(
                    action=GateAction.REFUSE,
                    reason="Streamable HTTP requires Origin header (DNS rebinding protection)"
                )

        return GateDecision(
            action=GateAction.EXECUTE,
            reason="Security gate passed"
        )


class AdversarialGate(Gate):
    """Guardian agent defense (stub for now)."""

    async def evaluate(self, action_statement: str, context_history: List[str]) -> GateDecision:
        """
        Simplified: just check if action is unusual given history.
        In production, this would be a separate model.
        """
        # Stub: always pass for now
        return GateDecision(
            action=GateAction.EXECUTE,
            reason="Adversarial gate passed (stub implementation)"
        )


class HumanApprovalGate(Gate):
    """Block high-risk actions pending human approval."""

    async def evaluate(self, claim_bundle: ClaimBundle) -> GateDecision:
        """
        Rule: If max(risk_tier) >= PRIVILEGE, escalate to security.
              If >= DELETE, escalate to ops.
              If >= MODIFY, allow with logging.
              Otherwise, auto-approve.
        """
        if not claim_bundle.claims:
            return GateDecision(
                action=GateAction.EXECUTE,
                reason="No claims to approve"
            )

        max_tier = max((c.risk_tier for c in claim_bundle.claims),
                       default=RiskTier.READ_ONLY)

        if max_tier == RiskTier.PRIVILEGE:
            return GateDecision(
                action=GateAction.ESCALATE,
                reason="PRIVILEGE-tier action requires security team approval"
            )

        if max_tier == RiskTier.DELETE:
            return GateDecision(
                action=GateAction.ESCALATE,
                reason="DELETE-tier action requires ops approval"
            )

        if max_tier == RiskTier.MODIFY:
            return GateDecision(
                action=GateAction.EXECUTE,
                reason="MODIFY-tier action approved (logged)"
            )

        return GateDecision(
            action=GateAction.EXECUTE,
            reason="Within auto-approval tier"
        )

"""
Gate implementations for PROMETHEUS verification pipeline.

All bundles pass through 5 gates:
1. Evidence Gate - Verify FACT claims have sources
2. Uncertainty Gate - Defer high-uncertainty claims
3. Security Gate - Enforce privilege hierarchy
4. Adversarial Gate - Guardian agent monitors anomalies
5. Human Approval Gate - Final sign-off for high-risk actions

Reference: docs/GATES.md
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from src.claim_bundle import (
    ClaimBundle,
    ClaimType,
    BundleDecision,
    RiskTier,
)


@dataclass
class GateResult:
    """Result of a gate evaluation."""
    gate_name: str
    passed: bool
    decision: BundleDecision
    reason: str = ""
    escalate_to: Optional[str] = None


class EvidenceGate:
    """Gate 1: Verify FACT claims have evidence."""

    MIN_CONFIDENCE = 0.60

    @classmethod
    def evaluate(cls, bundle: ClaimBundle) -> GateResult:
        """Evaluate bundle against evidence requirements."""
        for claim in bundle.claims:
            if claim.claim_type != ClaimType.FACT:
                continue

            # FACT claims must have evidence
            if not claim.evidence_pointers:
                return GateResult(
                    gate_name="Evidence Gate",
                    passed=False,
                    decision=BundleDecision.REFUSE,
                    reason=f"FACT claim '{claim.id}' has no evidence"
                )

            # At least one source must have confidence >= threshold
            max_confidence = max(
                (ev.source_confidence for ev in claim.evidence_pointers),
                default=0.0
            )

            if max_confidence < cls.MIN_CONFIDENCE:
                return GateResult(
                    gate_name="Evidence Gate",
                    passed=False,
                    decision=BundleDecision.DEFER,
                    reason=f"FACT claim lacks confident sources (max: {max_confidence:.2f}, required: {cls.MIN_CONFIDENCE})"
                )

        return GateResult(
            gate_name="Evidence Gate",
            passed=True,
            decision=BundleDecision.PUBLISH,
            reason="All FACT claims have sufficient evidence"
        )


class UncertaintyGate:
    """Gate 2: Defer high-uncertainty claims."""

    DEFER_THRESHOLD = 0.75
    EXPLAIN_THRESHOLD = 0.50

    @classmethod
    def evaluate(cls, bundle: ClaimBundle) -> GateResult:
        """Evaluate bundle against uncertainty thresholds."""
        max_uncertainty = max(
            (claim.uncertainty.value for claim in bundle.claims),
            default=0.0
        )

        if max_uncertainty > cls.DEFER_THRESHOLD:
            return GateResult(
                gate_name="Uncertainty Gate",
                passed=False,
                decision=BundleDecision.DEFER,
                reason=f"Uncertainty {max_uncertainty:.2f} exceeds threshold {cls.DEFER_THRESHOLD}"
            )

        if max_uncertainty > cls.EXPLAIN_THRESHOLD:
            return GateResult(
                gate_name="Uncertainty Gate",
                passed=True,
                decision=BundleDecision.PUBLISH,
                reason=f"Moderate uncertainty {max_uncertainty:.2f}: include caveats in narrative"
            )

        return GateResult(
            gate_name="Uncertainty Gate",
            passed=True,
            decision=BundleDecision.PUBLISH,
            reason=f"Low uncertainty {max_uncertainty:.2f}"
        )


class SecurityGate:
    """Gate 3: Enforce privilege hierarchy and transport security."""

    TIER_HIERARCHY = {
        RiskTier.READ_ONLY: 0,
        RiskTier.WRITE_LIMITED: 1,
        RiskTier.MODIFY: 2,
        RiskTier.DELETE: 3,
        RiskTier.PRIVILEGE: 4,
    }

    @classmethod
    def evaluate(
        cls,
        bundle: ClaimBundle,
        agent_tier: int = 4,  # Default: max tier
        allow_transport: str = "stdio"
    ) -> GateResult:
        """Evaluate bundle against security requirements."""
        # Check privilege hierarchy
        max_tier_value = max(
            (
                cls.TIER_HIERARCHY.get(claim.risk_tier, 0)
                for claim in bundle.claims
            ),
            default=0
        )

        if agent_tier < max_tier_value:
            return GateResult(
                gate_name="Security Gate",
                passed=False,
                decision=BundleDecision.REFUSE,
                reason=f"Agent tier {agent_tier} insufficient for required tier {max_tier_value}"
            )

        # Check transport security
        if allow_transport == "streamable_http":
            # In production, validate Origin header
            # Stub for now: assume Origin validation passed
            pass

        return GateResult(
            gate_name="Security Gate",
            passed=True,
            decision=BundleDecision.PUBLISH,
            reason="Security requirements met"
        )


class AdversarialGate:
    """Gate 4: Guardian agent monitors for anomalies.
    
    Stub implementation: would call guardian LLM in production.
    """

    THREAT_THRESHOLD = 0.70

    @classmethod
    def evaluate(cls, bundle: ClaimBundle, threat_score: float = 0.0) -> GateResult:
        """Evaluate bundle for adversarial patterns.
        
        Args:
            bundle: ClaimBundle to evaluate
            threat_score: Pre-computed threat score (0.0-1.0). In production,
                         this would be computed by guardian LLM.
        """
        if threat_score > cls.THREAT_THRESHOLD:
            return GateResult(
                gate_name="Adversarial Gate",
                passed=False,
                decision=BundleDecision.DEFER,
                reason=f"Adversarial pattern detected (threat_score: {threat_score:.2f})"
            )

        return GateResult(
            gate_name="Adversarial Gate",
            passed=True,
            decision=BundleDecision.PUBLISH,
            reason="No adversarial patterns detected"
        )


class HumanApprovalGate:
    """Gate 5: Human approval for high-risk actions."""

    # Tier -> (requires_approval, escalate_to)
    APPROVAL_MAP = {
        RiskTier.READ_ONLY: (False, None),
        RiskTier.WRITE_LIMITED: (False, None),
        RiskTier.MODIFY: (False, "audit_log"),
        RiskTier.DELETE: (True, "ops_team"),
        RiskTier.PRIVILEGE: (True, "security_team"),
    }

    @classmethod
    def evaluate(cls, bundle: ClaimBundle) -> GateResult:
        """Evaluate bundle for human approval requirements."""
        # Find max risk tier
        max_tier = max(
            (claim.risk_tier for claim in bundle.claims),
            default=RiskTier.READ_ONLY
        )

        requires_approval, escalate_to = cls.APPROVAL_MAP.get(
            max_tier,
            (True, "human_reviewer")
        )

        if requires_approval:
            return GateResult(
                gate_name="Human Approval Gate",
                passed=False,
                decision=BundleDecision.ESCALATE,
                reason=f"Action requires {escalate_to} approval",
                escalate_to=escalate_to
            )

        return GateResult(
            gate_name="Human Approval Gate",
            passed=True,
            decision=BundleDecision.PUBLISH,
            reason=f"Auto-approved (tier: {max_tier.value})"
        )


class GateStack:
    """Orchestrate all 5 gates in sequence."""

    GATES = [
        EvidenceGate,
        UncertaintyGate,
        SecurityGate,
        AdversarialGate,
        HumanApprovalGate,
    ]

    @classmethod
    def evaluate(cls, bundle: ClaimBundle) -> GateResult:
        """Run bundle through all gates."""
        for gate_class in cls.GATES:
            result = gate_class.evaluate(bundle)
            bundle.add_gate_result(result.gate_name, result.passed)

            if not result.passed:
                bundle.decision = result.decision
                bundle.reason = result.reason
                return result

        # All gates passed
        bundle.decision = BundleDecision.PUBLISH
        return GateResult(
            gate_name="GateStack",
            passed=True,
            decision=BundleDecision.PUBLISH,
            reason="All gates passed"
        )

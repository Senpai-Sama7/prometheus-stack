"""Tests for gate implementations."""

import pytest
import asyncio
from src.gates import (
    EvidenceGate,
    UncertaintyGate,
    SecurityGate,
    GateAction,
    ToolInvocation,
)
from src.claim_bundle import RiskTier


class TestEvidenceGate:
    """Test Evidence Gate."""

    @pytest.mark.asyncio
    async def test_evidence_gate_pass(self, sample_bundle_all_gates_pass):
        """Test Evidence Gate with valid evidence."""
        gate = EvidenceGate()
        decision = await gate.evaluate(sample_bundle_all_gates_pass)
        assert decision.action == GateAction.EXECUTE

    @pytest.mark.asyncio
    async def test_evidence_gate_fail_no_evidence(self, sample_claim_without_evidence):
        """Test Evidence Gate with no evidence."""
        from src.claim_bundle import ClaimBundle
        bundle = ClaimBundle(claims=[sample_claim_without_evidence])
        gate = EvidenceGate()
        decision = await gate.evaluate(bundle)
        assert decision.action == GateAction.REFUSE


class TestUncertaintyGate:
    """Test Uncertainty Gate."""

    @pytest.mark.asyncio
    async def test_uncertainty_gate_pass(self, sample_claim_with_evidence):
        """Test Uncertainty Gate with low uncertainty."""
        gate = UncertaintyGate()
        decision = await gate.evaluate(sample_claim_with_evidence)
        assert decision.action == GateAction.EXECUTE

    @pytest.mark.asyncio
    async def test_uncertainty_gate_defer(self, sample_high_uncertainty_claim):
        """Test Uncertainty Gate with high uncertainty."""
        gate = UncertaintyGate()
        decision = await gate.evaluate(sample_high_uncertainty_claim)
        assert decision.action == GateAction.DEFER


class TestSecurityGate:
    """Test Security Gate."""

    @pytest.mark.asyncio
    async def test_security_gate_permission_check(self):
        """Test Security Gate permission tier check."""
        gate = SecurityGate(
            tool_registry={
                "sensitive_tool": {"required_tier": RiskTier.MODIFY}
            },
            agent_permissions={
                "limited_agent": RiskTier.READ_ONLY
            }
        )
        invocation = ToolInvocation(
            tool_name="sensitive_tool",
            arguments={}
        )
        decision = await gate.evaluate(invocation, "limited_agent")
        assert decision.action == GateAction.REFUSE

    @pytest.mark.asyncio
    async def test_security_gate_pass(self):
        """Test Security Gate with valid permission."""
        gate = SecurityGate(
            tool_registry={
                "web_search": {"required_tier": RiskTier.READ_ONLY}
            },
            agent_permissions={
                "research_agent": RiskTier.READ_ONLY
            }
        )
        invocation = ToolInvocation(
            tool_name="web_search",
            arguments={}
        )
        decision = await gate.evaluate(invocation, "research_agent")
        assert decision.action == GateAction.EXECUTE

"""Tests for ExecutionOrchestrator."""

import pytest
import asyncio
from src.orchestrator import ExecutionOrchestrator
from src.claim_bundle import BundleDecision


class TestExecutionOrchestrator:
    """Test ExecutionOrchestrator."""

    @pytest.mark.asyncio
    async def test_execute_with_gates_all_pass(self, sample_bundle_all_gates_pass, orchestrator):
        """Test orchestrator with all gates passing."""
        result = await orchestrator.execute_with_gates(
            sample_bundle_all_gates_pass,
            agent_id="research_agent"
        )
        assert result.decision == BundleDecision.PUBLISH
        assert "evidence_gate" in result.audit_trail.gates_passed
        assert "uncertainty_gate" in result.audit_trail.gates_passed
        assert "security_gate" in result.audit_trail.gates_passed

    @pytest.mark.asyncio
    async def test_execute_with_gates_evidence_fails(
        self,
        sample_claim_without_evidence,
        orchestrator
    ):
        """Test orchestrator when Evidence Gate fails."""
        from src.claim_bundle import ClaimBundle
        bundle = ClaimBundle(claims=[sample_claim_without_evidence])
        result = await orchestrator.execute_with_gates(bundle, agent_id="research_agent")
        assert result.decision == BundleDecision.REFUSE
        assert "evidence_gate" in result.audit_trail.gates_failed

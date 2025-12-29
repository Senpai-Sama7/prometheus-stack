"""Pytest fixtures for PROMETHEUS tests."""

import pytest
from src.claim_bundle import (
    ClaimBundle,
    Claim,
    EvidencePointer,
    Uncertainty,
    ClaimType,
    RiskTier,
    UncertaintyMethod,
)
from src.audit_log import AuditLog
from src.mcp_registry import MCPToolRegistry
from src.orchestrator import ExecutionOrchestrator


@pytest.fixture
def audit_log():
    """Create audit log fixture."""
    return AuditLog()


@pytest.fixture
def mcp_registry():
    """Create MCP registry fixture with sample tools."""
    registry = MCPToolRegistry()
    registry.register_tool(
        name="web_search",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        },
        required_tier="READ_ONLY"
    )
    return registry


@pytest.fixture
def orchestrator():
    """Create orchestrator fixture."""
    return ExecutionOrchestrator()


@pytest.fixture
def sample_claim_with_evidence():
    """Create a claim with valid evidence."""
    return Claim(
        statement="Semantic entropy detects hallucinations",
        claim_type=ClaimType.FACT,
        evidence_pointers=[
            EvidencePointer(
                source="https://nature.com/articles/s41586-024-07421-0",
                source_confidence=0.85,
                evidence_hash="abc123"
            )
        ],
        uncertainty=Uncertainty(
            method=UncertaintyMethod.SEMANTIC_ENTROPY,
            value=0.30,
            interpretation="Strong empirical validation"
        ),
        risk_tier=RiskTier.READ_ONLY,
        if_wrong_cost="Hallucination detection fails"
    )


@pytest.fixture
def sample_claim_without_evidence():
    """Create a claim without evidence (will fail Evidence Gate)."""
    return Claim(
        statement="This claim has no evidence",
        claim_type=ClaimType.FACT,
        evidence_pointers=[],
        risk_tier=RiskTier.READ_ONLY
    )


@pytest.fixture
def sample_high_uncertainty_claim():
    """Create a claim with high uncertainty (will fail Uncertainty Gate)."""
    return Claim(
        statement="High uncertainty claim",
        claim_type=ClaimType.INFERENCE,
        uncertainty=Uncertainty(
            method=UncertaintyMethod.CONFIDENCE_SCORE,
            value=0.85,  # Above defer threshold
            interpretation="Very uncertain"
        )
    )


@pytest.fixture
def sample_bundle_all_gates_pass(sample_claim_with_evidence):
    """Create a bundle that passes all gates."""
    bundle = ClaimBundle(
        origin_agent="research_agent",
        claims=[sample_claim_with_evidence]
    )
    return bundle

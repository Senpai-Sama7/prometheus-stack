"""Tests for ClaimBundle and related classes."""

import pytest
import json
from src.claim_bundle import (
    ClaimBundle,
    Claim,
    EvidencePointer,
    Uncertainty,
    ClaimType,
    RiskTier,
    UncertaintyMethod,
)


class TestClaimBundle:
    """Test ClaimBundle serialization and validation."""

    def test_claim_bundle_creation(self):
        """Test creating a ClaimBundle."""
        bundle = ClaimBundle(origin_agent="test_agent")
        assert bundle.origin_agent == "test_agent"
        assert bundle.id is not None
        assert bundle.timestamp is not None

    def test_claim_bundle_to_dict(self, sample_bundle_all_gates_pass):
        """Test serializing ClaimBundle to dict."""
        bundle_dict = sample_bundle_all_gates_pass.to_dict()
        assert "id" in bundle_dict
        assert "claims" in bundle_dict
        assert "decision" in bundle_dict
        assert len(bundle_dict["claims"]) == 1

    def test_claim_bundle_to_json(self, sample_bundle_all_gates_pass):
        """Test serializing ClaimBundle to JSON."""
        json_str = sample_bundle_all_gates_pass.to_json()
        parsed = json.loads(json_str)
        assert "id" in parsed
        assert isinstance(parsed["claims"], list)

    def test_claim_creation(self, sample_claim_with_evidence):
        """Test creating a Claim."""
        assert sample_claim_with_evidence.statement == "Semantic entropy detects hallucinations"
        assert sample_claim_with_evidence.claim_type == ClaimType.FACT
        assert len(sample_claim_with_evidence.evidence_pointers) == 1

    def test_evidence_pointer_creation(self):
        """Test creating an EvidencePointer."""
        evidence = EvidencePointer(
            source="https://example.com",
            source_confidence=0.9,
            evidence_hash="abc123"
        )
        assert evidence.source == "https://example.com"
        assert evidence.source_confidence == 0.9

    def test_uncertainty_creation(self):
        """Test creating Uncertainty."""
        uncertainty = Uncertainty(
            method=UncertaintyMethod.SEMANTIC_ENTROPY,
            value=0.5,
            interpretation="Moderately uncertain"
        )
        assert uncertainty.method == UncertaintyMethod.SEMANTIC_ENTROPY
        assert uncertainty.value == 0.5

    def test_claim_type_enum(self):
        """Test ClaimType enum."""
        assert ClaimType.FACT.value == "FACT"
        assert ClaimType.INFERENCE.value == "INFERENCE"
        assert ClaimType.DECISION.value == "DECISION"

    def test_risk_tier_enum(self):
        """Test RiskTier enum."""
        tiers = [
            RiskTier.READ_ONLY,
            RiskTier.WRITE_LIMITED,
            RiskTier.MODIFY,
            RiskTier.DELETE,
            RiskTier.PRIVILEGE
        ]
        assert len(tiers) == 5

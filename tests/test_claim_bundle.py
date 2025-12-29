"""
Unit tests for ClaimBundle contract.

Validates:
- Dataclass initialization
- Evidence pointer validation
- Uncertainty quantification
- JSON serialization/deserialization
- Bundle validation logic
"""

import json
import pytest
from src.claim_bundle import (
    ClaimBundle, Claim, Uncertainty, EvidencePointer,
    ClaimType, UncertaintyMethod, GateRecommendation, RiskTier, BundleDecision
)


class TestEvidencePointer:
    """Test EvidencePointer dataclass."""

    def test_create_pointer(self):
        """Test basic pointer creation."""
        pointer = EvidencePointer(
            source="https://example.com",
            source_confidence=0.95,
            evidence_hash="abc123"
        )
        assert pointer.source == "https://example.com"
        assert pointer.source_confidence == 0.95
        assert pointer.evidence_hash == "abc123"
        assert pointer.retrieved_at is not None  # Should be set automatically

    def test_pointer_from_dict(self):
        """Test creating pointer from dict."""
        data = {
            "source": "https://nature.com",
            "source_confidence": 0.85,
            "evidence_hash": "def456"
        }
        pointer = EvidencePointer.from_dict(data)
        assert pointer.source == "https://nature.com"
        assert pointer.source_confidence == 0.85

    def test_pointer_confidence_validation(self):
        """Test confidence score validation."""
        with pytest.raises(ValueError):
            EvidencePointer(
                source="https://example.com",
                source_confidence=1.5,  # Invalid: > 1.0
                evidence_hash="abc"
            )
        with pytest.raises(ValueError):
            EvidencePointer(
                source="https://example.com",
                source_confidence=-0.1,  # Invalid: < 0.0
                evidence_hash="abc"
            )


class TestUncertainty:
    """Test Uncertainty dataclass."""

    def test_create_uncertainty(self):
        """Test basic uncertainty creation."""
        uncertainty = Uncertainty(
            method=UncertaintyMethod.SEMANTIC_ENTROPY,
            value=0.25
        )
        assert uncertainty.method == UncertaintyMethod.SEMANTIC_ENTROPY
        assert uncertainty.value == 0.25

    def test_uncertainty_value_validation(self):
        """Test uncertainty value validation."""
        with pytest.raises(ValueError):
            Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=1.5  # Invalid: > 1.0
            )

    def test_uncertainty_to_dict(self):
        """Test uncertainty serialization."""
        uncertainty = Uncertainty(
            method=UncertaintyMethod.MODEL_DISAGREEMENT,
            value=0.6,
            interpretation="Models disagreed",
            gate_recommendation=GateRecommendation.DEFER
        )
        data = uncertainty.to_dict()
        assert data["method"] == "model_disagreement"
        assert data["value"] == 0.6
        assert data["gate_recommendation"] == "DEFER"


class TestClaim:
    """Test Claim dataclass."""

    def test_create_fact_claim_with_evidence(self):
        """Test creating FACT claim with evidence."""
        claim = Claim(
            statement="PROMETHEUS uses semantic entropy",
            claim_type=ClaimType.FACT,
            evidence_pointers=[
                EvidencePointer(
                    source="https://nature.com/articles/s41586-024-07421-0",
                    source_confidence=0.95,
                    evidence_hash="bd24c2aa"
                )
            ],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.SEMANTIC_ENTROPY,
                value=0.15
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        assert claim.statement == "PROMETHEUS uses semantic entropy"
        assert claim.claim_type == ClaimType.FACT
        assert len(claim.evidence_pointers) == 1
        assert claim.evidence_pointers[0].source_confidence == 0.95

    def test_create_inference_claim(self):
        """Test creating INFERENCE claim (evidence optional)."""
        claim = Claim(
            statement="Therefore, semantic entropy works",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],  # Optional for INFERENCE
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.7
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        assert claim.claim_type == ClaimType.INFERENCE
        assert len(claim.evidence_pointers) == 0

    def test_validate_fact_without_evidence(self):
        """Test validation: FACT without evidence fails."""
        claim = Claim(
            statement="False claim",
            claim_type=ClaimType.FACT,
            evidence_pointers=[],  # Missing evidence
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        errors = claim.validate()
        assert len(errors) > 0
        assert "no evidence" in errors[0].lower()

    def test_validate_fact_with_weak_evidence(self):
        """Test validation: FACT with weak evidence fails."""
        claim = Claim(
            statement="Weak evidence claim",
            claim_type=ClaimType.FACT,
            evidence_pointers=[
                EvidencePointer(
                    source="https://example.com",
                    source_confidence=0.50,  # Below 0.60 threshold
                    evidence_hash="weak"
                )
            ],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        errors = claim.validate()
        assert len(errors) > 0

    def test_claim_to_dict(self):
        """Test claim serialization."""
        claim = Claim(
            statement="Test claim",
            claim_type=ClaimType.FACT,
            evidence_pointers=[
                EvidencePointer(
                    source="https://test.com",
                    source_confidence=0.9,
                    evidence_hash="test123"
                )
            ],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.SEMANTIC_ENTROPY,
                value=0.2
            ),
            risk_tier=RiskTier.MODIFY,
            if_wrong_cost="User state affected"
        )
        data = claim.to_dict()
        assert data["statement"] == "Test claim"
        assert data["claim_type"] == "FACT"
        assert len(data["evidence_pointers"]) == 1
        assert data["risk_tier"] == "MODIFY"


class TestClaimBundle:
    """Test ClaimBundle dataclass."""

    def test_create_bundle(self):
        """Test basic bundle creation."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(
            origin_agent="test_agent",
            claims=[claim]
        )
        assert bundle.origin_agent == "test_agent"
        assert len(bundle.claims) == 1
        assert bundle.id is not None
        assert bundle.timestamp is not None

    def test_bundle_json_serialization(self):
        """Test bundle JSON serialization."""
        claim = Claim(
            statement="Semantic entropy AUROC >= 0.75",
            claim_type=ClaimType.FACT,
            evidence_pointers=[
                EvidencePointer(
                    source="https://nature.com/articles/s41586-024-07421-0",
                    source_confidence=0.95,
                    evidence_hash="bd24c2aa"
                )
            ],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.SEMANTIC_ENTROPY,
                value=0.15
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(
            origin_agent="research_agent",
            claims=[claim],
            reason="Testing semantic entropy"
        )
        json_str = bundle.to_json()
        data = json.loads(json_str)
        
        assert data["origin_agent"] == "research_agent"
        assert data["reason"] == "Testing semantic entropy"
        assert len(data["claims"]) == 1
        assert data["claims"][0]["statement"] == "Semantic entropy AUROC >= 0.75"

    def test_bundle_json_deserialization(self):
        """Test bundle JSON deserialization."""
        original = ClaimBundle(
            origin_agent="agent",
            claims=[
                Claim(
                    statement="Test",
                    claim_type=ClaimType.INFERENCE,
                    evidence_pointers=[],
                    uncertainty=Uncertainty(
                        method=UncertaintyMethod.CONFIDENCE_SCORE,
                        value=0.5
                    ),
                    risk_tier=RiskTier.READ_ONLY
                )
            ]
        )
        json_str = original.to_json()
        restored = ClaimBundle.from_json(json_str)
        
        assert restored.origin_agent == original.origin_agent
        assert len(restored.claims) == len(original.claims)
        assert restored.claims[0].statement == original.claims[0].statement

    def test_bundle_validation(self):
        """Test bundle validation."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.FACT,
            evidence_pointers=[],  # Missing evidence
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(
            origin_agent="test",
            claims=[claim]
        )
        errors = bundle.validate()
        assert len(errors) > 0

    def test_add_gate_result(self):
        """Test adding gate results to audit trail."""
        bundle = ClaimBundle(
            origin_agent="test",
            claims=[]
        )
        bundle.add_gate_result("Evidence Gate", True)
        bundle.add_gate_result("Security Gate", False)
        
        assert "Evidence Gate" in bundle.audit_trail["gates_passed"]
        assert "Security Gate" in bundle.audit_trail["gates_failed"]

    def test_add_human_approval(self):
        """Test adding human approval to audit trail."""
        bundle = ClaimBundle(
            origin_agent="test",
            claims=[]
        )
        bundle.add_human_approval(
            approver="alice@example.com",
            decision="APPROVED",
            reason="Verified evidence"
        )
        
        assert len(bundle.audit_trail["human_approvals"]) == 1
        assert bundle.audit_trail["human_approvals"][0]["approver"] == "alice@example.com"
        assert bundle.audit_trail["human_approvals"][0]["decision"] == "APPROVED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

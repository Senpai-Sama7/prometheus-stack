"""
Unit tests for gate implementations.

Validates:
- Evidence Gate (FACT claims must have sources)
- Uncertainty Gate (defer high-uncertainty claims)
- Security Gate (privilege hierarchy)
- Adversarial Gate (anomaly detection)
- Human Approval Gate (high-risk actions)
- GateStack orchestration
"""

import pytest
from src.claim_bundle import (
    ClaimBundle, Claim, Uncertainty, EvidencePointer,
    ClaimType, UncertaintyMethod, GateRecommendation, RiskTier, BundleDecision
)
from src.gates import (
    EvidenceGate, UncertaintyGate, SecurityGate, AdversarialGate,
    HumanApprovalGate, GateStack
)


class TestEvidenceGate:
    """Test Evidence Gate."""

    def test_fact_claim_with_evidence_passes(self):
        """FACT claim with strong evidence should pass."""
        claim = Claim(
            statement="Test fact",
            claim_type=ClaimType.FACT,
            evidence_pointers=[
                EvidencePointer(
                    source="https://example.com",
                    source_confidence=0.95,
                    evidence_hash="abc"
                )
            ],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.2
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = EvidenceGate.evaluate(bundle)
        assert result.passed is True
        assert result.decision == BundleDecision.PUBLISH

    def test_fact_claim_without_evidence_fails(self):
        """FACT claim without evidence should fail."""
        claim = Claim(
            statement="Unsupported fact",
            claim_type=ClaimType.FACT,
            evidence_pointers=[],  # Missing!
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = EvidenceGate.evaluate(bundle)
        assert result.passed is False
        assert result.decision == BundleDecision.REFUSE

    def test_fact_claim_with_weak_evidence_defers(self):
        """FACT with confidence < 0.60 should defer."""
        claim = Claim(
            statement="Weak fact",
            claim_type=ClaimType.FACT,
            evidence_pointers=[
                EvidencePointer(
                    source="https://example.com",
                    source_confidence=0.50,  # Below threshold
                    evidence_hash="weak"
                )
            ],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = EvidenceGate.evaluate(bundle)
        assert result.passed is False
        assert result.decision == BundleDecision.DEFER

    def test_inference_without_evidence_passes(self):
        """INFERENCE claims don't require evidence."""
        claim = Claim(
            statement="Inference",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],  # OK for INFERENCE
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = EvidenceGate.evaluate(bundle)
        assert result.passed is True


class TestUncertaintyGate:
    """Test Uncertainty Gate."""

    def test_low_uncertainty_executes(self):
        """Uncertainty < 0.50 should execute."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.30
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = UncertaintyGate.evaluate(bundle)
        assert result.passed is True
        assert result.decision == BundleDecision.PUBLISH

    def test_moderate_uncertainty_explains(self):
        """0.50 < uncertainty < 0.75 should EXPLAIN."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.65
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = UncertaintyGate.evaluate(bundle)
        assert result.passed is True
        assert "caveats" in result.reason.lower() or "explain" in result.reason.lower()

    def test_high_uncertainty_defers(self):
        """Uncertainty > 0.75 should DEFER."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.82
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = UncertaintyGate.evaluate(bundle)
        assert result.passed is False
        assert result.decision == BundleDecision.DEFER


class TestSecurityGate:
    """Test Security Gate."""

    def test_read_only_tier_always_passes(self):
        """READ_ONLY tier should always pass."""
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
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = SecurityGate.evaluate(bundle, agent_tier=0)  # Lowest tier
        assert result.passed is True

    def test_privilege_escalation_blocked(self):
        """Agent can't access PRIVILEGE tier if tier < 4."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.DECISION,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.PRIVILEGE
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = SecurityGate.evaluate(bundle, agent_tier=2)  # Mid tier
        assert result.passed is False
        assert result.decision == BundleDecision.REFUSE

    def test_privilege_tier_agent_can_access_all(self):
        """Agent with tier 4 can access PRIVILEGE operations."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.DECISION,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.PRIVILEGE
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = SecurityGate.evaluate(bundle, agent_tier=4)  # Max tier
        assert result.passed is True


class TestAdversarialGate:
    """Test Adversarial Gate."""

    def test_low_threat_passes(self):
        """Low threat score should pass."""
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
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = AdversarialGate.evaluate(bundle, threat_score=0.3)
        assert result.passed is True

    def test_high_threat_defers(self):
        """High threat score (> 0.70) should defer."""
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
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = AdversarialGate.evaluate(bundle, threat_score=0.85)
        assert result.passed is False
        assert result.decision == BundleDecision.DEFER


class TestHumanApprovalGate:
    """Test Human Approval Gate."""

    def test_read_only_auto_approved(self):
        """READ_ONLY tier should auto-approve."""
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
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = HumanApprovalGate.evaluate(bundle)
        assert result.passed is True

    def test_write_limited_auto_approved(self):
        """WRITE_LIMITED tier should auto-approve."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.DECISION,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.WRITE_LIMITED
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = HumanApprovalGate.evaluate(bundle)
        assert result.passed is True

    def test_delete_requires_approval(self):
        """DELETE tier should require approval."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.DECISION,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.DELETE
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = HumanApprovalGate.evaluate(bundle)
        assert result.passed is False
        assert result.decision == BundleDecision.ESCALATE

    def test_privilege_requires_approval(self):
        """PRIVILEGE tier should require approval."""
        claim = Claim(
            statement="Test",
            claim_type=ClaimType.DECISION,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.PRIVILEGE
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = HumanApprovalGate.evaluate(bundle)
        assert result.passed is False
        assert result.decision == BundleDecision.ESCALATE
        assert result.escalate_to == "security_team"


class TestGateStack:
    """Test GateStack orchestration."""

    def test_all_gates_pass(self):
        """Valid bundle should pass all gates."""
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
        bundle = ClaimBundle(origin_agent="research_agent", claims=[claim])
        result = GateStack.evaluate(bundle)
        assert result.passed is True
        assert bundle.decision == BundleDecision.PUBLISH
        assert len(bundle.audit_trail["gates_passed"]) > 0

    def test_gate_stops_on_first_failure(self):
        """Should stop at first failing gate."""
        claim = Claim(
            statement="Unsupported fact",
            claim_type=ClaimType.FACT,
            evidence_pointers=[],  # Missing evidence
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        result = GateStack.evaluate(bundle)
        assert result.passed is False
        assert bundle.decision == BundleDecision.REFUSE
        assert "Evidence Gate" in bundle.audit_trail["gates_failed"]

    def test_complex_bundle_sequence(self):
        """Test realistic bundle with multiple claims."""
        claims = [
            Claim(
                statement="Fact 1",
                claim_type=ClaimType.FACT,
                evidence_pointers=[
                    EvidencePointer(
                        source="https://source1.com",
                        source_confidence=0.9,
                        evidence_hash="hash1"
                    )
                ],
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.SEMANTIC_ENTROPY,
                    value=0.2
                ),
                risk_tier=RiskTier.READ_ONLY
            ),
            Claim(
                statement="Inference from Fact 1",
                claim_type=ClaimType.INFERENCE,
                evidence_pointers=[],
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.CONFIDENCE_SCORE,
                    value=0.4
                ),
                risk_tier=RiskTier.READ_ONLY
            )
        ]
        bundle = ClaimBundle(origin_agent="test", claims=claims)
        result = GateStack.evaluate(bundle)
        assert result.passed is True
        assert bundle.decision == BundleDecision.PUBLISH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Phase 2 Acceptance Tests: Uncertainty Gate.

Acceptance Metrics:
- Hallucination detection AUROC >= 0.75 (H001)
- 5-15% defer rate
- Zero crashes
"""

import pytest
from src.gates import UncertaintyGate, GateResult
from src.claim_bundle import (
    ClaimBundle, Claim, Uncertainty, EvidencePointer,
    ClaimType, UncertaintyMethod, RiskTier, BundleDecision
)


class TestPhase2HallucinationDetection:
    """Test Phase 2 acceptance criteria."""

    def test_uncertainty_gate_defer_rate(self):
        """Test: Defer rate is 5-15% (appropriate, not 0% or 90%)."""
        gate = UncertaintyGate()
        
        # Create 100 claims with varying uncertainty
        defer_count = 0
        for i in range(100):
            claim = Claim(
                statement=f"Test claim {i}",
                claim_type=ClaimType.INFERENCE,
                evidence_pointers=[],
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.CONFIDENCE_SCORE,
                    value=0.5 + (i / 200)  # 0.5 to 1.0
                ),
                risk_tier=RiskTier.READ_ONLY
            )
            bundle = ClaimBundle(origin_agent="test", claims=[claim])
            result = gate.evaluate(bundle)
            if result.decision == BundleDecision.DEFER:
                defer_count += 1
        
        defer_rate = defer_count / 100
        # Should be between 5-15%
        assert 0.05 <= defer_rate <= 0.15, f"Defer rate {defer_rate} outside 5-15% target"

    def test_uncertainty_gate_no_crashes(self):
        """Test: Gate doesn't crash on edge cases."""
        gate = UncertaintyGate()
        
        # Edge cases
        claims = [
            Claim(
                statement="Extreme low",
                claim_type=ClaimType.INFERENCE,
                evidence_pointers=[],
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.CONFIDENCE_SCORE,
                    value=0.0
                ),
                risk_tier=RiskTier.READ_ONLY
            ),
            Claim(
                statement="Extreme high",
                claim_type=ClaimType.INFERENCE,
                evidence_pointers=[],
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.CONFIDENCE_SCORE,
                    value=1.0
                ),
                risk_tier=RiskTier.READ_ONLY
            ),
            Claim(
                statement="Semantic entropy",
                claim_type=ClaimType.INFERENCE,
                evidence_pointers=[],
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.SEMANTIC_ENTROPY,
                    value=0.5
                ),
                risk_tier=RiskTier.READ_ONLY
            ),
        ]
        
        for claim in claims:
            bundle = ClaimBundle(origin_agent="test", claims=[claim])
            result = gate.evaluate(bundle)
            assert isinstance(result, GateResult)
            assert result.decision is not None

"""Phase 2 Acceptance Tests: Uncertainty Gate.

Acceptance Metrics:
- Hallucination detection AUROC >= 0.75 (H001)
- 5-15% defer rate
- Zero crashes
"""

import pytest
from src.gates import UncertaintyGate, GateAction
from src.claim_bundle import Claim, Uncertainty, UncertaintyMethod


class TestPhase2HallucinationDetection:
    """Test Phase 2 acceptance criteria."""

    @pytest.mark.asyncio
    async def test_uncertainty_gate_defer_rate(self):
        """Test: Defer rate is 5-15% (appropriate, not 0% or 90%)."""
        gate = UncertaintyGate()
        
        # Create 100 claims with varying uncertainty
        defer_count = 0
        for i in range(100):
            claim = Claim(
                statement=f"Test claim {i}",
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.CONFIDENCE_SCORE,
                    value=0.5 + (i / 200)  # 0.5 to 1.0
                )
            )
            decision = await gate.evaluate(claim)
            if decision.action == GateAction.DEFER:
                defer_count += 1
        
        defer_rate = defer_count / 100
        # Should be between 5-15%
        assert 0.05 <= defer_rate <= 0.15, f"Defer rate {defer_rate} outside 5-15% target"

    @pytest.mark.asyncio
    async def test_uncertainty_gate_no_crashes(self):
        """Test: Gate doesn't crash on edge cases."""
        gate = UncertaintyGate()
        
        # Edge cases
        claims = [
            Claim(uncertainty=Uncertainty(method=UncertaintyMethod.CONFIDENCE_SCORE, value=0.0)),
            Claim(uncertainty=Uncertainty(method=UncertaintyMethod.CONFIDENCE_SCORE, value=1.0)),
            Claim(uncertainty=Uncertainty(method=UncertaintyMethod.SEMANTIC_ENTROPY, value=0.5)),
        ]
        
        for claim in claims:
            decision = await gate.evaluate(claim)
            assert decision.action is not None

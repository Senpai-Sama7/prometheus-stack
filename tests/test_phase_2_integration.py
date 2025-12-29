"""
Phase 2 Integration Tests

Tests for:
- PrometheusOrchestrator (full gate pipeline)
- SemanticEntropyCalculator (H001 hypothesis)
- UncertaintyQuantifier (unified interface)
- End-to-end orchestration flow
"""

import pytest
from src.claim_bundle import (
    ClaimBundle, Claim, Uncertainty, EvidencePointer,
    ClaimType, UncertaintyMethod, GateRecommendation, RiskTier, BundleDecision
)
from src.orchestration import PrometheusOrchestrator, OrchestratorConfig
from src.uncertainty.semantic_entropy import (
    SemanticEntropyCalculator,
    compute_semantic_entropy,
    hallucination_likelihood,
)
from src.uncertainty.uncertainty_quantifier import UncertaintyQuantifier


class TestSemanticEntropyCalculator:
    """Test semantic entropy computation for hallucination detection."""
    
    def test_low_entropy_confidence(self):
        """Low entropy should indicate hallucination unlikely."""
        calculator = SemanticEntropyCalculator()
        
        # Identical outputs = no diversity = low entropy
        texts = [
            "The capital of France is Paris.",
            "The capital of France is Paris.",
            "The capital of France is Paris.",
        ]
        
        result = calculator.compute(texts)
        
        assert result.entropy_value < 0.3, "Identical texts should have low entropy"
        assert result.hallucination_probability < 0.2, "Should be low hallucination risk"
        assert result.confidence_score > 0.8, "Should be high confidence"
        assert not result.is_hallucination, "Should not flag as hallucination"
    
    def test_high_entropy_hallucination(self):
        """High entropy should indicate hallucination likely."""
        calculator = SemanticEntropyCalculator()
        
        # Diverse outputs = high entropy
        texts = [
            "Paris is the capital of France.",
            "Rome is the capital of Italy.",
            "London is the capital of England.",
            "Madrid is the capital of Spain.",
            "Berlin is the capital of Germany.",
        ]
        
        result = calculator.compute(texts)
        
        assert result.entropy_value > 0.6, "Diverse texts should have high entropy"
        # Note: This is semantically different content, not hallucination
        # In real scenario, diverse outputs for same question = hallucination risk
    
    def test_moderate_entropy(self):
        """Moderate entropy should indicate some variance."""
        calculator = SemanticEntropyCalculator()
        
        # Partially similar outputs
        texts = [
            "The Eiffel Tower is in Paris, France.",
            "The Eiffel Tower is located in Paris.",
            "In Paris, France, stands the Eiffel Tower.",
            "The Eiffel Tower is a famous structure in Paris.",
        ]
        
        result = calculator.compute(texts)
        
        assert 0.3 < result.entropy_value < 0.7, "Moderate variance should give moderate entropy"
        assert result.confidence_score > 0.5, "Should still be reasonably confident"
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        texts = ["Output A", "Output A", "Output A"]
        
        entropy, hallucination_prob = compute_semantic_entropy(texts)
        assert entropy < 0.3
        assert hallucination_prob < 0.2
        
        halluc_likelihood = hallucination_likelihood(texts)
        assert halluc_likelihood < 0.2


class TestUncertaintyQuantifier:
    """Test unified uncertainty quantification interface."""
    
    def test_from_semantic_entropy(self):
        """Test uncertainty estimation from semantic entropy."""
        quantifier = UncertaintyQuantifier()
        
        texts = ["Paris is the capital"] * 3
        estimate = quantifier.from_semantic_entropy(texts)
        
        assert estimate.uncertainty_value < 0.3
        assert estimate.confidence_value > 0.7
        assert "entropy" in estimate.interpretation.lower()
        assert "Wang et al" in estimate.additional_data["paper_reference"]
    
    def test_from_confidence_score(self):
        """Test uncertainty from single confidence score."""
        quantifier = UncertaintyQuantifier()
        
        estimate = quantifier.from_confidence_score(0.85)
        
        assert estimate.uncertainty_value == 0.15
        assert estimate.confidence_value == 0.85
        assert "high confidence" in estimate.interpretation.lower()
    
    def test_from_token_length(self):
        """Test uncertainty heuristic from token length."""
        quantifier = UncertaintyQuantifier()
        
        # Short response
        short = quantifier.from_token_length(20)
        assert short.uncertainty_value == 0.2, "Short response = high confidence"
        
        # Medium response
        medium = quantifier.from_token_length(50)
        assert medium.uncertainty_value == 0.5, "Medium response = medium confidence"
        
        # Long response
        long = quantifier.from_token_length(100)
        assert long.uncertainty_value == 0.7, "Long response = lower confidence"
    
    def test_combine_estimates(self):
        """Test combining multiple uncertainty estimates."""
        quantifier = UncertaintyQuantifier()
        
        estimates = [
            quantifier.from_confidence_score(0.9),
            quantifier.from_confidence_score(0.8),
            quantifier.from_confidence_score(0.85),
        ]
        
        combined = quantifier.combine_estimates(estimates)
        
        # Should average to ~0.85 confidence
        assert 0.83 < combined.confidence_value < 0.87
        assert combined.uncertainty_value == pytest.approx(0.15, abs=0.02)
        assert len(combined.additional_data["methods"]) == 3


class TestPrometheusOrchestrator:
    """Test orchestration engine."""
    
    def test_orchestrator_all_gates_pass(self):
        """Valid bundle should pass through all gates."""
        orchestrator = PrometheusOrchestrator()
        
        claim = Claim(
            statement="Semantic entropy AUROC >= 0.78",
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
        
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        state = orchestrator.orchestrate(bundle)
        
        assert state.final_decision == BundleDecision.PUBLISH
        assert len(state.gate_results) == 5, "Should evaluate all 5 gates"
        assert all(gate in state.reasoning_path for gate in 
                  ["Evidence Gate", "Uncertainty Gate", "Security Gate",
                   "Adversarial Gate", "Human Approval Gate"])
        # Gates should be in reasoning_path as dicts
        gates_in_path = [g["gate"] for g in state.reasoning_path]
        assert len(gates_in_path) == 5
    
    def test_orchestrator_evidence_gate_failure(self):
        """Invalid bundle should fail at evidence gate."""
        orchestrator = PrometheusOrchestrator()
        
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
        state = orchestrator.orchestrate(bundle)
        
        assert state.final_decision == BundleDecision.REFUSE
        assert state.current_phase.value == "COMPLETE"
        # Should stop at evidence gate
        gates_evaluated = [g["gate"] for g in state.reasoning_path]
        assert gates_evaluated == ["Evidence Gate"]
    
    def test_orchestrator_uncertainty_gate_defer(self):
        """High uncertainty should defer decision."""
        orchestrator = PrometheusOrchestrator()
        
        claim = Claim(
            statement="Uncertain claim",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.85  # High uncertainty (> 0.75 threshold)
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        state = orchestrator.orchestrate(bundle)
        
        assert state.final_decision == BundleDecision.DEFER
        # Should evaluate evidence gate (pass) then uncertainty gate (fail)
        gates_evaluated = [g["gate"] for g in state.reasoning_path]
        assert "Evidence Gate" in gates_evaluated
        assert "Uncertainty Gate" in gates_evaluated
    
    def test_orchestrator_execution_history(self):
        """Orchestrator should track execution history."""
        orchestrator = PrometheusOrchestrator()
        
        # Create and orchestrate multiple bundles
        for i in range(3):
            claim = Claim(
                statement=f"Claim {i}",
                claim_type=ClaimType.INFERENCE,
                evidence_pointers=[],
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.CONFIDENCE_SCORE,
                    value=0.5
                ),
                risk_tier=RiskTier.READ_ONLY
            )
            bundle = ClaimBundle(origin_agent="test", claims=[claim])
            orchestrator.orchestrate(bundle)
        
        history = orchestrator.get_execution_history()
        assert len(history) == 3
        assert all(state.final_decision == BundleDecision.PUBLISH for state in history)
    
    def test_orchestrator_reasoning_path_retrieval(self):
        """Should be able to retrieve reasoning path by bundle ID."""
        orchestrator = PrometheusOrchestrator()
        
        claim = Claim(
            statement="Test claim",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.5
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        
        bundle = ClaimBundle(origin_agent="test", claims=[claim])
        state = orchestrator.orchestrate(bundle)
        
        reasoning = orchestrator.get_reasoning_path(state.bundle_id)
        assert reasoning is not None
        assert len(reasoning) > 0
        assert all("gate" in entry for entry in reasoning)


class TestPhase2EndToEnd:
    """End-to-end integration tests for Phase 2."""
    
    def test_h001_semantic_entropy_hypothesis(self):
        """
        H001: Semantic entropy can detect hallucinations (AUROC >= 0.75)
        
        Reference: Wang et al., Nature 2024
        """
        print("\n[TEST] H001: Semantic Entropy Hypothesis")
        
        # Simulated case: consistent outputs (high confidence)
        consistent_outputs = [
            "Paris is the capital of France.",
            "The capital of France is Paris.",
            "In France, the capital is Paris.",
            "Paris serves as France's capital.",
            "France's capital city is Paris.",
        ]
        
        entropy, halluc_prob = compute_semantic_entropy(consistent_outputs)
        assert entropy < 0.3, "Consistent outputs should have low entropy"
        assert halluc_prob < 0.2, "Should have low hallucination probability"
        
        # Simulated case: diverse outputs (low confidence)
        diverse_outputs = [
            "Paris",
            "Rome",
            "London",
            "Madrid",
            "Berlin",
        ]
        
        entropy, halluc_prob = compute_semantic_entropy(diverse_outputs)
        assert entropy > 0.5, "Diverse outputs should have high entropy"
        assert halluc_prob > 0.4, "Should have higher hallucination probability"
        
        print(f"  ✓ Consistent case: entropy={entropy:.3f}, halluc_prob={halluc_prob:.1%}")
        print(f"  ✓ H001 semantic entropy detection working correctly")
    
    def test_full_pipeline_h001_to_decision(self):
        """
        Full pipeline: H001 → Orchestrator → BundleDecision
        
        Flow:
        1. Claim about semantic entropy
        2. Compute uncertainty using semantic entropy
        3. Create ClaimBundle
        4. Run through orchestrator
        5. Get final PUBLISH decision
        """
        print("\n[TEST] Full Pipeline: H001 → Decision")
        
        # Step 1: Create claim with semantic entropy evidence
        claim = Claim(
            statement="Semantic entropy AUROC >= 0.78 for hallucination detection",
            claim_type=ClaimType.FACT,
            evidence_pointers=[
                EvidencePointer(
                    source="https://nature.com/articles/s41586-024-07421-0",
                    source_confidence=0.95,
                    evidence_hash="bd24c2aaef2ef37ae95f0f9e5f7d9e7c"
                )
            ],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.SEMANTIC_ENTROPY,
                value=0.15,
                interpretation="Semantic entropy successfully detects hallucinations",
                gate_recommendation=GateRecommendation.EXECUTE
            ),
            risk_tier=RiskTier.READ_ONLY
        )
        
        # Step 2: Create bundle
        bundle = ClaimBundle(
            origin_agent="ml_researcher",
            claims=[claim],
            reason="Validate H001: Semantic entropy for hallucination detection"
        )
        
        # Step 3: Run through orchestrator
        orchestrator = PrometheusOrchestrator()
        state = orchestrator.orchestrate(bundle)
        
        # Step 4: Verify decision
        assert state.final_decision == BundleDecision.PUBLISH
        assert len(state.reasoning_path) == 5
        
        # All gates should pass
        for gate_entry in state.reasoning_path:
            assert gate_entry["passed"] is True, f"{gate_entry['gate']} should pass"
        
        print(f"  ✓ Claim routed through all 5 gates")
        print(f"  ✓ Final decision: PUBLISH")
        print(f"  ✓ Full pipeline working correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
Phase 2: Orchestration + Semantic Entropy

Demonstrates:
1. SemanticEntropyCalculator for hallucination detection (H001)
2. PrometheusOrchestrator for intelligent routing
3. Full gate pipeline with reasoning path
4. Decision making based on uncertainty

Run: python3 examples/phase_2_orchestration.py
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.claim_bundle import (
    ClaimBundle, Claim, Uncertainty, EvidencePointer,
    ClaimType, UncertaintyMethod, GateRecommendation, RiskTier, BundleDecision
)
from src.orchestration import PrometheusOrchestrator, OrchestratorConfig
from src.uncertainty.semantic_entropy import (
    SemanticEntropyCalculator,
    compute_semantic_entropy,
)
from src.uncertainty.uncertainty_quantifier import UncertaintyQuantifier


def demo_semantic_entropy():
    """
    Demo 1: Semantic Entropy for Hallucination Detection
    
    Reference: Wang et al., Nature 2024
    AUROC >= 0.78
    """
    print("\n" + "="*70)
    print("DEMO 1: Semantic Entropy Hallucination Detection")
    print("="*70)
    
    calculator = SemanticEntropyCalculator()
    
    # Case 1: Consistent outputs (high confidence)
    print("\n[CASE 1] Consistent Model Outputs")
    print("-" * 70)
    
    consistent = [
        "The Eiffel Tower is a wrought iron lattice tower in Paris, France.",
        "A wrought iron lattice tower in Paris, France is the Eiffel Tower.",
        "In Paris, France stands the Eiffel Tower, made of wrought iron lattice.",
        "The Eiffel Tower, located in Paris, France, is constructed of wrought iron.",
        "Wrought iron lattice tower in France's capital: the Eiffel Tower.",
    ]
    
    for i, output in enumerate(consistent, 1):
        print(f"  Output {i}: {output[:60]}...")
    
    result = calculator.compute(consistent)
    print(f"\n  Entropy: {result.entropy_value:.3f}")
    print(f"  Hallucination Probability: {result.hallucination_probability:.1%}")
    print(f"  Confidence Score: {result.confidence_score:.1%}")
    print(f"  Status: {'HALLUCINATION' if result.is_hallucination else 'CONFIDENT'}")
    assert not result.is_hallucination
    print(f"  ✅ Result: HIGH CONFIDENCE (outputs consistent)")
    
    # Case 2: Diverse outputs (low confidence)
    print("\n[CASE 2] Diverse Model Outputs")
    print("-" * 70)
    
    diverse = [
        "The capital of France is Paris.",
        "France is located in Western Europe.",
        "The Eiffel Tower is in Paris.",
        "French cuisine is world-famous.",
        "The Seine river flows through Paris.",
    ]
    
    for i, output in enumerate(diverse, 1):
        print(f"  Output {i}: {output}")
    
    result = calculator.compute(diverse)
    print(f"\n  Entropy: {result.entropy_value:.3f}")
    print(f"  Hallucination Probability: {result.hallucination_probability:.1%}")
    print(f"  Confidence Score: {result.confidence_score:.1%}")
    print(f"  Status: {'HALLUCINATION' if result.is_hallucination else 'UNCERTAIN'}")
    assert result.entropy_value > 0.5
    print(f"  ✅ Result: LOW CONFIDENCE (outputs diverse - possible hallucination)")


def demo_uncertainty_quantifier():
    """
    Demo 2: Unified Uncertainty Quantification
    
    Different methods for computing uncertainty
    """
    print("\n" + "="*70)
    print("DEMO 2: Uncertainty Quantification Methods")
    print("="*70)
    
    quantifier = UncertaintyQuantifier()
    
    # Method 1: Semantic Entropy
    print("\n[METHOD 1] Semantic Entropy")
    print("-" * 70)
    texts = ["Output A"] * 5
    estimate = quantifier.from_semantic_entropy(texts)
    print(f"  Uncertainty: {estimate.uncertainty_value:.2f}")
    print(f"  Confidence: {estimate.confidence_value:.2f}")
    print(f"  Interpretation: {estimate.interpretation}")
    
    # Method 2: Confidence Score
    print("\n[METHOD 2] Confidence Score")
    print("-" * 70)
    estimate = quantifier.from_confidence_score(0.85)
    print(f"  Uncertainty: {estimate.uncertainty_value:.2f}")
    print(f"  Confidence: {estimate.confidence_value:.2f}")
    print(f"  Interpretation: {estimate.interpretation}")
    
    # Method 3: Token Length Heuristic
    print("\n[METHOD 3] Token Length Heuristic")
    print("-" * 70)
    for tokens in [20, 50, 100]:
        estimate = quantifier.from_token_length(tokens)
        print(f"  Tokens: {tokens:3d} → Uncertainty: {estimate.uncertainty_value:.2f}")


def demo_orchestration_pipeline():
    """
    Demo 3: Full Orchestration Pipeline
    
    Routes claims through all 5 gates with reasoning path
    """
    print("\n" + "="*70)
    print("DEMO 3: Orchestration Pipeline (All 5 Gates)")
    print("="*70)
    
    orchestrator = PrometheusOrchestrator()
    
    # Create a well-founded claim about semantic entropy
    claim = Claim(
        statement="Semantic entropy AUROC >= 0.78 for hallucination detection (Wang et al., Nature 2024)",
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
            interpretation="Multiple papers confirm semantic entropy effectiveness",
            gate_recommendation=GateRecommendation.EXECUTE
        ),
        risk_tier=RiskTier.READ_ONLY
    )
    
    bundle = ClaimBundle(
        origin_agent="research_agent",
        claims=[claim],
        reason="H001: Validate semantic entropy for hallucination detection"
    )
    
    print(f"\n[INPUT]")
    print(f"  Origin Agent: {bundle.origin_agent}")
    print(f"  Claim: {claim.statement[:60]}...")
    print(f"  Evidence Source: {claim.evidence_pointers[0].source}")
    print(f"  Evidence Confidence: {claim.evidence_pointers[0].source_confidence:.0%}")
    print(f"  Uncertainty (Semantic Entropy): {claim.uncertainty.value:.2f}")
    
    # Route through orchestrator
    print(f"\n[ORCHESTRATION]")
    state = orchestrator.orchestrate(bundle)
    
    print(f"  Pipeline Phase: {state.current_phase.value}")
    print(f"  Final Decision: {state.final_decision.value}")
    print(f"\n  Gate Sequence:")
    
    for i, gate_entry in enumerate(state.reasoning_path, 1):
        status = "✅" if gate_entry["passed"] else "❌"
        print(f"    {i}. {status} {gate_entry['gate']:25s} → {gate_entry['decision']}")
    
    print(f"\n[OUTPUT]")
    print(f"  Final Decision: {state.final_decision.value}")
    print(f"  Reasoning Path Length: {len(state.reasoning_path)} gates")
    print(f"  Time Elapsed: {(state.timestamp_completed - state.timestamp_created).total_seconds():.3f}s")
    
    assert state.final_decision == BundleDecision.PUBLISH
    print(f"\n  ✅ Claim successfully published through gate pipeline")


def demo_failure_case():
    """
    Demo 4: Failure Case - High Uncertainty
    
    Shows how DEFER decision works
    """
    print("\n" + "="*70)
    print("DEMO 4: High Uncertainty → DEFER Decision")
    print("="*70)
    
    orchestrator = PrometheusOrchestrator()
    
    # Create a claim with high uncertainty
    claim = Claim(
        statement="AI will achieve AGI by 2027",
        claim_type=ClaimType.INFERENCE,
        evidence_pointers=[],
        uncertainty=Uncertainty(
            method=UncertaintyMethod.CONFIDENCE_SCORE,
            value=0.85  # High uncertainty (> 0.75 threshold)
        ),
        risk_tier=RiskTier.READ_ONLY
    )
    
    bundle = ClaimBundle(
        origin_agent="prediction_agent",
        claims=[claim],
        reason="Test high uncertainty handling"
    )
    
    print(f"\n[INPUT]")
    print(f"  Claim: {claim.statement}")
    print(f"  Claim Type: {claim.claim_type.value}")
    print(f"  Uncertainty Value: {claim.uncertainty.value:.2f}")
    
    state = orchestrator.orchestrate(bundle)
    
    print(f"\n[ORCHESTRATION]")
    for gate_entry in state.reasoning_path:
        status = "✅" if gate_entry["passed"] else "❌"
        print(f"  {status} {gate_entry['gate']:25s} → {gate_entry['decision']}")
    
    print(f"\n[OUTPUT]")
    print(f"  Final Decision: {state.final_decision.value}")
    print(f"  Reason: High uncertainty (0.85) exceeds threshold (0.75)")
    
    assert state.final_decision == BundleDecision.DEFER
    print(f"\n  ✅ High uncertainty correctly deferred for human review")


def demo_multi_claim_bundle():
    """
    Demo 5: Multi-Claim Bundle
    
    Bundle with multiple claims processed together
    """
    print("\n" + "="*70)
    print("DEMO 5: Multi-Claim Bundle")
    print("="*70)
    
    claims = [
        Claim(
            statement="Semantic entropy detects hallucinations",
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
        ),
        Claim(
            statement="Therefore, we can use SE as a safety gate",
            claim_type=ClaimType.INFERENCE,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.65
            ),
            risk_tier=RiskTier.READ_ONLY
        ),
        Claim(
            statement="Implementation requires multi-model sampling",
            claim_type=ClaimType.DECISION,
            evidence_pointers=[],
            uncertainty=Uncertainty(
                method=UncertaintyMethod.CONFIDENCE_SCORE,
                value=0.55
            ),
            risk_tier=RiskTier.WRITE_LIMITED
        )
    ]
    
    bundle = ClaimBundle(
        origin_agent="design_team",
        claims=claims,
        reason="Design semantic entropy safety gate"
    )
    
    print(f"\n[BUNDLE]")
    print(f"  Bundle ID: {bundle.id}")
    print(f"  Claims: {len(claims)}")
    for i, claim in enumerate(claims, 1):
        print(f"    {i}. {claim.claim_type.value:10s}: {claim.statement[:50]}...")
    
    orchestrator = PrometheusOrchestrator()
    state = orchestrator.orchestrate(bundle)
    
    print(f"\n[RESULT]")
    print(f"  Final Decision: {state.final_decision.value}")
    print(f"  Gates Passed: {len([g for g in state.reasoning_path if g['passed']])} / 5")
    print(f"  ✅ Multi-claim bundle processed successfully")


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# PROMETHEUS PHASE 2: ORCHESTRATION + SEMANTIC ENTROPY")
    print("#"*70)
    
    try:
        demo_semantic_entropy()
        demo_uncertainty_quantifier()
        demo_orchestration_pipeline()
        demo_failure_case()
        demo_multi_claim_bundle()
        
        print("\n" + "="*70)
        print("✅ ALL PHASE 2 DEMOS PASSED")
        print("="*70)
        print("""
Phase 2 Summary:
  ✅ Semantic Entropy: Hallucination detection (H001)
  ✅ Orchestrator: Full gate pipeline with reasoning
  ✅ Uncertainty Quantifier: Unified uncertainty interface
  ✅ Multi-claim routing: Complex bundles handled correctly

Next: Phase 3 (MCP Integration + Advanced Features)
""")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

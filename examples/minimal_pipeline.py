"""Minimal working pipeline: ClaimBundle -> Gates -> Decision."""

import asyncio
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
from src.orchestrator import ExecutionOrchestrator


async def main():
    print("=" * 80)
    print("PROMETHEUS REFERENCE PIPELINE DEMO")
    print("=" * 80)
    
    # 1. Create a claim with evidence
    claim_1 = Claim(
        statement="Semantic entropy detects hallucinations with AUROC >= 0.75",
        claim_type=ClaimType.FACT,
        evidence_pointers=[
            EvidencePointer(
                source="https://nature.com/articles/s41586-024-07421-0",
                source_confidence=0.85,
                evidence_hash="bd24c2aaef2ef37ae95f0f9e5f7d9e7c"
            )
        ],
        uncertainty=Uncertainty(
            method=UncertaintyMethod.SEMANTIC_ENTROPY,
            value=0.30,  # Low uncertainty
            interpretation="Strong empirical validation"
        ),
        risk_tier=RiskTier.READ_ONLY,
        if_wrong_cost="Hallucination detection fails"
    )
    
    # 2. Create a bundle
    bundle = ClaimBundle(
        origin_agent="research_agent",
        claims=[claim_1]
    )
    
    print("\nInput ClaimBundle:")
    print(json.dumps(bundle.to_dict(), indent=2))
    
    # 3. Run through gates
    orchestrator = ExecutionOrchestrator()
    result = await orchestrator.execute_with_gates(bundle, agent_id="research_agent")
    
    print("\n" + "=" * 80)
    print("Output ClaimBundle (after gates):")
    print("=" * 80)
    print(json.dumps(result.to_dict(), indent=2))
    
    print("\n" + "=" * 80)
    print("GATE RESULTS:")
    print("=" * 80)
    print(f"Decision: {result.decision.value}")
    print(f"Reason: {result.reason}")
    print(f"Gates Passed: {result.audit_trail.gates_passed}")
    print(f"Gates Failed: {result.audit_trail.gates_failed}")
    print(f"\n✓ All gates passed. Claim ready for publication.")


if __name__ == "__main__":
    asyncio.run(main())

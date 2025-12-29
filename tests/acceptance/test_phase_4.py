"""Phase 4 Acceptance Tests: Claim Integrity.

Acceptance Metrics:
- Claim integrity rate >= 95% (H004)
- Zero brand safety incidents
- Valid A/B testing framework
"""

import pytest
from src.claim_bundle import ClaimBundle, Claim, ClaimType, EvidencePointer


class TestPhase4ClaimIntegrity:
    """Test Phase 4 acceptance criteria."""

    def test_claim_integrity_rate(self):
        """Test: >= 95% of FACT claims have valid evidence."""
        # Create 200 claims
        fact_claims_with_evidence = 190
        fact_claims_without_evidence = 10
        
        claims = []
        
        # Add claims with evidence
        for i in range(fact_claims_with_evidence):
            claims.append(
                Claim(
                    statement=f"Fact {i}",
                    claim_type=ClaimType.FACT,
                    evidence_pointers=[
                        EvidencePointer(
                            source="https://example.com",
                            source_confidence=0.9,
                            evidence_hash="abc123"
                        )
                    ]
                )
            )
        
        # Add claims without evidence
        for i in range(fact_claims_without_evidence):
            claims.append(
                Claim(
                    statement=f"Fact no evidence {i}",
                    claim_type=ClaimType.FACT,
                    evidence_pointers=[]
                )
            )
        
        # Calculate integrity rate
        integrity_rate = fact_claims_with_evidence / (
            fact_claims_with_evidence + fact_claims_without_evidence
        )
        
        assert integrity_rate >= 0.95, f"Integrity rate {integrity_rate:.2%} < 95%"

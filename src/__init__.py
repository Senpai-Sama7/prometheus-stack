"""
PROMETHEUS: Verifiable AI execution engine with evidence gates.

Core modules:
  - claim_bundle: ClaimBundle contract and serialization
  - gates: Evidence, Security, Adversarial, Uncertainty gates
  - uncertainty: Semantic entropy, model disagreement, conformal prediction
  - orchestrator: LangGraph-based task orchestration
  - mcp: Model Context Protocol integration
  - audit: Immutable event logging
"""

__version__ = "2.0.0"
__author__ = "PROMETHEUS Team"

from src.claim_bundle import ClaimBundle, Claim, Uncertainty, EvidencePointer

__all__ = [
    "ClaimBundle",
    "Claim",
    "Uncertainty",
    "EvidencePointer",
]

"""
Uncertainty Quantification Module

Implements semantic entropy and other uncertainty methods.

Ref: Wang et al., Nature (2024)
URL: https://nature.com/articles/s41586-024-07421-0

Key Result: AUROC >= 0.78 for hallucination detection
"""

from .semantic_entropy import (
    SemanticEntropyCalculator,
    compute_semantic_entropy,
    hallucination_likelihood,
)
from .uncertainty_quantifier import (
    UncertaintyQuantifier,
    UncertaintyEstimate,
)

__all__ = [
    "SemanticEntropyCalculator",
    "compute_semantic_entropy",
    "hallucination_likelihood",
    "UncertaintyQuantifier",
    "UncertaintyEstimate",
]

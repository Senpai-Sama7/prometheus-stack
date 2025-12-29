"""
Unified Uncertainty Quantification Interface

Abstracts different uncertainty methods:
- Semantic entropy (hallucination detection)
- Model disagreement (ensemble variance)
- Confidence scores (from logits)
- Token length (as proxy for complexity)

Phase 2: Semantic entropy focus
Phase 3: Add ensemble methods
Phase 4: Full integration with all methods
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

from src.claim_bundle import UncertaintyMethod
from src.uncertainty.semantic_entropy import (
    SemanticEntropyCalculator,
    SemanticEntropyResult
)


class UncertaintyMethod(str, Enum):
    """Supported uncertainty quantification methods."""
    SEMANTIC_ENTROPY = "semantic_entropy"
    MODEL_DISAGREEMENT = "model_disagreement"
    CONFIDENCE_SCORE = "confidence_score"
    TOKEN_LENGTH = "token_length"


@dataclass
class UncertaintyEstimate:
    """
    Unified uncertainty estimate across methods.
    
    Attributes:
        method: Which uncertainty method was used
        uncertainty_value: Scalar (0-1) representing uncertainty
        confidence_value: 1 - uncertainty_value
        interpretation: Human-readable explanation
        additional_data: Method-specific data (e.g., entropy details)
    """
    method: UncertaintyMethod
    uncertainty_value: float  # 0-1
    confidence_value: float   # 0-1
    interpretation: str
    additional_data: Dict[str, Any]


class UncertaintyQuantifier:
    """
    Main uncertainty quantification interface.
    
    Provides uniform API for computing uncertainty from:
    - Model outputs (semantic entropy)
    - Ensemble predictions (disagreement)
    - Single model logits (confidence)
    - Text properties (token length as proxy)
    """
    
    def __init__(self):
        """Initialize quantifier."""
        self.semantic_entropy_calc = SemanticEntropyCalculator()
    
    def from_semantic_entropy(
        self,
        model_outputs: List[str],
        claim: Optional[str] = None
    ) -> UncertaintyEstimate:
        """
        Compute uncertainty from semantic entropy.
        
        Args:
            model_outputs: Multiple LLM outputs
            claim: Optional claim context
        
        Returns:
            UncertaintyEstimate
        
        Reference:
            Wang et al., Nature 2024
            AUROC >= 0.78 for hallucination detection
        """
        result = self.semantic_entropy_calc.compute(model_outputs, claim)
        
        # Map entropy to uncertainty (high entropy = high uncertainty)
        uncertainty = result.entropy_value
        confidence = result.confidence_score
        
        # Generate interpretation
        if result.is_hallucination:
            interpretation = f"High uncertainty (entropy={result.entropy_value:.2f}). " \
                           f"Hallucination likelihood: {result.hallucination_probability:.1%}. " \
                           f"Consider deferring decision or requesting additional sources."
        elif uncertainty > 0.5:
            interpretation = f"Moderate uncertainty (entropy={result.entropy_value:.2f}). " \
                           f"Model outputs show diversity. " \
                           f"Recommend including caveats in explanation."
        else:
            interpretation = f"Low uncertainty (entropy={result.entropy_value:.2f}). " \
                           f"Model outputs consistent. " \
                           f"High confidence in claim."
        
        return UncertaintyEstimate(
            method=UncertaintyMethod.SEMANTIC_ENTROPY,
            uncertainty_value=uncertainty,
            confidence_value=confidence,
            interpretation=interpretation,
            additional_data={
                "entropy_value": result.entropy_value,
                "hallucination_probability": result.hallucination_probability,
                "num_samples": result.num_samples,
                "is_hallucination": result.is_hallucination,
                "paper_reference": "Wang et al., Nature 2024",
                "auroc": 0.78,
            }
        )
    
    def from_model_disagreement(
        self,
        predictions: List[Dict[str, Any]],
        method: str = "variance"
    ) -> UncertaintyEstimate:
        """
        Compute uncertainty from ensemble model disagreement.
        
        Args:
            predictions: List of predictions from different models
            method: "variance" or "entropy" for aggregation
        
        Returns:
            UncertaintyEstimate
        
        Note: Phase 3 feature (placeholder for now)
        """
        # Placeholder for Phase 3
        avg_confidence = sum(p.get("confidence", 0.5) for p in predictions) / len(predictions)
        uncertainty = 1.0 - avg_confidence
        
        interpretation = f"Model disagreement: average confidence {avg_confidence:.1%}"
        
        return UncertaintyEstimate(
            method=UncertaintyMethod.MODEL_DISAGREEMENT,
            uncertainty_value=uncertainty,
            confidence_value=avg_confidence,
            interpretation=interpretation,
            additional_data={
                "num_models": len(predictions),
                "method": method,
                "status": "Phase 3 feature",
            }
        )
    
    def from_confidence_score(
        self,
        confidence: float,
        explanation: Optional[str] = None
    ) -> UncertaintyEstimate:
        """
        Compute uncertainty from single confidence score.
        
        Args:
            confidence: Confidence value (0-1)
            explanation: Optional explanation
        
        Returns:
            UncertaintyEstimate
        """
        uncertainty = 1.0 - confidence
        
        if explanation is None:
            if confidence > 0.9:
                explanation = "Very high confidence in claim"
            elif confidence > 0.7:
                explanation = "High confidence in claim"
            elif confidence > 0.5:
                explanation = "Moderate confidence in claim"
            else:
                explanation = "Low confidence in claim"
        
        return UncertaintyEstimate(
            method=UncertaintyMethod.CONFIDENCE_SCORE,
            uncertainty_value=uncertainty,
            confidence_value=confidence,
            interpretation=explanation,
            additional_data={
                "source": "single_score",
            }
        )
    
    def from_token_length(
        self,
        token_count: int,
        max_tokens: int = 100
    ) -> UncertaintyEstimate:
        """
        Estimate uncertainty from text length.
        
        Heuristic: Longer responses may indicate complexity/uncertainty.
        
        Args:
            token_count: Number of tokens in response
            max_tokens: Reference maximum (for normalization)
        
        Returns:
            UncertaintyEstimate
        
        Note: Weak proxy for uncertainty, should be combined with other methods
        """
        # Simple heuristic: normalized token count
        normalized_length = min(1.0, token_count / max_tokens)
        
        # Interpret as uncertainty
        # Short responses (< 30 tokens) = high confidence
        # Medium responses (30-70 tokens) = medium confidence  
        # Long responses (> 70 tokens) = possible elaboration/uncertainty
        
        if token_count < 30:
            uncertainty = 0.2
            interpretation = "Concise response suggests high confidence"
        elif token_count < 70:
            uncertainty = 0.5
            interpretation = "Standard-length response"
        else:
            uncertainty = 0.7
            interpretation = "Long response may indicate elaboration or uncertainty"
        
        return UncertaintyEstimate(
            method=UncertaintyMethod.TOKEN_LENGTH,
            uncertainty_value=uncertainty,
            confidence_value=1.0 - uncertainty,
            interpretation=interpretation,
            additional_data={
                "token_count": token_count,
                "max_tokens": max_tokens,
                "note": "Weak proxy for uncertainty - use with other methods",
            }
        )
    
    def combine_estimates(
        self,
        estimates: List[UncertaintyEstimate],
        weights: Optional[List[float]] = None
    ) -> UncertaintyEstimate:
        """
        Combine multiple uncertainty estimates.
        
        Args:
            estimates: List of UncertaintyEstimate objects
            weights: Optional weights (default: equal)
        
        Returns:
            Combined UncertaintyEstimate
        
        Note: Phase 3 feature for ensemble uncertainty
        """
        if not estimates:
            raise ValueError("Need at least one estimate")
        
        if weights is None:
            weights = [1.0 / len(estimates)] * len(estimates)
        
        if len(weights) != len(estimates):
            raise ValueError("Weights must match estimates count")
        
        # Weighted average of uncertainties
        combined_uncertainty = sum(
            est.uncertainty_value * w for est, w in zip(estimates, weights)
        )
        combined_confidence = 1.0 - combined_uncertainty
        
        # Combine interpretations
        interpretations = [est.interpretation for est in estimates]
        combined_interpretation = " | ".join(interpretations)
        
        # Collect all method data
        combined_data = {
            "methods": [est.method.value for est in estimates],
            "weights": weights,
            "individual_uncertainties": [est.uncertainty_value for est in estimates],
        }
        
        return UncertaintyEstimate(
            method=UncertaintyMethod.SEMANTIC_ENTROPY,  # Primary method
            uncertainty_value=combined_uncertainty,
            confidence_value=combined_confidence,
            interpretation=combined_interpretation,
            additional_data=combined_data
        )

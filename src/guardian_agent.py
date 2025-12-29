"""Guardian Agent: Adversarial defense using message monitoring."""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class GuardianEvaluation:
    """Guardian agent evaluation result."""
    threat_score: float  # 0.0-1.0
    threat_detected: bool
    explanation: str
    recommended_action: str  # ALLOW, DEFER, REFUSE


class GuardianAgent:
    """Guardian agent for detecting adversarial manipulation (stub)."""

    def __init__(self, threat_threshold: float = 0.70):
        self.threat_threshold = threat_threshold

    async def evaluate(
        self,
        action: str,
        current_plan: List[str],
        execution_history: List[str],
        agent_id: str
    ) -> GuardianEvaluation:
        """
        Evaluate if an action is anomalous given the plan and history.
        In production: use trained adversarial detection model.
        """
        # Stub: always low threat score
        threat_score = 0.2

        return GuardianEvaluation(
            threat_score=threat_score,
            threat_detected=threat_score > self.threat_threshold,
            explanation="Action consistent with plan (stub evaluation)",
            recommended_action="ALLOW"
        )

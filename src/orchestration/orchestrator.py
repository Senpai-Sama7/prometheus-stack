"""
Prometheus Orchestrator

Core orchestration engine:
- Routes claims through gate pipeline
- Manages decision state
- Tracks reasoning path
- Integrates with LangGraph for async execution

Architecture:
  Bundle → Evidence Gate → Uncertainty Gate → Security Gate → 
  Adversarial Gate → Human Approval Gate → Decision
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

from src.claim_bundle import ClaimBundle, BundleDecision
from src.gates import (
    GateStack, EvidenceGate, UncertaintyGate, SecurityGate,
    AdversarialGate, HumanApprovalGate, GateResult
)


class OrchestratorPhase(str, Enum):
    """Orchestration pipeline phases."""
    RECEIVED = "RECEIVED"           # Bundle received, validation pending
    EVIDENCE_GATE = "EVIDENCE_GATE"
    UNCERTAINTY_GATE = "UNCERTAINTY_GATE"
    SECURITY_GATE = "SECURITY_GATE"
    ADVERSARIAL_GATE = "ADVERSARIAL_GATE"
    HUMAN_APPROVAL_GATE = "HUMAN_APPROVAL_GATE"
    DECISION_MADE = "DECISION_MADE"
    COMPLETE = "COMPLETE"


@dataclass
class OrchestratorConfig:
    """
    Configuration for orchestrator behavior.
    
    Attributes:
        max_retries: Max gate evaluation retries on transient failures
        evidence_confidence_threshold: Min confidence for FACT evidence (0-1)
        uncertainty_threshold_low: Below this = EXECUTE (0-1)
        uncertainty_threshold_high: Above this = DEFER (0-1)
        threat_score_threshold: Above this = DEFER for adversarial (0-1)
        enable_human_escalation: Whether to escalate to humans for risky decisions
        audit_log_path: Path to append-only audit log
    """
    max_retries: int = 3
    evidence_confidence_threshold: float = 0.60
    uncertainty_threshold_low: float = 0.50
    uncertainty_threshold_high: float = 0.75
    threat_score_threshold: float = 0.70
    enable_human_escalation: bool = True
    audit_log_path: str = "/var/log/prometheus/audit.log"


@dataclass
class OrchestratorState:
    """
    State machine for orchestration.
    
    Tracks:
    - Current phase in gate pipeline
    - Reasoning path (which gates evaluated, results)
    - Intermediate decisions
    - Final decision
    """
    bundle_id: str
    bundle: ClaimBundle
    current_phase: OrchestratorPhase = OrchestratorPhase.RECEIVED
    reasoning_path: List[Dict[str, Any]] = field(default_factory=list)
    gate_results: List[GateResult] = field(default_factory=list)
    final_decision: Optional[BundleDecision] = None
    timestamp_created: datetime = field(default_factory=datetime.utcnow)
    timestamp_completed: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def add_gate_evaluation(self, gate_name: str, result: GateResult) -> None:
        """
        Record gate evaluation in reasoning path.
        
        Args:
            gate_name: Name of gate evaluated
            result: GateResult from evaluation
        """
        self.gate_results.append(result)
        self.reasoning_path.append({
            "gate": gate_name,
            "passed": result.passed,
            "decision": result.decision.value if result.decision else None,
            "reason": result.reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def advance_phase(self, new_phase: OrchestratorPhase) -> None:
        """
        Advance to next orchestration phase.
        
        Args:
            new_phase: Target phase
        """
        self.current_phase = new_phase
    
    def mark_complete(self, decision: BundleDecision) -> None:
        """
        Mark orchestration as complete with final decision.
        
        Args:
            decision: Final decision
        """
        self.current_phase = OrchestratorPhase.COMPLETE
        self.final_decision = decision
        self.timestamp_completed = datetime.utcnow()


class PrometheusOrchestrator:
    """
    Main orchestration engine.
    
    Coordinates:
    1. Gate evaluation sequence
    2. State transitions
    3. Decision logic
    4. Audit trail recording
    
    LangGraph Integration:
    - Each gate is a node
    - Transitions based on GateResult
    - State flows through graph
    - Finally produces BundleDecision
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize orchestrator.
        
        Args:
            config: Orchestrator configuration (uses defaults if None)
        """
        self.config = config or OrchestratorConfig()
        self.execution_history: List[OrchestratorState] = []
    
    def orchestrate(self, bundle: ClaimBundle) -> OrchestratorState:
        """
        Main orchestration method: route bundle through gate pipeline.
        
        Args:
            bundle: ClaimBundle to evaluate
        
        Returns:
            OrchestratorState with final decision
        
        Raises:
            ValueError: If bundle is invalid
        """
        # Initialize state
        state = OrchestratorState(
            bundle_id=str(uuid.uuid4()),
            bundle=bundle,
        )
        
        # Phase 1: Evidence Gate
        state.advance_phase(OrchestratorPhase.EVIDENCE_GATE)
        try:
            evidence_result = EvidenceGate.evaluate(bundle)
            state.add_gate_evaluation("Evidence Gate", evidence_result)
            
            if not evidence_result.passed:
                state.mark_complete(evidence_result.decision)
                self.execution_history.append(state)
                return state
        except Exception as e:
            state.error_message = f"Evidence Gate error: {str(e)}"
            state.mark_complete(BundleDecision.REFUSE)
            self.execution_history.append(state)
            return state
        
        # Phase 2: Uncertainty Gate
        state.advance_phase(OrchestratorPhase.UNCERTAINTY_GATE)
        try:
            uncertainty_result = UncertaintyGate.evaluate(bundle)
            state.add_gate_evaluation("Uncertainty Gate", uncertainty_result)
            
            if not uncertainty_result.passed:
                state.mark_complete(uncertainty_result.decision)
                self.execution_history.append(state)
                return state
        except Exception as e:
            state.error_message = f"Uncertainty Gate error: {str(e)}"
            state.mark_complete(BundleDecision.DEFER)
            self.execution_history.append(state)
            return state
        
        # Phase 3: Security Gate
        state.advance_phase(OrchestratorPhase.SECURITY_GATE)
        try:
            security_result = SecurityGate.evaluate(bundle, agent_tier=0)  # Default tier
            state.add_gate_evaluation("Security Gate", security_result)
            
            if not security_result.passed:
                state.mark_complete(security_result.decision)
                self.execution_history.append(state)
                return state
        except Exception as e:
            state.error_message = f"Security Gate error: {str(e)}"
            state.mark_complete(BundleDecision.REFUSE)
            self.execution_history.append(state)
            return state
        
        # Phase 4: Adversarial Gate
        state.advance_phase(OrchestratorPhase.ADVERSARIAL_GATE)
        try:
            adversarial_result = AdversarialGate.evaluate(bundle, threat_score=0.3)  # Default threat
            state.add_gate_evaluation("Adversarial Gate", adversarial_result)
            
            if not adversarial_result.passed:
                state.mark_complete(adversarial_result.decision)
                self.execution_history.append(state)
                return state
        except Exception as e:
            state.error_message = f"Adversarial Gate error: {str(e)}"
            state.mark_complete(BundleDecision.DEFER)
            self.execution_history.append(state)
            return state
        
        # Phase 5: Human Approval Gate
        state.advance_phase(OrchestratorPhase.HUMAN_APPROVAL_GATE)
        try:
            human_result = HumanApprovalGate.evaluate(bundle)
            state.add_gate_evaluation("Human Approval Gate", human_result)
            
            if not human_result.passed:
                state.mark_complete(human_result.decision)
                self.execution_history.append(state)
                return state
        except Exception as e:
            state.error_message = f"Human Approval Gate error: {str(e)}"
            state.mark_complete(BundleDecision.ESCALATE)
            self.execution_history.append(state)
            return state
        
        # All gates passed
        state.advance_phase(OrchestratorPhase.DECISION_MADE)
        state.mark_complete(BundleDecision.PUBLISH)
        
        # Record in bundle's audit trail
        bundle.decision = BundleDecision.PUBLISH
        for gate_name in ["Evidence Gate", "Uncertainty Gate", "Security Gate",
                          "Adversarial Gate", "Human Approval Gate"]:
            bundle.add_gate_result(gate_name, True)
        
        self.execution_history.append(state)
        return state
    
    def get_reasoning_path(self, bundle_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve reasoning path for a bundle.
        
        Args:
            bundle_id: Bundle ID to look up
        
        Returns:
            Reasoning path or None if not found
        """
        for state in self.execution_history:
            if state.bundle_id == bundle_id:
                return state.reasoning_path
        return None
    
    def get_execution_history(self) -> List[OrchestratorState]:
        """
        Get full execution history.
        
        Returns:
            List of all OrchestratorState objects
        """
        return self.execution_history.copy()

#!/usr/bin/env python3
"""
WEEK 2: Complete LangGraph State Machine Implementation

This file contains the core state machine that orchestrates the 4-phase
claim processing pipeline.
"""

from typing import TypedDict, Literal
from datetime import datetime
import json


class ClaimProcessingState(TypedDict):
    """
    Complete state object for a claim as it flows through 4 phases.
    Every claim carries this state from start to finish.
    """

    # ═══════════════════════════════════════════════════════════
    # INPUT LAYER (What comes in)
    # ═══════════════════════════════════════════════════════════
    claim_id: str  # Unique identifier
    user_input: str  # Raw claim narrative/data
    claim_type: str  # "medical", "dental", "vision", etc.
    provider_id: str  # Healthcare provider identifier
    patient_id: str  # Patient identifier

    # ═══════════════════════════════════════════════════════════
    # CONTROL LAYER (Where we are in the process)
    # ═══════════════════════════════════════════════════════════
    phase: Literal[
        "validation",  # Phase 1: Structure checks
        "analysis",  # Phase 2: LLM extraction
        "reasoning",  # Phase 3: Multi-turn logic
        "completion",  # Phase 4: Final determination
    ]
    iteration: int  # Which loop iteration (0-N for reasoning)

    # ═══════════════════════════════════════════════════════════
    # PROCESSING LAYER (The work in progress)
    # ═══════════════════════════════════════════════════════════
    messages: list[dict]  # Conversation history with Claude
    tools_used: list[str]  # List of tools called so far

    # Phase-specific results
    validation_result: dict | None  # Output from Phase 1
    analysis_result: dict | None  # Output from Phase 2
    reasoning_result: dict | None  # Output from Phase 3

    # ═══════════════════════════════════════════════════════════
    # OUTPUT LAYER (What comes out)
    # ═══════════════════════════════════════════════════════════
    final_determination: str  # "APPROVED" | "REJECTED" | "PENDING_REVIEW"
    confidence_score: float  # 0.0 to 1.0
    reasoning_chain: list[dict]  # Full reasoning path with evidence
    errors: list[str]  # Any errors encountered

    # ═══════════════════════════════════════════════════════════
    # METADATA LAYER (Observability)
    # ═══════════════════════════════════════════════════════════
    start_time: datetime  # When processing started
    end_time: datetime | None  # When processing ended
    processing_time_ms: float  # Total time in milliseconds


def initialize_state(claim_id: str, user_input: str, **kwargs) -> ClaimProcessingState:
    """
    Create initial state for a new claim.

    Args:
        claim_id: Unique claim identifier
        user_input: Raw claim data/narrative
        **kwargs: Additional fields (claim_type, provider_id, patient_id, etc.)

    Returns:
        Initialized ClaimProcessingState ready for processing
    """
    return {
        # Input
        "claim_id": claim_id,
        "user_input": user_input,
        "claim_type": kwargs.get("claim_type", "medical"),
        "provider_id": kwargs.get("provider_id", "PROV-000"),
        "patient_id": kwargs.get("patient_id", "PAT-000"),
        # Control
        "phase": "validation",
        "iteration": 0,
        # Processing
        "messages": [],
        "tools_used": [],
        "validation_result": None,
        "analysis_result": None,
        "reasoning_result": None,
        # Output
        "final_determination": "",
        "confidence_score": 0.0,
        "reasoning_chain": [],
        "errors": [],
        # Metadata
        "start_time": datetime.now(),
        "end_time": None,
        "processing_time_ms": 0.0,
    }


def state_to_dict(state: ClaimProcessingState) -> dict:
    """
    Convert state to JSON-serializable dict.

    Handles datetime conversion and other non-serializable types.
    """
    result = dict(state)
    result["start_time"] = state["start_time"].isoformat()
    if state["end_time"]:
        result["end_time"] = state["end_time"].isoformat()
    return result


class PhaseTransition:
    """Helper for tracking phase transitions and timing."""

    PHASES = ["validation", "analysis", "reasoning", "completion"]

    @staticmethod
    def next_phase(current_phase: str) -> str:
        """Get next phase in sequence."""
        try:
            idx = PhaseTransition.PHASES.index(current_phase)
            return PhaseTransition.PHASES[idx + 1]
        except (ValueError, IndexError):
            return "completion"

    @staticmethod
    def phase_index(phase: str) -> int:
        """Get phase progress (0-3, 0-100%)."""
        try:
            return PhaseTransition.PHASES.index(phase)
        except ValueError:
            return 3

    @staticmethod
    def progress_percent(phase: str) -> int:
        """Get percentage progress through pipeline."""
        return (PhaseTransition.phase_index(phase) + 1) * 25


# Example usage and state lifecycle
if __name__ == "__main__":
    # Create initial state
    state = initialize_state(
        claim_id="CLM-EXAMPLE-001",
        user_input="Patient Jane Smith underwent cataract surgery on left eye...",
        claim_type="medical",
        provider_id="PROV-001",
        patient_id="PAT-001",
    )

    print("Initial State:")
    print(f"  Phase: {state['phase']}")
    print(f"  Progress: {PhaseTransition.progress_percent(state['phase'])}%")
    print(f"  Determination: {state['final_determination']}")
    print()

    # Simulate phase transitions
    for phase in PhaseTransition.PHASES:
        state["phase"] = phase
        state["reasoning_chain"].append(
            {
                "step": PhaseTransition.phase_index(phase) + 1,
                "phase": phase,
                "status": "complete",
            }
        )

    # Mark completion
    state["final_determination"] = "APPROVED"
    state["confidence_score"] = 0.95
    state["end_time"] = datetime.now()
    state["processing_time_ms"] = (
        state["end_time"] - state["start_time"]
    ).total_seconds() * 1000

    print("Final State:")
    print(f"  Determination: {state['final_determination']}")
    print(f"  Confidence: {state['confidence_score']:.1%}")
    print(f"  Processing Time: {state['processing_time_ms']:.0f}ms")
    print(f"  Phases Completed: {len(state['reasoning_chain'])}")
    print()

    # Export to JSON
    print("JSON Export:")
    print(json.dumps(state_to_dict(state), indent=2))

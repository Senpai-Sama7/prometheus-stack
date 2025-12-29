"""
Orchestrator: LangGraph-based task orchestration with gate integration.

Core workflow:
  1. Decompose task into subtasks
  2. Execute subtasks with evidence collection
  3. Wrap results in ClaimBundle
  4. Pass through GateStack
  5. On PUBLISH: emit to output
  6. On DEFER/REFUSE: log and escalate

Reference: docs/BUILD_SPEC.md (Phase 2)

Production implementation uses:
  - LangGraph for state machine
  - Checkpointing for fault tolerance
  - Redis for distributed coordination
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import asyncio

from src.claim_bundle import ClaimBundle, Claim, BundleDecision
from src.gates import GateStack


class TaskState(str, Enum):
    """States in task orchestration workflow."""
    DECOMPOSE = "decompose"
    EXECUTE = "execute"
    COLLECT = "collect"
    GATE = "gate"
    OUTPUT = "output"
    ESCALATE = "escalate"
    ERROR = "error"


@dataclass
class TaskContext:
    """Context for a task execution."""
    task_id: str
    task_description: str
    state: TaskState = TaskState.DECOMPOSE
    subtasks: List[str] = None
    bundle: Optional[ClaimBundle] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.subtasks is None:
            self.subtasks = []
        if self.metadata is None:
            self.metadata = {}


class Orchestrator:
    """
    Main orchestrator for task execution with verification gates.
    
    In production, this is implemented as a LangGraph state machine with:
    - Checkpointing for persistence
    - Threading for concurrent task execution
    - Integration with MCP tools
    """

    def __init__(self, agent_id: str = "orchestrator"):
        self.agent_id = agent_id
        self.context_stack: List[TaskContext] = []

    async def execute(
        self,
        task_description: str,
        decompose_fn: Optional[Callable] = None,
        execute_fn: Optional[Callable] = None,
        collect_fn: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task with full gate verification.
        
        Args:
            task_description: Human-readable task description
            decompose_fn: Function to break task into subtasks
            execute_fn: Function to execute each subtask
            collect_fn: Function to collect evidence from execution
            
        Returns:
            Result dictionary with bundle and gate results
        """
        context = TaskContext(
            task_id=str(len(self.context_stack)),
            task_description=task_description
        )
        self.context_stack.append(context)

        try:
            # Step 1: Decompose
            context.state = TaskState.DECOMPOSE
            if decompose_fn:
                context.subtasks = await self._call_async(decompose_fn, task_description)
            else:
                context.subtasks = [task_description]

            # Step 2: Execute
            context.state = TaskState.EXECUTE
            results = []
            for subtask in context.subtasks:
                if execute_fn:
                    result = await self._call_async(execute_fn, subtask)
                    results.append(result)

            # Step 3: Collect evidence
            context.state = TaskState.COLLECT
            if collect_fn:
                evidence = await self._call_async(collect_fn, results)
            else:
                evidence = {"raw_results": results}

            # Step 4: Create ClaimBundle
            claims = self._build_claims_from_evidence(evidence)
            context.bundle = ClaimBundle(
                origin_agent=self.agent_id,
                claims=claims,
                reason=f"Task: {task_description}"
            )

            # Step 5: Pass through GateStack
            context.state = TaskState.GATE
            gate_result = GateStack.evaluate(context.bundle)

            # Step 6: Handle decision
            if context.bundle.decision == BundleDecision.PUBLISH:
                context.state = TaskState.OUTPUT
                return self._format_output(context, gate_result, success=True)
            else:
                context.state = TaskState.ESCALATE
                return self._format_output(context, gate_result, success=False)

        except Exception as e:
            context.state = TaskState.ERROR
            context.error = str(e)
            return {
                "task_id": context.task_id,
                "success": False,
                "error": str(e),
                "state": context.state.value
            }
        finally:
            self.context_stack.pop()

    async def _call_async(self, fn: Callable, *args, **kwargs) -> Any:
        """Call function (async or sync)."""
        if asyncio.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        else:
            return fn(*args, **kwargs)

    def _build_claims_from_evidence(self, evidence: Dict[str, Any]) -> List[Claim]:
        """Convert evidence dict into Claim objects.
        
        Stub: In production, this extracts facts/inferences from execution results
        and wraps them in ClaimBundle format.
        """
        from src.claim_bundle import (
            Claim, Uncertainty, UncertaintyMethod, GateRecommendation, RiskTier, ClaimType
        )

        # Simple stub: create one claim per evidence item
        claims = []
        for key, value in evidence.items():
            claim = Claim(
                statement=f"Evidence: {key}",
                claim_type=ClaimType.INFERENCE,
                uncertainty=Uncertainty(
                    method=UncertaintyMethod.CONFIDENCE_SCORE,
                    value=0.5,
                    interpretation="Stub uncertainty",
                    gate_recommendation=GateRecommendation.EXECUTE
                ),
                risk_tier=RiskTier.READ_ONLY
            )
            claims.append(claim)

        return claims

    def _format_output(self, context: TaskContext, gate_result, success: bool) -> Dict[str, Any]:
        """Format final output."""
        return {
            "task_id": context.task_id,
            "task_description": context.task_description,
            "success": success,
            "bundle": context.bundle.to_dict() if context.bundle else None,
            "gate_result": {
                "gate_name": gate_result.gate_name,
                "passed": gate_result.passed,
                "decision": gate_result.decision.value,
                "reason": gate_result.reason
            },
            "state": context.state.value
        }

    def get_checkpoint(self) -> Dict[str, Any]:
        """Get current checkpoint for persistence.
        
        In production: serialized to Redis or database.
        """
        return {
            "agent_id": self.agent_id,
            "context_depth": len(self.context_stack),
            "current_context": {
                "task_id": self.context_stack[-1].task_id if self.context_stack else None,
                "state": self.context_stack[-1].state.value if self.context_stack else None
            }
        }


# Convenience functions
async def run_task(
    task_description: str,
    agent_id: str = "orchestrator",
    decompose_fn: Optional[Callable] = None,
    execute_fn: Optional[Callable] = None,
    collect_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Helper to run a single task."""
    orchestrator = Orchestrator(agent_id)
    return await orchestrator.execute(
        task_description=task_description,
        decompose_fn=decompose_fn,
        execute_fn=execute_fn,
        collect_fn=collect_fn
    )

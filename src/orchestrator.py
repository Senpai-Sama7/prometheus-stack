"""ExecutionOrchestrator: LangGraph-like orchestration with gates."""

from src.claim_bundle import ClaimBundle, BundleDecision
from src.gates import (
    EvidenceGate,
    UncertaintyGate,
    SecurityGate,
    AdversarialGate,
    HumanApprovalGate,
    ToolInvocation,
    GateAction,
    GateDecision,
)


class ExecutionOrchestrator:
    """Minimal orchestration mimicking LangGraph structure."""

    def __init__(self):
        self.evidence_gate = EvidenceGate()
        self.uncertainty_gate = UncertaintyGate(defer_threshold=0.75, explain_threshold=0.50)
        self.security_gate = SecurityGate(
            tool_registry={
                "web_search": {"required_tier": "READ_ONLY"},
                "update_database": {"required_tier": "MODIFY"},
                "delete_user": {"required_tier": "DELETE"}
            },
            agent_permissions={
                "research_agent": "READ_ONLY",
                "write_agent": "MODIFY",
                "admin_agent": "PRIVILEGE"
            }
        )
        self.adversarial_gate = AdversarialGate()
        self.human_approval_gate = HumanApprovalGate()

    async def execute_with_gates(self, claim_bundle: ClaimBundle, agent_id: str) -> ClaimBundle:
        """
        Run all gates in sequence.
        If any gate fails, update ClaimBundle.decision and return.
        """

        # Gate 1: Evidence
        evidence_decision = await self.evidence_gate.evaluate(claim_bundle)
        if evidence_decision.action == GateAction.REFUSE:
            claim_bundle.audit_trail.gates_failed.append("evidence_gate")
            claim_bundle.decision = BundleDecision.REFUSE
            claim_bundle.reason = evidence_decision.reason
            return claim_bundle

        claim_bundle.audit_trail.gates_passed.append("evidence_gate")

        # Gate 2: Uncertainty (for each claim)
        for claim in claim_bundle.claims:
            uncertainty_decision = await self.uncertainty_gate.evaluate(claim)
            if uncertainty_decision.action == GateAction.DEFER:
                claim_bundle.audit_trail.gates_failed.append(f"uncertainty_gate (claim {claim.id})")
                claim_bundle.decision = BundleDecision.DEFER
                claim_bundle.reason = uncertainty_decision.reason
                return claim_bundle

        claim_bundle.audit_trail.gates_passed.append("uncertainty_gate")

        # Gate 3: Security (simulated)
        security_decision = await self.security_gate.evaluate(
            ToolInvocation(
                tool_name="web_search",
                arguments={"query": "test"},
            ),
            agent_id=agent_id
        )
        if security_decision.action == GateAction.REFUSE:
            claim_bundle.audit_trail.gates_failed.append("security_gate")
            claim_bundle.decision = BundleDecision.REFUSE
            claim_bundle.reason = security_decision.reason
            return claim_bundle

        claim_bundle.audit_trail.gates_passed.append("security_gate")

        # Gate 4: Adversarial
        adversarial_decision = await self.adversarial_gate.evaluate(
            action_statement="execute web_search",
            context_history=[]
        )
        if adversarial_decision.action == GateAction.DEFER:
            claim_bundle.audit_trail.gates_failed.append("adversarial_gate")
            claim_bundle.decision = BundleDecision.DEFER
            claim_bundle.reason = adversarial_decision.reason
            return claim_bundle

        claim_bundle.audit_trail.gates_passed.append("adversarial_gate")

        # Gate 5: Human Approval
        approval_decision = await self.human_approval_gate.evaluate(claim_bundle)
        if approval_decision.action == GateAction.ESCALATE:
            claim_bundle.audit_trail.gates_failed.append("human_approval_gate")
            claim_bundle.decision = BundleDecision.ESCALATE
            claim_bundle.reason = approval_decision.reason
            claim_bundle.required_approvals.append("security_team")
            return claim_bundle

        claim_bundle.audit_trail.gates_passed.append("human_approval_gate")

        # All gates passed
        claim_bundle.decision = BundleDecision.PUBLISH
        claim_bundle.reason = "All gates passed. Ready for publication."
        return claim_bundle

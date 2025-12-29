"""Phase 3 Acceptance Tests: Guardian Agent.

Acceptance Metrics:
- Guardian ASR reduction >= 40% (H002)
- False positive rate <= 2%
- 100% of actions auditable
"""

import pytest
from src.audit_log import AuditLog


class TestPhase3SecurityMoat:
    """Test Phase 3 acceptance criteria."""

    def test_audit_log_immutability(self, audit_log):
        """Test: All actions are auditable and immutable."""
        # Log 50 events
        trace_ids = []
        for i in range(50):
            trace_id = audit_log.log_event(
                event_type="tool_invocation",
                agent_id=f"agent_{i % 5}",
                details={"tool": f"tool_{i}"}
            )
            trace_ids.append(trace_id)
        
        # Verify all events are retrievable
        total_events = audit_log.get_events()
        assert len(total_events) == 50
        
        # Verify immutability
        assert audit_log.verify_immutability()

    def test_audit_log_queryability(self, audit_log):
        """Test: Audit log is queryable by agent."""
        for i in range(10):
            audit_log.log_event(
                event_type="action",
                agent_id="agent_a",
                details={"action": i}
            )
        
        # Query by agent
        events = audit_log.get_events(agent_id="agent_a")
        assert len(events) == 10

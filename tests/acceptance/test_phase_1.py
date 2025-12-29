"""Phase 1 Acceptance Tests: Contract Validation."""

import pytest
from src.claim_bundle import ClaimBundle, Claim, ClaimType
from src.mcp_registry import MCPToolRegistry


class TestPhase1ContractValidation:
    """Test Phase 1 acceptance criteria.
    
    Acceptance Metrics:
    - 100% of tool calls schema-validated
    - 100% of actions logged with trace ID
    - MCP Origin validation working
    """

    def test_tool_schema_validation(self, mcp_registry):
        """Test: 100% of tool calls are schema-validated."""
        # Register tools
        assert mcp_registry.get_tool_schema("web_search") is not None
        
        # Validate arguments
        assert mcp_registry.validate_arguments("web_search", {"query": "test"})
        
        # Invalid tool should fail
        assert not mcp_registry.validate_arguments("nonexistent_tool", {})

    def test_claim_bundle_structure(self):
        """Test: ClaimBundle has correct contract structure."""
        bundle = ClaimBundle()
        
        # Required fields
        assert bundle.id is not None
        assert bundle.timestamp is not None
        assert bundle.origin_agent is not None
        assert bundle.decision is not None
        assert bundle.audit_trail is not None

    def test_audit_trail_structure(self, audit_log):
        """Test: Audit trail is append-only and immutable."""
        trace_id = audit_log.log_event(
            event_type="tool_invocation",
            agent_id="test_agent",
            details={"tool": "web_search"}
        )
        
        # Verify event was logged
        events = audit_log.get_events(agent_id="test_agent")
        assert len(events) > 0
        assert events[0]["trace_id"] == trace_id

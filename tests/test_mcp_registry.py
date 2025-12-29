"""Tests for MCP Tool Registry."""

from src.mcp_registry import MCPToolRegistry


class TestMCPToolRegistry:
    """Test MCPToolRegistry."""

    def test_register_tool(self, mcp_registry):
        """Test registering a tool."""
        tools = mcp_registry.list_tools()
        assert len(tools) > 0
        assert any(t["name"] == "web_search" for t in tools)

    def test_get_tool_schema(self, mcp_registry):
        """Test getting tool schema."""
        schema = mcp_registry.get_tool_schema("web_search")
        assert schema is not None
        assert "properties" in schema

    def test_validate_arguments(self, mcp_registry):
        """Test argument validation."""
        is_valid = mcp_registry.validate_arguments(
            "web_search",
            {"query": "test"}
        )
        assert is_valid

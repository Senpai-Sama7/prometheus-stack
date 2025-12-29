"""MCP Tool Registry: Schema validation and permission management."""

from typing import Dict, Optional, List


class MCPToolRegistry:
    """Minimal MCP tool registry for managing tools and schemas."""

    def __init__(self):
        self.tools = {}

    def register_tool(self, name: str, schema: Dict, required_tier: str = "READ_ONLY"):
        """Register a tool with JSON schema."""
        self.tools[name] = {
            "name": name,
            "schema": schema,
            "required_tier": required_tier
        }

    def list_tools(self) -> List[Dict]:
        """List all registered tools."""
        return list(self.tools.values())

    def get_tool_schema(self, name: str) -> Optional[Dict]:
        """Get tool schema by name."""
        tool = self.tools.get(name)
        return tool["schema"] if tool else None

    def validate_arguments(self, tool_name: str, arguments: Dict) -> bool:
        """Minimal argument validation (stub)."""
        if tool_name not in self.tools:
            return False
        # In production: use jsonschema library
        return True

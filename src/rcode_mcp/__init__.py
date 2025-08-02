"""
R-Code MCP Package
==================

Model Context Protocol integration for R-Code AI assistant.
"""

from .mcp_integration import (
    RCodeMCPManager,
    mcp_manager,
    initialize_mcp_from_config,
    get_mcp_tools,
    is_mcp_available,
    get_mcp_status,
    get_mcp_info_tools
)

__all__ = [
    "RCodeMCPManager",
    "mcp_manager", 
    "initialize_mcp_from_config",
    "get_mcp_tools",
    "is_mcp_available",
    "get_mcp_status",
    "get_mcp_info_tools"
]

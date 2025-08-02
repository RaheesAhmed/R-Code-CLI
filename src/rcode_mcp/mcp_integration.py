"""
R-Code MCP Integration
=====================

Model Context Protocol integration for R-Code AI assistant.
Enables dynamic loading of MCP servers and their tools.
"""

import asyncio
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool, BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from functools import wraps

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError as e:
    MCP_AVAILABLE = False
    MultiServerMCPClient = None
    print(f"❌ MCP import failed: {e}")
    print("💡 Try: pip install langchain-mcp-adapters")
except Exception as e:
    MCP_AVAILABLE = False
    MultiServerMCPClient = None
    print(f"❌ MCP unexpected error: {e}")


class RCodeMCPManager:
    """Manages MCP server connections and tools for R-Code"""
    
    def __init__(self):
        """Initialize MCP manager"""
        self.client: Optional[MultiServerMCPClient] = None
        self.available_tools = []
        self.connected_servers = {}
        self.mcp_available = MCP_AVAILABLE
    
    async def initialize(self, server_configs: Dict[str, Any]) -> bool:
        """
        Initialize MCP client with server configurations
        
        Args:
            server_configs: Dictionary of server configurations
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not self.mcp_available:
            print("⚠️  MCP not available. Install with: pip install langchain-mcp-adapters")
            return False
        
        if not server_configs:
            return True
        
        try:
            # Convert Cline MCP config format to LangGraph format
            mcp_config = {}
            
            for server_key, server_config in server_configs.items():
               
                if "command" in server_config:
                    mcp_config[server_key] = {
                        "command": server_config["command"],
                        "args": server_config.get("args", []),
                        "transport": "stdio"
                    }
            
            if mcp_config:
                self.client = MultiServerMCPClient(mcp_config)
                self.available_tools = await self.client.get_tools()
                self.connected_servers = mcp_config
                
                print(f"✅ Connected to {len(mcp_config)} MCP servers")
                print(f"📦 Loaded {len(self.available_tools)} MCP tools")
                
                return True
            else:
                return True
                
        except Exception as e:
            print(f"❌ Failed to initialize MCP servers: {str(e)}")
            return False
    
    def get_tools(self) -> List:
        """Get list of available MCP tools"""
        return self.available_tools if self.available_tools else []
    
    def is_available(self) -> bool:
        """Check if MCP is available and initialized"""
        return self.mcp_available and self.client is not None
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of connected MCP servers"""
        return {
            "mcp_available": self.mcp_available,
            "client_initialized": self.client is not None,
            "connected_servers": list(self.connected_servers.keys()),
            "total_tools": len(self.available_tools),
            "tools": [tool.name for tool in self.available_tools] if self.available_tools else []
        }
    
    async def close(self):
        """Close MCP client connections"""
        if self.client:
            try:
                await self.client.close()
                self.client = None
                self.available_tools = []
                self.connected_servers = {}
                print("🔌 MCP connections closed")
            except Exception as e:
                print(f"⚠️  Error closing MCP connections: {str(e)}")


# Global MCP manager instance
mcp_manager = RCodeMCPManager()


async def initialize_mcp_from_config(server_configs: Dict[str, Any]) -> bool:
    """
    Initialize MCP manager from configuration
    
    Args:
        server_configs: Server configurations from config
        
    Returns:
        bool: True if successful
    """
    return await mcp_manager.initialize(server_configs)


def get_mcp_tools() -> List:
    """Get available MCP tools - return directly without wrapping"""
    return mcp_manager.get_tools()


def is_mcp_available() -> bool:
    """Check if MCP is available"""
    return mcp_manager.is_available()


def get_mcp_status() -> Dict[str, Any]:
    """Get MCP status information"""
    return mcp_manager.get_server_status()


@tool
def mcp_status() -> str:
    """
    Get status of MCP (Model Context Protocol) servers and tools.
    
    Shows information about connected MCP servers, available tools,
    and overall MCP integration status.
    
    Returns:
        String with MCP status information
    """
    status = get_mcp_status()
    
    if not status["mcp_available"]:
        return "❌ MCP not available. Install with: pip install langchain-mcp-adapters"
    
    if not status["client_initialized"]:
        return "⚠️  MCP client not initialized. No servers configured or connection failed."
    
    result = f"✅ MCP Status:\n"
    result += f"📡 Connected servers: {len(status['connected_servers'])}\n"
    
    if status["connected_servers"]:
        result += f"🖥️  Servers: {', '.join(status['connected_servers'])}\n"
    
    result += f"🛠️  Available tools: {status['total_tools']}\n"
    
    if status["tools"]:
        result += f"📦 Tools: {', '.join(status['tools'])}\n"
    
    return result


def get_mcp_info_tools() -> List:
    """Get MCP information tools"""
    return [mcp_status]

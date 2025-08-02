"""
R-Code AI Agent
==============

Configuration-driven coding agent with MCP support and full file management capabilities.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict, Annotated

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent

from ..prompts import get_system_prompt
from ..tools import (
    get_web_search_tools, 
    is_web_search_available, 
    get_file_operation_tools,
    get_terminal_operation_tools,
    initialize_checkpoint_file_ops,
    get_checkpoint_aware_file_operation_tools
)
from ..checkpoint import CheckpointManager
from ..commands import SlashCommandHandler
from ..config import config_manager
from ..rcode_mcp import initialize_mcp_from_config, get_mcp_tools, is_mcp_available, get_mcp_info_tools


class RCodeState(TypedDict):
    """State for R-Code agent"""
    messages: Annotated[List[BaseMessage], add_messages]


class RCodeAgent:
    """Configuration-driven R-Code AI agent with MCP support"""
    
    def __init__(self):
        """Initialize R-Code agent with configuration management"""
        self.checkpointer = InMemorySaver()
        self.models = {}
        self.graph = None
        self.config = config_manager.load_config()
        self.custom_rules = config_manager.load_rules()
        self.mcp_initialized = False
        
        # Initialize checkpoint system
        self.checkpoint_manager = CheckpointManager()
        self.slash_command_handler = SlashCommandHandler(self.checkpoint_manager)
        
        # Initialize checkpoint-aware file operations
        initialize_checkpoint_file_ops(self.checkpoint_manager)
        
        # Initialize everything
        self._initialize_models()
        
        # Build graph (MCP tools will be added after async init)
        self._build_graph()
        
        # Load custom rules silently
        pass

    async def initialize_mcp(self):
        """Initialize MCP servers from configuration - must be called after constructor"""
        if self.mcp_initialized:
            return
            
        try:
            mcp_servers = config_manager.get_enabled_mcp_servers()
            if mcp_servers:
                success = await initialize_mcp_from_config(mcp_servers)
                if success:
                    self.mcp_initialized = True
                    # Rebuild graph with MCP tools
                    self._build_graph()
                    print("✅ MCP integration completed")
            else:
                print("ℹ️  No MCP servers configured")
                self.mcp_initialized = True
        except Exception as e:
            print(f"⚠️  MCP initialization failed: {e}")
            self.mcp_initialized = True  # Mark as done to avoid retries

    @classmethod
    async def create(cls):
        """Create and initialize RCodeAgent with MCP support"""
        agent = cls()
        await agent.initialize_mcp()
        return agent

    def _initialize_models(self):
        """Initialize available AI models from configuration"""
        enabled_models = config_manager.get_enabled_models()
        
        for model_key, model_config in enabled_models.items():
            try:
                api_key_env = model_config.get("api_key_env")
                if api_key_env and os.getenv(api_key_env):
                    self.models[model_key] = init_chat_model(
                        model_config["name"],
                        temperature=model_config.get("temperature", 0.1),
                        max_tokens=model_config.get("max_tokens", 4000)
                    )
            except Exception as e:
                print(f"⚠️  Failed to initialize {model_key}: {e}")

        if not self.models:
            # Fallback to environment-based initialization
            claude_key = os.getenv("ANTHROPIC_API_KEY")
            if claude_key:
                self.models["claude"] = init_chat_model(
                    "anthropic:claude-3-5-sonnet-20241022",
                    temperature=0.1,
                    max_tokens=4000
                )

            openai_key = os.getenv("OPENAI_API_KEY") 
            if openai_key:
                self.models["openai"] = init_chat_model(
                    "openai:gpt-4-turbo-preview",
                    temperature=0.1,
                    max_tokens=4000
                )

        if not self.models:
            raise RuntimeError("No API keys configured. Please set API keys or update .rcode/config.json")

    def _build_graph(self):
        """Build Graph with tools integrated using create_react_agent for MCP compatibility"""
        # Get all available tools
        tools = []
        
        # Add web search tools if available and enabled
        tool_config = self.config.get("tools", {})
        if tool_config.get("web_search", {}).get("enabled", True) and is_web_search_available():
            tools.extend(get_web_search_tools())
        
        # Add checkpoint-aware file operation tools if enabled (default: enabled)
        if tool_config.get("file_operations", {}).get("enabled", True):
            tools.extend(get_checkpoint_aware_file_operation_tools())
        
        # Add terminal operation tools if enabled (default: enabled)
        if tool_config.get("terminal_operations", {}).get("enabled", True):
            tools.extend(get_terminal_operation_tools())
        
        # Add MCP tools if available
        if is_mcp_available():
            tools.extend(get_mcp_tools())
        
        # Add MCP info tools
        tools.extend(get_mcp_info_tools())
        
        # Get primary model from config
        primary_model_key = self.config.get("models", {}).get("primary", "claude")
        fallback_model_key = self.config.get("models", {}).get("fallback", "openai")
        
        self.primary_model = self.models.get(primary_model_key, self.models.get(fallback_model_key))
        if not self.primary_model:
            self.primary_model = list(self.models.values())[0]  # Use first available
        
        # Create system message
        system_message = get_system_prompt()
        if self.custom_rules:
            system_message += f"\n\n## Custom User Rules:\n{self.custom_rules}"
        
        # Use create_react_agent which handles async MCP tools properly
        self.graph = create_react_agent(
            self.primary_model,
            tools,
            checkpointer=self.checkpointer,
            state_modifier=system_message
        )

    def chat(self, message: str, thread_id: str = "default") -> str:
        """Simple chat interface using create_react_agent"""
        config = {"configurable": {"thread_id": thread_id}}
        
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=message)]}, 
            config
        )
        
        return result["messages"][-1].content

    def stream_chat(self, message: str, thread_id: str = "default"):
        """Stream with beautiful tool output and real-time token streaming"""
        config = {"configurable": {"thread_id": thread_id}}
        
        # Stream from the react agent
        for chunk in self.graph.stream(
            {"messages": [HumanMessage(content=message)]}, 
            config,
            stream_mode="values"
        ):
            if "messages" in chunk:
                last_message = chunk["messages"][-1]
                if hasattr(last_message, 'content'):
                    yield {"type": "text", "content": str(last_message.content)}

    async def astream_chat(self, message: str, thread_id: str = "default"):
        """Async stream with beautiful tool separation and clean token streaming"""
        # Check for slash commands first
        if self.slash_command_handler.is_slash_command(message):
            try:
                command_response = await self.slash_command_handler.handle_command(message)
                if command_response:
                    yield {"type": "token", "content": command_response}
                    return
            except Exception as e:
                yield {"type": "token", "content": f"❌ Command error: {str(e)}"}
                return
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Use combined streaming modes for complete experience
        async for stream_mode, chunk in self.graph.astream(
            {"messages": [HumanMessage(content=message)]}, 
            config,
            stream_mode=["updates", "messages"]
        ):
            if stream_mode == "updates":
                # Handle tool execution updates
                for node_name, node_output in chunk.items():
                    if node_name == "tools":
                        # Tool execution completed - show results
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, 'content') and msg.content:
                                    tool_name = getattr(msg, 'name', 'Tool')
                                    yield {"type": "tool_result", "content": str(msg.content), "tool_name": tool_name}
                    
                    elif node_name == "agent":
                        # Agent is processing - check for tool calls
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, 'content') and isinstance(msg.content, list):
                                    # Look for tool use in structured content
                                    for item in msg.content:
                                        if isinstance(item, dict) and item.get('type') == 'tool_use':
                                            tool_name = item.get('name', 'Tool')
                                            yield {"type": "tool_use", "tool_name": tool_name}
            
            elif stream_mode == "messages":
                # Handle clean token streaming for AI responses
                message_chunk, metadata = chunk
                if hasattr(message_chunk, 'content') and message_chunk.content:
                    if isinstance(message_chunk.content, str):
                        yield {"type": "token", "content": message_chunk.content}
                    elif isinstance(message_chunk.content, list):
                        # Handle structured content - only extract text parts
                        for item in message_chunk.content:
                            if isinstance(item, dict) and item.get('type') == 'text' and item.get('text'):
                                yield {"type": "token", "content": item['text']}

    def get_state(self, thread_id: str):
        """Get conversation state"""
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.get_state(config)

    def get_available_models(self) -> List[str]:
        """Get available models"""
        return list(self.models.keys())
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information"""
        return config_manager.get_config_info()

    def __str__(self) -> str:
        return f"RCodeAgent(models={list(self.models.keys())}, config_version={self.config.get('version', 'unknown')})"

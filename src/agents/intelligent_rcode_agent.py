"""
Intelligent R-Code AI Agent
===========================

Enhanced AI agent with dynamic prompts, learning capabilities, and intelligent context management.
Uses LangGraph v0.6 context system for persistent learning and adaptive behavior.
"""

import os
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union
from typing_extensions import TypedDict, Annotated
from pathlib import Path


from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, AnyMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.runtime import get_runtime
from langgraph.prebuilt.chat_agent_executor import AgentState

from ..prompts import get_system_prompt
from ..tools import (
    get_web_search_tools, 
    is_web_search_available, 
    get_file_operation_tools,
    get_terminal_operation_tools,
    get_approval_aware_terminal_tools,
    initialize_checkpoint_file_ops,
    get_checkpoint_aware_file_operation_tools
)
from ..checkpoint import CheckpointManager
from ..commands import SlashCommandHandler
from ..config import config_manager
from ..rcode_mcp import initialize_mcp_from_config, get_mcp_tools, is_mcp_available, get_mcp_info_tools
from ..context import ContextProvider, get_context_tools


@dataclass
class RCodeContext:
    """Static runtime context for user preferences and session data"""
    user_name: str = "Developer"
    user_id: str = "default"
    project_root: str = "."
    session_id: str = "default"
    
    # User preferences
    coding_style: Dict[str, Any] = None
    preferred_frameworks: List[str] = None
    language_preferences: List[str] = None
    code_complexity_preference: str = "balanced"  # simple, balanced, advanced
    explanation_style: str = "detailed"  # brief, detailed, comprehensive
    
    # Project metadata
    project_type: str = "general"
    tech_stack: List[str] = None
    project_goals: List[str] = None
    
    def __post_init__(self):
        if self.coding_style is None:
            self.coding_style = {
                "indentation": "4_spaces",
                "naming_convention": "snake_case",
                "comment_style": "descriptive",
                "error_handling": "comprehensive",
                "documentation": "docstring"
            }
        
        if self.preferred_frameworks is None:
            self.preferred_frameworks = []
        
        if self.language_preferences is None:
            self.language_preferences = ["python", "javascript", "typescript"]
        
        if self.tech_stack is None:
            self.tech_stack = []
        
        if self.project_goals is None:
            self.project_goals = []


class IntelligentRCodeState(AgentState):
    """Enhanced state with learning and context data"""
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Dynamic context that evolves during conversation
    user_preferences: Dict[str, Any] = {}
    project_context: Dict[str, Any] = {}
    session_insights: Dict[str, Any] = {}
    
    # Learning data
    successful_patterns: List[Dict[str, Any]] = []
    user_feedback: List[Dict[str, Any]] = []
    code_style_adaptations: Dict[str, Any] = {}
    
    # Task tracking
    current_task_complexity: str = "medium"
    task_history: List[Dict[str, Any]] = []
    solution_quality_scores: List[float] = []
    
    # Project intelligence
    project_architecture: Dict[str, Any] = {}
    dependency_graph: Dict[str, Any] = {}
    recent_changes: List[Dict[str, Any]] = []


class UserLearningStore:
    """Persistent learning storage for cross-conversation memory"""
    
    def __init__(self, storage_dir: str = ".rcode/learning"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_profiles_file = self.storage_dir / "user_profiles.json"
        self.project_memories_file = self.storage_dir / "project_memories.json"
        self.learning_patterns_file = self.storage_dir / "learning_patterns.json"
    
    def load_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Load persistent user profile"""
        try:
            if self.user_profiles_file.exists():
                with open(self.user_profiles_file, 'r') as f:
                    profiles = json.load(f)
                    return profiles.get(user_id, {})
        except Exception as e:
            print(f"⚠️  Error loading user profile: {e}")
        return {}
    
    def save_user_profile(self, user_id: str, profile: Dict[str, Any]):
        """Save persistent user profile"""
        try:
            profiles = {}
            if self.user_profiles_file.exists():
                with open(self.user_profiles_file, 'r') as f:
                    profiles = json.load(f)
            
            profiles[user_id] = profile
            profiles[user_id]['last_updated'] = datetime.now().isoformat()
            
            with open(self.user_profiles_file, 'w') as f:
                json.dump(profiles, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving user profile: {e}")
    
    def load_project_memory(self, project_root: str) -> Dict[str, Any]:
        """Load persistent project memory"""
        try:
            if self.project_memories_file.exists():
                with open(self.project_memories_file, 'r') as f:
                    memories = json.load(f)
                    return memories.get(project_root, {})
        except Exception as e:
            print(f"⚠️  Error loading project memory: {e}")
        return {}
    
    def save_project_memory(self, project_root: str, memory: Dict[str, Any]):
        """Save persistent project memory"""
        try:
            memories = {}
            if self.project_memories_file.exists():
                with open(self.project_memories_file, 'r') as f:
                    memories = json.load(f)
            
            memories[project_root] = memory
            memories[project_root]['last_updated'] = datetime.now().isoformat()
            
            with open(self.project_memories_file, 'w') as f:
                json.dump(memories, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving project memory: {e}")
    
    def learn_from_interaction(self, interaction_data: Dict[str, Any]):
        """Learn from successful interactions"""
        try:
            patterns = []
            if self.learning_patterns_file.exists():
                with open(self.learning_patterns_file, 'r') as f:
                    patterns = json.load(f)
            
            interaction_data['timestamp'] = datetime.now().isoformat()
            patterns.append(interaction_data)
            
            # Keep only recent patterns (last 1000)
            patterns = patterns[-1000:]
            
            with open(self.learning_patterns_file, 'w') as f:
                json.dump(patterns, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving learning pattern: {e}")


class DynamicPromptGenerator:
    """Generates context-aware, adaptive system prompts"""
    
    def __init__(self, learning_store: UserLearningStore):
        self.learning_store = learning_store
        self.base_prompt = get_system_prompt()
    
    def generate_prompt(self, state: IntelligentRCodeState, context: RCodeContext) -> str:
        """Generate dynamic system prompt based on context and learning"""
        
        # Load persistent user data
        user_profile = self.learning_store.load_user_profile(context.user_id)
        project_memory = self.learning_store.load_project_memory(context.project_root)
        
        # Build adaptive prompt
        prompt_parts = [self.base_prompt]
        
        # Add user-specific context
        if context.user_name != "Developer":
            prompt_parts.append(f"\n## User Context\nYou are assisting {context.user_name} with their coding tasks.")
        
        # Add coding style preferences
        if context.coding_style:
            style_text = self._format_coding_style(context.coding_style)
            prompt_parts.append(f"\n## Coding Style Preferences\n{style_text}")
        
        # Add learned user patterns
        if user_profile:
            learned_preferences = self._format_learned_preferences(user_profile)
            if learned_preferences:
                prompt_parts.append(f"\n## Learned User Patterns\n{learned_preferences}")
        
        # Add project context
        if project_memory or context.tech_stack:
            project_context = self._format_project_context(context, project_memory)
            prompt_parts.append(f"\n## Project Intelligence\n{project_context}")
        
        # Add session insights (handle both dict and object state)
        session_insights = getattr(state, 'session_insights', None) or state.get('session_insights', {})
        if session_insights:
            insights = self._format_session_insights(session_insights)
            prompt_parts.append(f"\n## Current Session Context\n{insights}")
        
        # Add task complexity adaptation
        current_complexity = getattr(state, 'current_task_complexity', None) or state.get('current_task_complexity', 'medium')
        complexity_guidance = self._get_complexity_guidance(current_complexity)
        prompt_parts.append(f"\n## Task Complexity Guidance\n{complexity_guidance}")
        
        # Add recent learning patterns
        successful_patterns = getattr(state, 'successful_patterns', None) or state.get('successful_patterns', [])
        if successful_patterns:
            patterns = self._format_successful_patterns(successful_patterns[-3:])  # Last 3
            prompt_parts.append(f"\n## Recent Successful Patterns\n{patterns}")
        
        return "\n".join(prompt_parts)
    
    def _format_coding_style(self, style: Dict[str, Any]) -> str:
        """Format coding style preferences"""
        style_lines = []
        for key, value in style.items():
            formatted_key = key.replace('_', ' ').title()
            style_lines.append(f"- {formatted_key}: {value}")
        return "\n".join(style_lines)
    
    def _format_learned_preferences(self, profile: Dict[str, Any]) -> str:
        """Format learned user preferences"""
        patterns = []
        
        if profile.get('preferred_solutions'):
            patterns.append(f"- Prefers: {', '.join(profile['preferred_solutions'])}")
        
        if profile.get('common_tasks'):
            patterns.append(f"- Common tasks: {', '.join(profile['common_tasks'])}")
        
        if profile.get('feedback_patterns'):
            patterns.append(f"- Feedback patterns: {profile['feedback_patterns']}")
        
        return "\n".join(patterns) if patterns else ""
    
    def _format_project_context(self, context: RCodeContext, memory: Dict[str, Any]) -> str:
        """Format project intelligence context"""
        lines = []
        
        if context.project_type != "general":
            lines.append(f"- Project Type: {context.project_type}")
        
        if context.tech_stack:
            lines.append(f"- Tech Stack: {', '.join(context.tech_stack)}")
        
        if context.project_goals:
            lines.append(f"- Goals: {', '.join(context.project_goals)}")
        
        if memory.get('architecture_patterns'):
            lines.append(f"- Known Patterns: {', '.join(memory['architecture_patterns'])}")
        
        if memory.get('common_issues'):
            lines.append(f"- Previous Challenges: {memory['common_issues']}")
        
        return "\n".join(lines)
    
    def _format_session_insights(self, insights: Dict[str, Any]) -> str:
        """Format current session insights"""
        lines = []
        
        if insights.get('user_mood'):
            lines.append(f"- User appears: {insights['user_mood']}")
        
        if insights.get('task_focus'):
            lines.append(f"- Current focus: {insights['task_focus']}")
        
        if insights.get('help_level_needed'):
            lines.append(f"- Help level: {insights['help_level_needed']}")
        
        return "\n".join(lines)
    
    def _get_complexity_guidance(self, complexity: str) -> str:
        """Get task complexity-specific guidance"""
        guidance = {
            "simple": "Provide concise, straightforward solutions. Minimize explanation unless asked.",
            "medium": "Balance detail with clarity. Explain key concepts and provide examples.",
            "advanced": "Provide comprehensive solutions with detailed explanations, alternatives, and best practices."
        }
        return guidance.get(complexity, guidance["medium"])
    
    def _format_successful_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format recent successful patterns"""
        lines = []
        for pattern in patterns:
            if pattern.get('solution_type') and pattern.get('success_rating', 0) > 0.8:
                lines.append(f"- Successful: {pattern['solution_type']} (rating: {pattern['success_rating']:.1f})")
        return "\n".join(lines)


class IntelligentRCodeAgent:
    """Enhanced R-Code AI agent with learning and intelligent context"""
    
    def __init__(self):
        """Initialize intelligent R-Code agent"""
        self.checkpointer = InMemorySaver()
        self.models = {}
        self.graph = None
        self.config = config_manager.load_config()
        self.custom_rules = config_manager.load_rules()
        self.mcp_initialized = False
        
        # Initialize learning system
        self.learning_store = UserLearningStore()
        self.prompt_generator = DynamicPromptGenerator(self.learning_store)
        
        # Initialize checkpoint system
        self.checkpoint_manager = CheckpointManager()
        self.slash_command_handler = SlashCommandHandler(self.checkpoint_manager)
        
        # Initialize checkpoint-aware file operations
        initialize_checkpoint_file_ops(self.checkpoint_manager)
        
        # Initialize context provider
        project_root = os.getcwd()
        self.context_provider = ContextProvider(project_root)
        
        # Initialize everything
        self._initialize_models()
        
        # Build graph will be called after context is set
    
    async def initialize_mcp(self):
        """Initialize MCP servers from configuration"""
        if self.mcp_initialized:
            return
            
        try:
            mcp_servers = config_manager.get_enabled_mcp_servers()
            if mcp_servers:
                success = await initialize_mcp_from_config(mcp_servers)
                if success:
                    self.mcp_initialized = True
                    print("✅ MCP integration completed")
            else:
                print("ℹ️  No MCP servers configured")
                self.mcp_initialized = True
        except Exception as e:
            print(f"⚠️  MCP initialization failed: {e}")
            self.mcp_initialized = True
    
    @classmethod
    async def create(cls, context: RCodeContext = None):
        """Create and initialize IntelligentRCodeAgent with context"""
        agent = cls()
        await agent.initialize_mcp()
        
        # Set default context if none provided
        if context is None:
            context = RCodeContext(
                project_root=os.getcwd(),
                session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
        
        # Build graph with context
        agent._build_graph(context)
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
            raise RuntimeError("No models available! Please check:\n"
                             "1. API keys are set in environment variables\n"
                             "2. Models are enabled in .rcode/config.json\n"
                             "3. Configuration is valid")
    
    def _build_graph(self, context: RCodeContext):
        """Build intelligent graph with dynamic prompts and context awareness"""
        # Get all available tools
        tools = []
        
        # Add web search tools if available and enabled
        tool_config = self.config.get("tools", {})
        if tool_config.get("web_search", {}).get("enabled", True) and is_web_search_available():
            tools.extend(get_web_search_tools())
        
        # Add checkpoint-aware file operation tools if enabled
        if tool_config.get("file_operations", {}).get("enabled", True):
            tools.extend(get_checkpoint_aware_file_operation_tools())
        
        # Add approval-aware terminal operation tools if enabled
        if tool_config.get("terminal_operations", {}).get("enabled", True):
            tools.extend(get_approval_aware_terminal_tools())
        
        # Add MCP tools if available
        if is_mcp_available():
            tools.extend(get_mcp_tools())
        
        # Add MCP info tools
        tools.extend(get_mcp_info_tools())
        
        # Add context-aware tools
        tools.extend(get_context_tools())
        
        # Get primary model
        primary_model_key = self.config.get("models", {}).get("primary", "claude")
        fallback_model_key = self.config.get("models", {}).get("fallback", "openai")
        
        self.primary_model = self.models.get(primary_model_key, self.models.get(fallback_model_key))
        if not self.primary_model:
            self.primary_model = list(self.models.values())[0]
        
        # Dynamic prompt function
        def dynamic_prompt(state: IntelligentRCodeState) -> List[AnyMessage]:
            """Generate dynamic system prompt based on state and context"""
            prompt_content = self.prompt_generator.generate_prompt(state, context)
            
            # Add custom rules if present
            if self.custom_rules:
                prompt_content += f"\n\n## Custom User Rules:\n{self.custom_rules}"
            
            return [{"role": "system", "content": prompt_content}] + state["messages"]
        
        # Create react agent with dynamic prompts
        self.graph = create_react_agent(
            self.primary_model,
            tools,
            checkpointer=self.checkpointer,
            state_schema=IntelligentRCodeState,
            prompt=dynamic_prompt
        )
    
    def learn_from_interaction(self, user_input: str, ai_response: str, user_feedback: str = None, success_rating: float = None):
        """Learn from user interactions to improve future responses"""
        interaction_data = {
            "user_input": user_input,
            "ai_response": ai_response[:500],  # Truncate for storage
            "user_feedback": user_feedback,
            "success_rating": success_rating,
            "session_id": getattr(self, 'current_session_id', 'unknown'),
            "task_type": self._classify_task_type(user_input)
        }
        
        self.learning_store.learn_from_interaction(interaction_data)
    
    def _classify_task_type(self, user_input: str) -> str:
        """Classify the type of task from user input"""
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ['debug', 'error', 'fix', 'bug']):
            return 'debugging'
        elif any(word in input_lower for word in ['create', 'build', 'make', 'implement']):
            return 'creation'
        elif any(word in input_lower for word in ['explain', 'how', 'what', 'why']):
            return 'explanation'
        elif any(word in input_lower for word in ['optimize', 'improve', 'refactor']):
            return 'optimization'
        elif any(word in input_lower for word in ['test', 'testing', 'unittest']):
            return 'testing'
        else:
            return 'general'
    
    def update_user_context(self, context_updates: Dict[str, Any], user_id: str = "default"):
        """Update user context and save to persistent storage"""
        user_profile = self.learning_store.load_user_profile(user_id)
        user_profile.update(context_updates)
        self.learning_store.save_user_profile(user_id, user_profile)
    
    def update_project_memory(self, memory_updates: Dict[str, Any], project_root: str = None):
        """Update project memory and save to persistent storage"""
        if project_root is None:
            project_root = os.getcwd()
        
        project_memory = self.learning_store.load_project_memory(project_root)
        project_memory.update(memory_updates)
        self.learning_store.save_project_memory(project_root, project_memory)
    
    async def astream_chat(self, message: str, context: RCodeContext = None, thread_id: str = "default"):
        """Enhanced async streaming with learning and context adaptation"""
        if context is None:
            context = RCodeContext()
        
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
        
        # Rebuild graph if context changed significantly
        if not hasattr(self, 'graph') or not self.graph:
            self._build_graph(context)
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Initialize state with learning data
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_preferences": self.learning_store.load_user_profile(context.user_id),
            "project_context": self.learning_store.load_project_memory(context.project_root),
            "current_task_complexity": self._assess_task_complexity(message),
            "session_insights": self._generate_session_insights(message)
        }
        
        ai_response_parts = []
        
        # Stream with enhanced context
        async for stream_mode, chunk in self.graph.astream(
            initial_state,
            config,
            stream_mode=["updates", "messages"]
        ):
            if stream_mode == "updates":
                # Handle tool execution updates
                for node_name, node_output in chunk.items():
                    if node_name == "tools":
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, 'content') and msg.content:
                                    tool_name = getattr(msg, 'name', 'Tool')
                                    yield {"type": "tool_result", "content": str(msg.content), "tool_name": tool_name}
                    
                    elif node_name == "agent":
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, 'content') and isinstance(msg.content, list):
                                    for item in msg.content:
                                        if isinstance(item, dict) and item.get('type') == 'tool_use':
                                            tool_name = item.get('name', 'Tool')
                                            yield {"type": "tool_use", "tool_name": tool_name}
            
            elif stream_mode == "messages":
                # Handle AI response streaming
                message_chunk, metadata = chunk
                if hasattr(message_chunk, 'content') and message_chunk.content:
                    if isinstance(message_chunk.content, str):
                        ai_response_parts.append(message_chunk.content)
                        yield {"type": "token", "content": message_chunk.content}
                    elif isinstance(message_chunk.content, list):
                        for item in message_chunk.content:
                            if isinstance(item, dict) and item.get('type') == 'text' and item.get('text'):
                                ai_response_parts.append(item['text'])
                                yield {"type": "token", "content": item['text']}
        
        # Learn from this interaction
        full_ai_response = ''.join(ai_response_parts)
        if full_ai_response:
            # Auto-assess quality based on response characteristics
            success_rating = self._auto_assess_response_quality(message, full_ai_response)
            self.learn_from_interaction(message, full_ai_response, success_rating=success_rating)
    
    def _assess_task_complexity(self, message: str) -> str:
        """Assess task complexity from user message"""
        message_lower = message.lower()
        
        # Complex indicators
        complex_indicators = ['architecture', 'design pattern', 'system design', 'optimization', 'performance', 'scale']
        if any(indicator in message_lower for indicator in complex_indicators):
            return "advanced"
        
        # Simple indicators
        simple_indicators = ['hello', 'hi', 'help', 'quick question', 'simple']
        if any(indicator in message_lower for indicator in simple_indicators):
            return "simple"
        
        # Default to medium
        return "medium"
    
    def _generate_session_insights(self, message: str) -> Dict[str, Any]:
        """Generate insights about the current session"""
        insights = {}
        
        # Detect urgency
        if any(word in message.lower() for word in ['urgent', 'asap', 'quickly', 'fast']):
            insights['user_mood'] = 'urgent'
        elif any(word in message.lower() for word in ['please', 'help', 'stuck']):
            insights['user_mood'] = 'seeking_help'
        else:
            insights['user_mood'] = 'collaborative'
        
        # Detect focus area
        task_type = self._classify_task_type(message)
        insights['task_focus'] = task_type
        
        # Detect help level needed
        if '?' in message or any(word in message.lower() for word in ['how', 'what', 'why', 'explain']):
            insights['help_level_needed'] = 'explanation'
        elif any(word in message.lower() for word in ['show', 'example', 'demo']):
            insights['help_level_needed'] = 'demonstration'
        else:
            insights['help_level_needed'] = 'implementation'
        
        return insights
    
    def _auto_assess_response_quality(self, user_input: str, ai_response: str) -> float:
        """Auto-assess response quality based on various factors"""
        score = 0.5  # Base score
        
        # Length appropriateness
        if len(ai_response) > 100:  # Not too short
            score += 0.1
        if len(ai_response) < 2000:  # Not too long
            score += 0.1
        
        # Contains code if requested
        if any(word in user_input.lower() for word in ['code', 'function', 'class', 'implement']):
            if '```' in ai_response or 'def ' in ai_response or 'function' in ai_response:
                score += 0.2
        
        # Contains explanation if requested
        if any(word in user_input.lower() for word in ['explain', 'how', 'why', 'what']):
            if len(ai_response.split('.')) > 3:  # Multiple sentences
                score += 0.1
        
        return min(1.0, score)
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        try:
            patterns = []
            if self.learning_store.learning_patterns_file.exists():
                with open(self.learning_store.learning_patterns_file, 'r') as f:
                    patterns = json.load(f)
            
            stats = {
                "total_interactions": len(patterns),
                "task_types": {},
                "average_success_rating": 0.0,
                "recent_interactions": len([p for p in patterns if p.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))])
            }
            
            # Calculate task type distribution
            for pattern in patterns:
                task_type = pattern.get('task_type', 'unknown')
                stats['task_types'][task_type] = stats['task_types'].get(task_type, 0) + 1
            
            # Calculate average success rating
            ratings = [p.get('success_rating', 0) for p in patterns if p.get('success_rating')]
            if ratings:
                stats['average_success_rating'] = sum(ratings) / len(ratings)
            
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    def __str__(self) -> str:
        return f"IntelligentRCodeAgent(models={list(self.models.keys())}, learning_enabled=True)"

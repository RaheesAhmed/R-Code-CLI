"""
Agent Type Definitions for R-Code CLI
====================================

Type definitions specific to agent interfaces and configurations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .base_types import ChatMessage, TaskType, AgentStatus, ModelProvider
from .model_types import BaseModel, ModelResponse


@dataclass
class AgentConfig:
    """Configuration for agents"""
    name: str
    description: str
    supported_tasks: List[TaskType]
    default_model_provider: ModelProvider = ModelProvider.CLAUDE
    max_iterations: int = 10
    timeout: int = 300
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    memory_enabled: bool = True
    streaming: bool = True

    def __post_init__(self):
        if self.tools is None:
            self.tools = []


@dataclass
class AgentState:
    """Current state of an agent"""
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[TaskType] = None
    messages: List[ChatMessage] = field(default_factory=list)
    iteration_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_response: Optional[ModelResponse] = None
    error_message: Optional[str] = None

    def reset(self) -> None:
        """Reset agent state"""
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.messages = []
        self.iteration_count = 0
        self.metadata = {}
        self.last_response = None
        self.error_message = None

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)

    def get_conversation_context(self) -> str:
        """Get formatted conversation context"""
        context = []
        for msg in self.messages:
            context.append(f"{msg.role.value}: {msg.content}")
        return "\n\n".join(context)


@dataclass
class TaskRequest:
    """Represents a task request to an agent"""
    task_type: TaskType
    prompt: str
    context: Optional[Dict[str, Any]] = None
    files: Optional[List[str]] = None
    preferred_model: Optional[str] = None
    stream: bool = True
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.files is None:
            self.files = []


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_type: TaskType
    success: bool
    content: str
    model_used: str
    tokens_used: Optional[int] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "task_type": self.task_type.value,
            "success": self.success,
            "content": self.content,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "error_message": self.error_message
        }


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig, models: Dict[ModelProvider, BaseModel]):
        self.config = config
        self.models = models
        self.state = AgentState()
        self._callbacks: Dict[str, List[Callable]] = {}
    
    @abstractmethod
    async def execute_task(self, request: TaskRequest) -> TaskResult:
        """Execute a task"""
        pass
    
    @abstractmethod
    async def stream_task(self, request: TaskRequest) -> AsyncGenerator[str, None]:
        """Stream task execution"""
        pass
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Add a callback for an event"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, *args, **kwargs) -> None:
        """Trigger callbacks for an event"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    # Log error but don't stop execution
                    print(f"Callback error for {event}: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        models = []
        for provider, model in self.models.items():
            models.append(f"{provider.value}:{model.model_name}")
        return models
    
    def supports_task(self, task_type: TaskType) -> bool:
        """Check if agent supports a task type"""
        return task_type in self.config.supported_tasks
    
    def reset_state(self) -> None:
        """Reset agent state"""
        self.state.reset()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.config.name,
            "status": self.state.status.value,
            "current_task": self.state.current_task.value if self.state.current_task else None,
            "iteration_count": self.state.iteration_count,
            "message_count": len(self.state.messages),
            "available_models": self.get_available_models(),
            "supported_tasks": [task.value for task in self.config.supported_tasks]
        }


# Import AsyncGenerator properly
from typing import AsyncGenerator

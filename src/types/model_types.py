"""
Model Type Definitions for R-Code CLI
====================================

Type definitions specific to AI model interfaces and configurations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass

from .base_types import ModelProvider, ChatMessage, ModelResponse, TaskType


@dataclass
class ModelConfig:
    """Configuration for AI models"""
    provider: ModelProvider
    model_name: str
    api_key: str
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 30
    base_url: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class BaseModel(ABC):
    """Abstract base class for all AI model implementations"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.provider = config.provider
        self.model_name = config.model_name
        self._client = None
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the model client"""
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> ModelResponse:
        """Generate a response from the model"""
        pass
    
    @abstractmethod
    async def stream_response(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from the model"""
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate the API key"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass
    
    async def health_check(self) -> bool:
        """Check if the model is healthy and available"""
        try:
            return await self.validate_api_key()
        except Exception:
            return False
    
    def supports_task(self, task_type: TaskType) -> bool:
        """Check if model supports a specific task type"""
        # Default implementation - all models support all tasks
        return True
    
    def get_cost_per_token(self) -> Dict[str, float]:
        """Get cost per token for input/output"""
        # Default implementation - return 0 cost
        return {"input": 0.0, "output": 0.0}


@dataclass
class StreamChunk:
    """Represents a chunk of streamed response"""
    content: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModelCapabilities:
    """Describes what a model can do"""
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_code_generation: bool = True
    supports_streaming: bool = True
    max_context_length: int = 4000
    supports_system_messages: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "supports_function_calling": self.supports_function_calling,
            "supports_vision": self.supports_vision,
            "supports_code_generation": self.supports_code_generation,
            "supports_streaming": self.supports_streaming,
            "max_context_length": self.max_context_length,
            "supports_system_messages": self.supports_system_messages
        }

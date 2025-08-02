"""
Base Type Definitions for R-Code CLI
===================================

Core type definitions and enums used throughout the application.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod


class ModelProvider(Enum):
    """Supported AI model providers"""
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROK = "grok"
    OLLAMA = "ollama"


class MessageRole(Enum):
    """Chat message roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class TaskType(Enum):
    """Types of tasks the agent can perform"""
    CODE_GENERATION = "code_generation"
    CODE_FIXING = "code_fixing"
    CODE_ANALYSIS = "code_analysis"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata or {},
            "timestamp": self.timestamp
        }


@dataclass
class ModelResponse:
    """Response from an AI model"""
    content: str
    provider: ModelProvider
    model_name: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "content": self.content,
            "provider": self.provider.value,
            "model_name": self.model_name,
            "tokens_used": self.tokens_used,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata or {}
        }


@dataclass
class RCodeConfig:
    """Global R-Code configuration"""
    default_provider: ModelProvider = ModelProvider.CLAUDE
    api_keys: Dict[str, str] = None
    model_preferences: Dict[TaskType, str] = None
    max_tokens: int = 4000
    temperature: float = 0.1
    debug_mode: bool = False

    def __post_init__(self):
        if self.api_keys is None:
            self.api_keys = {}
        if self.model_preferences is None:
            self.model_preferences = {}

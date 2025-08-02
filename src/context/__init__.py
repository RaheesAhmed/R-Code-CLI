"""
R-Code Context System
====================

Comprehensive project context management system that provides AI with complete
project understanding including file relationships, code structure, imports/exports,
and real-time project state to prevent duplicates and code breaking.
"""

from .project_context_manager import ProjectContextManager
from .code_analyzer import CodeAnalyzer, FileAnalysis, ProjectAnalysis
from .relationship_mapper import RelationshipMapper, FileRelationship
from .context_provider import ContextProvider, get_context_tools
from .context_types import (
    ProjectContext,
    FileContext,
    CodeContext,
    RelationshipContext
)

__all__ = [
    "ProjectContextManager",
    "CodeAnalyzer", 
    "FileAnalysis",
    "ProjectAnalysis",
    "RelationshipMapper",
    "FileRelationship", 
    "ContextProvider",
    "get_context_tools",
    "ProjectContext",
    "FileContext",
    "CodeContext",
    "RelationshipContext"
]

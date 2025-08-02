"""
R-Code Context Types
===================

Data structures for comprehensive project context management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from enum import Enum


class FileType(Enum):
    """Types of files in the project"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TEXT = "text"
    CONFIG = "config"
    REQUIREMENTS = "requirements"
    PACKAGE_JSON = "package_json"
    DOCKERFILE = "dockerfile"
    UNKNOWN = "unknown"


class CodeElementType(Enum):
    """Types of code elements"""
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    EXPORT = "export"
    DECORATOR = "decorator"
    PROPERTY = "property"
    ASYNC_FUNCTION = "async_function"


class RelationshipType(Enum):
    """Types of relationships between files/code elements"""
    IMPORTS = "imports"
    EXPORTS = "exports"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    OVERRIDES = "overrides"


@dataclass
class CodeElement:
    """Represents a code element (class, function, variable, etc.)"""
    name: str
    type: CodeElementType
    line_start: int
    line_end: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False
    is_static: bool = False
    is_private: bool = False
    parent: Optional[str] = None  # Parent class/function
    children: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """Analysis of a single file"""
    file_path: str
    file_type: FileType
    size: int
    lines_of_code: int
    last_modified: datetime
    encoding: str
    hash_md5: str
    elements: List[CodeElement] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    complexity_score: int = 0
    maintainability_score: float = 0.0
    test_coverage: float = 0.0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class FileRelationship:
    """Relationship between two files"""
    source_file: str
    target_file: str
    relationship_type: RelationshipType
    elements: List[str] = field(default_factory=list)  # Specific elements involved
    strength: float = 1.0  # Relationship strength (0-1)
    bidirectional: bool = False


@dataclass
class DirectoryStructure:
    """Represents directory structure and organization"""
    path: str
    name: str
    type: str  # 'directory' or 'file'
    size: int
    file_count: int
    children: List['DirectoryStructure'] = field(default_factory=list)
    file_types: Dict[FileType, int] = field(default_factory=dict)
    description: Optional[str] = None
    purpose: Optional[str] = None


@dataclass
class ProjectMetadata:
    """Project-level metadata"""
    name: str
    root_path: str
    project_type: str
    language: str
    framework: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    scripts: Dict[str, str] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)
    test_directories: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    documentation_files: List[str] = field(default_factory=list)
    build_files: List[str] = field(default_factory=list)


@dataclass
class ProjectAnalysis:
    """Complete project analysis"""
    metadata: ProjectMetadata
    directory_structure: DirectoryStructure
    files: Dict[str, FileAnalysis] = field(default_factory=dict)
    relationships: List[FileRelationship] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    architecture_patterns: List[str] = field(default_factory=list)
    code_metrics: Dict[str, Any] = field(default_factory=dict)
    quality_scores: Dict[str, float] = field(default_factory=dict)
    potential_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    last_analyzed: datetime = field(default_factory=datetime.now)


@dataclass
class FileContext:
    """Context for a specific file"""
    file_path: str
    analysis: FileAnalysis
    related_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    similar_files: List[str] = field(default_factory=list)
    modification_history: List[datetime] = field(default_factory=list)
    current_content: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CodeContext:
    """Context for code operations"""
    operation_type: str
    target_files: List[str] = field(default_factory=list)
    affected_elements: List[str] = field(default_factory=list)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    safety_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class RelationshipContext:
    """Context about file and code relationships"""
    file_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    reverse_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    circular_dependencies: List[List[str]] = field(default_factory=list)
    unused_imports: Dict[str, List[str]] = field(default_factory=dict)
    missing_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    coupling_metrics: Dict[str, float] = field(default_factory=dict)
    cohesion_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ProjectContext:
    """Complete project context for AI operations"""
    project_analysis: ProjectAnalysis
    file_contexts: Dict[str, FileContext] = field(default_factory=dict)
    relationship_context: RelationshipContext = field(default_factory=RelationshipContext)
    current_state: Dict[str, Any] = field(default_factory=dict)
    recent_changes: List[Dict[str, Any]] = field(default_factory=list)
    active_patterns: List[str] = field(default_factory=list)
    naming_conventions: Dict[str, str] = field(default_factory=dict)
    coding_standards: Dict[str, Any] = field(default_factory=dict)
    best_practices: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def get_summary(self) -> str:
        """Get a comprehensive summary of the project context"""
        total_files = len(self.project_analysis.files)
        total_lines = sum(file.lines_of_code for file in self.project_analysis.files.values())
        main_language = self.project_analysis.metadata.language
        
        return f"""
Project: {self.project_analysis.metadata.name}
Type: {self.project_analysis.metadata.project_type}
Language: {main_language}
Files: {total_files}
Lines of Code: {total_lines}
Dependencies: {len(self.project_analysis.metadata.dependencies)}
Architecture Patterns: {', '.join(self.project_analysis.architecture_patterns)}
Quality Score: {self.project_analysis.quality_scores.get('overall', 0.0):.2f}
Last Analyzed: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
    
    def get_file_suggestions(self, operation: str, target_path: str) -> List[str]:
        """Get suggestions for file operations to prevent conflicts"""
        suggestions = []
        
        # Check for duplicates
        target_name = Path(target_path).name
        similar_files = [
            path for path in self.project_analysis.files.keys()
            if Path(path).name.lower() == target_name.lower()
        ]
        
        if similar_files:
            suggestions.append(f"⚠️  Similar files found: {', '.join(similar_files)}")
        
        # Check for naming conventions
        if target_path in self.file_contexts:
            context = self.file_contexts[target_path]
            if context.recommendations:
                suggestions.extend(context.recommendations)
        
        return suggestions
    
    def validate_operation(self, operation: str, target: str) -> Dict[str, Any]:
        """Validate an operation against project context"""
        return {
            "safe": True,
            "warnings": [],
            "suggestions": self.get_file_suggestions(operation, target),
            "impact": "low"
        }

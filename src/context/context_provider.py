"""
R-Code Context Provider
======================

LangGraph integration layer that provides comprehensive project context
to AI agents for intelligent, context-aware operations.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from langchain_core.tools import tool
from langgraph.runtime import get_runtime

from .project_context_manager import ProjectContextManager
from .context_types import ProjectContext, FileContext, CodeContext


class ContextProvider:
    """Provides project context to LangGraph agents"""
    
    def __init__(self, project_root: str):
        """Initialize context provider"""
        self.project_root = project_root
        self.context_manager = ProjectContextManager(project_root)
        self._current_context: Optional[ProjectContext] = None
    
    def get_project_context(self, force_refresh: bool = False) -> ProjectContext:
        """Get comprehensive project context"""
        if force_refresh or self._current_context is None:
            self._current_context = self.context_manager.get_project_context(force_refresh)
        return self._current_context
    
    def get_context_for_operation(self, operation: str, target_path: str = None, 
                                 content: str = None) -> CodeContext:
        """Get context optimized for a specific operation"""
        project_context = self.get_project_context()
        
        # Analyze the operation and its impact
        impact_analysis = self._analyze_operation_impact(operation, target_path, content, project_context)
        
        # Generate safety checks
        safety_checks = self._generate_safety_checks(operation, target_path, project_context)
        
        # Generate warnings
        warnings = self._generate_warnings(operation, target_path, project_context)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(operation, target_path, project_context)
        
        return CodeContext(
            operation_type=operation,
            target_files=[target_path] if target_path else [],
            impact_analysis=impact_analysis,
            safety_checks=safety_checks,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _analyze_operation_impact(self, operation: str, target_path: str, 
                                content: str, context: ProjectContext) -> Dict[str, Any]:
        """Analyze the potential impact of an operation"""
        impact = {
            "risk_level": "low",
            "affected_files": [],
            "dependency_impact": [],
            "breaking_changes": [],
            "recommendations": []
        }
        
        if not target_path:
            return impact
        
        # Check if file exists and analyze dependencies
        if target_path in context.file_contexts:
            file_context = context.file_contexts[target_path]
            
            # Files that depend on this one might be affected
            impact["affected_files"] = file_context.dependents
            
            # Check for breaking changes
            if operation in ["delete", "rename", "move"]:
                impact["risk_level"] = "high"
                impact["breaking_changes"].append(f"Operation '{operation}' on '{target_path}' may break dependent files")
            
            # Dependency impact
            if file_context.dependencies:
                impact["dependency_impact"] = file_context.dependencies
        
        # Check for duplicate files
        if operation == "create":
            target_name = Path(target_path).name
            similar_files = [
                path for path in context.project_analysis.files.keys()
                if Path(path).name.lower() == target_name.lower()
            ]
            
            if similar_files:
                impact["risk_level"] = "medium"
                impact["recommendations"].append(f"Similar files exist: {', '.join(similar_files[:3])}")
        
        return impact
    
    def _generate_safety_checks(self, operation: str, target_path: str, 
                              context: ProjectContext) -> List[str]:
        """Generate safety checks for the operation"""
        checks = []
        
        if operation == "create" and target_path:
            # Check for naming convention compliance
            if context.naming_conventions:
                file_name = Path(target_path).stem
                if "files" in context.naming_conventions:
                    convention = context.naming_conventions["files"]
                    if convention == "snake_case" and "-" in file_name:
                        checks.append(f"File name '{file_name}' should use snake_case convention")
                    elif convention == "kebab-case" and "_" in file_name:
                        checks.append(f"File name '{file_name}' should use kebab-case convention")
            
            # Check directory structure consistency
            target_dir = str(Path(target_path).parent)
            similar_files_in_dir = [
                path for path in context.project_analysis.files.keys()
                if str(Path(path).parent) == target_dir
            ]
            
            if similar_files_in_dir:
                # Check if file type matches directory pattern
                target_ext = Path(target_path).suffix
                dir_extensions = set(Path(p).suffix for p in similar_files_in_dir)
                
                if target_ext not in dir_extensions and dir_extensions:
                    checks.append(f"File extension '{target_ext}' is uncommon in directory '{target_dir}'")
        
        elif operation == "modify" and target_path:
            if target_path in context.file_contexts:
                file_context = context.file_contexts[target_path]
                
                # Check if modifying a critical file
                if len(file_context.dependents) > 5:
                    checks.append(f"Modifying '{target_path}' may affect {len(file_context.dependents)} dependent files")
                
                # Check for circular dependency risk
                circular_deps = context.relationship_context.circular_dependencies
                for cycle in circular_deps:
                    if target_path in cycle:
                        checks.append(f"File is part of circular dependency: {' -> '.join(cycle)}")
        
        elif operation == "delete" and target_path:
            if target_path in context.file_contexts:
                file_context = context.file_contexts[target_path]
                
                if file_context.dependents:
                    checks.append(f"Deleting '{target_path}' will break {len(file_context.dependents)} dependent files")
        
        return checks
    
    def _generate_warnings(self, operation: str, target_path: str, 
                         context: ProjectContext) -> List[str]:
        """Generate warnings for the operation"""
        warnings = []
        
        # Check for anti-patterns
        if operation == "create" and target_path:
            target_dir = str(Path(target_path).parent)
            
            # Warn about creating files in high-coupling areas
            high_coupling_files = [
                path for path, score in context.relationship_context.coupling_metrics.items()
                if score > 0.7 and str(Path(path).parent) == target_dir
            ]
            
            if high_coupling_files:
                warnings.append(f"Directory '{target_dir}' has high coupling - consider refactoring before adding new files")
        
        # Check for potential naming conflicts
        if target_path and operation in ["create", "rename"]:
            target_name = Path(target_path).stem.lower()
            similar_names = [
                path for path in context.project_analysis.files.keys()
                if Path(path).stem.lower() == target_name and path != target_path
            ]
            
            if similar_names:
                warnings.append(f"Similar file names exist: {', '.join(similar_names[:2])}")
        
        return warnings
    
    def _generate_suggestions(self, operation: str, target_path: str, 
                            context: ProjectContext) -> List[str]:
        """Generate helpful suggestions for the operation"""
        suggestions = []
        
        if operation == "create" and target_path:
            # Suggest better locations based on project structure
            target_ext = Path(target_path).suffix
            target_dir = str(Path(target_path).parent)
            
            # Find directories with similar file types
            similar_dirs = {}
            for file_path in context.project_analysis.files.keys():
                if Path(file_path).suffix == target_ext:
                    dir_path = str(Path(file_path).parent)
                    similar_dirs[dir_path] = similar_dirs.get(dir_path, 0) + 1
            
            # Suggest most common directory for this file type
            if similar_dirs and target_dir not in similar_dirs:
                best_dir = max(similar_dirs, key=similar_dirs.get)
                if similar_dirs[best_dir] > 2:  # Only suggest if significant
                    suggestions.append(f"Consider placing {target_ext} files in '{best_dir}' (used by {similar_dirs[best_dir]} similar files)")
            
            # Suggest following naming conventions
            if context.naming_conventions.get("files"):
                convention = context.naming_conventions["files"]
                file_name = Path(target_path).stem
                
                if convention == "snake_case" and any(c.isupper() for c in file_name):
                    snake_name = file_name.lower().replace(' ', '_').replace('-', '_')
                    suggestions.append(f"Consider using snake_case: '{snake_name}{Path(target_path).suffix}'")
                elif convention == "kebab-case" and ('_' in file_name or any(c.isupper() for c in file_name)):
                    kebab_name = file_name.lower().replace('_', '-').replace(' ', '-')
                    suggestions.append(f"Consider using kebab-case: '{kebab_name}{Path(target_path).suffix}'")
        
        # Suggest adding documentation
        if operation in ["create", "modify"] and target_path:
            if Path(target_path).suffix == ".py":
                suggestions.append("Consider adding comprehensive docstrings following project standards")
                
                # Detect docstring style from context
                if context.coding_standards.get("docstring_style"):
                    style = context.coding_standards["docstring_style"]
                    suggestions.append(f"Use {style}-style docstrings to match project convention")
        
        # Suggest tests
        if operation == "create" and target_path and not "test" in target_path.lower():
            if Path(target_path).suffix in [".py", ".js", ".ts"]:
                suggestions.append("Consider creating corresponding test files")
        
        return suggestions


# LangGraph tool integrations
@tool
def get_project_context_summary() -> str:
    """
    Get a comprehensive summary of the current project context.
    
    This tool provides the AI with complete project understanding including:
    - Project structure and organization
    - File relationships and dependencies
    - Code metrics and quality scores
    - Architecture patterns and frameworks
    - Naming conventions and coding standards
    
    Use this tool at the beginning of conversations to understand the project.
    
    Returns:
        Comprehensive project context summary
    """
    try:
        # Try to get runtime context, fall back to current directory
        try:
            runtime = get_runtime()
            project_root = runtime.context.get("project_root", ".") if runtime and runtime.context else "."
        except:
            project_root = "."
        
        provider = ContextProvider(project_root)
        context = provider.get_project_context()
        
        return context.get_summary()
        
    except Exception as e:
        return f"❌ Failed to get project context: {str(e)}"


@tool
def validate_file_operation(operation: str, target_path: str, content: str = None) -> str:
    """
    Validate a file operation against project context to prevent conflicts and mistakes.
    
    This tool analyzes the impact of file operations and provides:
    - Safety checks for the operation
    - Warnings about potential issues
    - Suggestions for better approaches
    - Impact analysis on related files
    
    Use this tool before creating, modifying, or deleting files.
    
    Args:
        operation: Type of operation (create, modify, delete, rename, move)
        target_path: Path of the target file
        content: File content (for create/modify operations)
        
    Returns:
        Detailed validation results with recommendations
    """
    try:
        # Try to get runtime context, fall back to current directory
        try:
            runtime = get_runtime()
            project_root = runtime.context.get("project_root", ".") if runtime and runtime.context else "."
        except:
            project_root = "."
        
        provider = ContextProvider(project_root)
        code_context = provider.get_context_for_operation(operation, target_path, content)
        
        result = f"🔍 Operation Validation: {operation} on {target_path}\n\n"
        
        # Impact analysis
        impact = code_context.impact_analysis
        result += f"📊 Risk Level: {impact['risk_level'].upper()}\n"
        
        if impact['affected_files']:
            result += f"📁 Affected Files: {len(impact['affected_files'])}\n"
            for file in impact['affected_files'][:3]:
                result += f"  • {file}\n"
            if len(impact['affected_files']) > 3:
                result += f"  • ... and {len(impact['affected_files']) - 3} more\n"
        
        # Safety checks
        if code_context.safety_checks:
            result += f"\n🛡️ Safety Checks:\n"
            for check in code_context.safety_checks:
                result += f"  • {check}\n"
        
        # Warnings
        if code_context.warnings:
            result += f"\n⚠️ Warnings:\n"
            for warning in code_context.warnings:
                result += f"  • {warning}\n"
        
        # Suggestions
        if code_context.suggestions:
            result += f"\n💡 Suggestions:\n"
            for suggestion in code_context.suggestions:
                result += f"  • {suggestion}\n"
        
        # Breaking changes
        if impact['breaking_changes']:
            result += f"\n🚨 Breaking Changes:\n"
            for change in impact['breaking_changes']:
                result += f"  • {change}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to validate operation: {str(e)}"


@tool
def get_file_context(file_path: str) -> str:
    """
    Get detailed context for a specific file.
    
    This tool provides comprehensive information about a file including:
    - File analysis (classes, functions, imports, exports)
    - Dependencies and dependents
    - Similar files in the project
    - File-specific recommendations
    - Code quality metrics
    
    Use this tool when working with specific files to understand their role in the project.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Detailed file context information
    """
    try:
        runtime = get_runtime()
        project_root = runtime.context.get("project_root", ".")
        
        provider = ContextProvider(project_root)
        file_context = provider.context_manager.get_file_context(file_path)
        
        if not file_context:
            return f"❌ File not found or not analyzed: {file_path}"
        
        analysis = file_context.analysis
        
        result = f"📄 File Context: {file_path}\n\n"
        result += f"📊 Type: {analysis.file_type.value}\n"
        result += f"📏 Size: {analysis.size} bytes ({analysis.lines_of_code} LOC)\n"
        result += f"🔧 Complexity: {analysis.complexity_score}\n"
        result += f"🏷️ Maintainability: {analysis.maintainability_score:.2f}\n"
        
        if analysis.classes:
            result += f"\n🏗️ Classes ({len(analysis.classes)}):\n"
            for cls in analysis.classes[:5]:
                result += f"  • {cls}\n"
            if len(analysis.classes) > 5:
                result += f"  • ... and {len(analysis.classes) - 5} more\n"
        
        if analysis.functions:
            result += f"\n⚙️ Functions ({len(analysis.functions)}):\n"
            for func in analysis.functions[:5]:
                result += f"  • {func}\n"
            if len(analysis.functions) > 5:
                result += f"  • ... and {len(analysis.functions) - 5} more\n"
        
        if analysis.imports:
            result += f"\n📥 Imports ({len(analysis.imports)}):\n"
            for imp in analysis.imports[:5]:
                result += f"  • {imp}\n"
            if len(analysis.imports) > 5:
                result += f"  • ... and {len(analysis.imports) - 5} more\n"
        
        if file_context.dependencies:
            result += f"\n🔗 Dependencies ({len(file_context.dependencies)}):\n"
            for dep in file_context.dependencies[:3]:
                result += f"  • {dep}\n"
            if len(file_context.dependencies) > 3:
                result += f"  • ... and {len(file_context.dependencies) - 3} more\n"
        
        if file_context.dependents:
            result += f"\n⬅️ Dependents ({len(file_context.dependents)}):\n"
            for dep in file_context.dependents[:3]:
                result += f"  • {dep}\n"
            if len(file_context.dependents) > 3:
                result += f"  • ... and {len(file_context.dependents) - 3} more\n"
        
        if file_context.recommendations:
            result += f"\n💡 Recommendations:\n"
            for rec in file_context.recommendations:
                result += f"  • {rec}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to get file context: {str(e)}"


@tool 
def refresh_project_context() -> str:
    """
    Force refresh of the project context analysis.
    
    This tool rebuilds the complete project context from scratch, useful when:
    - Significant changes have been made to the project
    - New files have been added or removed
    - Project structure has changed
    - You want the most up-to-date analysis
    
    Returns:
        Status of the refresh operation
    """
    try:
        runtime = get_runtime()
        project_root = runtime.context.get("project_root", ".")
        
        provider = ContextProvider(project_root)
        context = provider.get_project_context(force_refresh=True)
        
        return f"✅ Project context refreshed successfully!\n\n{context.get_summary()}"
        
    except Exception as e:
        return f"❌ Failed to refresh project context: {str(e)}"


def get_context_tools() -> List:
    """Get list of context-aware tools for LangGraph integration"""
    return [
        get_project_context_summary,
        validate_file_operation,
        get_file_context,
        refresh_project_context
    ]

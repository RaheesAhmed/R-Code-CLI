"""
R-Code Code Analyzer
===================

Advanced code analysis system that parses files to understand structure,
relationships, imports, exports, classes, functions, and dependencies.
"""

import ast
import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime
import json

from .context_types import (
    FileType, CodeElementType, FileAnalysis, CodeElement, 
    ProjectMetadata, DirectoryStructure, ProjectAnalysis
)


class CodeAnalyzer:
    """Advanced code analyzer for comprehensive project understanding"""
    
    def __init__(self):
        """Initialize the code analyzer"""
        self.file_type_patterns = {
            FileType.PYTHON: ['.py', '.pyw', '.pyi'],
            FileType.JAVASCRIPT: ['.js', '.jsx', '.mjs'],
            FileType.TYPESCRIPT: ['.ts', '.tsx', '.d.ts'],
            FileType.JSON: ['.json'],
            FileType.YAML: ['.yml', '.yaml'],
            FileType.MARKDOWN: ['.md', '.markdown'],
            FileType.CONFIG: ['.cfg', '.conf', '.ini', '.toml'],
            FileType.REQUIREMENTS: ['requirements.txt', 'requirements-dev.txt'],
            FileType.PACKAGE_JSON: ['package.json'],
            FileType.DOCKERFILE: ['Dockerfile', 'dockerfile', '.dockerignore']
        }
        
        # Common framework/library patterns
        self.framework_patterns = {
            'flask': ['from flask', 'import flask', 'Flask('],
            'django': ['from django', 'import django', 'DJANGO_SETTINGS'],
            'fastapi': ['from fastapi', 'import fastapi', 'FastAPI('],
            'react': ['import React', 'from "react"', 'React.'],
            'vue': ['import Vue', 'from "vue"', 'Vue.'],
            'angular': ['import { Component }', '@Component', 'angular'],
            'express': ['import express', 'require("express")', 'express()'],
            'nest': ['@nestjs', 'import { Module }', 'NestFactory']
        }
        
        # Architecture patterns
        self.architecture_patterns = {
            'mvc': ['models', 'views', 'controllers'],
            'mvp': ['models', 'views', 'presenters'],
            'mvvm': ['models', 'views', 'viewmodels'],
            'layered': ['presentation', 'business', 'data'],
            'clean': ['entities', 'use_cases', 'interfaces'],
            'microservices': ['services', 'api', 'gateway'],
            'monorepo': ['packages', 'apps', 'libs']
        }
    
    def determine_file_type(self, file_path: str) -> FileType:
        """Determine the type of a file based on its extension and name"""
        path = Path(file_path)
        name = path.name.lower()
        suffix = path.suffix.lower()
        
        for file_type, patterns in self.file_type_patterns.items():
            for pattern in patterns:
                if pattern.startswith('.') and suffix == pattern:
                    return file_type
                elif not pattern.startswith('.') and name == pattern.lower():
                    return file_type
        
        return FileType.UNKNOWN
    
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """Perform comprehensive analysis of a single file"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Basic file information
        stat = path.stat()
        file_type = self.determine_file_type(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                encoding = 'latin-1'
            except Exception:
                content = ""
                encoding = 'unknown'
        
        # Calculate hash
        hash_md5 = hashlib.md5(content.encode()).hexdigest()
        
        # Count lines of code (excluding empty lines and comments)
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Create basic analysis
        analysis = FileAnalysis(
            file_path=str(path),
            file_type=file_type,
            size=stat.st_size,
            lines_of_code=lines_of_code,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            encoding=encoding,
            hash_md5=hash_md5
        )
        
        # Perform language-specific analysis
        if file_type == FileType.PYTHON:
            self._analyze_python_file(content, analysis)
        elif file_type in [FileType.JAVASCRIPT, FileType.TYPESCRIPT]:
            self._analyze_js_ts_file(content, analysis)
        elif file_type == FileType.JSON:
            self._analyze_json_file(content, analysis)
        elif file_type == FileType.PACKAGE_JSON:
            self._analyze_package_json(content, analysis)
        elif file_type == FileType.REQUIREMENTS:
            self._analyze_requirements_file(content, analysis)
        
        # Calculate complexity and maintainability scores
        analysis.complexity_score = self._calculate_complexity(analysis)
        analysis.maintainability_score = self._calculate_maintainability(analysis)
        
        return analysis
    
    def _analyze_python_file(self, content: str, analysis: FileAnalysis):
        """Analyze Python file for classes, functions, imports, etc."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            analysis.issues.append(f"Syntax error: {e}")
            return
        
        # Extract docstring
        if (tree.body and isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            analysis.docstring = tree.body[0].value.value
        
        # Analyze AST nodes
        for node in ast.walk(tree):
            self._process_python_node(node, analysis, content.split('\n'))
    
    def _process_python_node(self, node: ast.AST, analysis: FileAnalysis, lines: List[str]):
        """Process a Python AST node"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                analysis.imports.append(alias.name)
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                import_str = f"{module}.{alias.name}" if module else alias.name
                analysis.imports.append(import_str)
        
        elif isinstance(node, ast.ClassDef):
            self._process_class_def(node, analysis, lines)
        
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            self._process_function_def(node, analysis, lines)
        
        elif isinstance(node, ast.Assign):
            self._process_assignment(node, analysis)
    
    def _process_class_def(self, node: ast.ClassDef, analysis: FileAnalysis, lines: List[str]):
        """Process a class definition"""
        analysis.classes.append(node.name)
        
        # Get docstring
        docstring = None
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant)):
            docstring = node.body[0].value.value
        
        # Get decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Get base classes
        bases = [self._get_name(base) for base in node.bases]
        
        element = CodeElement(
            name=node.name,
            type=CodeElementType.CLASS,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring,
            decorators=decorators,
            references=bases
        )
        
        analysis.elements.append(element)
    
    def _process_function_def(self, node, analysis: FileAnalysis, lines: List[str]):
        """Process a function definition"""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        analysis.functions.append(node.name)
        
        # Get docstring
        docstring = None
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant)):
            docstring = node.body[0].value.value
        
        # Get decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Get parameters
        parameters = [arg.arg for arg in node.args.args]
        
        # Get return type
        return_type = None
        if node.returns:
            return_type = self._get_name(node.returns)
        
        element = CodeElement(
            name=node.name,
            type=CodeElementType.ASYNC_FUNCTION if is_async else CodeElementType.FUNCTION,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring,
            decorators=decorators,
            parameters=parameters,
            return_type=return_type,
            is_async=is_async,
            is_private=node.name.startswith('_')
        )
        
        analysis.elements.append(element)
    
    def _process_assignment(self, node: ast.Assign, analysis: FileAnalysis):
        """Process variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                if name.isupper():
                    analysis.constants.append(name)
                else:
                    analysis.variables.append(name)
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_name(decorator.func)
        return str(decorator)
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return str(node)
    
    def _analyze_js_ts_file(self, content: str, analysis: FileAnalysis):
        """Analyze JavaScript/TypeScript file"""
        lines = content.split('\n')
        
        # Simple regex-based analysis for JS/TS
        import_pattern = r'^import\s+(?:(?:\{[^}]+\}|\w+|\*\s+as\s+\w+)\s+from\s+)?["\']([^"\']+)["\']'
        export_pattern = r'^export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)'
        function_pattern = r'(?:function\s+(\w+)|(\w+)\s*(?:\([^)]*\))?\s*=>|(\w+)\s*:\s*(?:\([^)]*\))?\s*=>'
        class_pattern = r'^class\s+(\w+)'
        
        for line in lines:
            line = line.strip()
            
            # Imports
            import_match = re.search(import_pattern, line)
            if import_match:
                analysis.imports.append(import_match.group(1))
            
            # Exports
            export_match = re.search(export_pattern, line)
            if export_match:
                analysis.exports.append(export_match.group(1))
            
            # Functions
            func_match = re.search(function_pattern, line)
            if func_match:
                func_name = func_match.group(1) or func_match.group(2) or func_match.group(3)
                if func_name:
                    analysis.functions.append(func_name)
            
            # Classes
            class_match = re.search(class_pattern, line)
            if class_match:
                analysis.classes.append(class_match.group(1))
    
    def _analyze_json_file(self, content: str, analysis: FileAnalysis):
        """Analyze JSON file"""
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                analysis.variables.extend(data.keys())
        except json.JSONDecodeError as e:
            analysis.issues.append(f"JSON parse error: {e}")
    
    def _analyze_package_json(self, content: str, analysis: FileAnalysis):
        """Analyze package.json file"""
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                # Extract dependencies
                deps = data.get('dependencies', {})
                dev_deps = data.get('devDependencies', {})
                analysis.dependencies.extend(list(deps.keys()) + list(dev_deps.keys()))
                
                # Extract scripts
                scripts = data.get('scripts', {})
                analysis.variables.extend(scripts.keys())
        except json.JSONDecodeError as e:
            analysis.issues.append(f"Package.json parse error: {e}")
    
    def _analyze_requirements_file(self, content: str, analysis: FileAnalysis):
        """Analyze requirements.txt file"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (remove version specifiers)
                package = re.split(r'[>=<!=]', line)[0].strip()
                if package:
                    analysis.dependencies.append(package)
    
    def _calculate_complexity(self, analysis: FileAnalysis) -> int:
        """Calculate code complexity score"""
        complexity = 0
        complexity += len(analysis.classes) * 3
        complexity += len(analysis.functions) * 2
        complexity += len(analysis.imports)
        complexity += analysis.lines_of_code // 10
        return complexity
    
    def _calculate_maintainability(self, analysis: FileAnalysis) -> float:
        """Calculate maintainability score (0-1)"""
        score = 1.0
        
        # Reduce score for high complexity
        if analysis.complexity_score > 100:
            score -= 0.3
        elif analysis.complexity_score > 50:
            score -= 0.1
        
        # Reduce score for large files
        if analysis.lines_of_code > 1000:
            score -= 0.2
        elif analysis.lines_of_code > 500:
            score -= 0.1
        
        # Increase score for documentation
        documented_elements = sum(1 for elem in analysis.elements if elem.docstring)
        if documented_elements > 0:
            doc_ratio = documented_elements / max(len(analysis.elements), 1)
            score += doc_ratio * 0.2
        
        return max(0.0, min(1.0, score))
    
    def analyze_directory_structure(self, root_path: str) -> DirectoryStructure:
        """Analyze directory structure"""
        path = Path(root_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {root_path}")
        
        return self._build_directory_tree(path)
    
    def _build_directory_tree(self, path: Path) -> DirectoryStructure:
        """Build directory tree recursively"""
        if path.is_file():
            file_type = self.determine_file_type(str(path))
            return DirectoryStructure(
                path=str(path),
                name=path.name,
                type='file',
                size=path.stat().st_size,
                file_count=1,
                file_types={file_type: 1}
            )
        
        # Directory
        children = []
        total_size = 0
        total_files = 0
        file_type_counts = {}
        
        try:
            for child_path in path.iterdir():
                if child_path.name.startswith('.') and child_path.name not in ['.gitignore', '.env']:
                    continue
                
                try:
                    child_structure = self._build_directory_tree(child_path)
                    children.append(child_structure)
                    total_size += child_structure.size
                    total_files += child_structure.file_count
                    
                    # Merge file type counts
                    for file_type, count in child_structure.file_types.items():
                        file_type_counts[file_type] = file_type_counts.get(file_type, 0) + count
                
                except (OSError, PermissionError):
                    continue
        
        except (OSError, PermissionError):
            pass
        
        return DirectoryStructure(
            path=str(path),
            name=path.name,
            type='directory',
            size=total_size,
            file_count=total_files,
            children=children,
            file_types=file_type_counts,
            description=self._infer_directory_purpose(path.name)
        )
    
    def _infer_directory_purpose(self, dir_name: str) -> Optional[str]:
        """Infer the purpose of a directory based on its name"""
        purposes = {
            'src': 'Source code',
            'lib': 'Libraries',
            'test': 'Test files',
            'tests': 'Test files',
            'docs': 'Documentation',
            'config': 'Configuration files',
            'utils': 'Utility functions',
            'components': 'Reusable components',
            'services': 'Service layer',
            'models': 'Data models',
            'views': 'View components',
            'controllers': 'Controllers',
            'api': 'API endpoints',
            'static': 'Static assets',
            'assets': 'Asset files',
            'public': 'Public files',
            'private': 'Private files',
            'build': 'Build output',
            'dist': 'Distribution files',
            'node_modules': 'Node.js dependencies',
            '__pycache__': 'Python cache files'
        }
        
        return purposes.get(dir_name.lower())
    
    def analyze_project_metadata(self, root_path: str) -> ProjectMetadata:
        """Analyze project metadata from configuration files"""
        path = Path(root_path)
        
        # Default metadata
        metadata = ProjectMetadata(
            name=path.name,
            root_path=str(path),
            project_type="unknown",
            language="unknown"
        )
        
        # Check for package.json (Node.js project)
        package_json = path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                
                metadata.name = data.get('name', metadata.name)
                metadata.description = data.get('description')
                metadata.version = data.get('version')
                metadata.project_type = "node"
                metadata.language = "javascript"
                metadata.dependencies = list(data.get('dependencies', {}).keys())
                metadata.dev_dependencies = list(data.get('devDependencies', {}).keys())
                metadata.scripts = data.get('scripts', {})
                
                if data.get('main'):
                    metadata.entry_points.append(data['main'])
                
            except (json.JSONDecodeError, IOError):
                pass
        
        # Check for requirements.txt (Python project)
        requirements_txt = path / "requirements.txt"
        if requirements_txt.exists():
            metadata.project_type = "python"
            metadata.language = "python"
            
            try:
                with open(requirements_txt, 'r') as f:
                    content = f.read()
                
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        package = re.split(r'[>=<!=]', line)[0].strip()
                        if package:
                            metadata.dependencies.append(package)
            except IOError:
                pass
        
        # Check for pyproject.toml (Modern Python project)
        pyproject_toml = path / "pyproject.toml"
        if pyproject_toml.exists():
            metadata.project_type = "python"
            metadata.language = "python"
        
        # Look for common files
        for file_path in path.iterdir():
            if file_path.is_file():
                name = file_path.name.lower()
                
                if name in ['readme.md', 'readme.txt', 'readme.rst']:
                    metadata.documentation_files.append(str(file_path))
                elif name in ['dockerfile', '.dockerignore']:
                    metadata.build_files.append(str(file_path))
                elif name.endswith('.json') and 'config' in name:
                    metadata.config_files.append(str(file_path))
        
        # Look for test directories
        for dir_path in path.iterdir():
            if dir_path.is_dir():
                name = dir_path.name.lower()
                if name in ['test', 'tests', '__tests__', 'spec']:
                    metadata.test_directories.append(str(dir_path))
        
        return metadata
    
    def detect_frameworks_and_patterns(self, files: Dict[str, FileAnalysis]) -> Tuple[List[str], List[str]]:
        """Detect frameworks and architecture patterns"""
        frameworks = set()
        patterns = set()
        
        # Analyze file contents for framework usage
        for file_analysis in files.values():
            if file_analysis.file_type == FileType.PYTHON:
                for import_name in file_analysis.imports:
                    for framework, indicators in self.framework_patterns.items():
                        if any(indicator in import_name for indicator in indicators):
                            frameworks.add(framework)
        
        # Analyze directory structure for architecture patterns
        all_paths = list(files.keys())
        directory_names = set()
        
        for file_path in all_paths:
            parts = Path(file_path).parts
            directory_names.update(part.lower() for part in parts[:-1])  # Exclude filename
        
        for pattern, indicators in self.architecture_patterns.items():
            if any(indicator in directory_names for indicator in indicators):
                patterns.add(pattern)
        
        return list(frameworks), list(patterns)

"""
R-Code Project Context Manager
=============================

Main orchestrator for comprehensive project context analysis and management.
Provides the AI with complete project understanding to prevent mistakes and conflicts.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import asdict

from .context_types import (
    ProjectContext, ProjectAnalysis, FileContext, RelationshipContext,
    ProjectMetadata, DirectoryStructure, FileAnalysis, FileType
)
from .code_analyzer import CodeAnalyzer
from .relationship_mapper import RelationshipMapper


class ProjectContextManager:
    """Comprehensive project context manager for AI operations"""
    
    def __init__(self, project_root: str, cache_dir: str = ".rcode/context"):
        """
        Initialize project context manager
        
        Args:
            project_root: Root directory of the project
            cache_dir: Directory to store context cache
        """
        self.project_root = Path(project_root)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize analyzers
        self.code_analyzer = CodeAnalyzer()
        self.relationship_mapper = RelationshipMapper()
        
        # Cache management
        self.context_cache: Optional[ProjectContext] = None
        self.last_analysis_time: Optional[datetime] = None
        self.file_modification_times: Dict[str, float] = {}
        
        # Threading for performance
        self._analysis_lock = threading.Lock()
        
        # Configuration
        self.max_file_size = 1024 * 1024  # 1MB max file size for analysis
        self.excluded_dirs = {
            '__pycache__', '.git', 'node_modules', '.vscode', '.idea',
            'dist', 'build', '.pytest_cache', '.mypy_cache', 
            'venv', 'env', '.venv', '.env',  # Virtual environments
            'site-packages', 'lib', 'lib64', 'Scripts', 'bin',  # More venv dirs
            '.tox', '.coverage', 'htmlcov', 'cover',  # Testing dirs
            '.sass-cache', '.cache', 'tmp', 'temp',  # Cache dirs
            'logs', 'log'  # Log dirs
        }
        self.excluded_files = {
            '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin',
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.tar',
            '.log', '.sqlite', '.db', '.lock', '.tmp'  # More excluded files
        }
        
        # Auto-refresh settings
        self.auto_refresh_interval = 300  # 5 minutes
        self.force_refresh_threshold = 0.1  # Refresh if 10% of files changed
    
    def get_project_context(self, force_refresh: bool = False) -> ProjectContext:
        """
        Get comprehensive project context with intelligent caching
        
        Args:
            force_refresh: Force full re-analysis even if cache is valid
            
        Returns:
            Complete project context
        """
        with self._analysis_lock:
            # Check if we need to refresh
            needs_refresh = self._needs_refresh(force_refresh)
            
            if needs_refresh or self.context_cache is None:
                print("🔍 Analyzing project structure...")
                self.context_cache = self._build_full_context()
                self.last_analysis_time = datetime.now()
                self._save_cache()
                print("✅ Project analysis complete")
            
            return self.context_cache
    
    def _needs_refresh(self, force_refresh: bool) -> bool:
        """Check if context needs to be refreshed"""
        if force_refresh:
            return True
        
        if self.context_cache is None:
            return True
        
        # Check age-based refresh
        if self.last_analysis_time:
            age = datetime.now() - self.last_analysis_time
            if age.total_seconds() > self.auto_refresh_interval:
                return True
        
        # Check file modification times
        changed_files = self._get_changed_files()
        if changed_files:
            total_files = len(self.context_cache.project_analysis.files)
            change_ratio = len(changed_files) / max(1, total_files)
            
            if change_ratio > self.force_refresh_threshold:
                return True
        
        return False
    
    def _get_changed_files(self) -> List[str]:
        """Get list of files that have been modified since last analysis"""
        changed_files = []
        
        for file_path in self._get_project_files():
            try:
                current_mtime = os.path.getmtime(file_path)
                cached_mtime = self.file_modification_times.get(str(file_path))
                
                if cached_mtime is None or current_mtime > cached_mtime:
                    changed_files.append(str(file_path))
            
            except (OSError, IOError):
                continue
        
        return changed_files
    
    def _build_full_context(self) -> ProjectContext:
        """Build complete project context"""
        start_time = time.time()
        
        # Get all project files
        project_files = self._get_project_files()
        print(f"📁 Found {len(project_files)} files to analyze")
        
        # Analyze project metadata
        metadata = self.code_analyzer.analyze_project_metadata(str(self.project_root))
        
        # Analyze directory structure
        directory_structure = self.code_analyzer.analyze_directory_structure(str(self.project_root))
        
        # Analyze files in parallel
        file_analyses = self._analyze_files_parallel(project_files)
        
        # Build relationships
        print("🔗 Analyzing file relationships...")
        relationships = self.relationship_mapper.analyze_file_relationships(file_analyses)
        
        # Build relationship context
        relationship_context = self.relationship_mapper.build_relationship_context(
            file_analyses, relationships
        )
        
        # Detect frameworks and patterns
        frameworks, patterns = self.code_analyzer.detect_frameworks_and_patterns(file_analyses)
        
        # Calculate quality metrics
        quality_scores = self._calculate_quality_scores(file_analyses, relationships)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            file_analyses, relationships, relationship_context
        )
        
        # Build project analysis
        project_analysis = ProjectAnalysis(
            metadata=metadata,
            directory_structure=directory_structure,
            files=file_analyses,
            relationships=relationships,
            dependency_graph=relationship_context.file_dependencies,
            architecture_patterns=patterns,
            code_metrics=self._calculate_code_metrics(file_analyses),
            quality_scores=quality_scores,
            recommendations=recommendations
        )
        
        # Build file contexts
        file_contexts = self._build_file_contexts(file_analyses, relationships)
        
        # Detect naming conventions and standards
        naming_conventions = self._detect_naming_conventions(file_analyses)
        coding_standards = self._detect_coding_standards(file_analyses)
        best_practices = self._identify_best_practices(file_analyses)
        anti_patterns = self._identify_anti_patterns(file_analyses, relationship_context)
        
        # Build complete context
        context = ProjectContext(
            project_analysis=project_analysis,
            file_contexts=file_contexts,
            relationship_context=relationship_context,
            current_state=self._get_current_state(),
            recent_changes=self._get_recent_changes(),
            active_patterns=patterns + frameworks,
            naming_conventions=naming_conventions,
            coding_standards=coding_standards,
            best_practices=best_practices,
            anti_patterns=anti_patterns
        )
        
        # Update file modification times
        self._update_file_modification_times(project_files)
        
        analysis_time = time.time() - start_time
        print(f"⏱️  Analysis completed in {analysis_time:.2f} seconds")
        
        return context
    
    def _get_project_files(self) -> List[str]:
        """Get all relevant project files"""
        files = []
        
        for root, dirs, filenames in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # Skip excluded file types
                if file_path.suffix.lower() in self.excluded_files:
                    continue
                
                # Skip hidden files (except specific ones)
                if filename.startswith('.') and filename not in ['.gitignore', '.env']:
                    continue
                
                # Skip large files
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        continue
                except (OSError, IOError):
                    continue
                
                files.append(str(file_path))
        
        return files
    
    def _analyze_files_parallel(self, file_paths: List[str]) -> Dict[str, FileAnalysis]:
        """Analyze files in parallel for better performance"""
        analyses = {}
        
        # Use ThreadPoolExecutor for I/O bound tasks
        max_workers = min(8, len(file_paths))  # Reasonable limit
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit analysis tasks
            future_to_file = {
                executor.submit(self._safe_analyze_file, file_path): file_path
                for file_path in file_paths
            }
            
            # Collect results
            completed = 0
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                completed += 1
                
                if completed % 10 == 0:
                    print(f"📊 Analyzed {completed}/{len(file_paths)} files...")
                
                try:
                    analysis = future.result()
                    if analysis:
                        analyses[file_path] = analysis
                except Exception as e:
                    print(f"⚠️  Failed to analyze {file_path}: {e}")
        
        return analyses
    
    def _safe_analyze_file(self, file_path: str) -> Optional[FileAnalysis]:
        """Safely analyze a file with error handling"""
        try:
            return self.code_analyzer.analyze_file(file_path)
        except Exception as e:
            # Log error but continue with other files
            return None
    
    def _calculate_quality_scores(self, files: Dict[str, FileAnalysis], 
                                 relationships: List) -> Dict[str, float]:
        """Calculate overall project quality scores"""
        if not files:
            return {"overall": 0.0}
        
        # Calculate individual metrics
        maintainability_scores = [f.maintainability_score for f in files.values()]
        avg_maintainability = sum(maintainability_scores) / len(maintainability_scores)
        
        # Documentation coverage
        total_elements = sum(len(f.elements) for f in files.values())
        documented_elements = sum(
            len([e for e in f.elements if e.docstring]) 
            for f in files.values()
        )
        doc_coverage = documented_elements / max(1, total_elements)
        
        # Test coverage (approximate based on test files)
        test_files = len([f for f in files.values() 
                         if 'test' in f.file_path.lower() or f.file_path.endswith('_test.py')])
        source_files = len([f for f in files.values() 
                           if f.file_type in [FileType.PYTHON, FileType.JAVASCRIPT, FileType.TYPESCRIPT]])
        test_coverage = min(1.0, test_files / max(1, source_files))
        
        # Complexity score (inverse - lower is better)
        avg_complexity = sum(f.complexity_score for f in files.values()) / len(files)
        complexity_score = max(0.0, 1.0 - (avg_complexity / 200))  # Normalize
        
        # Calculate overall score
        overall_score = (
            avg_maintainability * 0.3 +
            doc_coverage * 0.25 +
            test_coverage * 0.25 +
            complexity_score * 0.2
        )
        
        return {
            "overall": overall_score,
            "maintainability": avg_maintainability,
            "documentation": doc_coverage,
            "test_coverage": test_coverage,
            "complexity": complexity_score
        }
    
    def _calculate_code_metrics(self, files: Dict[str, FileAnalysis]) -> Dict[str, Any]:
        """Calculate comprehensive code metrics"""
        total_lines = sum(f.lines_of_code for f in files.values())
        total_files = len(files)
        total_classes = sum(len(f.classes) for f in files.values())
        total_functions = sum(len(f.functions) for f in files.values())
        
        # File type distribution
        file_types = {}
        for analysis in files.values():
            file_type = analysis.file_type.value
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            "total_lines_of_code": total_lines,
            "total_files": total_files,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "avg_lines_per_file": total_lines / max(1, total_files),
            "avg_functions_per_file": total_functions / max(1, total_files),
            "file_type_distribution": file_types
        }
    
    def _generate_recommendations(self, files: Dict[str, FileAnalysis], 
                                relationships: List, 
                                relationship_context: RelationshipContext) -> List[str]:
        """Generate project-level recommendations"""
        recommendations = []
        
        # Check for circular dependencies
        if relationship_context.circular_dependencies:
            recommendations.append(
                f"⚠️  Found {len(relationship_context.circular_dependencies)} circular dependencies - consider refactoring"
            )
        
        # Check for unused imports
        unused_count = sum(len(imports) for imports in relationship_context.unused_imports.values())
        if unused_count > 0:
            recommendations.append(f"🧹 Remove {unused_count} unused imports to clean up code")
        
        # Check for large files
        large_files = [f for f in files.values() if f.lines_of_code > 500]
        if large_files:
            recommendations.append(f"📦 Consider splitting {len(large_files)} large files into smaller modules")
        
        # Check for missing documentation
        total_elements = sum(len(f.elements) for f in files.values())
        documented = sum(len([e for e in f.elements if e.docstring]) for f in files.values())
        doc_ratio = documented / max(1, total_elements)
        
        if doc_ratio < 0.5:
            recommendations.append("📚 Improve documentation coverage - less than 50% of code is documented")
        
        # Check for high coupling
        high_coupling_files = [
            path for path, score in relationship_context.coupling_metrics.items()
            if score > 0.7
        ]
        if high_coupling_files:
            recommendations.append(f"🔗 Reduce coupling in {len(high_coupling_files)} highly coupled files")
        
        return recommendations
    
    def _build_file_contexts(self, files: Dict[str, FileAnalysis], 
                           relationships: List) -> Dict[str, FileContext]:
        """Build individual file contexts"""
        file_contexts = {}
        
        # Build dependency maps
        dependencies = {}
        dependents = {}
        
        for rel in relationships:
            # Dependencies (what this file depends on)
            if rel.source_file not in dependencies:
                dependencies[rel.source_file] = []
            dependencies[rel.source_file].append(rel.target_file)
            
            # Dependents (what depends on this file)
            if rel.target_file not in dependents:
                dependents[rel.target_file] = []
            dependents[rel.target_file].append(rel.source_file)
        
        # Build contexts
        for file_path, analysis in files.items():
            # Find similar files (same type, similar size)
            similar_files = self._find_similar_files(file_path, analysis, files)
            
            # Generate file-specific recommendations
            file_recommendations = self._generate_file_recommendations(analysis)
            
            context = FileContext(
                file_path=file_path,
                analysis=analysis,
                dependencies=dependencies.get(file_path, []),
                dependents=dependents.get(file_path, []),
                similar_files=similar_files,
                recommendations=file_recommendations
            )
            
            file_contexts[file_path] = context
        
        return file_contexts
    
    def _find_similar_files(self, target_path: str, target_analysis: FileAnalysis,
                           all_files: Dict[str, FileAnalysis]) -> List[str]:
        """Find files similar to the target file"""
        similar = []
        
        for file_path, analysis in all_files.items():
            if file_path == target_path:
                continue
            
            # Same file type
            if analysis.file_type != target_analysis.file_type:
                continue
            
            # Similar size (within 50%)
            size_ratio = min(analysis.lines_of_code, target_analysis.lines_of_code) / max(
                analysis.lines_of_code, target_analysis.lines_of_code, 1
            )
            
            if size_ratio < 0.5:
                continue
            
            # Similar structure (classes/functions)
            class_similarity = min(len(analysis.classes), len(target_analysis.classes)) / max(
                len(analysis.classes), len(target_analysis.classes), 1
            )
            
            func_similarity = min(len(analysis.functions), len(target_analysis.functions)) / max(
                len(analysis.functions), len(target_analysis.functions), 1
            )
            
            avg_similarity = (class_similarity + func_similarity) / 2
            
            if avg_similarity > 0.6:
                similar.append(file_path)
        
        return similar[:5]  # Limit to top 5 similar files
    
    def _generate_file_recommendations(self, analysis: FileAnalysis) -> List[str]:
        """Generate recommendations for a specific file"""
        recommendations = []
        
        # Large file
        if analysis.lines_of_code > 500:
            recommendations.append("Consider splitting this large file into smaller modules")
        
        # High complexity
        if analysis.complexity_score > 100:
            recommendations.append("Simplify complex code structure")
        
        # Missing documentation
        if analysis.elements:
            documented = sum(1 for elem in analysis.elements if elem.docstring)
            doc_ratio = documented / len(analysis.elements)
            
            if doc_ratio < 0.3:
                recommendations.append("Add documentation to functions and classes")
        
        # Too many classes
        if len(analysis.classes) > 5:
            recommendations.append("Consider moving some classes to separate files")
        
        # Syntax issues
        if analysis.issues:
            recommendations.extend([f"Fix: {issue}" for issue in analysis.issues])
        
        return recommendations
    
    def _detect_naming_conventions(self, files: Dict[str, FileAnalysis]) -> Dict[str, str]:
        """Detect project naming conventions"""
        conventions = {}
        
        # Analyze function naming
        function_names = []
        for analysis in files.values():
            function_names.extend(analysis.functions)
        
        if function_names:
            # Check for snake_case vs camelCase
            snake_case_count = sum(1 for name in function_names if '_' in name and name.islower())
            camel_case_count = sum(1 for name in function_names if name[0].islower() and any(c.isupper() for c in name))
            
            if snake_case_count > camel_case_count:
                conventions["functions"] = "snake_case"
            else:
                conventions["functions"] = "camelCase"
        
        # Analyze class naming
        class_names = []
        for analysis in files.values():
            class_names.extend(analysis.classes)
        
        if class_names:
            # Most classes should be PascalCase
            if all(name[0].isupper() for name in class_names if name):
                conventions["classes"] = "PascalCase"
        
        # Analyze file naming
        file_names = [Path(path).stem for path in files.keys()]
        snake_case_files = sum(1 for name in file_names if '_' in name and name.islower())
        kebab_case_files = sum(1 for name in file_names if '-' in name and name.islower())
        
        if snake_case_files > kebab_case_files:
            conventions["files"] = "snake_case"
        elif kebab_case_files > 0:
            conventions["files"] = "kebab-case"
        
        return conventions
    
    def _detect_coding_standards(self, files: Dict[str, FileAnalysis]) -> Dict[str, Any]:
        """Detect coding standards and patterns"""
        standards = {}
        
        # Docstring style
        docstring_styles = {"google": 0, "numpy": 0, "sphinx": 0}
        
        for analysis in files.values():
            for element in analysis.elements:
                if element.docstring:
                    doc = element.docstring.lower()
                    if "args:" in doc or "returns:" in doc:
                        docstring_styles["google"] += 1
                    elif "parameters" in doc or "returns" in doc:
                        docstring_styles["numpy"] += 1
                    elif ":param" in doc or ":return" in doc:
                        docstring_styles["sphinx"] += 1
        
        if docstring_styles:
            dominant_style = max(docstring_styles, key=docstring_styles.get)
            if docstring_styles[dominant_style] > 0:
                standards["docstring_style"] = dominant_style
        
        # Import organization
        import_styles = {"absolute": 0, "relative": 0}
        
        for analysis in files.values():
            for import_name in analysis.imports:
                if import_name.startswith('.'):
                    import_styles["relative"] += 1
                else:
                    import_styles["absolute"] += 1
        
        if import_styles["absolute"] > import_styles["relative"]:
            standards["import_style"] = "absolute_preferred"
        elif import_styles["relative"] > 0:
            standards["import_style"] = "mixed"
        
        return standards
    
    def _identify_best_practices(self, files: Dict[str, FileAnalysis]) -> List[str]:
        """Identify best practices being followed"""
        practices = []
        
        # Check for type hints (Python)
        python_files = [f for f in files.values() if f.file_type == FileType.PYTHON]
        if python_files:
            typed_functions = sum(
                1 for f in python_files 
                for elem in f.elements 
                if elem.return_type or elem.parameters
            )
            total_functions = sum(len(f.functions) for f in python_files)
            
            if typed_functions / max(1, total_functions) > 0.7:
                practices.append("Good type annotation coverage")
        
        # Check for error handling
        try_catch_files = sum(
            1 for f in files.values() 
            if any("try" in str(elem.name).lower() or "except" in str(elem.name).lower() 
                   for elem in f.elements)
        )
        
        if try_catch_files > len(files) * 0.3:
            practices.append("Good error handling practices")
        
        # Check for testing
        test_files = [f for f in files.values() if "test" in f.file_path.lower()]
        if len(test_files) > len(files) * 0.2:
            practices.append("Good test coverage")
        
        return practices
    
    def _identify_anti_patterns(self, files: Dict[str, FileAnalysis], 
                               relationship_context: RelationshipContext) -> List[str]:
        """Identify anti-patterns in the codebase"""
        anti_patterns = []
        
        # God objects (classes with too many methods)
        for analysis in files.values():
            for element in analysis.elements:
                if len(element.children) > 20:
                    anti_patterns.append(f"God object detected: {element.name} has {len(element.children)} methods")
        
        # Circular dependencies
        if relationship_context.circular_dependencies:
            anti_patterns.append(f"Circular dependencies found in {len(relationship_context.circular_dependencies)} locations")
        
        # High coupling
        high_coupling = [
            path for path, score in relationship_context.coupling_metrics.items()
            if score > 0.8
        ]
        if high_coupling:
            anti_patterns.append(f"High coupling detected in {len(high_coupling)} files")
        
        # Dead code (unused imports)
        if relationship_context.unused_imports:
            total_unused = sum(len(imports) for imports in relationship_context.unused_imports.values())
            anti_patterns.append(f"Potential dead code: {total_unused} unused imports")
        
        return anti_patterns
    
    def _get_current_state(self) -> Dict[str, Any]:
        """Get current project state snapshot"""
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "cache_location": str(self.cache_dir),
            "auto_refresh_enabled": True,
            "last_refresh": self.last_analysis_time.isoformat() if self.last_analysis_time else None
        }
    
    def _get_recent_changes(self) -> List[Dict[str, Any]]:
        """Get recent file changes (placeholder for future git integration)"""
        # TODO: Integrate with git to get actual change history
        return []
    
    def _update_file_modification_times(self, file_paths: List[str]):
        """Update cached file modification times"""
        for file_path in file_paths:
            try:
                mtime = os.path.getmtime(file_path)
                self.file_modification_times[file_path] = mtime
            except (OSError, IOError):
                continue
    
    def _save_cache(self):
        """Save context cache to disk"""
        if self.context_cache:
            cache_file = self.cache_dir / "project_context.json"
            
            try:
                # Convert to serializable format
                cache_data = {
                    "timestamp": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                    "file_modification_times": self.file_modification_times,
                    "context_summary": self.context_cache.get_summary()
                }
                
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                    
            except Exception as e:
                print(f"⚠️  Failed to save context cache: {e}")
    
    def _load_cache(self) -> bool:
        """Load context cache from disk"""
        cache_file = self.cache_dir / "project_context.json"
        
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Load basic cache info
            if cache_data.get("timestamp"):
                self.last_analysis_time = datetime.fromisoformat(cache_data["timestamp"])
            
            self.file_modification_times = cache_data.get("file_modification_times", {})
            
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to load context cache: {e}")
            return False
    
    def invalidate_cache(self):
        """Invalidate current cache"""
        self.context_cache = None
        self.last_analysis_time = None
        self.file_modification_times.clear()
    
    def get_file_context(self, file_path: str) -> Optional[FileContext]:
        """Get context for a specific file"""
        context = self.get_project_context()
        return context.file_contexts.get(file_path)
    
    def validate_operation(self, operation: str, target_path: str, 
                          content: str = None) -> Dict[str, Any]:
        """Validate an operation against project context"""
        context = self.get_project_context()
        return context.validate_operation(operation, target_path)
    
    def get_suggestions_for_file(self, file_path: str, 
                                operation: str = "create") -> List[str]:
        """Get suggestions for file operations"""
        context = self.get_project_context()
        return context.get_file_suggestions(operation, file_path)
    
    def get_project_summary(self) -> str:
        """Get a comprehensive project summary"""
        context = self.get_project_context()
        return context.get_summary()

"""
R-Code Relationship Mapper
=========================

Maps and analyzes relationships between files, classes, functions, and modules
to build a comprehensive dependency graph and prevent code conflicts.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict, deque

from .context_types import (
    FileAnalysis, FileRelationship, RelationshipType, 
    RelationshipContext, FileType
)


class RelationshipMapper:
    """Maps and analyzes code relationships and dependencies"""
    
    def __init__(self):
        """Initialize the relationship mapper"""
        self.import_patterns = {
            FileType.PYTHON: [
                r'^from\s+([^\s]+)\s+import',
                r'^import\s+([^\s,]+)',
            ],
            FileType.JAVASCRIPT: [
                r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
                r'require\(["\']([^"\']+)["\']\)',
            ],
            FileType.TYPESCRIPT: [
                r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
                r'import\s+["\']([^"\']+)["\']',
            ]
        }
        
        # Patterns for different relationship types
        self.relationship_patterns = {
            RelationshipType.INHERITS: [
                r'class\s+\w+\(([^)]+)\)',  # Python inheritance
                r'class\s+\w+\s+extends\s+(\w+)',  # JS/TS inheritance
            ],
            RelationshipType.IMPLEMENTS: [
                r'class\s+\w+.*implements\s+([^{]+)',  # TS implements
            ],
            RelationshipType.CALLS: [
                r'(\w+)\s*\(',  # Function calls
            ],
            RelationshipType.REFERENCES: [
                r'(\w+)\.',  # Attribute access
            ]
        }
    
    def analyze_file_relationships(self, files: Dict[str, FileAnalysis]) -> List[FileRelationship]:
        """Analyze relationships between all files"""
        relationships = []
        
        # Build import relationships
        import_relationships = self._build_import_relationships(files)
        relationships.extend(import_relationships)
        
        # Build inheritance relationships
        inheritance_relationships = self._build_inheritance_relationships(files)
        relationships.extend(inheritance_relationships)
        
        # Build call relationships
        call_relationships = self._build_call_relationships(files)
        relationships.extend(call_relationships)
        
        # Calculate relationship strengths
        self._calculate_relationship_strengths(relationships)
        
        return relationships
    
    def _build_import_relationships(self, files: Dict[str, FileAnalysis]) -> List[FileRelationship]:
        """Build import/dependency relationships"""
        relationships = []
        
        for file_path, analysis in files.items():
            for import_name in analysis.imports:
                target_file = self._resolve_import_to_file(import_name, file_path, files)
                
                if target_file and target_file in files:
                    relationship = FileRelationship(
                        source_file=file_path,
                        target_file=target_file,
                        relationship_type=RelationshipType.IMPORTS,
                        elements=[import_name],
                        strength=1.0
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _resolve_import_to_file(self, import_name: str, source_file: str, 
                               files: Dict[str, FileAnalysis]) -> Optional[str]:
        """Resolve an import name to an actual file path"""
        source_path = Path(source_file)
        
        # Handle relative imports
        if import_name.startswith('.'):
            # Relative import
            parts = import_name.split('.')
            current_dir = source_path.parent
            
            # Navigate up directories for each leading dot
            dots = 0
            for part in parts:
                if part == '':
                    dots += 1
                else:
                    break
            
            for _ in range(dots - 1):
                current_dir = current_dir.parent
            
            # Build target path
            if dots < len(parts):
                module_parts = parts[dots:]
                target_path = current_dir / '/'.join(module_parts)
            else:
                target_path = current_dir
        
        else:
            # Absolute import - try to find in project
            parts = import_name.split('.')
            
            # Look for matching files
            for file_path in files:
                file_parts = Path(file_path).with_suffix('').parts
                
                # Check if import matches file path
                if len(parts) <= len(file_parts):
                    if file_parts[-len(parts):] == tuple(parts):
                        return file_path
                
                # Check if file name matches import
                if file_parts[-1] == parts[-1]:
                    return file_path
            
            # For absolute imports, construct potential paths
            source_dir = Path(source_file).parent
            project_root = source_dir
            while project_root.parent != project_root:
                project_root = project_root.parent
                if (project_root / 'src').exists():
                    project_root = project_root / 'src'
                    break
            
            target_path = project_root / '/'.join(parts)
        
        # Try common extensions
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx']:
            candidate = str(target_path) + ext
            if candidate in files:
                return candidate
        
        # Try __init__.py for directories
        init_file = str(target_path / '__init__.py')
        if init_file in files:
            return init_file
        
        return None
    
    def _build_inheritance_relationships(self, files: Dict[str, FileAnalysis]) -> List[FileRelationship]:
        """Build inheritance relationships between classes"""
        relationships = []
        
        for file_path, analysis in files.items():
            for element in analysis.elements:
                if element.references:  # Base classes or interfaces
                    for reference in element.references:
                        # Find the file containing the referenced class
                        target_file = self._find_class_definition(reference, files)
                        
                        if target_file and target_file != file_path:
                            relationship = FileRelationship(
                                source_file=file_path,
                                target_file=target_file,
                                relationship_type=RelationshipType.INHERITS,
                                elements=[element.name, reference],
                                strength=0.8
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _find_class_definition(self, class_name: str, files: Dict[str, FileAnalysis]) -> Optional[str]:
        """Find the file where a class is defined"""
        for file_path, analysis in files.items():
            if class_name in analysis.classes:
                return file_path
        return None
    
    def _build_call_relationships(self, files: Dict[str, FileAnalysis]) -> List[FileRelationship]:
        """Build function call relationships"""
        relationships = []
        
        for file_path, analysis in files.items():
            for element in analysis.elements:
                if element.calls:  # Functions called by this element
                    for call in element.calls:
                        # Find the file containing the called function
                        target_file = self._find_function_definition(call, files)
                        
                        if target_file and target_file != file_path:
                            relationship = FileRelationship(
                                source_file=file_path,
                                target_file=target_file,
                                relationship_type=RelationshipType.CALLS,
                                elements=[element.name, call],
                                strength=0.6
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _find_function_definition(self, function_name: str, files: Dict[str, FileAnalysis]) -> Optional[str]:
        """Find the file where a function is defined"""
        for file_path, analysis in files.items():
            if function_name in analysis.functions:
                return file_path
        return None
    
    def _calculate_relationship_strengths(self, relationships: List[FileRelationship]):
        """Calculate the strength of relationships based on usage patterns"""
        relationship_counts = defaultdict(int)
        
        # Count relationships between file pairs
        for rel in relationships:
            key = (rel.source_file, rel.target_file)
            relationship_counts[key] += 1
        
        # Update strengths based on frequency
        for rel in relationships:
            key = (rel.source_file, rel.target_file)
            count = relationship_counts[key]
            
            # Increase strength for multiple relationships
            if count > 1:
                rel.strength = min(1.0, rel.strength + (count - 1) * 0.1)
    
    def build_dependency_graph(self, relationships: List[FileRelationship]) -> Dict[str, List[str]]:
        """Build a dependency graph from relationships"""
        graph = defaultdict(list)
        
        for rel in relationships:
            if rel.relationship_type in [RelationshipType.IMPORTS, RelationshipType.DEPENDS_ON]:
                graph[rel.source_file].append(rel.target_file)
        
        return dict(graph)
    
    def find_circular_dependencies(self, dependency_graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find circular dependencies in the dependency graph"""
        def dfs(node: str, path: List[str], visited: Set[str], rec_stack: Set[str]) -> List[List[str]]:
            cycles = []
            
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return cycles
            
            if node in visited:
                return cycles
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependency_graph.get(node, []):
                cycles.extend(dfs(neighbor, path.copy(), visited, rec_stack.copy()))
            
            rec_stack.remove(node)
            return cycles
        
        all_cycles = []
        visited = set()
        
        for node in dependency_graph:
            if node not in visited:
                cycles = dfs(node, [], set(), set())
                all_cycles.extend(cycles)
        
        # Remove duplicate cycles
        unique_cycles = []
        for cycle in all_cycles:
            # Normalize cycle (start with smallest element)
            if cycle:
                min_idx = cycle.index(min(cycle[:-1]))  # Exclude last element (duplicate of first)
                normalized = cycle[min_idx:-1] + cycle[:min_idx]
                if normalized not in unique_cycles:
                    unique_cycles.append(normalized)
        
        return unique_cycles
    
    def analyze_coupling(self, files: Dict[str, FileAnalysis], 
                        relationships: List[FileRelationship]) -> Dict[str, float]:
        """Analyze coupling between files"""
        coupling_scores = {}
        
        for file_path in files:
            # Count outgoing dependencies
            outgoing = len([r for r in relationships if r.source_file == file_path])
            
            # Count incoming dependencies
            incoming = len([r for r in relationships if r.target_file == file_path])
            
            # Calculate coupling score (normalized)
            total_files = len(files)
            coupling_score = (outgoing + incoming) / max(1, total_files - 1)
            coupling_scores[file_path] = coupling_score
        
        return coupling_scores
    
    def analyze_cohesion(self, files: Dict[str, FileAnalysis]) -> Dict[str, float]:
        """Analyze cohesion within files"""
        cohesion_scores = {}
        
        for file_path, analysis in files.items():
            # Simple cohesion metric based on:
            # - Ratio of public to private elements
            # - Presence of docstrings
            # - Logical organization
            
            total_elements = len(analysis.elements)
            if total_elements == 0:
                cohesion_scores[file_path] = 1.0
                continue
            
            # Count documented elements
            documented = sum(1 for elem in analysis.elements if elem.docstring)
            doc_ratio = documented / total_elements
            
            # Count private elements (good for encapsulation)
            private = sum(1 for elem in analysis.elements if elem.is_private)
            private_ratio = private / total_elements
            
            # Calculate cohesion score
            cohesion = (doc_ratio * 0.6) + (private_ratio * 0.4)
            cohesion_scores[file_path] = cohesion
        
        return cohesion_scores
    
    def find_unused_imports(self, files: Dict[str, FileAnalysis]) -> Dict[str, List[str]]:
        """Find unused imports in files"""
        unused_imports = {}
        
        for file_path, analysis in files.items():
            unused = []
            
            # For each import, check if it's used in the code
            for import_name in analysis.imports:
                # Simple check - look for the imported name in elements
                import_parts = import_name.split('.')
                base_name = import_parts[-1]
                
                used = False
                
                # Check if imported name is used in any element
                for element in analysis.elements:
                    if (base_name in element.calls or 
                        base_name in element.references or
                        base_name in element.name):
                        used = True
                        break
                
                if not used:
                    unused.append(import_name)
            
            if unused:
                unused_imports[file_path] = unused
        
        return unused_imports
    
    def suggest_refactoring_opportunities(self, files: Dict[str, FileAnalysis],
                                        relationships: List[FileRelationship]) -> Dict[str, List[str]]:
        """Suggest refactoring opportunities"""
        suggestions = defaultdict(list)
        
        # Analyze coupling
        coupling_scores = self.analyze_coupling(files, relationships)
        cohesion_scores = self.analyze_cohesion(files)
        
        for file_path, analysis in files.items():
            file_suggestions = []
            
            # High coupling
            if coupling_scores.get(file_path, 0) > 0.7:
                file_suggestions.append("Consider reducing dependencies - file has high coupling")
            
            # Low cohesion
            if cohesion_scores.get(file_path, 1.0) < 0.3:
                file_suggestions.append("Consider improving documentation and organization - file has low cohesion")
            
            # Large files
            if analysis.lines_of_code > 500:
                file_suggestions.append("Consider splitting large file into smaller modules")
            
            # Complex files
            if analysis.complexity_score > 100:
                file_suggestions.append("Consider simplifying complex code structure")
            
            # Too many classes in one file
            if len(analysis.classes) > 5:
                file_suggestions.append("Consider moving some classes to separate files")
            
            # Missing documentation
            undocumented = sum(1 for elem in analysis.elements if not elem.docstring)
            if undocumented > len(analysis.elements) * 0.5:
                file_suggestions.append("Consider adding documentation to functions and classes")
            
            if file_suggestions:
                suggestions[file_path] = file_suggestions
        
        return dict(suggestions)
    
    def build_relationship_context(self, files: Dict[str, FileAnalysis],
                                 relationships: List[FileRelationship]) -> RelationshipContext:
        """Build comprehensive relationship context"""
        # Build dependency graph
        dependency_graph = self.build_dependency_graph(relationships)
        
        # Build reverse dependencies
        reverse_deps = defaultdict(list)
        for source, targets in dependency_graph.items():
            for target in targets:
                reverse_deps[target].append(source)
        
        # Find circular dependencies
        circular_deps = self.find_circular_dependencies(dependency_graph)
        
        # Find unused imports
        unused_imports = self.find_unused_imports(files)
        
        # Analyze coupling and cohesion
        coupling_metrics = self.analyze_coupling(files, relationships)
        cohesion_metrics = self.analyze_cohesion(files)
        
        return RelationshipContext(
            file_dependencies=dependency_graph,
            reverse_dependencies=dict(reverse_deps),
            circular_dependencies=circular_deps,
            unused_imports=unused_imports,
            coupling_metrics=coupling_metrics,
            cohesion_metrics=cohesion_metrics
        )

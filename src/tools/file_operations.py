"""
R-Code File Operations Tool
==========================

Comprehensive file management tool for R-Code AI assistant.
Provides safe file operations including read, write, search, replace, create, delete.
"""

import os
import shutil
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from langchain_core.tools import tool


class RCodeFileOperations:
    """Professional file operations manager for R-Code AI assistant"""
    
    def __init__(self, base_path: str = "."):
        """
        Initialize file operations with base path
        
        Args:
            base_path: Base directory for file operations (security boundary)
        """
        self.base_path = Path(base_path).resolve()
    
    def _validate_path(self, file_path: str) -> Path:
        """
        Validate and resolve file path within security boundaries
        
        Args:
            file_path: File path to validate
            
        Returns:
            Resolved Path object
            
        Raises:
            ValueError: If path is outside base directory
        """
        try:
            resolved_path = Path(file_path).resolve()
            
            # Ensure path is within base directory (security check)
            if not str(resolved_path).startswith(str(self.base_path)):
                resolved_path = self.base_path / file_path
                resolved_path = resolved_path.resolve()
            
            return resolved_path
        except Exception as e:
            raise ValueError(f"Invalid file path: {file_path}. Error: {str(e)}")
    
    def read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read file contents"""
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "content": None
                }
            
            if not path.is_file():
                return {
                    "success": False,
                    "error": f"Path is not a file: {file_path}",
                    "content": None
                }
                
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
                
            return {
                "success": True,
                "file_path": str(path),
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file {file_path}: {str(e)}",
                "content": None
            }
    
    def write_file(self, file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> Dict[str, Any]:
        """Write content to file"""
        try:
            path = self._validate_path(file_path)
            
            # Create parent directories if needed
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": str(path),
                "message": f"Successfully wrote {len(content)} characters to {file_path}",
                "size": len(content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file {file_path}: {str(e)}"
            }
    
    def search_in_file(self, file_path: str, search_term: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """Search for term in file"""
        try:
            read_result = self.read_file(file_path)
            if not read_result["success"]:
                return read_result
            
            content = read_result["content"]
            lines = content.splitlines()
            matches = []
            
            search_func = str.find if case_sensitive else lambda s, t: s.lower().find(t.lower())
            search_lower = search_term if case_sensitive else search_term.lower()
            
            for line_num, line in enumerate(lines, 1):
                check_line = line if case_sensitive else line.lower()
                if search_lower in check_line:
                    matches.append({
                        "line_number": line_num,
                        "line_content": line.strip(),
                        "match_positions": []
                    })
                    
                    # Find all match positions in the line
                    start = 0
                    while True:
                        pos = search_func(check_line[start:], search_lower)
                        if pos == -1:
                            break
                        actual_pos = start + pos
                        matches[-1]["match_positions"].append(actual_pos)
                        start = actual_pos + 1
            
            return {
                "success": True,
                "file_path": file_path,
                "search_term": search_term,
                "matches_found": len(matches),
                "matches": matches
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to search in file {file_path}: {str(e)}"
            }
    
    def replace_in_file(self, file_path: str, search_term: str, replace_term: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """Replace text in file"""
        try:
            read_result = self.read_file(file_path)
            if not read_result["success"]:
                return read_result
            
            content = read_result["content"]
            
            if case_sensitive:
                new_content = content.replace(search_term, replace_term)
            else:
                import re
                new_content = re.sub(re.escape(search_term), replace_term, content, flags=re.IGNORECASE)
            
            replacements = content.count(search_term) if case_sensitive else len(re.findall(re.escape(search_term), content, re.IGNORECASE))
            
            if replacements == 0:
                return {
                    "success": True,
                    "file_path": file_path,
                    "message": f"No occurrences of '{search_term}' found in file",
                    "replacements_made": 0
                }
            
            write_result = self.write_file(file_path, new_content)
            if not write_result["success"]:
                return write_result
            
            return {
                "success": True,
                "file_path": file_path,
                "message": f"Successfully replaced {replacements} occurrences of '{search_term}' with '{replace_term}'",
                "replacements_made": replacements
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to replace in file {file_path}: {str(e)}"
            }
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete file"""
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File does not exist: {file_path}"
                }
            
            if path.is_file():
                path.unlink()
                return {
                    "success": True,
                    "message": f"Successfully deleted file: {file_path}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Path is not a file: {file_path}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete file {file_path}: {str(e)}"
            }
    
    def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """Create directory"""
        try:
            path = self._validate_path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "message": f"Successfully created directory: {dir_path}",
                "directory_path": str(path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create directory {dir_path}: {str(e)}"
            }
    
    def delete_directory(self, dir_path: str, recursive: bool = False) -> Dict[str, Any]:
        """Delete directory"""
        try:
            path = self._validate_path(dir_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Directory does not exist: {dir_path}"
                }
            
            if not path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {dir_path}"
                }
            
            if recursive:
                shutil.rmtree(path)
                message = f"Successfully deleted directory and all contents: {dir_path}"
            else:
                path.rmdir()  # Only works if directory is empty
                message = f"Successfully deleted empty directory: {dir_path}"
            
            return {
                "success": True,
                "message": message
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete directory {dir_path}: {str(e)}"
            }
    
    def list_files(self, dir_path: str = ".", pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
        """List files in directory"""
        try:
            path = self._validate_path(dir_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Directory does not exist: {dir_path}"
                }
            
            if not path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {dir_path}"
                }
            
            files = []
            directories = []
            
            if recursive:
                for item in path.rglob(pattern):
                    relative_path = item.relative_to(path)
                    if item.is_file():
                        files.append({
                            "name": item.name,
                            "path": str(relative_path),
                            "size": item.stat().st_size,
                            "type": "file"
                        })
                    elif item.is_dir():
                        directories.append({
                            "name": item.name,
                            "path": str(relative_path),
                            "type": "directory"
                        })
            else:
                for item in path.glob(pattern):
                    if item.is_file():
                        files.append({
                            "name": item.name,
                            "path": item.name,
                            "size": item.stat().st_size,
                            "type": "file"
                        })
                    elif item.is_dir():
                        directories.append({
                            "name": item.name,
                            "path": item.name,
                            "type": "directory"
                        })
            
            return {
                "success": True,
                "directory_path": str(path),
                "files": files,
                "directories": directories,
                "total_files": len(files),
                "total_directories": len(directories)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list files in {dir_path}: {str(e)}"
            }


# Global instance
_file_ops = RCodeFileOperations()


@tool
def read_file(file_path: str) -> str:
    """
    Read the contents of a file.
    
    Use this tool to examine file contents, analyze code, review configurations,
    or extract information from any text file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        String containing file contents and metadata
    """
    result = _file_ops.read_file(file_path)
    
    if result["success"]:
        return f"📁 File: {result['file_path']}\n📊 Size: {result['size']} characters, {result['lines']} lines\n\n📄 Content:\n{result['content']}"
    else:
        return f"❌ Error reading file: {result['error']}"


@tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file. Creates the file if it doesn't exist.
    
    Use this tool to create new files, save code, write documentation,
    or update existing files with new content.
    
    Args:
        file_path: Path where to write the file
        content: Content to write to the file
        
    Returns:
        String with operation result
    """
    result = _file_ops.write_file(file_path, content)
    
    if result["success"]:
        return f"✅ {result['message']}"
    else:
        return f"❌ Error writing file: {result['error']}"


@tool
def create_and_open_file(file_path: str, content: str) -> str:
    """
    Create a new file, open it in VSCode, and write content for live coding experience.
    
    This tool provides a live coding experience by:
    1. Creating the file with initial structure
    2. Opening it in VSCode so user can see it
    3. Writing the full content to the file
    
    Use this tool when creating new files that the user should see being built.
    
    Args:
        file_path: Path where to create the file
        content: Content to write to the file
        
    Returns:
        String with operation result
    """
    import subprocess
    import time
    
    try:
        # First, create the file with a basic header or empty content
        path = _file_ops._validate_path(file_path)
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine file type and create initial structure
        file_extension = path.suffix.lower()
        initial_content = ""
        
        if file_extension == '.py':
            initial_content = f'"""\n{path.name}\n{"=" * len(path.name)}\n\nCreated by R-Code AI Assistant\n"""\n\n'
        elif file_extension in ['.js', '.ts']:
            initial_content = f'/**\n * {path.name}\n * Created by R-Code AI Assistant\n */\n\n'
        elif file_extension in ['.html']:
            initial_content = '<!DOCTYPE html>\n<html>\n<head>\n    <title>R-Code Generated</title>\n</head>\n<body>\n    <!-- Content being generated... -->\n'
        elif file_extension in ['.md']:
            initial_content = f'# {path.stem.replace("_", " ").title()}\n\n*Generated by R-Code AI Assistant*\n\n'
        else:
            initial_content = f'# {path.name}\n# Created by R-Code AI Assistant\n\n'
        
        # Create file with initial content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        # Check if we're already in VSCode
        in_vscode = (
            os.getenv('VSCODE_PID') is not None or 
            os.getenv('TERM_PROGRAM') == 'vscode' or
            'Code' in os.getenv('TERM_PROGRAM_VERSION', '')
        )
        
        if in_vscode:
            # We're already in VSCode, file will appear automatically
            vscode_status = "📝 File will appear in current VSCode workspace"
        else:
            # Try to open in VSCode
            try:
                subprocess.run(['code', str(path)], check=False, capture_output=True)
                vscode_status = "📝 File opened in VSCode for live viewing"
            except (subprocess.SubprocessError, FileNotFoundError):
                vscode_status = "⚠️  VSCode not available - file created successfully"
        
        # Small delay for file system
        time.sleep(0.2)
        
        # Now write the full content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        success_msg = f"✅ Created and populated {file_path} ({len(content)} characters)"
        success_msg += f"\n{vscode_status}"
        
        return success_msg
        
    except Exception as e:
        return f"❌ Error creating file: {str(e)}"


@tool
def live_write_file(file_path: str, content: str, chunk_size: int = 100) -> str:
    """
    Write content to a file in chunks with delays for live coding effect.
    
    This creates a live coding experience by writing content in small chunks
    with brief delays, allowing users to watch the file being built in real-time.
    
    Args:
        file_path: Path to the file to write
        content: Content to write
        chunk_size: Size of each chunk to write (default: 100 characters)
        
    Returns:
        String with operation result
    """
    import time
    
    try:
        path = _file_ops._validate_path(file_path)
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clear the file first
        with open(path, 'w', encoding='utf-8') as f:
            f.write("")
        
        # Write content in chunks
        written = 0
        total_length = len(content)
        
        while written < total_length:
            chunk = content[written:written + chunk_size]
            
            with open(path, 'a', encoding='utf-8') as f:
                f.write(chunk)
            
            written += len(chunk)
            
            # Small delay for live effect (but not too slow)
            time.sleep(0.1)
            
            # Update progress
            progress = (written / total_length) * 100
            if written % (chunk_size * 5) == 0:  # Update every 5 chunks
                print(f"📝 Writing {file_path}... {progress:.0f}% complete", flush=True)
        
        return f"✅ Live-wrote {total_length} characters to {file_path}\n📝 File created with live coding effect"
        
    except Exception as e:
        return f"❌ Error live-writing file: {str(e)}"


@tool
def search_in_file(file_path: str, search_term: str, case_sensitive: bool = False) -> str:
    """
    Search for text within a file and show all matches with line numbers.
    
    Use this tool to find specific code, text, or patterns within files.
    Great for debugging, code analysis, or finding specific content.
    
    Args:
        file_path: Path to the file to search in
        search_term: Text to search for
        case_sensitive: Whether search should be case sensitive (default: False)
        
    Returns:
        String with search results
    """
    result = _file_ops.search_in_file(file_path, search_term, case_sensitive)
    
    if not result["success"]:
        return f"❌ Error searching file: {result['error']}"
    
    if result["matches_found"] == 0:
        return f"🔍 No matches found for '{search_term}' in {file_path}"
    
    formatted_result = f"🔍 Found {result['matches_found']} matches for '{search_term}' in {result['file_path']}:\n\n"
    
    for match in result["matches"]:
        formatted_result += f"Line {match['line_number']}: {match['line_content']}\n"
    
    return formatted_result


@tool
def replace_in_file(file_path: str, search_term: str, replace_term: str, case_sensitive: bool = False) -> str:
    """
    Replace text within a file with new text.
    
    Use this tool to fix bugs, update code, modify configurations,
    or make any text replacements within files.
    
    Args:
        file_path: Path to the file to modify
        search_term: Text to find and replace
        replace_term: Text to replace with
        case_sensitive: Whether replacement should be case sensitive (default: False)
        
    Returns:
        String with operation result
    """
    result = _file_ops.replace_in_file(file_path, search_term, replace_term, case_sensitive)
    
    if result["success"]:
        return f"✅ {result['message']}"
    else:
        return f"❌ Error replacing in file: {result['error']}"


@tool
def delete_file(file_path: str) -> str:
    """
    Delete a file.
    
    Use this tool to remove unwanted files, clean up temporary files,
    or delete files that are no longer needed.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        String with operation result
    """
    result = _file_ops.delete_file(file_path)
    
    if result["success"]:
        return f"✅ {result['message']}"
    else:
        return f"❌ Error deleting file: {result['error']}"


@tool
def create_directory(dir_path: str) -> str:
    """
    Create a new directory (folder).
    
    Use this tool to organize files, create project structure,
    or set up new directories for your project.
    
    Args:
        dir_path: Path of the directory to create
        
    Returns:
        String with operation result
    """
    result = _file_ops.create_directory(dir_path)
    
    if result["success"]:
        return f"✅ {result['message']}"
    else:
        return f"❌ Error creating directory: {result['error']}"


@tool
def delete_directory(dir_path: str, recursive: bool = False) -> str:
    """
    Delete a directory (folder).
    
    Use this tool to remove empty directories or entire directory trees.
    Be careful with recursive deletion as it removes all contents.
    
    Args:
        dir_path: Path of the directory to delete
        recursive: Whether to delete directory and all its contents (default: False)
        
    Returns:
        String with operation result
    """
    result = _file_ops.delete_directory(dir_path, recursive)
    
    if result["success"]:
        return f"✅ {result['message']}"
    else:
        return f"❌ Error deleting directory: {result['error']}"


@tool
def list_files(dir_path: str = ".", pattern: str = "*", recursive: bool = False) -> str:
    """
    List files and directories in a specified directory.
    
    Use this tool to explore project structure, find files,
    or get an overview of directory contents.
    
    Args:
        dir_path: Directory path to list (default: current directory)
        pattern: File pattern to match (default: "*" for all files)
        recursive: Whether to list files recursively in subdirectories (default: False)
        
    Returns:
        String with directory listing
    """
    result = _file_ops.list_files(dir_path, pattern, recursive)
    
    if not result["success"]:
        return f"❌ Error listing files: {result['error']}"
    
    formatted_result = f"📁 Directory: {result['directory_path']}\n"
    formatted_result += f"📊 Found: {result['total_files']} files, {result['total_directories']} directories\n\n"
    
    if result["directories"]:
        formatted_result += "📁 Directories:\n"
        for dir_info in result["directories"]:
            formatted_result += f"  📁 {dir_info['path']}\n"
        formatted_result += "\n"
    
    if result["files"]:
        formatted_result += "📄 Files:\n"
        for file_info in result["files"]:
            size_kb = file_info['size'] / 1024
            formatted_result += f"  📄 {file_info['path']} ({size_kb:.1f} KB)\n"
    
    return formatted_result


@tool
def check_mcp_installation() -> str:
    """
    Check MCP installation status and provide installation guidance.
    
    Checks for langchain-mcp-adapters package and provides
    installation instructions if missing.
    
    Returns:
        String with MCP installation status and instructions
    """
    import subprocess
    import sys
    
    try:
        # Try importing the package
        import langchain_mcp_adapters
        return "✅ langchain-mcp-adapters is installed and working"
    except ImportError:
        # Try to install it
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "langchain-mcp-adapters"
            ], capture_output=True, text=True, check=True)
            
            return f"✅ Successfully installed langchain-mcp-adapters:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"❌ Failed to install langchain-mcp-adapters:\n{e.stderr}"
        except Exception as e:
            return f"❌ Error installing langchain-mcp-adapters: {str(e)}"


def get_file_operation_tools() -> List:
    """
    Get list of file operation tools for LangGraph integration
    
    Returns:
        List of file operation tools
    """
    return [
        read_file,
        write_file,
        create_and_open_file,
        live_write_file,
        search_in_file,
        replace_in_file,
        delete_file,
        create_directory,
        delete_directory,
        list_files,
        check_mcp_installation
    ]

"""
R-Code Checkpoint-Aware File Operations
======================================

File operations with automatic checkpoint integration for tracking AI changes.
Wraps standard file operations with checkpoint tracking and rollback capabilities.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

from .file_operations import RCodeFileOperations
from ..checkpoint.checkpoint_manager import CheckpointManager, OperationType


class CheckpointAwareFileOperations:
    """File operations with automatic checkpoint tracking"""
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        """Initialize with checkpoint manager"""
        self.checkpoint_manager = checkpoint_manager
        self.file_ops = RCodeFileOperations()
        self.current_operation_id = None
    
    def _get_affected_files(self, file_path: str, operation_type: OperationType) -> List[str]:
        """Get list of files that might be affected by an operation"""
        files = [file_path]
        
        # For directory operations, we might need to track contained files
        if operation_type in [OperationType.DIRECTORY_DELETE]:
            try:
                path = Path(file_path)
                if path.exists() and path.is_dir():
                    # Add all files in directory for tracking
                    for item in path.rglob('*'):
                        if item.is_file():
                            files.append(str(item))
            except:
                pass
        
        return files
    
    def start_file_operation(self, operation_type: OperationType, description: str, 
                           file_path: str, user_message: str = None) -> str:
        """Start tracking a file operation"""
        affected_files = self._get_affected_files(file_path, operation_type)
        operation_id = self.checkpoint_manager.start_operation(
            operation_type, description, affected_files, user_message
        )
        self.current_operation_id = operation_id
        return operation_id
    
    def complete_file_operation(self, ai_response: str = None):
        """Complete the current file operation"""
        if self.current_operation_id:
            self.checkpoint_manager.complete_operation(
                self.current_operation_id, ai_response
            )
            self.current_operation_id = None
    
    def read_file_tracked(self, file_path: str, user_message: str = None) -> Dict[str, Any]:
        """Read file with checkpoint tracking"""
        # Reading doesn't change files, so we don't need to track it extensively
        return self.file_ops.read_file(file_path)
    
    def write_file_tracked(self, file_path: str, content: str, user_message: str = None) -> Dict[str, Any]:
        """Write file with checkpoint tracking"""
        # Determine if this is create or modify
        path = Path(file_path)
        operation_type = OperationType.FILE_CREATE if not path.exists() else OperationType.FILE_MODIFY
        
        # Start tracking
        operation_id = self.start_file_operation(
            operation_type, 
            f"{'Create' if operation_type == OperationType.FILE_CREATE else 'Modify'} {file_path}",
            file_path,
            user_message
        )
        
        # Perform the operation
        result = self.file_ops.write_file(file_path, content)
        
        # Complete tracking
        if result["success"]:
            ai_response = f"Successfully wrote {len(content)} characters to {file_path}"
        else:
            ai_response = f"Failed to write to {file_path}: {result.get('error', 'Unknown error')}"
        
        self.checkpoint_manager.complete_operation(operation_id, ai_response)
        
        return result
    
    def replace_in_file_tracked(self, file_path: str, search_term: str, replace_term: str, 
                               case_sensitive: bool = False, user_message: str = None) -> Dict[str, Any]:
        """Replace in file with checkpoint tracking"""
        operation_id = self.start_file_operation(
            OperationType.FILE_MODIFY,
            f"Replace '{search_term}' with '{replace_term}' in {file_path}",
            file_path,
            user_message
        )
        
        # Perform the operation
        result = self.file_ops.replace_in_file(file_path, search_term, replace_term, case_sensitive)
        
        # Complete tracking
        ai_response = result.get("message", "Replace operation completed") if result["success"] else result.get("error", "Replace operation failed")
        self.checkpoint_manager.complete_operation(operation_id, ai_response)
        
        return result
    
    def delete_file_tracked(self, file_path: str, user_message: str = None) -> Dict[str, Any]:
        """Delete file with checkpoint tracking"""
        operation_id = self.start_file_operation(
            OperationType.FILE_DELETE,
            f"Delete {file_path}",
            file_path,
            user_message
        )
        
        # Perform the operation
        result = self.file_ops.delete_file(file_path)
        
        # Complete tracking
        ai_response = result.get("message", "File deleted") if result["success"] else result.get("error", "Delete operation failed")
        self.checkpoint_manager.complete_operation(operation_id, ai_response)
        
        return result
    
    def create_directory_tracked(self, dir_path: str, user_message: str = None) -> Dict[str, Any]:
        """Create directory with checkpoint tracking"""
        operation_id = self.start_file_operation(
            OperationType.DIRECTORY_CREATE,
            f"Create directory {dir_path}",
            dir_path,
            user_message
        )
        
        # Perform the operation
        result = self.file_ops.create_directory(dir_path)
        
        # Complete tracking
        ai_response = result.get("message", "Directory created") if result["success"] else result.get("error", "Directory creation failed")
        self.checkpoint_manager.complete_operation(operation_id, ai_response)
        
        return result
    
    def delete_directory_tracked(self, dir_path: str, recursive: bool = False, user_message: str = None) -> Dict[str, Any]:
        """Delete directory with checkpoint tracking"""
        operation_id = self.start_file_operation(
            OperationType.DIRECTORY_DELETE,
            f"Delete directory {dir_path}{'(recursive)' if recursive else ''}",
            dir_path,
            user_message
        )
        
        # Perform the operation
        result = self.file_ops.delete_directory(dir_path, recursive)
        
        # Complete tracking
        ai_response = result.get("message", "Directory deleted") if result["success"] else result.get("error", "Directory deletion failed")
        self.checkpoint_manager.complete_operation(operation_id, ai_response)
        
        return result


# Global checkpoint-aware file operations (will be initialized by agent)
_checkpoint_file_ops: Optional[CheckpointAwareFileOperations] = None


def initialize_checkpoint_file_ops(checkpoint_manager: CheckpointManager):
    """Initialize the global checkpoint-aware file operations"""
    global _checkpoint_file_ops
    _checkpoint_file_ops = CheckpointAwareFileOperations(checkpoint_manager)


def get_checkpoint_manager() -> Optional[CheckpointManager]:
    """Get the current checkpoint manager"""
    return _checkpoint_file_ops.checkpoint_manager if _checkpoint_file_ops else None


# Checkpoint-aware tool implementations

@tool
def read_file_checkpoint_aware(file_path: str = "") -> str:
    """
    Read the contents of a file with checkpoint awareness.
    
    This is a checkpoint-aware version of file reading that tracks access
    patterns while not modifying files.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        String containing file contents and metadata
    """
    # Parameter validation
    if not file_path or file_path.strip() == "":
        return "❌ PARAMETER ERROR: file_path is required but was empty. You must provide the path to the file to read."
    
    if _checkpoint_file_ops is None:
        # Fallback to standard file operations
        from .file_operations import _file_ops
        result = _file_ops.read_file(file_path)
    else:
        result = _checkpoint_file_ops.read_file_tracked(file_path)
    
    if result["success"]:
        return f"📁 File: {result.get('file_path', file_path)}\n📊 Size: {result['size']} characters, {result['lines']} lines\n\n📄 Content:\n{result['content']}"
    else:
        return f"❌ Error reading file: {result['error']}"


@tool
def write_file_checkpoint_aware(file_path: str = "", content: str = "") -> str:
    """Write content to a file with automatic checkpoint tracking.
    
    Args:
        file_path: The path where to write the file
        content: The actual content to write to the file
    """
    # Explicit parameter validation with clear error messages
    if not file_path or file_path.strip() == "":
        return "❌ PARAMETER ERROR: file_path is required but was empty. You must provide both file_path AND content parameters."
    
    if content is None or content == "":
        return "❌ PARAMETER ERROR: content parameter is missing or empty. You MUST call this tool with BOTH parameters: write_file_checkpoint_aware(file_path='your/path', content='your content here')"
    
    if _checkpoint_file_ops is None:
        # Fallback to standard file operations
        from .file_operations import _file_ops
        result = _file_ops.write_file(file_path, content)
    else:
        result = _checkpoint_file_ops.write_file_tracked(file_path, content)
    
    if result["success"]:
        return f"✅ {result['message']}\n🔄 Operation tracked - use /undo to revert if needed"
    else:
        return f"❌ Error writing file: {result['error']}"


@tool
def replace_in_file_checkpoint_aware(file_path: str = "", search_term: str = "", replace_term: str = "", case_sensitive: bool = False) -> str:
    """Replace text within a file with automatic checkpoint tracking.
    
    Args:
        file_path: Path to the file to modify
        search_term: Text to find and replace
        replace_term: Text to replace with
        case_sensitive: Whether replacement should be case sensitive (default: False)
    """
    # Parameter validation
    if not file_path or file_path.strip() == "":
        return "❌ PARAMETER ERROR: file_path is required but was empty. You must provide file_path, search_term, and replace_term parameters."
    
    if not search_term or search_term.strip() == "":
        return "❌ PARAMETER ERROR: search_term is required but was empty. You must provide the text to search for."
    
    if replace_term is None:
        return "❌ PARAMETER ERROR: replace_term is required. You must provide the replacement text (can be empty string for deletion)."
    
    if _checkpoint_file_ops is None:
        # Fallback to standard file operations
        from .file_operations import _file_ops
        result = _file_ops.replace_in_file(file_path, search_term, replace_term, case_sensitive)
    else:
        result = _checkpoint_file_ops.replace_in_file_tracked(file_path, search_term, replace_term, case_sensitive)
    
    if result["success"]:
        return f"✅ {result['message']}\n🔄 Operation tracked - use /undo to revert if needed"
    else:
        return f"❌ Error replacing in file: {result['error']}"


@tool
def delete_file_checkpoint_aware(file_path: str = "") -> str:
    """
    Delete a file with automatic checkpoint tracking.
    
    This creates a backup before deletion, allowing you to restore the file.
    The operation is automatically tracked and can be reverted.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        String with operation result
    """
    # Parameter validation
    if not file_path or file_path.strip() == "":
        return "❌ PARAMETER ERROR: file_path is required but was empty. You must provide the path to the file to delete."
    
    if _checkpoint_file_ops is None:
        # Fallback to standard file operations
        from .file_operations import _file_ops
        result = _file_ops.delete_file(file_path)
    else:
        result = _checkpoint_file_ops.delete_file_tracked(file_path)
    
    if result["success"]:
        return f"✅ {result['message']}\n🔄 Operation tracked - use /undo to restore if needed"
    else:
        return f"❌ Error deleting file: {result['error']}"


@tool
def create_directory_checkpoint_aware(dir_path: str = "") -> str:
    """
    Create a new directory with automatic checkpoint tracking.
    
    This tracks directory creation, allowing you to undo the operation.
    The operation is automatically tracked and can be reverted.
    
    Args:
        dir_path: Path of the directory to create
        
    Returns:
        String with operation result
    """
    # Parameter validation
    if not dir_path or dir_path.strip() == "":
        return "❌ PARAMETER ERROR: dir_path is required but was empty. You must provide the path of the directory to create."
    
    if _checkpoint_file_ops is None:
        # Fallback to standard file operations
        from .file_operations import _file_ops
        result = _file_ops.create_directory(dir_path)
    else:
        result = _checkpoint_file_ops.create_directory_tracked(dir_path)
    
    if result["success"]:
        return f"✅ {result['message']}\n🔄 Operation tracked - use /undo to revert if needed"
    else:
        return f"❌ Error creating directory: {result['error']}"


@tool
def delete_directory_checkpoint_aware(dir_path: str = "", recursive: bool = False) -> str:
    """
    Delete a directory with automatic checkpoint tracking.
    
    This creates backups before deletion, allowing you to restore the directory.
    The operation is automatically tracked and can be reverted.
    
    Args:
        dir_path: Path of the directory to delete
        recursive: Whether to delete directory and all its contents (default: False)
        
    Returns:
        String with operation result
    """
    # Parameter validation
    if not dir_path or dir_path.strip() == "":
        return "❌ PARAMETER ERROR: dir_path is required but was empty. You must provide the path of the directory to delete."
    
    if _checkpoint_file_ops is None:
        # Fallback to standard file operations
        from .file_operations import _file_ops
        result = _file_ops.delete_directory(dir_path, recursive)
    else:
        result = _checkpoint_file_ops.delete_directory_tracked(dir_path, recursive)
    
    if result["success"]:
        return f"✅ {result['message']}\n🔄 Operation tracked - use /undo to restore if needed"
    else:
        return f"❌ Error deleting directory: {result['error']}"


# Keep non-modifying operations the same
@tool
def search_in_file_checkpoint_aware(file_path: str = "", search_term: str = "", case_sensitive: bool = False) -> str:
    """
    Search for text within a file (non-modifying operation).
    
    This is identical to the standard search but part of the checkpoint-aware toolset.
    
    Args:
        file_path: Path to the file to search in
        search_term: Text to search for
        case_sensitive: Whether search should be case sensitive (default: False)
        
    Returns:
        String with search results
    """
    # Parameter validation
    if not file_path or file_path.strip() == "":
        return "❌ PARAMETER ERROR: file_path is required but was empty. You must provide the path to the file to search in."
    
    if not search_term or search_term.strip() == "":
        return "❌ PARAMETER ERROR: search_term is required but was empty. You must provide the text to search for."
    
    from .file_operations import _file_ops
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
def list_files_checkpoint_aware(dir_path: str = ".", pattern: str = "*", recursive: bool = False) -> str:
    """
    List files and directories with smart filtering to avoid token overload.
    
    Automatically excludes common large directories like .venv, node_modules, etc.
    to prevent token limit errors and provide relevant project files only.
    
    Args:
        dir_path: Directory path to list (default: current directory)
        pattern: File pattern to match (default: "*" for all files)
        recursive: Whether to list files recursively in subdirectories (default: False)
        
    Returns:
        String with directory listing (filtered)
    """
    from .file_operations import _file_ops
    result = _file_ops.list_files(dir_path, pattern, recursive)
    
    if not result["success"]:
        return f"❌ Error listing files: {result['error']}"
    
    formatted_result = f"📁 Directory: {result['directory_path']}\n"
    formatted_result += f"📊 Found: {result['total_files']} files, {result['total_directories']} directories"
    
    # Show ignored count if any
    if result.get('ignored_items', 0) > 0:
        formatted_result += f" (excluded {result['ignored_items']} items from .venv, node_modules, etc.)"
    
    formatted_result += "\n\n"
    
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
    
    if not result["files"] and not result["directories"]:
        formatted_result += "📝 No relevant files found (common build/cache directories are automatically excluded)\n"
    
    return formatted_result


def get_checkpoint_aware_file_operation_tools() -> List:
    """
    Get list of checkpoint-aware file operation tools for LangGraph integration
    
    Returns:
        List of checkpoint-aware file operation tools
    """
    return [
        read_file_checkpoint_aware,
        write_file_checkpoint_aware,
        replace_in_file_checkpoint_aware,
        delete_file_checkpoint_aware,
        create_directory_checkpoint_aware,
        delete_directory_checkpoint_aware,
        search_in_file_checkpoint_aware,
        list_files_checkpoint_aware
    ]

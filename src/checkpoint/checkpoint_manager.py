"""
R-Code Checkpoint Manager
========================

Advanced checkpoint system for tracking and reverting AI-made changes.
Provides enterprise-grade version control for AI operations with detailed history.
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class OperationType(Enum):
    """Types of operations that can be tracked"""
    FILE_CREATE = "file_create"
    FILE_MODIFY = "file_modify"
    FILE_DELETE = "file_delete"
    DIRECTORY_CREATE = "directory_create"
    DIRECTORY_DELETE = "directory_delete"
    TERMINAL_COMMAND = "terminal_command"
    AI_CHAT = "ai_chat"


@dataclass
class FileSnapshot:
    """Snapshot of a file's state"""
    path: str
    content: Optional[str]
    exists: bool
    size: int
    hash_md5: Optional[str]
    modified_time: float
    permissions: Optional[str]


@dataclass
class Operation:
    """Single operation in the checkpoint system"""
    id: str
    type: OperationType
    timestamp: datetime
    description: str
    files_before: Dict[str, FileSnapshot]
    files_after: Dict[str, FileSnapshot]
    metadata: Dict[str, Any]
    user_message: Optional[str] = None
    ai_response: Optional[str] = None


@dataclass
class Checkpoint:
    """A checkpoint containing multiple operations"""
    id: str
    timestamp: datetime
    description: str
    operations: List[Operation]
    auto_created: bool
    tag: Optional[str] = None


class CheckpointManager:
    """Enterprise-grade checkpoint manager for R-Code"""
    
    def __init__(self, workspace_path: str = None):
        """Initialize checkpoint manager"""
        self.workspace_path = Path(workspace_path or os.getcwd())
        self.checkpoint_dir = self.workspace_path / ".rcode" / "checkpoints"
        self.backup_dir = self.workspace_path / ".rcode" / "backups"
        self.state_file = self.checkpoint_dir / "state.json"
        
        # Ensure directories exist
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self.checkpoints: List[Checkpoint] = []
        self.current_operations: List[Operation] = []
        self.session_id = str(uuid.uuid4())[:8]
        
        # Load existing state
        self._load_state()
        
        # Auto-create initial checkpoint
        self._create_initial_checkpoint()
    
    def _load_state(self):
        """Load checkpoint state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert loaded data back to dataclasses
                self.checkpoints = []
                for cp_data in data.get('checkpoints', []):
                    operations = []
                    for op_data in cp_data.get('operations', []):
                        # Convert file snapshots
                        files_before = {
                            path: FileSnapshot(**snapshot_data)
                            for path, snapshot_data in op_data.get('files_before', {}).items()
                        }
                        files_after = {
                            path: FileSnapshot(**snapshot_data)
                            for path, snapshot_data in op_data.get('files_after', {}).items()
                        }
                        
                        operation = Operation(
                            id=op_data['id'],
                            type=OperationType(op_data['type']),
                            timestamp=datetime.fromisoformat(op_data['timestamp']),
                            description=op_data['description'],
                            files_before=files_before,
                            files_after=files_after,
                            metadata=op_data.get('metadata', {}),
                            user_message=op_data.get('user_message'),
                            ai_response=op_data.get('ai_response')
                        )
                        operations.append(operation)
                    
                    checkpoint = Checkpoint(
                        id=cp_data['id'],
                        timestamp=datetime.fromisoformat(cp_data['timestamp']),
                        description=cp_data['description'],
                        operations=operations,
                        auto_created=cp_data.get('auto_created', True),
                        tag=cp_data.get('tag')
                    )
                    self.checkpoints.append(checkpoint)
                    
            except Exception as e:
                print(f"⚠️  Failed to load checkpoint state: {e}")
    
    def _save_state(self):
        """Save checkpoint state to disk"""
        try:
            # Convert dataclasses to serializable format
            data = {
                'checkpoints': [],
                'session_id': self.session_id,
                'last_updated': datetime.now().isoformat()
            }
            
            for checkpoint in self.checkpoints:
                cp_data = {
                    'id': checkpoint.id,
                    'timestamp': checkpoint.timestamp.isoformat(),
                    'description': checkpoint.description,
                    'auto_created': checkpoint.auto_created,
                    'tag': checkpoint.tag,
                    'operations': []
                }
                
                for operation in checkpoint.operations:
                    files_before = {
                        path: asdict(snapshot)
                        for path, snapshot in operation.files_before.items()
                    }
                    files_after = {
                        path: asdict(snapshot)
                        for path, snapshot in operation.files_after.items()
                    }
                    
                    op_data = {
                        'id': operation.id,
                        'type': operation.type.value,
                        'timestamp': operation.timestamp.isoformat(),
                        'description': operation.description,
                        'files_before': files_before,
                        'files_after': files_after,
                        'metadata': operation.metadata,
                        'user_message': operation.user_message,
                        'ai_response': operation.ai_response
                    }
                    cp_data['operations'].append(op_data)
                
                data['checkpoints'].append(cp_data)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint state: {e}")
    
    def _create_file_snapshot(self, file_path: str) -> FileSnapshot:
        """Create a snapshot of a file's current state"""
        path = Path(file_path)
        
        if path.exists() and path.is_file():
            try:
                content = path.read_text(encoding='utf-8')
                hash_md5 = hashlib.md5(content.encode('utf-8')).hexdigest()
                stat = path.stat()
                
                return FileSnapshot(
                    path=str(path),
                    content=content,
                    exists=True,
                    size=stat.st_size,
                    hash_md5=hash_md5,
                    modified_time=stat.st_mtime,
                    permissions=oct(stat.st_mode)[-3:]
                )
            except Exception as e:
                # File exists but can't read (binary, permissions, etc.)
                stat = path.stat()
                return FileSnapshot(
                    path=str(path),
                    content=None,
                    exists=True,
                    size=stat.st_size,
                    hash_md5=None,
                    modified_time=stat.st_mtime,
                    permissions=oct(stat.st_mode)[-3:]
                )
        else:
            return FileSnapshot(
                path=str(path),
                content=None,
                exists=False,
                size=0,
                hash_md5=None,
                modified_time=0,
                permissions=None
            )
    
    def _backup_file(self, file_path: str, operation_id: str):
        """Create a backup of a file"""
        try:
            source = Path(file_path)
            if source.exists() and source.is_file():
                backup_name = f"{operation_id}_{source.name}_{int(datetime.now().timestamp())}"
                backup_path = self.backup_dir / backup_name
                shutil.copy2(source, backup_path)
                return str(backup_path)
        except Exception as e:
            print(f"⚠️  Failed to backup {file_path}: {e}")
        return None
    
    def _restore_file(self, snapshot: FileSnapshot):
        """Restore a file from a snapshot"""
        try:
            path = Path(snapshot.path)
            
            if snapshot.exists and snapshot.content is not None:
                # Ensure parent directory exists
                path.parent.mkdir(parents=True, exist_ok=True)
                # Restore file content
                path.write_text(snapshot.content, encoding='utf-8')
                # Restore permissions if available
                if snapshot.permissions:
                    try:
                        os.chmod(path, int(snapshot.permissions, 8))
                    except:
                        pass
            elif not snapshot.exists and path.exists():
                # File should not exist, remove it
                path.unlink()
                
        except Exception as e:
            print(f"⚠️  Failed to restore {snapshot.path}: {e}")
    
    def start_operation(self, operation_type: OperationType, description: str, 
                       files: List[str], user_message: str = None) -> str:
        """Start tracking a new operation"""
        operation_id = str(uuid.uuid4())[:8]
        
        # Create snapshots of files before operation
        files_before = {}
        for file_path in files:
            files_before[file_path] = self._create_file_snapshot(file_path)
            # Create backup if file exists
            if files_before[file_path].exists:
                self._backup_file(file_path, operation_id)
        
        # Store operation start state
        operation = Operation(
            id=operation_id,
            type=operation_type,
            timestamp=datetime.now(),
            description=description,
            files_before=files_before,
            files_after={},  # Will be filled when operation completes
            metadata={},
            user_message=user_message
        )
        
        self.current_operations.append(operation)
        return operation_id
    
    def complete_operation(self, operation_id: str, ai_response: str = None, 
                          metadata: Dict[str, Any] = None):
        """Complete an operation and create snapshots of final state"""
        operation = None
        for op in self.current_operations:
            if op.id == operation_id:
                operation = op
                break
        
        if not operation:
            return
        
        # Create snapshots of files after operation
        files_after = {}
        for file_path in operation.files_before.keys():
            files_after[file_path] = self._create_file_snapshot(file_path)
        
        # Update operation
        operation.files_after = files_after
        operation.ai_response = ai_response
        if metadata:
            operation.metadata.update(metadata)
        
        # Remove from current operations
        self.current_operations.remove(operation)
        
        # Auto-create checkpoint if significant changes
        if self._has_significant_changes(operation):
            self.create_checkpoint(f"Auto: {operation.description}", [operation], auto_created=True)
    
    def _has_significant_changes(self, operation: Operation) -> bool:
        """Check if operation has significant changes worth checkpointing"""
        for path, before in operation.files_before.items():
            after = operation.files_after.get(path)
            if not after:
                continue
                
            # Check if file was created, deleted, or modified
            if before.exists != after.exists:
                return True
            if before.hash_md5 != after.hash_md5:
                return True
        
        return False
    
    def create_checkpoint(self, description: str, operations: List[Operation] = None, 
                         auto_created: bool = False, tag: str = None) -> str:
        """Create a new checkpoint"""
        checkpoint_id = str(uuid.uuid4())[:8]
        
        if operations is None:
            operations = self.current_operations.copy()
            self.current_operations.clear()
        
        checkpoint = Checkpoint(
            id=checkpoint_id,
            timestamp=datetime.now(),
            description=description,
            operations=operations,
            auto_created=auto_created,
            tag=tag
        )
        
        self.checkpoints.append(checkpoint)
        self._save_state()
        
        return checkpoint_id
    
    def get_checkpoints(self, limit: int = None) -> List[Checkpoint]:
        """Get list of checkpoints, newest first"""
        checkpoints = sorted(self.checkpoints, key=lambda x: x.timestamp, reverse=True)
        return checkpoints[:limit] if limit else checkpoints
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a specific checkpoint"""
        for checkpoint in self.checkpoints:
            if checkpoint.id == checkpoint_id:
                return checkpoint
        return None
    
    def revert_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Revert to a specific checkpoint"""
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            return False
        
        try:
            # Collect all files that need to be reverted
            all_files = set()
            
            # Get files from all operations after this checkpoint
            checkpoint_time = checkpoint.timestamp
            for cp in self.checkpoints:
                if cp.timestamp > checkpoint_time:
                    for operation in cp.operations:
                        all_files.update(operation.files_before.keys())
                        all_files.update(operation.files_after.keys())
            
            # Get the state before this checkpoint's operations
            for operation in checkpoint.operations:
                for file_path, snapshot in operation.files_before.items():
                    self._restore_file(snapshot)
            
            # Remove checkpoints after this one
            self.checkpoints = [cp for cp in self.checkpoints if cp.timestamp <= checkpoint_time]
            self._save_state()
            
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to revert to checkpoint {checkpoint_id}: {e}")
            return False
    
    def undo_last_operation(self) -> bool:
        """Undo the last operation"""
        if not self.checkpoints:
            return False
        
        # Get the last checkpoint
        last_checkpoint = self.checkpoints[-1]
        if not last_checkpoint.operations:
            return False
        
        # Get the last operation
        last_operation = last_checkpoint.operations[-1]
        
        try:
            # Restore files to their before state
            for file_path, snapshot in last_operation.files_before.items():
                self._restore_file(snapshot)
            
            # Remove the operation from the checkpoint
            last_checkpoint.operations.remove(last_operation)
            
            # If checkpoint is empty, remove it
            if not last_checkpoint.operations:
                self.checkpoints.remove(last_checkpoint)
            
            self._save_state()
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to undo last operation: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of checkpoint system"""
        total_operations = sum(len(cp.operations) for cp in self.checkpoints)
        
        return {
            "session_id": self.session_id,
            "workspace_path": str(self.workspace_path),
            "total_checkpoints": len(self.checkpoints),
            "total_operations": total_operations,
            "current_operations": len(self.current_operations),
            "last_checkpoint": self.checkpoints[-1].timestamp.isoformat() if self.checkpoints else None,
            "checkpoint_dir": str(self.checkpoint_dir),
            "backup_dir": str(self.backup_dir)
        }
    
    def _create_initial_checkpoint(self):
        """Create initial checkpoint for the session"""
        if not self.checkpoints:
            # Create initial checkpoint with current state
            initial_op = Operation(
                id=str(uuid.uuid4())[:8],
                type=OperationType.AI_CHAT,
                timestamp=datetime.now(),
                description="Initial session state",
                files_before={},
                files_after={},
                metadata={"session_start": True}
            )
            
            self.create_checkpoint("Session Start", [initial_op], auto_created=True, tag="initial")
    
    def cleanup_old_checkpoints(self, keep_count: int = 50):
        """Clean up old checkpoints to save space"""
        if len(self.checkpoints) > keep_count:
            # Keep the most recent checkpoints
            self.checkpoints = sorted(self.checkpoints, key=lambda x: x.timestamp, reverse=True)
            old_checkpoints = self.checkpoints[keep_count:]
            self.checkpoints = self.checkpoints[:keep_count]
            
            # Clean up backup files for removed checkpoints
            for checkpoint in old_checkpoints:
                for operation in checkpoint.operations:
                    # Remove backup files for this operation
                    backup_pattern = f"{operation.id}_*"
                    for backup_file in self.backup_dir.glob(backup_pattern):
                        try:
                            backup_file.unlink()
                        except:
                            pass
            
            self._save_state()

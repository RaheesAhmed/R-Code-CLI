"""
R-Code Checkpoint Module
=======================

Enterprise-grade checkpoint and version control system for R-Code AI operations.
Provides automatic change tracking, rollback capabilities, and session management.
"""

from .checkpoint_manager import (
    CheckpointManager,
    OperationType,
    FileSnapshot,
    Operation,
    Checkpoint
)

__all__ = [
    'CheckpointManager',
    'OperationType',
    'FileSnapshot',
    'Operation',
    'Checkpoint'
]

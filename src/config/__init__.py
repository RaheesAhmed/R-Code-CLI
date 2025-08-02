"""
R-Code Configuration Package
===========================

Configuration management for R-Code AI assistant including models,
MCP servers, and custom user rules.
"""

from .config_manager import RCodeConfigManager, config_manager

__all__ = [
    "RCodeConfigManager",
    "config_manager"
]

#!/usr/bin/env python3
"""
R-Code CLI - Main Entry Script
==============================
This is the main entry point for the R-Code CLI application.
Redirects to the main application logic in src/main.py.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the main CLI application
from src.main import cli_entry_point

if __name__ == "__main__":
    cli_entry_point()

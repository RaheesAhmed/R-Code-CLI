#!/usr/bin/env python3
"""
R-Code CLI - Main Entry Script
==============================
This is the main entry point for the R-Code CLI application.
Launches the interactive AI chat assistant with premium styling.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """
    Main entry point for R-Code CLI.
    Launches the interactive AI chat assistant.
    """
    try:
        # Import and run the main chat application
        from src.main import main as chat_main
        
        # Run the async chat application
        asyncio.run(chat_main())
        
    except KeyboardInterrupt:
        # Handle graceful shutdown
        print("\n👋 R-Code CLI terminated by user")
        sys.exit(0)
        
    except ImportError as e:
        print(f"❌ Error importing R-Code modules: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error starting R-Code CLI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
R-Code CLI Dependency Installer
=======================================
Handles network timeouts and installation issues gracefully
"""

import subprocess
import sys
import time
import os
from typing import List, Dict, Any

class DependencyInstaller:
    """Advanced dependency installer with retry logic and timeout handling"""
    
    def __init__(self):
        self.max_retries = 3
        self.timeout = 300  # 5 minutes
        self.retry_delay = 10  # seconds
        
    def run_command(self, command: List[str], timeout: int = None) -> Dict[str, Any]:
        """Run command with timeout and error handling"""
        timeout = timeout or self.timeout
        
        try:
            print(f"Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def install_with_retry(self, package: str, retries: int = None) -> bool:
        """Install package with retry logic"""
        retries = retries or self.max_retries
        
        for attempt in range(retries):
            print(f"\nAttempt {attempt + 1}/{retries} to install {package}")
            
            # Try different installation strategies
            strategies = [
                # Strategy 1: Standard install with increased timeout
                [sys.executable, "-m", "pip", "install", "--timeout", "300", package],
                
                # Strategy 2: Use alternative index
                [sys.executable, "-m", "pip", "install", "--index-url", "https://pypi.org/simple/", "--timeout", "300", package],
                
                # Strategy 3: Use cached wheels if available
                [sys.executable, "-m", "pip", "install", "--no-deps", "--timeout", "300", package],
                
                # Strategy 4: Force reinstall
                [sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-cache-dir", "--timeout", "300", package]
            ]
            
            for strategy_idx, command in enumerate(strategies):
                print(f"  Using strategy {strategy_idx + 1}: {' '.join(command)}")
                result = self.run_command(command)
                
                if result['success']:
                    print(f"✅ Successfully installed {package}")
                    return True
                else:
                    print(f"❌ Strategy {strategy_idx + 1} failed: {result['stderr']}")
                    
                    # If it's a timeout, try next strategy immediately
                    if 'timed out' in result['stderr'].lower():
                        continue
                    
                    # For other errors, wait before retry
                    if strategy_idx < len(strategies) - 1:
                        time.sleep(5)
            
            if attempt < retries - 1:
                print(f"Waiting {self.retry_delay} seconds before next attempt...")
                time.sleep(self.retry_delay)
        
        print(f"❌ Failed to install {package} after {retries} attempts")
        return False
    
    def install_core_dependencies(self) -> bool:
        """Install core dependencies in order of importance"""
        
        # Core packages in order of dependency
        core_packages = [
            "wheel",
            "setuptools",
            "typing-extensions>=4.6.0",
            "pydantic>=2.0.0",
            "langchain-core",
            "langchain",
            "langchain-openai",
            "sqlalchemy>=2.0.0",
            "langgraph",
        ]
        
        print("🚀 Installing core dependencies for Multi-Agent System...")
        
        failed_packages = []
        
        for package in core_packages:
            if not self.install_with_retry(package):
                failed_packages.append(package)
        
        if failed_packages:
            print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
            print("\nTroubleshooting suggestions:")
            print("1. Check your internet connection")
            print("2. Try using a VPN if you're behind a firewall")
            print("3. Consider using conda instead: conda install -c conda-forge <package>")
            print("4. Try manual installation: pip install <package> --user")
            return False
        
        print("\n✅ All core dependencies installed successfully!")
        return True
    
    def install_optional_dependencies(self) -> bool:
        """Install optional dependencies"""
        
        optional_packages = [
            "rich",
            "click",
            "loguru",
            "python-dotenv",
            "aiohttp",
            "httpx",
        ]
        
        print("\n🔧 Installing optional dependencies...")
        
        for package in optional_packages:
            if not self.install_with_retry(package, retries=2):
                print(f"⚠️ Optional package {package} failed to install (continuing...)")
        
        return True
    
    def verify_installation(self) -> bool:
        """Verify that key packages can be imported"""
        
        test_imports = [
            "langchain",
            "langchain_core",
            "langchain_openai", 
            "langgraph",
            "sqlalchemy",
            "pydantic",
        ]
        
        print("\n🔍 Verifying installation...")
        
        failed_imports = []
        
        for package in test_imports:
            try:
                __import__(package)
                print(f"✅ {package} - OK")
            except ImportError as e:
                print(f"❌ {package} - FAILED: {e}")
                failed_imports.append(package)
        
        if failed_imports:
            print(f"\n❌ Failed imports: {', '.join(failed_imports)}")
            return False
        
        print("\n✅ All packages verified successfully!")
        return True

def main():
    """Main installation process"""
    installer = DependencyInstaller()
    
    print("=" * 60)
    print("🤖 Multi-Agent Coding System - Dependency Installer")
    print("=" * 60)
    
    # Step 1: Upgrade pip first
    print("\n1. Upgrading pip...")
    result = installer.run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    if result['success']:
        print("✅ pip upgraded successfully")
    else:
        print("⚠️ pip upgrade failed, continuing anyway...")
    
    # Step 2: Install core dependencies
    if not installer.install_core_dependencies():
        print("\n❌ Core dependency installation failed!")
        sys.exit(1)
    
    # Step 3: Install optional dependencies
    installer.install_optional_dependencies()
    
    # Step 4: Verify installation
    if not installer.verify_installation():
        print("\n⚠️ Some packages failed verification. The system may not work correctly.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Installation completed successfully!")
    print("🚀 R-Code is ready to use!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
    print("2. Run the system: python agents.py")
    print("3. Check the README.md for usage examples")

if __name__ == "__main__":
    main()

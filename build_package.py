#!/usr/bin/env python3
"""
R-Code CLI Package Builder
=========================

Professional package builder for R-Code CLI with comprehensive validation and build steps.
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path


def run_command(cmd, description=""):
    """Run command with error handling"""
    print(f"🔧 {description}")
    print(f"   Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False


def validate_project_structure():
    """Validate project structure before building"""
    print("🔍 Validating project structure...")
    
    required_files = [
        "pyproject.toml",
        "setup.py", 
        "MANIFEST.in",
        "README.MD",
        "LICENSE",
        "cli.py",
        "src/__init__.py",
        "src/main.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True


def clean_build_artifacts():
    """Clean previous build artifacts"""
    print("🧹 Cleaning build artifacts...")
    
    artifacts = ["build", "dist", "*.egg-info", "__pycache__"]
    
    for artifact in artifacts:
        if "*" in artifact:
            # Handle wildcards
            for path in Path(".").glob(artifact):
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"   Removed directory: {path}")
                else:
                    path.unlink()
                    print(f"   Removed file: {path}")
        else:
            path = Path(artifact)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"   Removed directory: {path}")
                else:
                    path.unlink()
                    print(f"   Removed file: {path}")


def check_dependencies():
    """Check if build dependencies are installed"""
    print("📦 Checking build dependencies...")
    
    required_packages = ["build", "twine", "wheel"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️  Missing build dependencies: {missing_packages}")
        print("   Installing missing dependencies...")
        
        for package in missing_packages:
            if not run_command(f"pip install {package}", f"Installing {package}"):
                return False
    
    print("✅ All build dependencies available")
    return True


def build_package():
    """Build the package"""
    print("🏗️  Building package...")
    
    if not run_command("python -m build", "Building wheel and source distribution"):
        return False
    
    print("✅ Package built successfully")
    return True


def validate_package():
    """Validate the built package"""
    print("🔍 Validating built package...")
    
    # Check if dist files exist
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ No dist directory found")
        return False
    
    whl_files = list(dist_dir.glob("*.whl"))
    tar_files = list(dist_dir.glob("*.tar.gz"))
    
    if not whl_files:
        print("❌ No wheel file found")
        return False
    
    if not tar_files:
        print("❌ No source distribution found") 
        return False
    
    print(f"✅ Found wheel: {whl_files[0].name}")
    print(f"✅ Found source: {tar_files[0].name}")
    
    # Validate with twine
    if not run_command("twine check dist/*", "Validating package with twine"):
        return False
    
    print("✅ Package validation successful")
    return True


def get_package_info():
    """Get package information"""
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()
            
        # Extract basic info (simple parsing)
        lines = content.split("\n")
        info = {}
        
        for line in lines:
            if line.startswith('name = '):
                info['name'] = line.split('"')[1]
            elif line.startswith('version = '):
                info['version'] = line.split('"')[1]
            elif line.startswith('description = '):
                info['description'] = line.split('"')[1]
        
        return info
    except Exception as e:
        print(f"⚠️  Could not parse package info: {e}")
        return {"name": "rcode", "version": "unknown", "description": "R-Code CLI"}


def main():
    """Main build process"""
    print("🚀 R-Code CLI Package Builder")
    print("=" * 50)
    
    # Get package info
    pkg_info = get_package_info()
    print(f"📦 Package: {pkg_info['name']} v{pkg_info['version']}")
    print(f"📝 Description: {pkg_info['description']}")
    print()
    
    # Validation steps
    if not validate_project_structure():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Build steps
    clean_build_artifacts()
    
    if not build_package():
        sys.exit(1)
    
    if not validate_package():
        sys.exit(1)
    
    print()
    print("🎉 Package built successfully!")
    print()
    print("📦 Available distributions:")
    
    dist_dir = Path("dist")
    for file in dist_dir.iterdir():
        print(f"   • {file.name} ({file.stat().st_size / 1024:.1f} KB)")
    
    print()
    print("🚀 Next steps:")
    print("   • Test installation: pip install dist/*.whl")
    print("   • Upload to PyPI: twine upload dist/*")
    print("   • Install from PyPI: pip install rcode")


if __name__ == "__main__":
    main()

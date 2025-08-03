#!/usr/bin/env python3
"""
R-Code CLI PyPI Upload Script
============================

Professional PyPI upload script with comprehensive checks and safe upload process.
"""

import os
import sys
import subprocess
import getpass
from pathlib import Path


def run_command(cmd, description="", capture_output=True):
    """Run command with error handling"""
    print(f"🔧 {description}")
    print(f"   Running: {cmd}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=capture_output, 
            text=True
        )
        if result.stdout and capture_output:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False


def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if dist directory exists
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ No dist directory found. Run 'python build_package.py' first.")
        return False
    
    # Check if build artifacts exist
    whl_files = list(dist_dir.glob("*.whl"))
    tar_files = list(dist_dir.glob("*.tar.gz"))
    
    if not whl_files or not tar_files:
        print("❌ Missing build artifacts. Run 'python build_package.py' first.")
        return False
    
    print(f"✅ Found {len(whl_files)} wheel file(s)")
    print(f"✅ Found {len(tar_files)} source distribution(s)")
    
    # Check if twine is available
    try:
        subprocess.run(["twine", "--version"], check=True, capture_output=True)
        print("✅ Twine is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Twine not found. Install with: pip install twine")
        return False
    
    return True


def validate_package():
    """Validate package before upload"""
    print("🔍 Validating package...")
    
    if not run_command("twine check dist/*", "Validating with twine"):
        return False
    
    print("✅ Package validation successful")
    return True


def get_upload_choice():
    """Get user choice for upload target"""
    print("\n📦 Upload Options:")
    print("1. TestPyPI (Recommended for testing)")
    print("2. PyPI (Production - Live package)")
    print("3. Cancel")
    
    while True:
        choice = input("\nChoose upload target (1-3): ").strip()
        
        if choice == "1":
            return "testpypi"
        elif choice == "2":
            return "pypi"
        elif choice == "3":
            return None
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def upload_to_testpypi():
    """Upload to TestPyPI"""
    print("🚀 Uploading to TestPyPI...")
    print("📝 Note: You'll need TestPyPI credentials")
    print("   Create account at: https://test.pypi.org/account/register/")
    
    cmd = "twine upload --repository testpypi dist/*"
    return run_command(cmd, "Uploading to TestPyPI", capture_output=False)


def upload_to_pypi():
    """Upload to PyPI"""
    print("🚀 Uploading to PyPI...")
    print("⚠️  WARNING: This will upload to the LIVE PyPI repository!")
    print("📝 Note: You'll need PyPI credentials")
    print("   Create account at: https://pypi.org/account/register/")
    
    confirm = input("\nAre you sure you want to upload to PyPI? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("❌ Upload cancelled")
        return False
    
    cmd = "twine upload dist/*"
    return run_command(cmd, "Uploading to PyPI", capture_output=False)


def show_post_upload_info(target):
    """Show information after successful upload"""
    print("\n🎉 Upload successful!")
    
    if target == "testpypi":
        print("\n📦 TestPyPI Package Information:")
        print("   URL: https://test.pypi.org/project/rcode/")
        print("   Install: pip install -i https://test.pypi.org/simple/ rcode")
        print("\n💡 Test your package:")
        print("   1. Create a new virtual environment")
        print("   2. Install from TestPyPI using the command above")
        print("   3. Test: rcode --help")
        print("   4. If everything works, upload to PyPI")
        
    elif target == "pypi":
        print("\n📦 PyPI Package Information:")
        print("   URL: https://pypi.org/project/rcode/")
        print("   Install: pip install rcode")
        print("\n🎊 Congratulations! Your package is now live on PyPI!")
        print("   Anyone can now install R-Code CLI with: pip install rcode")


def main():
    """Main upload process"""
    print("🚀 R-Code CLI PyPI Upload")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Validate package
    if not validate_package():
        sys.exit(1)
    
    # Get upload choice
    target = get_upload_choice()
    
    if target is None:
        print("❌ Upload cancelled")
        sys.exit(0)
    
    # Upload based on choice
    success = False
    
    if target == "testpypi":
        success = upload_to_testpypi()
    elif target == "pypi":
        success = upload_to_pypi()
    
    if success:
        show_post_upload_info(target)
    else:
        print("❌ Upload failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

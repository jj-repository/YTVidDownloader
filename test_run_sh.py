#!/usr/bin/env python3
"""Test that run.sh would work correctly"""

import subprocess
import os

print("Testing run.sh script...")
print("-" * 50)

# Check if run.sh exists and is executable
if not os.path.exists("run.sh"):
    print("✗ run.sh not found!")
    exit(1)

if not os.access("run.sh", os.X_OK):
    print("✗ run.sh is not executable!")
    exit(1)

print("✓ run.sh exists and is executable")

# Check if venv/bin/python exists
if not os.path.exists("./venv/bin/python"):
    print("✗ venv/bin/python not found!")
    exit(1)

print("✓ venv/bin/python exists")

# Check if downloader.py exists
if not os.path.exists("downloader.py"):
    print("✗ downloader.py not found!")
    exit(1)

print("✓ downloader.py exists")

# Verify the Python interpreter works
try:
    result = subprocess.run(
        ["./venv/bin/python", "--version"],
        capture_output=True,
        text=True,
        check=True
    )
    print(f"✓ Python interpreter works: {result.stdout.strip()}")
except Exception as e:
    print(f"✗ Python interpreter failed: {e}")
    exit(1)

# Test that downloader.py can be compiled by the venv Python
try:
    result = subprocess.run(
        ["./venv/bin/python", "-m", "py_compile", "downloader.py"],
        capture_output=True,
        text=True,
        check=True
    )
    print("✓ downloader.py compiles successfully with venv Python")
except Exception as e:
    print(f"✗ Compilation failed: {e}")
    exit(1)

print("\n" + "="*50)
print("✓ ./run.sh should work correctly!")
print("="*50)
print("\nYou can run the application with:")
print("  ./run.sh")
print("\nNote: Requires a display server (X11/Wayland) for the GUI")

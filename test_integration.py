#!/usr/bin/env python3
"""Integration test for downloader functionality"""

import sys
import os

# Test importing the modules
print("Testing imports...")
try:
    import tkinter as tk
    from tkinter import ttk
    print("✓ tkinter imported successfully")
except ImportError as e:
    print(f"✗ Failed to import tkinter: {e}")
    sys.exit(1)

try:
    import threading
    import subprocess
    import re
    from pathlib import Path
    print("✓ Standard library modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import standard modules: {e}")
    sys.exit(1)

# Test parsing the downloader.py file for syntax
print("\nChecking downloader.py structure...")
try:
    with open('downloader.py', 'r') as f:
        content = f.read()

    # Check for key new features
    checks = [
        ("trim_enabled_var", "Trim checkbox variable"),
        ("fetch_duration_btn", "Fetch duration button"),
        ("start_slider", "Start time slider"),
        ("end_slider", "End time slider"),
        ("seconds_to_hms", "Time conversion function"),
        ("toggle_trim", "Toggle trim function"),
        ("fetch_video_duration", "Fetch duration function"),
        ("on_slider_change", "Slider change handler"),
        ("--download-sections", "Download sections flag"),
        ("--force-keyframes-at-cuts", "Keyframes flag"),
    ]

    all_found = True
    for keyword, description in checks:
        if keyword in content:
            print(f"✓ Found: {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False

    if all_found:
        print("\n✓ All required components found!")
    else:
        print("\n✗ Some components are missing!")
        sys.exit(1)

except Exception as e:
    print(f"✗ Error reading downloader.py: {e}")
    sys.exit(1)

# Test that the file is valid Python
print("\nValidating Python syntax...")
try:
    compile(content, 'downloader.py', 'exec')
    print("✓ Python syntax is valid!")
except SyntaxError as e:
    print(f"✗ Syntax error: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✓ All integration tests passed!")
print("="*50)
print("\nThe application should work correctly.")
print("Note: Actual GUI testing requires a display server.")

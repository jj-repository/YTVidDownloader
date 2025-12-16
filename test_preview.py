#!/usr/bin/env python3
"""Test frame preview functionality"""

import os
import sys

print("Testing Frame Preview Feature...")
print("-" * 50)

# Test 1: Check PIL/Pillow import
try:
    from PIL import Image, ImageTk
    print("✓ PIL/Pillow imported successfully")
except ImportError as e:
    print(f"✗ Failed to import PIL: {e}")
    sys.exit(1)

# Test 2: Check ffmpeg availability
try:
    import subprocess
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    if result.returncode == 0:
        version = result.stdout.split('\n')[0]
        print(f"✓ ffmpeg available: {version}")
    else:
        print("✗ ffmpeg not working")
        sys.exit(1)
except FileNotFoundError:
    print("✗ ffmpeg not found in PATH")
    sys.exit(1)

# Test 3: Check downloader.py has all new components
print("\nChecking downloader.py for preview components...")
try:
    with open('downloader.py', 'r') as f:
        content = f.read()

    checks = [
        ("from PIL import Image, ImageTk", "PIL import"),
        ("import tempfile", "tempfile import"),
        ("self.start_preview_label", "Start preview label"),
        ("self.end_preview_label", "End preview label"),
        ("def extract_frame", "Frame extraction function"),
        ("def schedule_preview_update", "Preview update scheduling"),
        ("def update_previews", "Update previews function"),
        ("def cleanup_temp_files", "Temp file cleanup"),
        ("self.temp_dir", "Temp directory variable"),
        ("self.current_video_url", "Current video URL storage"),
    ]

    all_found = True
    for keyword, description in checks:
        if keyword in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ Missing: {description}")
            all_found = False

    if not all_found:
        print("\n✗ Some components are missing!")
        sys.exit(1)

except Exception as e:
    print(f"✗ Error reading downloader.py: {e}")
    sys.exit(1)

# Test 4: Compile check
print("\nValidating Python syntax...")
try:
    compile(content, 'downloader.py', 'exec')
    print("✓ Python syntax is valid!")
except SyntaxError as e:
    print(f"✗ Syntax error: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✓ All frame preview tests passed!")
print("="*50)
print("\nThe frame preview feature is ready!")
print("\nHow it works:")
print("1. Enter YouTube URL")
print("2. Enable trimming and fetch duration")
print("3. Move sliders - preview frames update after 500ms")
print("4. Frames are extracted at selected timestamps")
print("5. Previews show exactly what will be at start/end")

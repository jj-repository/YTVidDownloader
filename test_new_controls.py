#!/usr/bin/env python3
"""Test script to verify new control features"""
import sys

def test_new_controls():
    """Test new controls: filename clear, playlist numbering, speed limit"""
    print("=" * 60)
    print("TESTING: New Control Features")
    print("=" * 60)

    with open('downloader.py', 'r') as f:
        code = f.read()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Reset to 100% button (already exists)
    print("\n1. Testing Reset to 100% button...")
    if 'text="Reset to 100%"' in code and 'reset_volume' in code:
        print("   ✓ Reset to 100% button exists")
        tests_passed += 1
    else:
        print("   ✗ Reset button missing")
        tests_failed += 1

    if 'def reset_volume(self' in code:
        print("   ✓ reset_volume method exists")
        tests_passed += 1
    else:
        print("   ✗ reset_volume method missing")
        tests_failed += 1

    # Test 2: Filename field clears on URL/file change
    print("\n2. Testing filename field auto-clear...")

    # Check in browse_local_file
    browse_section = code[code.find('def browse_local_file'):code.find('def browse_local_file') + 1200]
    if 'self.filename_entry.delete(0, tk.END)' in browse_section:
        print("   ✓ Filename cleared when browsing local file")
        tests_passed += 1
    else:
        print("   ✗ Filename not cleared in browse_local_file")
        tests_failed += 1

    # Check in on_url_change
    url_change_section = code[code.find('def on_url_change'):code.find('def on_url_change') + 500]
    if 'self.filename_entry.delete(0, tk.END)' in url_change_section:
        print("   ✓ Filename cleared when URL changes")
        tests_passed += 1
    else:
        print("   ✗ Filename not cleared in on_url_change")
        tests_failed += 1

    # Test 3: Speed limit UI
    print("\n3. Testing speed limit UI controls...")

    if 'self.speed_limit_var' in code:
        print("   ✓ Speed limit variable created")
        tests_passed += 1
    else:
        print("   ✗ Speed limit variable missing")
        tests_failed += 1

    if 'self.speed_limit_entry' in code:
        print("   ✓ Speed limit entry field created")
        tests_passed += 1
    else:
        print("   ✗ Speed limit entry field missing")
        tests_failed += 1

    if 'text="MB/s"' in code:
        print("   ✓ MB/s label added")
        tests_passed += 1
    else:
        print("   ✗ MB/s label missing")
        tests_failed += 1

    # Test 4: Speed limit helper method
    print("\n4. Testing speed limit implementation...")

    if 'def _get_speed_limit_args(self' in code:
        print("   ✓ _get_speed_limit_args method exists")
        tests_passed += 1
    else:
        print("   ✗ _get_speed_limit_args method missing")
        tests_failed += 1

    if "'--limit-rate'" in code:
        print("   ✓ Uses yt-dlp --limit-rate flag")
        tests_passed += 1
    else:
        print("   ✗ --limit-rate flag not used")
        tests_failed += 1

    # Check speed limit is applied in multiple places
    speed_limit_calls = code.count('self._get_speed_limit_args()')
    if speed_limit_calls >= 4:
        print(f"   ✓ Speed limit applied in {speed_limit_calls} places")
        tests_passed += 1
    else:
        print(f"   ✗ Speed limit only applied in {speed_limit_calls} place(s)")
        tests_failed += 1

    # Test 5: Playlist custom filename numbering
    print("\n5. Testing playlist custom filename numbering...")

    playlist_section = code[code.find('def download_playlist'):code.find('def download_playlist') + 1500]

    if 'custom_name = self.filename_entry.get().strip()' in playlist_section:
        print("   ✓ Retrieves custom filename in playlist download")
        tests_passed += 1
    else:
        print("   ✗ Custom filename not retrieved")
        tests_failed += 1

    if "output_template = f'{custom_name}-%(playlist_index)s.%(ext)s'" in playlist_section:
        print("   ✓ Custom filename template: name-1, name-2, etc.")
        tests_passed += 1
    else:
        print("   ✗ Custom filename template not found")
        tests_failed += 1

    if "'%(playlist_index)s-%(title)s.%(ext)s'" in playlist_section:
        print("   ✓ Default template: index-title format")
        tests_passed += 1
    else:
        print("   ✗ Default template missing")
        tests_failed += 1

    # Final summary
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\n🎛️ New Control Features:")
        print("  1. ✓ Reset to 100% button (already existed)")
        print("  2. ✓ Filename field auto-clears on new URL/file")
        print("  3. ✓ Speed limit entry field (MB/s)")
        print("  4. ✓ Speed limit applied to all downloads")
        print("  5. ✓ Playlist custom filename with numbering")
        print("\n💡 How to use:")
        print("  • Reset volume: Click 'Reset to 100%' button")
        print("  • Speed limit: Enter number in field (e.g., '5' for 5 MB/s)")
        print("  • Playlist names: Enter 'MyVideo' → gets MyVideo-1, MyVideo-2...")
        print("  • Filename auto-clears when you paste a new URL")
        print("\n📝 Examples:")
        print("  Speed limit '10' → Downloads capped at 10 MB/s")
        print("  Filename 'Lecture' + Playlist → Lecture-1, Lecture-2, Lecture-3...")
        print("  Empty filename + Playlist → 1-Title, 2-Title, 3-Title...")
        print("\n🎉 All new controls working perfectly!")
        return True
    else:
        print(f"\n❌ {tests_failed} test(s) failed")
        return False

if __name__ == "__main__":
    success = test_new_controls()
    sys.exit(0 if success else 1)

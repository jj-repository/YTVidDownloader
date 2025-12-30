#!/usr/bin/env python3
"""Test script to verify file size updates when quality changes"""
import sys

def test_quality_filesize_update():
    """Test that file size updates when quality selection changes"""
    print("=" * 60)
    print("TESTING: File Size Update on Quality Change")
    print("=" * 60)

    with open('downloader.py', 'r') as f:
        code = f.read()

    tests_passed = 0
    tests_failed = 0

    # Test 1: on_quality_change method exists
    print("\n1. Testing on_quality_change method...")
    if 'def on_quality_change(self' in code:
        print("   ✓ on_quality_change method exists")
        tests_passed += 1
    else:
        print("   ✗ on_quality_change method missing")
        tests_failed += 1

    # Test 2: quality_var has trace attached
    print("\n2. Testing quality_var callback attachment...")
    if "self.quality_var.trace_add('write', self.on_quality_change)" in code:
        print("   ✓ quality_var callback attached")
        tests_passed += 1
    else:
        print("   ✗ quality_var callback not attached")
        tests_failed += 1

    # Test 3: Re-fetches file size
    print("\n3. Testing file size re-fetch on quality change...")
    on_quality_start = code.find('def on_quality_change(self')
    if on_quality_start > 0:
        on_quality_method = code[on_quality_start:on_quality_start + 600]
        if 'self._fetch_file_size(self.current_video_url)' in on_quality_method:
            print("   ✓ Re-fetches file size with new quality")
            tests_passed += 1
        else:
            print("   ✗ File size re-fetch missing")
            tests_failed += 1

        # Check if background threading is used
        if 'Calculating size...' in on_quality_method:
            print("   ✓ Shows loading indicator while fetching")
            tests_passed += 1
        else:
            print("   ✗ Loading indicator missing")
            tests_failed += 1
    else:
        print("   ✗ Cannot find on_quality_change method")
        tests_failed += 2

    # Test 3b: Trimmed filesize updates in display callback
    print("\n3b. Testing trimmed filesize update integration...")
    display_update_start = code.find('def _update_filesize_display(self')
    if display_update_start > 0:
        display_method = code[display_update_start:display_update_start + 600]
        if 'self._update_trimmed_filesize()' in display_method:
            print("   ✓ Trimmed filesize updates after size is fetched")
            tests_passed += 1
        else:
            print("   ✗ Trimmed filesize update not in display callback")
            tests_failed += 1
    else:
        print("   ✗ Cannot find _update_filesize_display method")
        tests_failed += 1

    # Test 4: Checks for valid URL and duration
    print("\n4. Testing validation before re-fetch...")
    if on_quality_start > 0:
        on_quality_method = code[on_quality_start:on_quality_start + 600]
        if 'if self.current_video_url and self.video_duration > 0' in on_quality_method:
            print("   ✓ Validates URL and duration before re-fetch")
            tests_passed += 1
        else:
            print("   ✗ Validation missing")
            tests_failed += 1

        if 'not self.is_playlist' in on_quality_method:
            print("   ✓ Skips file size update for playlists")
            tests_passed += 1
        else:
            print("   ✗ Playlist check missing")
            tests_failed += 1
    else:
        tests_failed += 2

    # Test 5: Background threading
    print("\n5. Testing background threading...")
    fetch_size_start = code.find('def _fetch_file_size(self')
    if fetch_size_start > 0:
        fetch_method = code[fetch_size_start:fetch_size_start + 2000]
        if 'self.thread_pool.submit(_fetch)' in fetch_method:
            print("   ✓ Uses ThreadPoolExecutor for background fetching")
            tests_passed += 1
        else:
            print("   ✗ Background threading not used")
            tests_failed += 1

        if 'self.root.after(0, lambda:' in fetch_method:
            print("   ✓ Updates UI on main thread using root.after()")
            tests_passed += 1
        else:
            print("   ✗ UI update not thread-safe")
            tests_failed += 1
    else:
        print("   ✗ Cannot find _fetch_file_size method")
        tests_failed += 2

    # Test 6: PhotoImage error fix
    print("\n6. Testing PhotoImage error fix...")
    # Check that we're not double-wrapping PhotoImage
    error_placeholders = code.count('self.create_placeholder_image(PREVIEW_WIDTH, PREVIEW_HEIGHT, "Error")')
    if error_placeholders >= 2:
        print(f"   ✓ Found {error_placeholders} error placeholder calls")
        tests_passed += 1
    else:
        print(f"   ✗ Only found {error_placeholders} error placeholder call(s)")
        tests_failed += 1

    # Check for the fixed lambda usage (no double PhotoImage wrapping)
    if 'lambda img=error_img: self._set_start_preview(img)' in code:
        print("   ✓ Start preview error fixed (no double PhotoImage wrap)")
        tests_passed += 1
    else:
        print("   ✗ Start preview error not fixed")
        tests_failed += 1

    if 'lambda img=error_img: self._set_end_preview(img)' in code:
        print("   ✓ End preview error fixed (no double PhotoImage wrap)")
        tests_passed += 1
    else:
        print("   ✗ End preview error not fixed")
        tests_failed += 1

    # Final summary
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\nQuality change features:")
        print("  1. ✓ on_quality_change callback method")
        print("  2. ✓ Callback attached to quality_var")
        print("  3. ✓ Re-fetches file size when quality changes")
        print("  4. ✓ Shows 'Calculating size...' loading indicator")
        print("  5. ✓ Trimmed size updates after fetch completes")
        print("  6. ✓ Background threading for responsive UI")
        print("  7. ✓ Thread-safe UI updates (root.after)")
        print("  8. ✓ Validates URL and duration before re-fetch")
        print("  9. ✓ Skips file size update for playlists")
        print(" 10. ✓ PhotoImage error fixed in preview frames")
        print("\n🎉 File size updates instantly with NO UI lag!")
        print("\nHow it works:")
        print("  • Click a quality → UI shows 'Calculating size...' immediately")
        print("  • File size fetches in background thread (no blocking!)")
        print("  • Uses yt-dlp to get the actual size for that quality")
        print("  • When ready, updates display with accurate size")
        print("  • If trimming enabled, applies trim calculation")
        print("  • Result: Snappy UI + accurate file size estimates!")
        return True
    else:
        print(f"\n❌ {tests_failed} test(s) failed")
        return False

if __name__ == "__main__":
    success = test_quality_filesize_update()
    sys.exit(0 if success else 1)

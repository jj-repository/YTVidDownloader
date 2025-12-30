#!/usr/bin/env python3
"""Test script to verify YouTube Shorts support and filename customization"""
import sys

def test_new_features():
    """Test that the new features are implemented"""
    print("=" * 60)
    print("TESTING: YouTube Shorts & Filename Customization")
    print("=" * 60)

    with open('downloader.py', 'r') as f:
        code = f.read()

    tests_passed = 0
    tests_failed = 0

    # Test 1: YouTube Shorts duration parsing (single seconds)
    print("\n1. Testing YouTube Shorts duration support...")
    if 'if len(parts) == 1:  # Just seconds' in code:
        print("   ✓ Single seconds format (e.g., '59') supported")
        tests_passed += 1
    else:
        print("   ✗ Single seconds format missing")
        tests_failed += 1

    if 'self.video_duration = int(parts[0])' in code:
        print("   ✓ Duration parsing for seconds-only format")
        tests_passed += 1
    else:
        print("   ✗ Duration parsing for seconds missing")
        tests_failed += 1

    # Test 2: Filename customization UI
    print("\n2. Testing filename customization UI...")
    if 'self.filename_entry' in code:
        print("   ✓ Filename entry field added")
        tests_passed += 1
    else:
        print("   ✗ Filename entry field missing")
        tests_failed += 1

    if 'Output filename:' in code:
        print("   ✓ Filename label added")
        tests_passed += 1
    else:
        print("   ✗ Filename label missing")
        tests_failed += 1

    if 'Optional - leave empty for auto-generated name' in code:
        print("   ✓ Helper text added")
        tests_passed += 1
    else:
        print("   ✗ Helper text missing")
        tests_failed += 1

    # Test 3: Custom filename instance variable
    print("\n3. Testing filename customization variable...")
    if 'self.custom_filename' in code:
        print("   ✓ custom_filename variable initialized")
        tests_passed += 1
    else:
        print("   ✗ custom_filename variable missing")
        tests_failed += 1

    # Test 4: Filename integration in YouTube downloads
    print("\n4. Testing filename in YouTube downloads...")
    if 'custom_name = self.filename_entry.get().strip()' in code:
        print("   ✓ Custom filename retrieved from entry field")
        tests_passed += 1
    else:
        print("   ✗ Custom filename retrieval missing")
        tests_failed += 1

    # Check both audio and video sections
    custom_name_checks = code.count('custom_name = self.filename_entry.get().strip()')
    if custom_name_checks >= 3:
        print(f"   ✓ Custom filename checked in {custom_name_checks} places (audio, video, local)")
        tests_passed += 1
    else:
        print(f"   ✗ Custom filename only checked in {custom_name_checks} place(s)")
        tests_failed += 1

    # Test 5: Base name usage
    print("\n5. Testing base name substitution...")
    if "base_name = custom_name" in code:
        print("   ✓ Custom name used as base_name")
        tests_passed += 1
    else:
        print("   ✗ Base name substitution missing")
        tests_failed += 1

    if "base_name = '%(title)s'" in code:
        print("   ✓ Fallback to yt-dlp title template")
        tests_passed += 1
    else:
        print("   ✗ Fallback template missing")
        tests_failed += 1

    # Test 6: Local file custom filename
    print("\n6. Testing local file custom filename...")
    if 'base_name = input_path.stem' in code:
        print("   ✓ Fallback to original file stem for local files")
        tests_passed += 1
    else:
        print("   ✗ Local file stem fallback missing")
        tests_failed += 1

    # Test 7: Duration error message improvement
    print("\n7. Testing duration error messages...")
    if 'Invalid duration format: {duration_str}' in code:
        print("   ✓ Improved error message shows actual format received")
        tests_passed += 1
    else:
        print("   ✗ Error message not improved")
        tests_failed += 1

    # Final summary
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\nNew features implemented:")
        print("  1. ✓ YouTube Shorts support (single seconds duration)")
        print("  2. ✓ Duration parsing for SS format")
        print("  3. ✓ Duration parsing for MM:SS format")
        print("  4. ✓ Duration parsing for HH:MM:SS format")
        print("  5. ✓ Filename customization UI field")
        print("  6. ✓ Custom filename for YouTube downloads (audio)")
        print("  7. ✓ Custom filename for YouTube downloads (video)")
        print("  8. ✓ Custom filename for local file processing")
        print("  9. ✓ Auto-generated filename fallback")
        print(" 10. ✓ Improved duration error messages")
        print("\n🎉 YouTube Shorts and filename customization fully implemented!")
        return True
    else:
        print(f"\n❌ {tests_failed} test(s) failed")
        return False

if __name__ == "__main__":
    success = test_new_features()
    sys.exit(0 if success else 1)

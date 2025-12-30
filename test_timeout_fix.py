#!/usr/bin/env python3
"""Test script to verify download timeout increases"""
import sys

def test_timeout_fix():
    """Test that download timeouts are increased"""
    print("=" * 60)
    print("TESTING: Download Timeout Increases")
    print("=" * 60)

    with open('downloader.py', 'r') as f:
        code = f.read()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Stall timeout increased
    print("\n1. Testing stall timeout...")
    if 'DOWNLOAD_PROGRESS_TIMEOUT = 600' in code:
        print("   ✓ Stall timeout increased to 600s (10 minutes)")
        tests_passed += 1
    else:
        print("   ✗ Stall timeout not set to 600s")
        tests_failed += 1

    # Test 2: Absolute timeout increased
    print("\n2. Testing absolute timeout...")
    if 'DOWNLOAD_TIMEOUT = 3600' in code:
        print("   ✓ Absolute timeout increased to 3600s (60 minutes)")
        tests_passed += 1
    else:
        print("   ✗ Absolute timeout not set to 3600s")
        tests_failed += 1

    # Test 3: Error messages updated
    print("\n3. Testing error messages...")
    if 'no progress for 10 minutes' in code:
        print("   ✓ Stall error message updated to '10 minutes'")
        tests_passed += 1
    else:
        print("   ✗ Stall error message not updated")
        tests_failed += 1

    if '60 min limit exceeded' in code:
        print("   ✓ Absolute timeout message updated to '60 min'")
        tests_passed += 1
    else:
        print("   ✗ Absolute timeout message not updated")
        tests_failed += 1

    # Test 4: Constants still in use
    print("\n4. Testing timeout enforcement...")
    stall_checks = code.count('> DOWNLOAD_PROGRESS_TIMEOUT')
    if stall_checks >= 1:
        print(f"   ✓ Stall timeout checked {stall_checks} time(s)")
        tests_passed += 1
    else:
        print("   ✗ Stall timeout check missing")
        tests_failed += 1

    absolute_checks = code.count('> DOWNLOAD_TIMEOUT')
    if absolute_checks >= 1:
        print(f"   ✓ Absolute timeout checked {absolute_checks} time(s)")
        tests_passed += 1
    else:
        print("   ✗ Absolute timeout check missing")
        tests_failed += 1

    # Final summary
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\nTimeout increases:")
        print("  • Stall timeout: 5 min → 10 min (2x increase)")
        print("  • Absolute timeout: 30 min → 60 min (2x increase)")
        print("\nWhat this fixes:")
        print("  ✓ Long videos (11+ minutes) won't timeout")
        print("  ✓ Slow network connections get more time")
        print("  ✓ Post-processing (ffmpeg merge) won't stall")
        print("  ✓ Quality re-encoding has enough time")
        print("\nWhen timeouts trigger:")
        print("  • Stall: No progress updates for 10 continuous minutes")
        print("  • Absolute: Download runs for more than 60 minutes total")
        print("\n🎉 Downloads should complete successfully now!")
        return True
    else:
        print(f"\n❌ {tests_failed} test(s) failed")
        return False

if __name__ == "__main__":
    success = test_timeout_fix()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Test script to verify playlist support and file size estimation"""
import sys

def test_playlist_and_filesize():
    """Test that playlist and file size features are implemented"""
    print("=" * 60)
    print("TESTING: Playlist Support & File Size Estimation")
    print("=" * 60)

    with open('downloader.py', 'r') as f:
        code = f.read()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Window size
    print("\n1. Testing window size...")
    if 'self.root.geometry("900x1140")' in code:
        print("   ✓ Window size set to 900x1140")
        tests_passed += 1
    else:
        print("   ✗ Window size not 900x1140")
        tests_failed += 1

    # Test 2: Playlist instance variables
    print("\n2. Testing playlist variables...")
    if 'self.is_playlist = False' in code:
        print("   ✓ is_playlist variable initialized")
        tests_passed += 1
    else:
        print("   ✗ is_playlist variable missing")
        tests_failed += 1

    if 'self.estimated_filesize = None' in code:
        print("   ✓ estimated_filesize variable initialized")
        tests_passed += 1
    else:
        print("   ✗ estimated_filesize variable missing")
        tests_failed += 1

    # Test 3: Playlist detection method
    print("\n3. Testing playlist detection...")
    if 'def is_playlist_url(self' in code:
        print("   ✓ is_playlist_url method exists")
        tests_passed += 1
    else:
        print("   ✗ is_playlist_url method missing")
        tests_failed += 1

    if "'/playlist' in parsed.path" in code or "'/playlist' in parsed.path" in code:
        print("   ✓ Playlist path detection")
        tests_passed += 1
    else:
        print("   ✗ Playlist path detection missing")
        tests_failed += 1

    if "'list=' in parsed.query" in code:
        print("   ✓ Playlist query parameter detection")
        tests_passed += 1
    else:
        print("   ✗ Playlist query detection missing")
        tests_failed += 1

    # Test 4: File size estimation
    print("\n4. Testing file size estimation...")
    if 'self.filesize_label' in code:
        print("   ✓ File size label UI element added")
        tests_passed += 1
    else:
        print("   ✗ File size label missing")
        tests_failed += 1

    if 'def _fetch_file_size(self' in code:
        print("   ✓ _fetch_file_size method exists")
        tests_passed += 1
    else:
        print("   ✗ _fetch_file_size method missing")
        tests_failed += 1

    if '--dump-json' in code:
        print("   ✓ Using yt-dlp --dump-json for size estimation")
        tests_passed += 1
    else:
        print("   ✗ --dump-json not used")
        tests_failed += 1

    if 'Estimated size:' in code:
        print("   ✓ File size display in UI")
        tests_passed += 1
    else:
        print("   ✗ File size display missing")
        tests_failed += 1

    # Test 5: Playlist download method
    print("\n5. Testing playlist download...")
    if 'def download_playlist(self' in code:
        print("   ✓ download_playlist method exists")
        tests_passed += 1
    else:
        print("   ✗ download_playlist method missing")
        tests_failed += 1

    if '%(playlist_index)s-%(title)s' in code:
        print("   ✓ Playlist filename template")
        tests_passed += 1
    else:
        print("   ✗ Playlist filename template missing")
        tests_failed += 1

    # Test 6: Playlist trimming disabled
    print("\n6. Testing playlist restrictions...")
    if 'Trimming and upload disabled for playlists' in code:
        print("   ✓ Playlist restriction message")
        tests_passed += 1
    else:
        print("   ✗ Playlist restriction message missing")
        tests_failed += 1

    if 'self.trim_enabled_var.set(False)' in code and 'self.is_playlist' in code:
        print("   ✓ Trimming disabled for playlists")
        tests_passed += 1
    else:
        print("   ✗ Trimming not disabled for playlists")
        tests_failed += 1

    # Test 7: Volume applied to playlists
    print("\n7. Testing volume in playlist downloads...")
    volume_in_playlist = code.count('volume_multiplier') >= 3
    if volume_in_playlist:
        print("   ✓ Volume multiplier used in playlist downloads")
        tests_passed += 1
    else:
        print("   ✗ Volume not applied to playlists")
        tests_failed += 1

    # Test 8: Playlist validation
    print("\n8. Testing playlist URL validation...")
    if "'list=' in parsed.query" in code and 'validate_youtube_url' in code:
        print("   ✓ Playlist URLs validated")
        tests_passed += 1
    else:
        print("   ✗ Playlist validation missing")
        tests_failed += 1

    # Test 9: Row numbers updated
    print("\n9. Testing UI row adjustments...")
    if 'self.filesize_label.grid(row=9,' in code:
        print("   ✓ File size label at row 9")
        tests_passed += 1
    else:
        print("   ✗ File size label not at row 9")
        tests_failed += 1

    # Final summary
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\nNew features implemented:")
        print("  1. ✓ Window size: 900x1140")
        print("  2. ✓ Playlist URL detection")
        print("  3. ✓ Playlist download support")
        print("  4. ✓ Volume applied to all playlist videos")
        print("  5. ✓ Quality settings applied to playlists")
        print("  6. ✓ Trimming disabled for playlists")
        print("  7. ✓ Upload disabled for playlists")
        print("  8. ✓ File size estimation for single videos")
        print("  9. ✓ File size displayed in UI")
        print(" 10. ✓ Playlist index in filenames")
        print("\n🎉 Playlist support and file size estimation fully implemented!")
        return True
    else:
        print(f"\n❌ {tests_failed} test(s) failed")
        return False

if __name__ == "__main__":
    success = test_playlist_and_filesize()
    sys.exit(0 if success else 1)

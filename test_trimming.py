#!/usr/bin/env python3
"""Test script for trimming functionality"""

# Test time conversion
def seconds_to_hms(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# Test cases
test_cases = [
    (0, "00:00:00"),
    (45, "00:00:45"),
    (90, "00:01:30"),
    (3665, "01:01:05"),
    (7200, "02:00:00"),
]

print("Testing time conversion:")
all_passed = True
for seconds, expected in test_cases:
    result = seconds_to_hms(seconds)
    passed = result == expected
    all_passed = all_passed and passed
    status = "✓" if passed else "✗"
    print(f"{status} {seconds}s -> {result} (expected: {expected})")

print()

# Test command building simulation
def build_trim_command(start_time, end_time, is_audio=False):
    """Simulate building the trim command"""
    start_hms = seconds_to_hms(start_time)
    end_hms = seconds_to_hms(end_time)

    if is_audio:
        return f"Audio trim: -ss {start_time} -to {end_time}"
    else:
        return f"Video trim: --download-sections *{start_hms}-{end_hms} --force-keyframes-at-cuts"

print("Testing command building:")
print(build_trim_command(15, 90, is_audio=False))
print(build_trim_command(30, 120, is_audio=True))
print()

if all_passed:
    print("✓ All tests passed!")
else:
    print("✗ Some tests failed!")

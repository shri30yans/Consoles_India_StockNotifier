#!/usr/bin/env python3
"""Test product name normalization to verify the fix works."""

from commerce_platform.platform.text_normalization import normalize_product_name

# Test cases: (input, expected_output)
test_cases = [
    ("Sony PS5® Console Slim", "Sony PS5® Console Slim"),
    # UTF-8 for U+1F3AE (🎮) misread as Windows-1252 → 4 mojibake characters before title text
    (
        b"\xf0\x9f\x8e\xae".decode("cp1252") + " Sony PS5® Console Slim - EA SPORTS FC 26 Bundle",
        "\U0001f3ae Sony PS5® Console Slim - EA SPORTS FC 26 Bundle",
    ),
    ("Sony PS5Â® Console Slim", "Sony PS5® Console Slim"),
    ("Sony PS5Â Console Slim", "Sony PS5 Console Slim"),
    ("PlayStation5", "PlayStation 5"),
    ("PlayStation 5", "PlayStation 5"),
    ("PS  5", "PS5"),
    ("Xbox Series X", "Xbox Series X"),
    ("Xbox Series  S", "Xbox Series S"),
    ("Product–with–en-dashes", "Product-with-en-dashes"),
    ("Product—with—em-dashes", "Product-with-em-dashes"),
    ("Extra   spaces   here", "Extra spaces here"),
    ("  Leading and trailing  ", "Leading and trailing"),
]

print("Testing product name normalization:\n")
passed = 0
failed = 0

for input_name, expected in test_cases:
    result = normalize_product_name(input_name)
    status = "PASS" if result == expected else "FAIL"
    if result == expected:
        passed += 1
    else:
        failed += 1
    print(f"{status}")
    print(f"  Input:    {ascii(input_name)}")
    print(f"  Expected: {ascii(expected)}")
    print(f"  Got:      {ascii(result)}")
    if result != expected:
        print(f"  Diff: Got {ascii(result)} but expected {ascii(expected)}")
    print()

print(f"\nSummary: {passed} passed, {failed} failed")
exit(0 if failed == 0 else 1)

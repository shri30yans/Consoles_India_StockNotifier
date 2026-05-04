"""Text normalization utilities for product names and descriptions."""

import re
import unicodedata


def _repair_utf8_misread_as_cp1252(s: str) -> str:
    """
    Repair mojibake where UTF-8 bytes were decoded as Windows-1252 (common for emoji and symbols).

    Works on segments: only replaces a substring when re-encoding as cp1252 and decoding as UTF-8
    yields different text (e.g. four chars 'ðŸŽ®' → one emoji). Applying this to the whole string at
    once would break valid text mixed with U+00AE, because ® encodes to a single byte that is not
    valid UTF-8 alone.
    """
    i = 0
    out: list[str] = []
    while i < len(s):
        replaced = False
        for n in range(min(8, len(s) - i), 0, -1):
            chunk = s[i : i + n]
            try:
                raw = chunk.encode("cp1252")
                fixed = raw.decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            if fixed != chunk:
                out.append(fixed)
                i += n
                replaced = True
                break
        if not replaced:
            out.append(s[i])
            i += 1
    return "".join(out)


def normalize_product_name(name: str) -> str:
    """
    Normalize product name: fix encoding issues, standardize spacing, clean whitespace.

    Handles:
    - UTF-8 read as cp1252 (e.g. leading emoji showing as 'ðŸŽ®')
    - Â® → ® (broken encoding of registered trademark)
    - Â → (remove stray broken character)
    - en dash variations (normalize to hyphens/spaces)
    - PlayStation5 → PlayStation 5
    - Extra whitespace and control characters
    """
    if not name:
        return name

    name = _repair_utf8_misread_as_cp1252(name)

    # Fix broken UTF-8 sequences (Â® and stray Â characters)
    name = name.replace('Â®', '®')
    name = name.replace('Â', '')

    # Normalize various dash/hyphen variations to standard hyphen
    name = name.replace('–', '-')  # en-dash to hyphen
    name = name.replace('—', '-')  # em-dash to hyphen

    # Normalize spacing around common terms
    name = re.sub(r'PlayStation\s*5', 'PlayStation 5', name, flags=re.IGNORECASE)
    name = re.sub(r'PS\s*5', 'PS5', name, flags=re.IGNORECASE)
    name = re.sub(r'Xbox\s*Series\s*X', 'Xbox Series X', name, flags=re.IGNORECASE)
    name = re.sub(r'Xbox\s*Series\s*S', 'Xbox Series S', name, flags=re.IGNORECASE)

    # Normalize unicode (e.g., decompose accented characters to base + combining)
    name = unicodedata.normalize('NFKC', name)

    # Remove control characters and other problematic unicode
    name = ''.join(c for c in name if unicodedata.category(c)[0] != 'C')

    # Clean up excess whitespace: multiple spaces, tabs, newlines → single space
    name = re.sub(r'\s+', ' ', name)

    # Strip leading/trailing whitespace
    name = name.strip()

    return name

"""Text normalization utilities for product names and descriptions."""

import unicodedata
import re


def normalize_product_name(name: str) -> str:
    """
    Normalize product name: fix encoding issues, standardize spacing, clean whitespace.

    Handles:
    - Â® → ® (broken encoding of registered trademark)
    - Â → (remove stray broken character)
    - en dash variations (normalize to hyphens/spaces)
    - PlayStation5 → PlayStation 5
    - Extra whitespace and control characters
    """
    if not name:
        return name

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

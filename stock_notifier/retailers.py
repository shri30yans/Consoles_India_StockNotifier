"""
Retailers that have a first-class HTML parser implementation.

Jobs must only reference these `website_key` values; configuration and
`jobs.yaml` are validated at load time.
"""

from typing import Final

PARSER_SUPPORTED_WEBSITE_KEYS: Final[frozenset[str]] = frozenset({"amazon", "flipkart"})

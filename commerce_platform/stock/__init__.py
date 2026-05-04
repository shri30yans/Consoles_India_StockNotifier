"""Stock notifier: YAML-driven retail stock monitoring.

Listing-centric **availability** alerts only: poll product pages, detect
in-stock transitions vs persisted state, notify. This package does **not**
implement deal scoring or 90-day price gates (see ``commerce_platform.deals``).
"""

__version__ = "2.0.0"

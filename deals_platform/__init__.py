"""DealsPlatform — AI-curated deal aggregator on top of stock_notifier primitives.

Layered architecture (designed from first principles):

    sources    -> ingest raw signals from retailers & aggregators
    domain     -> pure types & business rules (no I/O)
    pipeline   -> normalize -> score -> curate -> publish
    storage    -> persistence ports + Postgres adapters
    llm        -> pluggable LLM provider (Gemini default)
    notify     -> per-platform notifier adapters
    runtime    -> wires everything together

Run with:
    python -m deals_platform
"""

__version__ = "0.1.0"

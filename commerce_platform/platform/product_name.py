"""Catalog product names: one coercion path for YAML, API strings, and Postgres."""

from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator, TypeAdapter

from commerce_platform.platform.text_normalization import normalize_product_name

# Shared by ProductConfig.name and plain-str persistence (repo); BeforeValidator is the single hook.
CanonicalProductName = Annotated[str, BeforeValidator(normalize_product_name)]

_adapter = TypeAdapter(CanonicalProductName)


def coerce_product_name(value: str) -> str:
    """Same transformation as validating ``ProductConfig.name`` — use for raw strings that skip the model."""
    return _adapter.validate_python(value)

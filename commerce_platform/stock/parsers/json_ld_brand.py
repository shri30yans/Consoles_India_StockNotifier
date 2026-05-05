"""Extract schema.org Product brand from parsed JSON-LD structures."""

from __future__ import annotations


def brand_from_json_ld_object(obj: object) -> str | None:
    """Walk JSON-LD (dict/list tree) for the first ``Product`` brand name."""
    if isinstance(obj, dict):
        types = obj.get("@type")
        type_ok = types == "Product" or (
            isinstance(types, list) and any(str(t) == "Product" for t in types)
        )
        if type_ok:
            b = obj.get("brand")
            if isinstance(b, dict):
                name = b.get("name")
                if isinstance(name, str) and name.strip():
                    return name.strip()
            elif isinstance(b, str) and b.strip():
                return b.strip()
        for v in obj.values():
            got = brand_from_json_ld_object(v)
            if got:
                return got
    elif isinstance(obj, list):
        for item in obj:
            got = brand_from_json_ld_object(item)
            if got:
                return got
    return None

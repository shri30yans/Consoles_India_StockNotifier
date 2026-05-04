"""Small validation helpers for API inputs."""


def slug_ok(s: str) -> bool:
    return bool(s) and s.replace("_", "").replace("-", "").isalnum()

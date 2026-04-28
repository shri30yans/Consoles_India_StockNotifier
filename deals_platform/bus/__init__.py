"""Event bus abstraction.

`InMemoryBus` is the default. Swap to a Redis-Streams or NATS implementation
later by writing another class with the same interface.
"""

from deals_platform.bus.bus import EventBus, InMemoryBus

__all__ = ["EventBus", "InMemoryBus"]

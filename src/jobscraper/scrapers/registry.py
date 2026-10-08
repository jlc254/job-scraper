"""Adapter registry keyed by source id (D14). The runner is never edited to add a source."""

from __future__ import annotations

from collections.abc import Callable

from jobscraper.scrapers.base import Adapter

_REGISTRY: dict[str, type[Adapter]] = {}


def register(cls: type[Adapter]) -> type[Adapter]:
    """Class decorator that registers an adapter under its `id`."""
    if cls.id in _REGISTRY:
        raise ValueError(f"duplicate adapter id: {cls.id}")
    _REGISTRY[cls.id] = cls
    return cls


def get_adapter_class(source_id: str) -> type[Adapter] | None:
    return _REGISTRY.get(source_id)


def registered_ids() -> list[str]:
    return sorted(_REGISTRY)


def clear_registry_for_tests() -> Callable[[], None]:
    """Test helper: empty the registry and return a function that restores it."""
    snapshot = dict(_REGISTRY)
    _REGISTRY.clear()

    def restore() -> None:
        _REGISTRY.clear()
        _REGISTRY.update(snapshot)

    return restore

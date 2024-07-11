from __future__ import annotations
from typing import TypeVar, Callable

K = TypeVar("K")
V = TypeVar("V")


# why does defaultdict not do this? are they stupid?
# https://stackoverflow.com/a/73975965
class KeyDefaultDict(dict[K, V]):
    def __init__(self, default_factory: Callable[[K], V], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_factory = default_factory

    def __missing__(self, key: K) -> V:
        self[key] = self._default_factory(key)
        return self[key]

from __future__ import annotations
from os.path import isfile, abspath

from common import load, Log


class Source:
    _nxt_raw_id: int = 0
    _pool: dict[str, Source] = {}

    def __init__(self, content: str) -> None:
        self._content: str = content

    @classmethod
    def content_of(cls, handle: str) -> str:
        return cls._pool[handle]._content

    @classmethod
    def raw(cls, content: str) -> str:
        handle: str = f"raw-{cls._nxt_raw_id}"
        cls._nxt_raw_id += 1
        cls._pool[handle] = Source(content)
        return handle

    @classmethod
    def load(cls, file: str) -> str:
        if not isfile(file):
            # todo: error
            raise ValueError(f"invalid source file: '{file}'")

        handle: str = abspath(file)
        if handle not in cls._pool:
            Log.t(f"Loading '{file}'", tag="Source")
            cls._pool[handle] = Source(load(file))
        return handle

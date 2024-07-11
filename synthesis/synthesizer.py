from __future__ import annotations
from typing import Any, DefaultDict, Callable
from collections import defaultdict
from itertools import pairwise
from collections import deque


from common import limit, Log, it
from langs import Lang, A, B, B2, Expr
from syntax.ast import ASTNode

from .source import Source


class Synthesize:
    _graph: DefaultDict[str, dict[str, Callable[..., Any]]] = defaultdict(lambda: {})

    def __call__(
        self,
        target: str,
        source: str,
        source_lang: str | None = None,
        waypoints: list[str] = [],
    ) -> Any:
        if source_lang is None:
            source_lang = Synthesize._guess_lang(source)
            Log.d(
                f"guessed source language for '{limit(source, rjust=True)}' to be {source_lang}"
            )

        path: list[str] = [source_lang]
        waypoints = waypoints + [target]
        last_target: str = source_lang
        for next_target in waypoints:
            path += self._find_path(last_target, next_target)
            last_target = next_target
        Log.d(
            f"synthesis path of '{limit(source, rjust=True)}' from {source_lang} to {target}: {' -> '.join(path)}"
        )

        artifact = Source.content_of(source)
        for s, t in pairwise(path):
            artifact = self._transform(s, t)(artifact)
        return artifact

    @classmethod
    def synthesizable(cls, s: str, t: str) -> bool:
        try:
            cls._find_path(s, t)
        except ValueError:
            return False
        return True

    # bfs, returns path excluding source
    @classmethod
    def _find_path(cls, s: str, t: str) -> list[str]:
        if s == t:
            return []
        prev: dict[str, str] = {}
        bfs: deque[str] = deque([s])
        while bfs:
            u: str = bfs.popleft()
            if u == t:
                break
            for v in cls._graph[u]:
                if v in prev:
                    continue
                prev[v] = u
                bfs.append(v)

        if t not in prev:
            # todo: error
            raise ValueError(f"cannot synthesize {t} from {s}")

        # reconstruct path
        path: list[str] = [t]
        while prev[path[-1]] != s:
            path.append(prev[path[-1]])

        return list(reversed(path))

    @classmethod
    def _transform(cls, s: str, t: str) -> Callable[..., Any]:
        return cls._graph[s][t]

    @staticmethod
    def _guess_lang(source_handle: str) -> str:
        source: str = Source.content_of(source_handle)
        for lang, parse in {
            "a": A.parse,
            "b": B.parse,
            "b2": B2.parse,
            "expr": Expr.parse,
        }.items():
            try:
                parse(source)
            except:
                continue
            return lang
        # todo: error
        raise ValueError(f"invalid source: {limit(source)}")

    @classmethod
    def add_transform(cls, s: str, t: str, transform: Callable[..., Any]) -> None:
        cls._graph[s][t] = transform

    @classmethod
    def add_lang(cls, lang: type[Lang]):
        Log.d(f"adding {lang.name} to synthesizer")
        cls.add_transform(f"{lang.name}", f"{lang.name}-raw-ast", lang.parse)
        cls.add_transform(f"{lang.name}-raw-ast", f"{lang.name}-ast", lang.shake)
        cls.add_transform(f"{lang.name}-ast", f"{lang.name}-formatted", lang.print)
        cls.add_transform(f"{lang.name}-formatted", f"{lang.name}", it)


Synthesize.add_lang(A)
Synthesize.add_lang(B)
Synthesize.add_lang(B2)
Synthesize.add_lang(Expr)

Synthesize.add_transform("a-ast", "mp0", A.assemble)
Synthesize.add_transform("b-ast", "a", B.compile)
Synthesize.add_transform("b", "b2", it)
Synthesize.add_transform("b2-ast", "b", B2.translate)

synthesize = Synthesize()

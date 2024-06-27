from __future__ import annotations
import re
from typing import Callable, Any, Iterator


class Vocabulary:

    class Definition:
        def __init__(
            self,
            matcher: re.Pattern,
            literal_generator: Callable[[str], Any] = lambda _: None,
        ):
            self._matcher = matcher
            self._literal_generator = literal_generator

        def __repr__(self) -> str:
            return f"Definition({self._matcher})"

        @property
        def matcher(self) -> re.Pattern:
            return self._matcher

        @property
        def literal_generator(self) -> Callable[[str], Any]:
            return self._literal_generator

        # todo: no regex shenanigans with exact matches (e.g. \*)
        @classmethod
        def make(
            cls,
            pattern: str,
            literal_generator: Callable[[str], Any] = lambda _: None,
        ) -> Vocabulary.Definition:
            return cls(
                re.compile(f"\\A{pattern}"),
                literal_generator,
            )

        builtin: dict[str, Vocabulary.Definition]

    Definition.builtin = {
        "identifier": Definition.make(
            r"[A-Za-z_$][A-Za-z0-9_$]*",
            str,
        ),
        "decimal_integer": Definition.make(
            r"-?(0|[1-9][0-9]*)",
            int,
        ),
        "escaped_string": Definition.make(
            r'"(\.|[^\"])*"',
            # todo: delete
            # lambda lexeme: bytes(lexeme[1:-1], "utf-8").decode("unicode_escape"),
            lambda lexeme: lexeme[1:-1],
        ),
    }

    DEFAULT_IGNORE = ["[ \t\n]+"]

    def __init__(
        self,
        dictionary: dict[str, Vocabulary.Definition],
        ignore: list[str] = DEFAULT_IGNORE,
    ):
        self._dictionary: dict[str, Vocabulary.Definition] = dictionary
        self._dictionary.update(Vocabulary.Definition.builtin)
        # todo: ew
        self._ignore: list[re.Pattern] = list(
            map(lambda pattern: re.compile(f"\\A{pattern}"), ignore)
        )

    def __repr__(self) -> str:
        return f"Vocabulary(dictionary={self._dictionary}, ignore={self._ignore})"

    def __iter__(self) -> Iterator[str]:
        return iter(self._dictionary)

    def __getitem__(self, key: str) -> Definition:
        if key in self._dictionary:
            return self._dictionary[key]

        else:
            # todo: add 'do you mean...'?
            raise KeyError(f"'{key}' does not exist in dictionary")

    @property
    def ignore(self) -> list[re.Pattern]:
        return self._ignore

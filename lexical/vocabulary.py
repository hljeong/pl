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

        @classmethod
        def make_exact(
            cls,
            pattern: str,
            literal_generator: Callable[[str], Any] = lambda _: None,
        ) -> Vocabulary.Definition:
            escapes: list[str] = [
                "\\",
                ".",
                "+",
                "*",
                "?",
                "^",
                "$",
                "(",
                ")",
                "[",
                "]",
                "{",
                "}",
                "|",
            ]
            for escape in escapes:
                pattern = pattern.replace(escape, f"\\{escape}")
            return cls(
                re.compile(f"\\A{pattern}"),
                literal_generator,
            )

        @classmethod
        def make_regex(
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
        "identifier": Definition.make_regex(
            r"[A-Za-z_$][A-Za-z0-9_$]*",
            str,
        ),
        "decimal_integer": Definition.make_regex(
            r"-?(0|[1-9][0-9]*)",
            int,
        ),
        "escaped_string": Definition.make_regex(
            r'"(\.|[^\"])*"',
            lambda lexeme: lexeme[1:-1],
        ),
        "regex": Definition.make_regex(
            r'r"(\.|[^\"])*"',
            lambda lexeme: lexeme[2:-1],
        ),
        "e": Definition.make_exact(""),
        "$": Definition.make_regex(r"\Z"),
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

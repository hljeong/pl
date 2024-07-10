from __future__ import annotations
from typing import Any
from copy import copy
import re

from common import Cursor, CursorRange, Log

from .vocabulary import Vocabulary
from .token import Token


class Lex:
    class Position:
        def __init__(self):
            self._start: int = 0
            self._start_cursor: Cursor = Cursor()
            self._current: int = 0
            self._current_cursor: Cursor = Cursor()

        def advance(self, scanned: str) -> None:
            for ch in scanned:
                self._current += 1
                self._lag_cursor = copy(self._current_cursor)
                if ch == "\n":
                    self._current_cursor = self._current_cursor.next_line
                else:
                    self._current_cursor = self._current_cursor.right

        def advance_start(self) -> None:
            self._start = self._current
            self._start_cursor = copy(self._current_cursor)

        @property
        def start(self) -> int:
            return self._start

        @property
        def current(self) -> int:
            return self._current

        @property
        def cursor(self) -> Cursor:
            return self._current_cursor

        @property
        def range(self) -> CursorRange:
            return CursorRange(self._start_cursor, self._lag_cursor)

    class LexError(Exception):
        def __init__(self, msg: str = "an error occurred"):
            super().__init__(msg)

    @classmethod
    def for_vocabulary(cls, vocabulary: Vocabulary) -> Lex:
        return cls(vocabulary)

    @classmethod
    def for_grammar(cls, grammar: "Grammar") -> Lex:  # type: ignore
        return cls(grammar.vocabulary, grammar_name=grammar.name)

    @classmethod
    def for_lang(cls, lang: "Lang") -> Lex:  # type: ignore
        return cls.for_grammar(lang.grammar)

    def __init__(
        self,
        vocabulary: Vocabulary,
        grammar_name: str = "none",
    ):
        self._grammar_name: str = grammar_name
        self._vocabulary: Vocabulary = vocabulary
        self._c: str = ""

    def __repr__(self) -> str:
        return f"Lexer({self._grammar_name})"

    def _at_end(self):
        return self._position.current >= len(self._source)

    def _peek(self) -> None:
        if self._at_end():
            self._c = "\0"
        else:
            self._c = self._source[self._position.current]

    def _advance(self, scanned: str) -> None:
        self._position.advance(scanned)
        self._peek()

    def _advance_start(self) -> None:
        self._position.advance_start()

    # todo: efficiency
    def _match(self, matcher: re.Pattern) -> re.Match | None:
        return matcher.match(self._source[self._position.current :])

    def _make_token(
        self,
        token_type: str,
    ) -> Token:
        lexeme: str = self._source[self._position.start : self._position.current]

        literal: Any = self._vocabulary[token_type].literal_generator(lexeme)

        return Token(
            token_type,
            lexeme,
            literal,
            {"range": self._position.range},
        )

    def _consume_ignored(self) -> None:
        while not self._at_end():
            for matcher in self._vocabulary.ignore:
                match = self._match(matcher)
                if match:
                    self._advance(match.group())
                    break

            else:
                # no ignored matches found
                self._advance_start()
                return

    def _scan_token(self) -> Token:
        token_matches = {}
        for token_type in self._vocabulary:
            token_match = self._match(self._vocabulary[token_type].matcher)
            if token_match:
                token_matches[token_type] = token_match.group()

        if len(token_matches) == 0 or all(
            map(lambda token_match: token_match in ["e", "$"], token_matches)
        ):
            raise Lex.LexError(
                f"invalid character '{self._c}' encountered at {str(self._position.cursor)}"
            )
            # todo: errors...
            Log.ef(
                f"[red]LexError:[/red] invalid character '{self._c}' encountered at {str(self._position.cursor)}:"
            )
            lines: list[str] = self._source.split("\n")
            line: str = lines[self._position.cursor.line - 1]
            column: int = self._position.cursor.column - 1
            if self._position.cursor.line > 1:
                Log.ef(
                    f"[yellow]{self._position.cursor.line - 1}[/yellow] {lines[self._position.cursor.line - 2]}",
                    highlight=False,
                )
            Log.ef(
                f"[yellow]{self._position.cursor.line}[/yellow] {line[:column]}[red]{line[column]}[/red]{line[column + 1:]}",
                highlight=False,
            )
            if self._position.cursor.line <= len(lines):
                Log.ef(
                    f"[yellow]{self._position.cursor.line + 1}[/yellow] {lines[self._position.cursor.line]}",
                    highlight=False,
                )

            exit(1)

        else:
            longest_match_token_type = max(
                token_matches, key=lambda token_type: len(token_matches[token_type])
            )
            # todo: hopefully make this more elegant when no longer lexing with library regex engine
            self._advance(token_matches[longest_match_token_type])
            # todo: fix this hack
            if (
                f'"{self._source[self._position.start : self._position.current]}"'
                in token_matches
            ):
                longest_match_token_type = (
                    f'"{self._source[self._position.start : self._position.current]}"'
                )

            token = self._make_token(longest_match_token_type)
            self._advance_start()
            return token

    def _lex(self):
        self._peek()
        self._consume_ignored()
        while not self._at_end():
            self._tokens.append(self._scan_token())
            self._consume_ignored()

    def __call__(self, source: str) -> list[Token]:
        self._source: str = source
        self._position = Lex.Position()
        self._tokens: list[Token] = []

        self._lex()

        return self._tokens

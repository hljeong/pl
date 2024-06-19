from __future__ import annotations
from copy import copy
import re

from common import Cursor, CursorRange, Log

from .token import Token


class Lexer:
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

    def __init__(
        self,
        grammar: Optional[Grammar] = None,
        vocabulary: Optional[Vocabulary] = None,
    ):
        if grammar is not None and vocabulary is not None:
            Log.w("more than sufficient arguments provided", tag="Lexer")

        if vocabulary is None:
            if grammar is None:
                error: ValueError = ValueError(
                    "provide either grammar or vocabulary to create a lexer"
                )
                if not Log.ef(
                    "[red]ValueError:[/red] provide either grammar or vocabulary to create a lexer"
                ):
                    raise error

            self._grammar_name: str = grammar.name
            self._vocabulary: Vocabulary = grammar.vocabulary

        else:
            self._grammar_name: str = "none"
            self._vocabulary: Vocabulary = vocabulary

    def __repr__(self) -> str:
        return f"Lexer({self._grammar_name})"

    def __at_end(self):
        return self._position.current >= len(self._source)

    def __peek(self) -> None:
        if self.__at_end():
            self._peek = "\0"
        else:
            self._peek = self._source[self._position.current]

    def __advance(self, scanned: str) -> None:
        self._position.advance(scanned)
        self.__peek()

    def __advance_start(self) -> None:
        self._position.advance_start()

    # todo: efficiency
    def __match(self, matcher: re.Pattern) -> re.Match:
        return matcher.match(self._source[self._position.current :])

    def __consume_match(self, matcher_name: str) -> bool:
        match = self.__match(matchers[matcher_name])
        if match:
            self.__advance(match.group())
            return True
        return False

    def __make_token(
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

    def __consume_ignored(self) -> None:
        while not self.__at_end():
            for matcher in self._vocabulary.ignore:
                match = self.__match(matcher)
                if match:
                    self.__advance(match.group())
                    break

            else:
                # no ignored matches found
                self.__advance_start()
                return

    def __scan_token(self) -> Token:
        token_matches = {}
        for token_type in self._vocabulary:
            token_match = self.__match(self._vocabulary[token_type].matcher)
            if token_match:
                token_matches[token_type] = token_match.group()

        if len(token_matches) == 0:
            # todo: do this more elegantly
            error: Lexer.LexError = Lexer.LexError(
                f"invalid character '{self._peek}' encountered at {str(self._position.cursor)}"
            )

            if Log.begin_e():
                Log.ef(
                    f"[red]LexError:[/red] invalid character '{self._peek}' encountered at {str(self._position.cursor)}:"
                )
                lines: list[str] = self._source.split("\n")
                line: str = lines[self._position.cursor.line - 1]
                column: int = self._position.cursor.column - 1
                Log.ef(
                    f"  {line[:column]}[red]{line[column]}[/red]{line[column + 1:]}",
                    highlight=False,
                )
                Log.end_e()

            else:
                raise error

        else:
            longest_match_token_type = max(
                token_matches, key=lambda token_type: len(token_matches[token_type])
            )
            # todo: hopefully make this more elegant when no longer lexing with library regex engine
            self.__advance(token_matches[longest_match_token_type])
            # todo: fix this hack
            if (
                f'"{self._source[self._position.start : self._position.current]}"'
                in token_matches
            ):
                longest_match_token_type = (
                    f'"{self._source[self._position.start : self._position.current]}"'
                )

            token = self.__make_token(longest_match_token_type)
            self.__advance_start()
            return token

    def __lex(self):
        self.__peek()
        self.__consume_ignored()
        while not self.__at_end():
            self._tokens.append(self.__scan_token())
            self.__consume_ignored()

    def lex(self, source: str) -> list[Token]:
        self._source: str = source
        self._position = Lexer.Position()
        self._tokens: list[Token] = []

        self.__lex()

        return self._tokens

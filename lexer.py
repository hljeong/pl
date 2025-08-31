from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import total_ordering
import re
from typing import ClassVar


@total_ordering
@dataclass(frozen=True)
class Cursor:
    row: int
    col: int

    def __str__(self) -> str:
        return f"row {self.row + 1} col {self.col + 1}"

    def __iter__(self) -> Iterator[int]:
        yield self.row
        yield self.col

    def __lt__(self, other: Cursor) -> bool:
        return self.row < other.row or (self.row == other.row and self.col < other.col)


@dataclass(frozen=True)
class CursorRange:
    start: Cursor
    end: Cursor

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError(f"start ({self.start}) is after end ({self.end})")

    def __iter__(self) -> Iterator[Cursor]:
        yield self.start
        yield self.end


@dataclass
class Source:
    src: str
    lines: list[str] = field(init=False)

    def __post_init__(self):
        self.lines = self.src.split("\n")

    @staticmethod
    def from_file(path: str) -> Source:
        with open(path) as f:
            return Source(f.read().rstrip("\n"))

    @property
    def rows(self) -> int:
        return len(self.lines)

    def cols(self, row: int) -> int:
        return len(self.lines[row])

    def valid(self, pos: Cursor) -> bool:
        row: int
        col: int
        row, col = pos
        return row < self.rows and col <= self.cols(row)

    def next(self, pos: Cursor, *, n: int = 1) -> Cursor:
        match n:
            case 1:
                if self[pos] == "eof":
                    raise StopIteration

                if pos.col == self.cols(pos.row):
                    return Cursor(pos.row + 1, 0)
                else:
                    return Cursor(pos.row, pos.col + 1)

            case _:
                for _ in range(n):
                    pos = self.next(pos)
                return pos

    def range(self, start: Cursor, end: Cursor | None = None) -> Iterator[Cursor]:
        pos: Cursor = start
        while pos != end:
            yield pos
            if self[pos] == "eof":
                break
            else:
                pos = self.next(pos)

    def len(self, rng: CursorRange) -> int:
        return sum(1 for _ in self.range(rng.start, rng.end))

    def char_at(self, pos: Cursor) -> str:
        row: int
        col: int
        row, col = pos

        if col == self.cols(row):
            return "eof" if row == self.rows - 1 else "\n"
        else:
            return self.lines[row][col]

    def str_at(self, rng: CursorRange) -> str:
        start: Cursor
        end: Cursor
        start, end = rng
        return "".join(self[pos] for pos in self.range(start, end))

    def __getitem__(self, key: Cursor | CursorRange) -> str:
        match key:
            case Cursor():
                return self.char_at(key)

            case CursorRange():
                return self.str_at(key)


@dataclass
class Token:
    src: Source = field(repr=False)
    rng: CursorRange
    lexeme: str = field(init=False)
    alternative: Token | None = field(default=None, repr=False)

    compiled_regex: ClassVar[re.Pattern]

    __match_args__ = ("lexeme",)

    def __post_init__(self):
        self.lexeme = self.src[self.rng]

    @property
    def len(self) -> int:
        return len(self.lexeme)

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @staticmethod
    def define(token_type: str, regex: str) -> type[Token]:
        return type(token_type, (Token,), dict(compiled_regex=re.compile(regex)))

    @classmethod
    def regex(cls) -> re.Pattern:
        return cls.compiled_regex


Character: type[Token] = Token.define("Character", r"[A-Za-z0-9_]")
Identifier: type[Token] = Token.define("Identifier", r"[A-Za-z_][A-Za-z0-9_]*")
LeftParenthesis: type[Token] = Token.define("Left Parenthesis", r"\(")
RightParenthesis: type[Token] = Token.define("Right Parenthesis", r"\)")
LeftBracket: type[Token] = Token.define("Left Bracket", r"\[")
RightBracket: type[Token] = Token.define("Right Bracket", r"\]")
LeftBrace: type[Token] = Token.define("Left Brace", r"\{")
RightBrace: type[Token] = Token.define("Right Brace", r"\}")
LeftAngleBracket: type[Token] = Token.define("Left Angle Bracket", r"<")
RightAngleBracket: type[Token] = Token.define("Right Angle Bracket", r">")
Plus: type[Token] = Token.define("Plus", r"\+")
Minus: type[Token] = Token.define("Minus", r"-")
Asterisk: type[Token] = Token.define("Asterisk", r"\*")
Slash: type[Token] = Token.define("Slash", r"/")
Equals: type[Token] = Token.define("Equals", r"=")
Question: type[Token] = Token.define("Question", r"\?")
Exclamation: type[Token] = Token.define("Exclamation", r"!")
Pipe: type[Token] = Token.define("Pipe", r"\|")
Colon: type[Token] = Token.define("Colon", r":")
Semicolon: type[Token] = Token.define("Semicolon", r";")
DoubleQuote: type[Token] = Token.define("DoubleQuote", r'"')
SingleQuote: type[Token] = Token.define("SingleQuote", r"'")


class Lexer:
    WHITESPACE: set[str] = {" ", "\t", "\n"}

    # todo: how to properly do exceptions?
    class Error(Exception):
        def __init__(self, src: Source, pos: Cursor, msg: str = "an error occurred"):
            rows_to_show: list[int] = list(
                range(max(0, pos.row - 3), min(src.rows, pos.row + 3))
            )
            # todo: this should come from utils lib for text column formatting
            # todo: also move this visualization code into Source
            line_num_width: int = max(len(str(row + 1)) for row in rows_to_show)
            rows: list[str] = [
                f"  {row + 1:>{line_num_width}} {src.lines[row]}"
                for row in rows_to_show
            ]
            rows.insert(
                rows_to_show.index(pos.row) + 1,
                f"  {' ' * line_num_width} {' ' * pos.col}^",
            )
            super().__init__("\n".join([msg] + rows))

    class Instance:
        def __init__(self, src: Source):
            self.src: Source = src
            self.pos: Cursor = Cursor(0, 0)

        def skip_whitespace(self):
            for pos in self.src.range(self.pos):
                self.pos = pos
                if self.src[pos] not in Lexer.WHITESPACE:
                    return

        def parse_token(self, token_types: list[type[Token]]) -> Token:
            matches: list[Token] = []
            for token_type in token_types:
                match token_type.regex().match(
                    self.src.lines[self.pos.row][self.pos.col :]
                ):
                    case None:
                        pass

                    case match:
                        matches.append(
                            token_type(
                                self.src,
                                CursorRange(
                                    self.pos, self.src.next(self.pos, n=match.end())
                                ),
                            )
                        )

            if not matches:
                raise Lexer.Error(
                    self.src, self.pos, f"could not parse token at {self.pos}"
                )

            matches = sorted(matches, key=lambda token: token.len)
            matches = [token for token in matches if token.len == matches[-1].len]

            # if longest match fits multiple token types, chain alternatives
            result = matches[0]
            for match in matches[1:]:
                match.alternative = result
                result = match

            self.pos = result.rng.end
            self.skip_whitespace()

            return result

        def lex_tokens(self, token_types: list[type[Token]]) -> list[Token]:
            result: list[Token] = []
            self.skip_whitespace()
            while self.src[self.pos] != "eof":
                result.append(self.parse_token(token_types))
            return result

        def lex(self) -> list[Token]:
            raise NotImplementedError

    def lex(self, src: Source) -> list[Token]:
        return self.Instance(src).lex()


class GenericLexer(Lexer):
    def __init__(self, token_types: list[type[Token]]):
        self.token_types: list[type[Token]] = token_types

        oself: GenericLexer = self

        class Instance(Lexer.Instance):
            def __init__(self, src: Source):
                super().__init__(src)

            def lex(self) -> list[Token]:
                result: list[Token] = []
                self.skip_whitespace()
                while self.src[self.pos] != "eof":
                    print(repr(self.src[self.pos]), ord(self.src[self.pos]))
                    result.append(self.parse_token(oself.token_types))
                return result

        self.Instance: type[Lexer.Instance] = Instance

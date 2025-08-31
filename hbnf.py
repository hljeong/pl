from __future__ import annotations

from lexer import (
    Asterisk,
    Cursor,
    Lexer as AbstractLexer,
    Token,
    Identifier,
    Plus,
    Question,
    Colon,
    Source,
    Semicolon,
)
from utils import oxford


String: type[Token] = Token.define("String", r'"([^"]|\\")*"')

TOKEN_TYPES: list[type[Token]] = [
    String,
    Identifier,
    Colon,
    Question,
    Asterisk,
    Plus,
    Semicolon,
]


class Lexer(AbstractLexer):
    def __init__(self):
        class Instance(AbstractLexer.Instance):
            def __init__(self, src: Source):
                super().__init__(src)

            def lex(self) -> list[Token]:
                return self.lex_tokens(TOKEN_TYPES)

        self.Instance: type[AbstractLexer.Instance] = Instance


# todo: generalize parsing
from dataclasses import dataclass
from typing import Iterator, TypeAlias


class Node:
    @property
    def lexeme(self) -> str:
        raise NotImplementedError(repr(self))


class InternalNode(Node):
    def __len__(self) -> int:
        return len(tuple(iter(self)))

    def __iter__(self) -> Iterator[Node]:
        raise NotImplementedError(type(self).__name__)

    @property
    def lexeme(self) -> str:
        # todo: fix this
        return " ".join(child.lexeme for child in self)


LeafNode: TypeAlias = Token


# todo: semantic nomenclature
@dataclass
class MultUnnamedVariant1(InternalNode):
    question: Question

    def __iter__(self) -> Iterator[Node]:
        yield self.question


@dataclass
class MultUnnamedVariant2(InternalNode):
    asterisk: Asterisk

    def __iter__(self) -> Iterator[Node]:
        yield self.asterisk


@dataclass
class MultUnnamedVariant3(InternalNode):
    plus: Plus

    def __iter__(self) -> Iterator[Node]:
        yield self.plus


Mult: TypeAlias = MultUnnamedVariant1 | MultUnnamedVariant2 | MultUnnamedVariant3


@dataclass
class Term(InternalNode):
    string: String

    def __iter__(self) -> Iterator[Node]:
        yield self.string


@dataclass
class Nonterm(InternalNode):
    identifier: Identifier

    def __iter__(self) -> Iterator[Node]:
        yield self.identifier


@dataclass
class SymbolUnnamedVariant1(InternalNode):
    nonterm: Nonterm

    def __iter__(self) -> Iterator[Node]:
        yield self.nonterm


@dataclass
class SymbolUnnamedVariant2(InternalNode):
    term: Term

    def __iter__(self) -> Iterator[Node]:
        yield self.term


Symbol: TypeAlias = SymbolUnnamedVariant1 | SymbolUnnamedVariant2


@dataclass
class Factor(InternalNode):
    symbol: Symbol
    mult: Mult | None

    def __iter__(self) -> Iterator[Node]:
        yield self.symbol
        if self.mult:
            yield self.mult


@dataclass
class Rule(InternalNode):
    factors: list[Factor]

    def __iter__(self) -> Iterator[Node]:
        yield from self.factors


@dataclass
class Prod(InternalNode):
    nonterm: Nonterm
    rules: list[Rule]

    def __iter__(self) -> Iterator[Node]:
        yield self.nonterm
        yield from self.rules


@dataclass
class Hbnf(InternalNode):
    prods: list[Prod]

    def __iter__(self) -> Iterator[Node]:
        yield from self.prods


class Parser:
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
        def __init__(self, tokens: list[Token]):
            if not tokens:
                # todo: possible to make Parser.Error better to account for this?
                raise ValueError("empty source")
            self.tokens: list[Token] = tokens
            # todo: kinda ugly
            self.src: Source = self.tokens[0].src
            self.idx: int = 0

        def at_end(self) -> bool:
            return self.idx >= len(self.tokens)

        def peek(self) -> Token:
            assert not self.at_end()
            return self.tokens[self.idx]

        def lookahead(self, *token_types: type[Token]) -> Token | None:
            if self.at_end():
                return None

            token: Token = self.peek()
            for token_type in token_types:
                if isinstance(token, token_type):
                    return token

            return None

        def advance(self):
            assert not self.at_end()
            self.idx += 1

        def consume(self) -> Token:
            token: Token = self.peek()
            self.advance()
            return token

        # todo: return type should be union of token_type -- is it even possible?
        def expect(self, *token_types: type[Token]) -> Token:
            if self.at_end():
                raise Parser.Error(
                    self.src,
                    self.tokens[-1].rng.end,
                    f"expected {oxford(token_type.name() for token_type in token_types)} but reached eof",
                )

            token: Token = self.peek()
            if not any(isinstance(token, token_type) for token_type in token_types):
                raise Parser.Error(
                    self.src,
                    token.rng.start,
                    f"expected {oxford(token_type.name() for token_type in token_types)} but got {token.name()}",
                )

            self.advance()
            return token

        # todo: return from lookahead directly
        # todo: return type should be token_type | None -- is it even possible?
        def maybe(self, *token_types: type[Token]) -> Token | None:
            return self.expect(*token_types) if self.lookahead(*token_types) else None

        # todo: type analysis
        def parse_mult(self) -> Mult:
            match self.expect(Question, Asterisk, Plus):
                case Question() as question:
                    return MultUnnamedVariant1(question)

                case Asterisk() as asterisk:
                    return MultUnnamedVariant2(asterisk)

                case Plus() as plus:
                    return MultUnnamedVariant3(plus)

        def parse_nonterm(self) -> Nonterm:
            return Nonterm(self.expect(Identifier))

        def parse_symbol_unnamed_variant_1(self) -> SymbolUnnamedVariant1:
            return SymbolUnnamedVariant1(self.parse_nonterm())

        def parse_term(self) -> Term:
            return Term(self.expect(String))

        def parse_symbol_unnamed_variant_2(self) -> SymbolUnnamedVariant2:
            return SymbolUnnamedVariant2(self.parse_term())

        # todo: type analysis
        def parse_symbol(self) -> Symbol:
            match self.lookahead(Identifier, String):
                case Identifier():
                    return self.parse_symbol_unnamed_variant_1()

                case String():
                    return self.parse_symbol_unnamed_variant_2()

                # appease dimwit type checker
                case _:
                    assert False

        def parse_factor(self) -> Factor:
            symbol: Symbol = self.parse_symbol()
            if self.lookahead(Question, Asterisk, Plus):
                return Factor(symbol, self.parse_mult())
            else:
                return Factor(symbol, None)

        def parse_rule(self) -> Rule:
            self.expect(Colon)
            factors: list[Factor] = [self.parse_factor()]
            while self.lookahead(Identifier, String):
                factors.append(self.parse_factor())
            return Rule(factors)

        def parse_prod(self) -> Prod:
            nonterm: Nonterm = self.parse_nonterm()
            rules: list[Rule] = [self.parse_rule()]
            while self.lookahead(Colon):
                rules.append(self.parse_rule())
            self.expect(Semicolon)
            return Prod(nonterm, rules)

        def parse(self) -> Hbnf:
            prods: list[Prod] = []
            while not self.at_end():
                prods.append(self.parse_prod())
            return Hbnf(prods)

    def parse(self, tokens: list[Token]) -> Hbnf:
        return self.Instance(tokens).parse()


def ast_str(
    node: Node,
    prefix: str = "",
    last: bool = False,
    entry_point: bool = True,
) -> str:
    use_prefix: str = ""
    if not entry_point:
        if last:
            use_prefix = prefix + "└─ "
            prefix += "   "

        else:
            use_prefix = prefix + "├─ "
            prefix += "│  "

    match node:
        case LeafNode():
            return f"{use_prefix}{node.lexeme}"

        case InternalNode():
            lines = [f"{use_prefix}{type(node).__name__}"]
            for idx, child in enumerate(node):
                is_last = idx == len(node) - 1
                lines.append(
                    ast_str(
                        child,
                        prefix,
                        is_last,
                        False,
                    )
                )
            return "\n".join(lines)

        case _:
            assert False, repr(node)

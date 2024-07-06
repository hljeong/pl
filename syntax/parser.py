from __future__ import annotations
from typing import NamedTuple, Optional, Callable

from common import Log
from lexical import Token, Vocabulary

from .ast import (
    ASTNode,
    NonterminalASTNode,
    ChoiceNonterminalASTNode,
    AliasASTNode,
    TerminalASTNode,
)

NodeParser = Callable[["Parser", Optional[bool]], Optional[ASTNode]]


# todo: use dataclass?
class ExpressionTerm:
    def __init__(
        self,
        node_type: str,
        multiplicity: str = "1",
        label: Optional[str] = None,
    ):
        self._node_type: str = node_type
        self._multiplicity: str = multiplicity
        self._label: Optional[str] = label

    @property
    def node_type(self) -> str:
        return self._node_type

    @property
    def multiplicity(self) -> str:
        return self._multiplicity

    @property
    def label(self) -> Optional[str]:
        return self._label

    def __str__(self) -> str:
        if type(self._multiplicity) is int and self._multiplicity == "":
            return f"{self._node_type}"
        else:
            return f"{self._node_type}{self._multiplicity}"

    def __repr__(self) -> str:
        return f"ExpressionTerm({self})"


class Parser:

    class Result(NamedTuple):
        node: ASTNode
        n_tokens_consumed: int

    class ParseError(Exception):
        def __init__(self, msg: str = "an error occured"):
            super().__init__(msg)

    @staticmethod
    def for_grammar(grammar: "Grammar", entry_point: Optional[str] = None):  # type: ignore
        return Parser(
            grammar.node_parsers,
            grammar.entry_point if entry_point is None else entry_point,
            grammar_name=grammar.name,
        )

    @staticmethod
    def for_lang(lang: "Lang", entry_point: Optional[str] = None):  # type: ignore
        return Parser.for_grammar(lang.grammar, entry_point)

    def __init__(
        self,
        node_parsers: dict[str, NodeParser],
        entry_point: str,
        grammar_name: str = "none",
    ):
        self._grammar_name: str = grammar_name
        self._node_parsers: dict[str, NodeParser] = node_parsers
        self._entry_point: str = entry_point

    def __repr__(self) -> str:
        return f"Parser(grammar={self._grammar_name})"

    def __parse(self) -> ASTNode:
        parse_result: Parser.Result = self._node_parsers[self._entry_point](self)

        if parse_result is None:
            error: Parser.ParseError = Parser.ParseError("failed to parse")
            if not Log.ef("[red]ParseError:[/red] failed to parse"):
                raise error

        elif not self.at_end():
            error: Parser.ParseError = Parser.ParseError(
                "did not parse until end of file"
            )
            if not Log.ef("[red]ParseError:[/red] did not parse until end of file"):
                raise error

        return parse_result.node

    def parse_node(
        self, node_type: str, backtrack: bool = False
    ) -> Optional[Parser.Result]:
        Log.t(
            f"parsing {node_type}, next token (index {self._current}) is {self.__safe_peek()}",
            tag="Parser",
        )

        # todo: type annotation
        parser: Any = self._node_parsers[node_type]
        parse_result: Optional[Parser.Result] = parser(self, False)

        Log.begin_t()
        if parse_result is None:
            Log.t(f"unable to parse {node_type}", tag="Parser")
        else:
            Log.t(f"parsed {node_type}", tag="Parser")

        Log.t(
            f"next token (index {self._current}) is {self.__safe_peek()}", tag="Parser"
        )
        Log.end_t()

        return parse_result

    def at_end(self) -> bool:
        return self._current >= len(self._tokens)

    def __peek(self) -> Token:
        return self._tokens[self._current]

    def __safe_peek(self) -> Token:
        if self.at_end():
            return "EOF"
        else:
            return self.__peek()

    def expect(self, token_type: str) -> Optional[Token]:
        Log.t(f"expecting {token_type}", tag="Parser")

        if self.at_end():
            Log.t(f"got EOF", tag="Parser")
            return None

        token: Token = self.__peek()
        Log.t(f"got {token.token_type}", tag="Parser")
        if token.token_type != token_type:
            return None

        self.__advance(1)
        return token

    def __advance(self, n_tokens: int) -> None:
        self._current += n_tokens

    def __save(self) -> int:
        return self._current

    def __backtrack(self, to: int) -> None:
        self._current = to

    def __call__(self, tokens: list[Token]) -> ASTNode:
        self._tokens: list[Token] = tokens
        self._current: int = 0
        return self.__parse()

    @staticmethod
    def generate_nonterminal_parser(
        nonterminal: str, body: list[list[ExpressionTerm]]
    ) -> NodeParser:

        def nonterminal_parser(
            parser: Parser, entry_point: bool = True
        ) -> Optional[ChoiceNonterminalASTNode]:
            choices = {}

            for idx, expression_terms in enumerate(body):

                node: ChoiceNonterminalASTNode = ChoiceNonterminalASTNode(
                    nonterminal, idx
                )
                good: bool = True
                save: int = parser.__save()
                n_tokens_consumed: int = 0

                for expression_term_idx, expression_term in enumerate(expression_terms):
                    match expression_term.multiplicity:
                        # exactly 1 (default)
                        case "1":
                            child_parse_result: Optional[Parser.Result] = (
                                parser.parse_node(expression_term.node_type)
                            )

                            if child_parse_result is not None:
                                child_node: ASTNode
                                child_n_tokens_consumed: int
                                child_node, child_n_tokens_consumed = child_parse_result

                                if expression_term.label:
                                    child_node.extras["name"] = expression_term.label
                                node.add(child_node)
                                n_tokens_consumed += child_n_tokens_consumed

                            else:
                                good = False
                                break

                        # optional
                        case "?":
                            child: NonterminalASTNode = NonterminalASTNode(
                                f"{nonterminal}:{expression_term_idx}{expression_term.multiplicity}"
                            )
                            grandchild_parse_result: Optional[Parser.Result] = (
                                parser.parse_node(expression_term.node_type)
                            )

                            if grandchild_parse_result is not None:
                                grandchild_node: ASTNode
                                grandchild_n_tokens_consumed: int
                                grandchild_node, grandchild_n_tokens_consumed = (
                                    grandchild_parse_result
                                )

                                child.add(grandchild_node)
                                n_tokens_consumed += grandchild_n_tokens_consumed

                            if expression_term.label:
                                child.extras["name"] = expression_term.label
                            node.add(child)

                        # any number
                        case "*":
                            child: NonterminalASTNode = NonterminalASTNode(
                                f"{nonterminal}:{expression_term_idx}{expression_term.multiplicity}"
                            )

                            while True:
                                grandchild_parse_result: Optional[Parser.Result] = (
                                    parser.parse_node(expression_term.node_type)
                                )

                                if grandchild_parse_result is not None:
                                    grandchild_node: ASTNode
                                    grandchild_n_tokens_consumed: int
                                    grandchild_node, grandchild_n_tokens_consumed = (
                                        grandchild_parse_result
                                    )

                                    child.add(grandchild_node)
                                    n_tokens_consumed += grandchild_n_tokens_consumed

                                else:
                                    break

                            if expression_term.label:
                                child.extras["name"] = expression_term.label
                            node.add(child)

                        # at least 1
                        case "+":
                            child: NonterminalASTNode = NonterminalASTNode(
                                f"{nonterminal}:{expression_term_idx}{expression_term.multiplicity}"
                            )

                            grandchild_parse_result: Optional[Parser.Result] = (
                                parser.parse_node(expression_term.node_type)
                            )
                            if grandchild_parse_result is not None:
                                grandchild_node: ASTNode
                                grandchild_n_tokens_consumed: int
                                grandchild_node, grandchild_n_tokens_consumed = (
                                    grandchild_parse_result
                                )

                                child.add(grandchild_node)
                                n_tokens_consumed += grandchild_n_tokens_consumed

                            else:
                                good = False
                                break

                            while True:
                                grandchild_parse_result: Optional[Parser.Result] = (
                                    parser.parse_node(expression_term.node_type)
                                )

                                if grandchild_parse_result is not None:
                                    grandchild_node: ASTNode
                                    grandchild_n_tokens_consumed: int
                                    grandchild_node, grandchild_n_tokens_consumed = (
                                        grandchild_parse_result
                                    )

                                    child.add(grandchild_node)
                                    n_tokens_consumed += grandchild_n_tokens_consumed

                                else:
                                    break

                            if expression_term.label:
                                child.extras["name"] = expression_term.label
                            node.add(child)

                        case _:  # pragma: no cover
                            assert False

                if good:
                    choices[idx] = Parser.Result(node, n_tokens_consumed)
                parser.__backtrack(save)

            if len(choices) == 0:
                return None

            longest_match_idx = max(
                choices, key=lambda idx: choices[idx].n_tokens_consumed
            )

            parser.__advance(choices[longest_match_idx].n_tokens_consumed)

            return choices[longest_match_idx]

        return nonterminal_parser

    @staticmethod
    def generate_alias_parser(
        alias: str,
        terminal: str,
    ) -> NodeParser:

        def alias_parser(
            parser: Parser, entry_point: bool = False
        ) -> Optional[Union[Node, Token]]:
            token: Token = parser.expect(terminal)
            if token is None:
                return None
            return Parser.Result(AliasASTNode(alias, terminal, token), 1)

        return alias_parser

    @staticmethod
    def generate_terminal_parser(
        terminal: str,
    ) -> NodeParser:

        def terminal_parser(
            parser: Parser, entry_point: bool = False
        ) -> Optional[Union[Node, Token]]:
            token: Token = parser.expect(terminal)
            if token is None:
                return None
            return Parser.Result(TerminalASTNode(terminal, token), 1)

        return terminal_parser

    @staticmethod
    def generate_parsers_from_vocabulary(
        vocabulary: Vocabulary,
    ) -> dict[str, NodeParser]:
        return {
            terminal: Parser.generate_terminal_parser(terminal)
            for terminal in vocabulary
        }

from __future__ import annotations
from typing import NamedTuple, Callable, Any

from common import Log
from lexical import Token, Vocabulary

from .ast import (
    ASTNode,
    NonterminalASTNode,
    ChoiceNonterminalASTNode,
    AliasASTNode,
    TerminalASTNode,
)


# todo: use dataclass?
class ExpressionTerm:
    def __init__(
        self,
        node_type: str,
        multiplicity: str = "",
        label: str | None = None,
    ):
        self._node_type: str = node_type
        self._multiplicity: str = multiplicity
        self._label: str | None = label

    @property
    def node_type(self) -> str:
        return self._node_type

    @property
    def multiplicity(self) -> str:
        return self._multiplicity

    @property
    def label(self) -> str | None:
        return self._label

    def __str__(self) -> str:
        if type(self._multiplicity) is int and self._multiplicity == "":
            return f"{self._node_type}"
        else:
            return f"{self._node_type}{self._multiplicity}"

    def __repr__(self) -> str:
        return f"ExpressionTerm({self})"


class NExpressionTerm:
    def __init__(
        self,
        node_type: str,
        label: str | None = None,
    ):
        self._node_type: str = node_type
        self._label: str | None = label

    @property
    def node_type(self) -> str:
        return self._node_type

    @property
    def label(self) -> str | None:
        return self._label

    def __str__(self) -> str:
        if self._label is None:
            return f"{self._node_type}"
        else:
            return f"{self._label}={self._node_type}"

    def __repr__(self) -> str:
        return f"ExpressionTerm({self})"


class Parse:

    class ParseError(Exception):
        def __init__(self, msg: str = "an error occured"):
            super().__init__(msg)

    @classmethod
    def for_grammar(cls, grammar: "Grammar", entry_point: str | None = None):  # type: ignore
        if grammar.is_ll1:
            Log.d(f"using ll(1) parser for {grammar.name}")
            return cls.LL1(
                grammar.ll1_parsing_table,
                grammar.nrules,
                grammar.entry_point if entry_point is None else entry_point,
                grammar.name,
            )

        else:
            Log.d(f"using backtracking parser for {grammar.name}")
            return cls.Backtracking(
                grammar.node_parsers,
                grammar.entry_point if entry_point is None else entry_point,
                grammar.name,
            )

    @classmethod
    def for_lang(cls, lang: "Lang", entry_point: str | None = None):  # type: ignore
        return cls.for_grammar(lang.grammar, entry_point)

    class Backtracking:
        class Result(NamedTuple):
            node: ASTNode
            n_tokens_consumed: int

        NodeParser = Callable[["Parse.Backtracking"], Result | None]

        def __init__(
            self,
            node_parsers: dict[str, NodeParser],
            entry_point: str,
            grammar_name: str = "none",
        ):
            self._grammar_name: str = grammar_name
            self._node_parsers: dict[str, Parse.Backtracking.NodeParser] = node_parsers
            self._entry_point: str = entry_point

        def _parse(self) -> ASTNode:
            parse_result: Parse.Backtracking.Result | None = self._node_parsers[
                self._entry_point
            ](self)

            if parse_result is None:
                # todo: log this instead
                raise Parse.ParseError("failed to parse")

            elif not self.at_end():
                # todo: log this instead
                raise Parse.ParseError("did not parse until end of file")

            return parse_result.node

        def parse_node(
            self, node_type: str, **ctx: Any
        ) -> Parse.Backtracking.Result | None:
            Log.t(
                f"parsing {node_type}, next token (index {self._current}) is {self._safe_peek()}",
                tag="Parser",
            )

            # todo: type annotation
            parse: Parse.Backtracking.NodeParser = self._node_parsers[node_type]
            parse_result: Parse.Backtracking.Result | None = parse(self, **ctx)

            if parse_result is None:
                Log.t(f"unable to parse {node_type}", tag="Parser")
            else:
                Log.t(f"parsed {node_type}", tag="Parser")

            Log.t(
                f"next token (index {self._current}) is {self._safe_peek()}",
                tag="Parser",
            )

            return parse_result

        def at_end(self) -> bool:
            return self._current >= len(self._tokens)

        def _peek(self) -> Token:
            return self._tokens[self._current]

        def _safe_peek(self) -> Token:
            if self.at_end():
                return Token("$", "")
            else:
                return self._peek()

        def _expect(self, token_type: str) -> Token | None:
            Log.t(f"expecting {token_type}", tag="Parser")

            if self.at_end():
                Log.t(f"got EOF", tag="Parser")
                return None

            token: Token = self._peek()
            Log.t(f"got {token.token_type}", tag="Parser")
            if token.token_type != token_type:
                return None

            self._advance(1)
            return token

        def _advance(self, n_tokens: int) -> None:
            self._current += n_tokens

        def _save(self) -> int:
            return self._current

        def _backtrack(self, to: int) -> None:
            self._current = to

        def __call__(self, tokens: list[Token]) -> ASTNode:
            self._tokens: list[Token] = tokens
            self._current: int = 0
            return self._parse()

        @staticmethod
        def generate_nonterminal_parser(
            nonterminal: str, body: list[list[ExpressionTerm]]
        ) -> NodeParser:

            def nonterminal_parser(
                parser: Parse.Backtracking,
            ) -> Parse.Backtracking.Result | None:
                choices: dict[int, Parse.Backtracking.Result] = {}

                for idx, expression_terms in enumerate(body):

                    node: ChoiceNonterminalASTNode = ChoiceNonterminalASTNode(
                        nonterminal, idx
                    )
                    good: bool = True
                    save: int = parser._save()
                    n_tokens_consumed: int = 0

                    for expression_term_idx, expression_term in enumerate(
                        expression_terms
                    ):
                        match expression_term.multiplicity:
                            # exactly 1 (default)
                            case "":
                                child_parse_result: Parse.Backtracking.Result | None = (
                                    parser.parse_node(expression_term.node_type)
                                )

                                if child_parse_result is not None:
                                    child_node: ASTNode
                                    child_n_tokens_consumed: int
                                    child_node, child_n_tokens_consumed = (
                                        child_parse_result
                                    )

                                    if expression_term.label:
                                        child_node.extras["name"] = (
                                            expression_term.label
                                        )
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
                                grandchild_parse_result: (
                                    Parse.Backtracking.Result | None
                                ) = parser.parse_node(expression_term.node_type)

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
                                    grandchild_parse_result: (
                                        Parse.Backtracking.Result | None
                                    ) = parser.parse_node(expression_term.node_type)

                                    if grandchild_parse_result is not None:
                                        grandchild_node: ASTNode
                                        grandchild_n_tokens_consumed: int
                                        (
                                            grandchild_node,
                                            grandchild_n_tokens_consumed,
                                        ) = grandchild_parse_result

                                        child.add(grandchild_node)
                                        n_tokens_consumed += (
                                            grandchild_n_tokens_consumed
                                        )

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

                                grandchild_parse_result: (
                                    Parse.Backtracking.Result | None
                                ) = parser.parse_node(expression_term.node_type)
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
                                    grandchild_parse_result: (
                                        Parse.Backtracking.Result | None
                                    ) = parser.parse_node(expression_term.node_type)

                                    if grandchild_parse_result is not None:
                                        grandchild_node: ASTNode
                                        grandchild_n_tokens_consumed: int
                                        (
                                            grandchild_node,
                                            grandchild_n_tokens_consumed,
                                        ) = grandchild_parse_result

                                        child.add(grandchild_node)
                                        n_tokens_consumed += (
                                            grandchild_n_tokens_consumed
                                        )

                                    else:
                                        break

                                if expression_term.label:
                                    child.extras["name"] = expression_term.label
                                node.add(child)

                            case _:  # pragma: no cover
                                assert False

                    if good:
                        choices[idx] = Parse.Backtracking.Result(
                            node, n_tokens_consumed
                        )
                    parser._backtrack(save)

                if len(choices) == 0:
                    return None

                longest_match_idx = max(
                    choices, key=lambda idx: choices[idx].n_tokens_consumed
                )

                parser._advance(choices[longest_match_idx].n_tokens_consumed)

                return choices[longest_match_idx]

            return nonterminal_parser

        @staticmethod
        def generate_alias_parser(
            alias: str,
            terminal: str,
        ) -> NodeParser:

            # todo: review (enforce upstream?)
            assert terminal != "e"

            def alias_parser(
                parser: Parse.Backtracking,
            ) -> Parse.Backtracking.Result | None:
                token: Token | None = parser._expect(terminal)
                if token is None:
                    return None
                return Parse.Backtracking.Result(
                    AliasASTNode(alias, terminal, token), 1
                )

            return alias_parser

        @staticmethod
        def generate_terminal_parser(
            terminal: str,
        ) -> NodeParser:

            # todo: review epsilon handling
            if terminal == "e":
                return lambda *_: Parse.Backtracking.Result(
                    TerminalASTNode(terminal, Token("e", "")), 0
                )

            def terminal_parser(
                parser: Parse.Backtracking,
            ) -> Parse.Backtracking.Result | None:
                token: Token | None = parser._expect(terminal)
                if token is None:
                    return None
                return Parse.Backtracking.Result(TerminalASTNode(terminal, token), 1)

            return terminal_parser

        @staticmethod
        def generate_parsers_from_vocabulary(
            vocabulary: Vocabulary,
        ) -> dict[str, NodeParser]:
            return {
                terminal: Parse.Backtracking.generate_terminal_parser(terminal)
                for terminal in vocabulary
            }

    class LL1:

        def __init__(
            self,
            ll1_parsing_table,
            rules,
            entry_point: str,
            grammar_name: str = "none",
        ):
            self._grammar_name: str = grammar_name
            self._ll1_parsing_table = ll1_parsing_table
            self._rules = rules
            self._entry_point: str = entry_point

        def __repr__(self) -> str:
            return f"Parser(grammar={self._grammar_name})"

        def _parse(self) -> ASTNode:
            return self._parse_node(NExpressionTerm(self._entry_point))

        def _parse_node(self, term: NExpressionTerm) -> ASTNode:
            Log.t(
                f"parsing {term.node_type}, next token (index {self._current}) is {self._safe_peek()}",
                tag="Parser",
            )
            n: ASTNode

            # todo: terrible start...
            if term.node_type.startswith("<"):
                t: Token = self._safe_peek()
                # alias
                # todo: disgusting.
                if term.node_type not in self._ll1_parsing_table:
                    token = self._expect(self._rules[term.node_type].node_type)
                    if not token:
                        # todo: need way better error message
                        raise Parse.ParseError(
                            f"did not parse expected {term.node_type}"
                        )
                    n = AliasASTNode(
                        term.node_type,
                        self._rules[term.node_type].node_type,
                        token,
                    )
                    if term.label:
                        n.extras["name"] = term.label
                    return n

                if t.token_type not in self._ll1_parsing_table[term.node_type]:
                    raise Parse.ParseError(
                        f"unexpected token '{t.lexeme}' while parsing {term.node_type}, expecting {{{', '.join(self._ll1_parsing_table[term.node_type].keys())}}}"
                    )
                choice: int = self._ll1_parsing_table[term.node_type][t.token_type]
                n = ChoiceNonterminalASTNode(term.node_type, choice)
                if term.label:
                    n.extras["name"] = term.label
                production = self._rules[term.node_type][choice]
                match term.node_type[-1]:
                    case "?":
                        if choice == 0:
                            n.add(self._parse_node(production[0]))

                    case "+":
                        n.add(self._parse_node(production[0]))
                        for c in self._parse_node(production[1]):
                            n.add(c)

                    # todo: kinda ugly...
                    case "*":
                        while choice == 0:
                            n.add(self._parse_node(production[0]))
                            t = self._safe_peek()
                            if (
                                t.token_type
                                not in self._ll1_parsing_table[term.node_type]
                            ):
                                raise Parse.ParseError(
                                    f"unexpected token '{t.lexeme}' while parsing {term.node_type}, expecting {{{', '.join(self._ll1_parsing_table[term.node_type].keys())}}}"
                                )
                            choice = self._ll1_parsing_table[term.node_type][
                                t.token_type
                            ]

                    case _:
                        for term in production:
                            n.add(self._parse_node(term))
                return n
            elif term.node_type == "e":
                return TerminalASTNode("e", Token("e", ""))
            else:
                token = self._expect(term.node_type)
                if not token:
                    # todo: need way better error message
                    raise Parse.ParseError(f"did not parse expected {term.node_type}")
                return TerminalASTNode(term.node_type, token)

        def at_end(self) -> bool:
            return self._current >= len(self._tokens)

        def _peek(self) -> Token:
            return self._tokens[self._current]

        def _safe_peek(self) -> Token:
            if self.at_end():
                return Token("$", "")
            else:
                return self._peek()

        def _expect(self, token_type: str) -> Token | None:
            Log.t(f"expecting {token_type}", tag="Parser")

            if self.at_end():
                Log.t(f"got EOF", tag="Parser")
                return None

            token: Token = self._peek()
            Log.t(f"got {token.token_type}", tag="Parser")
            if token.token_type != token_type:
                return None

            self._advance(1)
            return token

        def _advance(self, n_tokens: int) -> None:
            self._current += n_tokens

        def __call__(self, tokens: list[Token]) -> ASTNode:
            self._tokens: list[Token] = tokens
            self._current: int = 0
            return self._parse()

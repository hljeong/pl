from __future__ import annotations
from typing import NamedTuple, Callable, Any
from sys import setrecursionlimit

# yikes
setrecursionlimit(5000)

from common import Log
from lexical import Token, Vocabulary

from .ast import (
    ASTNode,
    NonterminalASTNode,
    ChoiceNonterminalASTNode,
    AliasASTNode,
    TerminalASTNode,
)


class Term:
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

    clean: Callable[[ASTNode], ASTNode]

    class ParseError(Exception):
        def __init__(self, msg: str = "an error occured"):
            super().__init__(msg)

    @classmethod
    def for_grammar(cls, grammar: "Grammar", entry_point: str | None = None):  # type: ignore
        if grammar.is_ll1:
            Log.d(f"using ll(1) parser for {grammar.name}")
            return cls.LL1(
                grammar.ll1_parsing_table,
                grammar.rules,
                entry_point or grammar.entry_point,
                grammar.name,
            )

        else:
            Log.d(f"using nbacktracking parser for {grammar.name}")
            return cls.Backtracking(
                grammar.nnode_parsers,
                entry_point or grammar.entry_point,
                grammar.name,
            )

    @classmethod
    def for_lang(cls, lang: "Lang", entry_point: str | None = None):  # type: ignore
        return cls.for_grammar(lang.grammar, entry_point)

    @staticmethod
    def _clean(n: ASTNode) -> ASTNode:
        if isinstance(n, TerminalASTNode) or isinstance(n, AliasASTNode):
            return n

        n_: ASTNode
        match n.node_type[-1]:
            case "?":
                n_ = NonterminalASTNode(n.node_type, extras=n.extras)
                if n.choice == 0:
                    n_.add(Parse._clean(n[0]))
                return n_

            case "*":
                n_ = NonterminalASTNode(n.node_type, extras=n.extras)
                if n.choice == 0:
                    n_.add(Parse._clean(n[0]))
                    n_.add_all(Parse._clean(n[1]))
                return n_

            case "+":
                n_ = NonterminalASTNode(n.node_type, extras=n.extras)
                n_.add(Parse._clean(n[0]))
                n_.add_all(Parse._clean(n[1]))
                return n_

            case _:
                if isinstance(n, ChoiceNonterminalASTNode):
                    n_ = ChoiceNonterminalASTNode(
                        n.node_type, n.choice, extras=n.extras
                    )
                else:
                    n_ = NonterminalASTNode(n.node_type, extras=n.extras)

                for c in n:
                    n_.add(Parse._clean(c))

        return n_

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
            self, term: Term, **ctx: Any
        ) -> Parse.Backtracking.Result | None:
            Log.t(
                f"parsing {term.node_type}, next token (index {self._current}) is {self._safe_peek()}",
                tag="parser",
            )

            # todo: type annotation
            parse: Parse.Backtracking.NodeParser = self._node_parsers[term.node_type]
            parse_result: Parse.Backtracking.Result | None = parse(self, **ctx)

            if parse_result is None:
                Log.t(f"unable to parse {term.node_type}", tag="parser")
            else:
                Log.t(f"parsed {term.node_type}", tag="parser")

            Log.t(
                f"next token (index {self._current}) is {self._safe_peek()}",
                tag="parser",
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
            Log.t(f"expecting {token_type}", tag="parser")

            if self.at_end():
                Log.t(f"got EOF", tag="parser")
                return None

            token: Token = self._peek()
            Log.t(f"got {token.token_type}", tag="parser")
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
            return Parse._clean(self._parse())

        @staticmethod
        def generate_nonterminal_parser(
            nonterminal: str, body: list[list[Term]]
        ) -> NodeParser:

            def nonterminal_parser(
                parser: Parse.Backtracking,
            ) -> Parse.Backtracking.Result | None:
                choices: dict[int, Parse.Backtracking.Result] = {}

                for choice, production in enumerate(body):

                    n: ChoiceNonterminalASTNode = ChoiceNonterminalASTNode(
                        nonterminal, choice
                    )
                    good: bool = True
                    save: int = parser._save()
                    n_tokens_consumed: int = 0

                    c_res: Parse.Backtracking.Result | None
                    c: ASTNode

                    for term in production:
                        c_res: Parse.Backtracking.Result | None = parser.parse_node(
                            term
                        )

                        if c_res is not None:
                            c, c_n_tokens_consumed = c_res

                            if term.label:
                                c.extras["name"] = term.label
                            n.add(c)
                            n_tokens_consumed += c_n_tokens_consumed

                        else:
                            good = False
                            break

                    if good:
                        choices[choice] = Parse.Backtracking.Result(
                            n, n_tokens_consumed
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
            return self._parse_node(Term(self._entry_point))

        def _parse_node(self, term: Term) -> ASTNode:
            Log.t(
                f"parsing {term.node_type}, next token (index {self._current}) is {self._safe_peek()}",
                tag="parser",
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
            Log.t(f"expecting {token_type}", tag="parser")

            if self.at_end():
                Log.t(f"got EOF", tag="parser")
                return None

            token: Token = self._peek()
            Log.t(f"got {token.token_type}", tag="parser")
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

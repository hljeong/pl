from __future__ import annotations
from typing import NamedTuple, Callable, Any, DefaultDict
from collections import defaultdict
from itertools import pairwise
from sys import setrecursionlimit

# yikes
setrecursionlimit(5000)

from common import Log, ListSet, fixed_point
from lexical import Token, Vocabulary

from .ast import (
    ASTNode,
    NonterminalASTNode,
    AliasASTNode,
    TerminalASTNode,
)
from .grammar import Grammar


# placing here for now cuz static methods suck
def util_dict_eq(
    a: DefaultDict[str, ListSet[str]], b: DefaultDict[str, ListSet[str]]
) -> bool:
    return (
        all(k in b for k in a)
        and all(k in a for k in b)
        and all(a[k] == b[k] for k in a)
    )


# placing here for now cuz static methods suck
def util_dict_cp(d: DefaultDict[str, ListSet[str]]) -> DefaultDict[str, ListSet[str]]:
    d_: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
    for k, v in d.items():
        d_[k] = ListSet(v)
    return d_


# todo: super sucky in terms of efficiency
def generate_first(grammar: Grammar) -> DefaultDict[str, ListSet[str]]:
    vocabulary: Vocabulary = grammar.vocabulary
    rules: Grammar.Rules = grammar.rules
    productions: dict[str, Grammar.Production] = {}

    first: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
    for terminal in vocabulary:
        first[terminal].add(terminal)
    for nonterminal in rules:
        rule: Grammar.Rule = rules[nonterminal]
        match rule:
            case Grammar.Production():
                productions[nonterminal] = rule
            case Grammar.Alias():
                first[nonterminal].add(rule.node_type)
            case _:  # pragma: no cover
                assert False

    def iterate_first(cur):
        cur = util_dict_cp(cur)  # prevent side effects to the original cur
        nxt = util_dict_cp(cur)
        for nonterminal in productions:
            production = productions[nonterminal]
            for expression in production:
                nullable = True
                for term in expression:
                    if term.node_type == "e":
                        continue
                    nxt[nonterminal].add_all(cur[term.node_type].diff(["e"]))
                    if "e" not in cur[term.node_type]:
                        nullable = False
                        break

                if nullable:
                    nxt[nonterminal].add("e")
        return nxt

    return fixed_point(first, iterate_first, util_dict_eq)


# todo: super sucky in terms of efficiency
def generate_follow(grammar: Grammar) -> DefaultDict[str, ListSet[str]]:
    rules: Grammar.Rules = grammar.rules
    productions: dict[str, Grammar.Production] = {}

    for nonterminal in rules:
        rule: Grammar.Rule = rules[nonterminal]
        if type(rule) is Grammar.Production:
            productions[nonterminal] = rule

    first: DefaultDict[str, ListSet[str]] = generate_first(grammar)

    follow: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
    follow[f"<{grammar.name}>"].append("$")

    def iterate_follow(cur):
        cur = util_dict_cp(cur)  # prevent side effects to the original cur
        nxt = util_dict_cp(cur)
        for nonterminal in productions:
            production = productions[nonterminal]
            for expression in production:
                nxt[expression[-1].node_type].add_all(cur[nonterminal].diff(["e"]))

                right_nullable = True
                for l_term, r_term in reversed(tuple(pairwise(expression))):
                    l, r = l_term.node_type, r_term.node_type
                    nxt[l].add_all(first[r].diff(["e"]))
                    if right_nullable:
                        if "e" in first[r]:
                            nxt[l].add_all(cur[nonterminal].diff("e"))
                        else:
                            right_nullable = False

        return nxt

    return fixed_point(follow, iterate_follow, util_dict_eq)


class Parse:

    clean: Callable[[ASTNode], ASTNode]

    class ParseError(Exception):
        def __init__(self, msg: str = "an error occured"):
            super().__init__(msg)

    @staticmethod
    def for_grammar(grammar: Grammar, entry_point: str | None = None):
        entry_point = entry_point or grammar.entry_point
        return Parse.LL1.for_grammar(
            grammar, entry_point
        ) or Parse.Backtracking.for_grammar(grammar, entry_point)

    @staticmethod
    def for_lang(lang: "Lang", entry_point: str | None = None):  # type: ignore
        return Parse.for_grammar(lang.grammar, entry_point)

    @staticmethod
    def _clean(n: ASTNode) -> ASTNode:
        match n:
            case TerminalASTNode() | AliasASTNode():
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
                match n:
                    case NonterminalASTNode(node_type, choice, extras):
                        n_ = NonterminalASTNode(node_type, choice=choice, extras=extras)

                    case _:  # pragma: no cover
                        assert False

                for c in n:
                    n_.add(Parse._clean(c))

        return n_

    class Backtracking:
        class Result(NamedTuple):
            node: ASTNode
            n_tokens_consumed: int

        NodeParser = Callable[["Parse.Backtracking"], Result | None]

        @staticmethod
        def for_grammar(grammar: Grammar, entry_point: str) -> Parse.Backtracking:
            vocabulary = grammar.vocabulary
            rules = grammar.rules
            node_parsers: dict[str, Parse.Backtracking.NodeParser] = {}

            for nonterminal in rules:
                rule: Grammar.Rule = rules[nonterminal]
                match rule:
                    case Grammar.Production():
                        node_parsers[nonterminal] = (
                            Parse.Backtracking.generate_nonterminal_parser(
                                nonterminal, rule
                            )
                        )

                    case Grammar.Alias(node_type=node_type):
                        node_parsers[nonterminal] = (
                            Parse.Backtracking.generate_alias_parser(
                                nonterminal, node_type
                            )
                        )

                    case _:  # pragma: no cover
                        assert False

            node_parsers.update(
                Parse.Backtracking.generate_parsers_from_vocabulary(vocabulary)
            )

            return Parse.Backtracking(node_parsers, entry_point, grammar.name)

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
            self, term: "Term", **ctx: Any  # type: ignore
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
            nonterminal: str, body: Grammar.Production
        ) -> NodeParser:

            def nonterminal_parser(
                parser: Parse.Backtracking,
            ) -> Parse.Backtracking.Result | None:
                choices: dict[int, Parse.Backtracking.Result] = {}

                for choice, production in enumerate(body):

                    n: NonterminalASTNode = NonterminalASTNode(
                        nonterminal, choice=choice
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
        @staticmethod
        def for_grammar(grammar: Grammar, entry_point: str) -> Parse.LL1 | None:
            rules: Grammar.Rules = grammar.rules
            productions: dict[str, Grammar.Production] = {}

            for nonterminal in rules:
                rule: Grammar.Rule = rules[nonterminal]
                if type(rule) is Grammar.Production:
                    productions[nonterminal] = rule

            first: DefaultDict[str, ListSet[str]] = generate_first(grammar)
            follow: DefaultDict[str, ListSet[str]] = generate_follow(grammar)

            parsing_table: DefaultDict[
                str,
                dict[str, int | None],
            ] = defaultdict(lambda: {})

            for nonterminal in productions:
                production = productions[nonterminal]
                for idx, expression in enumerate(production):
                    nullable = True
                    for term in expression:
                        for x in first[term.node_type]:
                            if x != "e":
                                if x in parsing_table[nonterminal]:
                                    Log.w(
                                        f"{grammar.name} is not ll(1): multiple productions for ({nonterminal}, {x})"
                                    )
                                    return None
                                parsing_table[nonterminal][x] = idx
                        if "e" not in first[term.node_type]:
                            nullable = False
                            break
                    if nullable:
                        for x in follow[nonterminal]:
                            if x in parsing_table[nonterminal]:
                                Log.w(
                                    f"{grammar.name} is not ll(1): multiple productions for ({nonterminal}, {x})"
                                )
                                return None
                            parsing_table[nonterminal][x] = idx

            return Parse.LL1(parsing_table, rules, entry_point, grammar.name)

        def __init__(
            self,
            parsing_table,
            rules,
            entry_point: str,
            grammar_name: str = "none",
        ):
            self._grammar_name: str = grammar_name
            self._parsing_table = parsing_table
            self._rules = rules
            self._entry_point: str = entry_point

        def __repr__(self) -> str:
            return f"Parse(grammar={self._grammar_name})"

        def _parse(self) -> ASTNode:
            return self._parse_node(Grammar.Term(self._entry_point))

        def _parse_node(self, term: Grammar.Term) -> ASTNode:  # type: ignore
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
                if term.node_type not in self._parsing_table:
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

                if t.token_type not in self._parsing_table[term.node_type]:
                    raise Parse.ParseError(
                        f"unexpected token '{t.lexeme}' while parsing {term.node_type}, expecting {{{', '.join(self._parsing_table[term.node_type].keys())}}}"
                    )
                choice: int = self._parsing_table[term.node_type][t.token_type]
                n = NonterminalASTNode(term.node_type, choice=choice)
                if term.label:
                    n.extras["name"] = term.label
                production = self._rules[term.node_type][choice]
                n.add_all(self._parse_node(term) for term in production)
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
            return Parse._clean(self._parse())

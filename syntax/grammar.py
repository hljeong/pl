from __future__ import annotations
from collections import defaultdict
from typing import DefaultDict, Any

from common import Log, ListSet, fixed_point, autorepr
from lexical import Vocabulary


class Grammar:
    @classmethod
    def from_xbnf(cls, name: str, xbnf: str, ignore: list[str] = []) -> Grammar: ...

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
            return f"Term({self})"

    @autorepr
    class Expression(list[Term]):
        def __str__(self) -> str:
            return " ".join(map(str, self))

    @autorepr
    class Production(list[Expression]):
        def __str__(self) -> str:
            return " | ".join(map(str, self))

    @autorepr
    class Alias(Term): ...

    Rule = Production | Alias

    @autorepr
    class Rules(dict[str, Rule]):
        def __str__(self) -> str:
            return "; ".join(f"{lhs} -> {self[lhs]}" for lhs in self)

    def __init__(
        self,
        name: str,
        rules: Rules,
        # todo: move this to xbnf
        ignore: list[str] = [],
    ):
        # todo: validate input grammar
        self._name: str = name
        self._rules = rules
        self._generate_vocabulary(ignore)

    def __repr__(self) -> str:
        return f"Grammar(name='{self._name}')"

    @property
    def name(self) -> str:
        return self._name

    @property
    def rules(self) -> Rules:
        return self._rules

    @property
    def entry_point(self) -> str:
        return f"<{self._name}>"

    @property
    def vocabulary(self) -> Vocabulary:
        return self._vocabulary

    def _generate_vocabulary(self, ignore: list[str]) -> None:
        ignore.extend(Vocabulary.DEFAULT_IGNORE)
        dictionary: dict[str, Vocabulary.Definition] = {}

        # todo: what is this nesting :skull:
        for nonterminal in self._rules:
            rule: Grammar.Rule = self._rules[nonterminal]
            match rule:
                case Grammar.Production():
                    for expression in rule:
                        for term in expression:
                            # todo: terrible
                            if term.node_type.startswith('"'):
                                if term.node_type not in dictionary:
                                    # todo: ew... what?
                                    dictionary[term.node_type] = (
                                        Vocabulary.Definition.make_exact(
                                            term.node_type[1:-1]
                                        )
                                    )
                            elif term.node_type.startswith('r"'):
                                if term.node_type not in dictionary:
                                    dictionary[term.node_type] = (
                                        Vocabulary.Definition.make_regex(
                                            term.node_type[1:-1]
                                        )
                                    )
                case Grammar.Alias(node_type=node_type):
                    # todo: terrible
                    # todo: also duplicated logic
                    if node_type.startswith('"'):
                        if node_type not in dictionary:
                            # todo: ew... what?
                            dictionary[node_type] = Vocabulary.Definition.make_exact(
                                node_type[1:-1]
                            )
                    elif node_type.startswith('r"'):
                        if node_type not in dictionary:
                            dictionary[node_type] = Vocabulary.Definition.make_regex(
                                node_type[2:-1]
                            )

                case _:  # pragma: no cover
                    assert False

        self._vocabulary: Vocabulary = Vocabulary(dictionary, ignore)

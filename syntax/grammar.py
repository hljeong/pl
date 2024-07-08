from __future__ import annotations
from collections import defaultdict
from dataclasses import KW_ONLY
from typing import DefaultDict, cast, Optional, Callable, Union, Any

from common import Monad, Log, ListSet, fixed_point
from lexical import Vocabulary, Lex

from .ast import ASTNode, TerminalASTNode, NonterminalASTNode
from .parser import ExpressionTerm, Parse, NExpressionTerm
from .visitor import Visitor

Expression = list[ExpressionTerm]


class Production(list[Expression]): ...


class Alias(ExpressionTerm): ...


Rule = Production | Alias
Rules = dict[str, Rule]

NExpression = list[NExpressionTerm]


class NProduction(list[NExpression]): ...


class NAlias(NExpressionTerm): ...


NRule = NProduction | NAlias

NRules = dict[str, NRule]


class Grammar:
    @classmethod
    def from_xbnf(cls, name: str, xbnf: str, ignore: list[str] = []) -> Grammar:
        ast: ASTNode = (
            Monad(xbnf).then(Lex.for_lang(XBNF)).then(Parse.for_lang(XBNF)).value
        )

        # todo: dirty
        rules: Rules = GenerateRules()(ast)
        nrules: NRules = NGenerateRules()(ast)
        return cls(name, rules, nrules, ignore=ignore)

    def __init__(
        self,
        name: str,
        rules: Rules,
        nrules: NRules,
        # todo: move this to xbnf
        ignore: list[str] = [],
    ):
        # todo: validate input grammar
        self._name: str = name
        self._rules = rules
        self._nrules = nrules

        self._generate_vocabulary(ignore)
        self._generate_node_parsers()
        self._check_ll1()

    def __repr__(self) -> str:
        return f"Grammar(name='{self._name}')"

    @property
    def name(self) -> str:
        return self._name

    @property
    def rules(self) -> Rules:
        return self._rules

    @property
    def nrules(self) -> NRules:
        return self._nrules

    @property
    def entry_point(self) -> str:
        return f"<{self._name}>"

    @property
    def vocabulary(self) -> Vocabulary:
        return self._vocabulary

    # todo: stinky coupling
    @property
    def node_parsers(self) -> dict[str, Parse.Backtracking.NodeParser]:
        return self._node_parsers

    @property
    def is_ll1(self) -> bool:
        return self._is_ll1

    # todo: type annotation
    @property
    def ll1_parsing_table(self) -> Any:
        if not self._is_ll1:
            raise ValueError(f"{self._name} is not ll(1)")
        return self._ll1_parsing_table

    def _generate_vocabulary(self, ignore: list[str]) -> None:
        ignore.extend(Vocabulary.DEFAULT_IGNORE)
        dictionary: dict[str, Vocabulary.Definition] = {}

        # todo: what is this nesting :skull:
        for nonterminal in self._rules:
            rule: Rule = self._rules[nonterminal]
            if type(rule) is Production:
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

            elif type(rule) is Alias:
                # todo: terrible
                # todo: also duplicated logic
                if rule.node_type.startswith('"'):
                    if rule.node_type not in dictionary:
                        # todo: ew... what?
                        dictionary[rule.node_type] = Vocabulary.Definition.make_exact(
                            rule.node_type[1:-1]
                        )
                elif rule.node_type.startswith('r"'):
                    if rule.node_type not in dictionary:
                        dictionary[rule.node_type] = Vocabulary.Definition.make_regex(
                            rule.node_type[1:-1]
                        )

            else:  # pragma: no cover
                assert False

        self._vocabulary: Vocabulary = Vocabulary(dictionary, ignore)

    def _generate_node_parsers(self) -> None:
        self._node_parsers: dict[str, Parse.Backtracking.NodeParser] = {}

        for nonterminal in self._rules:
            rule: Rule = self._rules[nonterminal]
            if type(rule) is Production:
                self._node_parsers[nonterminal] = (
                    Parse.Backtracking.generate_nonterminal_parser(nonterminal, rule)
                )

            elif type(rule) is Alias:
                self._node_parsers[nonterminal] = (
                    Parse.Backtracking.generate_alias_parser(
                        nonterminal, rule.node_type
                    )
                )

            else:  # pragma: no cover
                assert False

        self._node_parsers.update(
            Parse.Backtracking.generate_parsers_from_vocabulary(self._vocabulary)
        )

    # todo: clean up
    def _check_ll1(self) -> None:
        eq = lambda a, b: all(k in b for k in a) and all(a[k] == b[k] for k in a)

        def cp(r):
            f = defaultdict(lambda: ListSet())
            for k in r:
                f[k] = ListSet(r[k])
            return f

        first: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
        for terminal in self._vocabulary:
            first[terminal].add(terminal)
        for nonterminal in self._nrules:
            rule: NRule = self._nrules[nonterminal]
            if type(rule) is NAlias:
                first[nonterminal].add(rule.node_type)

        def iterate_first(cur):
            nxt = cp(cur)
            for nonterminal in self._nrules:
                rule = self._nrules[nonterminal]
                if type(rule) is NProduction:
                    for expression in rule:
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

        first = fixed_point(first, iterate_first, eq)  # type: ignore

        follow: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
        follow[f"<{self._name}>"].append("$")

        def iterate_follow(cur):
            nxt = cp(cur)
            for nonterminal in self._nrules:
                rule = self._nrules[nonterminal]
                if type(rule) is NProduction:
                    for production in rule:
                        nxt[production[-1].node_type].add_all(
                            cur[nonterminal].diff(["e"])
                        )

                        right_nullable = True
                        for i in range(len(production) - 1, 0, -1):
                            l = production[i - 1].node_type
                            r = production[i].node_type
                            nxt[l].add_all(first[r].diff(["e"]))
                            if right_nullable:
                                if "e" in first[r]:
                                    nxt[l].add_all(cur[nonterminal].diff("e"))
                                else:
                                    right_nullable = False
            return nxt

        follow = fixed_point(follow, iterate_follow, eq)

        self._ll1_parsing_table: DefaultDict[
            str,
            dict[str, Optional[int]],
        ] = defaultdict(lambda: {})

        self._is_ll1 = True
        for nonterminal in self._nrules:
            rule = self._nrules[nonterminal]
            if type(rule) is NProduction:
                for idx, expression in enumerate(rule):
                    nullable = True
                    for term in expression:
                        for x in first[term.node_type]:
                            if x != "e":
                                if x in self._ll1_parsing_table[nonterminal]:
                                    self._is_ll1 = False
                                    Log.w(
                                        f"{self._name} is not ll(1): multiple productions for ({nonterminal}, {x})"
                                    )
                                    return
                                self._ll1_parsing_table[nonterminal][x] = idx
                        if "e" not in first[term.node_type]:
                            nullable = False
                            break
                    if nullable:
                        for x in follow[nonterminal]:
                            if x in self._ll1_parsing_table[nonterminal]:
                                self._is_ll1 = False
                                Log.w(
                                    f"{self._name} is not ll(1): multiple productions for ({nonterminal}, {x})"
                                )
                                return
                            self._ll1_parsing_table[nonterminal][x] = idx


class XBNF:
    nrules = NRules(
        [
            (
                "<xbnf>",
                NProduction(
                    [[NExpressionTerm("<production>"), NExpressionTerm("<rule>*")]],
                ),
            ),
            (
                "<rule>+",
                NProduction(
                    [
                        [NExpressionTerm("<rule>"), NExpressionTerm("<rule>+")],
                        [NExpressionTerm("<rule>")],
                    ],
                ),
            ),
            (
                "<rule>*",
                NProduction(
                    [[NExpressionTerm("<rule>+")], [NExpressionTerm("e")]],
                ),
            ),
            (
                "<rule>",
                NProduction(
                    [
                        [NExpressionTerm("<production>")],
                        [NExpressionTerm("<alias>")],
                    ],
                ),
            ),
            (
                "<production>",
                NProduction(
                    [
                        [
                            NExpressionTerm("<nonterminal>"),
                            NExpressionTerm('"::="'),
                            NExpressionTerm("<body>"),
                            NExpressionTerm('";"'),
                        ],
                    ],
                ),
            ),
            (
                "<alias>",
                NProduction(
                    [
                        [
                            NExpressionTerm('"alias"'),
                            NExpressionTerm("<nonterminal>"),
                            NExpressionTerm('"::="'),
                            NExpressionTerm("<terminal>"),
                            NExpressionTerm('";"'),
                        ],
                    ],
                ),
            ),
            (
                "<nonterminal>",
                NProduction(
                    [
                        [
                            NExpressionTerm('"<"'),
                            NExpressionTerm("identifier"),
                            NExpressionTerm('">"'),
                        ],
                    ],
                ),
            ),
            (
                "<body>",
                NProduction(
                    [
                        [
                            NExpressionTerm("<expression>"),
                            NExpressionTerm("<body>:1*"),
                        ],
                    ],
                ),
            ),
            (
                "<body>:1+",
                NProduction(
                    [
                        [NExpressionTerm("<body>:1"), NExpressionTerm("<body>:1+")],
                        [NExpressionTerm("<body>:1")],
                    ],
                ),
            ),
            (
                "<body>:1*",
                NProduction(
                    [
                        [NExpressionTerm("<body>:1+")],
                        [NExpressionTerm("e")],
                    ],
                ),
            ),
            (
                "<body>:1",
                NProduction(
                    [
                        [
                            NExpressionTerm('"|"'),
                            NExpressionTerm("<expression>"),
                        ],
                    ],
                ),
            ),
            (
                "<expression>",
                NProduction(
                    [
                        [
                            NExpressionTerm("<term>", "+"),
                        ],
                    ],
                ),
            ),
            (
                "<term>",
                NProduction(
                    [
                        [
                            NExpressionTerm("<term>:0?"),
                            NExpressionTerm("<group>"),
                            NExpressionTerm("<multiplicity>?"),
                        ],
                    ],
                ),
            ),
            (
                "<term>:0?",
                NProduction(
                    [
                        [NExpressionTerm("<term>:0")],
                        [NExpressionTerm("e")],
                    ],
                ),
            ),
            (
                "<multiplicity>?",
                NProduction(
                    [
                        [NExpressionTerm("<multiplicity>")],
                        [NExpressionTerm("e")],
                    ],
                ),
            ),
            (
                "<term>:0",
                NProduction(
                    [
                        [
                            NExpressionTerm("<label>"),
                            NExpressionTerm('"="'),
                        ],
                    ],
                ),
            ),
            (
                "<group>",
                NProduction(
                    [
                        [NExpressionTerm("<item>")],
                        [
                            NExpressionTerm('"("'),
                            NExpressionTerm("<body>"),
                            NExpressionTerm('")"'),
                        ],
                    ],
                ),
            ),
            (
                "<item>",
                NProduction(
                    [
                        [NExpressionTerm("<nonterminal>")],
                        [NExpressionTerm("<terminal>")],
                    ],
                ),
            ),
            (
                "<terminal>",
                NProduction(
                    [
                        [NExpressionTerm("escaped_string")],
                        [NExpressionTerm("regex")],
                        [NExpressionTerm("identifier")],
                    ],
                ),
            ),
            (
                "<multiplicity>",
                NProduction(
                    [
                        [NExpressionTerm('"?"')],
                        [NExpressionTerm('"*"')],
                        [NExpressionTerm('"+"')],
                    ],
                ),
            ),
            ("<label>", NAlias("identifier")),
        ]
    )

    rules = Rules(
        [
            (
                "<xbnf>",
                Production(
                    [[ExpressionTerm("<production>"), ExpressionTerm("<rule>", "*")]],
                ),
            ),
            (
                "<rule>",
                Production(
                    [
                        [ExpressionTerm("<production>")],
                        [ExpressionTerm("<alias>")],
                    ],
                ),
            ),
            (
                "<production>",
                Production(
                    [
                        [
                            ExpressionTerm("<nonterminal>"),
                            ExpressionTerm('"::="'),
                            ExpressionTerm("<body>"),
                            ExpressionTerm('";"'),
                        ],
                    ],
                ),
            ),
            (
                "<alias>",
                Production(
                    [
                        [
                            ExpressionTerm('"alias"'),
                            ExpressionTerm("<nonterminal>"),
                            ExpressionTerm('"::="'),
                            ExpressionTerm("<terminal>"),
                            ExpressionTerm('";"'),
                        ],
                    ],
                ),
            ),
            (
                "<nonterminal>",
                Production(
                    [
                        [
                            ExpressionTerm('"<"'),
                            ExpressionTerm("identifier"),
                            ExpressionTerm('">"'),
                        ],
                    ],
                ),
            ),
            (
                "<body>",
                Production(
                    [
                        [
                            ExpressionTerm("<expression>"),
                            ExpressionTerm("<body>:1", "*"),
                        ],
                    ],
                ),
            ),
            (
                "<body>:1",
                Production(
                    [
                        [
                            ExpressionTerm('"|"'),
                            ExpressionTerm("<expression>"),
                        ],
                    ],
                ),
            ),
            (
                "<expression>",
                Production(
                    [
                        [
                            ExpressionTerm("<term>", "+"),
                        ],
                    ],
                ),
            ),
            (
                "<term>",
                Production(
                    [
                        [
                            ExpressionTerm("<term>:0", "?"),
                            ExpressionTerm("<group>"),
                            ExpressionTerm("<multiplicity>", "?"),
                        ],
                    ],
                ),
            ),
            (
                "<term>:0",
                Production(
                    [
                        [
                            ExpressionTerm("<label>"),
                            ExpressionTerm('"="'),
                        ],
                    ],
                ),
            ),
            (
                "<group>",
                Production(
                    [
                        [ExpressionTerm("<item>")],
                        [
                            ExpressionTerm('"("'),
                            ExpressionTerm("<body>"),
                            ExpressionTerm('")"'),
                        ],
                    ],
                ),
            ),
            (
                "<item>",
                Production(
                    [
                        [ExpressionTerm("<nonterminal>")],
                        [ExpressionTerm("<terminal>")],
                    ],
                ),
            ),
            (
                "<terminal>",
                Production(
                    [
                        [ExpressionTerm("escaped_string")],
                        [ExpressionTerm("regex")],
                        [ExpressionTerm("identifier")],
                    ],
                ),
            ),
            (
                "<multiplicity>",
                Production(
                    [
                        [ExpressionTerm('"?"')],
                        [ExpressionTerm('"*"')],
                        [ExpressionTerm('"+"')],
                    ],
                ),
            ),
            ("<label>", Alias("identifier")),
        ]
    )

    vocabulary = Vocabulary(
        {
            '"alias"': Vocabulary.Definition.make_exact("alias"),
            '"<"': Vocabulary.Definition.make_exact("<"),
            '">"': Vocabulary.Definition.make_exact(">"),
            '"::="': Vocabulary.Definition.make_exact("::="),
            '"="': Vocabulary.Definition.make_exact("="),
            '";"': Vocabulary.Definition.make_exact(";"),
            '"("': Vocabulary.Definition.make_exact("("),
            '")"': Vocabulary.Definition.make_exact(")"),
            '"+"': Vocabulary.Definition.make_exact("+"),
            '"?"': Vocabulary.Definition.make_exact("?"),
            '"*"': Vocabulary.Definition.make_exact("*"),
            '"|"': Vocabulary.Definition.make_exact("|"),
            "identifier": Vocabulary.Definition.builtin["identifier"],
            "escaped_string": Vocabulary.Definition.builtin["escaped_string"],
        }
    )

    node_parsers = {
        "<xbnf>": Parse.Backtracking.generate_nonterminal_parser(
            "<xbnf>",
            [
                [ExpressionTerm("<production>"), ExpressionTerm("<rule>", "*")],
            ],
        ),
        "<rule>": Parse.Backtracking.generate_nonterminal_parser(
            "<rule>",
            [[ExpressionTerm("<production>")], [ExpressionTerm("<alias>")]],
        ),
        "<production>": Parse.Backtracking.generate_nonterminal_parser(
            "<production>",
            [
                [
                    ExpressionTerm("<nonterminal>"),
                    ExpressionTerm('"::="'),
                    ExpressionTerm("<body>"),
                    ExpressionTerm('";"'),
                ],
            ],
        ),
        "<alias>": Parse.Backtracking.generate_nonterminal_parser(
            "<alias>",
            [
                [
                    ExpressionTerm('"alias"'),
                    ExpressionTerm("<nonterminal>"),
                    ExpressionTerm('"::="'),
                    ExpressionTerm("<terminal>"),
                    ExpressionTerm('";"'),
                ],
            ],
        ),
        "<nonterminal>": Parse.Backtracking.generate_nonterminal_parser(
            "<nonterminal>",
            [
                [
                    ExpressionTerm('"<"'),
                    ExpressionTerm("identifier"),
                    ExpressionTerm('">"'),
                ],
            ],
        ),
        "<body>": Parse.Backtracking.generate_nonterminal_parser(
            "<body>",
            [
                [
                    ExpressionTerm("<expression>"),
                    ExpressionTerm("<body>:1", "*"),
                ],
            ],
        ),
        "<body>:1": Parse.Backtracking.generate_nonterminal_parser(
            "<body>:1",
            [
                [
                    ExpressionTerm('"|"'),
                    ExpressionTerm("<expression>"),
                ],
            ],
        ),
        "<expression>": Parse.Backtracking.generate_nonterminal_parser(
            "<expression>",
            [
                [
                    ExpressionTerm("<term>", "+"),
                ],
            ],
        ),
        "<term>": Parse.Backtracking.generate_nonterminal_parser(
            "<term>",
            [
                [
                    ExpressionTerm("<term>:0", "?"),
                    ExpressionTerm("<group>"),
                    ExpressionTerm("<multiplicity>", "?"),
                ],
            ],
        ),
        "<term>:0": Parse.Backtracking.generate_nonterminal_parser(
            "<term>:0",
            [
                [
                    ExpressionTerm("<label>"),
                    ExpressionTerm('"="'),
                ],
            ],
        ),
        "<group>": Parse.Backtracking.generate_nonterminal_parser(
            "<group>",
            [
                [ExpressionTerm("<item>")],
                [
                    ExpressionTerm('"("'),
                    ExpressionTerm("<body>"),
                    ExpressionTerm('")"'),
                ],
            ],
        ),
        "<item>": Parse.Backtracking.generate_nonterminal_parser(
            "<item>",
            [
                [ExpressionTerm("<nonterminal>")],
                [ExpressionTerm("<terminal>")],
            ],
        ),
        "<terminal>": Parse.Backtracking.generate_nonterminal_parser(
            "<terminal>",
            [
                [ExpressionTerm("escaped_string")],
                [ExpressionTerm("regex")],
                [ExpressionTerm("identifier")],
            ],
        ),
        "<multiplicity>": Parse.Backtracking.generate_nonterminal_parser(
            "<multiplicity>",
            [
                [ExpressionTerm('"?"')],
                [ExpressionTerm('"*"')],
                [ExpressionTerm('"+"')],
            ],
        ),
        "<label>": Parse.Backtracking.generate_alias_parser(
            "<label>",
            "identifier",
        ),
        **Parse.Backtracking.generate_parsers_from_vocabulary(vocabulary),
    }

    grammar: Grammar = Grammar(
        "xbnf",
        rules=rules,
        nrules=nrules,
    )


class GenerateNodeParsers(Visitor):
    def __init__(self):
        super().__init__()

        # todo: this is ugly, move to call stack
        self._lhs_stack: list[str] = []
        self._idx_stack: list[int] = []
        self._used: set[str] = set()

        self._node_parsers: dict[str, NodeParser] = {}

    def _visit_xbnf(self, n: ASTNode) -> dict[str, NodeParser]:
        # entry point is used
        self._used.add(f"<{n[0][0][1].lexeme}>")
        self._builtin_visit_all(n)

        for node_type in self._used:
            if node_type not in self._node_parsers:
                # todo: assert node_type is a nontemrinal
                error: ValueError = ValueError(
                    f"no productions defined for {node_type}"
                )
                if not Log.ef(
                    f"[red]ValueError:[/red] no productions defined for {node_type}"
                ):
                    raise error

        # todo: analyze tree from entry nonterminal to determine disconnected components
        # todo: currently this does not detect <x> ::= <y>; <y> ::= <x>;
        for node_type in self._node_parsers:
            Log.w(
                f"parsers are generated for {node_type} but not used",
                node_type not in self._used,
                tag="Grammar",
            )

        return self._node_parsers

    def _add_terminal(self, terminal: str) -> None:
        if terminal not in self._node_parsers:
            self._used.add(terminal)
            self._node_parsers[terminal] = Parse.generate_terminal_parser(terminal)

    def _add_alias(self, alias: str, terminal: str) -> None:
        if alias not in self._node_parsers:
            self._node_parsers[alias] = Parse.generate_alias_parser(alias, terminal)
        else:
            Log.w(
                f"multiple alias definitions for {alias} are disregarded",
                tag="Grammar",
            )

    def _add_nonterminal(
        self, nonterminal: str, body: list[list[ExpressionTerm]]
    ) -> None:
        if nonterminal not in self._node_parsers:
            self._node_parsers[nonterminal] = Parse.generate_nonterminal_parser(
                nonterminal, body
            )
        else:
            Log.w(
                f"multiple production definitions for {nonterminal} are disregarded",
                tag="Grammar",
            )

    def _visit_production(
        self,
        n: ASTNode,
    ) -> Any:
        nonterminal: str = f"<{n[0][1].lexeme}>"

        self._lhs_stack.append(nonterminal)
        self._idx_stack.append(0)

        # not using extend => force 1 production definition for each nonterminal
        self._add_nonterminal(nonterminal, self(n[2]))

        self._idx_stack.pop()
        self._lhs_stack.pop()

    def _visit_alias(
        self,
        n: ASTNode,
    ) -> Any:
        alias: str = f"<{n[1][1].lexeme}>"

        self._add_alias(alias, self(n[3]))

    def _visit_body(
        self,
        n: ASTNode,
    ) -> list[list[ExpressionTerm]]:
        productions: list[list[ExpressionTerm]] = []

        # only 1 production
        if len(n[1]) == 0:
            # node[0]: <expression>
            productions.append(self(n[0]))

        # multiple productions
        else:

            auxiliary_nonterminal = f"{self._lhs_stack[-1]}~{self._idx_stack[-1]}"
            self._lhs_stack.append(auxiliary_nonterminal)
            self._idx_stack.append(0)

            # node[0]: <expression>
            productions.append(self(n[0]))

            self._idx_stack.pop()
            self._lhs_stack.pop()
            self._idx_stack[-1] += 1

        # node[1]: ("\|" <expression>)*
        # or_production: "\|" <expression>
        for or_production in n[1]:
            auxiliary_nonterminal = f"{self._lhs_stack[-1]}~{self._idx_stack[-1]}"
            self._lhs_stack.append(auxiliary_nonterminal)
            self._idx_stack.append(0)

            # or_production[1]: <expression>
            productions.append(self(or_production[1]))

            self._idx_stack.pop()
            self._lhs_stack.pop()
            self._idx_stack[-1] += 1

        return productions

    def _visit_expression(
        self,
        n: ASTNode,
    ) -> list[ExpressionTerm]:
        ret = []

        # node[0]: <term>+
        # <term>: (<label> "=")? <group> <multiplicity>?
        for term in n[0]:
            label: Optional[str] = None
            optional_label: NonterminalASTNode = term[0]

            if optional_label:
                label = optional_label[0][0].lexeme

            # multiplicity: <multiplicity>?
            optional_multiplicity: NonterminalASTNode = term[2]

            multiplicity: str
            # default multiplicity is 1
            if not optional_multiplicity:
                multiplicity = ""

            else:
                multiplicity = self(optional_multiplicity[0])

            # expression_term[1]: <group>
            group: str = self(term[1])

            ret.append(ExpressionTerm(group, multiplicity, label))

        return ret

    def _visit_group(
        self,
        n: ASTNode,
    ) -> str:
        match n.choice:
            # node: <item>
            case 0:
                # term: <nonterminal> | <terminal>
                term = n[0]

                self._idx_stack[-1] += 1

                return self(term)

            # node: "\(" <body> "\)"
            case 1:
                auxiliary_nonterminal = f"{self._lhs_stack[-1]}:{self._idx_stack[-1]}"
                self._lhs_stack.append(auxiliary_nonterminal)
                self._idx_stack.append(0)
                self._used.add(auxiliary_nonterminal)

                # node[1]: <body>
                self._add_nonterminal(auxiliary_nonterminal, self(n[1]))

                self._idx_stack.pop()
                self._lhs_stack.pop()
                self._idx_stack[-1] += 1

                return auxiliary_nonterminal

    def _visit_nonterminal(
        self,
        n: ASTNode,
    ) -> str:
        nonterminal: str = f"<{n[1].lexeme}>"
        self._used.add(nonterminal)
        return nonterminal

    def _visit_terminal(
        self,
        n: ASTNode,
    ) -> str:
        terminal: str = n[0].lexeme
        self._add_terminal(terminal)
        return terminal

    def _visit_multiplicity(
        self,
        n: ASTNode,
    ) -> str:
        return n[0].lexeme


class GenerateRules(Visitor):
    def __init__(self):
        super().__init__()

        # todo: this is ugly, move to call stack
        self._lhs_stack: list[str] = []
        self._idx_stack: list[int] = []
        self._used: set[str] = set()

        self._rules: Rules = {}

    def _visit_xbnf(self, n: ASTNode) -> Rules:
        self._builtin_visit_all(n)
        return self._rules

    def _visit_production(
        self,
        n: ASTNode,
    ) -> None:
        nonterminal: str = f"<{n[0][1].lexeme}>"

        self._lhs_stack.append(nonterminal)
        self._idx_stack.append(0)

        self._rules[nonterminal] = self(n[2])

        self._idx_stack.pop()
        self._lhs_stack.pop()

    def _visit_alias(
        self,
        n: ASTNode,
    ) -> None:
        alias: str = f"<{n[1][1].lexeme}>"
        self._rules[alias] = Alias(self(n[3]))

    def _visit_body(
        self,
        n: ASTNode,
    ) -> Production:
        productions: Production = Production()

        # only 1 production
        if len(n[1]) == 0:
            # node[0]: <expression>
            productions.append(self(n[0]))

        # multiple productions
        else:

            auxiliary_nonterminal = f"{self._lhs_stack[-1]}~{self._idx_stack[-1]}"
            self._lhs_stack.append(auxiliary_nonterminal)
            self._idx_stack.append(0)

            # node[0]: <expression>
            productions.append(self(n[0]))

            self._idx_stack.pop()
            self._lhs_stack.pop()
            self._idx_stack[-1] += 1

        # node[1]: ("\|" <expression>)*
        # or_production: "\|" <expression>
        for or_production in n[1]:
            auxiliary_nonterminal = f"{self._lhs_stack[-1]}~{self._idx_stack[-1]}"
            self._lhs_stack.append(auxiliary_nonterminal)
            self._idx_stack.append(0)

            # or_production[1]: <expression>
            productions.append(self(or_production[1]))

            self._idx_stack.pop()
            self._lhs_stack.pop()
            self._idx_stack[-1] += 1

        return productions

    def _visit_expression(
        self,
        n: ASTNode,
    ) -> Expression:
        ret: Expression = Expression()

        # node[0]: <term>+
        # <term>: (<label> "=")? <group> <multiplicity>?
        for term in n[0]:
            label: Optional[str] = None
            optional_label: NonterminalASTNode = term[0]

            if optional_label:
                label = optional_label[0][0].lexeme

            # multiplicity: <multiplicity>?
            optional_multiplicity: NonterminalASTNode = term[2]

            multiplicity: str
            # default multiplicity is 1
            if not optional_multiplicity:
                multiplicity = ""

            else:
                multiplicity = self(optional_multiplicity[0])

            # expression_term[1]: <group>
            group: str = self(term[1])

            ret.append(ExpressionTerm(group, multiplicity, label))

        return ret

    def _visit_group(
        self,
        n: ASTNode,
    ) -> str:
        match n.choice:
            # node: <item>
            case 0:
                # term: <nonterminal> | <terminal>
                term = n[0]
                self._idx_stack[-1] += 1
                return self(term)

            # node: "\(" <body> "\)"
            case 1:
                auxiliary_nonterminal = f"{self._lhs_stack[-1]}:{self._idx_stack[-1]}"
                self._lhs_stack.append(auxiliary_nonterminal)
                self._idx_stack.append(0)

                # node[1]: <body>
                self._rules[auxiliary_nonterminal] = self(n[1])

                self._idx_stack.pop()
                self._lhs_stack.pop()
                self._idx_stack[-1] += 1

                return auxiliary_nonterminal

    def _visit_nonterminal(
        self,
        n: ASTNode,
    ) -> str:
        nonterminal: str = f"<{n[1].lexeme}>"
        return nonterminal

    def _visit_terminal(
        self,
        n: ASTNode,
    ) -> str:
        terminal: str = n[0].lexeme
        return terminal

    def _visit_multiplicity(
        self,
        n: ASTNode,
    ) -> str:
        return n[0].lexeme


class NGenerateRules(Visitor):
    def __init__(self):
        super().__init__()

        # todo: this is ugly, move to call stack
        self._lhs_stack: list[str] = []
        self._idx_stack: list[int] = []
        self._used: set[str] = set()

        self._rules: NRules = NRules()

    def _visit_xbnf(self, n: ASTNode) -> NRules:
        self._builtin_visit_all(n)
        return self._rules

    def _visit_production(
        self,
        n: ASTNode,
    ) -> None:
        nonterminal: str = f"<{n[0][1].lexeme}>"

        self._lhs_stack.append(nonterminal)
        self._idx_stack.append(0)

        self._rules[nonterminal] = self(n[2])

        self._idx_stack.pop()
        self._lhs_stack.pop()

    def _visit_alias(
        self,
        n: ASTNode,
    ) -> None:
        alias: str = f"<{n[1][1].lexeme}>"
        self._rules[alias] = NAlias(self(n[3]))

    def _visit_body(
        self,
        n: ASTNode,
    ) -> NProduction:
        productions: NProduction = NProduction()

        # only 1 production
        if len(n[1]) == 0:
            # node[0]: <expression>
            productions.append(self(n[0]))

        # multiple productions
        else:

            auxiliary_nonterminal = f"{self._lhs_stack[-1]}~{self._idx_stack[-1]}"
            self._lhs_stack.append(auxiliary_nonterminal)
            self._idx_stack.append(0)

            # node[0]: <expression>
            productions.append(self(n[0]))

            self._idx_stack.pop()
            self._lhs_stack.pop()
            self._idx_stack[-1] += 1

        # node[1]: ("\|" <expression>)*
        # or_production: "\|" <expression>
        for or_production in n[1]:
            auxiliary_nonterminal = f"{self._lhs_stack[-1]}~{self._idx_stack[-1]}"
            self._lhs_stack.append(auxiliary_nonterminal)
            self._idx_stack.append(0)

            # or_production[1]: <expression>
            productions.append(self(or_production[1]))

            self._idx_stack.pop()
            self._lhs_stack.pop()
            self._idx_stack[-1] += 1

        return productions

    def _visit_expression(
        self,
        n: ASTNode,
    ) -> NExpression:
        ret: NExpression = NExpression()

        # node[0]: <term>+
        # <term>: (<label> "=")? <group> <multiplicity>?
        for term in n[0]:
            label: Optional[str] = None
            optional_label: NonterminalASTNode = term[0]

            if optional_label:
                label = optional_label[0][0].lexeme

            # multiplicity: <multiplicity>?
            optional_multiplicity: NonterminalASTNode = term[2]

            multiplicity: str
            # default multiplicity is 1
            if not optional_multiplicity:
                multiplicity = ""

            else:
                multiplicity = self(optional_multiplicity[0])

            # expression_term[1]: <group>
            group: str = self(term[1])

            match multiplicity:
                case "":
                    ret.append(NExpressionTerm(group, label))

                case "?":
                    self._rules[f"{group}?"] = NProduction(
                        [
                            NExpression([NExpressionTerm(group)]),
                            NExpression([NExpressionTerm("e")]),
                        ]
                    )
                    ret.append(NExpressionTerm(f"{group}?", label))

                case "+":
                    self._rules[f"{group}+"] = NProduction(
                        [
                            NExpression(
                                [NExpressionTerm(group), NExpressionTerm(f"{group}+")]
                            ),
                            NExpression([NExpressionTerm(group)]),
                        ]
                    )
                    ret.append(NExpressionTerm(f"{group}+", label))

                case "*":
                    self._rules[f"{group}+"] = NProduction(
                        [
                            NExpression(
                                [NExpressionTerm(group), NExpressionTerm(f"{group}+")]
                            ),
                            NExpression([NExpressionTerm(group)]),
                        ]
                    )
                    self._rules[f"{group}*"] = NProduction(
                        [
                            NExpression([NExpressionTerm("e")]),
                            NExpression([NExpressionTerm(f"{group}+")]),
                        ]
                    )
                    ret.append(NExpressionTerm(f"{group}*", label))

                case _:
                    assert False

        return ret

    def _visit_group(
        self,
        n: ASTNode,
    ) -> str:
        match n.choice:
            # node: <item>
            case 0:
                # term: <nonterminal> | <terminal>
                term = n[0]
                self._idx_stack[-1] += 1
                return self(term)

            # node: "\(" <body> "\)"
            case 1:
                auxiliary_nonterminal = f"{self._lhs_stack[-1]}:{self._idx_stack[-1]}"
                self._lhs_stack.append(auxiliary_nonterminal)
                self._idx_stack.append(0)

                # node[1]: <body>
                self._rules[auxiliary_nonterminal] = self(n[1])

                self._idx_stack.pop()
                self._lhs_stack.pop()
                self._idx_stack[-1] += 1

                return auxiliary_nonterminal

    def _visit_nonterminal(
        self,
        n: ASTNode,
    ) -> str:
        nonterminal: str = f"<{n[1].lexeme}>"
        return nonterminal

    def _visit_terminal(
        self,
        n: ASTNode,
    ) -> str:
        terminal: str = n[0].lexeme
        return terminal

    def _visit_multiplicity(
        self,
        n: ASTNode,
    ) -> str:
        return n[0].lexeme

from __future__ import annotations
from collections import defaultdict
from typing import DefaultDict, Any

from common import Monad, Log, ListSet, fixed_point
from lexical import Vocabulary, Lex

from .ast import ASTNode, NonterminalASTNode
from .parser import Parse, Term
from .visitor import Visitor

Expression = list[Term]


class Production(list[Expression]): ...


class Alias(Term): ...


Rule = Production | Alias

Rules = dict[str, Rule]


class Grammar:
    @classmethod
    def from_xbnf(cls, name: str, xbnf: str, ignore: list[str] = []) -> Grammar:
        ast: ASTNode = Monad(xbnf).then(Lex.for_lang(XBNF)).then(Parse.for_lang(XBNF)).v
        rules: Rules = GenerateRules()(ast)
        return cls(name, rules, ignore=ignore)

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
            match rule:
                case Production():
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
                case Alias(node_type=node_type):
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

    def _generate_node_parsers(self) -> None:
        self._node_parsers: dict[str, Parse.Backtracking.NodeParser] = {}

        for nonterminal in self._rules:
            rule: Rule = self._rules[nonterminal]
            match rule:
                case Production():
                    self._node_parsers[nonterminal] = (
                        Parse.Backtracking.generate_nonterminal_parser(
                            nonterminal, rule
                        )
                    )

                case Alias(node_type=node_type):
                    self._node_parsers[nonterminal] = (
                        Parse.Backtracking.generate_alias_parser(nonterminal, node_type)
                    )

                case _:  # pragma: no cover
                    assert False

        self._node_parsers.update(
            Parse.Backtracking.generate_parsers_from_vocabulary(self._vocabulary)
        )

    # todo: clean up
    def _check_ll1(self) -> None:
        eq = (
            lambda a, b: all(k in b for k in a)
            and all(k in a for k in b)
            and all(a[k] == b[k] for k in a)
        )

        def cp(r):
            f = defaultdict(lambda: ListSet())
            for k in r:
                f[k] = ListSet(r[k])
            return f

        first: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
        for terminal in self._vocabulary:
            first[terminal].add(terminal)
        for nonterminal in self._rules:
            rule: Rule = self._rules[nonterminal]
            if type(rule) is Alias:
                first[nonterminal].add(rule.node_type)

        def iterate_first(cur):
            nxt = cp(cur)
            for nonterminal in self._rules:
                rule = self._rules[nonterminal]
                if type(rule) is Production:
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
            cur = cp(cur)  # prevent side effects to the original cur
            nxt = cp(cur)
            for nonterminal in self._rules:
                rule = self._rules[nonterminal]
                if type(rule) is Production:
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
            dict[str, int | None],
        ] = defaultdict(lambda: {})

        self._is_ll1 = True
        for nonterminal in self._rules:
            rule = self._rules[nonterminal]
            if type(rule) is Production:
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
    rules = Rules(
        [
            (
                "<xbnf>",
                Production(
                    [[Term("<production>"), Term("<rule>*")]],
                ),
            ),
            (
                "<rule>*",
                Production(
                    [
                        [Term("<rule>"), Term("<rule>*")],
                        [Term("e")],
                    ],
                ),
            ),
            (
                "<rule>",
                Production(
                    [
                        [Term("<production>")],
                        [Term("<alias>")],
                    ],
                ),
            ),
            (
                "<production>",
                Production(
                    [
                        [
                            Term("<nonterminal>"),
                            Term('"::="'),
                            Term("<body>"),
                            Term('";"'),
                        ],
                    ],
                ),
            ),
            (
                "<alias>",
                Production(
                    [
                        [
                            Term('"alias"'),
                            Term("<nonterminal>"),
                            Term('"::="'),
                            Term("<terminal>"),
                            Term('";"'),
                        ],
                    ],
                ),
            ),
            (
                "<nonterminal>",
                Production(
                    [
                        [
                            Term('"<"'),
                            Term("identifier"),
                            Term('">"'),
                        ],
                    ],
                ),
            ),
            (
                "<body>",
                Production(
                    [
                        [
                            Term("<expression>"),
                            Term("<body>:1*"),
                        ],
                    ],
                ),
            ),
            (
                "<body>:1*",
                Production(
                    [
                        [Term("<body>:1"), Term("<body>:1*")],
                        [Term("e")],
                    ],
                ),
            ),
            (
                "<body>:1",
                Production(
                    [
                        [
                            Term('"|"'),
                            Term("<expression>"),
                        ],
                    ],
                ),
            ),
            (
                "<expression>",
                Production(
                    [
                        [
                            Term("<term>+"),
                        ],
                    ],
                ),
            ),
            (
                "<term>*",
                Production(
                    [
                        [Term("<term>"), Term("<term>*")],
                        [Term("e")],
                    ],
                ),
            ),
            (
                "<term>+",
                Production(
                    [
                        [Term("<term>"), Term("<term>*")],
                    ],
                ),
            ),
            (
                "<term>",
                Production(
                    [
                        [
                            Term("<term>:0?"),
                            Term("<group>"),
                            Term("<multiplicity>?"),
                        ],
                    ],
                ),
            ),
            (
                "<term>:0?",
                Production(
                    [
                        [Term("<term>:0")],
                        [Term("e")],
                    ],
                ),
            ),
            (
                "<term>:0",
                Production(
                    [
                        [
                            Term("<label>"),
                            Term('"="'),
                        ],
                    ],
                ),
            ),
            (
                "<group>",
                Production(
                    [
                        [Term("<item>")],
                        [
                            Term('"("'),
                            Term("<body>"),
                            Term('")"'),
                        ],
                    ],
                ),
            ),
            (
                "<item>",
                Production(
                    [
                        [Term("<nonterminal>")],
                        [Term("<terminal>")],
                    ],
                ),
            ),
            (
                "<terminal>",
                Production(
                    [
                        [Term("escaped_string")],
                        [Term("regex")],
                        [Term("identifier")],
                    ],
                ),
            ),
            (
                "<multiplicity>?",
                Production(
                    [
                        [Term("<multiplicity>")],
                        [Term("e")],
                    ],
                ),
            ),
            (
                "<multiplicity>",
                Production(
                    [
                        [Term('"?"')],
                        [Term('"*"')],
                        [Term('"+"')],
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

    grammar: Grammar = Grammar(
        "xbnf",
        rules=rules,
    )


class GenerateRules(Visitor):
    def __init__(self):
        super().__init__()

        # todo: this is ugly, move to call stack
        self._lhs_stack: list[str] = []
        self._idx_stack: list[int] = []
        self._used: set[str] = set()

        self._rules: Rules = Rules()

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
            label: str | None = None
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
                    ret.append(Term(group, label))

                case "?":
                    self._rules[f"{group}?"] = Production(
                        [
                            Expression([Term(group)]),
                            Expression([Term("e")]),
                        ]
                    )
                    ret.append(Term(f"{group}?", label))

                case "*":
                    self._rules[f"{group}*"] = Production(
                        [
                            Expression([Term(group), Term(f"{group}*")]),
                            Expression([Term("e")]),
                        ]
                    )
                    ret.append(Term(f"{group}*", label))

                case "+":
                    self._rules[f"{group}*"] = Production(
                        [
                            Expression([Term(group), Term(f"{group}*")]),
                            Expression([Term("e")]),
                        ]
                    )
                    self._rules[f"{group}+"] = Production(
                        [
                            Expression([Term(group), Term(f"{group}*")]),
                        ]
                    )
                    ret.append(Term(f"{group}+", label))

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

            case _:  # pragma: no cover
                assert False

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

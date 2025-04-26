from __future__ import annotations
from typing import Any, Callable

from common import Monad, sjoin, sjoinv, Mutable
from lexical import Lex, Vocabulary
from syntax import (
    Grammar,
    Parse,
    ASTNode,
    Visitor,
    NonterminalASTNode,
)

from ..lang import Lang


class XBNF(Lang):
    name = "xbnf"

    @staticmethod
    def _prod(*expressions: Grammar.Expression) -> Grammar.Production:
        return Grammar.Production(expressions)

    @staticmethod
    def _expr(*terms: str | tuple[str, str]) -> Grammar.Expression:
        expr_terms: list[Grammar.Term] = []
        for term in terms:
            match term:
                case (label, node_type):
                    expr_terms.append(Grammar.Term(node_type, label))

                case node_type:
                    expr_terms.append(Grammar.Term(node_type))

        return Grammar.Expression(expr_terms)

    rules = Grammar.Rules(
        [
            ("<xbnf>", _prod(_expr("<production>", "<rule>*"))),
            ("<rule>*", _prod(_expr("<rule>", "<rule>*"), _expr("e"))),
            ("<rule>", _prod(_expr("<production>"), _expr("<alias>"))),
            ("<production>", _prod(_expr("<nonterminal>", '"::="', "<body>", '";"'))),
            (
                "<alias>",
                _prod(_expr('"alias"', "<nonterminal>", '"::="', "<terminal>", '";"')),
            ),
            ("<nonterminal>", _prod(_expr('"<"', "identifier", '">"'))),
            ("<body>", _prod(_expr(("first", "<expression>"), ("rest", "<body>:1*")))),
            ("<body>:1*", _prod(_expr("<body>:1", "<body>:1*"), _expr("e"))),
            ("<body>:1", _prod(_expr('"|"', "<expression>"))),
            ("<expression>", _prod(_expr("<term>+"))),
            ("<term>*", _prod(_expr("<term>", "<term>*"), _expr("e"))),
            ("<term>+", _prod(_expr("<term>", "<term>*"))),
            ("<term>", _prod(_expr("<term>:0?", "<group>", "<multiplicity>?"))),
            ("<term>:0?", _prod(_expr("<term>:0"), _expr("e"))),
            ("<term>:0", _prod(_expr("<label>", '"="'))),
            ("<group>", _prod(_expr("<item>"), _expr('"("', "<body>", '")"'))),
            ("<item>", _prod(_expr("<nonterminal>"), _expr("<terminal>"))),
            (
                "<terminal>",
                _prod(_expr("escaped_string"), _expr("regex"), _expr("identifier")),
            ),
            ("<multiplicity>?", _prod(_expr("<multiplicity>"), _expr("e"))),
            ("<multiplicity>", _prod(_expr('"?"'), _expr('"*"'), _expr('"+"'))),
            ("<label>", Grammar.Alias("identifier")),
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

    generate_rules: Callable[[ASTNode], Grammar.Rules]

    class Parse:
        def __init__(self, entry_point: str | None = None) -> None:
            self._lex = Lex.for_lang(XBNF)
            self._parse = Parse.for_lang(XBNF, entry_point=entry_point)

        def __call__(self, prog: str) -> ASTNode:
            return Monad(prog).then(self._lex).then(self._parse).v

    class Shake(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_body(self, n: ASTNode) -> ASTNode:
            return Visitor.flatten(self, n)

    class Print(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all("".join),
                default_terminal_node_visitor=lambda _, n: n.lexeme,
            )

        def _visit_xbnf(self, n: ASTNode) -> str:
            return sjoinv(self(n[0]), self._builtin_visit_all(n[1], sjoin))

        def _visit_production(self, n: ASTNode) -> str:
            nonterminal: str = self(n[0])
            expressions: list[str] = list(self(c) for c in n[2])
            ret: str = f"{nonterminal} ::= {' | '.join(expressions)};"
            if len(ret) > 80:
                lines: list[str] = []
                idx: int = 0
                while idx < len(expressions):
                    line: str = f"  {expressions[idx]}"
                    idx += 1
                    while (
                        idx < len(expressions)
                        and len(line)
                        + 3
                        + len(expressions[idx])
                        + (1 if idx == len(expressions) - 1 else 2)
                        <= 80
                    ):
                        line += f" | {expressions[idx]}"
                        idx += 1
                    line += ";" if idx == len(expressions) else " |"
                    lines.append(line)
                double_nl: str = "\n\n"
                return f"{nonterminal} ::=\n\n{double_nl.join(lines)}"
            else:
                return ret

        def _visit_alias(self, n: ASTNode) -> str:
            return f"alias {self(n[1])} ::= {self(n[3])};"

        def _visit_body(self, n: ASTNode) -> str:
            return self._builtin_visit_all(n, " | ".join)

        def _visit_expression(self, n: ASTNode) -> str:
            return self._builtin_visit_all(n[0], " ".join)

    class GenerateRules(Visitor):
        def __init__(self):
            super().__init__()

        def _visit_xbnf(self, n: ASTNode, **ctx: Any) -> Grammar.Rules:
            self._rules: Grammar.Rules = Grammar.Rules()
            self._builtin_visit_all(n, **ctx)
            return self._rules

        def _visit_production(self, n: ASTNode, **_: Any) -> None:
            nonterminal: str = f"<{n[0][1].lexeme}>"
            self._rules[nonterminal] = self(n[2], lhs=nonterminal, idx=0)

        def _visit_alias(self, n: ASTNode, **ctx: Any) -> None:
            alias: str = f"<{n[1][1].lexeme}>"
            self._rules[alias] = Grammar.Alias(self(n[3], **ctx))

        def _visit_body(
            self, n: ASTNode, lhs: str, idx: Mutable[int]
        ) -> Grammar.Production:
            productions: Grammar.Production = Grammar.Production()

            # only 1 production
            if len(n[1]) == 0:
                # node[0]: <expression>
                productions.append(self(n[0], lhs=lhs, idx=Mutable(0)))

            # multiple productions
            else:

                aux_nonterminal = f"{lhs}~{idx}"

                # node[0]: <expression>
                productions.append(self(n[0], lhs=aux_nonterminal, idx=Mutable(0)))
                idx += 1

            # node[1]: ("\|" <expression>)*
            # or_production: "\|" <expression>
            for or_production in n[1]:
                aux_nonterminal = f"{lhs}~{idx}"

                # or_production[1]: <expression>
                productions.append(
                    self(or_production[1], lhs=aux_nonterminal, idx=Mutable(0))
                )
                idx += 1

            return productions

        def _visit_expression(self, n: ASTNode, **ctx: Any) -> Grammar.Expression:
            expr: Grammar.Expression = Grammar.Expression()

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
                    multiplicity = self(optional_multiplicity[0], **ctx)

                # expression_term[1]: <group>
                group: str = self(term[1], **ctx)

                match multiplicity:
                    case "":
                        expr.append(Grammar.Term(group, label))

                    case "?":
                        self._rules[f"{group}?"] = Grammar.Production(
                            [
                                Grammar.Expression([Grammar.Term(group)]),
                                Grammar.Expression([Grammar.Term("e")]),
                            ]
                        )
                        expr.append(Grammar.Term(f"{group}?", label))

                    case "*":
                        self._rules[f"{group}*"] = Grammar.Production(
                            [
                                Grammar.Expression(
                                    [Grammar.Term(group), Grammar.Term(f"{group}*")]
                                ),
                                Grammar.Expression([Grammar.Term("e")]),
                            ]
                        )
                        expr.append(Grammar.Term(f"{group}*", label))

                    case "+":
                        self._rules[f"{group}*"] = Grammar.Production(
                            [
                                Grammar.Expression(
                                    [Grammar.Term(group), Grammar.Term(f"{group}*")]
                                ),
                                Grammar.Expression([Grammar.Term("e")]),
                            ]
                        )
                        self._rules[f"{group}+"] = Grammar.Production(
                            [
                                Grammar.Expression(
                                    [Grammar.Term(group), Grammar.Term(f"{group}*")]
                                )
                            ]
                        )
                        expr.append(Grammar.Term(f"{group}+", label))

                    case _:
                        assert False

            return expr

        def _visit_group(self, n: ASTNode, lhs: str, idx: Mutable[int]) -> str:
            match n.choice:
                # node: <item>
                case 0:
                    # term: <nonterminal> | <terminal>
                    term = n[0]
                    idx += 1
                    return self(term)

                # node: "\(" <body> "\)"
                case 1:
                    aux_nonterminal = f"{lhs}:{idx}"

                    # node[1]: <body>
                    self._rules[aux_nonterminal] = self(
                        n[1], lhs=aux_nonterminal, idx=Mutable(0)
                    )
                    idx += 1

                    return aux_nonterminal

                case _:  # pragma: no cover
                    assert False

        def _visit_nonterminal(self, n: ASTNode, **_: Any) -> str:
            nonterminal: str = f"<{n[1].lexeme}>"
            return nonterminal

        def _visit_terminal(self, n: ASTNode, **_: Any) -> str:
            terminal: str = n[0].lexeme
            return terminal

        def _visit_multiplicity(self, n: ASTNode, **_: Any) -> str:
            return n[0].lexeme


XBNF.parse = XBNF.Parse()
XBNF.shake = XBNF.Shake()
XBNF.print = XBNF.Print()

XBNF.generate_rules = XBNF.GenerateRules()


def grammar_from_xbnf(name: str, xbnf: str, ignore: list[str] = []) -> Grammar:
    return Grammar(
        name, Monad(xbnf).then(XBNF.parse).then(XBNF.generate_rules).v, ignore=ignore
    )


Grammar.from_xbnf = grammar_from_xbnf


# todo: delete
from common import load

# g = Grammar.from_xbnf("star", '<star> ::= <thing>*; <thing> ::= "a";')
# Monad("a a a").then(Lex.for_grammar(g)).then(Parse.for_grammar(g)).then(print)
# Parse.for_grammar(Grammar.from_xbnf("A", load("A.xbnf")))
# Parse.for_grammar(Grammar.from_xbnf("B", load("B.xbnf")))

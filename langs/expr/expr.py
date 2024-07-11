from __future__ import annotations
from typing import Callable

from common import Monad, load
from lexical import Lex
from syntax import (
    Grammar,
    Parse,
    ASTNode,
    Visitor,
    NonterminalASTNode,
)

from ..lang import Lang


class Expr(Lang):
    name = "expr"
    grammar = Grammar.from_xbnf(
        name, load("langs/expr/spec/expr.xbnf"), ignore=["#[^\n]*"]
    )

    class Parse:
        def __init__(self, entry_point: str | None = None) -> None:
            self._lex = Lex.for_lang(Expr)
            self._parse = Parse.for_lang(Expr, entry_point=entry_point)

        def __call__(self, prog: str) -> ASTNode:
            return Monad(prog).then(self._lex).then(self._parse).v

    class Shake(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_expr(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<expr>")
            n_.add(self(n.first))
            for c in n.rest:
                c_ = self(c)
                n_.add(c_[0])
                n_.add(c_[1])
            return n_

        def _visit_term(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<term>")
            n_.add(self(n.first))
            for c in n.rest:
                c_ = self(c)
                n_.add(c_[0])
                n_.add(c_[1])
            return n_

    class Print(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all(" ".join),
                default_terminal_node_visitor=lambda _, n: n.lexeme,
            )

        def _visit_factor(self, n: ASTNode) -> str:
            match n.choice:
                case 0:
                    return f"({self(n[1])})"
                case 1:
                    return self(n[0])
                case _:  # pragma: no cover
                    assert False


Expr.parse = Expr.Parse()
Expr.shake = Expr.Shake()
Expr.print = Expr.Print()

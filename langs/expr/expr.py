from __future__ import annotations
from typing import Optional, Callable

from common import Monad, load
from lexical import Lex
from syntax import (
    Grammar,
    Parse,
    ASTNode,
    Visitor,
)
from syntax.ast import NonterminalASTNode
from syntax.visitor import NonterminalASTNodeVisitor

from ..lang import Lang


class Expr(Lang):
    grammar: Grammar = Grammar.from_xbnf(
        "expr", load("langs/expr/spec/expr.xbnf"), ignore=["#[^\n]*"]
    )

    parse: Callable[[str], ASTNode]
    print: Callable[[ASTNode], str]

    class Parse:
        def __init__(self, entry_point: Optional[str] = None) -> None:
            self._lex = Lex.for_lang(Expr)
            self._parse = Parse.for_lang(Expr, entry_point=entry_point)

        def __call__(self, prog: str) -> ASTNode:
            return Monad(prog).then(self._lex).then(self._parse).v

    class BuildInternalAST(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_expr(self, n: ASTNode) -> Optional[ASTNode]:
            n_: NonterminalASTNode = NonterminalASTNode("<expr>")
            n_.add(self(n.first))
            for c in n.rest:
                c_ = self(c)
                n_.add(c_[0])
                n_.add(c_[1])
            return n_

        def _visit_term(self, n: ASTNode) -> Optional[ASTNode]:
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


Expr.parse = Monad.F(Expr.Parse()).then(Expr.BuildInternalAST()).f
Expr.print = Expr.Print()

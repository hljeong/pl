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

from ..lang import Lang


class Expr(Lang):
    grammar: Grammar = Grammar.from_xbnf(
        "expr", load("langs/expr/spec/expr.xbnf"), ignore=["#[^\n]*"]
    )

    parse: Callable[[str], ASTNode]
    build_internal_ast: Callable[[ASTNode], ASTNode]
    print: Callable[[ASTNode], str]

    class Parse:
        def __call__(self, prog: str, entry_point: Optional[str] = None) -> ASTNode:
            return (
                Monad(prog)
                .then(Lex.for_lang(Expr))
                .then(Parse.for_lang(Expr, entry_point=entry_point))
                .value
            )

    class BuildInternalAST(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_ep(self, n: ASTNode) -> Optional[ASTNode]:
            match n.choice:
                case 0:
                    return Visitor.rebuild(self, n)

                case 1:
                    return None

        def _visit_tp(self, n: ASTNode) -> Optional[ASTNode]:
            match n.choice:
                case 0:
                    return Visitor.rebuild(self, n)

                case 1:
                    return None

    class Print(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all(" ".join),
                default_terminal_node_visitor=lambda _, n: n.lexeme,
            )

        def _visit_f(self, n: ASTNode) -> str:
            match n.choice:
                case 0:
                    return f"({self(n[1])})"
                case 1:
                    return self(n[0])
                case _:  # pragma: no cover
                    assert False


Expr.parse = Expr.Parse()
Expr.build_internal_ast = Expr.BuildInternalAST()
Expr.print = Expr.Print()

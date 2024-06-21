from __future__ import annotations
from collections import defaultdict
from typing import Generic

from common import Monad, Log
from lexical import Token

from .ast import TerminalASTNode


class Visitor:
    @staticmethod
    def visit_all(node: NonterminalASTNode, visitor: Visitor) -> Any:
        return tuple(visitor.visit(child) for child in node)

    @staticmethod
    def visit_telescope(node: NonterminalASTNode, visitor: Visitor) -> Any:
        return visitor.visit(Visitor.telescope(node))

    # todo: change to telescope until multiple children?
    @staticmethod
    def telescope(node: NonterminalASTNode) -> TerminalASTNode:
        while type(node) is not TerminalASTNode:
            Log.w(
                f"telescoping node ({node}) with multiple children",
                len(node) > 1,
                tag="Visitor",
            )
            node = node[0]
        return node

    def __init__(
        self,
        node_visitors: dict[str, Callable[[ASTNode, Visitor], Any]],
        default_nonterminal_node_visitor: Callable[
            [NonterminalASTNode], Any
        ] = visit_telescope,
        default_terminal_node_visitor: Callable[
            [TerminalASTNode], Any
        ] = lambda *_: None,
    ):
        self._node_visitors: defaultdict[
            str, Callable[[ASTNode, Any, Visitor], Any]
        ] = defaultdict(
            lambda: lambda node, visitor: (
                default_terminal_node_visitor
                if type(node) is TerminalASTNode
                else default_nonterminal_node_visitor
            )(node, visitor)
        )
        self._node_visitors.update(node_visitors)

    def visit(
        self,
        node: ASTNode,
    ) -> Any:
        return self._node_visitors[node.node_type](node, self)

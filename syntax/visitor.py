from __future__ import annotations
from collections import defaultdict
from typing import cast, Any, Callable, Union

from common import Log
from syntax import ASTNode, NonterminalASTNode, TerminalASTNode

from .ast import ChoiceNonterminalASTNode, TerminalASTNode

TerminalASTNodeVisitor = Callable[[TerminalASTNode], Any]
ChoiceNonterminalASTNodeVisitor = Callable[[ChoiceNonterminalASTNode], Any]
# todo: review
PureNonterminalASTNodeVisitor = Callable[[NonterminalASTNode], Any]
NonterminalASTNodeVisitor = Union[
    PureNonterminalASTNodeVisitor, ChoiceNonterminalASTNodeVisitor
]
AgnosticASTNodeVisitor = Callable[[ASTNode], Any]
ASTNodeVisitor = Union[
    AgnosticASTNodeVisitor, NonterminalASTNodeVisitor, TerminalASTNode
]

# funny little hack because cant use self in default parameter
USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR: NonterminalASTNodeVisitor = (
    lambda _: None
)
DEFAULT_DEFAULT_TERMINAL_AST_NODE_VISITOR: TerminalASTNodeVisitor = lambda _: None


class Visitor:
    @staticmethod
    def visit_all(v: Visitor) -> NonterminalASTNodeVisitor:
        return lambda n: tuple(v.visit(c) for c in n)

    @staticmethod
    def visit_telescope(v: Visitor) -> NonterminalASTNodeVisitor:
        return lambda n: v.visit(Visitor.telescope(n))

    # todo: change to telescope until multiple children?
    @staticmethod
    def telescope(node: NonterminalASTNode) -> TerminalASTNode:
        Log.w(
            f"telescoping node ({node}) with multiple children",
            len(node) > 1,
            tag="Visitor",
        )
        while isinstance(node[0], NonterminalASTNode):
            node = cast(NonterminalASTNode, node[0])
        return cast(TerminalASTNode, node[0])

    def __init__(
        self,
        node_visitors: dict[str, ASTNodeVisitor],
        default_nonterminal_node_visitor: NonterminalASTNodeVisitor = USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR,
        default_terminal_node_visitor: TerminalASTNodeVisitor = DEFAULT_DEFAULT_TERMINAL_AST_NODE_VISITOR,
    ):
        if (
            default_nonterminal_node_visitor
            is USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR
        ):
            default_nonterminal_node_visitor = Visitor.visit_all(self)

        self._node_visitors: defaultdict[str, ASTNodeVisitor] = defaultdict(
            lambda: cast(
                AgnosticASTNodeVisitor,
                lambda n: (
                    default_terminal_node_visitor(cast(TerminalASTNode, n))
                    if isinstance(n, TerminalASTNode)
                    else (
                        cast(
                            ChoiceNonterminalASTNodeVisitor,
                            default_nonterminal_node_visitor,
                        )(cast(ChoiceNonterminalASTNode, n))
                        if isinstance(n, ChoiceNonterminalASTNode)
                        else cast(
                            PureNonterminalASTNodeVisitor,
                            default_nonterminal_node_visitor,
                        )(cast(NonterminalASTNode, n))
                    )
                ),
            )
        )
        self._node_visitors.update(node_visitors)

    def visit(
        self,
        n: ASTNode,
    ) -> Any:
        node_visitor: ASTNodeVisitor = self._node_visitors[n.node_type]
        if isinstance(n, NonterminalASTNode):
            return cast(NonterminalASTNodeVisitor, node_visitor)(n)

        elif isinstance(n, TerminalASTNode):
            return cast(TerminalASTNodeVisitor, node_visitor)(n)

        assert False

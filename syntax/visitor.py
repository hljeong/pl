from __future__ import annotations
from collections import defaultdict
from typing import cast, Any, Callable, Union, Iterable, no_type_check_decorator

from common import Log
from syntax import ASTNode, NonterminalASTNode, TerminalASTNode

from .ast import ChoiceNonterminalASTNode, TerminalASTNode

TerminalASTNodeVisitor = Callable[["Visitor", TerminalASTNode], Any]
ChoiceNonterminalASTNodeVisitor = Callable[["Visitor", ChoiceNonterminalASTNode], Any]
# todo: review
PureNonterminalASTNodeVisitor = Callable[["Visitor", NonterminalASTNode], Any]
NonterminalASTNodeVisitor = Union[
    PureNonterminalASTNodeVisitor, ChoiceNonterminalASTNodeVisitor
]
AgnosticASTNodeVisitor = Callable[["Visitor", ASTNode], Any]
ASTNodeVisitor = Union[
    AgnosticASTNodeVisitor, NonterminalASTNodeVisitor, TerminalASTNode
]

# funny little hack because cant use self in default parameter
USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR: NonterminalASTNodeVisitor = (
    lambda *_: None
)
DEFAULT_DEFAULT_TERMINAL_AST_NODE_VISITOR: TerminalASTNodeVisitor = lambda *_: None


class Visitor:
    # todo: what's class method?
    @staticmethod
    def visit_all(
        combine: Callable[[Iterable[Any]], Any] = tuple
    ) -> NonterminalASTNodeVisitor:
        return lambda v, n: v(n[0]) if len(n) == 1 else combine(v(c) for c in n)

    def _builtin_visit_all(
        self, n: NonterminalASTNode, combine: Callable[[Iterable[Any]], Any] = tuple
    ) -> Any:
        return self(n[0]) if len(n) == 1 else combine(self(c) for c in n)

    def __init__(
        self,
        default_nonterminal_node_visitor: NonterminalASTNodeVisitor = USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR,
        default_terminal_node_visitor: TerminalASTNodeVisitor = DEFAULT_DEFAULT_TERMINAL_AST_NODE_VISITOR,
    ):
        if (
            default_nonterminal_node_visitor
            is USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR
        ):
            default_nonterminal_node_visitor = Visitor._builtin_visit_all

        self._node_visitor: defaultdict[str, ASTNodeVisitor] = defaultdict(
            lambda: cast(
                AgnosticASTNodeVisitor,
                lambda v, n: (
                    default_terminal_node_visitor(v, cast(TerminalASTNode, n))
                    if isinstance(n, TerminalASTNode)
                    else (
                        cast(
                            ChoiceNonterminalASTNodeVisitor,
                            default_nonterminal_node_visitor,
                        )(v, cast(ChoiceNonterminalASTNode, n))
                        if isinstance(n, ChoiceNonterminalASTNode)
                        else cast(
                            PureNonterminalASTNodeVisitor,
                            default_nonterminal_node_visitor,
                        )(v, cast(NonterminalASTNode, n))
                    )
                ),
            ),
            {
                node_visitor[len("_visit_") :]: getattr(self.__class__, node_visitor)
                for node_visitor in dir(self.__class__)
                if callable(getattr(self.__class__, node_visitor))
                and node_visitor.startswith("_visit_")
            },
        )

    def __call__(self, n: ASTNode) -> Any:
        return self[n](self, n)

    def __getitem__(self, n: ASTNode):
        if n.node_type.endswith(">"):
            return self._node_visitor[n.node_type[1:-1]]

        else:
            return self._node_visitor[n.node_type]

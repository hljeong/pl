from __future__ import annotations
from collections import defaultdict
from typing import cast, Any, Callable, Iterable

from syntax import ASTNode, NonterminalASTNode, AliasASTNode, TerminalASTNode

from .ast import TerminalASTNode

# note: kwargs (ctx) not captured in these type aliases
TerminalASTNodeVisitor = Callable[["Visitor", TerminalASTNode], Any]
NonterminalASTNodeVisitor = Callable[["Visitor", NonterminalASTNode], Any]
AgnosticASTNodeVisitor = Callable[["Visitor", ASTNode], Any]
ASTNodeVisitor = AgnosticASTNodeVisitor | NonterminalASTNodeVisitor | TerminalASTNode

# funny little hack because cant use self in default parameter
USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR: NonterminalASTNodeVisitor = (
    lambda *_, **ctx: None
)
DEFAULT_DEFAULT_TERMINAL_AST_NODE_VISITOR: TerminalASTNodeVisitor = (
    lambda *_, **ctx: None
)


class Visitor:
    # todo: what's class method?
    @staticmethod
    def visit_all(
        combine: Callable[[Iterable[Any]], Any] = tuple
    ) -> NonterminalASTNodeVisitor:
        return lambda v, n, **ctx: (
            v(n[0], **ctx) if len(n) == 1 else combine(v(c, **ctx) for c in n)
        )

    @staticmethod
    def rebuild(v: Visitor, n: NonterminalASTNode, **ctx: Any) -> NonterminalASTNode:
        n_: NonterminalASTNode
        match n:
            case NonterminalASTNode(node_type, choice, extras):
                n_ = NonterminalASTNode(node_type, choice=choice, extras=extras)

            case _:  # pragma: no cover
                assert False

        for c in n:
            c_: ASTNode | Iterable[ASTNode] | None = v(c, **ctx)
            match c_:
                case ASTNode():
                    n_.add(c_)

                case Iterable():
                    n_.add_all_(c_)

                case None:
                    pass

                case _:  # pragma: no cover
                    assert False

        return n_

    @staticmethod
    def flatten(v: Visitor, n: NonterminalASTNode, **ctx: Any) -> NonterminalASTNode:
        assert (
            len(n) == 2
            and "name" in n[0].extras
            and "name" in n[1].extras
            and n[0].extras["name"] == "first"
            and n[1].extras["name"] == "rest"
        )

        n_: NonterminalASTNode = NonterminalASTNode(n.node_type)
        n_.add(v(n.first, **ctx))

        for c in n.rest:
            n_.add(v(c[1], **ctx))

        return n_

    def _builtin_visit_all(
        self,
        n: NonterminalASTNode,
        combine: Callable[[Iterable[Any]], Any] = tuple,
        **ctx: Any,
    ) -> Any:
        return self(n[0], **ctx) if len(n) == 1 else combine(self(c, **ctx) for c in n)

    def __init__(
        self,
        default_nonterminal_node_visitor: NonterminalASTNodeVisitor = USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR,
        default_terminal_node_visitor: TerminalASTNodeVisitor = DEFAULT_DEFAULT_TERMINAL_AST_NODE_VISITOR,
    ):
        # todo: get rid of this
        if (
            default_nonterminal_node_visitor
            is USE_DEFAULT_DEFAULT_NONTERMINAL_AST_NODE_VISITOR
        ):
            default_nonterminal_node_visitor = Visitor._builtin_visit_all

        self._node_visitor: defaultdict[str, ASTNodeVisitor] = defaultdict(
            lambda: cast(
                AgnosticASTNodeVisitor,
                lambda v, n, **ctx: (
                    default_terminal_node_visitor(v, n, **ctx)
                    if isinstance(n, TerminalASTNode) or isinstance(n, AliasASTNode)
                    else default_nonterminal_node_visitor(v, n, **ctx)
                ),
            ),
            {
                node_visitor[len("_visit_") :]: getattr(self.__class__, node_visitor)
                for node_visitor in dir(self.__class__)
                if callable(getattr(self.__class__, node_visitor))
                and node_visitor.startswith("_visit_")
            },
        )

    def __call__(self, n: ASTNode, **ctx: Any) -> Any:
        return self[n](self, n, **ctx)

    def __getitem__(self, n: ASTNode):
        match n:
            case NonterminalASTNode(node_type=node_type):
                return self._node_visitor[node_type[1:-1]]

            case AliasASTNode(node_type=node_type):
                return self._node_visitor[node_type[1:-1]]

            case TerminalASTNode(node_type=node_type):
                return self._node_visitor[node_type]

            case _:  # pragma: no cover
                assert False


class Shake(Visitor):
    def __init__(self) -> None:
        super().__init__(
            default_nonterminal_node_visitor=Shake._shake_nonterminal,
            default_terminal_node_visitor=Shake._shake_terminal,
        )

    @staticmethod
    def _shake_nonterminal(v: Visitor, n: ASTNode) -> ASTNode | None:
        n_: NonterminalASTNode
        match n:
            case NonterminalASTNode(node_type, choice, extras):
                n_ = NonterminalASTNode(node_type, choice=choice, extras=extras)

            case _:  # pragma: no cover
                assert False

        for c in n:
            c_: ASTNode | None = v(c)
            if c_:
                n_.add(c_)

        return n_ if n_ or "name" in n.extras else None

    @staticmethod
    def _shake_terminal(_: Visitor, n: ASTNode) -> ASTNode | None:
        return n if "name" in n.extras else None

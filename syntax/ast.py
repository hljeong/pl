from __future__ import annotations
from abc import ABC
from typing import Any, Iterator, Union

from common import dict_to_kwargs_str
from lexical import Token


class ASTNode(ABC):
    no_extras: dict[str, Any] = {}

    # janky way to circumvent tricky bug with static default parameter...
    def __init__(self, node_type: str, extras: dict[str, Any] = no_extras):
        self.node_type: str = node_type
        self.extras: dict[str, Any] = extras
        if self.extras is ASTNode.no_extras:
            self.extras = {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)})"


class NonterminalASTNode(ASTNode):
    def __init__(
        self,
        node_type: str,
        *children: ASTNode,
        extras: dict[str, Any] = ASTNode.no_extras,
    ):
        super().__init__(node_type, extras)
        self._children: list[ASTNode] = list(children)

    def __getitem__(self, key: int) -> ASTNode:
        return self._children[key]

    def __iter__(self) -> Iterator[ASTNode]:
        return iter(self.children)

    def __len__(self) -> int:
        return len(self.children)

    def add(self, child: ASTNode) -> None:
        self._children.append(child)

    def __str__(self) -> str:
        return f'{self.summary}{{{", ".join(map(str, self._children))}}}'

    @property
    def summary(self) -> str:
        if self.extras:
            return f"{self.node_type}[{dict_to_kwargs_str(self.extras)}]"

        else:
            return f"{self.node_type}"

    @property
    def children(self) -> tuple[ASTNode, ...]:
        return tuple(self._children)


class ChoiceNonterminalASTNode(NonterminalASTNode):
    def __init__(
        self,
        node_type: str,
        choice: int = 0,
        *children: ASTNode,
        extras: dict[str, Any] = ASTNode.no_extras,
    ):
        super().__init__(node_type, *children, extras=extras)
        self._choice = choice

    @property
    def choice(self) -> int:
        return self._choice


class AliasASTNode(ASTNode):
    def __init__(
        self,
        node_type: str,
        aliased_node_type: str,
        token: Token,
        extras: dict[str, Any] = ASTNode.no_extras,
    ):
        super().__init__(node_type, extras=extras)
        self.aliased_node_type: str = aliased_node_type
        self.token: Token = token

    def __str__(self) -> str:
        return str(self.token)

    def __getitem__(self, *_: Any) -> None:
        # todo: error
        raise ValueError(
            f"cannot subscript terminal of type '{self.node_type}' (alias of '{self.aliased_node_type}')"
        )

    # todo: how to decouple...
    @property
    def lexeme(self) -> str:
        return self.token.lexeme

    # todo: how to decouple...
    @property
    def literal(self) -> Union[str, int]:
        return self.token.literal


class TerminalASTNode(ASTNode):
    def __init__(
        self,
        node_type: str,
        token: Token,
    ):
        super().__init__(node_type)
        self.token = token

    def __str__(self) -> str:
        return str(self.token)

    def __getitem__(self, *_: Any) -> None:
        # todo: error
        raise ValueError(f"cannot subscript terminal of type '{self.node_type}'")

    # todo: how to decouple...
    @property
    def lexeme(self) -> str:
        return self.token.lexeme

    # todo: how to decouple...
    @property
    def literal(self) -> Union[str, int]:
        return self.token.literal

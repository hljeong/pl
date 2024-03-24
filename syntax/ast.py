from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator

from common import log_use
from lexical import Token

class ASTNode(ABC):
  def __init__(
    self,
    node_type: str,
  ):
    self._node_type: str = node_type

  def __repr__(self) -> str:
    return f'{self.__class__.__name__}({str(self)})'

  @property
  def node_type(self) -> str:
    return self._node_type
    


class NonterminalASTNode(ASTNode):
  def __init__(
    self,
    node_type: str,
  ):
    super().__init__(node_type)
    self._children: list[ASTNode] = []

  def __getitem__(self, key: int) -> ASTNode:
    return self._children[key]

  def __iter__(self) -> Iterator[ASTNode]:
    return iter(self.children)

  def __len__(self) -> int:
    return len(self.children)

  def add(self, child: ASTNode) -> None:
    self._children.append(child)

  def __str__(self) -> str:
    return f'{self.node_type}{{{", ".join(map(str, self._children))}}}'

  @property
  def children(self) -> tuple[ASTNode, ...]:
    return tuple(self._children)



class ChoiceNonterminalASTNode(NonterminalASTNode):
  def __init__(
    self,
    node_type: str,
    choice: int = 0,
  ):
    super().__init__(node_type)
    self._choice = choice

  @property
  def choice(self) -> int:
    return self._choice



class TerminalASTNode(ASTNode):
  def __init__(
    self,
    node_type: str,
    token: Token,
  ):
    super().__init__(node_type)
    self._token = token

  def __str__(self) -> str:
    return str(self._token)

  # todo: how to decouple...
  @property
  def lexeme(self) -> str:
    return self._token.lexeme

  # todo: how to decouple...
  @property
  def literal(self) -> Union[str, int]:
    return self._token.literal

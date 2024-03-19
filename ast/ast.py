from __future__ import annotations

from common import Token

class Node:
  def __init__(
    self,
    node_type: str,
    production: int,
  ):
    self._node_type: str = node_type
    self._production: int = production
    self._children: list[Union[Node, Token]] = []

  def add(self, child: Union[Node, Token]) -> None:
    self._children.append(child)

  def get(self, idx: int) -> Union[Node, Token]:
    return self._children[idx]

  @property
  def node_type(self) -> str:
    return self._node_type

  @property
  def production(self) -> int:
    return self._production

  @property
  def children(self) -> tuple[Union[Node, Token], ...]:
    return tuple(self._children)

  @property
  def tokens(self) -> tuple[Token, ...]:
    token_list = []
    for child in self._children:
      if type(child) is Token:
        token_list.append(child)
      else:
        token_list.extend(child.tokens)
    return tuple(token_list)

  def to_string(self, verbose = False) -> str:
    return f'{self._node_type}{{{", ".join(map(lambda child: child.to_string(verbose), self._children))}}}'

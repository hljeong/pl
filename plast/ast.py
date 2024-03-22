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
    self._children: list[Union[Node, list[Node], Token]] = []

  def add(self, child: Union[Node, Token]) -> None:
    self._children.append(child)

  def get(self, idx: int) -> Union[Node, list[Node], Token]:
    return self._children[idx]

  @property
  def node_type(self) -> str:
    return self._node_type

  @property
  def production(self) -> int:
    return self._production

  @property
  def children(self) -> tuple[Union[Node, list[Node], Token], ...]:
    return tuple(self._children)

  # todo: kinda bad hack for computing backtrack steps
  @property
  def tokens(self) -> tuple[Token, ...]:
    token_list = []
    for child in self._children:
      if type(child) is list:
        for child_node in child:
          token_list.extend(child_node.tokens)

      elif type(child) is Node:
        token_list.extend(child.tokens)

      elif type(child) is Token:
        token_list.append(child)

      else:
        # todo: better error
        raise ValueError('bad type')

    return tuple(token_list)

  def __str__(self) -> str:
    def child_to_string(child: Union[Node, list[Node], Token]) -> str:
      # todo: type annotation... list[Node] doesnt work
      if type(child) is list:
        return f'[{", ".join(map(str, child))}]'
      else:
        return str(child)
    return f'{self._node_type}{{{", ".join(map(child_to_string, self._children))}}}'

  def __repr__(self) -> str:
    return f'Node({self})'

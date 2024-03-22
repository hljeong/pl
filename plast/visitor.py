from __future__ import annotations
from collections import defaultdict

from common import Token

class Visitor:
  def __init__(
    self,
    ast: Node,
    node_visitors: dict[str, Callable[[Node, Visitor], Any]],
  ):
    self._node_visitors: defaultdict[str, Callable[[Node, Any, Visitor], Any]] = defaultdict(lambda: visit_it)
    self._node_visitors.update(node_visitors)
    self._ret: Any = self.visit(ast)

  def visit(
    self,
    node: Node,
  ) -> Any:
    return self._node_visitors[node.node_type](node, self)

  @property
  def ret(self) -> Any:
    return self._ret

def visit_it(node: Node, visitor: Visitor) -> Any:
  return visitor.visit(node[0])

def telescope(node: Node) -> Token:
  while type(node) is not Token:
    node = node[0]
  return node

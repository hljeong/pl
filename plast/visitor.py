from __future__ import annotations

class Visitor:
  def __init__(
    self,
    ast: Node,
    node_visitors: dict[str, Callable[[Node, Visitor], Any]],
  ):
    self._node_visitors: dict[str, Callable[[Node, Any, Visitor], Any]] = node_visitors
    self._ret: Any = self.visit(ast)

  def visit(
    self,
    node: Node,
  ) -> Any:
    return self._node_visitors[node.node_type](node, self)

  @property
  def ret(self) -> Any:
    return self._ret

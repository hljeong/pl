from __future__ import annotations

class Visitor:
  def __init__(
    self,
    ast: Node,
    node_visitors: dict[str, Callable[[Node, Visitor], Any]],
    initial_env: Any = None,
  ):
    self._node_visitors: dict[str, Callable[[Node, Any, Visitor], Any]] = node_visitors
    self._env: Any = initial_env
    self._ret: Any = self.visit(ast)

  def visit(
    self,
    node: Node,
  ) -> Any:
    return self._node_visitors[node.node_type](node, self)

  @property
  def env(self) -> Any:
    return self._env

  @property
  def ret(self) -> Any:
    return self._ret

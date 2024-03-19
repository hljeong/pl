from __future__ import annotations
from abc import ABC, abstractmethod

from common import Token

from .ast import ASTNode

class Visitor:
  def __init__(
    self,
    ast: ASTNode,
    node_visitors: dict[str, Callable[[ASTNode, Visitor], Any]],
    initial_env: Any = None,
  ):
    self._node_visitors: dict[str, Callable[[ASTNode, Any, Visitor], Any]] = node_visitors
    self._env: Any = initial_env
    self._ret: Any = self.visit(ast)

  def visit(
    self,
    node: ASTNode,
  ) -> Any:
    return self._node_visitors[node.node_type](node, self)

  @property
  def env(self) -> Any:
    return self._env

  @property
  def ret(self) -> Any:
    return self._ret

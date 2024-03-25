from __future__ import annotations
from collections import defaultdict
from typing import Generic

from common import Monad, Log, log_use, R
from lexical import Token

from .ast import TerminalASTNode

def visit_and_do_nothing(node: ASTNode, visitor: Visitor) -> Any:
  return None

@log_use
def visit_it(node: ASTNode, visitor: Visitor) -> Any:
  return visitor.visit(node[0])

# todo: change to telescope until multiple children?
def telescope(node: ASTNode) -> TerminalASTNode:
  while type(node) is not TerminalASTNode:
    Log.w(f'telescoping node ({node}) with multiple children', len(node) > 1)
    node = node[0]
  return node

class Visitor(Generic[R]):
  def __init__(
    self,
    node_visitors: dict[str, Callable[[ASTNode, Visitor], Any]],
    default_terminal_node_visitor: Callable[[TerminalASTNode], Any] = visit_and_do_nothing,
  ):
    self._node_visitors: defaultdict[str, Callable[[ASTNode, Any, Visitor], Any]] = defaultdict(lambda: lambda node, _: default_terminal_node_visitor(telescope(node), self))
    self._node_visitors.update(node_visitors)

  def visit(
    self,
    node: ASTNode,
  ) -> R:
    return self._node_visitors[node.node_type](node, self)

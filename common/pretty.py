from __future__ import annotations

from common import Token
from plast import Node

def ast_to_tree_string(
  ast: Union[Node, Token],
  prefix: str = '',
  last: bool = False,
  entry_point: bool = True,
):
  use_prefix: str = ''
  if not entry_point:
    if last:
      use_prefix = prefix + '└─ '
      prefix += '   '
    else:
      use_prefix = prefix + '├─ '
      prefix += '│  '

  if type(ast) is Token:
    return f'{use_prefix}{ast}'

  elif type(ast) is Node:
    lines = [f'{use_prefix}<{ast.node_type}>']
    for idx, child in enumerate(ast.children):
      is_last = idx == len(ast.children) - 1
      lines.append(ast_to_tree_string(
        child,
        prefix,
        is_last,
        False,
      ))
    return '\n'.join(lines)

  elif type(ast) is list:
    lines = [f'{use_prefix}(list)']
    for idx, child in enumerate(ast):
      is_last = idx == len(ast) - 1
      lines.append(ast_to_tree_string(
        child,
        prefix,
        is_last,
        False,
      ))
    return '\n'.join(lines)

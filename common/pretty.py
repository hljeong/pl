from __future__ import annotations
from typing import Iterable

# an internal node by duck typing must have node_type, __iter__, and __len__
def is_internal_node(x: Any):
  # todo: can this be done w hasattr?
  try:
    _ = x.node_type, iter(x), len(x)
    return True
  except:
    return False

def to_tree_string(
  node: Any,
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

  if is_internal_node(node):
    lines = [f'{use_prefix}{node.node_type}']
    for idx, child in enumerate(node):
      is_last = idx == len(node) - 1
      lines.append(to_tree_string(
        child, prefix, is_last, False,
      ))
    return '\n'.join(lines)
  
  elif type(node) is not list:
    return f'{use_prefix}{str(node)}'

  # todo: kill this by implementing different types of nodes as subclasses
  elif type(node) is list:
    lines = [f'{use_prefix}.']
    for idx, child in enumerate(node):
      is_last = idx == len(node) - 1
      lines.append(to_tree_string(
        child, prefix, is_last, False,
      ))
    return '\n'.join(lines)

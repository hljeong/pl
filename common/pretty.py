from __future__ import annotations
from typing import Iterable, Union


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
    prefix: str = "",
    last: bool = False,
    entry_point: bool = True,
) -> str:
    use_prefix: str = ""
    if not entry_point:
        if last:
            use_prefix = prefix + "└─ "
            prefix += "   "

        else:
            use_prefix = prefix + "├─ "
            prefix += "│  "

    if is_internal_node(node):
        lines = [f"{use_prefix}{node.node_type}"]
        for idx, child in enumerate(node):
            is_last = idx == len(node) - 1
            lines.append(
                to_tree_string(
                    child,
                    prefix,
                    is_last,
                    False,
                )
            )
        return "\n".join(lines)

    else:
        return f"{use_prefix}{str(node)}"


def join(lines_or_line: Union[Iterable[str], str], *rest_lines: str):
    if len(rest_lines) == 0:
        return "\n".join(lines_or_line)
    else:
        return "\n".join([lines_or_line, *rest_lines])


def tabbed(text: str, tab: int = 2):
    return join(map(lambda line: f'{" " * tab}{line}', text.split("\n")))


def count_lines(text: str):
    return text.count("\n") + 1

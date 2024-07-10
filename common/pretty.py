from __future__ import annotations
from typing import Any, Iterable
from rich import print

pprint = print


def dict_to_kwargs_str(d: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in d.items())


def arglist_str(args: tuple, kwargs: dict[str, Any]) -> str:
    args_str: str = ", ".join(map(repr, args))
    kwargs_str: str = dict_to_kwargs_str(kwargs)
    ret: str = ""

    if len(args_str) == 0:
        ret = kwargs_str
    elif len(kwargs_str) == 0:
        ret = args_str
    else:
        ret = f"{args_str}, {kwargs_str}"

    max_len = 20
    return f"{ret[:max_len - 3]}..." if len(ret) > max_len else ret


# an internal node by duck typing must have node_type, __iter__, and __len__
def is_internal_node(x: Any):
    # todo: can this be done w hasattr?
    try:
        _ = x.node_type, iter(x), len(x)
        return True
    except:
        return False


def ast_to_tree_string(
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
        lines = [f"{use_prefix}{node.summary}"]
        for idx, child in enumerate(node):
            is_last = idx == len(node) - 1
            lines.append(
                ast_to_tree_string(
                    child,
                    prefix,
                    is_last,
                    False,
                )
            )
        return "\n".join(lines)

    else:
        return f"{use_prefix}{str(node)}"


SPACE: str = (
    "this used to be an empty string and i thought the 'is' keyword compares reference instead of value..."
)


def join(*lines: str):
    return "\n".join(filter(lambda line: line is SPACE or len(line.strip()) > 0, lines))


def sjoin(*lines: str):
    return "\n\n".join(
        filter(lambda line: line is SPACE or len(line.strip()) > 0, lines)
    )


def joini(lines: Iterable[str]):
    return join(*lines)


def sjoini(lines: Iterable[str]):
    return sjoin(*lines)


def tabbed(text: str, tab: int = 2):
    return "\n".join(map(lambda line: f'{" " * tab}{line}', text.split("\n")))


def count_lines(text: str):
    return text.count("\n") + 1

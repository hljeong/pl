from __future__ import annotations
from typing import Any, Iterable
from rich import print

pprint = print


def hexdump(data: bytearray, columns=4) -> str:
    if not data:
        return ""

    # round up
    lines: int = (len(data) + columns - 1) // columns
    max_addr_width: int = len(f"{(len(data) - 1) // columns * columns:x}")
    return join(
        "".join(
            [
                f"0x{i * columns:0{max_addr_width}x}: ",
                " ".join(
                    map(
                        lambda b: f"{b:02x}",
                        data[i * columns : (i + 1) * columns][::-1],
                    )
                ),
            ]
        )
        for i in range(lines)
    )


def limit(s: str, lim: int = 20, rjust: bool = False) -> str:
    assert lim > 3
    if rjust:
        return f"...{s[-(lim - 3):]}" if len(s) > lim else s
    else:
        return f"{s[:lim - 3]}..." if len(s) > lim else s


def dict_to_kwargs_str(d: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in d.items())


def arglist_str(args: tuple, kwargs: dict[str, Any]) -> str:
    args_str: str = ", ".join(map(repr, args))
    kwargs_str: str = dict_to_kwargs_str(kwargs)

    if len(args_str) == 0:
        return limit(kwargs_str)
    elif len(kwargs_str) == 0:
        return limit(args_str)
    else:
        return limit(f"{args_str}, {kwargs_str}")


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


def joinv(*lines: str):
    return "\n".join(filter(lambda line: line is SPACE or len(line.strip()) > 0, lines))


def sjoinv(*lines: str):
    return "\n\n".join(
        filter(lambda line: line is SPACE or len(line.strip()) > 0, lines)
    )


def join(lines: Iterable[str]):
    return joinv(*lines)


def sjoin(lines: Iterable[str]):
    return sjoinv(*lines)


def tabbed(text: str, tab: int = 2):
    return "\n".join(map(lambda line: f'{" " * tab}{line}', text.split("\n")))


def count_lines(text: str):
    return text.count("\n") + 1

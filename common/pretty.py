from __future__ import annotations
from typing import Any, Iterable


def dict_to_kwargs_str(d: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in d.items())


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


class Text:
    class Token:
        def __init__(self, *components: Any):
            self._content: str = "".join(map(str, components))

        def __repr__(self) -> str:
            return self.render()

        @property
        def width(self) -> int:
            return len(self._content)

        def render(self) -> str:
            return self._content

        @staticmethod
        def gap(size: int) -> Text.Token:
            return Text.Token(" " * size)

    class Line:
        def __init__(self, *tokens: Text.Token, tabstop: int = 0):
            self._tokens: list[Text.Token] = list(tokens)
            self._tabstop: int = tabstop

        def __repr__(self) -> str:
            return self.render()

        @property
        def tokens(self) -> list[Text.Token]:
            return self._tokens

        @property
        def tabstop(self) -> int:
            return self._tabstop

        @property
        def width(self) -> int:
            return (
                self._tabstop * 2
                # todo: fix type annotation
                + sum(map(Text.Token.width.fget, self._tokens))
                + len(self._tokens)
                - 1
            )

        def render(self) -> str:
            return " ".join(map(Text.Token.render, self._tokens))

    def __init__(self, *lines: Line):
        self._lines: list[Text.Line] = list(lines)

    def __repr__(self) -> str:
        return self.render()

    @property
    def width(self) -> int:
        # todo: fix type annotation
        return max(map(Text.Line.width.fget, self._lines))

    def render(self) -> str:
        return join(map(Text.Line.render, self._lines))

    # todo: bad api
    def join_vertical(self, text: Text) -> Text:
        l_lines: list[Text.Line] = self._lines[:]
        r_lines: list[Text.Line] = text._lines[:]

        # todo: terrible code
        while len(l_lines) < len(r_lines):
            l_lines.append(Text.Line())

        while len(r_lines) < len(l_lines):
            r_lines.append(Text.Line())

        # *2-tabstop gap*
        l_adjust = (self._width + 3) // 2

        # todo: maybe this could be a bit confusing
        # zip is kinda goated here
        return Text(
            *map(
                lambda why_cant_i_destructure_this: Text.Line(
                    *why_cant_i_destructure_this[0].tokens,
                    Text.Token.gap(l_adjust - why_cant_i_destructure_this[0].width),
                    *why_cant_i_destructure_this[1].tokens,
                ),
                zip(l_lines, r_lines),
            )
        )

    # todo: bad code
    def tabbed(self) -> Text:
        return Text(
            Text.Line(*line._tokens, tabstop=line.tabstop + 1) for line in self._lines
        )

    @staticmethod
    def join(*texts: Text) -> Text:
        ret: Text = Text()

        for text in texts:
            ret._lines.extend(text._lines)
            if text._width > ret._width:
                ret._width = text._width

        return ret


# prefixed optional
def opt_p(prepend: str, optional: str):
    if len(optional) == 0:
        return ""

    return f"{prepend}{optional}"


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

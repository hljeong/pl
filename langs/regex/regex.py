from __future__ import annotations

from common import Monad, load
from lexical import Lex
from syntax import ASTNode, Grammar, Parse

from ..lang import Lang


class Regex(Lang):
    name = "regex"
    grammar = Grammar.from_xbnf("regex", load("langs/regex/spec/regex.xbnf"))

    class Parse:
        def __init__(self, entry_point: str | None = None):
            self._lex = Lex.for_lang(Regex)
            self._parse = Parse.for_lang(Regex, entry_point=entry_point)

        def __call__(self, prog) -> ASTNode:
            return Monad(prog).then(self._lex).then(self._parse).v


Regex.parse = Regex.Parse()

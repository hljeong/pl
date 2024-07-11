from __future__ import annotations
from typing import Callable
from abc import ABC

from syntax import Grammar, ASTNode


class Lang(ABC):
    name: str
    grammar: Grammar
    parse: Callable[[str], ASTNode]
    shake: Callable[[ASTNode], ASTNode]
    print: Callable[[ASTNode], str]

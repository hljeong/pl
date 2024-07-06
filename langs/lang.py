from __future__ import annotations
from abc import ABC

from syntax import Grammar


class Lang(ABC):
    grammar: Grammar

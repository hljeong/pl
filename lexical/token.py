from __future__ import annotations
from typing import Any

from .vocabulary import Vocabulary


class Token:
    def __init__(
        self,
        token_type: str,
        lexeme: str,
        literal: Any = None,
        extra: dict[str, Any] = {},
    ):
        self._token_type: str = token_type
        self._lexeme: str = lexeme
        self._literal: Any = literal
        self._extra: dict[str, Any] = extra

    def __eq__(self, other: object) -> bool:
        return type(other) is Token and (
            self._token_type == other._token_type
            and self._lexeme == other._lexeme
            and self._literal == other._literal
        )

    def __ne__(self, other: object) -> bool:
        return not self == other

    @property
    def token_type(self) -> str:
        return self._token_type

    @property
    def lexeme(self) -> str:
        return self._lexeme

    @property
    def literal(self) -> Any:
        return self._literal

    # todo: access control
    @property
    def extra(self) -> dict[str, Any]:
        return self._extra

    def __str__(self) -> str:
        # builtin token type
        if self._token_type in Vocabulary.Definition.builtin:
            return f"{self._token_type}('{self._lexeme}')"

        else:
            return f"'{self._lexeme}'"

    def __repr__(self) -> str:
        return f"Token({str(self)})"

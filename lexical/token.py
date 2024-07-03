from __future__ import annotations
from typing import Optional, Union

from .vocabulary import Vocabulary


class Token:
    def __init__(
        self,
        token_type: str,
        lexeme: str,
        literal: Optional[Union[str, int]] = None,
        extra: dict[str, Any] = {},
    ):
        self._token_type = token_type
        self._lexeme = lexeme
        self._literal = literal
        self._extra = extra

    def __eq__(self, other: Token) -> bool:
        return (
            self._token_type == other._token_type
            and self._lexeme == other._lexeme
            and self._literal == other._literal
        )

    def __ne__(self, other: Token) -> bool:
        return not self == other

    @property
    def token_type(self) -> str:
        return self._token_type

    @property
    def lexeme(self) -> str:
        return self._lexeme

    @property
    def literal(self) -> Optional[Union[str, int]]:
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

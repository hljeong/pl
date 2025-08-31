from io import StringIO

from lexer import Cursor, Source, Token
import hbnf


def regenerate_source(tokens: list[Token]) -> str:
    with StringIO() as s:
        row: int = 0
        col: int = 0
        for token in tokens:
            cursor: Cursor = token.rng.start
            s.write("\n" * (cursor.row - row))
            if cursor.row > row:
                row = cursor.row
                col = 0
            s.write(" " * (cursor.col - col))
            s.write(token.lexeme)
            col = token.rng.end.col
        s.seek(0)
        return s.read()


def test_bootstrap():
    src: Source = Source.from_file("hbnf.hbnf")
    tokens: list[Token] = hbnf.Lexer().lex(src)
    assert src.src == regenerate_source(tokens)

    ast: hbnf.Hbnf = hbnf.Parser().parse(tokens)
    print(hbnf.ast_str(ast))

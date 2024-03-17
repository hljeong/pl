from pytest import main, raises, fixture
from copy import copy

from context import common, lexer
from common import Cursor, CursorRange, Token
from lexer import Lexer

@fixture
def sources():
  return [
    'jump 0 # loop forever',
    'read 1\nsetv 4 1'
  ]

def test_lexer_lex_invalid_char():
  with raises(ValueError) as e:
    Lexer('hi!').lex()
  assert str(e.value) == 'invalid character (!) encountered at line 1 column 3'

def test_lexer_lex_0_byte():
  return
  token_list = Lexer('\0').lex()
  token_list_to_string = list(map(lambda token: token.to_string(), token_list))
  print(f'[{", ".join(token_list_to_string)}]')
  assert token_list == [
      Token(Token.Type.EOF, '\0', None, CursorRange(Cursor(1, 1), Cursor(1, 1))),
      Token(Token.Type.EOF, '\0', None, CursorRange(Cursor(1, 2), Cursor(1, 2))),
  ]

def test_lexer_lex(sources):
  token_list = Lexer(sources[0]).tokens
  token_list_to_string = list(map(lambda token: token.to_string(), token_list))
  print(f'[{", ".join(token_list_to_string)}]')

  token_list = Lexer(sources[1]).tokens
  token_list_to_string = list(map(lambda token: token.to_string(), token_list))
  print(f'[{", ".join(token_list_to_string)}]')

  assert False
  return
  token_lists = [
    [
      Token(Token.Type.EOF, '\0', None, CursorRange(Cursor(1, 1), Cursor(1, 1))),
    ],
    [
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 1), Cursor(1, 1))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 2), Cursor(1, 2))),
      Token(Token.Type.EOF, '\0', None, CursorRange(Cursor(1, 3), Cursor(1, 3))),
    ],
    [
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 1), Cursor(1, 1))),
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 2), Cursor(1, 2))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 3), Cursor(1, 3))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 4), Cursor(1, 4))),
      Token(Token.Type.EOF, '\0', None, CursorRange(Cursor(1, 5), Cursor(1, 5))),
    ],
    [
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 1), Cursor(1, 1))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 2), Cursor(1, 2))),
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 3), Cursor(1, 3))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 4), Cursor(1, 4))),
      Token(Token.Type.EOF, '\0', None, CursorRange(Cursor(1, 5), Cursor(1, 5))),
    ],
    [
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 1), Cursor(1, 1))),
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 2), Cursor(1, 2))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 3), Cursor(1, 3))),
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 4), Cursor(1, 4))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 5), Cursor(1, 5))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 6), Cursor(1, 6))),
      Token(Token.Type.LEFT_PAREN, '(', None, CursorRange(Cursor(1, 7), Cursor(1, 7))),
      Token(Token.Type.RIGHT_PAREN, ')', None, CursorRange(Cursor(1, 8), Cursor(1, 8))),
      Token(Token.Type.EOF, '\0', None, CursorRange(Cursor(1, 9), Cursor(1, 9))),
    ],
  ]

  for i in range(len(sources)):
    token_list = Lexer(sources[i]).lex()
    token_list_to_string = list(map(lambda token: token.to_string(), token_list))
    print(f'[{", ".join(token_list_to_string)}]')
    assert token_list == token_lists[i]

if __name__ == '__main__':
  main()

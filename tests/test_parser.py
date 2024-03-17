from pytest import main, raises, fixture
from copy import copy

from context import lexer, parser
from lexer import Lexer
from parser import Parser

@fixture
def sources():
  return [
    'jump 0 # loop forever',
    'read 1\nsetv 4 1'
  ]

def test_parser_parse(sources):
  token_list = Lexer(sources[1]).tokens
  ast = Parser(token_list).root
  assert False

  assert False
if __name__ == '__main__':
  main()

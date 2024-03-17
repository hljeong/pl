import sys

from lexer import Lexer
from parser import Parser, AInterpreter

if __name__ == '__main__':
  if len(sys.argv) == 1:
    prog = ''.join(sys.stdin.readlines())
  else:
    with open(sys.argv[1]) as f:
      prog = ''.join(f.readlines())

  AInterpreter(Parser(Lexer(prog).tokens).root).interpret()

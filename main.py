import sys

from grammar import Grammar
from langs.a import AParser, APrinter, AInterpreter
from langs.b import BParser

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print('usage: python main.py <prog>')
    exit(1)

  with open(sys.argv[1]) as f:
    prog = ''.join(f.readlines())

  # ast = AParser(prog).ast
  # print(APrinter(ast).str)
  # AInterpreter(ast).interpret()

  ast = BParser(prog).ast
  print(ast.to_string())

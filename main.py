import sys

from common import ast_to_tree_string
from grammar import Grammar
from plast import Node
from langs.a import AParser, APrinter, AInterpreter
from langs.b import BParser, XBParser, BPrinter, BAllocator

if __name__ == '__main__':

  if len(sys.argv) != 2:
    print('usage: python main.py <prog>')
    exit(1)

  with open(sys.argv[1]) as f:
    prog = ''.join(f.readlines())

  ast = XBParser(prog).ast
  print(ast_to_tree_string(ast))

  exit(0)

  # ast = AParser(prog).ast
  # print(APrinter(ast).str)
  # AInterpreter(ast).interpret()

  ast = BParser(prog).ast
  # print(ast_to_tree_string(ast))

  ast_prog = BPrinter(ast).str
  print(ast_prog)

  alloc = BAllocator(ast).alloc
  print(alloc)

import sys

from common import to_tree_string, log_timed, Log, LogLevel
Log.level = LogLevel.DEBUG
from syntax import Node, Grammar
from langs.a import AParser, APrinter, AInterpreter
from langs.b import BParser, XBParser, BPrinter, XBPrinter, BAllocator

if __name__ == '__main__':

  if len(sys.argv) != 2:
    print('usage: python main.py <prog>')
    exit(1)

  with open(sys.argv[1]) as f:
    prog = ''.join(f.readlines())

  ast = log_timed(lambda: XBParser(prog).ast, 'parse prog')
  # print(to_tree_string(ast))

  ast_prog = log_timed(lambda: XBPrinter(ast).str, 'print prog')
  print(ast_prog)

  exit(0)

  # ast = AParser(prog).ast
  # print(APrinter(ast).str)
  # AInterpreter(ast).interpret()

  ast = BParser(prog).ast
  # print(to_tree_string(ast))

  ast_prog = BPrinter(ast).str
  print(ast_prog)

  alloc = BAllocator(ast).alloc
  print(alloc)

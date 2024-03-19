import sys

from lexer import Lexer
from parser import ASTParser, Parser
from grammar import Grammar
from a import AInterpreter

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print('usage: python main.py <prog>')
    exit(1)

  with open(sys.argv[1]) as f:
    prog = ''.join(f.readlines())

  if False:
    grammar = Grammar(gram)
    tokens = Lexer(prog).tokens
    ast = ASTParser(grammar, tokens).ast
    print(ast.to_string())

  AInterpreter(prog).interpret()

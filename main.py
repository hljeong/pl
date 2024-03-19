import sys

from langs.a import AInterpreter

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print('usage: python main.py <prog>')
    exit(1)

  with open(sys.argv[1]) as f:
    prog = ''.join(f.readlines())

  AInterpreter(prog).interpret()

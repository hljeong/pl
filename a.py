import sys

from common import Monad
from langs.a import AParser, AInterpreter

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("usage: python a.py <prog>")
        exit(1)

    with open(sys.argv[1]) as f:
        prog = "".join(f.readlines())

    Monad(prog).then(AParser().parse).then(AInterpreter().interpret)

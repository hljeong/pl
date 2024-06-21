import sys

from common import Monad

from langs.a import AParser, AInterpreter
from langs.b import BParser, BCompiler

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("usage: python b.py <prog>")
        exit(1)

    with open(sys.argv[1]) as f:
        prog = "".join(f.readlines())

    (
        Monad(prog)
        .then(BParser().parse)
        .then(BCompiler().compile)
        .then(AParser().parse)
        .then(AInterpreter().interpret)
    )

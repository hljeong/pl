#!/usr/bin/env python

from argparse import ArgumentParser

from common import Monad
from langs.a import AParser, AInterpreter
from langs.b import BParser, BCompiler


def main():
    parser = ArgumentParser(prog="pl", description="toy languages")
    parser.add_argument("language")
    parser.add_argument("program")
    # todo: --action={execute, print_tree, print, ...}, --log-level
    args = parser.parse_args()

    with open(args.program) as f:
        program = "".join(f.readlines())

    match args.language:
        case "a":
            Monad(program).then(AParser().parse).then(AInterpreter().interpret)

        case "b":
            (
                Monad(program)
                .then(BParser().parse)
                .then(BCompiler().compile)
                .then(AParser().parse)
                .then(AInterpreter().interpret)
            )


if __name__ == "__main__":
    main()

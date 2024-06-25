#!/usr/bin/env python

from argparse import ArgumentParser

from common import Monad, Log
from langs.a import AParser, AInterpreter
from langs.ar import ARInterpreter, Machine
from langs.b import BParser, BCompiler
from langs.b2 import B2Parser, B2Compiler


def main():
    parser = ArgumentParser(prog="pl", description="toy languages")
    parser.add_argument("lang")
    parser.add_argument("prog")
    parser.add_argument("-l", "--log-level", type=str, default="e")
    # todo: --action={execute, print_tree, print, ...}, --log-level
    args = parser.parse_args()

    match args.log_level.lower():
        case "n" | "none":
            Log.level = Log.Level.NONE

        case "e" | "error":
            Log.level = Log.Level.ERROR

        case "d" | "debug":
            Log.level = Log.Level.DEBUG

        case "w" | "warn":
            Log.level = Log.Level.WARN

        case "t" | "trace":
            Log.level = Log.Level.TRACE

    with open(args.prog) as f:
        prog = "".join(f.readlines())

    match args.lang:
        case "a":
            Monad(prog).then(AParser().parse).then(AInterpreter().interpret)

        case "ar":
            Monad(prog).then(ARInterpreter().interpret)

        case "b":
            (
                Monad(prog)
                .then(BParser().parse)
                .then(BCompiler().compile)
                .then(AParser().parse)
                .then(AInterpreter().interpret)
            )

        case "b2":
            (
                Monad(prog)
                .then(B2Parser().parse)
                .then(B2Compiler().compile)
                .then(ARInterpreter(Machine(regfile_size=727)).interpret)
            )


if __name__ == "__main__":
    main()

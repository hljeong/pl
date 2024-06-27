#!/usr/bin/env python

from argparse import ArgumentParser

from common import Monad, Log
from langs.a import AAssembler, Machine
from langs.b import BParser, BAggregator, BAllocator, BCompiler


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
            Monad(prog).then(AAssembler(Machine()))

        case "b":
            (
                Monad(prog)
                .then(BParser())
                .keep_then(BAggregator())
                .keep_then(
                    lambda fix_this_ugly_thing_too: BAllocator()(
                        fix_this_ugly_thing_too[0]
                    )
                )
                .then(
                    lambda fix_this_ugly_thing: BCompiler(
                        fix_this_ugly_thing[0][1], fix_this_ugly_thing[1]
                    )(fix_this_ugly_thing[0][0])
                )
                .also(print)
                .then(AAssembler(Machine()))
            )


if __name__ == "__main__":
    main()

#!/usr/bin/env python

from argparse import ArgumentParser

from common import Log
from pl import run_a, print_b, compile_b, run_b


def main():
    parser = ArgumentParser(prog="pl", description="toy languages")
    parser.add_argument("lang")
    parser.add_argument("cmd")
    parser.add_argument("prog")
    parser.add_argument("-l", "--log-level", type=str, default="e")
    args = parser.parse_args()

    # todo: move this logic to Log
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

    # todo: defaultdict error message
    {
        "a": {"run": run_a},
        "b": {
            "print": print_b,
            "compile": compile_b,
            "run": run_b,
        },
    }[args.lang][args.cmd](prog)


if __name__ == "__main__":
    main()

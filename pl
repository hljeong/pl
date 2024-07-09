#!/usr/bin/env python

from argparse import ArgumentParser

from common import Log, load


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

    from pl import (
        print_a,
        run_a,
        print_b,
        compile_b,
        run_b,
        print_b2,
        translate_b2,
        compile_b2,
        run_b2,
        print_expr,
    )

    prog: str = load(args.prog)

    # todo: defaultdict error message
    {
        "a": {
            "print": print_a,
            "run": run_a,
        },
        "b": {
            "print": print_b,
            "compile": compile_b,
            "run": run_b,
        },
        "b2": {
            "print": print_b2,
            "translate": translate_b2,
            "compile": compile_b2,
            "run": run_b2,
        },
        "expr": {
            "print": print_expr,
        },
    }[args.lang][args.cmd](prog)


if __name__ == "__main__":
    main()

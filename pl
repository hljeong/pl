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

    Log.at(args.log_level)

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

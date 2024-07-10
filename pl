#!/usr/bin/env python

from argparse import ArgumentParser

from common import Log
from synthesis import Source


def main():
    parser = ArgumentParser(prog="pl", description="run pl programs")
    parser.add_argument("source", help="program to run")
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        default="e",
        help="[n]one, [w]arn, [d]ebug, [e]rror, or [t]race",
    )
    args = parser.parse_args()

    Log.at(args.log_level)

    from synthesis import synthesize
    from runtime import MP0

    MP0()(synthesize("mp0", Source.load(args.source)))


if __name__ == "__main__":
    main()

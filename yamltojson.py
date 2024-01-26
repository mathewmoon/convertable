#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace
from collections import deque
from json import dumps, load, loads
from re import compile
from sys import stdin
from typing import Callable, Dict, List

from pygments import highlight
from pygments.lexers.data import JsonLexer, YamlLexer
from pygments.formatters import TerminalFormatter

from yaml import safe_load, dump as yamldumps


# Parses indexes for arrays
INDEX_RE = compile(r"(.+)\[(\d+)\]$")
# Matches ANSI escape sequences. Used to remove terminal garbage from stdin
ANSI_RE = compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", type=str, help="File path to open.", required=False)
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        help="Return a specific path, in dotted notation.",
        default=None,
    )
    parser.add_argument(
        "-i",
        "--indent",
        type=int,
        help="Number of spaces for indentation of JSON.",
        default=2,
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Don't print color to terminal"
    )
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Operate in reverse, converting JSON to YAML.",
    )

    return parser.parse_args()


def parse_path(path: str, data: Dict | List) -> Dict:
    """
    Traverses the data using a dot-notation string representation of
    the path in the data we want to return.
    """
    # Use deque for speed and appendleft()
    path_parts = deque(path.split("."))

    # Tracks where we are in parsing the path in case we
    # need it for an error message
    parsed_path = ""

    while path_parts:
        original = path_parts.popleft()

        if isinstance(original, str) and (index := INDEX_RE.match(original)):
            # We've hit an array index. Parse it and push it
            # back into the parts list as the next item to parse
            keyname = index.group(1)
            index = int(index.group(2))
            path_parts.appendleft(index)
        else:
            keyname = original

        try:
            data = data[keyname]
            parsed_path += f"{original}."
        except (IndexError, KeyError):
            parsed_path += f"{original}."
            print(f"Invalid Key or Index at {parsed_path[0:-1]}")
            exit(1)

    return data


def load(loader: Callable, filepath: str = "", from_stdin: bool = False) -> Dict:
    """
    Load data from either a string on stdin or a file, depending on your loader
    """
    if from_stdin:
        # Strip ANSI escapes from string
        input_str = ANSI_RE.sub("", stdin.read())
        data = loader(input_str)
    else:
        with open(filepath, "r") as f:
            data = load(f)

    return data


def main() -> None:
    """Do stuff!"""

    args = parse_args()
    from_stdin = not stdin.isatty()

    if not args.reverse:
        loader = safe_load
        dumper = dumps
        dumper_opts = {"indent": args.indent}
        color_lexer = JsonLexer()

    else:
        loader = loads if from_stdin else load
        dumper = yamldumps
        dumper_opts = {"sort_keys": False}
        color_lexer = YamlLexer()

    data = load(loader, filepath=args.file, from_stdin=from_stdin)

    if args.path:
        data = parse_path(args.path, data)

    res = dumper(data, **dumper_opts)

    if not args.no_color:
        res = highlight(res, color_lexer, TerminalFormatter())

    print(res)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        exit(1)

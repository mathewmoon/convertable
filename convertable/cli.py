from argparse import ArgumentParser, Namespace
from re import compile
from sys import stdin, stdout

from pygments import highlight
from pygments.lexers.data import JsonLexer, YamlLexer
from pygments.lexers.configs import TOMLLexer
from pygments.formatters import TerminalFormatter

from .convertable import Parser


# Parses indexes for arrays
INDEX_RE = compile(r"(.+)\[(\d+)\]$")
# Matches ANSI escape sequences. Used to remove terminal garbage from stdin
ANSI_RE = compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


parser = ArgumentParser()


def parse_args() -> Namespace:
    parser.add_argument("expression", nargs="*", help="JQ Expression to run on output")

    parser.add_argument(
        "-f", "--file", type=str, help="File path to open.", required=False
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
    return parser.parse_args()


def convertable_cli() -> None:
    parser.add_argument("cmd", choices=["json", "toml", "yaml"], help="Command to run.")
    parser.add_argument(
        "-o",
        "--output-format",
        type=str,
        choices=["json", "yaml", "toml"],
        help="Output format.",
        default="json",
    )
    args = parse_args()
    input_type = args.cmd
    output_type = args.output_format

    return cli(input_type, output_type, args)


def yamltojson() -> None:
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Operate in reverse, converting JSON to YAML.",
    )

    args = parse_args()
    input_type = "yaml"
    output_type = "json"

    return cli(input_type, output_type, args, reverse=args.reverse)


def tomltojson() -> None:
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Operate in reverse, converting JSON to TOML.",
    )

    args = parse_args()
    input_type = "toml"
    output_type = "json"

    return cli(input_type, output_type, args, reverse=args.reverse)


def tomltoyaml() -> None:
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Operate in reverse, converting YAML to TOML.",
    )

    args = parse_args()
    input_type = "toml"
    output_type = "yaml"

    return cli(input_type, output_type, args, reverse=args.reverse)


def cli(
    input_type: str,
    output_type: str,
    args: Namespace,
    reverse: bool = False,
) -> None:
    color_lexers = dict(
        json=JsonLexer(),
        yaml=YamlLexer(),
        toml=TOMLLexer(),
    )
    if reverse:
        input_type, output_type = output_type, input_type

    from_stdin = not stdin.isatty()
    to_stdout = stdout.isatty()

    expression = args.expression
    if len(expression) > 1:
        print("Only one expression is allowed.")
        exit(1)
    expression = expression[0] if expression else "."

    if from_stdin and args.file:
        raise ValueError("Cannot use both stdin and a file.")

    if not from_stdin and not args.file:
        raise ValueError("Must provide either data or a filepath.")

    if from_stdin:
        # Strip ANSI escapes from string
        input_str = ANSI_RE.sub("", stdin.read())
    else:
        input_str = None

    parser = Parser(data=input_str, filepath=args.file, data_type=input_type)

    opts = {}
    if output_type == "json":
        opts["indent"] = args.indent

    try:
        data = parser.dump(output_type, expression=expression, **opts)
    except Exception as e:
        print(e)
        exit(1)

    if (not args.no_color) and to_stdout:
        data = highlight(data, color_lexers[output_type], TerminalFormatter())

    print(data)

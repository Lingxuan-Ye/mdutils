import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Callable, Container, List, Literal, Tuple

__all__ = ["iterdir", "format", "statistics"]

SEP = "\n" + "-" * 40 + "\n"


def iterdir(
    path: str,
    suffixes: Container[str] = None,
    recursive: bool = True
) -> List[Path]:
    stack = [Path(path)]
    if suffixes is None:
        suffixes = (".md", )
    result = []
    while stack:
        _path = stack.pop()
        if _path.is_file():
            _suffix = _path.suffix.lower()
            if _suffix in suffixes or _suffix.lstrip(".") in suffixes:
                result.append(_path)
        elif _path.is_dir() and recursive:
            stack.extend(_path.iterdir())
    return result


def __formatfunc_default(raw: str) -> str:

    temp = raw.strip() + "\n"

    # replace multiple blank lines by one
    temp = re.sub(r"\n{3,}", "\n\n", temp)

    # [[button]](src) -> [[ button ]](src)
    temp = re.sub(r"\[\[(?=\S)", "[[ ", temp)
    temp = re.sub(r"(?<=\S)\]\]", " ]]", temp)

    # remove spaces at end of each line
    temp = re.sub(r" +\n", "\n", temp)

    # add one space for '“ (\u201c)' and '” (\u201d)'
    temp = re.sub(r"(?<=\w)(“| {2,}“)", " “", temp)
    temp = re.sub(r"(”|” {2,})(?=\w)", "” ", temp)

    return temp


def format(
    path: str,
    formatfunc: Callable[[str], str] = __formatfunc_default,
    suffixes: Container[str] = None,
    recursive: bool = True
) -> None:
    for i in iterdir(path, suffixes, recursive):
        with open(i, encoding="utf-8") as f:
            raw = f.read()
            result = formatfunc(raw)
            with open(i, "w", newline="\n", encoding="utf-8") as g:
                g.write(result)


class Stat(Counter):

    def __repr__(self) -> str:
        temp = [
            f"{'paragraphs:':<32}{self['paragraphs']}",
            f"{'lines:':<32}{self['lines']}\n",

            f"{'words:':<32}{self['words']}",
            f"{'Chinese characters:':<32}{self['Chinese characters']}",
            f"{'punctuations:':<32}{self['punctuations']}",
            f"{'whitespaces:':<32}{self['whitespaces']}",
            f"{'other characters:':<32}{self['other characters']}\n",

            f"{'characters (no spaces):':<32}{self['characters (no spaces)']}",
            f"{'characters (with spaces):':<32}{self['characters (with spaces)']}"
        ]
        return "\n".join(temp)


def statistics(
    path: str,
    suffixes: Container[str] = None,
    recursive: bool = True,
    verbose: bool = False,
    redirect_to: str = None,
    redirect_mode: Literal["w", "a"] = "w"
) -> None:

    if verbose:
        overview: List[Tuple[str, Stat]] = []

    stat = Stat()
    path_list = iterdir(path, suffixes, recursive)
    path_list.sort()
    files = len(path_list)
    for i in path_list:

        with open(i, encoding="utf-8") as f:
            raw = f.read()

        _stat = Stat()
        _goups = re.findall(
            r"([\u4e00-\u9fa5])|(\w)|(\S)|((?<!\n)\n(?!\n))|(\n+)|(\s)|(.)",
            raw,
            flags=re.DOTALL
        )
        for j, k, l, m, n, o, p in _goups:
            if j:  # r"[\u4e00-\u9fa5]"; note that bool("") is False
                _stat["Chinese characters"] += 1
                _stat["words"] += 1
            elif k:  # r"\w"
                _stat["words"] += 1
            elif l:  # r"\S"
                _stat["punctuations"] += 1
            elif m:  # r"(?<!\n)\n(?!\n)"
                _stat["lines"] += 1
                _stat["whitespaces"] += 1
            elif n:  # r"\n+"
                _stat["lines"] += 1
                _stat["paragraphs"] += 1
                _stat["whitespaces"] += len(m)
            elif o:  # r"\s"; note that bool(" ") is True
                _stat["whitespaces"] += 1
            elif p: # r"."
                _stat["other characters"] += 1
        _stat["characters (no spaces)"] = _stat["words"] + _stat["punctuations"]
        _stat["characters (with spaces)"] = _stat["words"] + _stat["punctuations"] + _stat["whitespaces"]
        stat.update(_stat)

        if verbose:
            overview.append((f"{i.name}", _stat))

    message = f"STATISTICS{SEP}" + f"{'files:':<32}{files}\n\n" + str(stat)

    if verbose:
        details = f"{SEP}".join(
            f"file: {i[0]}\n\n{i[1]}" for i in overview
        )
        message += f"\n\n\nDETAILS{SEP}{details}"

    if redirect_to is not None:
        with open(redirect_to, mode=redirect_mode, newline="\n") as f:
            print(message, file=f)
    else:
        print(message)


def __format(args: argparse.Namespace) -> None:
    format(path=args.f, suffixes=args.s, recursive=args.r)


def __stats(args: argparse.Namespace) -> None:
    if args.R is None:
        statistics(path=args.f, suffixes=args.s, recursive=args.r, verbose=args.v)
    else:
        statistics(path=args.f, suffixes=args.s, recursive=args.r, verbose=args.v, redirect_to=args.R[0], redirect_mode=args.R[1])


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, title="subcommand", metavar="")
    parser_format = subparsers.add_parser("format", help="format markdown files")
    parser_format.add_argument("-f", default=".", metavar="", help="file or diractory path (current working directory by default)")
    parser_format.add_argument("-r", action="store_true", default=True, help="execute recursively, if a directory is passed")
    parser_format.add_argument("-s", action="extend", nargs="+", metavar="", help="specify suffix(es), '.md' for example")
    parser_format.set_defaults(func=__format)
    parser_stats = subparsers.add_parser("stats", help="show statistics")
    parser_stats.add_argument("-f", default=".", metavar="", help="file or diractory path (current working directory by default)")
    parser_stats.add_argument("-r", action="store_true", default=True, help="execute recursively, if a directory is passed")
    parser_stats.add_argument("-s", action="extend", nargs="+", metavar="", help="specify suffix(es), '.md' for example")
    parser_stats.add_argument("-v", action="store_true", default=False, help="print verbosely")
    parser_stats.add_argument("-R", action="extend", nargs=2, metavar="", help="redirect output; pos 1: file path, pos 2: 'w' for 'write', 'a' for 'append', raise exception elsewise")
    parser_stats.set_defaults(func=__stats)
    args = parser.parse_args()
    args.func(args)
    print("\nfinished.\n")


if __name__ == "__main__":
    main()

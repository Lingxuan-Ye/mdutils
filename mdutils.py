import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Callable, List, Literal, Tuple

__all__ = ["iterdir", "format", "statistics"]

SEP = "\n" + "-" * 40 + "\n"


def iterdir(
    path: str,
    suffix: str = ".md",
    recursive: bool = True
) -> List[Path]:
    stack = [Path(path)]
    result = []
    while stack:
        _path = stack.pop()
        if _path.is_file():
            if _path.suffix.lower() == suffix:
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
    suffix: str = ".md",
    recursive: bool = True
) -> None:
    for i in iterdir(path, suffix, recursive):
        with open(i, encoding="utf-8") as f:
            raw = f.read()
            result = formatfunc(raw)
            with open(i, "w", newline="\n", encoding="utf-8") as g:
                g.write(result)


class Stat(Counter):

    def __repr__(self) -> str:
        temp = [
            f"{'characters (no spaces):':<28}{self['characters (no spaces)']}",
            f"{'characters (with spaces):':<28}{self['characters (with spaces)']}\n",

            f"{'words:':<28}{self['words']}",
            f"{'punctuations:':<28}{self['punctuations']}",
            f"{'Chinese characters:':<28}{self['Chinese characters']}\n",

            f"{'paragraphs:':<28}{self['paragraphs']}",
            f"{'lines:':<28}{self['lines']}",
            f"{'whitespaces:':<28}{self['whitespaces']}\n",

            f"{'other characters:':<28}{self['other characters']}"
        ]
        return "\n".join(temp)


def statistics(
    path: str,
    suffix: str = ".md",
    recursive: bool = True,
    verbose: bool = False,
    redirect: str = None,
    redirect_mode: Literal["w", "a"] = "w"
) -> None:
    stat = Stat()
    overview: List[Tuple[str, Stat]] = []
    path_list = iterdir(path, suffix, recursive)
    path_list.sort()
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
        if verbose:
            overview.append((f"{i.name}", _stat))
        stat.update(_stat)
    message = f"STATISTICS{SEP}" + str(stat)
    if verbose:
        details = f"{SEP}".join(
            f"file: {i[0]}\n\n{i[1]}" for i in overview
        )
        message += f"\n\n\nDETAILS{SEP}{details}"
    if redirect is not None:
        with open(redirect, mode=redirect_mode, newline="\n") as f:
            print(message, file=f)
    else:
        print(message)


def __format(args: argparse.Namespace) -> None:
    format(path=args.f, recursive=args.r)


def __stats(args: argparse.Namespace) -> None:
    statistics(path=args.f, recursive=args.r, verbose=args.v)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, title="subcommand", metavar="")
    parser_format = subparsers.add_parser("format", help="format markdown files")
    parser_format.add_argument("-f", default=".", metavar="", help="file or diractory path (current working directory by default)")
    parser_format.add_argument("-r", action="store_true", default=True, help="execute recursively, if a directory is passed")
    parser_format.set_defaults(func=__format)
    parser_stats = subparsers.add_parser("stats", help="show statistics")
    parser_stats.add_argument("-f", default=".", metavar="", help="file or diractory path (current working directory by default)")
    parser_stats.add_argument("-r", action="store_true", default=True, help="execute recursively, if a directory is passed")
    parser_stats.add_argument("-v", action="store_true", default=False, help="print verbosely")
    parser_stats.set_defaults(func=__stats)
    args = parser.parse_args()
    args.func(args)
    print("\n\nfinished.")


if __name__ == "__main__":
    main()

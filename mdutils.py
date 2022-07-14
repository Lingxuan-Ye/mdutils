import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Callable, Container, List, Literal, NamedTuple, Tuple

__all__ = ["iterdir", "format", "statistics"]

SEP = "\n" + "-" * 40 + "\n"


def iterdir(
    path: str,
    suffixes: Container[str] = None,
    recursive: bool = True
) -> List[Path]:
    stack = [Path(path)]
    if not suffixes:  # None or empty
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


class FormatResult(NamedTuple):

    output: str
    questionable: bool


def __formatfunc_default(raw: str) -> FormatResult:
    temp = raw.strip() + "\n"

    # replace multiple blank lines by one
    temp = re.sub(r"\n{3,}", "\n\n", temp)

    # [[button]](src) -> [[ button ]](src)
    # [button] -> [ button ]
    temp = re.sub(r"\[(?=[^\s\[\]][^\]]*\][^(])","[ ", temp)
    temp = re.sub(r"(?<=[^\s\]\[])\](?!\()", " ]", temp)
    # temp = re.sub(r"\[\[(?=\S)", "[[ ", temp)
    # temp = re.sub(r"(?<=\S)\]\]", " ]]", temp)

    # remove spaces at end of each line
    temp = re.sub(r" +\n", "\n", temp)

    # add one space for '“ (\u201c)' and '” (\u201d)'
    temp = re.sub(r"(?<=\w)(“| {2,}“)", " “", temp)
    temp = re.sub(r"(”|” {2,})(?=\w)", "” ", temp)

    if re.search(r"`.*`", raw) is not None:
        # raw text contains code block
        return FormatResult(temp, True)
    else:
        return FormatResult(temp, False)


def format(
    path: str,
    formatfunc: Callable[[str], FormatResult] = __formatfunc_default,
    suffixes: Container[str] = None,
    recursive: bool = True
) -> None:
    for i in iterdir(path, suffixes, recursive):
        with open(i, encoding="utf-8") as f:
            raw = f.read()
            result = formatfunc(raw)
            with open(i, "w", newline="\n", encoding="utf-8") as g:
                g.write(result.output)
            if result.questionable:
                path_ = Path(i)
                copy_name = path_.stem + "_raw" + path_.suffix
                copy_to = path_.parent / copy_name
                with open(copy_to, "w", newline="\n", encoding="utf-8") as g:
                    g.write(raw)
                print(f"ambiguity warning in file '{i}'")


class Stat(Counter):

    def __repr__(self) -> str:
        temp = [
            f"{'Paragraphs:':<32}{self['paragraphs']}",
            f"{'Non-Blank Lines:':<32}{self['non_blank_lines']}",
            f"{'Lines:':<32}{self['lines']}\n",

            f"{'Words:':<32}{self['words']}",
            f"{'Chinese:':<32}{self['CJK']}",
            f"{'Hiragana:':<32}{self['Hiragana']}",
            f"{'Katakana:':<32}{self['Katakana']}",
            f"{'Punctuations:':<32}{self['punctuations']}",
            f"{'Whitespaces:':<32}{self['whitespaces']}",
            f"{'Other Characters:':<32}{self['other_chars']}\n",

            f"{'Characters (no spaces):':<32}{self['chars_no_spaces']}",
            f"{'Characters (with spaces):':<32}{self['chars_with_spaces']}"
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
    path_list = iterdir(path, suffixes, recursive)
    files = len(path_list)
    print_verbosely = verbose and files > 0
    if print_verbosely:
        inventory: List[Tuple[str, Stat]] = []
    path_list.sort()
    stat = Stat()

    for i in path_list:

        with open(i, encoding="utf-8") as f:
            raw = f.read()

        _stat = Stat()
        _goups: List[Tuple[str, ...]] = re.findall(
            r"([\u4E00-\u9FFF])|"
            r"([\u3400-\u4DBF\U00020000-\U0002A6DF\U0002A700-\U0002EBEF\U00030000-\U0003134F])|"
            r"([\u3040-\u309F])|"
            r"([\u30A0-\u30FF])|"
            r"(\w)|"
            r"(\S)|"
            r"((\s*\n)+)|"
            r"(\s)|"
            r"(.)",
            raw,
            # flags=re.DOTALL
        )
        for j, k, l, m, n, o, p, _, q, r in _goups:
            # note that bool("") is False
            if j:  # CJK Unified Ideographs
                _stat["CJK"] += 1
                _stat["words"] += 1
            elif k:  # CJK Extension
                _stat["CJK"] += 1
                _stat["words"] += 1
            elif l:  # Hiragana
                _stat["Hiragana"] += 1
                _stat["words"] += 1
            elif m:  # Katakana
                _stat["Katakana"] += 1
                _stat["words"] += 1
            elif n:  # r"\w"
                _stat["words"] += 1
            elif o:  # r"\S"
                _stat["punctuations"] += 1
            elif p:  # r"(\s*\n)+"
                _linefeeds: int = p.count("\n")
                if _linefeeds > 1:
                    _stat["paragraphs"] += 1
                _stat["non_blank_lines"] += 1
                _stat["lines"] += _linefeeds
                _stat["whitespaces"] += len(p)
            elif q:  # r"\s"; note that bool(" ") is True
                _stat["whitespaces"] += 1
            elif r: # r"."
                _stat["other_chars"] += 1
        _linefeeds_at_EOF: int = _goups[-1][7].count("\n")
        if _linefeeds_at_EOF == 0:
            _stat["paragraphs"] += 1
            _stat["non_blank_lines"] += 1
            _stat["lines"] += 1
        elif _linefeeds_at_EOF == 1:
            _stat["paragraphs"] += 1
        _stat["chars_no_spaces"] = _stat["words"] + _stat["punctuations"] + _stat["other_chars"]
        _stat["chars_with_spaces"] = _stat["chars_no_spaces"] + _stat["whitespaces"]
        stat.update(_stat)

        if print_verbosely:
            inventory.append((f"{i.name}", _stat))

    message = f"STATISTICS{SEP}{'Files:':<32}{files}\n\n{stat}\n"

    if print_verbosely:
        details = f"{SEP}".join(
            f"File Name: {i[0]}\n\n{i[1]}" for i in inventory
        )
        message += f"\n\nDETAILS{SEP}{details}\n"

    if redirect_to is not None:
        with open(redirect_to, mode=redirect_mode, encoding="utf-8", newline="\n") as f:
            f.write(message)
    else:
        print("\n")
        print(message, end="")


def __format(args: argparse.Namespace) -> None:
    path: str = args.f
    suffixes: List[str] = []
    temp = re.search(r"\.\w+$", path)
    if temp is not None:
        suffixes.append(temp.group())
    if args.s is not None:
        suffixes.extend(args.s)
    if args.e is not None:
        suffixes.extend(args.e)
    format(path, suffixes=suffixes)


def __stats(args: argparse.Namespace) -> None:
    path: str = args.f
    suffixes: List[str] = []
    temp = re.search(r"\.\w+$", path)
    if temp is not None:
        suffixes.append(temp.group())
    if args.s is not None:
        suffixes.extend(args.s)
    if args.e is not None:
        suffixes.extend(args.e)
    if args.R is None:
        statistics(path, suffixes, True, args.v)
    else:
        statistics(path, suffixes, True, args.v, args.R[0], args.R[1])


def main():
    parser = argparse.ArgumentParser(prog="mdutils")
    subparsers = parser.add_subparsers(required=True, title="subcommand", metavar="")
    parser_format = subparsers.add_parser("format", help="format markdown files")
    parser_format.add_argument("-f", default=".", metavar="", help="file or diractory path (current working directory by default)")
    parser_format.add_argument("-s", action="extend", nargs="+", metavar="", help="specify suffix(es), '.md' for example")
    parser_format.add_argument("-e", action="extend", nargs="+", metavar="", help="specify extension(s), 'md' for example")
    parser_format.set_defaults(func=__format)
    parser_stats = subparsers.add_parser("stats", help="show statistics")
    parser_stats.add_argument("-f", default=".", metavar="", help="file or diractory path (current working directory by default)")
    parser_stats.add_argument("-s", action="extend", nargs="+", metavar="", help="specify suffix(es), '.md' for example")
    parser_stats.add_argument("-e", action="extend", nargs="+", metavar="", help="specify extension(s), 'md' for example")
    parser_stats.add_argument("-v", action="store_true", default=False, help="print verbosely")
    parser_stats.add_argument("-R", action="extend", nargs=2, metavar="", help="redirect output; pos 1: file path, pos 2: 'w' for 'write', 'a' for 'append', raise exception elsewise")
    parser_stats.set_defaults(func=__stats)
    args = parser.parse_args()
    args.func(args)
    print("\nfinished.\n")


if __name__ == "__main__":
    main()

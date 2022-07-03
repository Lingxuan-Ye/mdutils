from pathlib import Path
import re

lst = list(Path().iterdir())
lst_ = []

while lst:
    path = lst.pop()
    if path.is_file():
        if path.suffix == ".md":
            lst_.append(path)
    elif path.is_dir():
        lst.extend(path.iterdir())

for i in lst_:
    with open(i, 'r', encoding="utf-8") as f:
        content = f.read()
        with open(i, "w", newline="\n",encoding="utf-8") as g:
            g.write(re.sub(r"\n{3,}", "\n\n", content))

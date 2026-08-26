r"""Apply every round's edits to the markdown source as well as to the LaTeX.

`paper/penumbra-revised.docx` is what the submission is built from; `paper/penumbra-kbs.md` is what
`scripts/check_paper.py` validates. The edits live in `paper/round*-edits.txt` and `round*-splits*.txt`
and are written against the `.tex`, so applying them here means translating the markup back: `\textbf`
to `**`, `\texttt` to backticks, the accent commands to their letters, `` `` '' `` to curly quotes,
`\(x\)` to `$x$`.

Two kinds of edit cannot be translated and are reported rather than forced:

* anything quoting a `\citet` or `\citep`, because the markdown carries the numeric form and, for
  `\citet`, the author's name that natbib prints;
* the round-three abstract, whose `find` is the docx's old wording and never existed in this file.

Without this the two sources drift on exactly what the readings complained about: regenerate the docx
from the markdown and the revision tags, the number-heavy abstract and the long sentences come back.

    python scripts/sync_markdown_edits.py
    python scripts/sync_markdown_edits.py --check    # report, change nothing
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

MD = ROOT / "paper" / "penumbra-kbs.md"

# Edits with no counterpart in the round files, because the two sources word the passage differently
# and translating the markup cannot bridge that. The docx carries bracketed placeholders for the
# repository address and the release tag; this file never had them, so the round-six edit written
# against the .tex finds nothing here and this pair does the same work.
MD_ONLY = [
    ("are released as one repository, at the tagged release the reported numbers were computed "
     "from, under the MIT licence.",
     "are released as one repository at <https://github.com/McahitKutsal/Leakage-Horizons>, "
     "under the MIT licence."),
    # The .tex takes the DOI from declaration/MANIFEST.json, which the docx has a placeholder for and
    # this file never did. Written out here rather than left to drift.
    ("The artefact Section 5.1's protocol rests on is deposited separately, with a checksum for "
     "each file,",
     "The artefact Section 5.1's protocol rests on is deposited separately at "
     "<https://doi.org/10.5281/zenodo.22110800>, with a checksum for each file,"),
]


def latex_to_markdown(text: str, accents: dict) -> str:
    """The inverse of what the converter does to markup, as far as it inverts."""
    for ch, cmd in accents.items():
        text = text.replace(cmd, ch)
    text = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", text)
    text = re.sub(r"\\emph\{([^{}]*)\}", r"*\1*", text)
    text = re.sub(r"\\texttt\{((?:[^{}]|\\_)*)\}", lambda m: "`" + m.group(1).replace("\\_", "_") + "`",
                  text)
    text = re.sub(r"``(.*?)''", lambda m: "\u201c" + m.group(1) + "\u201d", text)
    text = re.sub(r"\\\((.*?)\\\)", lambda m: "$" + m.group(1) + "$", text)
    text = re.sub(r"\\url\{([^{}]*)\}", lambda m: "<" + m.group(1) + ">", text)
    return text


def loose(text: str) -> re.Pattern:
    """Match across the markdown's hard line wrapping: any run of whitespace matches any other."""
    return re.compile(r"\s+".join(re.escape(w) for w in text.split()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args()

    import build_jmlr as bj

    # The .tex writes accents as commands; the markdown keeps the letters.
    accents = {ch: cmd for ch, cmd in bj.ACCENTS.items()
               if cmd.startswith("\\") and not cmd.startswith("\\(")}

    text = before = MD.read_text(encoding="utf-8")

    n = len(re.findall(bj.REGEX_EDITS[0][0], text))
    text = re.sub(bj.REGEX_EDITS[0][0], bj.REGEX_EDITS[0][1], text)
    print(f"  revision tags removed: {n}")

    applied = already = 0
    untranslatable, missing = [], []
    for path in bj.EDITS_FILES:
        for reason, find, replace in bj.load_edits(path):
            if re.search(r"\\cite[tp]\{", find):
                untranslatable.append((path.name, reason))
                continue
            f = latex_to_markdown(find, accents)
            r = latex_to_markdown(replace, accents)
            # "Already applied" is tested first, because an insertion keeps its own `find` inside its
            # `replace` — the acknowledgement edit adds a sentence after one that stays. Testing hits
            # first re-applied it on every run, and this file, unlike the .tex, is not rebuilt from
            # the docx each time, so the sentence accumulated.
            if r and loose(r).search(text):
                already += 1
                continue
            hits = len(loose(f).findall(text))
            if hits == 1:
                text = loose(f).sub(lambda _: r, text, count=1)
                applied += 1
            elif hits > 1:
                missing.append((path.name, reason + f" [matches {hits} times]"))
            else:
                missing.append((path.name, reason))

    md_done = md_already = 0
    for find, replace in MD_ONLY:
        if loose(replace).search(text):
            md_already += 1
        elif len(loose(find).findall(text)) == 1:
            text = loose(find).sub(lambda _: replace, text, count=1)
            md_done += 1
        else:
            missing.append(("MD_ONLY", find[:60]))
    if md_done or md_already:
        print(f"  markdown-only edits: {md_done} applied, {md_already} already in place")

    print(f"  prose edits: {applied} applied, {already} already in place, "
          f"{len(untranslatable)} not translatable, {len(missing)} did not match")
    for name, reason in untranslatable:
        print(f"    quotes a citation, left to the .tex ({name}): {reason}")
    for name, reason in missing:
        print(f"    no match ({name}): {reason}")

    if args.check:
        print("\n--check: nothing written")
        return 0
    if text != before:
        MD.write_text(text, encoding="utf-8", newline="\n")
        print(f"  wrote {MD.relative_to(ROOT)}")
    else:
        print("  nothing to change")
    return 0


if __name__ == "__main__":
    sys.exit(main())

r"""Bundle paper/jmlr into one archive for Overleaf, and check the archive rather than trust it.

Overleaf takes a zip whose root is the project root, so `penumbra.tex` and `jmlr2e.sty` sit at the top
and the figures sit in `figures/`. Anything else in the directory — the README, JMLR's own sample, the
kept pandoc output — is working material and stays out.

The archive is checked after it is written, not before: every file the document asks for has to be in
it, under the name the document uses. A missing style file or a figure one directory too deep is the
usual way an upload compiles locally and not on Overleaf.

    python scripts/pack_jmlr.py
"""
from __future__ import annotations

import hashlib
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "jmlr"
OUT = SRC / "penumbra-overleaf.zip"

# What a compile needs, and nothing else.
INCLUDE = ["penumbra.tex", "penumbra.bib", "jmlr2e.sty"]
EXCLUDE = {"README.md", "sample.tex", "_raw.tex", "captions-trimmed.md", OUT.name}


def main() -> int:
    tex = (SRC / "penumbra.tex").read_text(encoding="utf-8")

    members: dict[str, Path] = {}
    for name in INCLUDE:
        p = SRC / name
        if not p.exists():
            raise SystemExit(f"FAIL: {name} is not in {SRC}")
        members[name] = p

    # Every figure the document includes, under the path the document writes.
    wanted = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex)
    if not wanted:
        raise SystemExit("FAIL: the document includes no figures, which cannot be right")
    for rel in wanted:
        p = (SRC / rel).resolve()
        if not p.exists():
            raise SystemExit(f"FAIL: the document asks for {rel} and it is not on disk")
        members[rel] = p

    # The bibliography has to be findable under the name \bibliography gives.
    bib = re.search(r"\\bibliography\{([^}]*)\}", tex)
    if not bib:
        raise SystemExit("FAIL: no \\bibliography in the document")
    if f"{bib.group(1)}.bib" not in members:
        raise SystemExit(f"FAIL: the document cites {bib.group(1)}.bib and the archive has "
                         f"{[m for m in members if m.endswith('.bib')]}")

    left_out = sorted(p.name for p in SRC.iterdir()
                      if p.is_file() and p.name not in members and p.name not in EXCLUDE)
    if left_out:
        raise SystemExit(f"FAIL: {left_out} is in paper/jmlr and neither packed nor listed as "
                         "working material; decide which it is")

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, path in sorted(members.items()):
            z.write(path, arc)

    # Read the archive back. A listing built from the same dict that wrote it proves nothing, and
    # neither does a name, so each entry is compared with the file on disk byte for byte. This
    # confirms the write landed; it cannot catch an archive that went stale, because this script
    # rewrites it from disk every time it runs. What catches that is in build_jmlr.py, which knows
    # when the .tex has just changed.
    with zipfile.ZipFile(OUT) as z:
        packed = set(z.namelist())
        bad = z.testzip()
        if bad:
            raise SystemExit(f"FAIL: {bad} is corrupt in the archive")
        stale = []
        for arc, path in sorted(members.items()):
            if hashlib.sha256(z.read(arc)).hexdigest() != \
                    hashlib.sha256(path.read_bytes()).hexdigest():
                stale.append(arc)
        if stale:
            raise SystemExit(f"FAIL: the archive holds an older version of {stale}")
    missing = sorted(set(members) - packed)
    if missing:
        raise SystemExit(f"FAIL: written but not in the archive: {missing}")

    size = OUT.stat().st_size
    print(f"wrote {OUT.relative_to(ROOT)}  ({size:,} bytes, {len(packed)} files)")
    for name in sorted(packed):
        print(f"  {name:34s} {(SRC / name).stat().st_size:>9,} bytes")
    print()
    print("Overleaf: New Project -> Upload Project -> this file.")
    print("Then Menu -> Compiler: pdfLaTeX, and check the main document is penumbra.tex.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

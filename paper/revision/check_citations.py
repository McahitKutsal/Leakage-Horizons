"""Citation audit.

1. every in-text citation resolves to an entry in the reference list
2. every entry in the reference list is cited at least once
3. the author-year form in the text matches the entry's author count
   (one author -> "Surname, year"; two -> "A and B, year"; three or more -> "A et al., year")
4. no entry is duplicated, and the list is in alphabetical order
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
MD = (HERE / "manuscript.md").read_text(encoding="utf-8")

body, _, refs = MD.partition("## References")
refs, _, _ = refs.partition("## Declaration of competing interest")

fail = 0


def report(ok, title, detail=""):
    global fail
    print(("  PASS  " if ok else "  FAIL  ") + title)
    for line in detail.splitlines():
        if line:
            print("          " + line)
    if not ok:
        fail += 1


# ---- parse the reference list ------------------------------------------
# "Surname, A. B., and Other, C. (1999). Title..."  /  "Surname, A. (1999)."
ENTRY = re.compile(r"^([A-ZÀ-Ý][^(]*?)\((\d{4}[a-z]?)\)\.", re.M)

entries = []
for m in ENTRY.finditer(refs):
    authors_raw, year = m.group(1).strip(), m.group(2)
    # surnames are the tokens that precede a comma-initial group
    surnames = re.findall(r"(?:^|,\s+and\s+|,\s+|^and\s+)"
                          r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’\-]+(?:\s+(?:von|van|de|der))?)"
                          r",\s+[A-ZÀ-Ý]\.", authors_raw)
    if not surnames:
        surnames = [authors_raw.split(",")[0].strip()]
    etal = "et al." in authors_raw
    entries.append({"surnames": surnames, "year": year, "etal": etal,
                    "raw": authors_raw})

report(len(entries) >= 40, f"reference list parsed: {len(entries)} entries")


def expected_key(e):
    s = e["surnames"]
    if e["etal"] or len(s) >= 3:
        return f"{s[0]} et al., {e['year']}"
    if len(s) == 2:
        return f"{s[0]} and {s[1]}, {e['year']}"
    return f"{s[0]}, {e['year']}"


expected = {expected_key(e): e for e in entries}

dupes = [k for k in expected if sum(1 for e in entries
                                    if expected_key(e) == k) > 1]
report(not dupes, "no duplicated reference entries",
       "duplicated: " + ", ".join(dupes) if dupes else "")

alpha = [e["surnames"][0].lower() for e in entries]
out_of_order = [f"{a} before {b}" for a, b in zip(alpha, alpha[1:]) if a > b]
report(not out_of_order, "reference list is in alphabetical order",
       "\n".join(out_of_order) if out_of_order else "")

# ---- collect citations from the body -----------------------------------
NAME = r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’\-]+"
PAREN = re.compile(r"\((" + NAME + r"(?: et al\.| and " + NAME + r")?,\s*\d{4}[a-z]?"
                   r"(?:;\s*" + NAME + r"(?: et al\.| and " + NAME + r")?,\s*\d{4}[a-z]?)*)\)")
NARRATIVE = re.compile(r"\b(" + NAME + r"(?: et al\.| and " + NAME + r")?)"
                       r"(?:'s)?\s+\((\d{4}[a-z]?)\)")

found = set()
for m in PAREN.finditer(body):
    for part in m.group(1).split(";"):
        found.add(re.sub(r"\s+", " ", part.strip()))
for m in NARRATIVE.finditer(body):
    found.add(f"{m.group(1).strip()}, {m.group(2)}")

report(len(found) >= 30, f"citations found in the body: {len(found)} distinct")

unresolved = sorted(c for c in found if c not in expected)
report(not unresolved, "every citation resolves to a reference entry",
       "\n".join(unresolved) if unresolved else "")

uncited = sorted(k for k in expected if k not in found)
report(not uncited, "every reference entry is cited",
       "\n".join(uncited) if uncited else "")

print()
if fail:
    print(f"{fail} citation check(s) failed")
    sys.exit(1)
print("all citation checks passed")

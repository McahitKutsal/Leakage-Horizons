"""Check every reference in the manuscript against the publisher record.

For each entry carrying a DOI, fetch the Crossref record and compare the year,
the first author's surname, the container title, the volume and the pages with
what the manuscript prints. Entries without a DOI (books, some proceedings) are
listed for manual confirmation rather than guessed at.

Writes a report to reference-audit.txt and exits non-zero on any mismatch.
"""
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
MD = (HERE / "manuscript.md").read_text(encoding="utf-8")
# Crossref's polite pool wants a contact address; override it with your own.
MAILTO = os.environ.get("CROSSREF_MAILTO", "mucahitkutsal@ankara.edu.tr")

_, _, refs = MD.partition("## References")
refs, _, _ = refs.partition("## Declaration of competing interest")
lines = [l.strip() for l in refs.split("\n") if l.strip()]

DOI = re.compile(r"https://doi\.org/(10\.\S+?)\s*$")
YEAR = re.compile(r"\((\d{4})[a-z]?\)\.")
VOLPAGES = re.compile(r"\*,?\s*(\d+)(?:\((\d+|[A-Z]\d+)\))?,\s*([\w–\-]+)")
TITLE = re.compile(r"\(\d{4}[a-z]?\)\.\s*(.+?)\.\s*(?:In\s+)?[*]")


def crossref(doi):
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": f"penumbra-reference-audit/1.0 (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=25) as fh:
        return json.load(fh)["message"]


def norm(s):
    s = s.lower().replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", "", s)


rows, problems, nodoi = [], [], []
for line in lines:
    m = DOI.search(line)
    year_m = YEAR.search(line)
    surname = line.split(",")[0].strip()
    if not year_m:
        continue
    year = year_m.group(1)
    if not m:
        nodoi.append(f"{surname} ({year}) — no DOI printed: {line[:95]}")
        continue
    doi = m.group(1).rstrip(".")
    try:
        rec = crossref(doi)
    except urllib.error.HTTPError as exc:
        problems.append(f"{surname} ({year}) — DOI {doi} not found "
                        f"at Crossref (HTTP {exc.code})")
        continue
    except Exception as exc:                         # network hiccup
        problems.append(f"{surname} ({year}) — DOI {doi} lookup failed: {exc}")
        continue

    issued = rec.get("issued", {}).get("date-parts", [[None]])[0][0]
    authors = rec.get("author") or []
    cr_surname = (authors[0].get("family") if authors else "") or ""
    cr_title = (rec.get("title") or [""])[0]
    cr_vol, cr_page = rec.get("volume"), rec.get("page")

    bad = []
    # a book chapter or a reissue can be indexed under a later year, so allow
    # a one-year drift and report anything wider
    if issued and abs(int(issued) - int(year)) > 1:
        bad.append(f"year {year} vs Crossref {issued}")
    if cr_surname and norm(cr_surname) != norm(surname):
        bad.append(f"first author '{surname}' vs Crossref '{cr_surname}'")

    vp = VOLPAGES.search(line)
    if vp and cr_vol and vp.group(1) != str(cr_vol):
        bad.append(f"volume {vp.group(1)} vs Crossref {cr_vol}")
    if vp and cr_page and norm(vp.group(3)) != norm(cr_page):
        # Crossref often stores only the first page for older journal records,
        # so a printed range whose start agrees is right and the record is thin
        start = re.split(r"[–\-]", vp.group(3))[0]
        if norm(start) != norm(cr_page):
            bad.append(f"pages {vp.group(3)} vs Crossref {cr_page}")

    # the strongest check: a DOI that resolves to a different paper
    tm = TITLE.search(line)
    if tm and cr_title:
        ours, theirs = norm(tm.group(1)), norm(cr_title)
        if ours not in theirs and theirs not in ours:
            shared = len(set(re.findall(r"[a-z]{4,}", tm.group(1).lower()))
                         & set(re.findall(r"[a-z]{4,}", cr_title.lower())))
            if shared < 3:
                bad.append(f"title '{tm.group(1)[:50]}' vs Crossref "
                           f"'{cr_title[:50]}'")

    rows.append((surname, year, doi, cr_title[:70], bad))
    if bad:
        problems.append(f"{surname} ({year}) — " + "; ".join(bad))
    time.sleep(0.12)

out = [f"Reference audit against Crossref, {len(rows)} entries with a DOI, "
       f"{len(nodoi)} without.", ""]
for surname, year, doi, title, bad in rows:
    flag = "  !!" if bad else "    "
    out.append(f"{flag} {surname} {year}  {doi}")
    out.append(f"       {title}")
    for b in bad:
        out.append(f"       -> {b}")
out.append("")
out.append("Entries with no DOI, to confirm by hand:")
out.extend("  " + n for n in nodoi)
(HERE / "reference-audit.txt").write_text("\n".join(out), encoding="utf-8")

print(f"checked {len(rows)} DOIs, {len(nodoi)} entries without a DOI")
for n in nodoi:
    print("  no DOI:", n[:110])
if problems:
    print()
    for p in problems:
        print("  MISMATCH:", p)
    print(f"\n{len(problems)} reference problem(s); see reference-audit.txt")
    sys.exit(1)
print("every DOI resolves and agrees with the manuscript")

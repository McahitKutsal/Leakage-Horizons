r"""Check every bibliography entry against the publisher's own record.

`build_jmlr.py` checks that every citation resolves to an entry and that every entry is cited, and
`check_paper.py` checks that a named work is cited to the entry that names it. Neither checks whether
the entry is *right*: a wrong year, a misspelled author, a paper attributed to the wrong venue. Those
are the cheapest thing for a reviewer to find and the least defensible to have got wrong, so they are
checked against CrossRef, which is the publisher's own deposit rather than a reference manager's guess.

What is compared, per entry with a DOI:

* the DOI resolves at all;
* the title, ignoring case, punctuation and LaTeX braces, and joined with the subtitle: ACM deposits
  the part after the question mark separately and a full title has to match the whole of it;
* the year, taken as the print or issue year rather than CrossRef's `published`, which returns the
  earliest date it holds. Nine of our entries are online-first a year before their issue, and the
  issue year is the one a citation carries. Reading the wrong field made nine correct entries look
  wrong, which is the sort of check that gets switched off;
* the container title -- journal or proceedings -- ignoring case and common abbreviations;
* the first author's family name, and the number of authors.

Entries with no DOI are listed rather than skipped silently. NeurIPS and ICLR proceedings mint none,
which is why six of ours have none, and those have to be read by eye.

    python scripts/check_citations.py
    python scripts/check_citations.py --json out.json
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "paper" / "jmlr" / "penumbra.bib"
UA = "penumbra-citation-check/1.0"
_last_dblp = 0.0


def parse_bib(text: str) -> list:
    out = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", text, re.S):
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|\d+)",
                              m.group(3)):
            v = fm.group(2).strip()
            if v[:1] in "{\"":
                v = v[1:-1]
            fields[fm.group(1).lower()] = re.sub(r"\s+", " ", v).strip()
        out.append({"kind": m.group(1).lower(), "key": m.group(2).strip(), **fields})
    return out


def flat(s: str) -> str:
    """Compare titles by their letters: braces, accents, punctuation and case all go.

    Entities and ampersands are normalised too. ACM deposits "Knowledge Discovery &amp; Data Mining"
    where the entry says "and", which is the same venue and was the last thing this check complained
    about.
    """
    s = html.unescape(s).replace("&", " and ")
    s = re.sub(r"\{|\}|\\[a-zA-Z]+", " ", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


VENUE_ALIASES = {
    "proceedingsofthenationalacademyofsciences": "pnas",
    "proceedingsofthenationalacademyofsciencesoftheunitedstatesofamerica": "pnas",
    "journalofmachinelearningresearch": "jmlr",
    "communicationsoftheacm": "cacm",
    "acmcomputingsurveys": "csur",
    "acmtransactionsonknowledgediscoveryfromdata": "tkdd",
}


def venue_key(s: str) -> str:
    f = flat(s)
    return VENUE_ALIASES.get(f, f)


def bib_authors(s: str) -> list:
    """Family names, in order, from a BibTeX author field."""
    out = []
    for chunk in re.split(r"\s+and\s+", s):
        chunk = chunk.strip().strip(",")
        if not chunk:
            continue
        out.append(flat(chunk.split(",")[0] if "," in chunk else chunk.split()[-1]))
    return out


def crossref(doi: str) -> dict | None:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as fh:
            return json.load(fh)["message"]
    except urllib.error.HTTPError as e:
        return {"__error__": f"HTTP {e.code}"}
    except Exception as e:                                   # noqa: BLE001
        return {"__error__": type(e).__name__}


# Deposits where CrossRef is wrong and the entry is right. Listed rather than tolerated silently,
# because "the publisher's record disagrees" is only useful if the disagreements are all real.
CROSSREF_WRONG = {
    "datasheets": "ACM deposited the author as given \"Hal Daum\u00e9\" family \"III\"; the family "
                  "name is Daum\u00e9 III and the entry has it right",
}


def dblp(title: str) -> list | None:
    """Candidate records from DBLP, which indexes the proceedings that mint no DOI.

    Returns [] when DBLP answers and has nothing, and None when it would not answer. The difference
    matters: the first version swallowed every exception into [], DBLP rate-limited the fifth and
    sixth query in a row, and two entries that DBLP knows perfectly well were reported as verified
    because "nothing found" and "not asked" had become the same value.
    """
    url = ("https://dblp.org/search/publ/api?format=json&h=6&q="
           + urllib.parse.quote(re.sub(r"[{}\\]", "", title)))
    # DBLP throttles a run of queries from one client, and the six entries with no DOI arrive in a
    # run. A pause between them costs eighteen seconds and is the difference between six answers and
    # five entries reported as unchecked.
    global _last_dblp
    wait = 3.0 - (time.monotonic() - _last_dblp)
    if wait > 0:
        time.sleep(wait)
    _last_dblp = time.monotonic()

    hits = None
    for attempt in range(4):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as fh:
                hits = json.load(fh)["result"].get("hits", {}).get("hit", [])
            break
        except Exception:                                    # noqa: BLE001
            if attempt == 3:
                return None
            time.sleep(2 * (attempt + 1))                    # DBLP throttles a run of queries
    if hits is None:
        return None
    out = []
    for h in hits:
        i = h.get("info", {})
        au = i.get("authors", {}).get("author", [])
        au = [au] if isinstance(au, dict) else au
        out.append({"title": i.get("title", ""), "year": i.get("year", ""),
                    "venue": i.get("venue", ""),
                    "authors": [a.get("text", "") for a in au]})
    return out


def check_without_doi(entry: dict) -> dict:
    """The six proceedings papers with no DOI, checked against DBLP instead.

    NeurIPS, ICLR and the workshop tracks mint no DOI, so "no DOI" is not a defect and not a reason to
    leave an entry unchecked. DBLP indexes them, and the title, year, first author and author count
    are exactly what would embarrass us if they were wrong.
    """
    r = {"key": entry["key"], "doi": "", "problems": [], "note": "checked against DBLP"}
    ours_title = flat(entry.get("title", ""))
    hits = dblp(entry.get("title", ""))
    if hits is None:
        r["note"] = "no DOI, and DBLP would not answer; UNCHECKED"
        r["unchecked"] = True
        return r
    if not hits:
        r["note"] = "no DOI, and DBLP has no record of this title; UNCHECKED"
        r["unchecked"] = True
        return r
    exact = [h for h in hits if flat(h["title"]).rstrip("0123456789.") == ours_title
             or flat(h["title"]) == ours_title]
    if not exact:
        r["problems"].append(f"DBLP has no record with this title; nearest is "
                             f"{hits[0]['title']!r} ({hits[0]['year']})")
        return r
    years = {h["year"] for h in exact}
    if str(entry.get("year", "")) not in years:
        r["problems"].append(f"year is {entry.get('year')} and DBLP has {sorted(years)}")
    ours = bib_authors(entry.get("author", ""))
    # DBLP disambiguates homonyms with a four-digit suffix: "Emanuele Rossi 0001". It is not a name.
    def family(name: str) -> str:
        toks = [t for t in name.split() if not re.fullmatch(r"\d{4}", t)]
        return flat(toks[-1]) if toks else ""

    theirs = [family(a) for a in exact[0]["authors"] if a.split()]
    if ours and theirs:
        if ours[0] != theirs[0]:
            r["problems"].append(f"first author: ours {ours[0]!r} against DBLP {theirs[0]!r}")
        if len(ours) != len(theirs):
            r["problems"].append(f"{len(ours)} authors listed and DBLP has {len(theirs)}")
    r["dblp"] = exact[0]
    return r


def check(entry: dict) -> dict:
    doi = entry.get("doi", "")
    r = {"key": entry["key"], "doi": doi, "problems": [], "note": ""}
    if not doi:
        return check_without_doi(entry)
    m = crossref(doi)
    if m is None or "__error__" in m:
        r["problems"].append(f"the DOI does not resolve at CrossRef ({m['__error__']})")
        return r

    got_title = (m.get("title") or [""])[0]
    if m.get("subtitle") and m["subtitle"][0]:
        got_title = got_title.rstrip() + " " + m["subtitle"][0]
    if flat(entry.get("title", "")) != flat(got_title):
        # a subtitle dropped on one side is worth reporting but is not the same as a wrong paper
        a, b = flat(entry.get("title", "")), flat(got_title)
        kind = "differs in part" if (a in b or b in a) else "does not match"
        r["problems"].append(f"title {kind}: ours {entry.get('title','')!r} against {got_title!r}")

    # The print or issue year, not `published`, which CrossRef defines as the earliest date it has.
    years = []
    for field in ("published-print", "issued", "published-online", "published"):
        parts = (m.get(field) or {}).get("date-parts") or [[None]]
        if parts[0][0]:
            years.append((field, parts[0][0]))
    ours_year = str(entry.get("year", ""))
    if years and ours_year not in {str(y) for _, y in years}:
        r["problems"].append(f"year is {ours_year} and CrossRef holds "
                             + ", ".join(f"{y} ({f})" for f, y in years))
    elif years and ours_year != str(years[0][1]):
        r["note"] = (f"year {ours_year} is the {dict((str(y), f) for f, y in years)[ours_year]} "
                     f"date; CrossRef's earliest is {years[0][1]}")

    ours_venue = entry.get("journal") or entry.get("booktitle") or entry.get("publisher") or ""
    got_venue = (m.get("container-title") or [""])[0]
    if ours_venue and got_venue and venue_key(ours_venue) != venue_key(got_venue):
        if venue_key(ours_venue) not in venue_key(got_venue) and \
                venue_key(got_venue) not in venue_key(ours_venue):
            r["problems"].append(f"venue: ours {ours_venue!r} against {got_venue!r}")

    ours = bib_authors(entry.get("author", ""))
    theirs = [flat(a.get("family", "")) for a in m.get("author", []) if a.get("family")]
    if ours and theirs:
        if ours[0] != theirs[0]:
            r["problems"].append(f"first author: ours {ours[0]!r} against {theirs[0]!r}")
        if len(ours) != len(theirs):
            r["problems"].append(f"{len(ours)} authors listed and CrossRef has {len(theirs)}")
        wrong = [(o, t) for o, t in zip(ours, theirs) if o != t]
        if entry["key"] in CROSSREF_WRONG:
            wrong = []
            r["note"] = CROSSREF_WRONG[entry["key"]]
        if wrong and ours[0] == theirs[0]:
            r["problems"].append(f"author order or spelling differs at {len(wrong)} position(s): "
                                 f"{wrong[:3]}")
    r["crossref"] = {"title": got_title, "year": years[0][1] if years else None,
                     "years": dict((f, y) for f, y in years), "venue": got_venue,
                     "n_authors": len(theirs)}
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    print(f"checking {len(entries)} entries against CrossRef\n")
    results, bad, nodoi, unchecked = [], 0, 0, 0
    for e in entries:
        r = check(e)
        results.append(r)
        if r["problems"]:
            bad += 1
            print(f"  FAIL {r['key']:16s} {r['doi']}")
            for p in r["problems"]:
                print(f"         {p}")
        elif r.get("unchecked"):
            unchecked += 1
            print(f"  ??   {r['key']:16s} {r['note']}")
        elif not r["doi"]:
            nodoi += 1
            print(f"  ok   {r['key']:16s} {r['note']}")
        elif r["note"]:
            print(f"  ok   {r['key']:16s} {r['doi']}")
            print(f"         note: {r['note']}")
        else:
            print(f"  ok   {r['key']:16s} {r['doi']}")

    print()
    print(f"{len(entries) - bad - nodoi - unchecked} verified against CrossRef, {nodoi} against "
          f"DBLP for want of a DOI, {bad} with a problem, {unchecked} unchecked")
    if unchecked:
        print("  an unchecked entry is not a passing entry; run it again or read it by eye")
    if args.json:
        args.json.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"written to {args.json}")
    return 1 if (bad or unchecked) else 0


if __name__ == "__main__":
    sys.exit(main())

"""Extract COW IGO's per-organisation provenance notes, then check them against the data.

PROTOCOL §1 comes before everything and says two things that pull in opposite directions:
verify coverage against the **materialised** file rather than the documentation, and declare the
provenance per relation in writing. Both are needed, and the interesting cases are the
disagreements -- a gap the codebook declares and the data does not carry, or the reverse.

Section IV of the v2.1 codebook lists all 495 organisations with formation year, termination year,
COW number and free-text notes recording name changes, missing-data years, and how gaps were
filled. It is the closest thing to §5.4's load-bearing provenance paragraph that this source
offers, and the v3 short codebook omits it entirely.

**Version mismatch, declared.** The notes are v2.1; the data is v3 (534 organisations against
495). Organisations present in one and not the other are reported rather than dropped quietly.

    python scripts/parse_igo_provenance.py --json results/igo_provenance.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.crosswalk import IGO_META, IGO_YEAR  # noqa: E402

CODEBOOK = ROOT / "data" / "raw" / "cow_igo" / "codebook_v2.1.pdf"
SECTION_IV_FROM_PAGE = 7          # 1-indexed; section IV opens on this page

# A record header is a number followed by a period and a name. Page numbers appear bare, with no
# period, which is the only reliable discriminator in the extracted text.
HEADER = re.compile(r"^\s*(\d{1,5})\.\s+(\S.*?)\s*$")
FIELD = re.compile(r"^\s*(Formed|Terminated|COW No\.)\s*:\s*(.*?)\s*$", re.I)
# Missing-data declarations come in several shapes: a single year, a hyphenated range, a
# comma-separated list, or several of those on one line.
MISSING = re.compile(r"Missing data\s*:?\s*(.+)", re.I)
YEAR_RANGE = re.compile(r"(1[89]\d{2}|20\d{2})\s*(?:-|–|—|to)\s*(1[89]\d{2}|20\d{2})")
YEAR_ONE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")


def _pages_text() -> str:
    reader = PdfReader(CODEBOOK)
    out = []
    for i, page in enumerate(reader.pages):
        if i + 1 < SECTION_IV_FROM_PAGE:
            continue
        t = page.extract_text() or ""
        # Drop the bare page number the extractor puts at the top of each page.
        t = re.sub(r"^\s*\d{1,3}\s*$", "", t, flags=re.M)
        out.append(t)
    return "\n".join(out)


def _years_from(text: str) -> list[int]:
    years: set[int] = set()
    rest = text
    for m in YEAR_RANGE.finditer(text):
        a, b = int(m.group(1)), int(m.group(2))
        if a <= b and b - a < 200:
            years.update(range(a, b + 1))
        rest = rest.replace(m.group(0), " ")
    years.update(int(m.group(1)) for m in YEAR_ONE.finditer(rest))
    return sorted(years)


def parse_records() -> pd.DataFrame:
    text = _pages_text()
    lines = text.split("\n")

    # Find header lines whose record body actually contains a Formed: field. Without that check a
    # numbered sentence in prose becomes a phantom organisation.
    starts = []
    for i, ln in enumerate(lines):
        m = HEADER.match(ln)
        if not m:
            continue
        window = "\n".join(lines[i + 1:i + 8])
        if re.search(r"Formed\s*:", window, re.I):
            starts.append((i, int(m.group(1)), m.group(2)))

    recs = []
    for k, (i, ionum, name) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        body = lines[i + 1:end]
        fields, notes = {}, []
        for ln in body:
            fm = FIELD.match(ln)
            if fm:
                fields[fm.group(1).lower().rstrip(".")] = fm.group(2)
            elif ln.strip() and not re.match(r"^\s*Notes\s*:", ln, re.I):
                notes.append(ln.strip())
        note_text = " ".join(notes)

        missing: list[int] = []
        for mm in MISSING.finditer(note_text):
            # Stop at the next sentence so an unrelated year later in the notes is not swept in.
            frag = re.split(r"(?<=\d)\s{2,}[A-Z]|\.\s+[A-Z]", mm.group(1))[0]
            missing.extend(_years_from(frag))

        formed = fields.get("formed", "")
        term = fields.get("terminated", "")
        recs.append({
            "ionum": ionum,
            "name_codebook": name,
            "formed_declared": int(YEAR_ONE.search(formed).group(1)) if YEAR_ONE.search(formed) else None,
            "terminated_declared": int(YEAR_ONE.search(term).group(1)) if YEAR_ONE.search(term) else None,
            "inactive_note": bool(re.search(r"inactive|dormant", term + " " + note_text, re.I)),
            "signature_or_accession_note": bool(
                re.search(r"\b(signature|signed|year of accession)\b", note_text, re.I)),
            "missing_years_declared": sorted(set(missing)),
            "n_missing_declared": len(set(missing)),
            "notes": note_text[:800],
        })
    df = pd.DataFrame(recs).drop_duplicates("ionum", keep="first")

    # A record with no Formed: field of its own is not an organisation. Two arise from sentences
    # inside the notes that open with a year and a period -- "1993. Name changes in 1993 to
    # AIDMO." -- which the header pattern cannot distinguish from a record number, and which pass
    # the look-ahead because the NEXT record's Formed: line falls inside the window. Dropping
    # them takes the count to exactly the 495 the codebook states, which is the check.
    phantom = df[df.formed_declared.isna()]
    if len(phantom):
        print(f"dropped {len(phantom)} parse artefacts with no Formed: field of their own: "
              f"{[str(x)[:40] for x in phantom.name_codebook]}")
    return df[df.formed_declared.notna()].reset_index(drop=True)


def materialised_missing() -> pd.DataFrame:
    """Years in which an organisation carries at least one -9 cell, from the v3 file."""
    d = pd.read_csv(IGO_YEAR, sep="\t", low_memory=False, encoding="latin-1")
    state_cols = [c for c in d.columns if c not in IGO_META]
    M = d[state_cols].apply(pd.to_numeric, errors="coerce").to_numpy()
    return pd.DataFrame({"ionum": d.ionum.astype(int), "year": d.year.astype(int),
                         "n_missing": (M == -9).sum(axis=1)})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "igo_provenance.json")
    args = ap.parse_args()

    recs = parse_records()
    print(f"parsed {len(recs)} organisation records from section IV; codebook states 495 "
          f"-> {'MATCH' if len(recs) == 495 else 'MISMATCH, investigate before trusting anything'}")
    print(f"  with a declared formation year   : {int(recs.formed_declared.notna().sum())}")
    print(f"  with a declared termination year : {int(recs.terminated_declared.notna().sum())}")
    print(f"  flagged inactive/dormant in text : {int(recs.inactive_note.sum())}")
    print(f"  mentioning signature/accession   : {int(recs.signature_or_accession_note.sum())}")
    print(f"  declaring missing-data years     : {int((recs.n_missing_declared > 0).sum())}")

    mat = materialised_missing()
    mat_years = (mat[mat.n_missing > 0].groupby("ionum").year
                 .apply(lambda s: set(s.tolist())).to_dict())
    v3_ids = set(mat.ionum.unique())
    cb_ids = set(recs.ionum)
    print(f"\nversion mismatch, declared: v3 has {len(v3_ids)} organisations, "
          f"codebook v2.1 section IV has {len(cb_ids)}")
    print(f"  in both              : {len(v3_ids & cb_ids)}")
    print(f"  v3 only (no notes)   : {len(v3_ids - cb_ids)}")
    print(f"  codebook only        : {len(cb_ids - v3_ids)}")

    rows = []
    for r in recs.itertuples():
        if r.ionum not in v3_ids:
            continue
        decl = set(r.missing_years_declared)
        real = mat_years.get(r.ionum, set())
        rows.append({"ionum": r.ionum, "name": r.name_codebook,
                     "declared": len(decl), "materialised": len(real),
                     "declared_not_materialised": sorted(decl - real),
                     "materialised_not_declared": sorted(real - decl)})
    cmp = pd.DataFrame(rows)
    dnm = cmp[cmp.declared_not_materialised.map(len) > 0]
    mnd = cmp[cmp.materialised_not_declared.map(len) > 0]
    print(f"\ncoverage cross-check over {len(cmp)} shared organisations:")
    print(f"  declared missing but NOT -9 in the data : {len(dnm)} organisations, "
          f"{int(dnm.declared_not_materialised.map(len).sum())} organisation-years")
    print(f"  -9 in the data but NOT declared         : {len(mnd)} organisations, "
          f"{int(mnd.materialised_not_declared.map(len).sum())} organisation-years")
    print("\nThe second direction is the one PROTOCOL §1 is written against: coverage the "
          "documentation does not mention.")
    if len(mnd):
        print("\nlargest undeclared gaps:")
        top = mnd.assign(n=mnd.materialised_not_declared.map(len)).nlargest(8, "n")
        for r in top.itertuples():
            ys = r.materialised_not_declared
            print(f"  ionum {r.ionum:>4} {r.name[:44]:<44} {len(ys):>3} yrs "
                  f"{ys[0]}-{ys[-1]}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps({
        "codebook": "COW IGO v2.1 section IV; the v3 short codebook omits it",
        "data": "igo_year_formatv3",
        "n_records_parsed": int(len(recs)),
        "n_records_claimed_by_codebook": 495,
        "version_mismatch": {"v3_only": sorted(v3_ids - cb_ids),
                             "codebook_only": sorted(cb_ids - v3_ids)},
        "signature_or_accession_flagged": sorted(
            recs.loc[recs.signature_or_accession_note, "ionum"].tolist()),
        "inactive_flagged": sorted(recs.loc[recs.inactive_note, "ionum"].tolist()),
        "coverage_cross_check": {
            "declared_not_materialised_orgs": int(len(dnm)),
            "declared_not_materialised_org_years": int(dnm.declared_not_materialised.map(len).sum()),
            "materialised_not_declared_orgs": int(len(mnd)),
            "materialised_not_declared_org_years": int(mnd.materialised_not_declared.map(len).sum()),
        },
        "records": recs.to_dict("records"),
    }, indent=2, default=str))
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

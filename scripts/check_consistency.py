"""Every number a document asserts must match the results file it came from.

Written because staleness has already bitten three times in this programme: the status header of
`PENUMBRA-OUTCOMES.md` drifted twice, and the accession count 6,290 stood in `DECISIONS.md` and
`LEDGER.md` after the audit that produced it was corrected to 6,115 (D-08). None of those was caught
by reading; the last was caught only because a second code path disagreed.

The registry below pairs each load-bearing claim with the artefact that produces it. A claim whose
source has moved is a failure, not a warning: a document that quotes a number the pipeline no longer
produces is worse than one that quotes none, because it looks verified.

    python scripts/check_consistency.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def jload(name: str):
    p = RESULTS / name
    return json.loads(p.read_text()) if p.exists() else None


def dig(obj, path: str):
    """Walk a dotted path through nested dicts and lists."""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur.get(part)
    return cur


# (document, the literal string that must appear, source file, dotted path, formatter)
# The formatter turns the source value into the exact text the document should contain, so a
# mismatch is a text-level failure rather than a judgement call.
REGISTRY = [
    # -- corpus scale, the evidence behind the section 11 decision (D-03) --
    ("DECISIONS.md", "corpus_scale.json", "atop.multilateral_by_bilat_flag", lambda v: f"{v}"),
    ("DECISIONS.md", "corpus_scale.json", "atop.accessions_multilateral", lambda v: f"{v}"),
    ("DECISIONS.md", "corpus_scale.json", "cow_igo.accessions_in_era", lambda v: f"{v:,}"),
    ("DECISIONS.md", "corpus_scale.json", "cow_igo.entities_alive_in_era", lambda v: f"{v}"),
    # The DESTA figures are asserted in OUTCOMES C7/C9 and in LEDGER's dating-strata table, not in
    # PROVENANCE, which states dating conventions rather than counts. Registering a claim against a
    # document that never made it produces a failure that teaches nothing, so the pairing is fixed
    # rather than the document padded.
    ("PENUMBRA-OUTCOMES.md", "corpus_scale.json", "desta.gap_n", lambda v: f"{v:,}"),
    ("LEDGER.md", "corpus_scale.json", "desta.gap_n", lambda v: f"{v:,}"),
    ("PENUMBRA-OUTCOMES.md", "corpus_scale.json", "desta.signed_never_entered_force",
     lambda v: f"{v}"),
    ("LEDGER.md", "corpus_scale.json", "cow_igo_causes.causes_1946plus.dissolution",
     lambda v: f"{v}"),
    ("LEDGER.md", "corpus_scale.json", "cow_igo_causes.causes_1946plus.absorption_integrated",
     lambda v: f"{v}"),

    # -- provenance parse, the section 5.4 declaration --
    ("PROVENANCE.md", "igo_provenance.json", "n_records_parsed", lambda v: f"{v}"),
    ("PROVENANCE.md", "igo_provenance.json",
     "coverage_cross_check.materialised_not_declared_orgs", lambda v: f"{v}"),
    ("PROVENANCE.md", "igo_provenance.json",
     "coverage_cross_check.materialised_not_declared_org_years", lambda v: f"{v}"),

    # -- LEDGER as built --
    ("LEDGER.md", "ledger_summary.json", "entities.total", lambda v: f"{v}"),
    ("LEDGER.md", "ledger_summary.json", "events.total", lambda v: f"{v:,}"),
    ("LEDGER.md", "ledger_summary.json", "entities.left_truncated", lambda v: f"{v}"),
    ("PENUMBRA-OUTCOMES.md", "ledger_summary.json", "entities.total", lambda v: f"{v}"),

    # -- Delta* calibration on synthetics (C18) --
    ("PENUMBRA-OUTCOMES.md", "delta_star_calibration.json", "invariance.density_range",
     lambda v: "6 of 6" if v == 0.0 else "DENSITY INVARIANCE BROKEN"),
]

NUMERIC = re.compile(r"[-+]?\d[\d,]*\.?\d*")


def main() -> int:
    docs = {p.name: p.read_text(encoding="utf-8") for p in ROOT.glob("*.md")}
    fails, skipped = [], []

    for doc, src, path, fmt in REGISTRY:
        obj = jload(src)
        if obj is None:
            skipped.append(f"{src} missing -> cannot check {doc} / {path}")
            continue
        val = dig(obj, path)
        if val is None:
            skipped.append(f"{src}:{path} absent -> cannot check {doc}")
            continue
        want = fmt(val)
        text = docs.get(doc)
        if text is None:
            fails.append(f"{doc} not found")
            continue
        if want not in text:
            fails.append(f"{doc} does not contain {want!r} from {src}:{path}")

    # Cross-file agreement: the same quantity asserted in two documents must match.
    pairs = [("LEDGER.md", "PENUMBRA-OUTCOMES.md", r"\b573\b", "entity count"),
             ("DECISIONS.md", "LEDGER.md", r"6,115", "corrected accession count")]
    for a, b, pat, label in pairs:
        ha = bool(re.search(pat, docs.get(a, "")))
        hb = bool(re.search(pat, docs.get(b, "")))
        if ha != hb:
            fails.append(f"{label}: present in {a if ha else b} but not {b if ha else a}")

    # The figure D-08 corrected must not have come back anywhere.
    for name, text in docs.items():
        if re.search(r"\b6,?290\b", text) and "D-08" not in text and "6,290 until" not in text:
            fails.append(f"{name} contains the retracted figure 6,290 outside its correction note")

    for s in skipped:
        print(f"  skip  {s}")
    for f in fails:
        print(f"  FAIL  {f}")
    print()
    if fails:
        print(f"{len(fails)} inconsistencies. A document that quotes a number the pipeline no "
              f"longer produces looks verified and is not.")
        return 1
    print(f"ok: {len(REGISTRY)} registered claims match their sources, "
          f"{len(skipped)} unchecked for want of a results file")
    return 0


if __name__ == "__main__":
    sys.exit(main())

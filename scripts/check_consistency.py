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
    # The "6 of 6" claim, counted from the results rather than proxied. This entry previously read
    # `invariance.density_range` and emitted the string "6 of 6" whenever it was 0.0 -- a check on
    # density invariance dressed as a check on the count, which is why nothing noticed when the script's
    # default `--betas` omitted 4 and it began producing "5 of 5" while both documents said six. After
    # D-34 this calibration is the *only* evidence the estimator recovers a known beta, so its count is
    # the last claim in the tree that should have been verified by proxy.
    ("PENUMBRA-OUTCOMES.md", "delta_star_calibration.json", "results",
     lambda rows: (lambda p: f"{sum(r['brackets_beta'] for r in p)} of {len(p)}")(
         [r for r in rows if r.get("stratum") == "never_event"])),
    ("SYNTHESIS.md", "delta_star_calibration.json", "results",
     lambda rows: (lambda p: f"{sum(r['brackets_beta'] for r in p)} of {len(p)}")(
         [r for r in rows if r.get("stratum") == "never_event"])),
    ("PENUMBRA-OUTCOMES.md", "delta_star_calibration.json", "invariance.density_range",
     lambda v: "density-invariant" if v == 0.0 else "DENSITY INVARIANCE BROKEN"),

    # -- V7's association, V9's ladder, V5's rung gain --
    # Each of these moved on 2026-08-04 and each is a verdict's headline number. Registered because the
    # ones that were registered survived four corpus rebuilds and the ones that were not had to be found
    # by hand.
    ("PENUMBRA-OUTCOMES.md", "p6.json", "spearman_rho", lambda v: f"{v:.3f}"),
    ("PENUMBRA-OUTCOMES.md", "p6.json", "p_value", lambda v: f"{v:.4f}"),
    # Rung 7's mean pooled AUC over four seeds, and rung 5's shortfall against the graph-free control.
    ("PENUMBRA-OUTCOMES.md", "p7_s4.json", "rows",
     lambda rows: f"{_rung_mean(rows, 7):.4f}".lstrip("0")),
    ("PENUMBRA-OUTCOMES.md", "p7_s4.json", "rows",
     lambda rows: f"{_rung_mean(rows, 5) - _rung_mean(rows, 4):+.4f}"),
    # V5's rung 3 - rung 2 gain on the within-coalition metric, the number §2(b) of SYNTHESIS turns on.
    ("PENUMBRA-OUTCOMES.md", "t1_ladder.json", "rows",
     lambda rows: f"{_rung_gain(rows, 2, 3, 'auc_within_coalition'):+.4f}"),

    # -- corpus-wide focal isolation (V11, V12) --
    ("PENUMBRA-OUTCOMES.md", "u1_isolation.json", "n_accessions", lambda v: f"{v:,}"),
    ("PENUMBRA-OUTCOMES.md", "u1_isolation.json",
     "first_entry_by_dating_stratum.exact.n_events", lambda v: f"{v:,}"),
    # The two ends of the anchor comparison. `trades` cannot record an IGO accession, so its
    # contrast at horizon 8 standing level with r*'s is the whole of V12's argument, and a
    # document that quotes it must quote the number the script produced.
    ("PENUMBRA-OUTCOMES.md", "u1_isolation.json",
     "matched_contrast.contrast.igo_comembership.0", lambda v: f"{v:.4f}"),
    ("PENUMBRA-OUTCOMES.md", "u1_isolation.json",
     "matched_contrast.contrast.trades.8", lambda v: f"{v:.4f}"),
    ("SYNTHESIS.md", "u1_isolation.json",
     "matched_contrast.contrast.igo_comembership.0", lambda v: f"{v:.4f}"),
    # V12's corpus-scale replication of V10: the step each instrument shows from horizon 0. These two
    # numbers were quoted for several hours after the script that produced them was restructured and
    # dropped the section -- the exact failure D-35 was written to prevent, committed in the prose
    # reporting D-35. Registered so it cannot recur silently.
    ("PENUMBRA-OUTCOMES.md", "u1_isolation.json", "matched_contrast.focal_step",
     lambda v: f"{v:.3f}"),
    ("PENUMBRA-OUTCOMES.md", "u1_isolation.json", "matched_contrast.pooled_step",
     lambda v: f"{v:.3f}"),
]

def _rung_mean(rows, rung: int) -> float:
    """Mean pooled AUC for one rung, averaged over seeds then over origin-horizon cells."""
    v = [r["auc"] for r in rows if r["rung"] == rung]
    return sum(v) / len(v)


def _rung_gain(rows, lo: int, hi: int, field: str = "auc") -> float:
    """Mean (hi - lo) on `field`, paired within origin-horizon-seed so the difference is per cell."""
    key = lambda r: (r["origin"], r["horizon"], r.get("seed", 0))
    a = {key(r): r[field] for r in rows if r["rung"] == lo}
    b = {key(r): r[field] for r in rows if r["rung"] == hi}
    both = sorted(set(a) & set(b))
    return sum(b[k] - a[k] for k in both) / len(both)


NUMERIC = re.compile(r"[-+]?\d[\d,]*\.?\d*")


def main() -> int:
    docs = {p.name: p.read_text(encoding="utf-8") for p in ROOT.glob("*.md")}
    # The documents set negative numbers with a typographic minus (U+2212) and `f"{v:+.4f}"` produces an
    # ASCII hyphen, so "-0.0009" and "−0.0009" are the same claim written two ways. Normalised for
    # comparison rather than fixed in each formatter, which would only push the problem to the next
    # negative number anyone registers.
    cmp_docs = {k: v.replace("−", "-") for k, v in docs.items()}
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
        text = cmp_docs.get(doc)
        if text is None:
            fails.append(f"{doc} not found")
            continue
        if want.replace("−", "-") not in text:
            fails.append(f"{doc} does not contain {want!r} from {src}:{path}")

    # Cross-file agreement: the same quantity asserted in two documents must match. The pattern must be
    # the **live** figure, not a retired one -- a pair on a retired number goes green when both documents
    # are stale together, which is how the 6,115 pair behaved until D-28 retired it.
    pairs = [("LEDGER.md", "PENUMBRA-OUTCOMES.md", r"\b565\b", "entity count")]
    for a, b, pat, label in pairs:
        ha = bool(re.search(pat, docs.get(a, "")))
        hb = bool(re.search(pat, docs.get(b, "")))
        if ha != hb:
            fails.append(f"{label}: present in {a if ha else b} but not {b if ha else a}")

    # Figures a later correction replaced must not come back outside the note that retires them.
    # A superseded number is more dangerous than a wrong one, because it was right once and so it
    # reads as verified. Each entry names the decision that retired it.
    #   6,290 -- D-08, a duplicated IGO_META that scored `dead` 0 -> 1 as an accession
    #   6,115 -- D-08's replacement, retired by V4's observer channel (+23) and D-28's ATOP fix
    #   573 / 10,556 -- D-31, phase rows counted as members admitted 8 bilateral treaties
    superseded = [(r"\b6,?290\b", "D-08"), (r"\b6,?115\b", "D-08"),
                  (r"\b573\b", "D-31"), (r"\b10,556\b", "D-31")]
    for name, text in docs.items():
        for pat, note in superseded:
            if re.search(pat, text) and note not in text:
                fails.append(f"{name} contains superseded figure {pat} outside its {note} note")

    # The corpus's live accession count, asserted where it is asserted. Checked against the pipeline
    # rather than across documents, because D-28 showed a cross-document pair can agree and both be
    # stale -- the pair on this quantity did exactly that until it was replaced by this check.
    summ = jload("ledger_summary.json")
    if summ is not None:
        live = dig(summ, "events.by_type.accession")
        if live is not None and f"{live:,}" not in docs.get("LEDGER.md", ""):
            fails.append(f"LEDGER.md does not contain the live accession count {live:,}")

    # **Every results file must have a script that writes it.** This is the check that produced D-32,
    # D-33 and D-34: three verdicts -- including the capstone -- rested on JSON no code path
    # regenerated, and regenerating each one found a further defect. A number nobody can recompute is
    # not a finding, however carefully it was written down.
    #
    # **No control characters in the prose.** A bash heredoc turns `\text` into TAB + "ext", `\approx`
    # into BEL + "pprox" and `\beta` into BS + "eta", so a LaTeX macro written that way silently becomes
    # a control byte and the sentence still looks fine in a terminal. It happened five times in one
    # working day, twice in the sentence stating a verdict, and once in the fixer written to repair it --
    # a single-quoted heredoc does it too. This is the check that ends it; the rule is to use the file
    # editor for any line containing a backslash.
    CTRL = {"\x07": r"\a", "\x08": r"\b", "\x09": r"\t", "\x0b": r"\v", "\x0c": r"\f"}
    for name, text in docs.items():
        for i, line in enumerate(text.splitlines(), 1):
            for ch, was in CTRL.items():
                if ch in line:
                    fails.append(f"{name}:{i} contains a raw control byte where {was!r} was meant "
                                 f"(heredoc ate a LaTeX escape)")

    # Attribution comes from the **artefact**, not from the script text. The first version of this check
    # tested whether a file's stem appeared anywhere under `scripts/`, and `p7_ctrl_w96` passed it
    # because a *comment* mentioned the filename -- a check satisfiable by writing prose. What settles
    # provenance is the file recording the command that wrote it (D-35), so that is what is required,
    # with two other ways to be accounted for: a name a script builds by interpolation from a declared
    # suffix, or an explicit supersession marker.
    INTERPOLATED = ("u1_real_", "u1_alliance_", "u2_real_", "t1_ladder", "t2_ladder")
    unattributed, reconstructed = [], []
    for f in sorted((ROOT / "results").glob("*.json")):
        stem = f.stem
        if any(stem.startswith(pre) for pre in INTERPOLATED):
            continue
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            obj = None
        d = obj if isinstance(obj, dict) else {}
        if d.get("SUPERSEDED") is True:
            continue
        if d.get("invocation"):
            if d.get("invocation_reconstructed"):
                reconstructed.append(stem)
            continue
        unattributed.append(stem)
    if reconstructed:
        print(f"  note  {len(reconstructed)} file(s) whose invocation was reconstructed from their own "
              f"fields rather than logged: {', '.join(reconstructed)}")
    if unattributed:
        print(f"  note  {len(unattributed)} results file(s) with no recorded invocation: "
              f"{', '.join(unattributed)}")

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

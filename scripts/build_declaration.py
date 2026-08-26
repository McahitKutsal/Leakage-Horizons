r"""Build the declaration artefact, and say exactly which parts of it a reader can check.

Section 5.1 rests the prospective test of Section 6.6 on a declaration written before any statistic, and
Section 9 says a claim is only worth what its artefact supports. Applying that to the declaration itself
is what this script is for, and doing so found that the two halves of the declaration are not equally
supported:

* **Corpus A's declaration is a timestamped pre-registration.** `penumbra-manifesto.md` was committed
  before any data was materialised and amended twice, and the three commits carry the dates. The target
  relation, the anchor set, the level ladder, the comparison strata, the resampling unit and the lead
  times are all in it, and a reader with the repository can read the file at the commit that froze it.
* **Corpus B's channel declaration is not.** The ten STRING channels were assigned to target,
  contaminated and anchor in the docstring of `scripts/run_second_domain.py`, and that file was not
  committed before it was run. The pre-registration does not name the channels at all. So the ordering
  the prospective test depends on is our account of when two parts of one file were written, and the
  repository cannot corroborate it.

Depositing an artefact now cannot fix the second case: a timestamp obtained after the statistic is not
evidence about the order. What the deposit can do is fix the text so it cannot drift, and record the
distinction plainly, which is what the manifest below does. The manuscript states the same distinction
where the test is reported rather than only in the threats section.

Writes `declaration/` with the declared text, a commit ledger, and a SHA-256 manifest, so that the
artefact a reader downloads can be checked byte for byte against the one the numbers were computed
against.

    python scripts/build_declaration.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402

OUT = ROOT / "declaration"
RESULTS = ROOT / "results"

# The pre-registration and its two amendments, by the commits that made them. Read from git rather
# than restated, so a rewritten history cannot leave this script agreeing with itself.
PREREG = "penumbra-manifesto.md"

# Where corpus B's channel assignment lives. Named here so its absence from the commit ledger is
# visible rather than something a reader has to notice.
CHANNEL_DECL = "scripts/run_second_domain.py"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


def commit_ledger(path: str) -> list:
    """Every commit that touched `path`, oldest first, with author date and subject."""
    raw = _git("log", "--reverse", "--format=%H|%ad|%s", "--date=iso", "--", path)
    out = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        h, date, subject = line.split("|", 2)
        out.append({"commit": h, "date": date, "subject": subject})
    return out


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=RESULTS / "declaration.json")
    ap.add_argument("--doi", default="",
                    help="the DOI the bundle was deposited under, e.g. 10.5281/zenodo.1234567. "
                         "Recorded in the manifest, and the manuscript takes it from there rather "
                         "than having it typed in a second place.")
    args = ap.parse_args()

    OUT.mkdir(exist_ok=True)
    prereg_log = commit_ledger(PREREG)
    channel_log = commit_ledger(CHANNEL_DECL)

    files = {}

    # 1. The pre-registration exactly as the freezing commit left it, not as it stands now.
    if prereg_log:
        frozen = prereg_log[-1]["commit"]
        blob = subprocess.run(["git", "show", f"{frozen}:{PREREG}"], cwd=ROOT,
                              capture_output=True, check=False).stdout
        p = OUT / "pre-registration.md"
        p.write_bytes(blob)
        files[p.name] = {"sha256": sha256(blob), "bytes": len(blob),
                         "source": f"{PREREG} at {frozen}",
                         "timestamped": True}          # by construction: read at its freezing commit

    # 2. Corpus B's channel assignment, as it stands, with its status stated in the file itself.
    decl = (ROOT / CHANNEL_DECL)
    if decl.exists():
        head = decl.read_text(encoding="utf-8")
        body = head.split('"""')[1] if '"""' in head else head
        text = ("# Corpus B channel declaration\n\n"
                "**Status: not timestamped.** This text assigns the ten STRING channels to target,\n"
                "contaminated and anchor. It was written in the analysis script's docstring before that\n"
                "script was run, which is our account of the order and is not corroborated by version\n"
                "control: the script was not committed before it was run, and the pre-registration in\n"
                "`pre-registration.md` does not name the channels. A reader is entitled to treat the\n"
                "prospective reading of Section 6.6 as our word about our own procedure. What is\n"
                "checkable is the content and the result: the assignment below is the one the released\n"
                "code uses, and the ranking it predicts is reproducible from that code.\n\n"
                "Reproduced verbatim from the docstring of `" + CHANNEL_DECL + "`:\n\n"
                "```\n" + body.strip() + "\n```\n")
        b = text.encode("utf-8")
        p = OUT / "corpus-b-channel-declaration.md"
        p.write_bytes(b)
        files[p.name] = {"sha256": sha256(b), "bytes": len(b),
                         "source": f"docstring of {CHANNEL_DECL}", "timestamped": False}

    # **A commit made now is not evidence about then, and this script has to keep saying so.** The
    # honest finding is that the corpus B declaration was not committed before it was run. If it is
    # committed later, a naive "has commits" test would flip to True and the manifest would look like
    # evidence. So the test is whether any commit predates the reference date below, which is when the
    # pre-registration was frozen and therefore the latest moment a declaration could still have
    # preceded the analysis. Anything committed after it, including today, fails.
    reference = prereg_log[-1]["date"] if prereg_log else None

    def predates_reference(log: list) -> bool:
        if not log or reference is None:
            return False
        return min(c["date"] for c in log) <= reference

    manifest = {
        "what_this_is": ("the declaration Section 5.1's protocol rests on, released so that the "
                         "ordering Section 6.6's prospective test depends on is checkable where it "
                         "can be and marked where it cannot"),
        "reference_date": reference,
        "why_a_reference_date": ("a commit made after the statistics were computed cannot establish "
                                 "that a declaration preceded them, so the test is not whether the "
                                 "file has commits but whether it has one at or before the moment the "
                                 "pre-registration was frozen"),
        "corpus_a": {
            "file": "pre-registration.md",
            "timestamped": predates_reference(prereg_log),
            "first_commit": prereg_log[0]["date"] if prereg_log else None,
            "commits": prereg_log,
            "declares": ["the target relation", "the anchor set", "the level ladder",
                         "the comparison strata", "the resampling unit", "the lead times",
                         "the predictions, including the two that were falsified"],
        },
        "corpus_b": {
            "file": "corpus-b-channel-declaration.md",
            "timestamped": predates_reference(channel_log),
            "first_commit": channel_log[0]["date"] if channel_log else None,
            "commits": channel_log,
            "declares": ["the target channel", "the two contaminated channels",
                         "the five anchor channels"],
            "limitation": ("the file carrying this declaration was not committed before it was run, "
                           "and the pre-registration does not name the channels, so version control "
                           "cannot corroborate that the reading preceded the statistic"),
        },
        "files": files,
        "head_commit": _git("rev-parse", "HEAD"),
        "deposit_identifier": args.doi.strip() or "TO BE COMPLETED AT DEPOSIT",
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("declaration bundle written to", OUT)
    for name, meta in files.items():
        print(f"  {name:38s} {meta['bytes']:>8,} bytes  sha256 {meta['sha256'][:16]}...  "
              f"timestamped={meta['timestamped']}")
    print(f"\n  corpus A: {len(prereg_log)} commits, "
          f"{prereg_log[0]['date'] if prereg_log else 'none'} to "
          f"{prereg_log[-1]['date'] if prereg_log else 'none'}")
    cb_ok = predates_reference(channel_log)
    print(f"  corpus B: {len(channel_log)} commits, earliest "
          f"{channel_log[0]['date'] if channel_log else 'none'}   "
          f"{'timestamped' if cb_ok else 'NOT TIMESTAMPED: no commit at or before ' + str(reference)}")
    if channel_log and not cb_ok:
        print("  a commit exists but postdates the analysis, which is not evidence about the order")

    write_result(args.json, manifest, indent=2)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

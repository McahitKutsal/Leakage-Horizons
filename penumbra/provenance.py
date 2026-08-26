"""Stamp every results artefact with the command that wrote it.

D-32, D-33 and D-34 all came from the same discovery: results files that no code path regenerated. Three
verdicts rested on them, one of them the capstone, and regenerating each found a further defect. The
general fix is not another audit -- it is that an artefact should carry its own provenance, so the
question "what produced this number?" is answered by the file rather than by memory.

`check_consistency.py` requires the `invocation` key, so a new ad-hoc artefact fails the check instead of
sitting quietly in `results/` until someone cites it.

Deliberately minimal. No timestamp, no host, no git hash: a timestamp changes on every rerun and turns a
byte-identical result into a diff, which is the opposite of what reproducibility wants. The corpus
version is what actually disambiguates two runs of the same command, so that is what is recorded
alongside.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SUMMARY = ROOT / "results" / "ledger_summary.json"


def corpus_fingerprint() -> dict | None:
    """Entity and event counts of the corpus currently on disk.

    Two runs of the same command on corpus v1 and v4 produce different numbers, and nothing in the
    command distinguishes them. These three integers do, and they are already computed.
    """
    try:
        d = json.loads(LEDGER_SUMMARY.read_text(encoding="utf-8"))
    except Exception:
        return None
    return {"entities": d["entities"]["total"], "events": d["events"]["total"],
            "accessions": d["events"]["by_type"].get("accession")}


def stamp(obj: dict) -> dict:
    """Return `obj` with provenance keys in front. Non-destructive if they are already set."""
    if not isinstance(obj, dict):
        raise TypeError("stamp() takes the result mapping; wrap a list before calling it")
    head = {"invocation": " ".join(sys.argv), "corpus": corpus_fingerprint()}
    return {**{k: v for k, v in head.items() if k not in obj}, **obj}


def write_result(path: Path, obj, indent: int = 2, **kwargs) -> Path:
    """Write a stamped JSON artefact, creating the directory.

    A list-valued result is wrapped as `{"records": [...]}` rather than left unstamped, because the one
    file in the tree that held a bare list -- `t2_focal.json` -- is also the one that carried a
    mislabelled key for a day without anywhere to record what wrote it (D-20, D-33).
    """
    path = Path(path)
    payload = stamp(obj if isinstance(obj, dict) else {"records": obj})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=indent, **kwargs), encoding="utf-8")
    return path

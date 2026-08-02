"""Check the vendored CLIQUEBAIT copy against the hashes it was pinned at.

Two distinct checks, reported separately because they mean different things:

* **vendored code** must match `pin.json` exactly. A mismatch means PENUMBRA's own copy has
  been edited, and every number computed with it is now of unknown provenance.
* **governing documents** live upstream and are allowed to change. A mismatch there is not a
  failure -- it means the protocol PENUMBRA inherited has been revised since it was pinned,
  and somebody has to decide whether the revision is binding here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / "CLIQUEBAIT"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    pin = json.loads((ROOT / "vendor" / "pin.json").read_text())
    code_bad, doc_moved, missing = [], [], []

    for rec in pin["files"]:
        rel, want = rec["path"], rec["sha256"]
        vendored = rel.startswith("cliquebait/")
        # the vendored copy sits at vendor/cliquebait/...; documents stay upstream
        p = (ROOT / "vendor" / rel) if vendored else (UPSTREAM / rel)
        if not p.exists():
            missing.append((rel, p))
            continue
        got = sha256(p)
        if got == want:
            continue
        (code_bad if vendored else doc_moved).append((rel, want, got))

    for rel, p in missing:
        print(f"MISSING   {rel}\n          expected at {p}")

    for rel, want, got in code_bad:
        print(f"DRIFTED   {rel}\n          pinned {want[:16]}  now {got[:16]}")

    for rel, want, got in doc_moved:
        print(f"UPSTREAM  {rel} has changed since it was pinned\n"
              f"          pinned {want[:16]}  now {got[:16]}")

    if not (code_bad or doc_moved or missing):
        print(f"ok: {len(pin['files'])} artefacts match the pin taken {pin['pinned_at']}")
        return 0

    # Only vendored-code drift and outright absence are failures. An upstream document that
    # has moved on is information, not an error -- but it must be acknowledged in DECISIONS.md
    # rather than silently carried.
    if code_bad or missing:
        print("\nFAIL: the vendored library is not what PENUMBRA's results were computed with.")
        return 1
    print("\nNot a failure. Record in DECISIONS.md whether the upstream revision binds here, "
          "then re-pin with scripts/repin.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

r"""Reproduce V11's defect quantification from the raw ATOP files, independent of LEDGER.

V11 was first quantified against the defective corpus and a corrected `penumbra/ledger.py` cannot emit
those figures again, which left a verdict resting on numbers nothing reproduces. This script computes
the defect's magnitude from `atop5_1a.csv` and `atop5_1m.csv` directly, so V11 stays checkable for as
long as the source files exist.

**Writing it found a second defect of the same family, and changed what V11 reports.** The originally
measured 221 of 481 spurious (45.9 %) could not be reconstructed, and the reason was not an error in
either count: `atop_entities` sized treaties by `groupby("atopid").size()`, a **row** count, so a
bilateral pact coded over two phases had four rows and passed a >= 3 members filter. 8 of 80 alliance
entities were bilateral treaties admitted that way. The 45.9 % was therefore produced by two overlapping
defects, and reinstating both to reproduce it would be reinstating a corpus nobody should have. V11 now
reports **149 of 373 (40.0 %)** on the corrected entity set, and the second defect is D-31.

It reimplements **both** accession rules side by side rather than importing either:

* `defective` -- one accession per membership row whose `yrent` postdates the treaty's `begyr`, which is
  what `atop_membership_events` did before D-28
* `corrected` -- one accession per (treaty, member) at its **first** `yrent` across phases, and only if
  that first entry postdates the treaty

Reimplementation is deliberate. Importing the fixed function to demonstrate what the broken one did is
circular, and importing a preserved copy of the broken one puts code in the library whose only purpose
is to be wrong.

    python scripts/quantify_atop_phase_defect.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.ledger import ATOP_DIR, MIN_MEMBERS, WINDOW_END, WINDOW_START  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402

REGIME = (1965, 2014)


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    """The raw files, restricted to **the corpus's own alliance entities**.

    Restricting by re-deriving the >= 3 members rule here would compare the defective accession rule
    against a different entity set than the corpus ever had, and the two filters do not agree: the
    entity rule also carries a window restriction, and it once counted phase rows instead of distinct
    members. Reading `entities.parquet` keeps the comparison on one population. That file is safe to
    read for this purpose because the entity set does not depend on the accession rule -- `atop_entities`
    reads `atop5_1a.csv` and never touches `yrent`.
    """
    a = pd.read_csv(ATOP_DIR / "atop5_1a.csv", low_memory=False, usecols=["atopid", "begyr"])
    m = pd.read_csv(ATOP_DIR / "atop5_1m.csv", low_memory=False)
    keep = [c for c in ("atopid", "member", "yrent", "yrexit", "phase") if c in m.columns]
    m = m[keep].copy()
    m["yrent_c"] = pd.to_numeric(m.yrent, errors="coerce").replace(0, np.nan)
    ent = pd.read_parquet(ROOT / "data" / "ledger" / "entities.parquet")
    ids = set(ent.loc[ent.entity_type == "alliance", "source_id"].astype(int))
    m = m[m.atopid.isin(ids)]
    return a.drop_duplicates("atopid").set_index("atopid"), m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "atop_phase_defect.json")
    args = ap.parse_args()

    agr, m = load()
    m["begyr"] = m.atopid.map(agr.begyr)
    in_window = m.yrent_c.between(WINDOW_START, WINDOW_END)

    # --- the two rules ---
    defective = m[in_window & (m.yrent_c > m.begyr)]
    pair = (m.groupby(["atopid", "member"], as_index=False)
            .agg(first_ent=("yrent_c", "min"), n_rows=("yrent_c", "size")))
    pair["begyr"] = pair.atopid.map(agr.begyr)
    corrected = pair[pair.first_ent.between(WINDOW_START, WINDOW_END)
                     & (pair.first_ent > pair.begyr)]

    # A defective event is spurious when the member's FIRST entry does not postdate the treaty: it was
    # there at the start and the later row is a phase continuation.
    first_of = pair.set_index(["atopid", "member"]).first_ent
    key = pd.MultiIndex.from_arrays([defective.atopid, defective.member])
    dfirst = first_of.reindex(key).to_numpy()
    spurious = dfirst <= defective.begyr.to_numpy()

    founders = int((pair.first_ent <= pair.begyr).sum())
    out = {
        "n_treaties": int(pair.atopid.nunique()),
        "n_pairs": int(len(pair)),
        "n_founders": founders,
        "n_later_joiners": int(len(pair) - founders),
        "defective_rule": {
            "n_events": int(len(defective)),
            "n_spurious": int(spurious.sum()),
            "share_spurious": round(float(spurious.mean()), 4),
            "n_genuine": int((~spurious).sum()),
        },
        "corrected_rule": {
            "n_events": int(len(corrected)),
            "n_in_regime": int(corrected.first_ent.between(*REGIME).sum()),
        },
        "phase_rows_per_pair": {int(k): int(v)
                                for k, v in pair.n_rows.value_counts().sort_index().items()},
    }

    # --- the presence figure the diagnostic reported, by how many rows the member has ---
    # Under the defective rule the member is on the record from its earliest row, so an event dated to
    # a later row shows presence at horizon 1 exactly when an earlier row exists. That is the whole
    # mechanism, and splitting by row count shows it as a step rather than a gradient.
    nrows = pair.set_index(["atopid", "member"]).n_rows.reindex(key).to_numpy()
    d = pd.DataFrame({"n_rows": nrows, "spurious": spurious,
                      "in_regime": defective.yrent_c.between(*REGIME).to_numpy()})
    by_rows = d.groupby("n_rows").agg(n_events=("spurious", "size"),
                                      presence_at_h1=("spurious", "mean"))
    out["presence_at_horizon_1_by_phase_rows"] = {
        int(k): {"n_events": int(r.n_events), "presence": round(float(r.presence_at_h1), 4)}
        for k, r in by_rows.iterrows()}

    print(f"corpus alliance entities covered: {out['n_treaties']} "
          f"(>= {MIN_MEMBERS} distinct members, in window)")
    print(f"(treaty, member) pairs: {out['n_pairs']}  "
          f"founders {out['n_founders']}  later joiners {out['n_later_joiners']}")
    print(f"\ndefective rule (one event per row with yrent > begyr): "
          f"{out['defective_rule']['n_events']} events")
    print(f"  spurious (member is a founder): {out['defective_rule']['n_spurious']} "
          f"= {out['defective_rule']['share_spurious']:.1%}")
    print(f"  genuine:                        {out['defective_rule']['n_genuine']}")
    print(f"\ncorrected rule (first entry per pair, postdating the treaty): "
          f"{out['corrected_rule']['n_events']} events, "
          f"{out['corrected_rule']['n_in_regime']} in {REGIME[0]}-{REGIME[1]}")
    print("\nhorizon-1 presence the diagnostic would report, by phase rows per member:")
    for k, v in out["presence_at_horizon_1_by_phase_rows"].items():
        print(f"  {k} row(s): n={v['n_events']:4d}  presence {v['presence']:.4f}")
    print(f"\noverall spurious share = {out['defective_rule']['share_spurious']:.4f}")
    print("  The corpus-wide diagnostic measured 0.458 before either fix, on an entity set that also")
    print("  admitted 8 bilateral treaties by phase-row count (D-31). Both defects are fixed, so that")
    print("  figure is not reproducible from any current code path and V11 reports this one instead.")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, out, indent=2)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

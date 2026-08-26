"""Build the observation graph and audit its coverage per relation per year.

Manifesto §2 makes the coverage audit a precondition rather than a companion: the audited
paper's headline architectural result lived entirely in a block that straddled a coverage break,
and D2 run on the unaudited graph pointed at the wrong relation. So the audit runs here, before
U1 and before any model.

    python scripts/build_graph.py --json results/graph_coverage.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from penumbra.graph import (IGO_COMEMBERSHIP, RELATION_SOURCES, WINDOW_END,  # noqa: E402
                           WINDOW_START, build_igo_comembership, coverage_audit,
                           load_relations)

OUT = ROOT / "data" / "graph"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "graph_coverage.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rels = load_relations()
    print("loaded from CLIQUEBAIT:")
    for name, d in rels.items():
        print(f"  {name:16} {len(d):>8} edges  {int(d.year.min())}-{int(d.year.max())}")

    print(f"\nbuilding {IGO_COMEMBERSHIP} from LEDGER membership ...")
    rels[IGO_COMEMBERSHIP] = build_igo_comembership()
    d = rels[IGO_COMEMBERSHIP]
    print(f"  {IGO_COMEMBERSHIP:16} {len(d):>8} edges  {int(d.year.min())}-{int(d.year.max())}"
          f"  weight 1-{int(d.weight.max())}")

    per_year, regimes = coverage_audit(rels)

    print(f"\nregimes over {WINDOW_START}-{WINDOW_END} "
          f"(a maximal run with the same set of non-empty relations):")
    for r in regimes.itertuples():
        print(f"  {r.start}-{r.end}  {r.n_years:>2}yr  {r.n_relations} relations: {r.relations}")

    # The gaps CLIQUEBAIT declared should reappear here. If they do not, something was silently
    # filled in, which is the failure PROTOCOL §1 is written against.
    print("\nyears where a relation is absent:")
    all_years = set(range(WINDOW_START, WINDOW_END + 1))
    for name in rels:
        have = set(per_year.loc[(per_year.relation == name) & (per_year.n_edges > 0), "year"])
        gap = sorted(all_years - have)
        print(f"  {name:16} {gap if gap else 'none'}")

    summary = {
        "window": [WINDOW_START, WINDOW_END],
        "relations": {
            name: {
                "n_edges": int(len(d)),
                "years": [int(d.year.min()), int(d.year.max())],
                "source": (RELATION_SOURCES[name][1] if name in RELATION_SOURCES
                           else "built from LEDGER membership, COW IGO v3 full members only"),
                "missing_years": sorted(all_years - set(
                    per_year.loc[(per_year.relation == name) & (per_year.n_edges > 0), "year"])),
            } for name, d in rels.items()
        },
        "regimes": regimes.to_dict("records"),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, summary, indent=2, default=str)
    print(f"\nwritten to {args.json}")

    if args.dry_run:
        print("dry run, edges not written")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, d in rels.items():
        p = OUT / f"edges_{name}.parquet"
        d.to_parquet(p, index=False)
        print(f"  wrote {p.name:34} {len(d):>8} rows")
    per_year.to_parquet(OUT / "coverage_per_year.parquet", index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())

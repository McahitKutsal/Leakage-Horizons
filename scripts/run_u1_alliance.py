"""U1 with $r^\\star$ = alliance edges, on alliance entities. The manifesto's original claim.

Everything so far tested $r^\\star$ = IGO co-membership, because §11 makes $r^\\star$ entity-type
dependent and LEDGER is organisation-majority. That left the **original** claim untested: the
manifesto's §3 table names alliance edges as the suspected $r^\\star$, and CLIQUEBAIT *measured* them
leaking -- $\\omega = 0.718$, a clique lift of 590x, $\\phi$-alone AUC 0.806. If a penumbra exists
anywhere in this corpus it should be here.

Two reasons to expect this test to say something where the co-membership one could not:

* **the group sizes are in range.** V3 showed the exact-clique contrast is 0.20-0.25 below twenty
  members and identically **zero** above eighty. Alliance entities have a median membership of
  **4** against the organisation majority's 51, so the statistic has power here and had none there.
* **the relation is not saturated.** `allies` has mean density 0.15 against co-membership's 0.995, so
  cliqueness is discriminative rather than universal.

One caveat that cuts both ways and is stated before the result. ATOP's codebook is unreachable
(PROVENANCE §4), so whether `allies` dates a pact from signature, ratification or entry into force is
**unverified**. If a penumbra appears, we cannot say which of those produced it. If none appears, we
cannot rule out that ATOP dates from entry into force -- in which case there is nothing to
back-date and the null is a property of the source rather than of the world.

    python scripts/run_u1_alliance.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.umbra import NEVER_EVENT, NOT_AT_HORIZON, HorizonAudit, delta_star  # noqa: E402
from scripts.run_u2 import REGIMES, load  # noqa: E402

RSTAR = "allies"
# The declared anchor set of PROVENANCE §5, unchanged. `igo_comembership` is NOT added even though
# for an alliance label it is not label-derived: it is saturated at density 0.995, so it would set
# the band by its own pathology rather than by anything about leakage.
ANCHORS = ["trades", "conflicts_with", "votes_with"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", choices=sorted(REGIMES), default="primary")
    ap.add_argument("--horizons", type=int, nargs="+", default=list(range(1, 11)))
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    regime = REGIMES[args.regime]
    args.json = args.json or ROOT / "results" / f"u1_alliance_{args.regime}.json"

    edges, mem, ev, _fam = load(regime)
    ent = pd.read_parquet(ROOT / "data" / "ledger" / "entities.parquet")
    alliance = set(ent.loc[ent.entity_type == "alliance", "entity_id"])
    mem_a = mem[mem.entity_id.isin(alliance)]
    ev_a = ev[ev.entity_id.isin(alliance)]

    n_acc = int(((ev_a.event_type == "accession") & ev_a.ccode.notna()).sum())
    sizes = mem_a[mem_a.status == 1].groupby(["entity_id", "year"]).size()
    print(f"regime {args.regime} {regime}")
    print(f"  alliance entities {mem_a.entity_id.nunique()}  alliance-years {len(sizes)}  "
          f"accessions {n_acc}")
    print(f"  membership size: median {int(sizes.median())}  mean {sizes.mean():.1f}  "
          f"max {int(sizes.max())}   <- V3's clique statistic has power below ~20")
    print(f"  r* {RSTAR}   anchors {ANCHORS}")

    audit = HorizonAudit(edges, mem_a, ev_a)
    out, verdicts = [], []
    for stratum in (NEVER_EVENT, NOT_AT_HORIZON):
        t0 = time.time()
        curve = audit.u1_curve(horizons=args.horizons,
                               levels={r: (1,) for r in audit.relations},
                               negatives=stratum)
        if curve.empty:
            print(f"\n{stratum}: no usable panel")
            continue
        out.append(curve.assign(negative_stratum=stratum))
        print(f"\n=== {stratum}  ({time.time() - t0:.0f}s) ===")
        print(curve.pivot_table(index="horizon", columns="relation",
                               values="clique_contrast").round(4).to_string())
        print("n_pos per horizon:",
              curve.groupby("horizon").n_pos.first().to_dict())
        ds = delta_star(curve, RSTAR, ANCHORS, level=1)
        lo, hi = ds["delta_star_lo"], ds["delta_star_hi"]
        print(f"  delta*_lo = {lo}   delta*_hi = {hi}")
        det = pd.DataFrame(ds["detail"])
        print(det[["horizon", "clique_contrast", "band_clique_contrast",
                   "auc_phi_alone", "band_auc", "rstar_is_top"]].round(4).to_string(index=False))
        verdicts.append({"stratum": stratum, "delta_star_lo": lo, "delta_star_hi": hi,
                         "detail": ds["detail"]})

    if not out:
        print("nothing computed")
        return 1
    curves = pd.concat(out, ignore_index=True)

    prim = [v for v in verdicts if v["stratum"] == NEVER_EVENT]
    print("\n--- P1 and P2 read on the manifesto's original r* ---")
    for v in prim:
        lo, hi = v["delta_star_lo"], v["delta_star_hi"]
        if lo is None:
            print("  P1: delta*_lo never reached -> instrumental non-identification, not support")
        else:
            print(f"  P1 requires delta*_lo >= 2 : {'HOLDS' if lo >= 2 else 'FALSIFIED'}  (lo={lo})")
        if hi is None:
            print("  P2 upper clause: delta*_hi unreachable -> non-identification per C18")
        else:
            print(f"  P2 requires delta*_hi <= 6 : {'HOLDS' if hi <= 6 else 'FALSIFIED'}  (hi={hi})")
    print("\nNOTE: ATOP's dating convention is unverified (PROVENANCE §4). Whatever this shows, it "
          "cannot attribute the result to signature, ratification or entry into force.")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps({
        "regime_name": args.regime, "regime": list(regime), "rstar": RSTAR, "anchors": ANCHORS,
        "n_alliance_entities": int(mem_a.entity_id.nunique()), "n_accessions": n_acc,
        "median_membership": int(sizes.median()),
        "atop_dating_unverified": True,
        "verdicts": verdicts, "curves": curves.to_dict("records"),
    }, indent=2, default=str))
    curves.to_parquet(ROOT / "results" / f"u1_alliance_{args.regime}.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

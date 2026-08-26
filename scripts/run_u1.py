"""U1 on real LEDGER: the leakage-horizon curve, and $\\Delta^\\star$ where it can be read.

Everything this needs was declared before it ran, which is the only order that makes either
declaration or result mean anything:

* **the anchors**, in `PROVENANCE.md` §5 — `trades`, `conflicts_with` and `votes_with`, each of
  which records something (a reporting-year flow, a dispute onset, a roll-call) that cannot
  anticipate an accession. `allies` is excluded because the ATOP codebook is unreachable and its
  dating convention is unverified; `igo_comembership` is $r^\\star$, not an anchor;
* **the band rule**, calibrated on synthetics where $\\beta$ is known and
  $\\Delta^\\star_{\\text{lo}}$ recovers $\\beta+1$ in 6 of 6 settings (C18), with the width coming
  from sampling noise rather than from a chosen tolerance (C17);
* **the primary level $k = 25$**, the median shared-organisation count, fixed in D-13 before this
  curve existed and read at no other level.

    python scripts/run_u1.py --regime primary
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
from penumbra.provenance import write_result  # noqa: E402
from scripts.run_u2 import LEVELS, REGIMES, load  # noqa: E402

RSTAR = "igo_comembership"
# PROVENANCE.md §5. Declared from the coding rules, not from any statistic, because no statistic
# can do it (§5.4).
ANCHORS = ["trades", "conflicts_with", "votes_with"]
PRIMARY_LEVEL = 25          # D-13, fixed before this ran


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", choices=sorted(REGIMES), default="primary")
    ap.add_argument("--horizons", type=int, nargs="+", default=list(range(1, 11)))
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    regime = REGIMES[args.regime]
    args.json = args.json or ROOT / "results" / f"u1_real_{args.regime}.json"
    edges, mem, ev, _fam = load(regime)
    print(f"regime {args.regime}: {regime[0]}-{regime[1]}")
    print(f"  r*      {RSTAR}   levels {LEVELS[RSTAR]}   primary k={PRIMARY_LEVEL}")
    print(f"  anchors {ANCHORS}  (allies excluded: dating unverified, PROVENANCE §4)")

    audit = HorizonAudit(edges, mem, ev)
    out, verdicts = [], []
    for stratum in (NEVER_EVENT, NOT_AT_HORIZON):
        t0 = time.time()
        curve = audit.u1_curve(horizons=args.horizons, levels=LEVELS, negatives=stratum)
        if curve.empty:
            print(f"\n{stratum}: no usable panel")
            continue
        curve = curve.assign(negative_stratum=stratum)
        out.append(curve)
        print(f"\n=== {stratum}  ({time.time() - t0:.0f}s) ===")
        print("clique_contrast by relation x horizon (r* at each level, anchors at level 1):")
        tab = curve.assign(rel=curve.relation + curve.level.map(
            lambda k: f"@k{k}" if k > 1 else "")).pivot_table(
            index="horizon", columns="rel", values="clique_contrast")
        print(tab.round(4).to_string())

        for k in LEVELS[RSTAR]:
            ds = delta_star(curve, RSTAR, ANCHORS, level=k)
            mark = "  <- PRIMARY (D-13)" if k == PRIMARY_LEVEL else ""
            print(f"  k={k:>3}  delta*_lo={ds['delta_star_lo']}  "
                  f"delta*_hi={ds['delta_star_hi']}{mark}")
            verdicts.append({"stratum": stratum, "level": k,
                             "delta_star_lo": ds["delta_star_lo"],
                             "delta_star_hi": ds["delta_star_hi"],
                             "primary": k == PRIMARY_LEVEL, "detail": ds["detail"]})

    if not out:
        print("nothing computed")
        return 1
    curves = pd.concat(out, ignore_index=True)

    prim = [v for v in verdicts if v["primary"] and v["stratum"] == NEVER_EVENT]
    print("\n--- P1 and P2, read where D-13 says to read them ---")
    for v in prim:
        lo, hi = v["delta_star_lo"], v["delta_star_hi"]
        print(f"  delta*_lo = {lo}   delta*_hi = {hi}   (k={v['level']}, {v['stratum']})")
        if lo is None:
            print("    P1: delta*_lo not reached inside the horizon range -> the relation never "
                  "enters the band; report as instrumental non-identification, not as support")
        else:
            print(f"    P1 requires delta*_lo >= 2 : {'HOLDS' if lo >= 2 else 'FALSIFIED'}")
        if hi is None:
            print("    P2 upper clause: delta*_hi unreachable -> instrumental "
                  "non-identification per C18, NOT falsification")
        else:
            print(f"    P2 requires delta*_hi <= 6 : {'HOLDS' if hi <= 6 else 'FALSIFIED'}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, {
        "regime_name": args.regime, "regime": list(regime),
        "rstar": RSTAR, "anchors": ANCHORS, "primary_level": PRIMARY_LEVEL,
        "levels": {k: list(v) for k, v in LEVELS.items()},
        "verdicts": verdicts,
        "curves": curves.to_dict("records"),
    }, indent=2, default=str)
    curves.to_parquet(ROOT / "results" / f"u1_real_{args.regime}.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

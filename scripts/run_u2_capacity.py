r"""The probe capacity sweep, on the matched panel. Mechanism (e)'s numbers.

Mechanism (e) of the manuscript is that a lead-time-resolved probe with free capacity can manufacture a
leakage horizon: the positive count necessarily falls with lead time, so a high-capacity probe overfits
more at long lead times and produces a decaying curve whatever the leakage is.

The numbers the manuscript quoted for it, a decay of 0.058 at 30 trees against 0.143 at 300 with a
linear probe at 0.041, came from V1d, whose header records "mechanism stands, **numbers void**". They
were measured on the panel V0 retracted, where negatives were drawn across coalition-years rather than
within them, so positive groups averaged 66 members against the negatives' 18 and the statistic partly
measured group size. The stored artefact for that run carries neither an invocation nor a corpus
fingerprint, which is how it was identified as predating the correction (D-45).

The mechanism does not depend on the defect, because the capacity comparison is internal to one panel:
the same negatives are used at every capacity, so a difference across capacities is a property of the
probe. The **numbers** do depend on it, and a paper should not quote figures its own reconciliation marks
as void. This recomputes them with matched negatives.

The replication regime is used because that is where the artefact appears: 1948 to 1963, the earlier
coverage regime, where the positive count is small enough for capacity to bite.

    python scripts/run_u2_capacity.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from penumbra.umbra import HorizonAudit  # noqa: E402
from scripts.run_u2 import LEVELS, REGIMES, load  # noqa: E402

# The four capacities V1d swept, so the comparison is like for like.
CAPACITIES = [(30, 2), (100, 2), (300, 3)]
HORIZONS = [1, 10]          # the decay is the difference between the ends
SEED = 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", choices=sorted(REGIMES), default="replication")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    args.json = args.json or ROOT / "results" / f"u2_capacity_{args.regime}.json"
    regime = REGIMES[args.regime]

    edges, mem, ev, fam = load(regime)
    audit = HorizonAudit(edges, mem, ev)
    print(f"regime {args.regime} {regime}: {len(ev)} events, {len(edges)} edge-years")

    rows = []
    for n_est, depth in CAPACITIES:
        df = audit.u2_shortcut(horizons=HORIZONS, levels=LEVELS, negatives="never_event",
                               groups_for_split=fam, seed=SEED, also_linear=True,
                               n_estimators=n_est, max_depth=depth)
        lo = df[df.horizon == HORIZONS[0]].iloc[0]
        hi = df[df.horizon == HORIZONS[-1]].iloc[0]
        rows.append({
            "n_estimators": n_est, "max_depth": depth,
            "n_pos_at_first": int(lo.n_pos), "n_pos_at_last": int(hi.n_pos),
            "auc_first": round(float(lo.auc_shortcut), 4),
            "auc_last": round(float(hi.auc_shortcut), 4),
            "decay": round(float(lo.auc_shortcut - hi.auc_shortcut), 4),
            "auc_first_linear": round(float(lo.auc_shortcut_linear), 4),
            "auc_last_linear": round(float(hi.auc_shortcut_linear), 4),
            "decay_linear": round(float(lo.auc_shortcut_linear - hi.auc_shortcut_linear), 4),
        })
        print(f"  {n_est:3d} trees / depth {depth}: "
              f"AUC {rows[-1]['auc_first']:.4f} -> {rows[-1]['auc_last']:.4f}  "
              f"decay {rows[-1]['decay']:+.4f}   linear decay {rows[-1]['decay_linear']:+.4f}")

    d = pd.DataFrame(rows)
    ratio = (d.decay.max() / d.decay.min()) if d.decay.min() > 0 else None
    print(f"\ndecay at lowest capacity {d.decay.min():.4f}, at highest {d.decay.max():.4f}"
          + (f", ratio {ratio:.2f}" if ratio else ""))
    print(f"linear probe decay, capacity independent by construction: "
          f"{d.decay_linear.min():.4f} to {d.decay_linear.max():.4f}")

    write_result(args.json, {
        "regime": list(regime), "regime_name": args.regime,
        "horizons": HORIZONS, "negatives": "never_event", "matched_negatives": True,
        "capacities": rows,
        "decay_lowest_capacity": float(d.decay.min()),
        "decay_highest_capacity": float(d.decay.max()),
        "decay_ratio": float(ratio) if ratio else None,
        "decay_linear_mean": round(float(d.decay_linear.mean()), 4),
    }, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

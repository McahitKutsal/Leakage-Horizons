"""U2 on real LEDGER: how much of the forecasting task falls to densities alone, per horizon.

§5.2 calls this "the single most informative plot the paper can produce, and it should appear
early". It is also a **baseline rather than an ablation** (§7 rung 3): whatever the hazard models
later achieve is measured against this curve, not against a weak strawman.

Everything the inherited protocol makes non-optional is switched on and named in the output:

* the probe is gradient-boosted, with the linear one reported beside it, because CLIQUEBAIT
  measured 0.915 against 0.979 on identical features and the leak is a clique-indicator effect;
* it is cross-fitted, because scoring rows with a probe fitted on them hides the collapse;
* folds are grouped on the membership-equivalent family, so a coalition cannot be split across
  folds (LEDGER.md §1.3);
* the run is confined to one coverage regime, since PROTOCOL §3 forbids pooling a ranking metric
  across a coverage break, and 1965–2014 is both the longest intact regime and the exactly-dated
  event stratum (LEDGER.md §6.1);
* both negative strata are reported, because at a horizon they are different estimands (§5.1).

    python scripts/run_u2.py --json results/u2_real.json
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

from penumbra.umbra import NEVER_EVENT, NOT_AT_HORIZON, HorizonAudit  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402

LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"

# The analysis regime, declared in LEDGER.md §6.1 rather than chosen here: 1965-2014 is both the
# longest run of intact relation coverage and the window in which event dates are not
# block-resolved. 1948-1963 is the out-of-regime replication -- five relations, but pre-1965
# membership dating -- and PROTOCOL §3 forbids pooling the two, so they are separate runs by
# construction rather than by discipline.
REGIME = (1965, 2014)
REGIMES = {"primary": (1965, 2014), "replication": (1948, 1963)}

# Co-membership is saturated as a binary relation, so it enters on the declared level ladder
# (LEDGER.md §6.2). The other four are presence relations and enter at level 1. Quantiles of the
# co-membership weight over the regime are 17 / 25 / 33 / 42, so the ladder spans them.
LEVELS = {
    "igo_comembership": (1, 17, 25, 33, 42),
    "allies": (1,), "trades": (1,), "votes_with": (1,), "conflicts_with": (1,),
}


def load(regime=REGIME):
    """Edges for the **declared** relations, membership, events and families.

    This globbed `edges_*.parquet` and so silently absorbed `edges_pta_signature.parquet` and
    `edges_pta_force.parquet` the moment V10's DESTA validation wrote them into the same directory.
    The consequence here is worse than the crash the same glob caused in `neural.py` (D-38): U2's probe
    gained **four** features -- `phi_pta_force_k1`, `clique_pta_force_k1`, `phi_pta_signature_k1`,
    `clique_pta_signature_k1` -- so a re-run reports 24 features where V1 and V2 were measured on 20, and
    it produces plausible numbers rather than an error. `pta_signature` is *deliberately* back-dated: it
    exists to carry a known penumbra, which makes it the single worst feature to add to a shortcut probe
    by accident (D-39).

    `LEVELS` is the declaration -- the relations U2 computes $\\phi_r(S; k)$ for -- so it is also the
    right source for which edge files to read.
    """
    missing = [r for r in LEVELS if not (GRAPH / f"edges_{r}.parquet").exists()]
    if missing:
        raise FileNotFoundError(f"declared relations with no edge file: {missing}")
    edges = pd.concat(
        [pd.read_parquet(GRAPH / f"edges_{r}.parquet").assign(relation=r) for r in LEVELS],
        ignore_index=True)
    edges = edges[edges.year.between(*regime)]
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    mem = mem[mem.year.between(*regime)]
    ev = pd.read_parquet(LEDGER / "events.parquet")
    ev = ev[ev.t_R.between(*regime)]
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    return edges, mem, ev, dict(zip(ent.entity_id, ent.family_id))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizons", type=int, nargs="+", default=list(range(0, 11)))
    ap.add_argument("--max-neg-per-pos", type=int, default=4)
    ap.add_argument("--regime", choices=sorted(REGIMES), default="primary")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    regime = REGIMES[args.regime]
    args.json = args.json or ROOT / "results" / f"u2_real_{args.regime}.json"
    edges, mem, ev, fam = load(regime)
    print(f"regime {args.regime}: {regime[0]}-{regime[1]}")
    print(f"  edges      {len(edges):>9}  relations {sorted(edges.relation.unique())}")
    print(f"  membership {len(mem):>9}")
    print(f"  accessions {int((ev.event_type == 'accession').sum()):>9}")
    print(f"  families   {len(set(fam.values())):>9}")

    audit = HorizonAudit(edges, mem, ev)
    out = []
    for stratum in (NEVER_EVENT, NOT_AT_HORIZON):
        t0 = time.time()
        curve = audit.u2_shortcut(horizons=args.horizons, levels=LEVELS, negatives=stratum,
                                  max_neg_per_pos=args.max_neg_per_pos,
                                  groups_for_split=fam)
        if curve.empty:
            print(f"\n{stratum}: no usable panel")
            continue
        curve = curve.assign(negative_stratum=stratum)
        out.append(curve)
        print(f"\n=== {stratum}  ({time.time() - t0:.0f}s) ===")
        cols = ["horizon", "n_pos", "n_neg", "n_clusters",
                "auc_shortcut", "auc_shortcut_linear", "nonlinear_gain"]
        print(curve[cols].to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    if not out:
        print("nothing computed")
        return 1
    all_curves = pd.concat(out, ignore_index=True)

    prim = all_curves[all_curves.negative_stratum == NEVER_EVENT].sort_values("horizon")
    print("\n--- reading the primary curve ---")
    if len(prim) >= 2:
        d0, dmax = prim.iloc[0], prim.iloc[-1]
        print(f"  AUC_shortcut at horizon {int(d0.horizon)}: {d0.auc_shortcut:.4f}")
        print(f"  AUC_shortcut at horizon {int(dmax.horizon)}: {dmax.auc_shortcut:.4f}")
        print(f"  decay across the range: {d0.auc_shortcut - dmax.auc_shortcut:+.4f}")
        mono = bool((prim.auc_shortcut.diff().dropna() <= 1e-9).all())
        print(f"  monotonically decreasing: {mono}   <- P2 predicts this")
        print(f"  mean non-linear gain over the linear probe: "
              f"{prim.nonlinear_gain.mean():+.4f}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, {
        # D-35: the invocation belongs in the artefact, since a `--json` override otherwise leaves the
        # file unattributable to the flags that produced it.
        "invocation": " ".join(sys.argv),
        "regime_name": args.regime, "regime": list(regime), "levels": {k: list(v) for k, v in LEVELS.items()},
        "max_neg_per_pos": args.max_neg_per_pos,
        "probe": "gradient boosting, 300 trees, depth 3, cross-fitted with GroupKFold on family",
        "curves": all_curves.drop(columns=["features"]).to_dict("records"),
        "features": all_curves.features.iloc[0].split(","),
    }, indent=2, default=str)
    all_curves.to_parquet(ROOT / "results" / f"u2_real_{args.regime}.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

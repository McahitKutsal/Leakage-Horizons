"""Does $\\Delta^\\star$ recover $\\beta$? The one question only synthetics can answer.

On real data $\\beta$ is the unknown. Here it is set, so the estimator can be graded rather than
merely run -- which is why §11 says the programme is a methods paper with this component and an IR
paper without it.

The target is stated before the run and is not negotiable afterwards: for a corpus generated at
back-dating horizon $\\beta$, $\\Delta^\\star$ should bracket $\\beta$. Specifically
$\\Delta^\\star_{\\text{lo}} \\leq \\beta \\leq \\Delta^\\star_{\\text{hi}}$ where both bounds exist,
since `lo` declares the penumbra closed early and `hi` late. A bound that lands on the wrong side
of $\\beta$ is a broken instrument, not an interesting finding.

    python scripts/calibrate_delta_star.py --json results/delta_star_calibration.json
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.synthetic import SyntheticConfig, generate, verify_invariance  # noqa: E402
from penumbra.umbra import NEVER_EVENT, NOT_AT_HORIZON, HorizonAudit, delta_star  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402

RSTAR = "r_star"
# Declared not to leak, by construction. On real data this list has to come from reading the
# coding rules (§5.4); here the generator guarantees it, which is the point of having synthetics.
# `r_current` is the primary anchor: same construction as r*, same completeness, beta = 0. The
# latent and noise relations are kept in the band but they cannot set it alone -- with no group
# mechanism their clique rate is exactly zero, which is what made the first calibration overshoot.
ANCHORS = ["r_current", "r_latent_1", "r_latent_2", "r_noise"]


def main() -> int:
    ap = argparse.ArgumentParser()
    # 0 through 5 inclusive. The default omitted 4, so the script produced "5 of 5" while C18 and
    # SYNTHESIS both quote "6 of 6" -- the documented figure came from a hand-passed flag, which is
    # D-35's lesson in the one place it does the most damage: after D-34 this calibration is the only
    # evidence the estimator recovers a known beta.
    ap.add_argument("--betas", type=int, nargs="+", default=[0, 1, 2, 3, 4, 5])
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--max-horizon", type=int, default=8)
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "delta_star_calibration.json")
    args = ap.parse_args()

    print("invariance check first -- without it nothing below means anything")
    inv = verify_invariance([0.0, 0.5, 1.0], args.betas, SyntheticConfig())
    dens_range = float(inv.density_rstar.max() - inv.density_rstar.min())
    comp_err = float((inv.completeness - inv.alpha).abs().max())
    print(f"  r* density range across alpha x beta : {dens_range:.8f}")
    print(f"  max |completeness - alpha|           : {comp_err:.5f}")
    print(f"  edge budget ever exceeded            : {bool(inv.budget_exceeded.any())}")
    if dens_range > 1e-6 or comp_err > 0.01 or bool(inv.budget_exceeded.any()):
        print("\nFAIL: the generator does not hold its invariances, so a horizon curve would "
              "move with beta for reasons unrelated to leakage. Nothing else is reported.")
        return 1

    horizons = range(0, args.max_horizon + 1)
    results, curves = [], []
    for beta in args.betas:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            edges, events, membership, _groups, meta = generate(args.alpha, beta,
                                                               SyntheticConfig())
        audit = HorizonAudit(edges, membership, events)

        for stratum in (NEVER_EVENT, NOT_AT_HORIZON):
            curve = audit.u1_curve(horizons=horizons, levels=(1,), negatives=stratum)
            if curve.empty:
                print(f"  beta={beta} {stratum}: no usable panel")
                continue
            ds = delta_star(curve, RSTAR, ANCHORS, level=1)
            curve = curve.assign(beta=beta)
            curves.append(curve)
            lo, hi = ds["delta_star_lo"], ds["delta_star_hi"]
            tgt = beta + 1
            brackets = (lo is not None and lo <= tgt and (hi is None or tgt <= hi))
            results.append({"beta": beta, "target": tgt, "stratum": stratum, "alpha": args.alpha,
                            "delta_star_lo": lo, "delta_star_hi": hi,
                            "brackets_beta": bool(brackets),
                            "n_accessions": meta["n_accessions"], "detail": ds["detail"]})
            print(f"  beta={beta}  {stratum:<20} lo={lo}  hi={hi}  brackets beta: {brackets}")

    res = pd.DataFrame([{k: v for k, v in r.items() if k != "detail"} for r in results])
    print("\ncalibration, primary stratum (never_event):")
    prim = res[res.stratum == NEVER_EVENT]
    print(prim.to_string(index=False))
    hit = int(prim.brackets_beta.sum())
    print(f"\nbeta bracketed in {hit} of {len(prim)} settings")

    if len(prim) and hit < len(prim):
        print("The estimator does not bracket the known back-dating horizon everywhere. That is a "
              "finding about the instrument and it goes in PENUMBRA-OUTCOMES.md before any "
              "Delta* on real data is quoted.")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, {
        "target": "delta_star_lo <= beta + 1 <= delta_star_hi",
        "alpha": args.alpha, "betas": args.betas, "horizons": list(horizons),
        "rstar": RSTAR, "anchors": ANCHORS,
        "invariance": {"density_range": dens_range, "completeness_error": comp_err},
        "results": results,
    }, indent=2, default=str)
    if curves:
        pd.concat(curves, ignore_index=True).to_parquet(
            ROOT / "results" / "u1_curves_synthetic.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

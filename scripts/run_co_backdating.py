r"""Is the focal group's own record the only place administrative back-dating can live?

Section 3.3 says it is: "a curator's decision to date a membership from signature rather than operation
affects that group's record and nothing else." An external read of the manuscript identified that
sentence as the single most fragile claim in it, and the objection is exact. It is true of the focal
*event* and it need not be true of the target *relation*. If the acceding entity and a sitting member
are co-members of some other group Y, the dyad they carry in $r^\star$ is Y's; if Y's record is
back-dated that dyad is an administrative trace of nothing focal isolation reads, because focal
isolation reads one record. For the trace to be *correlated with the label*, the entity's entry into Y
has to fall near its entry into the focal group, which is what accession waves are.

Table 4's first column reports focal isolation at 0.00 mean error and slope 1.00 in twelve cells, which
presents it as an unbiased instrument. If the objection holds, that column is a statement about one
generator rather than about the operation, and focal isolation is a *lower bound* on administrative
contamination rather than a measurement of it. Either answer is worth having, which is why this script
exists: `penumbra.synthetic` now carries a co-back-dating axis, and the generator knows exactly which
dyads are administrative and which record carries them, so the question is decidable rather than
arguable.

Two regimes, and the difference between them is the finding.

**One convention.** The partner group's record is back-dated by the same law as the focal group's. Every
dyad the wave puts into $r^\star$ early is one the focal record already carries, so focal isolation loses
nothing and Section 3.3's sentence holds. This is the regime a single curator working to a single rule
produces.

**Mixed conventions.** The partner group's record follows its own law, drawn here from the trade
register's coded gaps so the widths are ones a real curator produced. Now the trace in $r^\star$ can
reach further than the focal record does, and focal isolation reads the focal width. This is corpus A:
7,615 events the source dates exactly against 447 it dates only to a five-year block, inside one target
relation.

Three quantities per cell, all against a truth the generator sets:

* **the focal-record horizon**, the largest width the focal register carries plus one, which is what
  focal isolation identifies and what Table 4 grades it against;
* **the administrative horizon**, the largest lead time at which *any* record carries a dyad from the
  acceding entity into the focal group's members that the honest registers do not, counting only dyads
  the focal event caused;
* **the ambient off-focal reach**, the same statistic without the causal restriction, computed for
  positives and for matched negatives, because an administrative dyad that positives and negatives
  carry equally is not a trace of anything and calling it one would be the error this paper is about.

    python scripts/run_co_backdating.py
    python scripts/run_co_backdating.py --quick
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from penumbra.synthetic import ParametricConfig, generate_parametric  # noqa: E402
from penumbra.umbra import NEVER_EVENT, HorizonAudit, delta_star  # noqa: E402

RESULTS = ROOT / "results"
RSTAR = "r_star"
FIELD_ANCHORS = ["r_latent_1", "r_latent_2", "r_noise"]
HORIZONS = range(0, 9)
MAX_H = 8
THRESHOLD = 0.01
# The density is picked from this ladder by a measured worst case rather than set by hand, which is the
# discipline Section 5.2 states and `run_synthetic_homophily.budget_headroom` implements: back-dating
# and a wave both enlarge the pool of group-induced dyads, and if the fixed edge budget cannot record
# the widest setting then r*'s density moves with the setting and every curve slopes for that reason.
# 0.12 is Table 4's own density and is first in the ladder so the two grids are read in one regime
# wherever it covers the sweep.
DENSITY_LADDER = (0.12, 0.14, 0.16, 0.20, 0.25)
FOCAL_ZERO = 1e-9


def _pta_gap_pmf() -> tuple:
    d = json.loads((RESULTS / "desta_delta_star.json").read_text(encoding="utf-8"))
    dist = d["event_gaps"]["distribution"]
    return tuple((int(k), float(v)) for k, v in sorted(dist.items(), key=lambda kv: int(kv[0])))


def _first_below(series: dict, threshold: float) -> int | None:
    for h in sorted(series):
        if h >= 1 and series[h] < threshold:
            return int(h)
    return None


def _reported(estimate: int | None) -> int:
    return MAX_H + 1 if estimate is None else int(estimate)


def one_cell(beta: int, h: float, share: float, partner_pmf: tuple | None, seed: int,
             density: float) -> dict:
    """One corpus. Four estimators, two truths, and the gap between the two truths."""
    cfg = ParametricConfig(homophily=h, anchors_share_latent_space=True,
                           density_rstar=density, density_other=density, density_noise=density,
                           co_backdating=share, co_backdating_beta_pmf=partner_pmf, seed=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        edges, events, membership, _g, meta, recorded = generate_parametric(beta, 1.0, cfg)

    audit = HorizonAudit(edges, membership, events)
    curve = audit.u1_curve(horizons=HORIZONS, levels=(1,), negatives=NEVER_EVENT)
    rs = curve[curve.relation == RSTAR].set_index("horizon")
    pooled = {int(k): float(v) for k, v in rs.contrast.items()}
    best = curve[curve.relation.isin(FIELD_ANCHORS)].groupby("horizon").contrast.max()
    residual = {int(k): float(pooled[int(k)] - v) for k, v in best.items()}

    stub = pd.DataFrame({"relation": ["_stub"], "year": [0], "cow_i": [0], "cow_j": [1],
                         "weight": [1]})
    focal_audit = HorizonAudit(stub, recorded, events)
    tp = focal_audit.trace_presence(events, horizons=HORIZONS)
    focal_curve = {int(k): float(v) for k, v in tp.groupby("horizon").on_focal_record.mean().items()}

    ds = delta_star(curve, RSTAR, FIELD_ANCHORS, level=1)
    cb = meta["co_backdating"]
    est = {
        "focal_isolation": _reported(_first_below(focal_curve, FOCAL_ZERO)),
        "delta_star_lo": _reported(ds["delta_star_lo"]),
        "residual_rule": _reported(_first_below(residual, THRESHOLD)),
        "unbanded_rule": _reported(_first_below(pooled, THRESHOLD)),
    }
    return {
        "beta": beta, "homophily": h, "co_backdating": share, "seed": seed,
        "partner_law": "mixed" if partner_pmf else "one",
        "focal_record_horizon": cb["focal_record_horizon"],
        "focal_record_horizon_every_register": cb["focal_record_horizon_every_register"],
        "administrative_horizon": cb["administrative_horizon"],
        "gap": int(cb["administrative_horizon"] - cb["focal_record_horizon"]),
        "gap_every_register": int(cb["administrative_horizon"]
                                  - cb["focal_record_horizon_every_register"]),
        "events_added": cb["events_added"],
        "partner_width_max": cb["partner_width_max"],
        "share_of_events_with_a_caused_off_focal_trace":
            cb["share_of_events_with_a_caused_off_focal_trace"],
        "share_where_the_caused_trace_exceeds_the_focal_record":
            cb["share_where_the_caused_trace_exceeds_the_focal_record"],
        "ambient": {k: cb[k] for k in ("ambient_mean_reach_positives",
                                       "ambient_mean_reach_negatives",
                                       "ambient_share_positives",
                                       "ambient_share_negatives",
                                       "ambient_off_focal_horizon")},
        "estimates": est,
        "density_rstar": round(meta["density_rstar_mean"], 8),
        "density_rstar_range": float(meta["density_rstar_range"]),
        "budget_headroom": int(meta["budget_headroom"]),
        "n_accessions": int(meta["n_accessions"]),
    }


def _slope(xs, ys) -> float:
    x, y = np.asarray(xs, float), np.asarray(ys, float)
    if x.size < 2 or np.ptp(x) == 0:
        return float("nan")
    return float(np.polyfit(x, y, 1)[0])


def summarise(cells: list[dict]) -> dict:
    """Each estimator against each of the two truths, per convention regime and wave share.

    The pair of gradings is the point. Against the focal-record horizon, focal isolation is the
    instrument Table 4 reports. Against the administrative horizon, it is an estimator of a quantity
    that can exceed what it reads, and the slope says by how much it fails to track it.
    """
    df = pd.DataFrame([{**{k: c[k] for k in ("beta", "homophily", "co_backdating", "seed",
                                             "partner_law", "focal_record_horizon",
                                             "focal_record_horizon_every_register",
                                             "administrative_horizon", "gap",
                                             "gap_every_register")},
                        **{f"est_{k}": v for k, v in c["estimates"].items()}}
                       for c in cells])
    names = [c[4:] for c in df.columns if c.startswith("est_")]
    out = {}
    for (law, share), g in df.groupby(["partner_law", "co_backdating"]):
        key = f"{law},share={share}"
        out[key] = {"cells": int(len(g)),
                    "mean_gap_focal_group_only": round(float(g.gap.mean()), 3),
                    "max_gap_focal_group_only": int(g.gap.max()),
                    "share_of_cells_with_a_gap": round(float((g.gap > 0).mean()), 3),
                    "mean_gap_every_register": round(float(g.gap_every_register.mean()), 3),
                    "max_gap_every_register": int(g.gap_every_register.max()),
                    "share_of_cells_with_a_gap_every_register":
                        round(float((g.gap_every_register > 0).mean()), 3)}
        truths = {"vs_focal_group_only": "focal_record_horizon",
                  "vs_every_register": "focal_record_horizon_every_register",
                  "vs_administrative": "administrative_horizon"}
        for n in names:
            col = g[f"est_{n}"]
            out[key][n] = {}
            for label, truth in truths.items():
                tr = g[truth]
                out[key][n][label] = {
                    "mean_error": round(float((col - tr).mean()), 3),
                    "slope": round(_slope(tr, col), 3),
                    "exact": int((col == tr).sum()),
                    "undershoots": int((col < tr).sum())}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--json", type=Path, default=RESULTS / "co_backdating.json")
    args = ap.parse_args()

    pta = _pta_gap_pmf()
    betas = [0, 2, 4] if args.quick else [0, 1, 2, 3, 4, 5]
    hs = [0.0, 3.0] if args.quick else [0.0, 1.0, 2.0, 3.0]
    shares = [0.0, 0.5] if args.quick else [0.0, 0.1, 0.25, 0.5]
    seeds = [0, 1] if args.quick else [0, 1, 2, 3, 4]

    print("Section 3.3's 'and nothing else', as a measurement. Two conventions, four wave shares, "
          f"{len(betas)} widths, {len(hs)} homophily settings, {len(seeds)} seeds.\n")

    # ---- the edge budget first, because a density that cannot record the widest setting would make
    # ---- every curve below slope for a reason unrelated to leakage ----
    peak, arg = 0, None
    for h in hs:
        for law_pmf in (None, pta):
            for seed in seeds:
                cfg = ParametricConfig(homophily=h, density_rstar=DENSITY_LADDER[-1],
                                       density_other=DENSITY_LADDER[-1],
                                       density_noise=DENSITY_LADDER[-1],
                                       co_backdating=max(shares),
                                       co_backdating_beta_pmf=law_pmf, seed=seed)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    *_r, meta, _rec = generate_parametric(max(betas), 1.0, cfg)
                if meta["peak_eligible_backdated_dyads"] > peak:
                    peak = meta["peak_eligible_backdated_dyads"]
                    arg = {"homophily": h, "seed": seed,
                           "partner_law": "mixed" if law_pmf else "one",
                           "beta": max(betas), "co_backdating": max(shares)}
    n_pairs = 200 * 199 // 2
    density = next((d for d in DENSITY_LADDER if round(d * n_pairs) >= peak), None)
    if density is None:
        print(f"  FAIL: the widest setting needs {peak} of {n_pairs} pairs, above the ladder")
        return 1
    print(f"  the widest setting peaks at {peak:,} eligible dyads of {n_pairs:,} pairs, needing "
          f"density {peak / n_pairs:.4f}; the ladder's first covering value is {density}")
    print(f"  worst case at {arg}\n")

    cells = []
    for law, pmf in (("one", None), ("mixed", pta)):
        for share in shares:
            if share == 0.0 and law == "mixed":
                continue          # no wave, so the partner law cannot matter; one baseline is enough
            for h in hs:
                for beta in betas:
                    for seed in seeds:
                        cells.append(one_cell(beta, h, share, pmf, seed, density))
            g = [c for c in cells if c["partner_law"] == law and c["co_backdating"] == share]
            print(f"  {law:6s} share={share:<5} cells={len(g):3d}  "
                  f"gap on the focal group's record only "
                  f"{np.mean([c['gap'] for c in g]):+.2f} (max {max(c['gap'] for c in g)}, "
                  f"{np.mean([c['gap'] > 0 for c in g]) * 100:.0f} percent of cells)   "
                  f"gap when every register is read "
                  f"{np.mean([c['gap_every_register'] for c in g]):+.2f} "
                  f"(max {max(c['gap_every_register'] for c in g)})")

    dens = {c["density_rstar"] for c in cells}
    if len(dens) > 1 or max(c["density_rstar_range"] for c in cells) > 1e-12:
        print(f"  FAIL: r*'s density is not invariant across the sweep: {sorted(dens)}")
        return 1
    low = min(c["budget_headroom"] for c in cells)
    print(f"\n  r* density {sorted(dens)[0]:.6f} exactly across every cell; smallest budget "
          f"headroom {low} dyads")
    if low < 0:
        print("  FAIL: the edge budget cannot record the widest setting")
        return 1

    summary = summarise(cells)
    for est in ("focal_isolation", "delta_star_lo", "residual_rule", "unbanded_rule"):
        print(f"\n{est}, mean error / slope against each truth\n")
        print(f"  {'regime':22s} {'focal group only':>20s} {'every register':>20s} "
              f"{'administrative':>20s}")
        for key, body in summary.items():
            b = body[est]
            print(f"  {key:22s} "
                  f"{b['vs_focal_group_only']['mean_error']:+11.2f} /"
                  f"{b['vs_focal_group_only']['slope']:6.2f} "
                  f"{b['vs_every_register']['mean_error']:+11.2f} /"
                  f"{b['vs_every_register']['slope']:6.2f} "
                  f"{b['vs_administrative']['mean_error']:+11.2f} /"
                  f"{b['vs_administrative']['slope']:6.2f}")

    ambient = {
        "mean_reach_positives": round(float(np.mean(
            [c["ambient"]["ambient_mean_reach_positives"] for c in cells])), 4),
        "mean_reach_negatives": round(float(np.mean(
            [c["ambient"]["ambient_mean_reach_negatives"] for c in cells])), 4),
        "share_positives": round(float(np.mean(
            [c["ambient"]["ambient_share_positives"] for c in cells])), 4),
        "share_negatives": round(float(np.mean(
            [c["ambient"]["ambient_share_negatives"] for c in cells])), 4),
        "max_horizon": int(max(c["ambient"]["ambient_off_focal_horizon"] for c in cells)),
    }
    print("\nthe ambient off-focal administrative content, positives against matched negatives")
    print(f"  mean reach {ambient['mean_reach_positives']} against "
          f"{ambient['mean_reach_negatives']}; share carrying one "
          f"{ambient['share_positives']} against {ambient['share_negatives']}; "
          f"largest lead time at which any of it appears {ambient['max_horizon']}")
    print("  an administrative dyad positives and negatives carry alike is not a trace of the event, "
          "and the difference between the two columns is the part a diagnostic could read as one")

    payload = {
        "question": ("does administrative back-dating reach r-star from records other than the focal "
                     "group's own, and does focal isolation therefore undershoot"),
        "grid": {"betas": betas, "homophily": hs, "co_backdating_shares": shares, "seeds": seeds,
                 "density": density, "density_ladder": list(DENSITY_LADDER),
                 "partner_laws": ["one", "mixed"], "partner_mixed_pmf": pta},
        "budget_headroom": {"peak_eligible_backdated_dyads": int(peak), "n_pairs": int(n_pairs),
                            "minimum_density_the_worst_case_needs": round(peak / n_pairs, 6),
                            "density_chosen": density, "worst_case": arg},
        "invariance": {"density_values": sorted(dens),
                       "worst_within_run_range": float(max(c["density_rstar_range"]
                                                           for c in cells)),
                       "smallest_budget_headroom": int(low)},
        "cells": cells,
        "summary": summary,
        "ambient_off_focal": ambient,
    }
    write_result(args.json, payload, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

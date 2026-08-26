r"""Homophily against back-dating: turning Section 6.3's deepest claim from an argument into a curve.

Section 6.3 gives three reasons the diagnostic cannot identify a leakage horizon, and calls the third
the deepest: a trace of the event and a persistent similarity between the acceding entity and the
members enter a pooled contrast **identically**, so no contrast of that form can separate them. The
manuscript establishes that by reasoning, not by measurement, and it establishes it on a corpus where
the truth is unknown. The machine for measuring it -- a generator with a settable back-dating width --
was already in hand and had no homophily axis to vary (revision item 2.2).

`penumbra.synthetic.generate_parametric` adds three axes. This script sweeps them and grades **four**
estimators against a truth only a synthetic corpus can supply:

* **focal isolation.** The first lead time at which the acceding entity is absent from the focal
  group's own recorded register. Section 4's fourth component.
* **the pre-specified lower bound.** The first lead time at which $r^\star$'s *clique* contrast enters
  the anchor band. Section 4's U1, the rule Table 2 calibrates.
* **the residual rule.** The first lead time at which $r^\star$'s *pooled* contrast minus the
  strongest anchor's falls below 0.01. This is the rule Section 6.3 applies to corpus A, where it
  returns five periods against a focal record that carries nothing past one.
* **the unbanded rule.** The same without the anchor band, which is what a practitioner who never read
  Section 3.2 would compute.

Every estimand is $\beta + 1$: traces are present for $\Delta \le \beta$, so the smallest trace-free
lead time is $\beta + 1$. Two summaries follow, and they are the point of the script:

**Bias against homophily.** How far each estimator sits from the truth as a function of $h$, at a
fixed known width. The claim under test is that focal isolation's bias stays at zero while the pooled
estimators' grows.

**Identification slope.** For each $h$, the least-squares slope of the estimate on $\beta$ across the
six settings. A slope of 1 means the estimator tracks the truth; a slope near 0 means it reports
something else. This is the quantitative form of "the pooled statistic cannot tell the two apart": if
the slope falls to zero as $h$ rises while the *level* of the estimate rises with $h$, then what the
instrument is reading is homophily and it is reading it as back-dating.

Three further settings, each answering a separate objection:

**Anchors that do not share the latent space** (revision item 2.2). Corpus A's anchors express the same
latent quantity as its target relation, which is why the band subtracts nearly all of the decay;
corpus B's do not, which is why its residual is 0.4075. Both are produced here by one switch, so the
difference between the two field corpora becomes a setting rather than a conjecture.

**A heterogeneous width** (revision item 2.3). A sharp step is a regime the estimator can hardly fail
in. The width is redrawn per event from the PTA register's own coded gap distribution -- median 1,
mean 1.71, a tail to 9 -- which also makes "the true horizon" a decision, so the estimate is graded
against every quantile rather than against one chosen afterwards.

**A negative control** (revision item 2.10). At $h = 0$ and $\beta = 0$ there is nothing to find, and
an instrument that reports a horizon there is reporting noise. The false-positive rate is what the
manuscript currently has no number for.

    python scripts/run_synthetic_homophily.py
    python scripts/run_synthetic_homophily.py --quick     # a 3 x 3 grid, for a smoke test
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
from penumbra.umbra import (BAND_ONLY, NEVER_EVENT, RANK_AND_BAND,  # noqa: E402
                            HorizonAudit, delta_star)

RESULTS = ROOT / "results"
RSTAR = "r_star"

# Two anchor sets, and the difference between them is a finding rather than a robustness check.
#
# `FIELD_ANCHORS` are the relations a field corpus actually offers: relations that cannot record the
# event and are not the same register dated differently. Corpus A's trades, voting agreement and
# militarised disputes are all of this kind.
#
# `IDEAL_ANCHORS` adds `r_current`, which records the *same* membership at the same completeness and
# never back-dates. No field corpus in this paper has such a relation, and C17 records that without it
# the band is set by relations with no group mechanism at all, whose clique rate is exactly zero, so
# the band is too tight and the lower bound overshoots. Reporting both says how much of the estimator's
# performance depends on an anchor the field does not supply.
FIELD_ANCHORS = ["r_latent_1", "r_latent_2", "r_noise"]
IDEAL_ANCHORS = ["r_current", "r_latent_1", "r_latent_2", "r_noise"]

HORIZONS = range(0, 9)
THRESHOLD = 0.01          # Section 6.3's own threshold on the residual, not a new choice
MAX_H = 8                 # the largest lead time examined; "no fire" is reported as this + 1
ESTIMATORS = ["focal_isolation", "focal_isolation_median_rule", "delta_star_lo",
              "delta_star_lo_ideal_anchors", "residual_rule", "unbanded_rule"]

# Sized from the measured worst case rather than guessed, which is the same discipline the legacy
# generator's own configuration records. Back-dating enlarges the pool of group-induced dyads, and the
# widest setting used here -- the PTA gap distribution, whose tail reaches nine periods -- peaks at
# 1,794 eligible dyads of 19,900 pairs, so a budget at density 0.09 cannot record them all at
# completeness 1 and r*'s density would move with the width. 0.12 leaves a third of the budget spare.
# The alternative, letting the budget grow with the width, restores invariance on paper and destroys it
# in fact: every horizon curve would then slope because the relation got denser.
DENSITY = 0.12

# The saturation axis. Corpus A's target relation has density 0.9954 and corpus B's 0.001153, a factor
# of 864 (0.0023 and 431 until D-51), and the manuscript treats saturation (mechanism b) and homophily
# (mechanism h) as two separate
# corpus-specific findings. The sweep below tests whether they are separate: a clique is an extreme-tail
# event in a sparse relation, so homophily cannot complete one, but in a saturated relation it can.
SATURATION = (DENSITY, 0.50, 0.90)


def _pta_gap_pmf() -> tuple:
    """The PTA register's coded gap distribution, as a pmf over back-dating widths.

    Read from the artefact rather than restated, so a corpus rebuild moves it. This is the bridge
    revision item 2.3 asks for between the synthetic testbed and a field register: the widths are not
    invented, they are the ones a real curator produced.
    """
    d = json.loads((RESULTS / "desta_delta_star.json").read_text(encoding="utf-8"))
    dist = d["event_gaps"]["distribution"]
    return tuple((int(k), float(v)) for k, v in sorted(dist.items(), key=lambda kv: int(kv[0])))


def budget_headroom() -> dict:
    """Does the edge budget cover the widest setting used, measured rather than asserted?

    `DENSITY` above is justified by a peak eligible-dyad count, and until this function existed that
    count lived in a comment and in the manuscript's Section 5.2 and in no artefact -- which is exactly
    the defect D-45 records, committed in the text written to report the revision. The extremes are the
    two settings that open the most back-dating windows at once: the widest sharp width, and the PTA gap
    distribution whose tail reaches nine periods. Homophily is swept too, because concentrating the
    founding membership changes how much the groups overlap and therefore how many distinct dyads they
    induce between them.
    """
    peaks = []
    for kw in ({}, {"beta_pmf": _pta_gap_pmf()}):
        for h in (0.0, 4.0):
            beta = 0 if kw else max(6, 5)
            cfg = ParametricConfig(homophily=h, density_rstar=DENSITY, density_other=DENSITY,
                                   density_noise=DENSITY, **kw)
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                *_rest, meta, _rec = generate_parametric(beta, 1.0, cfg)
            peaks.append({"width_regime": "pta_gaps" if kw else f"sharp_beta_{beta}",
                          "homophily": h,
                          "peak_eligible_backdated_dyads": meta["peak_eligible_backdated_dyads"],
                          "headroom": meta["budget_headroom"]})
    worst = max(peaks, key=lambda r: r["peak_eligible_backdated_dyads"])
    n_pairs = 200 * 199 // 2
    return {
        "n_pairs": n_pairs,
        "edge_budget": int(round(DENSITY * n_pairs)),
        "density": DENSITY,
        "worst_case": worst,
        "minimum_density_the_worst_case_needs": round(
            worst["peak_eligible_backdated_dyads"] / n_pairs, 6),
        "per_setting": peaks,
        "budget_ever_exceeded": bool(min(r["headroom"] for r in peaks) < 0),
    }


def _first_below(series: dict, threshold: float) -> int | None:
    """The smallest lead time of one or more at which `series` falls below `threshold`."""
    for h in sorted(series):
        if h >= 1 and series[h] < threshold:
            return int(h)
    return None


# Under a sharp width the two rules below coincide. Under a spread one they do not, and which of them
# is right is the definitional decision revision item 2.3 asks to be reported rather than made
# silently. A share of events carries a width of at least Delta, so the *mean* presence at Delta is
# the tail probability of the width distribution: a rule that thresholds it at one half returns the
# median width, and a rule that waits for the mean to reach zero returns the maximum. The manuscript's
# own reading -- "a step function's mean is a width, not a presence, so the max matters more: one
# non-zero horizon is enough to widen the penumbra" -- prefers the second, and both are reported so
# that preference is visible as a choice.
FOCAL_MEDIAN_THRESHOLD = 0.5
FOCAL_ZERO = 1e-9


def _grade(estimate: int | None, target: float, max_h: int = MAX_H) -> dict:
    """An unreached bound is not a missing value: it is a claim that the horizon exceeds the range.

    `censored` is the flag Table 4 was missing. An estimator that reports the top of the examined range
    has produced a value the range chose, not a value the corpus chose, and a slope computed over cells
    that are all censored is mechanically zero. Recording it per cell is what lets the slope be read on
    the uncensored subset and what lets the range audit below say whether widening the range moves the
    estimate.
    """
    reported = max_h + 1 if estimate is None else estimate
    return {"estimate": estimate, "reported_as": int(reported),
            "error": float(reported - target), "fired": estimate is not None,
            "censored": bool(estimate is None or int(estimate) >= max_h)}


def one_cell(beta: int, h: float, shared: bool, cfg_kw: dict | None = None,
             horizons=None, max_h: int | None = None) -> dict:
    """One corpus, four estimators, one known truth.

    `cfg_kw` reaches `ParametricConfig` unchanged, so a caller can vary the seed or the homophily
    kernel without this function knowing which axis it is sweeping.
    """
    kw = {"density_rstar": DENSITY, "density_other": DENSITY, "density_noise": DENSITY}
    kw.update(cfg_kw or {})
    cfg = ParametricConfig(homophily=h, anchors_share_latent_space=shared, **kw)
    hz = HORIZONS if horizons is None else horizons
    mh = MAX_H if max_h is None else int(max_h)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        edges, events, membership, _g, meta, recorded = generate_parametric(beta, 1.0, cfg)

    # U1 is built on the honest register, because the risk set is "not already a member" and a
    # back-dated register would drop the leaking rows as ineligible.
    audit = HorizonAudit(edges, membership, events)
    curve = audit.u1_curve(horizons=hz, levels=(1,), negatives=NEVER_EVENT)

    rs = curve[curve.relation == RSTAR].set_index("horizon")
    pooled = {int(k): float(v) for k, v in rs.contrast.items()}
    best_field = curve[curve.relation.isin(FIELD_ANCHORS)].groupby("horizon").contrast.max()
    residual = {int(k): float(pooled[int(k)] - v) for k, v in best_field.items()}

    # Focal isolation reads the register a curator wrote, which is the only object that carries the
    # back-dating. A stub graph is enough: the component touches membership only.
    stub = pd.DataFrame({"relation": ["_stub"], "year": [0], "cow_i": [0], "cow_j": [1],
                         "weight": [1]})
    focal_audit = HorizonAudit(stub, recorded, events)
    tp = focal_audit.trace_presence(events, horizons=hz)
    focal_curve = {int(k): float(v)
                   for k, v in tp.groupby("horizon").on_focal_record.mean().items()}

    ds_field = delta_star(curve, RSTAR, FIELD_ANCHORS, level=1)
    ds_ideal = delta_star(curve, RSTAR, IDEAL_ANCHORS, level=1, upper_rule=RANK_AND_BAND)
    ds_band_only = delta_star(curve, RSTAR, IDEAL_ANCHORS, level=1, upper_rule=BAND_ONLY)

    quant = meta["beta_quantiles"]
    target = (beta + 1) if cfg.beta_pmf is None else (quant["max"] + 1)

    return {
        "beta": beta, "homophily": h, "anchors_share_latent_space": shared,
        "density_setting": kw["density_rstar"], "max_lead_time_examined": mh,
        "homophily_form": meta["homophily_form"], "seed": int(cfg.seed),
        "target": target, "beta_quantiles": quant,
        "density_rstar": round(meta["density_rstar_mean"], 8),
        "density_rstar_range": float(meta["density_rstar_range"]),
        "completeness": round(meta["completeness_mean"], 4),
        "n_accessions": meta["n_accessions"],
        "pooled_contrast": {k: round(v, 4) for k, v in pooled.items()},
        "best_field_anchor_contrast": {int(k): round(float(v), 4)
                                       for k, v in best_field.items()},
        "residual": {k: round(v, 4) for k, v in residual.items()},
        "focal_curve": {k: round(v, 4) for k, v in focal_curve.items()},
        "estimators": {
            "focal_isolation": _grade(_first_below(focal_curve, FOCAL_ZERO), target, mh),
            "focal_isolation_median_rule": _grade(
                _first_below(focal_curve, FOCAL_MEDIAN_THRESHOLD), target, mh),
            "delta_star_lo": _grade(ds_field["delta_star_lo"], target, mh),
            "delta_star_lo_ideal_anchors": _grade(ds_ideal["delta_star_lo"], target, mh),
            "residual_rule": _grade(_first_below(residual, THRESHOLD), target, mh),
            "unbanded_rule": _grade(_first_below(pooled, THRESHOLD), target, mh),
        },
        "upper_bound": {
            "rank_and_band": ds_ideal["delta_star_hi"],
            "band_only": ds_band_only["delta_star_hi"],
        },
    }


def _slope(xs, ys) -> float:
    """Least-squares slope of `ys` on `xs`. 1 means the estimator tracks the truth."""
    x = np.asarray(xs, float)
    y = np.asarray(ys, float)
    if x.size < 2 or np.ptp(x) == 0:
        return float("nan")
    return float(np.polyfit(x, y, 1)[0])


def summarise(cells: list[dict], names: list[str]) -> dict:
    """Bias, identification slope and censoring rate per homophily setting, per anchor regime.

    The censoring columns answer an objection Table 4 could not: when an estimator reports the largest
    lead time examined at every width, its slope on the true width is zero for a mechanical reason, and
    a table that shows only the slope cannot distinguish "the output does not depend on the truth" from
    "the range was too narrow to hold the output". `censored` counts the settings in the cell where the
    estimate sits at or above the top of the examined range, and `slope_on_beta_uncensored` recomputes
    the slope on the settings where it does not. A cell with a zero slope and no censoring is the strong
    version of the claim; the range audit is what settles the censored cells.
    """
    df = pd.DataFrame([{"beta": c["beta"], "h": c["homophily"],
                        "shared": c["anchors_share_latent_space"], "target": c["target"],
                        **{n: c["estimators"][n]["reported_as"] for n in names},
                        **{f"_cens_{n}": c["estimators"][n]["censored"] for n in names}}
                       for c in cells])
    out = {}
    for shared, g in df.groupby("shared"):
        key = "anchors_share_latent_space" if shared else "anchors_independent"
        out[key] = {}
        for h, gh in g.groupby("h"):
            cell = {}
            for n in names:
                free = gh[~gh[f"_cens_{n}"]]
                cell[n] = {
                    "mean_error": round(float((gh[n] - gh.target).mean()), 3),
                    "slope_on_beta": round(_slope(gh.beta, gh[n]), 3),
                    "exact_hits": int((gh[n] == gh.target).sum()),
                    "settings": int(len(gh)),
                    "censored": int(gh[f"_cens_{n}"].sum()),
                    "censoring_rate": round(float(gh[f"_cens_{n}"].mean()), 3),
                    "uncensored_settings": int(len(free)),
                    "slope_on_beta_uncensored": (round(_slope(free.beta, free[n]), 3)
                                                 if len(free) >= 2 else None),
                }
            out[key][f"h={h}"] = cell
    return out


def form_and_seed_robustness(betas: list, hs: list, forms: list, seeds: list) -> dict:
    r"""The whole grid, under three homophily kernels and three seeds.

    Two objections, one pass. The first is that "an exponent on latent similarity" is a single
    parametrisation carrying the paper's two most important results, so a finding about it may be a
    finding about that kernel. The second is that most of the 72-cell grid is one corpus at one seed.

    The three kernels are not reparametrisations of one another. `power` is unbounded in inverse squared
    distance. `logistic` is bounded and saturating, so no pair's weight can diverge however close it
    sits. `block` throws the distance kernel away: nodes carry a discrete latent community and two
    nodes are similar if they share one, which is a different generative story rather than a different
    exponent. All three collapse to a uniform weight at $h = 0$, which is what keeps the negative
    control comparable across them.

    What the pass reports is, per kernel and per estimator, the homophily setting at which the slope on
    the true width first leaves 1.00, and the spread of that threshold over seeds. If the collapse is a
    property of the kernel then the thresholds will differ between kernels; if it is a property of the
    statistic they will not.
    """
    out = {}
    for form in forms:
        out[form] = {}
        for shared in (True, False):
            key = "anchors_share_latent_space" if shared else "anchors_independent"
            per_h = {}
            for h in hs:
                per_seed = {}
                for seed in seeds:
                    cells = [one_cell(b, h, shared,
                                     {"seed": seed, "homophily_form": form}) for b in betas]
                    per_seed[str(seed)] = {
                        n: {"slope_on_beta": round(_slope(
                                [c["beta"] for c in cells],
                                [c["estimators"][n]["reported_as"] for c in cells]), 3),
                            "mean_error": round(float(np.mean(
                                [c["estimators"][n]["reported_as"] - c["target"]
                                 for c in cells])), 3),
                            "censored": int(sum(c["estimators"][n]["censored"] for c in cells))}
                        for n in ESTIMATORS}
                per_h[f"h={h}"] = per_seed
            # The threshold: the smallest h at which an estimator's slope drops below 0.9 at any seed,
            # reported as None where it never does inside the swept range.
            thresholds = {}
            for n in ESTIMATORS:
                per_seed_thr = []
                for seed in seeds:
                    thr = None
                    for h in hs:
                        if per_h[f"h={h}"][str(seed)][n]["slope_on_beta"] < 0.9:
                            thr = h
                            break
                    per_seed_thr.append(thr)
                fired = [t for t in per_seed_thr if t is not None]
                thresholds[n] = {
                    "per_seed": per_seed_thr,
                    "min": min(fired) if fired else None,
                    "max": max(fired) if fired else None,
                    "never_collapses_in_seeds": int(sum(1 for t in per_seed_thr if t is None)),
                }
            out[form][key] = {"per_homophily": per_h, "collapse_threshold": thresholds}
            line = "  ".join(
                f"{n.split('_')[0][:5]}="
                + ("none" if thresholds[n]["min"] is None
                   else (f"{thresholds[n]['min']}" if thresholds[n]['min'] == thresholds[n]['max']
                         else f"{thresholds[n]['min']}-{thresholds[n]['max']}"))
                for n in ESTIMATORS)
            print(f"  {form:9s} {key:26s} collapse at h: {line}")
    return out


def seed_replication(betas: list, seeds: list, hs: list) -> dict:
    """The transition rows at more than one seed, because a single seed is not an interval.

    Table 4 reports one corpus per cell and defends the reading on the table's shape: a monotone
    collapse reproduced independently in both anchor regimes across 72 corpora, with entries that are
    either 1.00 or within 0.03 of zero. That defence is about the figure and a reader is entitled to ask
    about the cell. The cells where it matters are the transitional ones, where an estimator is neither
    exact nor collapsed, so those are the ones re-run here at five seeds. What the pass reports is the
    spread of the per-seed slope, which is the quantity a single seed cannot show.
    """
    out = {}
    for shared in (True, False):
        key = "anchors_share_latent_space" if shared else "anchors_independent"
        out[key] = {}
        for h in hs:
            per_seed = {}
            for seed in seeds:
                cells = [one_cell(b, h, shared, {"seed": seed}) for b in betas]
                per_seed[str(seed)] = {
                    n: {"estimates": [c["estimators"][n]["reported_as"] for c in cells],
                        "mean_error": round(float(np.mean(
                            [c["estimators"][n]["reported_as"] - c["target"] for c in cells])), 3),
                        "slope_on_beta": round(_slope(
                            [c["beta"] for c in cells],
                            [c["estimators"][n]["reported_as"] for c in cells]), 3),
                        "censored": int(sum(c["estimators"][n]["censored"] for c in cells))}
                    for n in ESTIMATORS}
            agg = {}
            for n in ESTIMATORS:
                sl = [per_seed[str(sd)][n]["slope_on_beta"] for sd in seeds]
                er = [per_seed[str(sd)][n]["mean_error"] for sd in seeds]
                agg[n] = {
                    "slope_mean": round(float(np.mean(sl)), 3),
                    "slope_min": round(float(np.min(sl)), 3),
                    "slope_max": round(float(np.max(sl)), 3),
                    "slope_sd": round(float(np.std(sl, ddof=1)) if len(sl) > 1 else 0.0, 4),
                    "mean_error_mean": round(float(np.mean(er)), 3),
                    "mean_error_min": round(float(np.min(er)), 3),
                    "mean_error_max": round(float(np.max(er)), 3),
                    "seeds": len(seeds),
                }
            out[key][f"h={h}"] = {"per_seed": per_seed, "over_seeds": agg}
            line = "  ".join(f"{n.split('_')[0][:5]}={agg[n]['slope_mean']:+.2f}"
                             f"[{agg[n]['slope_min']:+.2f},{agg[n]['slope_max']:+.2f}]"
                             for n in ESTIMATORS)
            print(f"  {key:26s} h={h:<4} {line}")
    return out


def range_audit(betas: list, hs: list, wide_max: int) -> dict:
    """Is a zero slope a property of the estimator or of the range the estimator was examined over?

    Where an estimator reports the largest lead time examined at every width, its slope on the true
    width is zero because the output is a constant, and the constant is the top of the range. Widening
    the range separates the two readings. If the estimate moves with the range while the slope on the
    truth stays at zero, the output is tracking the range and carries no information about the width,
    which is the strong form of the claim. If the estimate stops moving and a slope appears, the
    original zero was an artefact of a range too narrow to hold the estimator.
    """
    out = {}
    wide = range(0, wide_max + 1)
    for shared in (True, False):
        key = "anchors_share_latent_space" if shared else "anchors_independent"
        out[key] = {}
        for h in hs:
            narrow_cells = [one_cell(b, h, shared) for b in betas]
            wide_cells = [one_cell(b, h, shared, horizons=wide, max_h=wide_max) for b in betas]
            per = {}
            for n in ESTIMATORS:
                nar = [c["estimators"][n]["reported_as"] for c in narrow_cells]
                wid = [c["estimators"][n]["reported_as"] for c in wide_cells]
                per[n] = {
                    "narrow_range_estimates": nar,
                    "wide_range_estimates": wid,
                    "narrow_max_lead_time": MAX_H, "wide_max_lead_time": wide_max,
                    "narrow_slope": round(_slope(betas, nar), 3),
                    "wide_slope": round(_slope(betas, wid), 3),
                    "narrow_censored": int(sum(c["estimators"][n]["censored"]
                                               for c in narrow_cells)),
                    "wide_censored": int(sum(c["estimators"][n]["censored"] for c in wide_cells)),
                    "estimate_moved_with_the_range": bool(any(w != nn for w, nn in zip(wid, nar))),
                }
            out[key][f"h={h}"] = per
            print(f"  {key:26s} h={h:<4} unbanded narrow {per['unbanded_rule']['narrow_range_estimates']} "
                  f"slope {per['unbanded_rule']['narrow_slope']:+.2f}  ->  wide "
                  f"{per['unbanded_rule']['wide_range_estimates']} slope "
                  f"{per['unbanded_rule']['wide_slope']:+.2f}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--json", type=Path, default=RESULTS / "synthetic_homophily.json")
    args = ap.parse_args()

    betas = [0, 2, 4] if args.quick else [0, 1, 2, 3, 4, 5]
    hs = [0.0, 1.0, 3.0] if args.quick else [0.0, 0.5, 1.0, 2.0, 3.0, 4.0]
    names = list(ESTIMATORS)

    print("the generator's invariance first: r*'s density must not move with h, beta or the regime, "
          "or every curve below slopes for a reason unrelated to leakage")
    head = budget_headroom()
    print(f"  edge budget {head['edge_budget']:,} dyads of {head['n_pairs']:,} pairs at density "
          f"{head['density']}; the widest setting used peaks at "
          f"{head['worst_case']['peak_eligible_backdated_dyads']:,} eligible dyads, needing density "
          f"{head['minimum_density_the_worst_case_needs']:.4f}")
    if head["budget_ever_exceeded"]:
        print("  FAIL: the budget cannot record the widest setting at completeness 1")
        return 1
    cells = []
    for shared in (True, False):
        for h in hs:
            for beta in betas:
                c = one_cell(beta, h, shared)
                cells.append(c)
                print(f"  shared={str(shared):5s} h={h:<4} beta={beta}  target={c['target']}  "
                      + "  ".join(f"{n.split('_')[0][:5]}={c['estimators'][n]['reported_as']}"
                                  for n in names))

    dens = {c["density_rstar"] for c in cells}
    rng_within = max(c["density_rstar_range"] for c in cells)
    print(f"\n  r* density across every cell: {sorted(dens)}  "
          f"worst within-run range {rng_within:.2e}")
    if len(dens) > 1 or rng_within > 1e-12:
        print("  FAIL: the parametric generator does not hold r*'s density fixed")
        return 1
    print("  the density is one exact value across the whole grid, because the edge budget is a "
          "fixed integer count rather than a sampled quantity")

    summary = summarise(cells, names)
    print("\nbias and identification slope, field anchors regime by regime")
    for regime, per_h in summary.items():
        print(f"\n  {regime}")
        print(f"    {'h':>5} " + " ".join(f"{n[:14]:>16s}" for n in names))
        for hk, per_n in per_h.items():
            print(f"    {hk.split('=')[1]:>5} " + " ".join(
                f"{per_n[n]['mean_error']:+6.2f}/{per_n[n]['slope_on_beta']:+5.2f}" + " " * 3
                for n in names))
    print("\n    each cell reads mean error / slope on beta. A slope of 1.00 means the estimator "
          "tracks the known width; a slope near zero means it is reading something else.")

    print("\ncensoring: settings per cell where the estimate sits at the top of the examined range, "
          "and the slope recomputed where it does not")
    for regime, per_h in summary.items():
        print(f"\n  {regime}")
        for hk, per_n in per_h.items():
            bits = []
            for n in names:
                c = per_n[n]
                sl = ("n/a" if c["slope_on_beta_uncensored"] is None
                      else f"{c['slope_on_beta_uncensored']:+.2f}")
                bits.append(f"{n.split('_')[0][:5]} {c['censored']}/{c['settings']} ({sl})")
            print(f"    h={hk.split('=')[1]:<4} " + "  ".join(bits))

    # ---- the whole grid under three kernels and three seeds ----
    print("\nrobustness: the same grid under three homophily kernels, three seeds each")
    forms = ["power", "logistic", "block"]
    grid_seeds = [0, 1] if args.quick else [0, 1, 2]
    robust = form_and_seed_robustness(betas, hs, forms, grid_seeds)
    print("    the collapse threshold is the smallest homophily setting at which an estimator's slope "
          "on the true width drops below 0.9. A kernel-specific finding would move it.")

    # ---- the transition rows at five seeds, because one seed is not an interval ----
    print("\nseed replication on the transition rows")
    seeds = [0, 1] if args.quick else [0, 1, 2, 3, 4]
    trans_hs = [1.0] if args.quick else [1.0, 2.0, 3.0]
    seed_rep = seed_replication(betas, seeds, trans_hs)

    # ---- and the range audit, because a censored slope is not an identification failure ----
    print("\nrange audit: the same cells over a range wide enough for the estimator to fire in")
    wide_max = 12 if args.quick else 20
    audit_hs = [3.0] if args.quick else [2.0, 3.0, 4.0]
    rng_audit = range_audit(betas, audit_hs, wide_max)

    # ---- the negative control: nothing to find, and what each instrument says anyway ----
    control = next(c for c in cells
                   if c["beta"] == 0 and c["homophily"] == 0.0
                   and c["anchors_share_latent_space"])
    false_positives = {n: control["estimators"][n]["reported_as"] > control["target"]
                       for n in names}
    print(f"\nnegative control, h = 0 and beta = 0, where the target is 1:")
    for n in names:
        print(f"  {n:30s} reports {control['estimators'][n]['reported_as']}  "
              f"{'FALSE POSITIVE' if false_positives[n] else 'correct'}")

    # ---- the upper bound, both definitions, over the whole grid ----
    ub = {"rank_and_band_fired": sum(1 for c in cells if c["upper_bound"]["rank_and_band"]
                                     is not None),
          "band_only_fired": sum(1 for c in cells if c["upper_bound"]["band_only"] is not None),
          "cells": len(cells),
          "band_only_equals_lower_bound": sum(
              1 for c in cells
              if c["upper_bound"]["band_only"] is not None
              and c["upper_bound"]["band_only"]
              == c["estimators"]["delta_star_lo_ideal_anchors"]["estimate"])}
    print(f"\nupper bound over {ub['cells']} cells: the pre-specified rule fires in "
          f"{ub['rank_and_band_fired']}, the band-crossing rule in {ub['band_only_fired']}, "
          f"and the band-crossing bound coincides with the lower bound in "
          f"{ub['band_only_equals_lower_bound']} of those")

    # ---- heterogeneous width, from the PTA register's own gaps ----
    pmf = _pta_gap_pmf()
    print(f"\nheterogeneous width, drawn per event from the PTA register's coded gaps: {pmf}")
    het = []
    for shared in (True, False):
        for h in hs:
            c = one_cell(0, h, shared, {"beta_pmf": pmf})
            het.append(c)
            q = c["beta_quantiles"]
            print(f"  shared={str(shared):5s} h={h:<4} realised widths max={q['max']} "
                  f"q90={q['q90']} median={q['median']}  "
                  + "  ".join(f"{n.split('_')[0][:5]}={c['estimators'][n]['reported_as']}"
                              for n in names))

    # Under a spread width the estimand is a choice, so every quantile is graded rather than one.
    het_grades = {}
    for c in het:
        q = c["beta_quantiles"]
        key = f"shared={c['anchors_share_latent_space']},h={c['homophily']}"
        est = {n: c["estimators"][n]["reported_as"] for n in names}
        targets = {"max_plus_1": q["max"] + 1, "q90_plus_1": q["q90"] + 1,
                   "median_plus_1": q["median"] + 1}
        het_grades[key] = {
            "targets": targets, "estimates": est,
            # Which definition of "the horizon" each estimator is actually reporting, rather than
            # which one it was hoped to report.
            "matches": {n: sorted(t for t, v in targets.items() if abs(v - est[n]) < 1e-9)
                        for n in names},
        }

    # ---- dating noise: the declared-resolution stratum's synthetic counterpart ----
    print("\ndating noise: a share of events whose coded date is one period late, the register being "
          "wrong rather than early")
    noisy = []
    for share in (0.0, 0.1, 0.3):
        c = one_cell(0, 1.0, True, {"date_noise": share, "date_noise_shift": 1})
        noisy.append({"date_noise": share, **c})
        print(f"  displaced share {share:<4} focal isolation curve "
              f"{[c['focal_curve'].get(i) for i in range(0, 4)]}  "
              f"focal estimate {c['estimators']['focal_isolation']['reported_as']}")
    print("  focal isolation reads the displacement as a width of exactly one period, which is what "
          "corpus A's declared-resolution stratum shows at 0.1419")

    # ---- saturation: is the clique statistic robust to homophily, or only to sparse homophily? ----
    print()
    print("saturation: the same homophily against a target relation of increasing density, which is "
          "the axis separating corpus A from corpus B")
    sat = []
    for sat_density in SATURATION:
        for h in (0.0, 3.0):
            c = one_cell(2, h, True, {"density_rstar": sat_density,
                                      "density_other": sat_density,
                                      "density_noise": sat_density})
            sat.append(c)
            print(f"  density {sat_density:<5} h={h:<4} target={c['target']}  "
                  + "  ".join(f"{n.split('_')[0][:5]}={c['estimators'][n]['reported_as']}"
                              for n in names))
            print(f"        clique contrast beyond the width: "
                  f"{[c['pooled_contrast'].get(i) for i in range(3, 9)]}")
    print("  a clique needs every dyad, so in a sparse relation homophily cannot complete one and the "
          "lower bound survives; the denser the relation, the less that is true")

    payload = {
        "grid": {"betas": betas, "homophily": hs, "regimes": [True, False],
                 "density": DENSITY},
        "budget_headroom": head,
        "estimand": "beta + 1, the smallest trace-free lead time",
        "threshold": THRESHOLD,
        "field_anchors": FIELD_ANCHORS, "ideal_anchors": IDEAL_ANCHORS,
        "invariance": {"density_values": sorted(dens),
                       "worst_within_run_range": float(rng_within),
                       "exactly_invariant": True},
        "cells": cells,
        "summary": summary,
        "seed_replication": seed_rep,
        "range_audit": rng_audit,
        "form_and_seed_robustness": robust,
        "homophily_forms": forms,
        "negative_control": {"cell": {k: control[k] for k in
                                      ("beta", "homophily", "target", "estimators",
                                       "pooled_contrast", "residual", "focal_curve")},
                             "false_positives": false_positives},
        "upper_bound": ub,
        "heterogeneous_width": {"pmf": pmf, "cells": het, "grades": het_grades},
        "dating_noise": noisy,
        "saturation": {"densities": list(SATURATION), "cells": sat},
    }
    write_result(args.json, payload, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

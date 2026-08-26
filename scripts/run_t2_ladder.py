r"""T2: interval-censored competing-risks termination. Reproduces V6, which had no script.

`results/t2_ladder.json` and `results/t2_focal.json` were produced by an ad-hoc run and no code path
regenerated them, which puts V6 -- one of the two verdicts that **hold** -- in the position V11 was in
before `quantify_atop_phase_defect.py`: a finding resting on numbers nothing reproduces. This closes
that, and it fixes a mislabelled key in the second file (see below).

Two outputs, matching what V6 reports.

**The ladder** (`t2_ladder.json`). The collapsed two-cause model with D-19's four pre-specified
covariates, fitted with and without §5.3's focal exclusion. Reports per-cause coefficients by **name**,
any-cause and per-cause AUC, events by cause, and events per parameter -- the last because D-19's whole
point is that 36 covariates were under-identified and four are not.

**The focal sweep** (`t2_focal.json`). $\phi$ level $\times$ focal exclusion, four cells, reporting
log-likelihood, AUC and the co-membership coefficient. **The original file's `beta_phi_*` keys held
`log_size`, not $\phi$** -- D-20 caught the positional-indexing slip and fixed the *document*, where V6
correctly reports $\phi = +0.255$ against `log_size` $= -0.402$, but the results file was never
regenerated and still carried the wrong label. Coefficients here are pulled by name from
`meta["feature_names"]`, so the class of error D-20 describes cannot recur.

D-19's covariates, chosen on substantive grounds before any coefficient was inspected and repeated here
because a script that silently picks features is the garden of forking paths:

1. `log_size` -- the most basic structural property of a coalition
2. `phi_igo_comembership` -- internal cohesion at D-13's primary level
3. `polity2_mean` -- regime type
4. `polity2_std` -- regime heterogeneity, the covariate P5 is about

    python scripts/run_t2_ladder.py
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

from penumbra.hazard import CENSORED, DiscreteHazard, events_per_parameter  # noqa: E402
from penumbra.t2 import build_panel  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402

# D-19's four, by name. A KeyError here is the correct failure: it means the panel's feature set moved
# and the pre-specification has to be revisited deliberately rather than silently re-matched.
COVARIATES = ["log_size", "phi_igo_comembership", "polity2_mean", "polity2_std"]
PHI_PRIMARY = 25            # D-13's primary level for co-membership
CAUSE_NAMES = {1: "dissolution", 2: "superseded"}
# `log` rather than `linear`, because D-20 records the coefficient columns as
# [intercept, log_duration, log_size, phi, polity2_mean, polity2_std] and only this baseline produces a
# log-duration column. Recovering it was how the original run's parameterisation was identified: the
# linear baseline gives a duration coefficient of +0.002 where the recorded table has +0.135.
BASELINE = "log"
# Minimum |coefficient| on both sides for a cross-cause sign flip to count as a reversal. Declared
# rather than tuned: 1 % change in log-odds per standard deviation is the smallest effect worth
# calling an effect, and P5 is scored on reversals.
REVERSAL_FLOOR = 0.01


def select(panel, meta):
    """Restrict the panel's design to D-19's four covariates, by name."""
    names = list(meta["feature_names"])
    idx = [names.index(c) for c in COVARIATES]
    panel.X = panel.X[:, idx]
    return panel, COVARIATES


def _row_labels(panel) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per row: the entity's cause, and whether this period lies inside its event interval."""
    tL, tR = panel.t_L[panel.entity], panel.t_R[panel.entity]
    inside = (panel.cause[panel.entity] != CENSORED) & (panel.period > tL) & (panel.period <= tR)
    return panel.cause[panel.entity], inside, (tR - tL)


def hazard_auc(model, panel) -> tuple[float, dict, dict]:
    r"""Discrimination at the **row** level: does this coalition terminate in this period?

    This is the estimand the hazard actually fits, and it is the definition the original ad-hoc run
    used -- established by reproducing its numbers, since the script itself no longer exists. The
    obvious alternative, scoring $1 - S$ at each entity's last observed period, is **inverted by
    construction**: an entity that terminates early has fewer rows and is therefore evaluated over a
    shorter window, so the cumulative event probability is *lower* for exactly the entities that had
    events. It returns 0.27. Recorded because it is a plausible-looking metric that measures exposure
    length rather than risk, and nothing in its output says so.

    Wide-interval positives would be undetermined at the row level -- the source says the event happened
    somewhere in $(t_L, t_R]$ without saying when -- so their count is returned rather than assumed
    zero. On this corpus it is zero: every termination has a unit-width interval in duration time, and
    section 9.7's knowability lag is a separate quantity from interval width.
    """
    from sklearn.metrics import roc_auc_score
    h = model.hazards(panel)
    cause, inside, width = _row_labels(panel)
    y = inside.astype(int)
    undetermined = int((inside & (width > 1)).sum())
    any_auc = (float(roc_auc_score(y, h.sum(axis=1))) if len(np.unique(y)) > 1 else float("nan"))
    per = {}
    for j, name in CAUSE_NAMES.items():
        yj = (inside & (cause == j)).astype(int)
        per[name] = (round(float(roc_auc_score(yj, h[:, j - 1])), 4)
                     if len(np.unique(yj)) > 1 else None)
    return any_auc, per, {"n_rows": int(len(y)), "n_positive_rows": int(y.sum()),
                          "undetermined_positive_rows": undetermined}


def fit_one(focal_excluded: bool, phi_level: int, collapse: bool = True) -> dict:
    panel, meta = build_panel(collapse=collapse, focal_excluded=focal_excluded,
                              phi_level=phi_level)
    panel, names = select(panel, meta)
    model = DiscreteHazard(n_causes=meta["n_causes"], baseline=BASELINE)
    model.fit(panel)

    # [intercept, log_duration] then the covariates, in the order `select` left them.
    cols = ["intercept", "log_duration"] + names
    coef = {c: {CAUSE_NAMES.get(j + 1, f"cause_{j + 1}"): round(float(model.coef_[j, k]), 6)
                for j in range(meta["n_causes"])}
            for k, c in enumerate(cols)}
    # Every column except the intercept, whose sign carries no cross-cause meaning. `log_duration` must
    # be in scope: it is the baseline rather than a covariate, and it is **one of the two reversals P5
    # is scored on** -- old coalitions dissolve while young ones are replaced. Restricting the scan to
    # the four covariates silently drops it and turns V6's two reversals into one.
    #
    # A sign flip needs both sides to be a coefficient rather than a rounding artefact. `polity2_mean`
    # came out -0.0925 against +0.0006 after the left-truncation fix, and a sign-only test reports that
    # as a third reversal for P5 when +0.0006 is not positive in any usable sense. The floor is declared
    # here, applies to standardised covariates on the logit scale, and both lists are reported so the
    # choice is visible instead of built in.
    signs = {c: {np.sign(v) for v in coef[c].values()} for c in coef if c != "intercept"}
    reversing_any = [c for c, s in signs.items() if len(s) > 1]
    reversing = [c for c in reversing_any
                 if all(abs(v) >= REVERSAL_FLOOR for v in coef[c].values())]
    auc_any, auc_cause, rows = hazard_auc(model, panel)
    return {
        "phi_level": phi_level, "focal_excluded": focal_excluded, "collapse": collapse,
        "loglik": round(float(model.loglik_), 4),
        "coef": coef,
        # P5 is about covariates that behave differently across causes, so the sign reversals are the
        # verdict's object and are extracted rather than left to be eyeballed from the table.
        "reversing": reversing,
        "reversing_sign_only": reversing_any,
        "reversal_floor": REVERSAL_FLOOR,
        "auc_any": round(auc_any, 4),
        "auc_cause": auc_cause,
        "row_counts": rows,
        "events": {str(k): int(v) for k, v in meta["events_by_cause"].items()},
        "rule_assigned": int(meta["rule_assigned_events"]),
        "events_per_parameter": {k: (round(float(v), 2) if isinstance(v, (int, float)) else v)
                                 for k, v in events_per_parameter(panel, len(names)).items()},
        "n_entities": int(meta["n_entities"]), "n_rows": int(meta["n_rows"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ladder", type=Path, default=ROOT / "results" / "t2_ladder.json")
    ap.add_argument("--focal", type=Path, default=ROOT / "results" / "t2_focal.json")
    args = ap.parse_args()

    print("=== ladder: collapsed two-cause model, D-19's four covariates ===")
    ladder = {}
    for fx in (False, True):
        r = fit_one(focal_excluded=fx, phi_level=PHI_PRIMARY)
        ladder[f"focal_{fx}"] = r
        print(f"\nfocal_excluded={fx}  loglik {r['loglik']}  auc_any {r['auc_any']}  "
              f"auc_cause {r['auc_cause']}")
        print(f"  events {r['events']}  rule_assigned {r['rule_assigned']}  "
              f"events/param {r['events_per_parameter']}")
        print(f"  {'covariate':22s} " + " ".join(f"{n:>13s}" for n in CAUSE_NAMES.values()))
        for c, v in r["coef"].items():
            print(f"  {c:22s} " + " ".join(f"{v[n]:>13.4f}" for n in CAUSE_NAMES.values()))
        print(f"  reversing across causes (|b| >= {r['reversal_floor']}): {r['reversing']}")
        extra = [c for c in r["reversing_sign_only"] if c not in r["reversing"]]
        if extra:
            print(f"    sign flips below the floor, not counted: {extra}")

    print("\n=== focal sweep: phi level x focal exclusion ===")
    sweep = []
    for lvl in (1, PHI_PRIMARY):
        for fx in (False, True):
            r = (ladder[f"focal_{fx}"] if lvl == PHI_PRIMARY
                 else fit_one(focal_excluded=fx, phi_level=lvl))
            phi = r["coef"]["phi_igo_comembership"]
            sweep.append({
                "phi_level": lvl, "focal_excluded": fx,
                "loglik": r["loglik"], "auc": r["auc_any"],
                # Named for what they are. The file this replaces called log_size "beta_phi" (D-20).
                "beta_phi_dissolution": round(phi["dissolution"], 4),
                "beta_phi_superseded": round(phi["superseded"], 4),
                "beta_log_size_dissolution": round(r["coef"]["log_size"]["dissolution"], 4),
                "beta_log_size_superseded": round(r["coef"]["log_size"]["superseded"], 4),
                # At level 1 co-membership density is ~0.995 for nearly every coalition-year (C15), so
                # phi is close to constant and standardising a near-constant inflates its coefficient
                # without adding information: the fitted values reach ~40 on the logit scale. The
                # log-likelihood and AUC columns are unaffected and are what V6 reports from this
                # sweep; the coefficient at level 1 is flagged rather than quoted.
                "phi_coefficient_interpretable": lvl != 1,
            })
    print(pd.DataFrame(sweep).to_string(index=False))

    print("\n=== three-cause model, reported descriptively (D-19) ===")
    three = fit_one(focal_excluded=False, phi_level=PHI_PRIMARY, collapse=False)
    print(f"  loglik {three['loglik']}  events {three['events']}  "
          f"events/param {three['events_per_parameter']}")
    print("  the absorption arm is under-identified and is not an estimate")

    write_result(args.ladder, {**ladder, "three_cause": three}, indent=2)
    write_result(args.focal, sweep, indent=2)
    print(f"\nwritten to {args.ladder} and {args.focal}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

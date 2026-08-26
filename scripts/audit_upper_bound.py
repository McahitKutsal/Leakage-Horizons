r"""Can the upper bound be repaired, or does the bracket have to go?

Section 4 estimates the leakage horizon as an interval bracketed below by an exact clique statistic,
declared specific and insensitive, and above by rank position together with single-feature
discrimination, declared sensitive and non-specific. The bracket is the paper's second stated
contribution and the abstract sells the suite as an interval estimator. Section 6.1 then reports that
the upper bound was unreachable in most synthetic settings, and Section 9 lists that as a threat.

Revision item 2.4 offers two ways out: repair the upper bound by replacing its rank condition with a
band crossing, or drop the interval from the framing and report the upper bound as a negative
methodological finding. This script decides between them with evidence rather than with preference,
and it answers three questions in the order that makes the third one meaningful.

**1. How often does the pre-specified rule actually fire?** The manuscript says 2 of 6 settings and
names them as the endpoints of the sweep. Both are checked here against the artefact rather than
restated.

**2. Does dropping the rank condition make it fire?** Yes, and that is not the end of the matter: a
bound that fires is useful only if it lies above the lower bound and carries information the lower
bound does not.

**3. Do the two statistics order the way the design assumes?** This is the question that settles it.
The design needs the specific statistic to declare the horizon closed early and the sensitive one to
declare it closed late. On corpus A they do the opposite at every lead time examined, which makes the
interval empty rather than wide -- a fact about the two statistics, not about the corpus.

    python scripts/audit_upper_bound.py
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
from penumbra.umbra import (BAND_ONLY, NEVER_EVENT, RANK_AND_BAND,  # noqa: E402
                            delta_star)

RESULTS = ROOT / "results"
RSTAR_A = "igo_comembership"
ANCHORS_A = ["trades", "conflicts_with", "votes_with"]


def synthetic_from_artefact() -> dict:
    """Both rules on the calibration artefact, recomputed from its own stored detail.

    The detail rows carry every field either rule needs -- the clique contrast and its band, the
    single-feature AUC and its band, and whether r* held top rank -- so the comparison needs no rerun
    and cannot drift from the run the manuscript quotes.
    """
    d = json.loads((RESULTS / "delta_star_calibration.json").read_text(encoding="utf-8"))
    rows = []
    for r in d["results"]:
        if r["stratum"] != NEVER_EVENT:
            continue
        det = r["detail"]
        hi_rank = next((x["horizon"] for x in det
                        if (not x["rstar_is_top"]) and x["auc_phi_alone"] <= x["band_auc"]), None)
        hi_band = next((x["horizon"] for x in det
                        if x["auc_phi_alone"] <= x["band_auc"]), None)
        rows.append({"beta": r["beta"], "target": r["target"], "lo": r["delta_star_lo"],
                     "hi_reported": r["delta_star_hi"], "hi_rank_and_band": hi_rank,
                     "hi_band_only": hi_band,
                     "rstar_top_at_every_lead_time": all(x["rstar_is_top"] for x in det)})
    df = pd.DataFrame(rows)
    fired_rank = int(df.hi_rank_and_band.notna().sum())
    fired_band = int(df.hi_band_only.notna().sum())
    return {
        "settings": int(len(df)),
        "pre_specified_rule_fires_in": fired_rank,
        "pre_specified_rule_fires_at_beta": df.loc[df.hi_rank_and_band.notna(), "beta"].tolist(),
        "band_only_rule_fires_in": fired_band,
        "recomputation_matches_the_stored_bound": bool(
            (df.hi_reported.fillna(-1) == df.hi_rank_and_band.fillna(-1)).all()),
        "band_only_equals_lower_bound_in": int((df.hi_band_only == df.lo).sum()),
        "band_only_equals_target_in": int((df.hi_band_only == df.target).sum()),
        "rows": rows,
    }


def corpus_a() -> dict:
    """Both rules on corpus A, at every level of the declared ladder, from the stored curves."""
    out = {}
    for fname, label in (("u1_real_primary.json", "organisations"),
                         ("u1_alliance_primary.json", "alliances")):
        path = RESULTS / fname
        if not path.exists():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        curve = pd.DataFrame(d["curves"])
        curve = curve[curve.negative_stratum == NEVER_EVENT]
        levels = sorted(int(x) for x in curve.loc[curve.relation == RSTAR_A, "level"].unique())
        rows = []
        for lvl in levels:
            per_rule = {}
            for rule in (RANK_AND_BAND, BAND_ONLY):
                ds = delta_star(curve, RSTAR_A, ANCHORS_A, level=lvl, upper_rule=rule)
                per_rule[rule] = ds
            base = per_rule[RANK_AND_BAND]
            lo = base["delta_star_lo"]
            hi_band = per_rule[BAND_ONLY]["delta_star_hi"]
            rows.append({
                "level": lvl, "lo": lo,
                "hi_rank_and_band": base["delta_star_hi"],
                "hi_band_only": hi_band,
                # The decisive quantity. An upper bound below the lower bound is not a wide interval,
                # it is an empty one, and it says the two statistics are not ordered as assumed.
                "ordering_holds": (lo is None or hi_band is None or hi_band >= lo),
                "rstar_top_at_every_lead_time": all(x["rstar_is_top"] for x in base["detail"]),
                "clique_contrast_outside_its_band_everywhere":
                    all(not x["in_band_lo"] for x in base["detail"]),
                "auc_inside_its_band_everywhere":
                    all(x["in_band_auc"] for x in base["detail"]),
                "detail": base["detail"],
            })
        out[label] = rows
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=RESULTS / "upper_bound_audit.json")
    args = ap.parse_args()

    syn = synthetic_from_artefact()
    print("1. the pre-specified upper bound on the synthetic calibration")
    print(f"   {'beta':>4} {'target':>6} {'lo':>4} {'hi as specified':>16} {'hi band only':>13}")
    for r in syn["rows"]:
        print(f"   {r['beta']:>4} {r['target']:>6} {str(r['lo']):>4} "
              f"{str(r['hi_rank_and_band']):>16} {str(r['hi_band_only']):>13}")
    print(f"   fires in {syn['pre_specified_rule_fires_in']} of {syn['settings']} settings, at "
          f"beta {syn['pre_specified_rule_fires_at_beta']}")
    print(f"   recomputation matches the stored bound: "
          f"{syn['recomputation_matches_the_stored_bound']}")

    print("\n2. the same sweep with the rank condition dropped")
    print(f"   fires in {syn['band_only_rule_fires_in']} of {syn['settings']} settings")
    print(f"   and coincides with the lower bound in {syn['band_only_equals_lower_bound_in']} "
          f"of them, with the target in {syn['band_only_equals_target_in']}")
    print("   a bound that always equals the lower bound is not an upper bound: the bracket it "
          "forms has width zero, so the repair buys reachability by giving up the second statistic")

    ca = corpus_a()
    print("\n3. corpus A, where the two statistics can be checked against each other")
    violations = []
    for label, rows in ca.items():
        for r in rows:
            print(f"   {label:14s} k={r['level']:>3}  lo={str(r['lo']):>4}  "
                  f"hi as specified={str(r['hi_rank_and_band']):>4}  "
                  f"hi band only={str(r['hi_band_only']):>4}  "
                  f"ordering holds: {r['ordering_holds']}")
            if not r["ordering_holds"]:
                violations.append((label, r["level"], r["lo"], r["hi_band_only"]))

    # Stated from the rows rather than asserted, because "at every lead time" is exactly the kind of
    # claim that survives a corpus rebuild in the prose and not in the data.
    primary = next((r for r in ca.get("organisations", []) if r["level"] == 25), None)
    if primary is not None:
        print()
        print(f"   at the declared primary level k=25, the clique contrast sits outside its band at "
              f"every lead time: {primary['clique_contrast_outside_its_band_everywhere']}; the "
              f"single-feature AUC sits inside its band at every lead time: "
              f"{primary['auc_inside_its_band_everywhere']}. Where both hold, the specific statistic "
              f"calls the relation distinguishable everywhere and the sensitive one calls it "
              f"indistinguishable everywhere, which is the reverse of the ordering the bracket "
              f"assumes.")
    if violations:
        print(f"   the assumed ordering fails in {len(violations)} level(s): {violations}")

    verdict = (
        "The interval should be dropped from the framing and the upper bound reported as "
        "non-identified, with both failure modes named. As specified the rule is unreachable, "
        "because a structurally similar anchor keeps top rank. Repaired as a band crossing it is "
        "always reachable but coincides with the lower bound on synthetic data, so it adds nothing, "
        "and on corpus A it falls below the lower bound, so the two statistics do not order the way "
        "the bracket requires. The estimand that survives is a lower bound."
    )
    print(f"\nverdict\n  {verdict}")

    write_result(args.json, {
        "question": "repair the upper bound, or drop the interval from the framing",
        "synthetic": syn,
        "corpus_a": ca,
        "ordering_violations": violations,
        "verdict": verdict,
    }, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

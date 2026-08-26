r"""Put the generator's homophily axis on a scale corpus A can be read on.

Two objections meet here. The first review asked how a reader is meant to know whether any real corpus
reaches the homophily strength at which identification collapses, since $h$ is a knob on a generator and
not a quantity anyone measures. The second asked whether "an exponent on latent similarity" is one
parametrisation carrying the paper's two most important results. Running the grid under a bounded
logistic kernel answered the second and sharpened the first: under that kernel nothing collapses inside
the swept range of $h$, which does **not** mean the collapse is a property of the power law. It means
$h$ is not comparable across kernels. A power law at $h = 4$ concentrates the edge weight far more than
a logistic kernel at $h = 4$ does, so the two axes are differently scaled and comparing thresholds on
them is meaningless.

The fix is to stop reporting the collapse against $h$ and report it against something a field corpus
also has. The choice is the **realised anchor clique contrast**: the strongest anchor's clique contrast
at level 1 on the never-event stratum, read at one period. It is a property of a corpus rather than of a
generator, it is what "the anchors carry the target relation's homophily" means when measured, and every
cell of the synthetic grid has one because it is the quantity the anchor band is built from.

**It has to be that statistic and not the more familiar one.** Table 7's 0.2448 for trade flows is a
matched *density* contrast, and the synthetic grid's band is built from a *clique* contrast; comparing
the two would be the units error Section 6.4 documents and mechanism (b)'s caption once committed.
Corpus A's anchor clique contrast at level 1 and one period is **0.0259**, read from the same artefact
that produces its horizon curve.

So this script reads, per kernel and per $h$, the realised anchor contrast the generator produced and
the estimators' behaviour at that setting, and reports the collapse threshold in units of anchor
contrast. The claim it is meant to support or refute is specific: if the three kernels collapse at
different values of $h$ but at similar anchor contrasts, then the collapse is a property of how
concentrated the similarity is and not of the functional form. If they collapse at different anchor
contrasts too, the functional form matters and the paper has to say so.

    python scripts/run_homophily_scale.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from scripts.run_synthetic_homophily import ESTIMATORS, one_cell  # noqa: E402

RESULTS = ROOT / "results"
# Read from corpus A's own horizon curve rather than typed in, so the reference cannot drift from the
# artefact and so it is guaranteed to be the same statistic the synthetic side reports: the clique
# contrast at level 1 on the never-event stratum. One period rather than zero because the risk set has no
# zero-lead-time row on either side -- a candidate that accedes at $t$ is already a member at $t$ and is
# therefore not at risk -- so the comparison is made where both sides exist.
LEAD = 1
CORPUS_A_CURVE = RESULTS / "u1_real_primary.json"


def corpus_a_reference() -> dict:
    """The strongest anchor's clique contrast at level 1 and lead time LEAD, from the artefact."""
    o = json.loads(CORPUS_A_CURVE.read_text(encoding="utf-8"))
    anchors = set(o["anchors"])
    rows = [r for r in o["curves"]
            if r["negative_stratum"] == "never_event" and r["level"] == 1
            and r["horizon"] == LEAD]
    per = {r["relation"]: round(float(r["clique_contrast"]), 4) for r in rows}
    best = max((v for k, v in per.items() if k in anchors), default=None)
    return {"statistic": "clique contrast at level 1, never-event stratum",
            "lead_time": LEAD, "per_relation": per, "anchors": sorted(anchors),
            "strongest_anchor": best,
            "r_star": per.get(o["rstar"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=RESULTS / "homophily_scale.json")
    ap.add_argument("--betas", type=int, nargs="+", default=[0, 1, 2, 3, 4, 5])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    args = ap.parse_args()

    forms = ["power", "logistic", "block"]
    hs = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0]

    ref = corpus_a_reference()
    print("the generator's homophily axis, in units corpus A also has\n")
    print(f"  reference statistic: {ref['statistic']}, lead time {ref['lead_time']}")
    print(f"  corpus A per relation: "
          + ", ".join(f"{k} {v}" for k, v in ref["per_relation"].items()))
    print(f"  corpus A strongest anchor: **{ref['strongest_anchor']}**, against its target relation "
          f"at {ref['r_star']}\n")

    cells = []
    for form in forms:
        for h in hs:
            for seed in args.seeds:
                for beta in args.betas:
                    c = one_cell(beta, h, True, {"seed": seed, "homophily_form": form})
                    cells.append({
                        "form": form, "homophily": h, "seed": seed, "beta": beta,
                        "target": c["target"],
                        "anchor_contrast": c["best_field_anchor_contrast"].get(LEAD),
                        "rstar_contrast": c["pooled_contrast"].get(LEAD),
                        "estimates": {n: c["estimators"][n]["reported_as"] for n in ESTIMATORS},
                        "censored": {n: c["estimators"][n]["censored"] for n in ESTIMATORS},
                    })

    summary = {}
    for form in forms:
        summary[form] = {}
        for h in hs:
            g = [c for c in cells if c["form"] == form and c["homophily"] == h]
            ac = [c["anchor_contrast"] for c in g if c["anchor_contrast"] is not None]
            assert ac, f"no anchor contrast at lead time {LEAD} for {form} h={h}"
            row = {"anchor_contrast_mean": round(float(np.mean(ac)), 4),
                   "anchor_contrast_min": round(float(np.min(ac)), 4),
                   "anchor_contrast_max": round(float(np.max(ac)), 4),
                   "lead_time": LEAD, "cells": len(g)}
            for n in ESTIMATORS:
                err = [c["estimates"][n] - c["target"] for c in g]
                row[n] = {"mean_error": round(float(np.mean(err)), 3),
                          "exact": int(sum(1 for e in err if e == 0)),
                          "censored": int(sum(c["censored"][n] for c in g))}
            summary[form][f"h={h}"] = row
            print(f"  {form:9s} h={h:<4} anchor contrast {row['anchor_contrast_mean']:.4f}   "
                  + "  ".join(f"{n.split('_')[0][:5]}={row[n]['mean_error']:+.2f}"
                              for n in ("delta_star_lo", "residual_rule", "unbanded_rule")))

    # The threshold, in anchor contrast rather than in h: the smallest realised anchor contrast at
    # which an estimator's mean error leaves zero.
    thresholds = {}
    for form in forms:
        thresholds[form] = {}
        for n in ESTIMATORS:
            hit = None
            for h in hs:
                r = summary[form][f"h={h}"]
                if abs(r[n]["mean_error"]) > 0.5:
                    hit = r["anchor_contrast_mean"]
                    break
            thresholds[form][n] = hit
    print(f"\n  collapse threshold in anchor contrast at lead time {LEAD}, by kernel")
    for form in forms:
        print(f"    {form:9s} " + "  ".join(
            f"{n.split('_')[0][:5]}="
            + ("never" if thresholds[form][n] is None else f"{thresholds[form][n]:.4f}")
            for n in ("delta_star_lo", "residual_rule", "unbanded_rule")))
    a = ref["strongest_anchor"]
    print(f"\n  corpus A's strongest anchor sits at {a} on this scale.")
    for form in forms:
        t = thresholds[form]["unbanded_rule"]
        reach = max(summary[form][f"h={h}"]["anchor_contrast_mean"] for h in hs)
        if t is None:
            print(f"    {form:9s} never collapses inside the swept range, and never exceeds "
                  f"{reach:.4f}, which is below every threshold reached by the others: the kernel does "
                  f"not get to the concentration rather than resisting it")
        else:
            rel = a / t
            print(f"    {form:9s} collapses at {t:.4f}, which corpus A exceeds by a factor of "
                  f"{rel:.1f}")

    payload = {
        "question": ("does the identification collapse happen at a similar realised anchor contrast "
                     "under three different homophily kernels, which would make it a property of how "
                     "concentrated the similarity is rather than of the functional form"),
        "why_not_h": ("h is a kernel parameter and the kernels scale it differently, so a threshold in "
                      "h is not comparable across them; the realised anchor contrast is a property of "
                      "the corpus and corpus A has one"),
        "lead_time": LEAD,
        "corpus_a_reference": ref,
        "grid": {"forms": forms, "homophily": hs, "betas": args.betas, "seeds": args.seeds},
        "cells": cells,
        "summary": summary,
        "collapse_threshold_in_anchor_contrast": thresholds,
    }
    write_result(args.json, payload, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

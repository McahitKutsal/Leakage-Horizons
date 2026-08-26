r"""The figures the manuscript asserts that no other script computes.

A coverage audit of `check_paper.py` found it registered 43 of the 293 distinct numeric tokens in the
manuscript, and a search for tokens with no match in any results file left 32, of which fourteen were
real claims computed ad hoc during drafting and never stored. Every one of them verified when
recomputed, but a verified number that lives only in prose is unauditable from the next edit onward,
which is the failure D-35 exists to prevent (D-45).

This script computes exactly those figures so that `check_paper.py` can register them:

* the two coverage regimes' target relation density and organisations per year, which mechanism (g)
  turns on;
* the left truncation audit, which Section 8 quotes;
* the duplicate membership rows the corpus fix removed, recomputed from the raw source since the
  corrected corpus can no longer exhibit them, and reported under **both** counting conventions
  because the manuscript previously stated the wrong one;
* the share of coded gaps at two periods or more;
* the derived aggregates the ladder and architecture tables imply but do not store as scalars.

    python scripts/paper_support.py
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

from penumbra.ledger import ATOP_DIR, WINDOW_END, WINDOW_START  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402

LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"
RESULTS = ROOT / "results"
REGIMES = {"early": (1948, 1963), "primary": (1965, 2014)}
R_STAR = "igo_comembership"


def _density(d: pd.DataFrame) -> float:
    n = len(np.unique(np.r_[d.cow_i.to_numpy(), d.cow_j.to_numpy()]))
    return len(d) / (n * (n - 1) / 2) if n > 1 else float("nan")


def regime_saturation() -> dict:
    """Target relation density and organisations per year, per coverage regime.

    Mechanism (g) is that shortcut reliance is a model by regime interaction rather than a model
    attribute, and it rests on these four numbers.
    """
    cm = pd.read_parquet(GRAPH / f"edges_{R_STAR}.parquet")
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    orgs = mem[(mem.status == 1) & mem.entity_id.str.startswith("igo:")]
    out = {}
    for name, (lo, hi) in REGIMES.items():
        sub = cm[cm.year.between(lo, hi)]
        per = sub.groupby("year").apply(_density, include_groups=False)
        out[name] = {
            "window": [lo, hi],
            "mean_density": round(float(per.mean()), 4),
            "min_density": round(float(per.min()), 4),
            "organisations_per_year": int(round(float(
                orgs[orgs.year.between(lo, hi)].groupby("year").entity_id.nunique().mean()))),
        }
    return out


def left_truncation() -> dict:
    """How many groups in the termination panel predate the analysis window, and their exposure."""
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    lo, hi = REGIMES["primary"]
    e = ent.assign(origin_used=np.maximum(ent.origin.astype(int), lo))
    panel = e[e.exit_year.astype(int) >= e.origin_used].copy()
    panel["years"] = np.minimum(panel.exit_year.astype(int), hi) - panel.origin_used + 1
    pre = panel.founded.astype("Int64") < lo
    ages = (lo - panel.loc[pre, "founded"].dropna().astype(int))
    return {
        "entities_in_panel": int(len(panel)),
        "predating_the_window": int(pre.sum()),
        "median_true_age_at_window_start": int(ages.median()),
        "max_true_age_at_window_start": int(ages.max()),
        "share_of_group_years": round(float(panel.loc[pre, "years"].sum() / panel.years.sum()), 4),
    }


def duplicate_membership_rows() -> dict:
    """Recomputed from the raw source: the corrected corpus cannot exhibit these.

    Reported under both conventions because the manuscript stated the wrong one. `redundant_rows` is
    the excess, what `duplicated()` counts with the first occurrence kept. `rows_in_duplicate_pairs`
    counts every row involved, which is twice as many when each key appears exactly twice, and reading
    the second as the excess doubles it.
    """
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    ids = set(ent.loc[ent.entity_type == "alliance", "source_id"].astype(int))
    m = pd.read_csv(ATOP_DIR / "atop5_1m.csv", low_memory=False)
    m = m[m.atopid.isin(ids)].copy()
    yi = pd.to_numeric(m.yrent, errors="coerce").replace(0, np.nan)
    yo = pd.to_numeric(m.yrexit, errors="coerce").replace(0, np.nan).fillna(WINDOW_END)
    m = m.assign(yi=yi, yo=yo).dropna(subset=["yi"])

    rows = []
    for r in m.itertuples():
        for y in range(max(int(r.yi), WINDOW_START), min(int(r.yo), WINDOW_END) + 1):
            rows.append((int(r.atopid), int(r.member), y))
    d = pd.DataFrame(rows, columns=["atopid", "member", "year"])
    sz = d.groupby(["atopid", "year"]).agg(rows=("member", "size"), uniq=("member", "nunique"))
    return {
        "redundant_rows": int(d.duplicated().sum()),
        "rows_in_duplicate_pairs": int(d.duplicated(keep=False).sum()),
        "distinct_duplicated_keys": int(d.duplicated().sum()),
        "inflated_group_years": int((sz.rows != sz.uniq).sum()),
        "max_inflation_factor": round(float((sz.rows / sz.uniq).max()), 2),
    }


def coded_gap_share() -> dict:
    d = json.loads((RESULTS / "desta_delta_star.json").read_text(encoding="utf-8"))
    dist = {int(k): v for k, v in d["event_gaps"]["distribution"].items()}
    tot = sum(dist.values())
    return {"n_events": tot,
            "share_gap_at_least_1": round(sum(v for k, v in dist.items() if k >= 1) / tot, 4),
            "share_gap_at_least_2": round(sum(v for k, v in dist.items() if k >= 2) / tot, 4)}


def derived_aggregates() -> dict:
    """Means the ladder and architecture tables imply but store only as per cell rows."""
    out = {}
    t1 = json.loads((RESULTS / "t1_ladder.json").read_text(encoding="utf-8"))
    r = pd.DataFrame(t1["rows"])
    for field, tag in (("auc", "pooled"), ("auc_within_coalition", "within")):
        piv = r.pivot_table(index=["origin", "horizon"], columns="rung", values=field)
        out[f"rung3_minus_rung2_{tag}"] = round(float((piv[3] - piv[2]).mean()), 4)
        out[f"rung2_minus_rung1_{tag}"] = round(float((piv[2] - piv[1]).mean()), 4)
    el = json.loads((RESULTS / "t1_ladder_eligibility.json").read_text(encoding="utf-8"))
    re_ = pd.DataFrame(el["rows"]).pivot_table(index=["origin", "horizon"], columns="rung",
                                               values="auc_within_coalition")
    out["rung3_minus_rung2_within_eligibility_clock"] = round(float((re_[3] - re_[2]).mean()), 4)

    p7 = pd.DataFrame(json.loads((RESULTS / "p7_s4.json").read_text(encoding="utf-8"))["rows"])
    per_seed = p7.groupby(["rung", "seed"]).auc.mean()
    for rung in sorted(p7.rung.unique()):
        s = per_seed.loc[rung]
        out[f"rung{rung}_mean_auc"] = round(float(s.mean()), 4)
        out[f"rung{rung}_sd_over_seeds"] = round(float(s.std(ddof=1)), 4)
    for f, tag in (("p7_ctrl_w96_s4.json", "mlp_w96"), ("p7_ctrl_w128_s4.json", "mlp_w128")):
        c = pd.DataFrame(json.loads((RESULTS / f).read_text(encoding="utf-8"))["rows"])
        cs = c.groupby("seed").auc.mean()
        out[f"{tag}_mean_auc"] = round(float(cs.mean()), 4)
        out[f"{tag}_sd_over_seeds"] = round(float(cs.std(ddof=1)), 4)
    out["rung6_minus_mlp_w96"] = round(out["rung6_mean_auc"] - out["mlp_w96_mean_auc"], 4)
    out["rung7_minus_mlp_w128"] = round(out["rung7_mean_auc"] - out["mlp_w128_mean_auc"], 4)
    out["width_64_to_96"] = round(out["mlp_w96_mean_auc"] - out["rung4_mean_auc"], 4)
    out["width_64_to_128"] = round(out["mlp_w128_mean_auc"] - out["rung4_mean_auc"], 4)
    return out


def architecture_at_ten_seeds() -> dict:
    r"""The same comparison at ten seeds, and the margin's own standard error, computed here.

    Section 9's fourth question is how much a number moves when nothing substantive changes, and the
    architectural margin is the example it uses: two seeds put it at 0.0009 and four at 0.0121. Four
    was where the manuscript stopped, which is the same mistake one step further out, so the whole
    comparison is rerun at ten and reported beside the four-seed version rather than replacing it. One
    verdict changes sign in significance, which is why both are kept.

    The standard error is the pooled standard error of a difference of two means over $n$ seeds each,
    $\sqrt{s_1^2/n + s_2^2/n}$, so the sigma multiples the manuscript quotes follow from this table and
    one line of arithmetic. The cell counts are the paired origin-by-horizon-by-seed comparisons, which
    is what says whether a mean margin is carried by a few cells or by most of them.
    """
    out = {}
    for tag, main_f, w96, w128 in (("four_seeds", "p7_s4.json", "p7_ctrl_w96_s4.json",
                                    "p7_ctrl_w128_s4.json"),
                                   ("ten_seeds", "p7_s10.json", "p7_ctrl_w96_s10.json",
                                    "p7_ctrl_w128_s10.json")):
        if not (RESULTS / main_f).exists():
            continue
        m = pd.DataFrame(json.loads((RESULTS / main_f).read_text(encoding="utf-8"))["rows"])
        blk = {"n_seeds": int(m.seed.nunique())}
        per = m.groupby(["rung", "seed"]).auc.mean()
        for rung in sorted(m.rung.unique()):
            sv = per.loc[rung]
            blk[f"rung{rung}_mean_auc"] = round(float(sv.mean()), 4)
            blk[f"rung{rung}_sd_over_seeds"] = round(float(sv.std(ddof=1)), 4)
        ctrls = {}
        for f, name in ((w96, "mlp_w96"), (w128, "mlp_w128")):
            c = pd.DataFrame(json.loads((RESULTS / f).read_text(encoding="utf-8"))["rows"])
            cs = c.groupby("seed").auc.mean()
            ctrls[name] = (c, cs)
            blk[f"{name}_mean_auc"] = round(float(cs.mean()), 4)
            blk[f"{name}_sd_over_seeds"] = round(float(cs.std(ddof=1)), 4)

        def margin(t_rung, ctrl_name, ctrl_frame):
            t = per.loc[t_rung]
            cs = ctrls[ctrl_name][1]
            n = min(len(t), len(cs))
            marg = float(t.mean() - cs.mean())
            se = float(np.sqrt(t.var(ddof=1) / len(t) + cs.var(ddof=1) / len(cs)))
            keys = ["origin", "horizon", "seed"]
            a = m[m.rung == t_rung].set_index(keys).auc
            b = ctrl_frame[ctrl_frame.rung == 4].set_index(keys).auc
            common = a.index.intersection(b.index)
            d = (a.loc[common] - b.loc[common])
            return {"margin": round(marg, 4), "standard_error": round(se, 5),
                    "sigma": round(marg / se, 2) if se else None,
                    "cells": int(len(d)), "cells_won": int((d > 0).sum()),
                    "seeds": int(n)}

        blk["width_64_to_96"] = round(blk["mlp_w96_mean_auc"] - blk["rung4_mean_auc"], 4)
        blk["width_64_to_128"] = round(blk["mlp_w128_mean_auc"] - blk["rung4_mean_auc"], 4)
        blk["relation_specific_vs_w96"] = margin(6, "mlp_w96", ctrls["mlp_w96"][0])
        blk["temporal_vs_w128"] = margin(7, "mlp_w128", ctrls["mlp_w128"][0])
        # The homogeneous encoder's control is the width-64 graph-free rung in the same file.
        t, c = per.loc[5], per.loc[4]
        marg = float(t.mean() - c.mean())
        se = float(np.sqrt(t.var(ddof=1) / len(t) + c.var(ddof=1) / len(c)))
        keys = ["origin", "horizon", "seed"]
        a = m[m.rung == 5].set_index(keys).auc
        b = m[m.rung == 4].set_index(keys).auc
        common = a.index.intersection(b.index)
        d = a.loc[common] - b.loc[common]
        blk["homogeneous_vs_w64"] = {"margin": round(marg, 4), "standard_error": round(se, 5),
                                     "sigma": round(marg / se, 2) if se else None,
                                     "cells": int(len(d)), "cells_won": int((d > 0).sum()),
                                     "seeds": int(min(len(t), len(c)))}
        p7 = json.loads((RESULTS / main_f).read_text(encoding="utf-8"))["p7"]
        blk["gain_by_lead_time_over_width_64"] = {
            k: {int(h): round(float(v), 4) for h, v in b["by_horizon"].items()}
            for k, b in p7.items()}
        out[tag] = blk
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=RESULTS / "paper_support.json")
    args = ap.parse_args()

    payload = {
        "regime_saturation": regime_saturation(),
        "left_truncation": left_truncation(),
        "duplicate_membership_rows": duplicate_membership_rows(),
        "coded_gap_share": coded_gap_share(),
        "derived_aggregates": derived_aggregates(),
        "architecture_by_seed_count": architecture_at_ten_seeds(),
    }
    for section, body in payload.items():
        print(f"\n{section}")
        print("  " + json.dumps(body, indent=2).replace("\n", "\n  "))
    write_result(args.json, payload, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

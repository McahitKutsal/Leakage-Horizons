r"""The clique contrast stratified by group size, on both corpora, with the level declared.

Figure 6 of the manuscript overlays the two domains, so the two series have to come from one script or
the overlay is not a comparison. Writing it found a specification gap in how V3's finding had been
summarised.

**The size dependence reverses with the level, so the level cannot be dropped.** At the declared primary
level $k = 25$ the contrast measured here runs 0.5833, 0.3617, 0.3391, 0.2437, 0.0521 and **0.0000**,
with the positive clique rate itself at 0.0000 above eighty. At $k = 1$ the same statistic on the same
corpus behaves the opposite way, rising from 0.0625 to **0.4778**, because co-membership at $k = 1$ has
density 0.9954 and both classes are near-cliques, so the contrast comes from the negative rate falling
with size rather than from the positive rate holding. A summary that omits the level is therefore false
at the level a reader would assume.

**This is a companion to V3, not a reproduction of it.** V3 states its conditions in full, "clique rate
at k = 25 by group size, horizon 3, matched panel"; the level was dropped when SYNTHESIS and the
manuscript summarised it. Here the cut differs in two declared ways: the contrast is taken at **zero lead
time**, the period the event falls in, because corpus B has no time axis and a cross-domain comparison has
to fix the lead time, and the size bins are finer. The shape is the same and the levels are not, which is
what a different cut should produce.

The two corpora are compared at the level each relation is informative at, and that difference is
reported rather than hidden: corpus A at $k = 25$ because its target relation is weighted and saturated
at $k = 1$, corpus B at $k = 1$ because its channels are binary. A single level across both would
compare a discriminating statistic against a degenerate one.

    python scripts/clique_by_size.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from penumbra.umbra import HorizonAudit  # noqa: E402
from vendor.cliquebait.diagnostics import LeakageAudit  # noqa: E402

LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"
WS2 = ROOT.parent / "CLIQUEBAIT" / "data" / "ws2"

BINS = [1, 3, 5, 10, 20, 80, 10_000]
REGIME = (1965, 2014)
R_STAR_A = "igo_comembership"
A_LEVELS = (1, 25)          # 1 to show the reversal, 25 because D-13 declares it primary
N_NEG = 2
SEED = 0


def _bin_table(rows, label_col="label") -> dict:
    d = pd.DataFrame(rows, columns=["n", label_col, "clique"])
    d["bin"] = pd.cut(d.n, BINS)
    out = {}
    for b, s in d.groupby("bin", observed=True):
        p, q = s[s[label_col] == 1], s[s[label_col] == 0]
        if not len(p) or not len(q):
            continue
        out[str(b)] = {
            "n_pos": int(len(p)), "n_neg": int(len(q)),
            "clique_rate_pos": round(float(p.clique.mean()), 4),
            "clique_rate_neg": round(float(q.clique.mean()), 4),
            "clique_contrast": round(float(p.clique.mean() - q.clique.mean()), 4),
        }
    return out


def corpus_a(levels=A_LEVELS) -> dict:
    """Matched negatives from the same (entity, year), for the reason V0 records."""
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    ev = pd.read_parquet(LEDGER / "events.parquet")
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    ev = ev.merge(ent[["entity_id", "entity_type"]], on="entity_id", how="left")
    cm = pd.read_parquet(GRAPH / f"edges_{R_STAR_A}.parquet").assign(relation=R_STAR_A)
    audit = HorizonAudit(cm, mem, ev)

    all_states = np.sort(mem.ccode.unique())
    ever = mem[mem.status == 1].groupby("entity_id").ccode.apply(set).to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()
             & ev.t_R.between(*REGIME)]

    out = {}
    for k in levels:
        rng = np.random.default_rng(SEED)
        rows = []
        for r in acc.itertuples():
            cc, t, eid = int(r.ccode), int(r.t_R), r.entity_id
            ms = audit._members.get((eid, t))
            if ms is None or len(ms) < 2:
                continue
            never = np.setdiff1d(all_states, np.fromiter(ever.get(eid, set()), np.int64))
            if never.size == 0:
                continue
            n = len(ms)
            negs = rng.choice(never, size=min(N_NEG, never.size), replace=False)
            for who, lab in [(cc, 1)] + [(int(x), 0) for x in negs]:
                grp = np.append(ms[ms != who], who)
                phi = audit.phi(grp, t, R_STAR_A, k)
                if not np.isnan(phi):
                    rows.append((n, lab, float(phi >= 1.0)))
        out[f"k={k}"] = _bin_table(rows)
    return out


def corpus_b(threshold: int = 400, relation: str = "database", negatives: str = "random") -> dict:
    g = pd.read_parquet(WS2 / f"groups_thr{threshold}.parquet")
    e = pd.read_parquet(WS2 / f"edges_thr{threshold}.parquet")
    phi = LeakageAudit(e, g).densities()
    col = f"phi_{relation}"
    d = phi[[col, "label", "size", "neg_type"]].rename(columns={col: "phi"}).dropna(subset=["phi"])
    d = d[(d.label == 1) | (d.neg_type == negatives)]
    rows = [(int(r.size), int(r.label), float(r.phi >= 1.0)) for r in d.itertuples()]
    return {"k=1": _bin_table(rows)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "clique_by_size.json")
    args = ap.parse_args()

    a = corpus_a()
    b = corpus_b()

    for name, tab in (("corpus A, co-membership", a), ("corpus B, curated-register channel", b)):
        for lvl, t in tab.items():
            print(f"\n{name}, level {lvl}")
            print(f"  {'members':14s} {'n_pos':>6s} {'clq_pos':>8s} {'clq_neg':>8s} {'contrast':>9s}")
            for bn, v in t.items():
                print(f"  {bn:14s} {v['n_pos']:>6d} {v['clique_rate_pos']:>8.4f} "
                      f"{v['clique_rate_neg']:>8.4f} {v['clique_contrast']:>9.4f}")

    below = [v["clique_contrast"] for bn, v in a["k=25"].items()
             if bn in ("(1, 3]", "(3, 5]", "(5, 10]", "(10, 20]")]
    print(f"\ncorpus A at k=25, range below twenty members: "
          f"{min(below):.4f} to {max(below):.4f}")
    print("  V3's 0.20 to 0.25 is for horizon 3 on corpus v1 with coarser bins; this is zero lead")
    print("  time on v4 with finer bins, so the shape matches and the levels need not")
    print(f"  above eighty: contrast {a['k=25']['(80, 10000]']['clique_contrast']:.4f}, "
          f"positive clique rate {a['k=25']['(80, 10000]']['clique_rate_pos']:.4f}")
    print(f"\nat k=1 the same statistic rises with size instead: "
          f"{a['k=1']['(1, 3]']['clique_contrast']:.4f} to "
          f"{a['k=1']['(80, 10000]']['clique_contrast']:.4f}")

    write_result(args.json, {
        "bins": [str(b) for b in pd.IntervalIndex(pd.cut(pd.Series(BINS[:-1]), BINS).cat.categories)],
        "regime": list(REGIME),
        "declared": {"corpus_a_relation": R_STAR_A, "corpus_a_levels": list(A_LEVELS),
                     "corpus_b_relation": "database", "corpus_b_level": 1,
                     "why_levels_differ": ("corpus A's target relation is weighted and saturated at "
                                           "k=1, corpus B's channels are binary; comparing at one "
                                           "level would put a discriminating statistic against a "
                                           "degenerate one")},
        "corpus_a": a, "corpus_b": b,
    }, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

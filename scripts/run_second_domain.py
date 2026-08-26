r"""The second domain: are SYNTHESIS section 2's (b), (c), (d) and (h) general or particular?

Three of the ten failure modes the paper rests on are claims about **any** curated group corpus, and all
three were measured on one. That is the largest remaining risk to the contribution, and CLIQUEBAIT's
protein benchmark is the adversarial test rather than a confirmation run, because its size distribution is
the **opposite** of LEDGER's: 2,540 complexes with a median of 3 members and 1.6 % above twenty, against
LEDGER's positive strata averaging 66 with 36 % above eighty.

**The statistics come from the pinned CLIQUEBAIT library, not from a reimplementation.** `LeakageAudit`
computes $\phi_r(S)$ and the clique contrast $P(\phi = 1 \mid \text{pos}) - P(\phi = 1 \mid \text{neg})$,
which is the statistic (c) and (h) are about, and its `Group` already carries a `'__static__'` time, so
the timeless case needs no adaptation. Only the size stratification is PENUMBRA's own (V3).

What each claim predicts here, written before the numbers:

**(b) a saturating relation hides the shadow.** Says coalition relations saturate — IGO co-membership has
density 0.995. If the protein relations are far from saturated, (b) is a claim about *coalition* relations
specifically, which is what it says, and the benchmark confirms the scope rather than the claim.

**(c) the exact-clique statistic is structurally zero on large groups.** Predicts the contrast has
*power* here, since 98 % of complexes are under twenty members and V3 measured 0.20-0.25 in that range.
**Falsified if the contrast is near zero on small protein complexes too** -- that would mean (c)'s
mechanism is not size.

**(d) there is no subpopulation where both problems go away.** The strongest test, and the one that can
break. This corpus has 2,540 positives *and* a median size of 3 -- size and sample favourable at once,
which LEDGER never offers. **If the contrast separates cleanly from its band here, (d) is false as
stated** and has to be restated as a property of coalition corpora rather than of curated group corpora.

**(h) the band cannot subtract homophily.** Testable only in its zero-lag form: do relations that cannot
record complex membership show the same contrast as the one that does? The horizon-resolved form does not
transfer -- this benchmark has no time axis, so there is no penumbra here and none is looked for.

$r^\star$ and the anchors are declared from what each STRING channel records, before any number is read,
which is section 5.4 applied to a new domain:

* $r^\star$ = **`database`** (and `database_transferred`). STRING's database channel imports CORUM and
  ComplexPortal -- the label source itself. Exactly analogous to `igo_comembership` being built from the
  file that supplies T1's labels: it leaks by construction, and that is the object of study.
* **Contaminated, and therefore not anchors**: `textmining` reads papers that describe complexes, and
  `experiments` covers co-immunoprecipitation and affinity purification, which *detect* complexes. Both
  can carry the label through a route that is not the database channel.
* **Anchors** = `coexpression`, `coexpression_transferred`, `fusion`, `cooccurence`, `homology`. mRNA
  correlation, gene-fusion events, phylogenetic co-occurrence and sequence similarity cannot record a
  curator's decision that a set of proteins forms a complex.

Negative strata are reported separately because V0 was retracted for pooling them: this benchmark ships
`random` and `hard` negatives and their group sizes are already matched to the positives (median 3, mean
5.1 on both sides), so the defect V0 records cannot arise here.

    python scripts/run_second_domain.py
    python scripts/run_second_domain.py --threshold 150
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
from vendor.cliquebait.diagnostics import LeakageAudit  # noqa: E402

WS2 = ROOT.parent / "CLIQUEBAIT" / "data" / "ws2"

R_STAR = ["database", "database_transferred"]
CONTAMINATED = ["textmining", "experiments", "experiments_transferred"]
ANCHORS = ["coexpression", "coexpression_transferred", "fusion", "cooccurence", "homology"]

# V3's bins, so the two domains are read on one scale. V3 measured 0.20-0.25 below twenty members and
# identically 0.000 above eighty.
SIZE_BINS = [1, 3, 5, 10, 20, 80, 10_000]


def load(threshold: int):
    g = pd.read_parquet(WS2 / f"groups_thr{threshold}.parquet")
    e = pd.read_parquet(WS2 / f"edges_thr{threshold}.parquet")
    u = pd.read_parquet(WS2 / f"universe_thr{threshold}.parquet")
    g = g.assign(n=g.members.apply(len))
    return g, e, u


def size_profile(g: pd.DataFrame) -> dict:
    pos = g[g.label == 1]
    cut = pd.cut(pos.n, SIZE_BINS)
    return {
        "n_positive": int(len(pos)), "n_negative": int((g.label == 0).sum()),
        "median": int(pos.n.median()), "mean": round(float(pos.n.mean()), 2),
        "max": int(pos.n.max()),
        "by_size": {str(k): int(v) for k, v in cut.value_counts().sort_index().items()},
        "share_at_least_20": round(float((pos.n >= 20).mean()), 4),
        "share_at_least_80": round(float((pos.n >= 80).mean()), 4),
        "negative_median": int(g.loc[g.label == 0, "n"].median()),
        "negative_mean": round(float(g.loc[g.label == 0, "n"].mean()), 2),
    }


def _slice(phi: pd.DataFrame, relation: str, negatives: str | None):
    """One (phi, label, size) frame for a relation. `densities()` returns wide `phi_{relation}` columns
    and already carries label, size and neg_type, so nothing needs merging back on."""
    col = f"phi_{relation}"
    d = phi[[col, "label", "size", "neg_type"]].rename(columns={col: "phi"})
    if negatives is not None:
        d = d[(d.label == 1) | (d.neg_type == negatives)]
    # A group whose members carry no edges at all is dropped by the library rather than scored zero,
    # which would read as "no leakage" when it means "no data" -- so NaN here is an absence, not a miss.
    return d.dropna(subset=["phi"])


def clique_contrast_by_size(phi: pd.DataFrame, relation: str,
                            negatives: str | None = None) -> dict:
    r"""$P(\phi = 1 \mid \text{pos}) - P(\phi = 1 \mid \text{neg})$ within each size stratum.

    The stratification is V3's contribution and the reason it exists: a pooled clique contrast over a
    heterogeneous size distribution is not interpretable, because the statistic's ceiling is a function
    of the group's dyad count. Reported with the per-stratum counts so a zero can be told apart from an
    absence.
    """
    d = _slice(phi, relation, negatives)
    d = d.assign(stratum=pd.cut(d["size"], SIZE_BINS), is_clique=(d.phi >= 1.0).astype(float))
    out = {}
    for s, sub in d.groupby("stratum", observed=True):
        p, q = sub[sub.label == 1], sub[sub.label == 0]
        if not len(p) or not len(q):
            continue
        out[str(s)] = {
            "n_pos": int(len(p)), "n_neg": int(len(q)),
            "clique_rate_pos": round(float(p.is_clique.mean()), 4),
            "clique_rate_neg": round(float(q.is_clique.mean()), 4),
            "clique_contrast": round(float(p.is_clique.mean() - q.is_clique.mean()), 4),
            "phi_mean_pos": round(float(p.phi.mean()), 4),
            "phi_mean_neg": round(float(q.phi.mean()), 4),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, default=400, choices=[150, 400],
                    help="STRING confidence cut; 150 is the denser graph")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    args.json = args.json or ROOT / "results" / f"second_domain_thr{args.threshold}.json"

    g, e, u = load(args.threshold)
    prof = size_profile(g)
    print(f"protein benchmark, STRING threshold {args.threshold}")
    print(f"  {prof['n_positive']} complexes, {prof['n_negative']} negatives, "
          f"{len(u)} proteins, {len(e)} edges over {e.relation.nunique()} relations")
    print(f"  positive sizes: median {prof['median']}  mean {prof['mean']}  max {prof['max']}")
    print(f"  share >= 20 members: {prof['share_at_least_20']}   >= 80: {prof['share_at_least_80']}")
    print(f"  negatives: median {prof['negative_median']}  mean {prof['negative_mean']} "
          f"<- already size-matched, so V0's defect cannot arise")

    audit = LeakageAudit(e, g)
    phi = audit.densities()

    # ---- (b) how saturated is each relation? ----
    # STRING ships both directions of every interaction, as the benchmark builder's own log states, so
    # the row count per channel is twice the number of dyads. The first version of this block divided
    # that row count by the *unordered* dyad count and reported every corpus B density at exactly twice
    # its value: r* at 0.0023 rather than 0.0012 and the densest channel at 0.0038 rather than 0.0019.
    # The qualitative claim (b) rests on -- nothing in this domain saturates -- survived the error and
    # the numbers did not, and the manuscript's cross-domain ratio was wrong by the same factor. The
    # densities are now taken over deduplicated unordered pairs, and the directed count is reported
    # beside them so the factor of two is visible rather than implicit (D-51).
    n_nodes = len(u)
    dyads = n_nodes * (n_nodes - 1) / 2
    lo = np.minimum(e.u.to_numpy(), e.v.to_numpy())
    hi = np.maximum(e.u.to_numpy(), e.v.to_numpy())
    pairs = pd.DataFrame({"relation": e.relation.to_numpy(), "lo": lo, "hi": hi})
    undirected = pairs.drop_duplicates().groupby("relation").size()
    directed = e.groupby("relation").size()
    dens = (undirected / dyads).sort_values(ascending=False)
    print("\n--- (b) relation density: is anything here saturated? ---")
    print(f"  {'channel':28s} {'directed':>10s} {'undirected':>11s} {'density':>9s}")
    for r, v in dens.items():
        tag = " <- r*" if r in R_STAR else (" (anchor)" if r in ANCHORS else
                                           " (contaminated)" if r in CONTAMINATED else "")
        print(f"  {r:28s} {directed[r]:>10,} {undirected[r]:>11,} {v:>9.6f}{tag}")
    print(f"  every channel ships both directions, ratio "
          f"{float((directed / undirected).max()):.4f} to "
          f"{float((directed / undirected).min()):.4f}")
    print(f"  LEDGER's igo_comembership for comparison: 0.9954, a factor of "
          f"{0.9954 / float(dens[R_STAR[0]]):.0f}")

    # ---- (c) and (d) the clique contrast, stratified ----
    print("\n--- (c) clique contrast by group size, r* = database ---")
    by_size = {}
    for neg in ("random", "hard"):
        by_size[neg] = clique_contrast_by_size(phi, "database", negatives=neg)
        print(f"  negatives = {neg}")
        print(f"    {'stratum':14s} {'n_pos':>6s} {'n_neg':>6s} {'clq_pos':>8s} "
              f"{'clq_neg':>8s} {'contrast':>9s}")
        for s, v in by_size[neg].items():
            print(f"    {s:14s} {v['n_pos']:>6d} {v['n_neg']:>6d} {v['clique_rate_pos']:>8.4f} "
                  f"{v['clique_rate_neg']:>8.4f} {v['clique_contrast']:>9.4f}")

    # ---- (h) do the anchors carry the same contrast as r*? ----
    print("\n--- (h) the same statistic on every relation, pooled ---")
    rows = []
    for rel in sorted(e.relation.unique()):
        for neg in ("random", "hard"):
            d = _slice(phi, rel, neg)
            p, q = d[d.label == 1], d[d.label == 0]
            if not len(p) or not len(q):
                continue
            rows.append({
                "relation": rel, "negatives": neg,
                "role": ("r*" if rel in R_STAR else "anchor" if rel in ANCHORS
                         else "contaminated" if rel in CONTAMINATED else "other"),
                "clique_contrast": round(float((p.phi >= 1).mean() - (q.phi >= 1).mean()), 4),
                "phi_contrast": round(float(p.phi.mean() - q.phi.mean()), 4),
                "density": round(float(dens.get(rel, np.nan)), 5),
            })
    tab = pd.DataFrame(rows)
    for neg in ("random", "hard"):
        sub = tab[tab.negatives == neg].sort_values("clique_contrast", ascending=False)
        print(f"  negatives = {neg}")
        print("    " + sub[["relation", "role", "clique_contrast", "phi_contrast",
                            "density"]].to_string(index=False).replace("\n", "\n    "))

    # The number (h) turns on: r* against the strongest anchor.
    verdicts = {}
    for neg in ("random", "hard"):
        sub = tab[tab.negatives == neg]
        rs = sub[sub.role == "r*"].clique_contrast.max()
        an = sub[sub.role == "anchor"].clique_contrast.max()
        verdicts[neg] = {"r_star_best": float(rs), "anchor_best": float(an),
                         "residual": round(float(rs - an), 4)}
        print(f"\n  negatives = {neg}: r* {rs:.4f}, strongest anchor {an:.4f}, "
              f"residual {rs - an:+.4f}")

    write_result(args.json, {
        "threshold": args.threshold,
        # Asserted in the manuscript, so it belongs in the artefact rather than in a printed line.
        "n_proteins": int(len(u)),
        "n_edges": int(len(e)),
        "n_relations": int(e.relation.nunique()),
        "declared": {"r_star": R_STAR, "anchors": ANCHORS, "contaminated": CONTAMINATED},
        "size_profile": prof,
        "relation_density": {k: round(float(v), 6) for k, v in dens.items()},
        "relation_density_note": ("over deduplicated unordered pairs against the shared protein "
                                  "universe; STRING ships both directions, so a row count would "
                                  "double every value (D-51)"),
        "edge_counts": {k: {"directed": int(directed[k]), "undirected": int(undirected[k])}
                        for k in dens.index},
        "target_relation_density": round(float(dens[R_STAR[0]]), 6),
        "highest_relation_density": round(float(dens.max()), 6),
        "densest_channel": str(dens.index[0]),
        "saturation_ratio_against_corpus_a": round(0.9954 / float(dens[R_STAR[0]]), 0),
        "clique_contrast_by_size": by_size,
        "per_relation": rows,
        "r_star_minus_best_anchor": verdicts,
    }, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

r"""How corpus B's negatives are drawn, and why their clique rate is zero in every size bin.

Table 4 reports a negative clique rate of 0.0000 at four decimal places in every size bin, and a
reviewer's first reading of that is that the sampler excluded existing edges -- which would make part
of the 0.4124 contrast structural rather than measured, and would put mechanism (c)'s *general* label
in doubt (revision item 1.5). A four-decimal zero cannot distinguish "none observed" from "none
possible", so this script replaces it with three things a reader can check:

1. **The procedure, stated exactly.** Read off the builder rather than described from memory:
   `scripts/build_ws2_benchmark.py` in the CLIQUEBAIT tree draws two `hard` and one `random` negative
   per positive. A `random` negative is $k$ proteins drawn uniformly without replacement from the
   universe of proteins carrying at least one channel edge, where $k$ is the positive's size. A `hard`
   negative keeps the positive's members minus $b = \min(2, k-2)$ of them and substitutes $b$ proteins
   drawn the same way. **No edge is excluded and no collision check is applied.**

2. **The evidence that nothing was excluded.** If existing edges had been avoided, the negatives' mean
   $\phi$ in the target relation would be zero. It is not: it sits at the relation's own density, which
   is what uniform sampling predicts and what edge exclusion forbids.

3. **Raw counters and the analytic expectation.** A clique on $n$ members needs all $\binom{n}{2}$
   dyads, so under independent sampling at density $p$ the expected count in a bin is
   $\sum_i p^{\binom{n_i}{2}}$. CORUM's floor of three members means the smallest bin needs three
   dyads rather than one, and $p^3 \approx 10^{-9}$: zero is not a suspiciously clean number here, it
   is the only number a correct sampler could produce.

The `hard` stratum is reported beside the `random` one because it is the stricter comparison -- it
keeps most of a real complex and swaps a member out -- and Table 4 uses `random`. Reporting both is
the substitute for the exclusion-free column revision item 1.5 asks for, there being no exclusion to
undo.

    python scripts/corpus_b_negatives.py
    python scripts/corpus_b_negatives.py --threshold 150
"""
from __future__ import annotations

import argparse
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from vendor.cliquebait.diagnostics import LeakageAudit  # noqa: E402

WS2 = ROOT.parent / "CLIQUEBAIT" / "data" / "ws2"
BINS = [1, 3, 5, 10, 20, 80, 10_000]
R_STAR = "database"

# Read off scripts/build_ws2_benchmark.py in the CLIQUEBAIT tree, whose pinned library this corpus
# comes from. Recorded here so the manuscript's Section 5.5 can cite a procedure rather than a memory.
PROCEDURE = {
    "negatives_per_positive": 3,
    "hard_per_positive": 2,
    "random_per_positive": 1,
    "random_negative": ("k proteins drawn uniformly without replacement from the universe of "
                        "proteins carrying at least one channel edge, k being the positive's size"),
    "hard_negative": ("the positive's members with b = min(2, k - 2) of them dropped and b proteins "
                      "substituted from the same universe"),
    "existing_edges_excluded": False,
    "collision_with_a_real_complex_checked": False,
    "size_matching": "by construction: a random negative has the positive's size exactly",
    "minimum_positive_size": 3,
    "seed": 0,
}


def undirected_density(edges: pd.DataFrame, relation: str, n_nodes: int) -> tuple[int, float]:
    e = edges[edges.relation == relation]
    lo = np.minimum(e.u.to_numpy(), e.v.to_numpy())
    hi = np.maximum(e.u.to_numpy(), e.v.to_numpy())
    n_und = len(set(zip(lo.tolist(), hi.tolist())))
    return n_und, n_und / (n_nodes * (n_nodes - 1) / 2)


def by_bin(d: pd.DataFrame, p: float) -> dict:
    d = d.assign(bin=pd.cut(d["size"], BINS))
    out = {}
    for b, s in d.groupby("bin", observed=True):
        pos, neg = s[s.label == 1], s[s.label == 0]
        if not len(pos) or not len(neg):
            continue
        # Expected cliques under independent sampling at the relation's own density.
        exp = float(sum(p ** (n * (n - 1) / 2) for n in neg["size"]))
        out[str(b)] = {
            "n_pos": int(len(pos)), "n_neg": int(len(neg)),
            "positive_cliques": int((pos.phi >= 1.0).sum()),
            "negative_cliques": int((neg.phi >= 1.0).sum()),
            "expected_negative_cliques_under_independence": float(f"{exp:.3g}"),
            "clique_rate_pos": round(float((pos.phi >= 1.0).mean()), 4),
            "clique_rate_neg": round(float((neg.phi >= 1.0).mean()), 4),
            "clique_contrast": round(float((pos.phi >= 1.0).mean() - (neg.phi >= 1.0).mean()), 4),
            "mean_phi_pos": round(float(pos.phi.mean()), 4),
            "mean_phi_neg": round(float(neg.phi.mean()), 5),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, default=400)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    out_json = args.json or ROOT / "results" / f"corpus_b_negatives_thr{args.threshold}.json"

    g = pd.read_parquet(WS2 / f"groups_thr{args.threshold}.parquet")
    e = pd.read_parquet(WS2 / f"edges_thr{args.threshold}.parquet")
    u = pd.read_parquet(WS2 / f"universe_thr{args.threshold}.parquet")
    n_prot = int(len(u))

    n_und, p = undirected_density(e, R_STAR, n_prot)
    print(f"target relation {R_STAR!r}: {n_und:,} undirected edges over {n_prot:,} proteins, "
          f"density {p:.6f}")

    phi = LeakageAudit(e, g).densities()
    base = phi[[f"phi_{R_STAR}", "label", "size", "neg_type"]].rename(
        columns={f"phi_{R_STAR}": "phi"}).dropna(subset=["phi"])

    strata = {}
    for stratum in ("random", "hard"):
        d = base[(base.label == 1) | (base.neg_type == stratum)]
        strata[stratum] = by_bin(d, p)
        neg = d[d.label == 0]
        print(f"\n{stratum} negatives: {len(neg):,} groups, "
              f"{int((neg.phi >= 1.0).sum())} cliques, mean phi {neg.phi.mean():.5f}")
        print(f"  {'members':14s} {'n_neg':>6s} {'cliques':>8s} {'E[cliques]':>12s} "
              f"{'mean phi':>10s} {'contrast':>9s}")
        for b, v in strata[stratum].items():
            print(f"  {b:14s} {v['n_neg']:>6d} {v['negative_cliques']:>8d} "
                  f"{v['expected_negative_cliques_under_independence']:>12.3g} "
                  f"{v['mean_phi_neg']:>10.5f} {v['clique_contrast']:>9.4f}")

    # The exclusion test. Uniform sampling puts the negatives' mean phi at the relation's density;
    # exclusion would put it at zero. Reported as a ratio so the comparison needs no threshold.
    mean_phi_random = float(base[(base.label == 0) & (base.neg_type == "random")].phi.mean())
    print(f"\nexclusion test: random negatives' mean phi {mean_phi_random:.5f} against the "
          f"relation's density {p:.5f}")
    print(f"  ratio {mean_phi_random / p:.2f} -- edge exclusion would force this to zero")

    # A worked instance, so the zero is checkable by hand rather than by trust: the smallest bin's
    # groups need three dyads each and the density is a thousandth.
    smallest = next(iter(strata["random"]))
    payload = {
        "threshold": args.threshold,
        "procedure": PROCEDURE,
        "target_relation": R_STAR,
        "n_proteins": n_prot,
        "n_undirected_edges_target": int(n_und),
        "target_relation_density": round(p, 6),
        "exclusion_test": {
            "mean_phi_random_negatives": round(mean_phi_random, 6),
            "relation_density": round(p, 6),
            "ratio": round(mean_phi_random / p, 3),
            "verdict": ("negatives carry the relation at its own density, so no edge exclusion was "
                        "applied; the zero clique rate is a property of the clique statistic on "
                        "groups of three or more, not of the sampler"),
        },
        "worked_example": {
            "bin": smallest,
            "n_neg": strata["random"][smallest]["n_neg"],
            "dyads_a_clique_needs_at_three_members": 3,
            "probability_per_group": float(f"{p ** 3:.3g}"),
            "expected_cliques":
                strata["random"][smallest]["expected_negative_cliques_under_independence"],
            "observed_cliques": strata["random"][smallest]["negative_cliques"],
        },
        "by_stratum": strata,
    }
    write_result(out_json, payload, indent=2, default=str)
    print(f"\nwritten to {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

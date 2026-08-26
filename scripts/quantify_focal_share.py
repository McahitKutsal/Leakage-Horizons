r"""What share of the target relation is the focal group's own contribution, in each corpus?

Mechanism (b) is a quantitative claim -- "a saturating target relation hides the trace, and the focal
contribution is only a small part of it" -- and until this script existed the manuscript supported it
with **one** number, 6.8 percent, computed on the PTA register in Section 5.3 and then quoted for
corpus A as well. The two corpora have different relations, different dating conventions and different
densities; a share computed on one is not a share on the other, and a figure that travels between
corpora reads as an error whether or not it is one (revision item 1.3).

So both shares are computed here, by one code path, and reported separately.

**PTA (Section 5.3).** The register codes a signature year and a force year per agreement, so the
back-dated increment is directly observable: the signature-dated relation's edge-years minus the
force-dated relation's. That difference divided by the signature-dated total is the share of the
relation that exists only because of the dating convention. This reproduces 13,966 / 204,747 from the
edge files rather than restating it.

**Corpus A.** The register codes one date, so there is no second relation to subtract and no
back-dated increment to measure -- that is Section 6.3's entailment argument and it is not repaired
here. What *is* measurable, and what mechanism (b) actually needs, is how much of the density the
statistic reads is the focal group's own contribution as against every other group's. Co-membership
carries a weight equal to the number of organisations a pair shares, and the focal entity contributes
exactly 1 to that weight, so the decomposition is exact rather than estimated:

* **star-local share** -- for each accession event, of the candidate-to-member dyads the statistic
  reads as present at level $k$, the share that would fall below $k$ if the focal entity alone were
  removed. This is the quantity the pooled contrast is computed from, so it is the one mechanism (b)
  is about.
* **relation-level share** -- the same subtraction over the whole relation rather than over one star,
  which is the closest structural analogue of the PTA computation.
* **induced-dyad share** -- the focal group's induced pairs as a share of all pairs, ignoring weight.
  Reported because it is the number a reader would reach for, and it is the wrong one: it measures
  how large the group is, not how much of the relation the group put there.

Both levels of the declared ladder are reported, because a dyad at weight $w$ leaves level $k$ when
the focal entity is removed only if $w = k$ exactly, so the share is a function of the level and a
single number for it would be the same specification gap D-44 records.

    python scripts/quantify_focal_share.py
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

LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"
REGIME = (1965, 2014)
R_STAR = "igo_comembership"
LEVELS = (1, 25)
FULL = 1


# --------------------------------------------------------------------------- PTA
def pta_share() -> dict:
    """Section 5.3's 6.8 percent, recomputed from the two edge files.

    The signature-dated relation carries every dyad-year the force-dated one does plus the ones the
    signature convention adds, so the difference is the back-dated increment and needs no model.
    """
    sig = pd.read_parquet(GRAPH / "edges_pta_signature.parquet")
    force = pd.read_parquet(GRAPH / "edges_pta_force.parquet")
    n_sig, n_force = len(sig), len(force)
    diff = n_sig - n_force

    # The increment is a set difference, not only a count difference: a convention that moved dyads
    # rather than adding them would give the same count difference and a different mechanism.
    key = lambda d: set(zip(d.year.to_numpy(), np.minimum(d.cow_i, d.cow_j),
                            np.maximum(d.cow_i, d.cow_j)))
    ks, kf = key(sig), key(force)
    return {
        "n_edge_years_signature": int(n_sig),
        "n_edge_years_force": int(n_force),
        "back_dated_increment": int(diff),
        "focal_share_of_relation": round(diff / n_sig, 4),
        "increment_is_a_superset_not_a_shift": bool(kf <= ks),
        "dyad_years_only_in_signature": int(len(ks - kf)),
        "dyad_years_only_in_force": int(len(kf - ks)),
    }


# ----------------------------------------------------------------------- corpus A
def _weight_lookup(cm: pd.DataFrame) -> dict[int, dict[tuple[int, int], int]]:
    """year -> {(lo, hi): weight}. Built once; the stars below hit it a few hundred thousand times."""
    out: dict[int, dict[tuple[int, int], int]] = {}
    yr = cm.year.to_numpy()
    lo = np.minimum(cm.cow_i.to_numpy(), cm.cow_j.to_numpy())
    hi = np.maximum(cm.cow_i.to_numpy(), cm.cow_j.to_numpy())
    w = cm.weight.to_numpy()
    for y in np.unique(yr):
        m = yr == y
        out[int(y)] = dict(zip(zip(lo[m].tolist(), hi[m].tolist()), w[m].tolist()))
    return out


def corpus_a_share() -> dict:
    """The focal entity's own contribution to the density the statistic reads, per level.

    Co-membership's weight is the number of organisations a pair shares, and the focal entity adds
    exactly one to it for pairs of its own members. So a dyad read as present at level $k$ is present
    *only through the focal entity* exactly when its weight equals $k$: removing that one organisation
    takes it to $k - 1$. No estimation is involved and the arithmetic is checkable by hand.
    """
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    ev = pd.read_parquet(LEDGER / "events.parquet")
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    ev = ev.merge(ent[["entity_id", "entity_type"]], on="entity_id", how="left")
    cm = pd.read_parquet(GRAPH / f"edges_{R_STAR}.parquet")

    W = _weight_lookup(cm)
    full = mem[mem.status == FULL]
    members = {(e, int(y)): g.ccode.to_numpy()
               for (e, y), g in full.groupby(["entity_id", "year"], sort=False)}

    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()
             & ev.t_R.between(*REGIME) & (ev.entity_type == "organisation")]

    # Relation-level totals, over the years the events fall in, so the denominator is the relation
    # the statistic was read on rather than the whole 1946-2014 file.
    years = sorted({int(t) for t in acc.t_R.unique()})
    per_level = {k: {"read": 0, "only_focal": 0, "star_read": 0, "star_only_focal": 0,
                     "induced": 0, "all_pairs": 0} for k in LEVELS}

    n_events = 0
    for r in acc.itertuples():
        eid, cc, t = r.entity_id, int(r.ccode), int(r.t_R)
        ms = members.get((eid, t))
        if ms is None or ms.size == 0:
            continue
        wy = W.get(t)
        if wy is None:
            continue
        n_events += 1
        others = ms[ms != cc]
        # The star the pooled statistic reads for this event.
        star_w = [wy.get((min(cc, int(m)), max(cc, int(m))), 0) for m in others]
        # The focal group's induced dyads, for the naive share.
        ind = others.size + (others.size * (others.size - 1)) // 2
        for k in LEVELS:
            read = sum(1 for w in star_w if w >= k)
            only = sum(1 for w in star_w if w == k)
            per_level[k]["star_read"] += read
            per_level[k]["star_only_focal"] += only
            per_level[k]["induced"] += ind

    # Relation-level: every dyad-year in the regime, and how many of them any single member
    # organisation is solely responsible for. A dyad at weight k is carried by k organisations and
    # exactly k of them could each be the sole one at that level, so the share attributable to one
    # average organisation is (dyads at weight k) / (dyads at weight >= k) / k -- reported below as
    # the unaveraged numerator and denominator so the reader can take whichever they mean.
    sub = cm[cm.year.between(*REGIME)]
    n_states = len(np.unique(np.r_[sub.cow_i.to_numpy(), sub.cow_j.to_numpy()]))
    rel = {}
    for k in LEVELS:
        at_least = int((sub.weight >= k).sum())
        exactly = int((sub.weight == k).sum())
        rel[f"k={k}"] = {
            "dyad_years_at_or_above_level": at_least,
            "dyad_years_exactly_at_level": exactly,
            "share_lost_if_one_organisation_removed": round(exactly / at_least, 4) if at_least else None,
        }

    out = {"regime": list(REGIME), "n_events": int(n_events), "relation": R_STAR,
           "n_states_in_relation": int(n_states),
           "target_relation_density_k1": round(float(len(sub[sub.weight >= 1])
                                                     / (n_states * (n_states - 1) / 2
                                                        * len(sub.year.unique()))), 4),
           "star_local": {}, "relation_level": rel}
    for k in LEVELS:
        d = per_level[k]
        out["star_local"][f"k={k}"] = {
            "dyads_read_as_present": int(d["star_read"]),
            "dyads_present_only_through_the_focal_entity": int(d["star_only_focal"]),
            "focal_share_of_what_the_statistic_reads":
                round(d["star_only_focal"] / d["star_read"], 4) if d["star_read"] else None,
        }
    out["induced_dyad_share_note"] = (
        "the focal group's induced pairs as a share of all pairs measures group size, not the "
        "group's contribution to the relation, and is reported only to say why it is not used")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "focal_share.json")
    args = ap.parse_args()

    pta = pta_share()
    print("PTA, Section 5.3 -- the back-dated increment is directly coded")
    for k, v in pta.items():
        print(f"  {k:44s} {v}")

    a = corpus_a_share()
    print("\ncorpus A -- one coded date, so the focal contribution rather than an increment")
    print(f"  events used: {a['n_events']:,} organisation accessions in "
          f"{a['regime'][0]}-{a['regime'][1]}")
    for k in LEVELS:
        s = a["star_local"][f"k={k}"]
        r = a["relation_level"][f"k={k}"]
        print(f"  level k={k}")
        print(f"    of the {s['dyads_read_as_present']:,} candidate-to-member dyads the pooled "
              f"statistic reads as present,")
        print(f"    {s['dyads_present_only_through_the_focal_entity']:,} are present only through "
              f"the focal entity: "
              f"{s['focal_share_of_what_the_statistic_reads'] * 100:.1f} percent")
        print(f"    relation-wide, {r['dyad_years_exactly_at_level']:,} of "
              f"{r['dyad_years_at_or_above_level']:,} dyad-years sit exactly at the level: "
              f"{r['share_lost_if_one_organisation_removed'] * 100:.1f} percent")

    print("\nthe two shares are not the same quantity and must not be quoted for each other:")
    print(f"  PTA      {pta['focal_share_of_relation'] * 100:.1f} percent, a coded back-dating "
          f"increment")
    print(f"  corpus A {a['star_local']['k=1']['focal_share_of_what_the_statistic_reads'] * 100:.1f} "
          f"percent at k=1 and "
          f"{a['star_local']['k=25']['focal_share_of_what_the_statistic_reads'] * 100:.1f} percent "
          f"at k=25, a focal contribution")

    write_result(args.json, {"pta": pta, "corpus_a": a}, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

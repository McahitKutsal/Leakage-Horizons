"""The observation graph $G_t$: five relations over COW state codes, one year at a time.

Four relations come from CLIQUEBAIT's rebuilt canonical edges, unchanged and with their declared
gaps intact. The fifth, `igo_comembership`, is built here and does not exist in the prior work,
because manifesto section 11 makes $r^\\star$ depend on entity type: for an alliance entity the leaking
relation is the alliance edge, and for an organisation it is co-membership. LEDGER is
organisation-majority, so without this relation U1 would be computing the horizon curve of a
channel that cannot carry the leak for four fifths of the corpus.

**Co-membership is built from the label source on purpose.** It is the same COW IGO file that
supplies T1's and T2's labels, so it leaks by construction -- that is not a defect to apologise
for, it is the object of study, and the question U1 asks is whether the leak decays with the
horizon. What must not happen is the focal organisation's own edges being counted, since those
*are* the label; `focal_excluded_weight` removes exactly them, which is section 5.3's intervention
expressed as arithmetic rather than as a rebuild.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CB = ROOT.parent / "CLIQUEBAIT"
CB_CANON = CB / "data" / "canonical"
PREV_CANON = CB / "previous-work-code-base" / "coalition-gnn" / "data" / "canonical"

WINDOW_START, WINDOW_END = 1946, 2014

# Provenance per relation, with the source actually read rather than the source advertised --
# PROTOCOL section 1, and the row that was wrong in the audited paper. Coverage is verified by
# `coverage_audit`, never asserted here.
RELATION_SOURCES = {
    "allies": (CB_CANON / "edges_ally.parquet",
               "ATOP v5.1 defence pacts, rebuilt by CLIQUEBAIT (FINDINGS section 4)"),
    "trades": (CB_CANON / "edges_trade.parquet",
               "IMF IMTS/DOTS, rebuilt by CLIQUEBAIT; begins 1948"),
    "votes_with": (PREV_CANON / "edges_vote.parquet",
                   "UNGA ideal points, k-NN k=30, reused unchanged"),
    "conflicts_with": (PREV_CANON / "edges_conflict.parquet",
                       "COW MID 5.0, reused; the source genuinely ends 2014"),
}

IGO_COMEMBERSHIP = "igo_comembership"
FULL_MEMBER = 1


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Undirected, deduplicated, cow_i < cow_j, restricted to the window."""
    d = df.rename(columns={c: c.lower() for c in df.columns})
    lo = np.minimum(d.cow_i.to_numpy(), d.cow_j.to_numpy())
    hi = np.maximum(d.cow_i.to_numpy(), d.cow_j.to_numpy())
    d = d.assign(cow_i=lo, cow_j=hi)
    d = d[(d.cow_i != d.cow_j) & d.year.between(WINDOW_START, WINDOW_END)]
    # Duplicates arise from directed source files; summing weights would double them, so the
    # maximum is taken and the choice is stated rather than left to whichever row sorts first.
    return (d.groupby(["year", "cow_i", "cow_j"], as_index=False)["weight"].max()
            .astype({"year": "int32", "cow_i": "int32", "cow_j": "int32"}))


def load_relations(names: list[str] | None = None) -> dict[str, pd.DataFrame]:
    out = {}
    for name in (names or list(RELATION_SOURCES)):
        path, _ = RELATION_SOURCES[name]
        out[name] = _normalise(pd.read_parquet(path))
    return out


def build_igo_comembership(membership: pd.DataFrame | None = None) -> pd.DataFrame:
    """Dyads sharing at least one organisation, weighted by how many they share.

    Full membership only. An observer is not a member (LEDGER.md section 4.1), and letting observer
    status create co-membership edges would put the administrative precursor into the relation
    that is supposed to be measured *against* it.

    Only `organisation` entities contribute. Alliance-treaty co-membership is already the
    `allies` relation, and pooling the two would make the fifth relation a mixture whose leak
    could not be attributed to either source.
    """
    if membership is None:
        membership = pd.read_parquet(ROOT / "data" / "ledger" / "membership.parquet")
    m = membership[(membership.status == FULL_MEMBER)
                   & membership.entity_id.str.startswith("igo:")]

    frames = []
    for (_eid, year), g in m.groupby(["entity_id", "year"], sort=False):
        codes = np.sort(g.ccode.to_numpy())
        if codes.size < 2:
            continue
        i, j = np.triu_indices(codes.size, 1)
        frames.append(pd.DataFrame({"year": year, "cow_i": codes[i], "cow_j": codes[j]}))
    if not frames:
        return pd.DataFrame(columns=["year", "cow_i", "cow_j", "weight"])

    allp = pd.concat(frames, ignore_index=True)
    out = (allp.groupby(["year", "cow_i", "cow_j"], as_index=False)
           .size().rename(columns={"size": "weight"}))
    return out.astype({"year": "int32", "cow_i": "int32", "cow_j": "int32",
                       "weight": "int32"})


def focal_excluded_weight(comembership: pd.DataFrame, membership: pd.DataFrame,
                          entity_id: str) -> pd.DataFrame:
    """Co-membership with the focal entity's own contribution removed. Section 5.3, U3.

    A dyad both of whose states are full members of `entity_id` in that year has one of its
    shared organisations counted by the entity under study, so the weight drops by one and the
    edge disappears when it reaches zero. This is exact rather than approximate: the weight *is*
    the count of shared organisations, so subtracting the focal one is the whole intervention.

    For termination forecasting this matters more than for accession, because the focal
    organisation's own co-membership edges are the label -- an organisation that ends is a set of
    co-membership edges that disappears.
    """
    mem = membership[(membership.status == FULL_MEMBER)
                     & (membership.entity_id == entity_id)]
    if mem.empty:
        return comembership

    focal = []
    for year, g in mem.groupby("year", sort=False):
        codes = np.sort(g.ccode.to_numpy())
        if codes.size < 2:
            continue
        i, j = np.triu_indices(codes.size, 1)
        focal.append(pd.DataFrame({"year": year, "cow_i": codes[i], "cow_j": codes[j],
                                   "focal": 1}))
    if not focal:
        return comembership

    f = pd.concat(focal, ignore_index=True)
    out = comembership.merge(f, on=["year", "cow_i", "cow_j"], how="left")
    out["weight"] = out.weight - out.focal.fillna(0).astype(int)
    return out.loc[out.weight > 0, ["year", "cow_i", "cow_j", "weight"]].reset_index(drop=True)


def coverage_audit(relations: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per relation per year: edges and nodes. Then the regimes those imply.

    Manifesto section 2 makes this a precondition rather than a robustness check, because the audited
    paper's headline architectural result came entirely from pooling a ranking metric across a
    coverage break -- +0.037 that appears in no sub-window. A regime here is a maximal run of
    consecutive years over which the *set* of non-empty relations does not change. No headline
    number may span two of them.
    """
    rows = []
    for name, d in relations.items():
        g = d.groupby("year")
        for year, sub in g:
            nodes = pd.unique(np.concatenate([sub.cow_i.to_numpy(), sub.cow_j.to_numpy()]))
            rows.append({"relation": name, "year": int(year), "n_edges": int(len(sub)),
                         "n_nodes": int(len(nodes))})
    per_year = pd.DataFrame(rows)

    years = range(WINDOW_START, WINDOW_END + 1)
    present = {y: frozenset(per_year.loc[(per_year.year == y) & (per_year.n_edges > 0),
                                         "relation"]) for y in years}
    regimes, start = [], WINDOW_START
    for y in years:
        if y > WINDOW_START and present[y] != present[y - 1]:
            regimes.append((start, y - 1, present[y - 1]))
            start = y
    regimes.append((start, WINDOW_END, present[WINDOW_END]))
    reg = pd.DataFrame([{"regime": i, "start": a, "end": b, "n_years": b - a + 1,
                         "n_relations": len(s), "relations": ",".join(sorted(s))}
                        for i, (a, b, s) in enumerate(regimes)])
    return per_year, reg

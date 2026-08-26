r"""An independent reference implementation of the group density and the clique contrast.

Section 9's first threat to validity is that $\phi_r(S; k)$ and $\kappa_r(\Delta)$ are computed by one
implementation across all four testbeds, so an error in it would be common to every result. The
survival likelihood does not have that problem -- it is checked against closed forms and against a
reference to within $10^{-13}$ -- and the density code had no equivalent (revision item 2.7).

This module is that equivalent. It is written to the definitions in Section 3.1 rather than from
`penumbra.umbra`, and it shares nothing with it:

* `umbra` packs each undirected dyad into one `int64`, sorts the packed keys per (relation, year), and
  answers membership with `numpy.searchsorted` over the sorted array. Here a dyad is a `tuple` of two
  ids and lookup is a Python `dict`. No array is built and `numpy` is not imported.
* `umbra` decomposes a candidate group's dyads into the member-only dyads, cached per (entity, year,
  relation, level), plus the star from the candidate to each member -- an optimisation whose whole
  point is not to enumerate the group's pairs. Here every pair is enumerated with
  `itertools.combinations` every time. The cache is the part of `umbra` most able to be subtly wrong,
  so the reference deliberately has no cache at all.
* `umbra` reads weights out of a parallel array indexed by the same search position. Here the weight
  is the dict's value.

Being slower by two orders of magnitude is the point: the two implementations agree or they do not,
and if they do, agreement is not an artefact of a shared trick.

Two conventions are inherited deliberately rather than rediscovered, because they are choices in the
specification and not consequences of it. Both are stated in `umbra.phi`:

1. A group with fewer than two members present in the graph's node set scores `nan`, not 0. No data is
   not the same as no leakage, and scoring it zero reads as the latter.
2. A relation with no edges at all in a given year scores 0 for every group, not `nan`. The relation
   exists and is empty; that is a measurement.
3. **Level 1 means presence, not weight at least one.** The level ladder is defined for the target
   relation, whose weight counts the organisations a pair shares and is therefore a positive integer.
   The anchors are presence relations carrying weights on scales that are not counts at all -- log
   trade volume runs from -3.98 to 3.54, voting agreement lies strictly inside the unit interval -- so
   a literal `weight >= 1` filter at level 1 would empty the voting relation entirely and leave trade
   flows with only its positive half.

The first draft of this module implemented convention 3 the literal way, and the cross-check reported
a disagreement of exactly 1.0 on the voting and trade stars. The specification was right and the
reference was wrong, which is the outcome a second implementation is *also* for: it tests whether the
convention was ever written down clearly enough to be re-implemented. This one was not, and Section 4
now says so.

A reference that made the opposite choices would disagree with `umbra` on those rows for a reason that
is not an error, and the disagreement would drown the ones that are.
"""
from __future__ import annotations

from itertools import combinations
from math import isnan

__all__ = ["ReferenceDensity", "clique_contrast", "node_id"]


def node_id(x):
    """Normalise a node label to a hashable, sortable Python scalar.

    Corpus A and the synthetic testbed identify nodes by integer country code; corpus B identifies
    proteins by string accession. One reference has to take both, and mixing `numpy.int64` with `int`
    in dict keys is the kind of silent mismatch a cross-check exists to expose rather than commit.
    """
    if isinstance(x, str):
        return x
    try:
        return int(x)
    except (TypeError, ValueError):
        return str(x)


class ReferenceDensity:
    """Group densities from a plain dict of dyad weights. No arrays, no caching, no decomposition.

    Parameters
    ----------
    edges : DataFrame [relation, year, cow_i, cow_j, weight]
        Read once into `{(relation, year): {(lo, hi): weight}}`.
    membership : DataFrame [entity_id, ccode, year, status]
        Full members define the group, as in `umbra`.
    """

    def __init__(self, edges, membership, full_status: int = 1):
        self.w: dict[tuple[str, int], dict[tuple, float]] = {}
        has_w = "weight" in edges.columns
        for row in edges.itertuples(index=False):
            i, j = node_id(row.cow_i), node_id(row.cow_j)
            key = (row.relation, int(row.year))
            d = self.w.get(key)
            if d is None:
                d = self.w[key] = {}
            d[(i, j) if i < j else (j, i)] = float(row.weight) if has_w else 1.0

        # Every node the graph knows about, so convention 1 can be applied. Built from the edge list
        # and the membership register together, matching what `umbra` puts in its index.
        self.nodes: set = set()
        for row in edges.itertuples(index=False):
            self.nodes.add(node_id(row.cow_i))
            self.nodes.add(node_id(row.cow_j))
        if membership is not None:
            for c in membership.ccode:
                self.nodes.add(node_id(c))

        self.members: dict[tuple[str, int], tuple] = {}
        if membership is not None:
            full = membership[membership.status == full_status]
            for row in full.itertuples(index=False):
                key = (row.entity_id, int(row.year))
                self.members.setdefault(key, []).append(node_id(row.ccode))
            self.members = {k: tuple(sorted(v)) for k, v in self.members.items()}

    # ------------------------------------------------------------------ densities
    def phi(self, members, year: int, relation: str, level: int = 1) -> float:
        r"""$\phi_r(S; k)$: the share of $S$'s pairs carrying weight at least $k$ in $r$ at `year`.

        Every pair is enumerated. Convention 1 applies when fewer than two members are nodes of the
        graph; convention 2 when the relation is empty that year.
        """
        present = sorted({node_id(m) for m in members if node_id(m) in self.nodes})
        if len(present) < 2:
            return float("nan")
        table = self.w.get((relation, int(year)))
        if not table:
            return 0.0
        hits = total = 0
        for u, v in combinations(present, 2):
            total += 1
            weight = table.get((u, v))
            if weight is None:
                continue
            if level <= 1 or weight >= level:      # convention 3
                hits += 1
        return hits / total

    def phi_candidate(self, entity_id: str, year: int, ccode: int, relation: str,
                      level: int = 1) -> float:
        """`phi` for the group `members(entity, year)` with `ccode` added.

        `umbra` answers this by adding a cached member-only count to a freshly computed star. Here the
        candidate group is assembled and handed to `phi`, so the two agree only if the decomposition
        is right.
        """
        ms = self.members.get((entity_id, int(year)))
        if not ms:
            return float("nan")
        group = set(ms)
        group.add(node_id(ccode))
        return self.phi(sorted(group), year, relation, level)

    def star(self, ccode: int, others, year: int, relation: str, level: int = 1) -> float:
        """Share of the dyads from `ccode` to `others` that `relation` carries at `year`.

        The statistic Table 3's matched contrast is built from. Kept separate from `phi` because it is
        a different quantity -- a star rather than a group -- and conflating them is exactly the kind
        of error a second implementation exists to catch.
        """
        c = node_id(ccode)
        if c not in self.nodes:
            return float("nan")
        oi = sorted({node_id(m) for m in others if node_id(m) in self.nodes} - {c})
        if not oi:
            return float("nan")
        table = self.w.get((relation, int(year)))
        if not table:
            return 0.0
        hits = 0
        for m in oi:
            weight = table.get((c, m) if c < m else (m, c))
            if weight is None:
                continue
            if level <= 1 or weight >= level:      # convention 3
                hits += 1
        return hits / len(oi)


def clique_contrast(values, labels, tol: float = 1e-9) -> dict:
    r"""$P(\phi = 1 \mid \text{pos}) - P(\phi = 1 \mid \text{neg})$, from two plain lists.

    Rows whose density is `nan` are dropped rather than scored, for the reason `umbra` gives: a group
    with no data in a relation is an absence, not a zero.
    """
    pos = [v for v, y in zip(values, labels) if y == 1 and not isnan(v)]
    neg = [v for v, y in zip(values, labels) if y == 0 and not isnan(v)]
    if not pos or not neg:
        return {"n_pos": len(pos), "n_neg": len(neg), "clique_contrast": float("nan")}
    cp = sum(1 for v in pos if v >= 1 - tol) / len(pos)
    cn = sum(1 for v in neg if v >= 1 - tol) / len(neg)
    return {"n_pos": len(pos), "n_neg": len(neg),
            "mean_pos": sum(pos) / len(pos), "mean_neg": sum(neg) / len(neg),
            "contrast": sum(pos) / len(pos) - sum(neg) / len(neg),
            "clique_rate_pos": cp, "clique_rate_neg": cn, "clique_contrast": cp - cn}

"""Membership-equivalence families: the resampling unit, not a deduplication rule.

Two bodies with the same members are usually a family rather than a duplicate -- the
Pan-American and European systems each run to double figures of organisations over one
membership -- so this module exists to find *dependence*, not identity. See LEDGER.md section 1.2 for
why membership cannot settle identity and section 1.3 for why it settles the bootstrap unit.
"""
from __future__ import annotations

import itertools
from collections import defaultdict

import numpy as np

__all__ = ["membership_families", "family_fate_correlation", "family_ids"]


def membership_families(sets: dict, years: dict, thresh: float = 0.90,
                        min_shared: int = 5) -> list[list]:
    """Connected components of the membership-equivalence graph.

    `sets` maps (entity, year) -> frozenset of member codes; `years` maps entity -> set of years.
    Components are returned largest first; singletons are omitted, since an entity in no family
    is its own family and the caller assigns that.
    """
    ids = sorted(years)
    adj: dict[object, set] = defaultdict(set)
    for a, b in itertools.combinations(ids, 2):
        shared = years[a] & years[b]
        if len(shared) < min_shared:
            continue
        js = [len(sets[(a, y)] & sets[(b, y)]) / max(1, len(sets[(a, y)] | sets[(b, y)]))
              for y in shared]
        if float(np.mean(js)) >= thresh:
            adj[a].add(b)
            adj[b].add(a)

    seen: set = set()
    fams: list[list] = []
    for n in ids:
        if n in seen:
            continue
        comp, stack = {n}, [n]
        seen.add(n)
        while stack:
            for v in adj[stack.pop()]:
                if v not in seen:
                    seen.add(v)
                    comp.add(v)
                    stack.append(v)
        if len(comp) > 1:
            fams.append(sorted(comp))
    return sorted(fams, key=len, reverse=True)


def family_ids(all_entities, fams: list[list]) -> dict:
    """entity -> family id. An entity in no multi-member family is its own family.

    The bootstrap resamples families, so every entity must belong to exactly one or the
    resampling silently drops it.
    """
    out = {}
    for i, f in enumerate(fams):
        for e in f:
            out[e] = f"fam:{i:03d}"
    for e in all_entities:
        out.setdefault(e, f"solo:{e}")
    return out


def family_fate_correlation(fams: list[list], deaddate: dict, population: set,
                            tol: int = 2, seed: int = 0) -> dict:
    """Do membership-equivalent entities die together?

    If they do, entity-level resampling treats correlated deaths as independent and the T2
    intervals are too narrow.

    The baseline population must be the one the families were drawn from. Pooling in deaths from
    entities outside the analysis window spreads the calendar distribution, lowers the random
    co-fate rate and inflates the enrichment -- measured at 3.72x instead of 2.66x, a 40 %
    overstatement in the direction of the conclusion. Naming the comparison stratum is
    PROTOCOL section 1, and this is what it is for.
    """
    from scipy.stats import binomtest

    within = [(a, b) for f in fams
              for a, b in itertools.combinations([i for i in f if i in deaddate], 2)]
    hits = sum(1 for a, b in within if abs(deaddate[a] - deaddate[b]) <= tol)

    dates = np.array([d for i, d in sorted(deaddate.items()) if i in population])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(dates), size=(20000, 2))
    idx = idx[idx[:, 0] != idx[:, 1]]
    base = float(np.mean(np.abs(dates[idx[:, 0]] - dates[idx[:, 1]]) <= tol))

    p = (float(binomtest(hits, len(within), base, alternative="greater").pvalue)
         if within else 1.0)
    return {
        "within_family_dead_pairs": len(within),
        "within_family_cofate": hits,
        "within_family_rate": round(hits / len(within), 4) if within else None,
        "random_pair_rate": round(base, 4),
        "enrichment": round((hits / len(within)) / base, 2) if within and base else None,
        "binomial_p_one_sided": round(p, 5),
        "caveat": "pairs within a family share entities, so they are not independent and the "
                  "nominal p is anti-conservative. Suggestive, not settled.",
    }

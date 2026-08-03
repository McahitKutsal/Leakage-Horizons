"""Does LEDGER count the same coalition twice, once from ATOP and once from COW IGO?

NATO is an alliance treaty in ATOP and an organisation in COW IGO. So are the OAS, the Arab
League, the EEC and the Warsaw Pact. Admitting both as entities would double-count them with
two founding dates, two termination codings and two dating regimes -- and because the same
coalition-years would then appear twice, the cluster bootstrap of manifesto section 9.4 would be
resampling units it believes are independent and are not.

The match is on membership rather than on name. Names disagree across sources in every way a
string can, and a coalition IS its member set at a point in time, so Jaccard over the
overlapping years is both more reliable and closer to the thing being deduplicated.

    python scripts/detect_entity_overlap.py --json results/entity_overlap.json

Output is candidates for review, not a decision. A high Jaccard between an alliance treaty and
an organisation is evidence that they are the same coalition; it can also mean two distinct
bodies with the same membership, which in regional politics is common -- the OAS and the Rio
Pact share almost every member and are not the same entity. The resolved list belongs in
LEDGER.md as a declared crosswalk.
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

from penumbra.crosswalk import igo_membership_long  # noqa: E402

ATOP = ROOT.parent / "CLIQUEBAIT" / "data" / "ATOP 5.1 (.csv)"

WINDOW = (1946, 2014)          # COW IGO ends 2014; ATOP runs later but cannot be compared past it
MIN_MEMBERS = 3                # COW IGO's own inclusion rule, so bilateral treaties cannot match
MIN_JACCARD = 0.60             # report threshold, deliberately low: this is triage
MIN_SHARED_YEARS = 3


def atop_membership() -> pd.DataFrame:
    """Long-format (atopid, year, ccode) for multilateral treaties active in the window."""
    a = pd.read_csv(ATOP / "atop5_1a.csv", low_memory=False)
    m = pd.read_csv(ATOP / "atop5_1m.csv", low_memory=False)

    size = m.groupby("atopid").size()
    keep = set(size[size >= MIN_MEMBERS].index) & set(a.loc[a.begyr >= WINDOW[0], "atopid"])
    m = m[m.atopid.isin(keep)].copy()

    # yrexit == 0 means the membership never ended in the source. Treating it as year zero would
    # silently empty every ongoing treaty, which is the failure mode that looks like "no
    # coalitions after 1946" rather than like a bug.
    m["yr_out"] = np.where(m.yrexit.fillna(0) > 0, m.yrexit, WINDOW[1])
    m["yr_in"] = m.yrent.replace(0, np.nan)
    m = m.dropna(subset=["yr_in"])

    rows = []
    for r in m.itertuples():
        lo = max(int(r.yr_in), WINDOW[0])
        hi = min(int(r.yr_out), WINDOW[1])
        for y in range(lo, hi + 1):
            rows.append((int(r.atopid), y, int(r.member)))
    return pd.DataFrame(rows, columns=["atopid", "year", "ccode"])


def _sets_by_year(df: pd.DataFrame, key: str) -> dict:
    out: dict[tuple, frozenset] = {}
    for (k, y), g in df.groupby([key, "year"], sort=False):
        out[(k, y)] = frozenset(g.ccode.tolist())
    return out


def membership_families(sets: dict, years: dict, thresh: float = 0.90,
                        min_shared: int = 5) -> list[list[int]]:
    """Connected components of the membership-equivalence graph over organisations.

    Not duplicates. Two bodies with the same members are usually a family -- the Pan-American
    and the European systems each run to double figures of organisations over one membership --
    and the reason to find them is not deduplication but the resampling unit of section 9.4.
    """
    import itertools
    from collections import defaultdict

    ids = sorted(years)
    adj: dict[int, set[int]] = defaultdict(set)
    for a, b in itertools.combinations(ids, 2):
        shared = years[a] & years[b]
        if len(shared) < min_shared:
            continue
        js = [len(sets[(a, y)] & sets[(b, y)]) / max(1, len(sets[(a, y)] | sets[(b, y)]))
              for y in shared]
        if float(np.mean(js)) >= thresh:
            adj[a].add(b)
            adj[b].add(a)

    seen: set[int] = set()
    fams: list[list[int]] = []
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


def family_fate_correlation(fams: list[list[int]], deaddate: dict, population: set[int],
                            tol: int = 2, seed: int = 0) -> dict:
    """Do membership-equivalent organisations die together?

    If they do, entity-level resampling treats correlated deaths as independent and the T2
    intervals are too narrow. The comparison is against randomly paired deaths from the same
    population, so the baseline already carries the calendar clustering of IGO deaths in
    general -- otherwise any two deaths in a busy decade would look like a shared fate.
    """
    import itertools

    within = [(a, b) for f in fams
              for a, b in itertools.combinations([i for i in f if i in deaddate], 2)]
    hits = sum(1 for a, b in within if abs(deaddate[a] - deaddate[b]) <= tol)

    # The baseline population must be the one the families were drawn from. Pooling in deaths
    # from organisations outside the analysis window spreads the calendar distribution, lowers
    # the random co-fate rate and inflates the enrichment -- measured here at 3.72x instead of
    # 2.6x, which is a 40 % overstatement in the direction of the conclusion. Naming the
    # comparison stratum is PROTOCOL section 1, and this is what it is for.
    dates = np.array([d for i, d in sorted(deaddate.items()) if i in population])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(dates), size=(20000, 2))
    idx = idx[idx[:, 0] != idx[:, 1]]
    base = float(np.mean(np.abs(dates[idx[:, 0]] - dates[idx[:, 1]]) <= tol))

    from scipy.stats import binomtest
    p = float(binomtest(hits, len(within), base, alternative="greater").pvalue) if within else 1.0
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--min-jaccard", type=float, default=MIN_JACCARD)
    args = ap.parse_args()

    atop = atop_membership()
    igo = igo_membership_long(full_only=True)
    igo = igo[(igo.year >= WINDOW[0]) & (igo.year <= WINDOW[1])]

    a_sets = _sets_by_year(atop, "atopid")
    i_sets = _sets_by_year(igo, "ionum")
    a_ids = sorted({k for k, _ in a_sets})
    i_ids = sorted({k for k, _ in i_sets})
    print(f"ATOP multilateral treaties active in {WINDOW}: {len(a_ids)}")
    print(f"COW IGO organisations active in {WINDOW}:      {len(i_ids)}")

    a_years = {}
    for (k, y) in a_sets:
        a_years.setdefault(k, []).append(y)
    i_years = {}
    for (k, y) in i_sets:
        i_years.setdefault(k, []).append(y)

    names = (pd.read_csv(ROOT / "data" / "raw" / "cow_igo" / "igo_year_formatv3.csv",
                         sep="\t", usecols=["ionum", "ioname", "orgname"], encoding="latin-1")
             .drop_duplicates("ionum").set_index("ionum"))
    anames = (pd.read_csv(ATOP / "atop5_1a.csv", low_memory=False,
                          usecols=["atopid", "begyr", "endyr"])
              .drop_duplicates("atopid").set_index("atopid"))

    cands = []
    for aid in a_ids:
        ay = set(a_years[aid])
        for iid in i_ids:
            shared = ay & set(i_years[iid])
            if len(shared) < MIN_SHARED_YEARS:
                continue
            js = []
            for y in shared:
                A, B = a_sets[(aid, y)], i_sets[(iid, y)]
                if not A and not B:
                    continue
                js.append(len(A & B) / len(A | B))
            if not js:
                continue
            j = float(np.mean(js))
            if j >= args.min_jaccard:
                cands.append({
                    "atopid": int(aid),
                    "atop_begyr": int(anames.loc[aid, "begyr"]),
                    "atop_endyr": int(anames.loc[aid, "endyr"]),
                    "ionum": int(iid),
                    "igo_name": str(names.loc[iid, "ioname"]),
                    "igo_orgname": str(names.loc[iid, "orgname"]),
                    "shared_years": len(shared),
                    "mean_jaccard": round(j, 4),
                    "max_jaccard": round(float(np.max(js)), 4),
                })

    cands.sort(key=lambda r: -r["mean_jaccard"])
    print(f"\ncandidate duplicate entities at Jaccard >= {args.min_jaccard}: {len(cands)}")
    print(f"{'atopid':>7} {'ionum':>6} {'yrs':>4} {'meanJ':>6} {'maxJ':>6}  organisation")
    for c in cands[:40]:
        print(f"{c['atopid']:>7} {c['ionum']:>6} {c['shared_years']:>4} "
              f"{c['mean_jaccard']:>6} {c['max_jaccard']:>6}  {c['igo_orgname'][:52]}")

    # An ATOP treaty matching several organisations, or the reverse, is the interesting case:
    # it means the two sources cut the same political object at different granularities and a
    # one-to-one crosswalk will not express it.
    from collections import Counter
    ca, ci = Counter(c["atopid"] for c in cands), Counter(c["ionum"] for c in cands)
    multi_a = {k: v for k, v in ca.items() if v > 1}
    multi_i = {k: v for k, v in ci.items() if v > 1}
    print(f"\nATOP treaties matching >1 organisation: {len(multi_a)} {multi_a or ''}")
    print(f"organisations matching >1 ATOP treaty:  {len(multi_i)} {multi_i or ''}")

    fams = membership_families(i_sets, {k: set(v) for k, v in i_years.items()})
    meta = (pd.read_csv(ROOT / "data" / "raw" / "cow_igo" / "igo_year_formatv3.csv", sep="\t",
                        usecols=["ionum", "deaddate"], encoding="latin-1")
            .groupby("ionum").deaddate.max().dropna())
    deaddate = {int(k): int(v) for k, v in meta.items()}
    fate = family_fate_correlation(fams, deaddate, population=set(i_ids))
    print(f"\nmembership-equivalent organisation families (J>=0.90, >=5 shared yrs): {len(fams)}")
    print(f"  sizes {[len(f) for f in fams][:12]}"
          f"   organisations inside a family: {sum(len(f) for f in fams)} of {len(i_ids)}")
    print(f"  within-family dead pairs dying within 2 yrs: {fate['within_family_cofate']}"
          f"/{fate['within_family_dead_pairs']} = {fate['within_family_rate']}"
          f"   vs random {fate['random_pair_rate']}"
          f"   enrichment {fate['enrichment']}x   p={fate['binomial_p_one_sided']}")
    print(f"  {fate['caveat']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "window": list(WINDOW), "min_jaccard": args.min_jaccard,
            "min_shared_years": MIN_SHARED_YEARS,
            "n_atop_multilateral": len(a_ids), "n_igo": len(i_ids),
            "candidates": cands,
            "atop_matching_multiple_igos": {str(k): v for k, v in multi_a.items()},
            "igos_matching_multiple_atop": {str(k): v for k, v in multi_i.items()},
            "membership_families": {
                "threshold_jaccard": 0.90, "min_shared_years": 5,
                "n_families": len(fams), "sizes": [len(f) for f in fams],
                "organisations_in_a_family": sum(len(f) for f in fams),
                "families": fams,
            },
            "family_fate_correlation": fate,
        }, indent=2))
        print(f"\nwritten to {args.json}")


if __name__ == "__main__":
    main()

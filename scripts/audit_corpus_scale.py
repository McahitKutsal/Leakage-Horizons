"""Event counts per candidate source, measured before the corpus is designed.

This is the evidence behind the §11 decision recorded in the manifesto's amendment record,
and it exists because that record cites numbers. Everything the amendment claims about ATOP's
scale and COW IGO's resolution is produced here, from the primary releases, and can be
re-run.

The order matters and is the inherited one: PROTOCOL §1 before anything else, and coverage
verified against the materialised file rather than the source's documentation. The IGO row of
the manifesto's §6 table was wrong in exactly the way that rule anticipates -- the
five-year-resolution claim is true of the literature and false of the file.

    python scripts/audit_corpus_scale.py            # table to stdout
    python scripts/audit_corpus_scale.py --json results/corpus_scale.json

Counts here are an upper bound on usable events, deliberately. They apply no risk-set rule,
no left-truncation rule and no de-clustering, because those are task definitions (§9.1) and
this script exists to decide whether a source is worth defining tasks over at all.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ATOP = ROOT.parent / "CLIQUEBAIT" / "data" / "ATOP 5.1 (.csv)"
IGO = ROOT / "data" / "raw" / "cow_igo" / "igo_year_formatv3.csv"

WINDOW_START = 1946

# COW IGO v3 membership codes. -9 and -1 are not zeros: a state that does not exist, or whose
# membership is unrecorded, is out of the risk set, and counting a transition out of either as
# an accession would manufacture events from state birth and from missing data.
FULL_MEMBER, NO_MEMBER = 1, 0

# Columns of the IGO year file that describe the organisation rather than a state's membership.
IGO_META = ["ioname", "orgname", "year", "longorgname", "ionum", "igocode", "version",
            "accuracyofpre1965membershipdates", "sourcesandnotes", "imputed",
            "political", "social", "economic"]


# --------------------------------------------------------------------------------- ATOP
def audit_atop() -> dict:
    """Alliance treaties as candidate coalition entities, ATOP 5.1 primary release."""
    a = pd.read_csv(ATOP / "atop5_1a.csv", low_memory=False)
    m = pd.read_csv(ATOP / "atop5_1m.csv", low_memory=False)

    # `bilat` is coded on the treaty; membership can still grow past two, so the two ways of
    # asking "is this multilateral" do not agree and both are reported. Choosing one silently
    # would move the entity count by a third.
    n_members = m.groupby("atopid").size().rename("n_members")
    a = a.merge(n_members, left_on="atopid", right_index=True, how="left")

    formed = a[a.begyr >= WINDOW_START]
    # endyr is 0 for treaties never terminated; `ineffect` is the source's own status flag and
    # the two are cross-checked rather than assumed consistent.
    ended = a[(a.endyr >= WINDOW_START) & (a.endyr > 0)]
    disagree = int(((a.endyr > 0) & (a.ineffect == 1)).sum())

    # The membership file carries its own `bilat`; take the treaty's, renamed, so the merge
    # cannot silently hand back a suffixed column and count the wrong one.
    treaty = (a[["atopid", "begyr", "endyr", "bilat", "n_members"]]
              .rename(columns={"bilat": "treaty_bilat"}))
    mm = m.drop(columns=["bilat"]).merge(treaty, on="atopid")
    # An accession is a member whose entry post-dates the treaty's own start. Members entering
    # in the founding year are founders, not accessions, at annual resolution.
    acc = mm[(mm.yrent > mm.begyr) & (mm.yrent >= WINDOW_START)]
    exits = m[(m.yrexit >= WINDOW_START) & (m.yrexit > 0)]

    return {
        "source": "ATOP 5.1 primary release",
        "window_start": WINDOW_START,
        "treaties_total": int(len(a)),
        "treaties_formed_in_window": int(len(formed)),
        "multilateral_by_bilat_flag": int((formed.bilat == 0).sum()),
        "multilateral_by_member_count_ge3": int((formed.n_members >= 3).sum()),
        "terminations_in_window": int(len(ended)),
        "terminations_multilateral": int((ended.bilat == 0).sum()),
        "accessions_in_window": int(len(acc)),
        "accessions_multilateral": int((acc.treaty_bilat == 0).sum()),
        "member_exits_in_window": int(len(exits)),
        "termination_causes_coded": {str(k): int(v) for k, v in
                                     m.termcaus.value_counts(dropna=False).items()},
        "endyr_ineffect_disagreements": disagree,
    }


# ------------------------------------------------------------------------------ COW IGO
def _load_igo() -> tuple[pd.DataFrame, list[str]]:
    # latin-1: the file carries non-UTF-8 bytes in organisation names, and tab-separated
    # despite the .csv extension. Both are the kind of thing that has to be found rather than
    # read about.
    d = pd.read_csv(IGO, sep="\t", low_memory=False, encoding="latin-1")
    d = d.sort_values(["ionum", "year"]).reset_index(drop=True).copy()
    state_cols = [c for c in d.columns if c not in IGO_META]
    return d, state_cols


def audit_igo(era_start: int = 1965) -> dict:
    """Organisations as entities. `era_start` is where the source stops imputing dates."""
    d, state_cols = _load_igo()
    M = d[state_cols].apply(pd.to_numeric, errors="coerce").to_numpy()
    yrs, ion = d.year.to_numpy(), d.ionum.to_numpy()

    # Resolution, measured. The manifesto's original §6 row claimed five-year intervals for
    # much of the series; the file is annual and flags its own uncertain records instead.
    years = np.sort(d.year.unique())
    annual = bool(np.all(np.diff(years) == 1))
    imputed_by_era = (d.assign(era=np.where(d.year < era_start, "pre", "post"))
                      .groupby("era").imputed.agg(["sum", "size"]))
    accuracy = d.groupby("ionum")["accuracyofpre1965membershipdates"].first()

    life = d.groupby("ionum").agg(first=("year", "min"), last=("year", "max"))
    last_year = int(years.max())
    # An organisation absent from every later year is a candidate death, not a coded one. COW
    # ships the status flag in the unit-level file, which is not this file; until that is
    # checked these are candidates and are named as such.
    deaths = life[(life["last"] < last_year) & (life["last"] >= era_start)]

    same_entity = ion[1:] == ion[:-1]
    consecutive = yrs[1:] == yrs[:-1] + 1
    in_era = yrs[1:] > era_start
    step = same_entity & consecutive & in_era
    prev, cur = M[:-1][step], M[1:][step]
    accessions = int(((prev == NO_MEMBER) & (cur == FULL_MEMBER)).sum())
    exits = int(((prev == FULL_MEMBER) & (cur == NO_MEMBER)).sum())

    return {
        "source": "COW IGO v3, igo_year_formatv3",
        "era_start": era_start,
        "years_covered": [int(years.min()), last_year],
        "series_is_annual": annual,
        "n_year_gaps": int((np.diff(years) != 1).sum()),
        "entities_total": int(d.ionum.nunique()),
        "entities_alive_in_era": int((life["last"] >= era_start).sum()),
        "entities_founded_in_era": int((life["first"] >= era_start).sum()),
        "death_candidates_in_era": int(len(deaths)),
        "accessions_in_era": accessions,
        "exits_in_era": exits,
        "imputed_years_pre_era": int(imputed_by_era.loc["pre", "sum"]),
        "imputed_years_in_era": int(imputed_by_era.loc["post", "sum"]),
        "date_accuracy_by_entity": {str(k): int(v) for k, v in
                                    accuracy.value_counts(dropna=False).items()},
        "unverified": "death_candidates_in_era is last-observed-year, not COW's coded "
                      "dead/dormant status; the unit-level file has not been checked",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--era-start", type=int, default=1965)
    args = ap.parse_args()

    atop, igo = audit_atop(), audit_igo(args.era_start)

    print(f"ATOP 5.1 - alliance treaties as entities, {WINDOW_START}+")
    print(f"  entities formed in window       {atop['treaties_formed_in_window']:>7}")
    print(f"    multilateral (bilat flag)     {atop['multilateral_by_bilat_flag']:>7}")
    print(f"    multilateral (>=3 members)    {atop['multilateral_by_member_count_ge3']:>7}")
    print(f"  accessions                      {atop['accessions_in_window']:>7}"
          f"   ({atop['accessions_multilateral']} multilateral)")
    print(f"  terminations                    {atop['terminations_in_window']:>7}"
          f"   ({atop['terminations_multilateral']} multilateral)  <- T2's event supply")
    print(f"  member exits                    {atop['member_exits_in_window']:>7}")

    print(f"\nCOW IGO v3 - organisations as entities, {igo['era_start']}+")
    print(f"  series annual over {igo['years_covered'][0]}-{igo['years_covered'][1]}"
          f"          {str(igo['series_is_annual']):>7}   ({igo['n_year_gaps']} gaps)")
    print(f"  imputed organisation-years, pre  {igo['imputed_years_pre_era']:>6}")
    print(f"  imputed organisation-years, era  {igo['imputed_years_in_era']:>6}"
          f"   <- why interval censoring is tractable")
    print(f"  entities alive in era           {igo['entities_alive_in_era']:>7}")
    print(f"  foundings in era                {igo['entities_founded_in_era']:>7}")
    print(f"  accessions in era               {igo['accessions_in_era']:>7}")
    print(f"  exits in era                    {igo['exits_in_era']:>7}")
    print(f"  death candidates in era         {igo['death_candidates_in_era']:>7}"
          f"   <- {igo['unverified'].split(';')[0]}")
    print("\n  date accuracy, per organisation:")
    for k, v in sorted(igo["date_accuracy_by_entity"].items(), key=lambda kv: -kv[1]):
        print(f"    {v:>5}  {k}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"atop": atop, "cow_igo": igo}, indent=2))
        print(f"\nwritten to {args.json}")


if __name__ == "__main__":
    main()

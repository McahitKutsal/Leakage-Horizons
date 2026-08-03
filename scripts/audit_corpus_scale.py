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
DESTA = ROOT / "data" / "raw" / "desta" / "desta_list_of_treaties_02_03.csv"

WINDOW_START = 1946

# COW IGO v3 membership codes, per the v3 codebook section III.A: 0 no membership, 1 full,
# 2 associate, 3 observer, -9 MISSING DATA, -1 STATE NOT A SYSTEM MEMBER. The two negative
# codes are the ones that matter and they are easy to get backwards. Neither is a zero: a
# state that does not yet exist and a state whose membership was not recorded are both out of
# the risk set, and counting a transition out of either as an accession manufactures events
# from state birth and from missing data respectively.
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


def audit_igo_causes() -> dict:
    """Termination events by coded cause -- T2's whole event supply.

    The v3 IGO-year file carries `dead`, `integrated`, `replaced`, `sdate` and `deaddate`
    alongside the membership matrix; the v2.3 unit-level file is not needed and using it would
    have spliced two versions together for no gain. `integrated` and `replaced` are modes of
    `dead` rather than alternatives to it, which is what makes the three causes exhaustive and
    mutually exclusive.
    """
    d, _ = _load_igo()
    u = (d.groupby("ionum")
         .agg(name=("ioname", "first"), sdate=("sdate", "first"),
              deaddate=("deaddate", "max"), last=("year", "max"),
              dead=("dead", "max"), integrated=("integrated", "max"),
              replaced=("replaced", "max"))
         .reset_index())
    dd = pd.to_numeric(u.deaddate, errors="coerce")
    terminated = (u.dead == 1) | (u.integrated == 1) | (u.replaced == 1)

    def by_cause(lo: int) -> dict:
        s = u[terminated & (dd >= lo)]
        return {
            "total": int(len(s)),
            # dissolution is the residual: dead, neither integrated nor replaced. Per the v3
            # codebook this is also where dormancy lands, via the ten-year plenary rule -- so
            # this cell is the one carrying rule-assigned dates (manifesto section 9.7).
            "dissolution": int(((s.integrated != 1) & (s.replaced != 1)).sum()),
            "replaced": int((s.replaced == 1).sum()),
            "absorption_integrated": int((s.integrated == 1).sum()),
        }

    m = u[terminated & dd.notna()]
    return {
        "causes_1946plus": by_cause(1946),
        "causes_1965plus": by_cause(1965),
        "deaddate_matches_last_observed_year": int((m["last"] == pd.to_numeric(m.deaddate)).sum()),
        "deaddate_coded_total": int(len(m)),
        "vanish_without_termination_flag_1965_2013":
            int(len(u[(u["last"] < 2014) & (u["last"] >= 1965) & (~terminated)])),
        "note": "dissolution is the cell dated by the ten-year plenary rule, so its dates "
                "consume up to ten years of data after the event (manifesto section 9.7)",
    }


def audit_desta() -> dict:
    """The signature-to-entry-into-force gap: section 6's external anchor on the penumbra.

    Section 6 calls this the closest thing to ground truth the programme has outside synthetics, and
    the round-1 amendment folded it into the likelihood rather than leaving it a side check.
    Measuring it is therefore measuring a quantity P1 is committed against, which is why the
    date this ran is recorded and P1 was not touched afterwards.
    """
    t = pd.read_csv(DESTA, low_memory=False, encoding="latin-1")
    post = t[t.year >= WINDOW_START]
    both = post[post.entryforceyear.notna() & post.year.notna()]
    gap = (both.entryforceyear - both.year).astype(float)
    return {
        "source": "DESTA v02.03 list of treaties",
        "entries_signed_in_window": int(len(post)),
        "by_entry_type": {str(k): int(v) for k, v in post.entry_type.value_counts().items()},
        "codes_entity_termination": False,
        "termination_note": "entry_type has base_treaty / accession / withdrawal / protocol or "
                            "amendment / consolidated. Withdrawal is a MEMBER exit, not an "
                            "agreement termination, so DESTA supplies no T2 entity events",
        "gap_n": int(len(gap)),
        "gap_mean": round(float(gap.mean()), 3),
        "gap_median": float(gap.median()),
        "gap_max": float(gap.max()),
        "gap_ge_1yr_share": round(float((gap >= 1).mean()), 4),
        "gap_ge_2yr_share": round(float((gap >= 2).mean()), 4),
        "gap_ge_3yr_share": round(float((gap >= 3).mean()), 4),
        # Signed and never in force: administrative traces exist, the event never happens. This
        # is a negative class no other source in LEDGER supplies.
        "signed_never_entered_force": int(((t.year >= WINDOW_START)
                                           & t.entryforceyear.isna()).sum()),
    }


def audit_horizon_window() -> dict:
    """Usable forecast origins per horizon. Checks a worry rather than confirming one.

    Relation coverage is CLIQUEBAIT's rebuilt graph (FINDINGS section 4); the event supply ends
    with COW IGO in 2014. The concern was that long horizons would leave too few origins. They
    do not -- the window is 67 years and the horizon only eats from the top. The real
    dependence problem is that one event contributes to every horizon from a different origin,
    so points on a Delta-curve are not independent.
    """
    rel = {"allies": (1946, 2016), "trades": (1948, 2016),
           "votes_with": (1946, 2016), "conflicts_with": (1946, 2014)}
    g_first, g_last = max(lo for lo, _ in rel.values()), min(hi for _, hi in rel.values())
    ev_last = 2014
    return {
        "graph_all_relations": [g_first, g_last],
        "event_supply_ends": ev_last,
        "origins_per_horizon": {str(D): max(0, min(g_last, ev_last - D) - g_first + 1)
                                for D in range(11)},
        "note": "origins are ample at every horizon; the curve points share events, which is a "
                "dependence problem and not a power problem",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--era-start", type=int, default=1965)
    args = ap.parse_args()

    atop, igo = audit_atop(), audit_igo(args.era_start)
    causes, desta, horizon = audit_igo_causes(), audit_desta(), audit_horizon_window()

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

    print("\nT2 event supply - COW IGO terminations by coded cause")
    for lab, key in (("1946+", "causes_1946plus"), ("1965+", "causes_1965plus")):
        c = causes[key]
        print(f"  {lab}  total {c['total']:>4}   dissolution {c['dissolution']:>4}"
              f"   replaced {c['replaced']:>3}   absorption {c['absorption_integrated']:>3}")
    print(f"  deaddate == last observed year: {causes['deaddate_matches_last_observed_year']}"
          f" of {causes['deaddate_coded_total']}")
    print(f"  vanish with no termination flag (1965-2013): "
          f"{causes['vanish_without_termination_flag_1965_2013']}")
    print("  NB dissolution is dated by the ten-year plenary rule -> manifesto 9.7")

    print("\nDESTA - signature to entry-into-force gap (section 6's external anchor)")
    print(f"  n {desta['gap_n']}   mean {desta['gap_mean']}   median {desta['gap_median']}"
          f"   max {desta['gap_max']}")
    print(f"  share >=1yr {desta['gap_ge_1yr_share']}   >=2yr {desta['gap_ge_2yr_share']}"
          f"   >=3yr {desta['gap_ge_3yr_share']}")
    print(f"  signed but never entered force: {desta['signed_never_entered_force']}")
    print(f"  entry types: {desta['by_entry_type']}")
    print(f"  supplies entity terminations: {desta['codes_entity_termination']}")

    print("\nUsable forecast origins per horizon")
    o = horizon["origins_per_horizon"]
    print("  " + "  ".join(f"D{k}={v}" for k, v in o.items()))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"atop": atop, "cow_igo": igo,
                                         "cow_igo_causes": causes, "desta": desta,
                                         "horizon_window": horizon}, indent=2))
        print(f"\nwritten to {args.json}")


if __name__ == "__main__":
    main()

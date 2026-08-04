"""DESTA: preferential trade agreements, and §6's unexecuted validation of $\\Delta^\\star$.

§6 says the signature-to-entry-into-force gap "is a natural experiment on the penumbra and should be
exploited rather than merely noted ... **the closest thing to ground truth the programme will have
outside synthetics**". C7 measured the gap and stopped there. This module supplies what the
measurement was for: a real corpus in which the back-dating width is **externally coded per
agreement**, so $\\Delta^\\star$ can be graded against a known answer outside the synthetic testbed.

The logic. An agreement is signed at $s$ and enters into force at $f$. Its members are legally
members from $f$; administratively they are on the record from $s$. If a relation built from DESTA's
membership carries the dyads from $s$, it back-dates by exactly $f - s$ -- a width the source states
rather than one we infer. That is $\\beta$, per agreement, on real data.

Three things this file refuses to do quietly, all of them recorded in LEDGER.md §1.1 when the entity
type was deferred:

**Non-COW parties are excluded, not force-matched.** Of 204 distinct parties, nine are not COW system
members: Cook Islands, Faroe Islands, Greenland, Hong Kong, Macao, Montserrat, Niue, the Palestinian
Territories and Western Sahara. They sign trade agreements and they are not states. Mapping them onto
whichever state administers them would put edges between a state and itself, or attribute a
territory's trade policy to a metropole.

**The encoding is cp1252, not latin-1.** Three country names carry a right single quotation mark at
byte 0x92, which is undefined in latin-1 and silently becomes a control character. Every other source
in this programme is latin-1, so the difference has to be stated where it will be read.

**The dyads file is not the membership file.** It covers 1,179 of 1,409 entries and omits withdrawals,
protocols and consolidations -- the non-dyadic entry types. Member sets therefore come from the wide
`c1..c91` columns, which cover every entry.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DESTA_DIR = ROOT / "data" / "raw" / "desta"
TREATIES = DESTA_DIR / "desta_list_of_treaties_02_03.csv"
DYADS = DESTA_DIR / "desta_list_of_treaties_02_03_dyads.csv"
COW_CODES = ROOT.parent / "CLIQUEBAIT" / "data" / "raw" / "cow_meta" / "COW-country-codes.csv"

ENCODING = "cp1252"          # NOT latin-1; see the module docstring

# Parties that are not COW system members. Declared and excluded rather than mapped, with the
# reason, because each is a trade party that is not a state.
NON_COW_PARTIES = {
    "Cook Islands": "self-governing in free association with New Zealand",
    "Faroe Islands": "autonomous territory of Denmark",
    "Greenland": "autonomous territory of Denmark",
    "Hong Kong SAR China": "special administrative region; a separate WTO customs territory",
    "Macao SAR China": "special administrative region; a separate WTO customs territory",
    "Montserrat": "British overseas territory",
    "Niue": "self-governing in free association with New Zealand",
    "Palestinian Territories": "not a COW system member in this period",
    "Western Sahara": "disputed, no COW membership",
}

# DESTA's country names that do not normalise onto a COW state name. Each is a decision.
NAME_OVERRIDES = {
    "United States": 2, "Trinidad & Tobago": 52, "St. Vincent & Grenadines": 57,
    "St. Kitts & Nevis": 60, "Bosnia & Herzegovina": 346, "North Macedonia": 343,
    "Serbia": 345,                       # COW keeps 345 across the Serbia-and-Montenegro renaming
    "Czechia": 316, "Eswatini": 572, "Congo - Brazzaville": 484, "Congo - Kinshasa": 490,
    "Myanmar (Burma)": 775, "Timor-Leste": 860, "Micronesia (Federated States of)": 987,
    # These two look like an encoding problem and are not one. COW calls them "Ivory Coast" and
    # "Sao Tome and Principe"; DESTA uses the endonym and an ampersand. Accent-stripping was a real
    # latent bug and fixing it did not fix these, because the names genuinely differ.
    "Côte d’Ivoire": 437,
    "São Tomé & Príncipe": 403,
}
def _norm(s) -> str:
    """Lowercase, strip accents by decomposition, then keep only a-z.

    Stripping accents rather than deleting the accented character matters: without the NFKD pass,
    "Cote d'Ivoire" normalises to "ctedivoire" because the o-circumflex is removed outright, and the
    two names carrying accents in DESTA fail to match COW for a reason that looks like a missing
    country. With it they match automatically and need no override at all.
    """
    dec = unicodedata.normalize("NFKD", str(s))
    return re.sub(r"[^a-z]", "", "".join(c for c in dec
                                         if not unicodedata.combining(c)).lower())


def _cow_name_to_code() -> dict[str, int]:
    with open(COW_CODES, "r", newline="", encoding="utf-8") as fh:
        raw = fh.read()
    recs = [ln for ln in re.split(r"[\r\n]+", raw) if ln.strip()]
    cow = pd.read_csv(StringIO("\n".join(recs)))
    out: dict[str, int] = {}
    for name, code in zip(cow.StateNme, cow.CCode):
        out.setdefault(_norm(name), int(code))
    return out


@lru_cache(maxsize=1)
def party_crosswalk() -> tuple[dict, dict, dict]:
    """(iso_numeric -> COW ccode, name -> ccode, excluded name -> reason).

    Raises if any party is neither mapped nor explicitly excluded, so a new DESTA release cannot
    silently drop a state. That is CLIQUEBAIT's rule -- its ISO/COW crosswalk aborts on ambiguity
    rather than guessing, and it caught a case that would have left Belgium and Luxembourg with no
    trade edges for fifty years.
    """
    d = pd.read_csv(DYADS, low_memory=False, encoding=ENCODING)
    pairs = (pd.concat([d[["country1", "iso1"]].rename(columns={"country1": "nm", "iso1": "num"}),
                        d[["country2", "iso2"]].rename(columns={"country2": "nm", "iso2": "num"})])
             .dropna().drop_duplicates())

    cow = _cow_name_to_code()
    num2cow, name2cow, excluded, unmapped = {}, {}, {}, []
    for nm, num in zip(pairs.nm, pairs.num):
        if nm in NON_COW_PARTIES:
            excluded[nm] = NON_COW_PARTIES[nm]
            continue
        code = NAME_OVERRIDES.get(nm) or cow.get(_norm(nm))
        if code is None:
            unmapped.append(nm)
            continue
        num2cow[int(num)] = int(code)
        name2cow[nm] = int(code)

    if unmapped:
        raise ValueError(
            f"{len(unmapped)} DESTA parties are neither mapped nor declared non-COW: {unmapped}. "
            f"Add to NAME_OVERRIDES with a code or to NON_COW_PARTIES with a reason. A party that "
            f"is silently dropped becomes an agreement with missing members, which reads downstream "
            f"as an agreement that was never cohesive.")

    # Many-to-one is the dangerous direction: two parties mapped to one state would merge them.
    rev: dict[int, list[str]] = {}
    for nm, code in name2cow.items():
        rev.setdefault(code, []).append(nm)
    collisions = {c: ns for c, ns in rev.items() if len(ns) > 1}
    if collisions:
        raise ValueError(f"COW codes claimed by more than one DESTA party: {collisions}")
    return num2cow, name2cow, excluded


def treaties(window=(1946, 2014)) -> pd.DataFrame:
    """Entries with their member sets in COW codes, signature and entry-into-force years.

    `entry_type` distinguishes base_treaty, accession, withdrawal, protocol and consolidated, so an
    accession is a first-class event here rather than something to be inferred from a membership
    panel -- which is what makes DESTA's dating usable as ground truth.
    """
    lo, hi = window
    num2cow, _n2c, _ex = party_crosswalk()
    t = pd.read_csv(TREATIES, low_memory=False, encoding=ENCODING)
    ccols = [f"c{i}" for i in range(1, 92) if f"c{i}" in t.columns]
    mcols = [f"mc{i}" for i in range(1, 92) if f"mc{i}" in t.columns]

    rows = []
    for r in t.itertuples():
        yr = getattr(r, "year", np.nan)
        if pd.isna(yr) or not (lo <= yr <= hi):
            continue
        nums = [getattr(r, c) for c in ccols]
        classes = [getattr(r, m) for m in mcols] if mcols else [np.nan] * len(nums)
        members, acceded, dropped_non_cow = [], [], 0
        for num, cls in zip(nums, classes):
            if pd.isna(num):
                continue
            cc = num2cow.get(int(num))
            if cc is None:
                dropped_non_cow += 1
                continue
            members.append(cc)
            # mc == 2 marks a party that acceded rather than founded, per the observed coding.
            if not pd.isna(cls) and int(cls) == 2:
                acceded.append(cc)
        f = getattr(r, "entryforceyear", np.nan)
        rows.append({
            "number": str(r.number),
            "base_treaty": str(getattr(r, "base_treaty", r.number)),
            "entry_type": str(getattr(r, "entry_type", "")),
            "typememb": getattr(r, "typememb", np.nan),
            "sig_year": int(yr),
            "force_year": (int(f) if not pd.isna(f) else pd.NA),
            "gap": (int(f) - int(yr)) if not pd.isna(f) else pd.NA,
            "never_in_force": bool(pd.isna(f)),
            "members": sorted(set(members)),
            "n_members": len(set(members)),
            "acceded": sorted(set(acceded)),
            "non_cow_parties_dropped": dropped_non_cow,
        })
    return pd.DataFrame(rows)


def summary(window=(1946, 2014)) -> dict:
    num2cow, name2cow, excluded = party_crosswalk()
    t = treaties(window)
    base = t[t.entry_type == "base_treaty"]
    gap = pd.to_numeric(t.gap, errors="coerce").dropna()
    return {
        "encoding": ENCODING,
        "parties_mapped": len(name2cow),
        "parties_excluded_non_cow": {k: v for k, v in excluded.items()},
        "entries_in_window": int(len(t)),
        "by_entry_type": t.entry_type.value_counts().to_dict(),
        "base_treaties": int(len(base)),
        "multilateral_base_treaties": int((base.n_members >= 3).sum()),
        "never_in_force": int(t.never_in_force.sum()),
        "non_cow_party_slots_dropped": int(t.non_cow_parties_dropped.sum()),
        "gap_years": {
            "n": int(len(gap)), "mean": round(float(gap.mean()), 3),
            "median": float(gap.median()), "max": float(gap.max()),
            "distribution": {int(k): int(v) for k, v in gap.value_counts().sort_index().items()},
        },
        "gap_ge_1": round(float((gap >= 1).mean()), 4),
        "gap_ge_2": round(float((gap >= 2).mean()), 4),
    }

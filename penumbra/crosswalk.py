"""COW IGO state columns to COW country codes, validated in both directions.

The IGO year file names states as column headers (`afghanistan`, `wgermany`, `sokorea`) while
ATOP and every node covariate use COW numeric codes. Joining them needs a crosswalk, and the
prior programme's experience is that this is where the silent errors live: CLIQUEBAIT's
ISO-COW crosswalk caught four real ambiguities and three reporters a naive filter would have
discarded, one of which would have left Belgium and Luxembourg with no trade edges for fifty
years.

The rule inherited from that is **abort rather than guess**. This module refuses to return a
partial crosswalk: an unmapped column or a code claimed by two columns raises, because a
crosswalk that silently drops a state produces a coalition with missing members, which reads
downstream as a coalition that was never dense rather than as data that was never joined.

    from penumbra.crosswalk import igo_state_crosswalk
    col2code = igo_state_crosswalk()          # {'usa': 2, 'wgermany': 260, ...}
"""
from __future__ import annotations

import re
from functools import lru_cache
from io import StringIO
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COW_CODES = ROOT.parent / "CLIQUEBAIT" / "data" / "raw" / "cow_meta" / "COW-country-codes.csv"
IGO_YEAR = ROOT / "data" / "raw" / "cow_igo" / "igo_year_formatv3.csv"

# Columns of the IGO year file that describe the organisation, not a state's membership.
IGO_META = frozenset({
    "ioname", "orgname", "year", "longorgname", "ionum", "igocode", "version",
    "accuracyofpre1965membershipdates", "sourcesandnotes", "imputed",
    "political", "social", "economic", "dead", "deaddate", "integrated", "replaced", "sdate",
})

# Hand-mapped columns whose header does not normalise onto a COW state name. Every entry is a
# decision, so every entry is listed rather than pattern-matched: an abbreviation table built
# from regexes is a table nobody can audit. Cases that carry real historical ambiguity are
# commented, because those are the ones a reader will want to check.
MANUAL = {
    "usa": 2, "trinidad": 52, "stvincent": 57, "stkitts": 60,
    "domrepublic": 42, "car": 482, "congobrazz": 484,
    "uk": 200,
    "bavariaelect": 245,        # Bavaria; the Electorate predates the COW state entry
    "hesseelect": 273, "hessegrand": 275, "mecklenburg": 280, "wurtenburg": 271,
    "czechrep": 316,
    "wgermany": 260, "egermany": 265,   # distinct COW states, NOT folded into Germany 255
    "fyromacedonia": 343, "bosnia": 346,
    "yugoslaviaserb": 345,      # COW keeps 345 across the Serbia-and-Montenegro renaming
    "soafrica": 560, "sosudan": 626, "saotome": 403, "eqguinea": 411,
    "zaire": 490,               # same COW state as Democratic Republic of the Congo
    "uae": 696,
    "nyemen": 678, "syemen": 680,       # Yemen Arab Rep. / Yemen People's Rep., both pre-1990
    "nokorea": 731, "sokorea": 732,
    "svietnam": 817,            # Republic of Vietnam; plain `vietnam` maps to 816
    "etimor": 860, "solomonis": 940, "marshallis": 983, "micronesiafs": 987,
    "wsamoa": 990,
}


def _norm(s) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def _cow_name_to_code() -> dict[str, int]:
    # The shipped file has CR-only line endings, so pandas reads it as a single row. Split on
    # either terminator rather than trusting the extension.
    with open(COW_CODES, "r", newline="", encoding="utf-8") as fh:
        raw = fh.read()
    recs = [ln for ln in re.split(r"[\r\n]+", raw) if ln.strip()]
    cow = pd.read_csv(StringIO("\n".join(recs)))
    out: dict[str, int] = {}
    for name, code in zip(cow.StateNme, cow.CCode):
        out.setdefault(_norm(name), int(code))
    return out


def igo_state_columns() -> list[str]:
    header = pd.read_csv(IGO_YEAR, sep="\t", nrows=0, encoding="latin-1").columns
    return [c for c in header if c not in IGO_META]


@lru_cache(maxsize=1)
def igo_state_crosswalk() -> dict[str, int]:
    """{IGO column name -> COW ccode}. Raises if incomplete or many-to-one."""
    name2code = _cow_name_to_code()
    cols = igo_state_columns()

    mapping: dict[str, int] = {}
    unmapped: list[str] = []
    for c in cols:
        if c in MANUAL:
            mapping[c] = MANUAL[c]
        elif _norm(c) in name2code:
            mapping[c] = name2code[_norm(c)]
        else:
            unmapped.append(c)

    if unmapped:
        raise ValueError(
            f"{len(unmapped)} IGO state columns have no COW code and none may be guessed: "
            f"{unmapped}. Add them to MANUAL with a comment, or the states they name will "
            f"vanish from every coalition they belong to.")

    # Many-to-one is the dangerous direction: two columns claiming one code silently merges two
    # states. As of this file there are none -- `zaire` (490) and `congobrazz` (484) are the two
    # that look like a pair and are not one -- so the check is strict. If a successor convention
    # ever produces a legitimate collision, add it here with the evidence rather than widening
    # the test; a tolerated exception that never fires is worse than no test, because it reads
    # as though the case was handled.
    rev: dict[int, list[str]] = {}
    for col, code in mapping.items():
        rev.setdefault(code, []).append(col)
    collisions = {code: cs for code, cs in rev.items() if len(cs) > 1}
    if collisions:
        raise ValueError(
            f"COW codes claimed by more than one IGO column, which would merge distinct "
            f"states: {collisions}. Resolve explicitly; do not let the last write win.")

    stale = sorted(set(MANUAL) - set(cols))
    if stale:
        raise ValueError(f"MANUAL maps columns absent from the IGO file: {stale}. The file has "
                         f"changed and the table is out of date.")
    return mapping


def igo_membership_long(full_only: bool = True) -> pd.DataFrame:
    """Long-format membership: one row per (ionum, year, ccode) where the state is a member.

    `full_only` keeps code 1 (full membership) and drops 2 (associate) and 3 (observer). That
    is a task definition, not a cleaning step: an observer is not a coalition member, but it is
    exactly the kind of pre-accession status the penumbra is about, so the observer rows are
    returned when `full_only=False` and U1 will want them.

    Codes -9 (missing data) and -1 (state not a system member) are never members and never
    non-members either -- they are outside the risk set, per PENUMBRA-OUTCOMES C5.
    """
    col2code = igo_state_crosswalk()
    d = pd.read_csv(IGO_YEAR, sep="\t", low_memory=False, encoding="latin-1")
    cols = list(col2code)
    long = d[["ionum", "year"] + cols].melt(
        id_vars=["ionum", "year"], var_name="state_col", value_name="status")
    long["status"] = pd.to_numeric(long["status"], errors="coerce")
    keep = long.status.isin([1] if full_only else [1, 2, 3])
    long = long[keep].copy()
    long["ccode"] = long.state_col.map(col2code).astype("int64")
    return long[["ionum", "year", "ccode", "status"]].reset_index(drop=True)


if __name__ == "__main__":
    cw = igo_state_crosswalk()
    print(f"ok: {len(cw)} IGO state columns mapped to COW codes "
          f"({len(MANUAL)} by hand, {len(cw) - len(MANUAL)} by name)")
    out = ROOT / "data" / "interim"
    out.mkdir(parents=True, exist_ok=True)
    (pd.DataFrame({"igo_column": list(cw), "ccode": list(cw.values())})
     .sort_values("ccode").to_csv(out / "igo_state_crosswalk.csv", index=False))
    print(f"written to {out / 'igo_state_crosswalk.csv'}")

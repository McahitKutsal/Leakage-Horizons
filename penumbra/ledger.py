"""LEDGER construction: entities, events, membership, risk-set exclusions.

Implements the declarations in `LEDGER.md`, which were written before this file. Where a choice
had to be made that the schema document did not settle, the choice is commented here AND the
schema document is the place it gets recorded -- not the other way round.

Every event carries an interval $(t_L, t_R]$ and a dating stratum, because section 7's likelihood
contributes $S(t_L) - S(t_R)$ and an exactly-dated event is the special case $t_R = t_L + 1$.
Events also carry `knowable_from`, which equals $t_R$ except for stratum 4, where COW IGO's
ten-year plenary rule assigns a date using data from up to a decade later (section 9.7). A width and a
knowability are different things and collapsing them is what section 9.7 exists to prevent.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from penumbra.crosswalk import IGO_YEAR, igo_state_crosswalk

ROOT = Path(__file__).resolve().parents[1]
ATOP_DIR = ROOT.parent / "CLIQUEBAIT" / "data" / "ATOP 5.1 (.csv)"

WINDOW_START, WINDOW_END = 1946, 2014
MIN_MEMBERS = 3          # COW IGO's own inclusion rule; applied to ATOP for comparability

# Dating strata, LEDGER.md section 3. Names rather than integers, so a stratum can never be silently
# compared with a count.
EXACT = "exact"
BRACKETED = "bracketed"
DECLARED = "declared_resolution"
RULE_ASSIGNED = "rule_assigned"

# COW IGO codes an organisation dead once ten consecutive years have passed without a plenary
# session, so a dissolution date is not knowable until a decade after the year it names.
PLENARY_RULE_YEARS = 10

# The Wallace and Singer five-year grid the pre-1965 imputation descends from, anchored at the
# start of the COW state system. An imputed membership change is located only within its block.
WS_GRID_ORIGIN, WS_GRID_STEP = 1815, 5


def _ws_block(year: int) -> tuple[int, int]:
    start = WS_GRID_ORIGIN + WS_GRID_STEP * ((year - WS_GRID_ORIGIN) // WS_GRID_STEP)
    return start, start + WS_GRID_STEP - 1


# ------------------------------------------------------------------------------ COW IGO
def _igo_frame() -> tuple[pd.DataFrame, list[str]]:
    d = pd.read_csv(IGO_YEAR, sep="\t", low_memory=False, encoding="latin-1")
    return d.sort_values(["ionum", "year"]).reset_index(drop=True).copy(), list(igo_state_crosswalk())


def igo_entities() -> pd.DataFrame:
    d, _ = _igo_frame()
    g = (d.groupby("ionum")
         .agg(name=("orgname", "first"), short=("ioname", "first"),
              sdate=("sdate", "first"), deaddate=("deaddate", "max"),
              first_obs=("year", "min"), last_obs=("year", "max"),
              dead=("dead", "max"), integrated=("integrated", "max"),
              replaced=("replaced", "max"), any_imputed=("imputed", "max"),
              accuracy=("accuracyofpre1965membershipdates", "first"))
         .reset_index())

    dd = pd.to_numeric(g.deaddate, errors="coerce")
    terminated = ((g.dead == 1) | (g.integrated == 1) | (g.replaced == 1)) & dd.notna()

    # integrated and replaced are modes of dead rather than alternatives, so dissolution is the
    # residual. Order matters: an entity flagged both would otherwise fall into whichever branch
    # was tested first, and none is, which is checked in validate_ledger.
    cause = np.where(g.integrated == 1, "absorbed",
                     np.where(g.replaced == 1, "replaced", "dissolution"))
    cause = np.where(terminated, cause, None)

    founded = pd.to_numeric(g.sdate, errors="coerce")
    out = pd.DataFrame({
        "entity_id": "igo:" + g.ionum.astype(int).astype(str),
        "entity_type": "organisation",
        "source": "COW IGO v3",
        "source_id": g.ionum.astype(int),
        "name": g.name.fillna(g.short),
        "founded": founded.astype("Int64"),
        "terminated": terminated,
        "term_year": dd.where(terminated).astype("Int64"),
        "term_cause": cause,
        "multilateral": True,                      # COW requires >= 3 members to be listed
        "declared_resolution_flag": (g.any_imputed == 1) | (g.accuracy == "Within 5 years"),
        "first_obs": g.first_obs.astype(int),
        "last_obs": g.last_obs.astype(int),
    })
    return out[(out.last_obs >= WINDOW_START) & (out.first_obs <= WINDOW_END)].reset_index(drop=True)


def igo_membership() -> pd.DataFrame:
    """Long (entity_id, ccode, year, status) for full, associate and observer status.

    Observer and associate are carried because they are the administrative precursor section 1
    describes, and LEDGER.md section 4.1 makes them a covariate rather than an outcome.
    """
    d, cols = _igo_frame()
    col2code = igo_state_crosswalk()
    long = d[["ionum", "year"] + cols].melt(id_vars=["ionum", "year"],
                                            var_name="state_col", value_name="status")
    long["status"] = pd.to_numeric(long["status"], errors="coerce")
    long = long[long.status.isin([1, 2, 3])].copy()
    long["entity_id"] = "igo:" + long.ionum.astype(int).astype(str)
    long["ccode"] = long.state_col.map(col2code).astype("int64")
    long["status"] = long.status.astype("int8")
    return long[["entity_id", "ccode", "year", "status"]].reset_index(drop=True)


def igo_riskset_exclusions() -> pd.DataFrame:
    """Per (entity, year) counts of -9 missing and -1 not-a-system-member. C5's tabulation.

    Recorded so that a coverage defect in the source appears as a shrinking denominator rather
    than as events -- the failure mode C5 exists to name.
    """
    d, cols = _igo_frame()
    M = d[cols].apply(pd.to_numeric, errors="coerce").to_numpy()
    return pd.DataFrame({
        "entity_id": "igo:" + d.ionum.astype(int).astype(str),
        "year": d.year.astype(int),
        "n_missing": (M == -9).sum(axis=1),
        "n_not_system": (M == -1).sum(axis=1),
        "n_full": (M == 1).sum(axis=1),
    })


def igo_membership_events(term_year: dict[str, int] | None = None) -> tuple[pd.DataFrame, dict]:
    """Accession (0 -> 1) and exit (1 -> 0) between consecutive observed years.

    Transitions out of -9 or -1 are not events: the first would manufacture accessions from
    missing data and the second from state birth (C5). Requiring both endpoints to be 0 or 1
    excludes them by construction rather than by a filter that could be forgotten.

    **The interval is bounded by the endpoint that is uncertain, not by the transition year.**
    `imputed` marks a *pre-1965* observation whose value is known only within its Wallace-Singer
    five-year block, so for a transition between y-1 and y the two bounds come from different
    places: t_L from the block containing y-1 when that row is imputed, t_R from the block
    containing y when *that* row is imputed. Applying the block of y to both bounds -- the first
    version of this function did -- pushes t_R up to four years past the transition, and for five
    organisations that put an accession after the year the organisation died. The validation
    caught it; the arithmetic would not have looked wrong in any summary.

    Returns the events and a dict of counts that had to be dropped, so nothing is silent.
    """
    d, cols = _igo_frame()
    col2code = igo_state_crosswalk()
    codes = np.array([col2code[c] for c in cols], dtype=np.int64)
    M = d[cols].apply(pd.to_numeric, errors="coerce").to_numpy()
    yrs, ion = d.year.to_numpy(), d.ionum.to_numpy()
    imputed = pd.to_numeric(d.imputed, errors="coerce").fillna(0).to_numpy()
    last_obs = d.groupby("ionum").year.max().to_dict()
    term_year = term_year or {}

    rows = []
    dropped = {"after_termination": 0, "after_last_observation": 0}
    for i in range(1, len(d)):
        if ion[i] != ion[i - 1] or yrs[i] != yrs[i - 1] + 1:
            continue
        y = int(yrs[i])
        if y < WINDOW_START or y > WINDOW_END:
            continue
        prev, cur = M[i - 1], M[i]
        # Entering full membership from any non-member status is an accession. The first version
        # required prev == 0, which silently excluded the 22 observer-to-member and 2
        # associate-to-member transitions -- and those are the only accessions in the corpus with
        # a visible administrative precursor, which is exactly what section 1 says a penumbra looks
        # like. 24 of 8,398 entries, so the omission changes no published number, but the
        # reasoning it broke was circular: a test for "were acceding states observers first" run
        # on events defined to exclude prior observers can only ever return zero.
        acc = np.isin(prev, [0, 2, 3]) & (cur == 1)
        exi = (prev == 1) & np.isin(cur, [0, 2, 3])
        if not (acc.any() or exi.any()):
            continue

        eid = "igo:" + str(int(ion[i]))
        # COW keeps some organisations in the file after their coded death and goes on updating
        # their membership -- the Francophone Agency is coded dead in 2005, replaced by a
        # successor, and its rows run to 2014 with membership still changing. LEDGER.md section 4.2
        # censors an entity at its termination, so those changes belong to the successor and are
        # not events of this entity. Dropped and counted, never merged.
        ty = term_year.get(eid)
        if ty is not None and y > ty:
            dropped["after_termination"] += int(acc.sum() + exi.sum())
            continue

        lo_imp, hi_imp = bool(imputed[i - 1] == 1), bool(imputed[i] == 1)
        t_L = (max(_ws_block(int(yrs[i - 1]))[0] - 1, WINDOW_START - 1) if lo_imp else y - 1)
        t_R = min(_ws_block(y)[1], WINDOW_END, last_obs[ion[i]]) if hi_imp else y
        if t_R <= t_L:                          # clipping collapsed the interval
            dropped["after_last_observation"] += int(acc.sum() + exi.sum())
            continue
        stratum = DECLARED if (lo_imp or hi_imp) else EXACT

        for kind, mask in (("accession", acc), ("exit", exi)):
            for c in codes[mask]:
                rows.append((eid, kind, int(c), t_L, t_R, stratum, t_R))
    return (pd.DataFrame(rows, columns=["entity_id", "event_type", "ccode",
                                        "t_L", "t_R", "dating_stratum", "knowable_from"]),
            dropped)


# --------------------------------------------------------------------------------- ATOP
def atop_entities() -> pd.DataFrame:
    a = pd.read_csv(ATOP_DIR / "atop5_1a.csv", low_memory=False)
    m = pd.read_csv(ATOP_DIR / "atop5_1m.csv", low_memory=False)
    # **Distinct members, not rows.** ATOP codes a member once per treaty phase, so a bilateral pact
    # with two phases has four rows and a row count admits it under a >= 3 members rule. Measured: 8 of
    # 80 alliance entities were bilateral treaties admitted this way, every one of them 2 members over
    # 2 phases. `MIN_MEMBERS` exists to apply COW IGO's inclusion rule to ATOP for comparability
    # (LEDGER.md section 2), and admitting bilateral treaties breaks precisely that. Same root cause as
    # D-28 -- a phase row is not a member -- found while making V11's numbers reproducible.
    size = m.groupby("atopid").member.nunique().rename("n_members")
    a = a.merge(size, left_on="atopid", right_index=True, how="left")

    # yrexit == 0 and endyr == 0 mean "never ended" in ATOP, not year zero. Treating them as
    # dates empties every ongoing treaty, which reads as "no coalitions after 1946".
    endyr = pd.to_numeric(a.endyr, errors="coerce").replace(0, np.nan)
    terminated = endyr.notna() & (endyr >= WINDOW_START) & (endyr <= WINDOW_END)

    out = pd.DataFrame({
        "entity_id": "atop:" + a.atopid.astype(int).astype(str),
        "entity_type": "alliance",
        "source": "ATOP 5.1",
        "source_id": a.atopid.astype(int),
        "name": "ATOP treaty " + a.atopid.astype(int).astype(str),
        "founded": pd.to_numeric(a.begyr, errors="coerce").astype("Int64"),
        "terminated": terminated,
        "term_year": endyr.where(terminated).astype("Int64"),
        # ATOP's termmode/termcaus vocabulary cannot be read without a codebook this network
        # cannot reach, so terminations are events without causes (LEDGER.md section 2.2).
        "term_cause": np.where(terminated, "uncoded", None),
        "multilateral": (a.n_members >= MIN_MEMBERS).fillna(False),
        "declared_resolution_flag": False,        # ATOP dates carry month and day
        "first_obs": pd.to_numeric(a.begyr, errors="coerce").astype("Int64"),
        "last_obs": endyr.fillna(WINDOW_END).astype(int),
    })
    keep = (out.last_obs >= WINDOW_START) & (out.founded <= WINDOW_END) & out.multilateral
    return out[keep].reset_index(drop=True)


def atop_membership(entity_ids: set[str]) -> pd.DataFrame:
    """Long (entity_id, ccode, year, status), one row per member-year.

    **The union of phase spans, deduplicated.** ATOP codes a member once per treaty phase and phases
    overlap in time, so expanding each row and concatenating gives a member two rows for the same year.
    Measured before the fix: 298 redundant rows over 298 (entity, ccode, year) keys, 596 rows standing in
    duplicate pairs, all alliance, and
    162 of 17,582 (entity, year) cells whose row count exceeded their distinct-member count by a mean
    factor of 1.36 and a maximum of 2.00. Any consumer taking group size as `.size()` -- `t1.py` and
    `t2.py` both did -- read those cells as coalitions up to twice their real size, so `log_size`
    entered T1's ladder and T2's hazard inflated for the multi-phase alliances.

    Third instance of one root cause: a phase row is not a member (D-28, D-31, D-32). Deduplicating
    here rather than in each consumer is deliberate -- the invariant belongs to the corpus, and
    `validate_ledger` now asserts it so a fourth consumer cannot reintroduce the assumption.
    """
    m = pd.read_csv(ATOP_DIR / "atop5_1m.csv", low_memory=False)
    m["entity_id"] = "atop:" + m.atopid.astype(int).astype(str)
    m = m[m.entity_id.isin(entity_ids)].copy()
    yr_in = pd.to_numeric(m.yrent, errors="coerce").replace(0, np.nan)
    yr_out = pd.to_numeric(m.yrexit, errors="coerce").replace(0, np.nan).fillna(WINDOW_END)
    m = m.assign(yr_in=yr_in, yr_out=yr_out).dropna(subset=["yr_in"])

    rows = []
    for r in m.itertuples():
        lo, hi = max(int(r.yr_in), WINDOW_START), min(int(r.yr_out), WINDOW_END)
        for y in range(lo, hi + 1):
            rows.append((r.entity_id, int(r.member), y, 1))
    out = pd.DataFrame(rows, columns=["entity_id", "ccode", "year", "status"])
    return out.drop_duplicates(subset=["entity_id", "ccode", "year"]).reset_index(drop=True)


def atop_membership_events(entity_ids: set[str]) -> pd.DataFrame:
    """Accession and exit events from ATOP, one per (treaty, member) rather than one per row.

    **ATOP codes a member once per treaty PHASE.** A member present in phase 1 and phase 2 has two
    rows with different `yrent`, and the first version of this function emitted an accession for
    every row whose `yrent` postdated the treaty -- so a founder of a multi-phase treaty acquired an
    accession it never had, dated to the phase that began later.

    Measured: of 481 events the row-wise rule produced, **221 (45.9 %)** belonged to members whose
    first entry was at or before the treaty's own start, i.e. founders. In 1965-2014 the corpus
    carried 336 alliance accessions where 177 are correct.

    It was found by `umbra.trace_presence`: focal isolation showed 45.8 % of alliance accessions with
    the member already on the treaty's record a year earlier, and 0.0 % for members with a single
    ATOP row. The diagnostic built to measure back-dating located a defect in the corpus instead,
    which is the more useful thing it could have done.

    The rule now: a member accedes at its **first** entry across phases, and only if that first entry
    postdates the treaty. Later phase rows are continuations. Exits are taken at the last recorded
    exit for the same reason.
    """
    a = pd.read_csv(ATOP_DIR / "atop5_1a.csv", low_memory=False,
                    usecols=["atopid", "begyr"]).set_index("atopid")
    m = pd.read_csv(ATOP_DIR / "atop5_1m.csv", low_memory=False)
    m = m[["atopid", "member", "yrent", "yrexit"]].copy()
    m["entity_id"] = "atop:" + m.atopid.astype(int).astype(str)
    m = m[m.entity_id.isin(entity_ids)]
    m["yrent_c"] = pd.to_numeric(m.yrent, errors="coerce").replace(0, np.nan)
    m["yrexit_c"] = pd.to_numeric(m.yrexit, errors="coerce").replace(0, np.nan)

    g = (m.groupby(["entity_id", "atopid", "member"], as_index=False)
         .agg(first_ent=("yrent_c", "min"), last_exit=("yrexit_c", "max")))
    g["begyr"] = g.atopid.map(a.begyr)

    rows = []
    for r in g.itertuples():
        ent, ext, beg = r.first_ent, r.last_exit, r.begyr
        # Founders are not accessors. Only an entry that postdates the treaty is an accession.
        if pd.notna(ent) and pd.notna(beg) and ent > beg and WINDOW_START <= ent <= WINDOW_END:
            rows.append((r.entity_id, "accession", int(r.member),
                         int(ent) - 1, int(ent), EXACT, int(ent)))
        if pd.notna(ext) and WINDOW_START <= ext <= WINDOW_END:
            rows.append((r.entity_id, "exit", int(r.member),
                         int(ext) - 1, int(ext), EXACT, int(ext)))
    return pd.DataFrame(rows, columns=["entity_id", "event_type", "ccode",
                                       "t_L", "t_R", "dating_stratum", "knowable_from"])


# ------------------------------------------------------------------------------ assembly
def entity_level_events(ent: pd.DataFrame) -> pd.DataFrame:
    """Founding and termination, with the dating stratum each deserves."""
    rows = []
    for r in ent.itertuples():
        if pd.notna(r.founded) and WINDOW_START <= r.founded <= WINDOW_END:
            stratum = DECLARED if r.declared_resolution_flag and r.founded < 1965 else EXACT
            if stratum == DECLARED:
                b0, b1 = _ws_block(int(r.founded))
                t_L, t_R = max(b0 - 1, WINDOW_START - 1), min(b1, WINDOW_END)
            else:
                t_L, t_R = int(r.founded) - 1, int(r.founded)
            rows.append((r.entity_id, "founding", pd.NA, None, t_L, t_R, stratum, t_R))

        if r.terminated and pd.notna(r.term_year):
            y = int(r.term_year)
            # Dissolution is the cause COW dates by the ten-year plenary rule. Its width is one
            # year and its knowability is a decade later -- the distinction section 9.7 turns on.
            if r.term_cause == "dissolution":
                stratum, knowable = RULE_ASSIGNED, y + PLENARY_RULE_YEARS
            else:
                stratum, knowable = EXACT, y
            rows.append((r.entity_id, "termination", pd.NA, r.term_cause,
                         y - 1, y, stratum, knowable))
    return pd.DataFrame(rows, columns=["entity_id", "event_type", "ccode", "cause",
                                       "t_L", "t_R", "dating_stratum", "knowable_from"])


def build() -> dict[str, pd.DataFrame]:
    from penumbra.entities import family_ids, membership_families

    ent = pd.concat([igo_entities(), atop_entities()], ignore_index=True)
    ent["origin"] = np.maximum(ent.founded.fillna(WINDOW_START).astype(int), WINDOW_START)
    ent["left_truncated"] = ent.founded.fillna(WINDOW_START).astype(int) < WINDOW_START
    ent["exit_year"] = np.where(ent.terminated & ent.term_year.notna(),
                                ent.term_year.fillna(WINDOW_END).astype(int), WINDOW_END)
    ent["censored"] = ~ent.terminated

    mem = pd.concat([igo_membership(), atop_membership(set(ent.entity_id))], ignore_index=True)
    mem = mem[(mem.year >= WINDOW_START) & (mem.year <= WINDOW_END)].reset_index(drop=True)

    # **The >= 3 members rule enforced against the data, not taken from the source's claim.** COW IGO
    # states that it lists only organisations with at least three members, and three of its entities do
    # not satisfy that in the observed window: the Regional Cooperation Council carries exactly one
    # coded full member across 2008-2014 with 868 cells at -9, and two pre-window bodies carry none at
    # all. That is C5's failure mode -- a coverage gap in the source presenting as structure -- and an
    # entity with fewer than three members yields no dyads, so no clique statistic, group density or
    # co-membership edge can be computed for it. Section 5.4 is the reason this is checked rather than
    # trusted: what a source records and what it advertises are different facts.
    kept = mem[mem.status == 1].groupby("entity_id").ccode.nunique()
    ok = set(kept[kept >= MIN_MEMBERS].index)
    under = ent[~ent.entity_id.isin(ok)]
    ent = ent[ent.entity_id.isin(ok)].reset_index(drop=True)
    mem = mem[mem.entity_id.isin(ok)].reset_index(drop=True)

    # Families are computed on FULL membership only: an observer does not make two bodies the
    # same coalition, and including observers would merge families through shared observers.
    full = mem[mem.status == 1]
    sets = {(e, y): frozenset(g.ccode) for (e, y), g in full.groupby(["entity_id", "year"],
                                                                    sort=False)}
    years: dict[str, set[int]] = {}
    for (e, y) in sets:
        years.setdefault(e, set()).add(y)
    fams = membership_families(sets, years)
    fmap = family_ids(list(ent.entity_id), fams)
    ent["family_id"] = ent.entity_id.map(fmap)

    term = {r.entity_id: int(r.term_year) for r in ent.itertuples()
            if r.terminated and pd.notna(r.term_year)}
    igo_ev, dropped = igo_membership_events(term_year=term)
    ev = pd.concat([
        entity_level_events(ent),
        igo_ev.assign(cause=None),
        atop_membership_events(set(ent.entity_id)).assign(cause=None),
    ], ignore_index=True)
    ev = ev[["entity_id", "event_type", "ccode", "cause", "t_L", "t_R",
             "dating_stratum", "knowable_from"]]
    ev.insert(0, "event_id", ["ev:" + str(i) for i in range(len(ev))])

    famtab = pd.DataFrame(
        [{"family_id": fmap[e], "entity_id": e} for e in ent.entity_id]
    ).merge(ent.groupby("family_id").size().rename("size"), on="family_id")

    # Membership rows after a coded termination belong to the successor, not to this entity, for
    # the same reason the events do. Trimmed here rather than in the loop so the count is one
    # number rather than scattered.
    exit_map = dict(zip(ent.entity_id, ent.exit_year))
    before = len(mem)
    mem = mem[mem.year <= mem.entity_id.map(exit_map)].reset_index(drop=True)
    dropped["membership_rows_after_exit"] = before - len(mem)

    # Named rather than counted: three is few enough that the names are the more useful record, and a
    # coverage gap that removes an entity should be attributable to the entity.
    dropped["entities_under_min_members"] = int(len(under))
    dropped["entities_under_min_members_named"] = sorted(
        f"{r.entity_id} ({r['name']})" for _, r in under.iterrows())

    return {
        "entities": ent.drop(columns=["declared_resolution_flag"]),
        "events": ev,
        "membership": mem,
        "families": famtab,
        "riskset_exclusions": igo_riskset_exclusions(),
        "_dropped": dropped,
    }

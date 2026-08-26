"""T1: accession as a dyad-level survival problem, and §7's comparison ladder.

The unit is the **(coalition, state) dyad**, at risk from the first year both exist and the state is
not a member, exiting at accession or at the end of observation. Manifesto §4 calls T1 a
"recurrent-event, member-level formulation with an unambiguous risk set"; this builds the risk set
exactly as LEDGER.md §4.1 declares it and treats only the **first** accession per dyad, which is
recorded as a simplification in `count_recurrences` rather than assumed away.

One consequence of using a hazard rather than a per-horizon classifier is worth stating, because it
changes what the horizon curve *is*: a fitted discrete-time hazard supplies **every** horizon from
one fit, through the cumulative incidence
$1 - \\prod_{s=o+1}^{o+\\Delta}(1 - h(s))$. U2 fitted a separate probe per horizon and paid for it in
the shrinking-sample artefact of V1d; the hazard cannot have that artefact, because the sample does
not change with $\\Delta$.

The ladder (§7), each rung capacity-matched and required to beat the one below:

    1  duration dependence alone           -- the base rate, with a baseline in dyad time
    2  + node covariates                   -- candidate state and coalition composition
    3  + densities                         -- the U2 feature set; a BASELINE, not an ablation
    4-7  graph-free MLP, homogeneous, heterogeneous, temporal encoders  -- not built here
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from penumbra.hazard import CENSORED, PeriodPanel

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "ledger"
NODES = (ROOT.parent / "CLIQUEBAIT" / "previous-work-code-base" / "coalition-gnn"
         / "data" / "canonical" / "nodes.parquet")

NODE_COLS = ["cinc", "polity2", "v2x_polyarchy", "v2x_libdem", "v2x_partipdem",
             "log_e_gdppc", "log_e_pop", "log_tpop", "log_milex", "log_milper"]


def _corpus_fingerprint() -> dict:
    """Sizes of the three corpus tables the risk set is derived from.

    Cheap enough to compute on every call -- parquet carries row counts in its footer -- and sufficient
    to catch a rebuild, since none of D-28, D-31 or D-32 left any of the three unchanged.
    """
    import pyarrow.parquet as pq
    out = {}
    for name in ("membership", "events", "entities"):
        f = LEDGER / f"{name}.parquet"
        out[name] = int(pq.ParquetFile(f).metadata.num_rows) if f.exists() else None
    return out


def count_recurrences(events: pd.DataFrame) -> dict:
    """How much the single-event simplification discards.

    A state can leave a coalition and rejoin, which §4's "recurrent-event" wording admits. Treating
    only the first accession per dyad is a simplification and its cost is measured rather than
    asserted to be small.
    """
    acc = events[(events.event_type == "accession") & events.ccode.notna()]
    per_dyad = acc.groupby(["entity_id", "ccode"]).size()
    return {"dyads_with_any_accession": int(len(per_dyad)),
            "dyads_with_more_than_one": int((per_dyad > 1).sum()),
            "accessions_discarded": int((per_dyad - 1).clip(lower=0).sum()),
            "share_discarded": round(float((per_dyad - 1).clip(lower=0).sum() / per_dyad.sum()), 4)}


def build_risk_set(regime=(1965, 2014)) -> pd.DataFrame:
    """The at-risk dyad-year rows, vectorised, cached to parquet.

    Two things the first version got wrong and both mattered.

    **The event period must be in the panel.** A dyad's rows were built by excluding years in which
    the state was already a full member -- but the accession year is exactly such a year, so the
    period in which the event occurs was missing and the interval (d-1, d] covered no row. In
    discrete time the event happens *during* a period that has to be observed. The accession year is
    now appended explicitly as the event period.

    **Speed is not a nicety here.** The Python triple loop took 369s per build and the ladder needs
    several, so the risk set is built by merge and cached. A slow builder gets rebuilt less often
    and tested less often.
    """
    lo, hi = regime
    cache = LEDGER / f"t1_riskset_{lo}_{hi}.parquet"
    stamp = LEDGER / f"t1_riskset_{lo}_{hi}.corpus.json"
    # **The cache is keyed on the corpus, not just the regime.** It was keyed on the regime alone and
    # returned unconditionally, so a corpus rebuild left a stale risk set that the next ladder run would
    # use in silence. The corpus went through four versions on 2026-08-04 and the cache had to be deleted
    # by hand each time; forgetting once would have fitted the ladder to the previous corpus and produced
    # numbers with nothing visibly wrong with them (D-40).
    fp = _corpus_fingerprint()
    if cache.exists():
        prev = None
        if stamp.exists():
            try:
                prev = json.loads(stamp.read_text(encoding="utf-8"))
            except Exception:
                prev = None
        if prev == fp:
            return pd.read_parquet(cache)
        print(f"  risk-set cache is stale ({prev} != {fp}); rebuilding")

    mem = pd.read_parquet(LEDGER / "membership.parquet")
    mem = mem[mem.year.between(lo, hi)]
    full = mem[mem.status == 1][["entity_id", "ccode", "year"]].astype({"ccode": "int32",
                                                                       "year": "int32"})
    ev = pd.read_parquet(LEDGER / "events.parquet")
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna() & ev.t_R.between(lo, hi)]
    first_acc = (acc.assign(ccode=acc.ccode.astype("int32"), year=acc.t_R.astype("int32"))
                 .groupby(["entity_id", "ccode"], as_index=False).year.min()
                 .rename(columns={"year": "acc_year"}))

    # candidate rows: every (entity-year) x (state in the system that year)
    ent_years = full[["entity_id", "year"]].drop_duplicates()
    sys_years = full[["year", "ccode"]].drop_duplicates()
    cand = ent_years.merge(sys_years, on="year")

    # drop years in which the state already holds full membership ...
    cand = cand.merge(full.assign(_m=1), on=["entity_id", "ccode", "year"], how="left")
    cand = cand[cand._m.isna()].drop(columns="_m")
    # ... then restore the accession year, which is the period the event happens in
    cand = cand.merge(first_acc, on=["entity_id", "ccode"], how="left")
    ev_rows = first_acc.rename(columns={"acc_year": "year"}).assign(acc_year=lambda d: d.year)
    cand = pd.concat([cand, ev_rows], ignore_index=True).drop_duplicates(
        ["entity_id", "ccode", "year"])
    # and drop anything after it: the dyad has exited
    cand = cand[cand.acc_year.isna() | (cand.year <= cand.acc_year)]

    cand = cand.sort_values(["entity_id", "ccode", "year"], ignore_index=True)
    cand["dyad"] = cand.groupby(["entity_id", "ccode"], sort=False).ngroup()
    cand["dur"] = cand.groupby("dyad", sort=False).cumcount() + 1
    cache.parent.mkdir(parents=True, exist_ok=True)
    cand.to_parquet(cache, index=False)
    stamp.write_text(json.dumps(fp), encoding="utf-8")
    return cand


OBSERVED_CLOCK = "observed"
ELIGIBILITY_CLOCK = "eligibility"


def _eligibility_clock(cand: pd.DataFrame, regime) -> tuple[pd.Series, np.ndarray]:
    r"""Duration measured from when the state first became eligible, with the truncated part unobserved.

    "Duration in dyad time" was stated and never defined against the coalition's founding, so `dur` was
    `cumcount() + 1`: every dyad starts at 1 in the year it enters the *observed* risk set. Measured on the
    1965-2014 risk set, **19.4 %** of dyads are truncated at the regime start with a median 11 and a
    maximum 150 years of eligibility already elapsed, 41.2 % of rows come from coalitions founded before
    the regime, and **58.4 % of positive dyads** do. Rung 1 is duration dependence *alone* and is the
    baseline every other rung is compared against, so this is the worst place in the ladder for an
    undeclared clock (D-37).

    The two clocks answer different questions and neither is wrong:

    * `observed` -- how long we have watched this dyad not accede. What `cumcount` gives.
    * `eligibility` -- how long the state has been able to join this coalition, which begins at
      $\max(\text{founded}, \text{state's first system year}, \text{window start})$. A state independent
      in 1960 was not eligible in 1900, so the state's own entry bounds it.

    Under the second, a truncated dyad enters observation at a positive age and `PeriodPanel.entry`
    carries the offset, which is what that field is for. Returns the per-row duration and the per-dyad
    entry offset.
    """
    lo = regime[0]
    # Eligibility needs BOTH parties to exist, so it is a maximum over three dates, not a minimum. An
    # earlier version wrote `min(max(founded, 1946), first_observed)`, which made a state independent in
    # 1975 eligible from a 1950 founding -- the docstring said max and the code said min, and it inflated
    # the truncated set from 19 % of dyads to 55 %. The state's own entry is the binding constraint for
    # most post-colonial states and it has to be read over the full window: inside the 1965-2014 risk set
    # every state that predates the regime looks like it entered in 1965.
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    state_entry = mem.groupby("ccode").year.min()

    g = cand.groupby("dyad", sort=False)
    founded = g.entity_founded.min().fillna(lo).astype(int)
    ccode = g.ccode.first().astype(int)
    first_obs = g.year.min().astype(int)

    elig = np.maximum(np.maximum(founded.to_numpy(), 1946),
                      ccode.map(state_entry).fillna(1946).to_numpy().astype(int))
    # Observation cannot begin before eligibility, and in practice begins at the regime start or at the
    # dyad's first row, whichever is later. Clipping at `elig` keeps `period > entry` for every row,
    # which is the invariant PeriodPanel refuses to build without.
    obs = np.maximum(elig, np.minimum(first_obs.to_numpy(), np.maximum(elig, lo)))
    elig_by_dyad = pd.Series(elig, index=founded.index)
    dur = cand.year.to_numpy() - cand.dyad.map(elig_by_dyad).to_numpy() + 1
    entry = (obs - elig).astype(int)
    return pd.Series(dur, index=cand.index), entry


def build_panel(regime=(1965, 2014), rung: int = 3, phi_features: pd.DataFrame | None = None,
                clock: str = OBSERVED_CLOCK):
    """Assemble the dyad-period panel for a given rung.

    Returns `(panel, meta)`. `period` is **duration in dyad time**, so §7's rung 1 is duration
    dependence; the calendar year rides in `meta` because rolling-origin evaluation and the
    determinacy rule need it. Keeping both is not redundancy -- conflating them is how a duration
    model silently becomes a calendar model.

    `clock` selects what "dyad time" means; see `_eligibility_clock`. The default stays `observed`
    because that is what V5 was measured on and changing a default silently would move a published
    number, and D-37 reports the ladder under both so the rung ordering can be checked for invariance
    rather than assumed.
    """
    if clock not in (OBSERVED_CLOCK, ELIGIBILITY_CLOCK):
        raise ValueError(f"unknown clock {clock!r}")
    cand = build_risk_set(regime)
    n_dyads = int(cand.dyad.max()) + 1

    entry = np.zeros(n_dyads, dtype=int)
    if clock == ELIGIBILITY_CLOCK:
        if "entity_founded" not in cand.columns:
            ent = pd.read_parquet(LEDGER / "entities.parquet")[["entity_id", "founded"]]
            cand = cand.merge(ent.rename(columns={"founded": "entity_founded"}),
                              on="entity_id", how="left")
        cand = cand.assign(dur=_eligibility_clock(cand, regime)[0].to_numpy())
        entry = _eligibility_clock(cand, regime)[1]

    last = cand.groupby("dyad").agg(dur_max=("dur", "max"), acc=("acc_year", "max"),
                                    y_last=("year", "max"))
    tL = np.zeros(n_dyads, dtype=int)
    tR = np.zeros(n_dyads, dtype=int)
    cause = np.full(n_dyads, CENSORED)
    has_ev = last.acc.notna().to_numpy()
    tR[:] = last.dur_max.to_numpy()
    tL[has_ev] = last.dur_max.to_numpy()[has_ev] - 1
    # A censored dyad's t_L is ignored; an event dyad's must sit at or after its entry offset, or the
    # interval would reach into periods before the dyad was observed.
    tL = np.maximum(tL, entry)
    cause[has_ev] = 1

    X_parts, names = [], []
    if rung >= 2:
        nodes = pd.read_parquet(NODES)[["year", "cow_code"] + NODE_COLS]
        j = cand.merge(nodes, left_on=["year", "ccode"], right_on=["year", "cow_code"], how="left")
        X_parts.append(j[NODE_COLS].to_numpy(float))
        names += [f"cand_{c}" for c in NODE_COLS]
        mem = pd.read_parquet(LEDGER / "membership.parquet")
        size = (mem[mem.status == 1].groupby(["entity_id", "year"]).size()
                .rename("coalition_size").reset_index())
        j2 = cand.merge(size, on=["entity_id", "year"], how="left").coalition_size.fillna(0)
        X_parts.append(np.column_stack([j2.to_numpy(float), np.log1p(j2.to_numpy(float))]))
        names += ["coalition_size", "log_coalition_size"]
    if rung >= 3:
        if phi_features is None:
            raise ValueError("rung 3 needs phi_features")
        m = cand.merge(phi_features, on=["entity_id", "ccode", "year"], how="left")
        cols = [c for c in phi_features.columns if c.startswith(("phi_", "clique_"))]
        X_parts.append(m[cols].to_numpy(float))
        names += cols

    X = np.column_stack(X_parts) if X_parts else np.zeros((len(cand), 1))
    if X_parts:
        # A missing covariate is not zero. Mean-impute and carry an indicator, so the model can
        # learn that the record was absent rather than that the value was average.
        miss = np.isnan(X)
        if miss.any():
            X = np.where(miss, np.nanmean(X, axis=0), X)
            keep = miss.any(axis=0)
            X = np.column_stack([X, miss[:, keep].astype(float)])
            names += [f"missing_{names[k]}" for k in np.nonzero(keep)[0]]
        sd = X.std(axis=0)
        X = (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0)

    panel = PeriodPanel(entity=cand.dyad.to_numpy(), period=cand.dur.to_numpy(), X=X,
                        entry=entry, t_L=tL, t_R=tR, cause=cause)
    meta = {"year": cand.year.to_numpy(), "feature_names": names,
            "n_rows": len(cand), "n_dyads": n_dyads,
            "n_events": int((cause != CENSORED).sum()), "rung": rung, "regime": list(regime)}
    return panel, meta


def cumulative_incidence(hazards: np.ndarray, horizons: list[int]) -> dict:
    """P(event within Delta periods) from a per-period hazard sequence.

    This is what makes the hazard formulation immune to V1d's artefact: one fit yields every
    horizon, so the sample does not shrink as the horizon grows and a high-capacity model cannot
    manufacture decay by overfitting the far end.
    """
    h = np.clip(hazards, 1e-12, 1 - 1e-12)
    out = {}
    for d in horizons:
        s = np.cumprod(1.0 - h[:, :d], axis=1)[:, -1] if h.ndim == 2 else (1.0 - h) ** d
        out[d] = 1.0 - s
    return out

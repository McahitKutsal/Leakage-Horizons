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
    if cache.exists():
        return pd.read_parquet(cache)

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
    return cand


def build_panel(regime=(1965, 2014), rung: int = 3, phi_features: pd.DataFrame | None = None):
    """Assemble the dyad-period panel for a given rung.

    Returns `(panel, meta)`. `period` is **duration in dyad time**, so §7's rung 1 is duration
    dependence; the calendar year rides in `meta` because rolling-origin evaluation and the
    determinacy rule need it. Keeping both is not redundancy -- conflating them is how a duration
    model silently becomes a calendar model.
    """
    cand = build_risk_set(regime)
    n_dyads = int(cand.dyad.max()) + 1

    last = cand.groupby("dyad").agg(dur_max=("dur", "max"), acc=("acc_year", "max"),
                                    y_last=("year", "max"))
    tL = np.zeros(n_dyads, dtype=int)
    tR = np.zeros(n_dyads, dtype=int)
    cause = np.full(n_dyads, CENSORED)
    has_ev = last.acc.notna().to_numpy()
    tR[:] = last.dur_max.to_numpy()
    tL[has_ev] = last.dur_max.to_numpy()[has_ev] - 1
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
                        entry=np.zeros(n_dyads, dtype=int), t_L=tL, t_R=tR, cause=cause)
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

"""UMBRA: the lagged extension of the CLIQUEBAIT D-series.

U1 is the leakage-horizon curve and U2 the horizon-resolved shortcut probe. Both take an event
corpus and an observation graph in LEDGER's column names, so the synthetic corpus and the real one
go through one code path -- which is what section 11's claim that the contribution is the instrument has
to rest on.

Three things differ from the zero-lag D-series and each is forced rather than chosen.

**The comparison group has to be declared.** At a horizon, "no event" is ambiguous in a way it is
not at zero lag: a state acceding at $t+1$ is a non-event for $\\Delta = 3$ and already carries the
back-dated traces the statistic looks for. Both strata of section 5.1 are computed -- *never-event* is the
estimand, *not-at-this-horizon* is what a naive implementation produces, and the gap between them
is contamination the horizon formulation introduces and the zero-lag one cannot have.

**Density is generalised to a level.** $\\phi_r(S; k)$ is the share of $S$'s dyads whose weight is
at least $k$, so a clique at level $k$ is a group every dyad of which shares at least $k$
organisations. At $k = 1$ this is exactly the manifesto's $\\phi_r(S)$; the generalisation exists
because co-membership -- the relation that must carry the leak for four fifths of LEDGER -- has
density 0.995 and is useless as a binary relation (LEDGER.md section 6.2).

**$\\Delta^\\star$ is an interval.** Bracketed below by the clique contrast, which is specific and
insensitive, and above by rank position together with $\\phi$-alone AUC, which are sensitive and
non-specific. Both bounds are relative to a band set by relations declared not to leak, and naming
those anchors is the caller's job because no statistic can do it (section 5.4).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

__all__ = ["HorizonAudit", "delta_star", "NEVER_EVENT", "NOT_AT_HORIZON"]

NEVER_EVENT = "never_event"
NOT_AT_HORIZON = "not_at_this_horizon"


@dataclass(frozen=True)
class _Key:
    relation: str
    year: int


class HorizonAudit:
    """U1 and U2 over an event corpus and a multi-relational observation graph.

    Parameters
    ----------
    edges : DataFrame [relation, year, cow_i, cow_j, weight]
    membership : DataFrame [entity_id, ccode, year, status]  -- full members define the group
    events : DataFrame [entity_id, event_type, ccode, t_L, t_R, ...]
    """

    def __init__(self, edges: pd.DataFrame, membership: pd.DataFrame, events: pd.DataFrame,
                 full_status: int = 1):
        self.relations = list(dict.fromkeys(edges.relation))
        nodes = pd.unique(pd.concat([edges.cow_i, edges.cow_j, membership.ccode],
                                    ignore_index=True))
        self._ix = {int(n): i for i, n in enumerate(nodes)}
        self._n = len(nodes)

        # Pack each undirected dyad into one int64 and hold a sorted array per (relation, year).
        # Sets of tuples cost >100 bytes an edge, which is fine for tens of thousands and fatal
        # for the 790k of co-membership; searchsorted also lets a whole group be tested at once.
        self._keys: dict[tuple, np.ndarray] = {}
        self._wts: dict[tuple, np.ndarray] = {}
        ui = edges.cow_i.map(self._ix).to_numpy(np.int64)
        vi = edges.cow_j.map(self._ix).to_numpy(np.int64)
        lo, hi = np.minimum(ui, vi), np.maximum(ui, vi)
        packed = lo * np.int64(self._n) + hi
        w = edges.weight.to_numpy(np.int64) if "weight" in edges else np.ones(len(edges), np.int64)
        frame = pd.DataFrame({"r": edges.relation.to_numpy(), "y": edges.year.to_numpy(),
                              "k": packed, "w": w})
        for (r, y), g in frame.groupby(["r", "y"], sort=False):
            order = np.argsort(g.k.to_numpy(), kind="stable")
            self._keys[(r, int(y))] = g.k.to_numpy()[order]
            self._wts[(r, int(y))] = g.w.to_numpy()[order]

        full = membership[membership.status == full_status]
        self._members: dict[tuple, np.ndarray] = {
            (e, int(y)): np.sort(g.ccode.to_numpy())
            for (e, y), g in full.groupby(["entity_id", "year"], sort=False)}
        self._member_years: dict[str, set[int]] = {}
        for (e, y) in self._members:
            self._member_years.setdefault(e, set()).add(y)

        self.events = events
        self._years = sorted({int(y) for (_r, y) in self._keys})

    # ------------------------------------------------------------------ densities
    def _pack(self, members: np.ndarray) -> np.ndarray:
        ids = np.array([self._ix[int(m)] for m in members if int(m) in self._ix], np.int64)
        if ids.size < 2:
            return np.empty(0, np.int64)
        ids = np.sort(ids)
        i, j = np.triu_indices(ids.size, 1)
        return ids[i] * np.int64(self._n) + ids[j]

    def phi(self, members, year: int, relation: str, level: int = 1) -> float:
        """Share of the group's dyads present in `relation` at `year` with weight >= level.

        A group whose members are entirely absent from the graph returns NaN rather than 0: no
        data is not the same as no leakage, and scoring it zero reads as the latter.
        """
        keys = self._pack(np.asarray(members))
        if keys.size == 0:
            return np.nan
        arr = self._keys.get((relation, year))
        if arr is None or arr.size == 0:
            return 0.0
        pos = np.searchsorted(arr, keys)
        pos = np.clip(pos, 0, arr.size - 1)
        hit = arr[pos] == keys
        if level <= 1:
            return float(hit.sum() / keys.size)
        wts = self._wts[(relation, year)][pos]
        return float((hit & (wts >= level)).sum() / keys.size)

    # ------------------------------------------------------------------------ U1
    def accession_panel(self, horizon: int, negatives: str = NEVER_EVENT,
                        max_neg_per_pos: int = 4, seed: int = 0) -> pd.DataFrame:
        """Candidate (entity, state, year) rows for one horizon, labelled.

        The risk set at `year` is states not already full members of the entity. Positives are
        those acceding at `year + horizon`. Negatives depend on the declared stratum:

        * `never_event`   -- the state never accedes to that entity anywhere in the window. This
          is the estimand, because it is the only stratum with no back-dated traces in it.
        * `not_at_this_horizon` -- the full complement, so a state acceding at a *different*
          horizon counts as a negative. This is what a naive implementation computes, and it
          carries exactly the traces the statistic is trying to detect.

        Negatives are subsampled at a declared rate with a fixed seed, because the full risk set
        is entities x states x years and the audit would otherwise cost more than the models.
        """
        if negatives not in (NEVER_EVENT, NOT_AT_HORIZON):
            raise ValueError(f"unknown negative stratum {negatives!r}")
        rng = np.random.default_rng(seed)

        acc = self.events[(self.events.event_type == "accession") & self.events.ccode.notna()]
        # (entity, state) -> every year it acceded, so both strata can be built from one pass
        joined: dict[tuple, set[int]] = {}
        for r in acc.itertuples():
            joined.setdefault((r.entity_id, int(r.ccode)), set()).add(int(r.t_R))

        rows = []
        for (eid, cc), years in joined.items():
            for y in years:
                t = y - horizon
                if t not in self._member_years.get(eid, ()):     # entity must exist at t
                    continue
                ms = self._members.get((eid, t))
                if ms is None or cc in set(ms.tolist()):
                    continue                                     # already a member: not at risk
                rows.append((eid, cc, t, 1))

        # Negatives: draw (entity, state, year) triples from the risk set under the stratum.
        ent_years = [(e, y) for (e, y) in self._members]
        all_states = sorted({int(c) for ms in self._members.values() for c in ms})
        n_neg = int(len(rows) * max_neg_per_pos)
        tries, made = 0, 0
        while made < n_neg and tries < 40 * n_neg:
            tries += 1
            eid, t = ent_years[int(rng.integers(len(ent_years)))]
            cc = all_states[int(rng.integers(len(all_states)))]
            ms = self._members.get((eid, t))
            if ms is None or cc in set(ms.tolist()):
                continue
            ys = joined.get((eid, cc), set())
            if negatives == NEVER_EVENT and ys:
                continue
            if negatives == NOT_AT_HORIZON and (t + horizon) in ys:
                continue
            rows.append((eid, cc, t, 0))
            made += 1

        panel = pd.DataFrame(rows, columns=["entity_id", "ccode", "year", "label"])
        panel.attrs["negative_stratum"] = negatives
        panel.attrs["horizon"] = horizon
        return panel

    def u1_curve(self, horizons=range(0, 11), levels=(1,), negatives: str = NEVER_EVENT,
                 max_neg_per_pos: int = 4, seed: int = 0) -> pd.DataFrame:
        """omega_r(Delta), the clique contrast, and phi-alone AUC, per relation per horizon."""
        out = []
        for h in horizons:
            panel = self.accession_panel(h, negatives, max_neg_per_pos, seed)
            if panel.empty or panel.label.nunique() < 2:
                continue
            groups = [np.append(self._members[(r.entity_id, r.year)], r.ccode)
                      for r in panel.itertuples()]
            for rel in self.relations:
                for k in levels:
                    vals = np.array([self.phi(g, y, rel, k)
                                     for g, y in zip(groups, panel.year)], float)
                    ok = ~np.isnan(vals)
                    y_ = panel.label.to_numpy()[ok]
                    v_ = vals[ok]
                    if y_.size == 0 or len(np.unique(y_)) < 2:
                        continue
                    pos, neg = v_[y_ == 1], v_[y_ == 0]
                    cl_pos = float((pos >= 1 - 1e-9).mean())
                    cl_neg = float((neg >= 1 - 1e-9).mean())
                    out.append({
                        "horizon": h, "relation": rel, "level": k,
                        "negative_stratum": negatives,
                        "n_pos": int(y_.sum()), "n_neg": int((1 - y_).sum()),
                        "omega": float(pos.mean()), "base_rate": float(neg.mean()),
                        "contrast": float(pos.mean() - neg.mean()),
                        "clique_rate_pos": cl_pos, "clique_rate_neg": cl_neg,
                        "clique_contrast": cl_pos - cl_neg,
                        "auc_phi_alone": float(roc_auc_score(y_, v_)),
                    })
        return pd.DataFrame(out)


def _cp_upper_zero(n: int, conf: float = 0.95) -> float:
    """Clopper-Pearson one-sided upper limit for 0 successes in n.

    The band's edge cannot be the anchors' point estimate. A non-leaking relation has a true
    clique contrast of zero and an observed one of order 1/n, so a knife-edge band at the
    anchors' maximum is a threshold that finite-sample noise can never satisfy -- the first
    version of this function used one and returned "never reached" at every beta on a synthetic
    corpus where the signal collapses exactly on cue. The band has to be the largest value a
    genuinely zero-contrast relation could show at this sample size, which is this bound.
    """
    return 1.0 - (1.0 - conf) ** (1.0 / max(n, 1)) if n > 0 else 1.0


def _auc_null_sd(n_pos: int, n_neg: int) -> float:
    """SD of AUC under no association, for widening the phi-alone band the same way."""
    if n_pos < 1 or n_neg < 1:
        return 0.5
    return float(np.sqrt((n_pos + n_neg + 1) / (12.0 * n_pos * n_neg)))


def delta_star(curve: pd.DataFrame, rstar: str, anchors: list[str],
               level: int | None = None, conf: float = 0.95, z: float = 1.645) -> dict:
    """Bracket $\\Delta^\\star$ between two statistics with opposite error profiles.

    `anchors` are the relations declared not to leak. No statistic can identify them -- section 5.4 --
    so the caller names them and the band is whatever they span.

    * `lo` -- the smallest horizon at which r*'s **clique contrast** enters the band. Specific and
      insensitive, so it declares the penumbra closed early: a lower bound. P1 is tested here.
    * `hi` -- the smallest horizon at which r* additionally loses top rank on clique contrast
      **and** its phi-alone AUC enters the band. Both are sensitive and fire on relations that
      merely predict, so this declares it closed late: an upper bound. P2 is tested here.

    Returns None for a bound never reached inside the horizons supplied, which is itself a
    result: an unreachable `hi` falsifies P2 for an instrumental reason and must be reported as
    that rather than as a wide penumbra.
    """
    c = curve if level is None else curve[curve.level == level]
    horizons = sorted(c.horizon.unique())
    lo = hi = None
    detail = []
    for h in horizons:
        sub = c[c.horizon == h].set_index("relation")
        if rstar not in sub.index:
            continue
        anc = [a for a in anchors if a in sub.index]
        if not anc:
            raise ValueError(f"none of the declared anchors {anchors} appear at horizon {h}")
        # The band is the anchors' maximum widened by the noise a zero-contrast relation carries
        # at this sample size, not the anchors' point estimate. Both widths are derived, not
        # chosen, which is what §5.1's "set on the synthetic testbed, not by eye" requires.
        n_pos = int(sub.loc[rstar, "n_pos"])
        n_neg = int(sub.loc[rstar, "n_neg"])
        band_cc = float(sub.loc[anc, "clique_contrast"].max()) + _cp_upper_zero(n_pos, conf)
        band_auc = (float(sub.loc[anc, "auc_phi_alone"].max())
                    + z * _auc_null_sd(n_pos, n_neg))
        cc = float(sub.loc[rstar, "clique_contrast"])
        auc = float(sub.loc[rstar, "auc_phi_alone"])
        top = sub["clique_contrast"].idxmax() == rstar
        in_lo = cc <= band_cc
        in_hi = (not top) and auc <= band_auc
        if lo is None and in_lo:
            lo = int(h)
        if hi is None and in_hi:
            hi = int(h)
        detail.append({"horizon": int(h), "clique_contrast": cc, "band_clique_contrast": band_cc,
                       "auc_phi_alone": auc, "band_auc": band_auc, "rstar_is_top": bool(top),
                       "in_band_lo": bool(in_lo), "in_band_hi": bool(in_hi)})
    return {"delta_star_lo": lo, "delta_star_hi": hi,
            "width": (hi - lo) if (lo is not None and hi is not None) else None,
            "rstar": rstar, "anchors": anchors, "level": level, "detail": detail}

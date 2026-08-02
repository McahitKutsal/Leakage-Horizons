"""
Target-relation leakage diagnostics: a domain-agnostic implementation of D1-D4.

Operates on a `(graph, groups, labels)` triple and knows nothing about any domain. Node ids
are any hashable; time is optional (pass `time=None` throughout for a static graph).

    from cliquebait.diagnostics import LeakageAudit

    audit = LeakageAudit(edges=edge_df, groups=group_df)   # long-format frames
    audit.d4_provenance()                                  # omega_r + contrast + lift
    audit.d1_shortcut(train_mask, test_mask)               # shortcut sufficiency
    audit.d3_curve(budgets=[1,2,3,4], universe=universe)   # negative-difficulty curve
    audit.d2_gap(fit_predict)                              # leakage gap, both halves

Two design choices come out of applying this to a real leaky benchmark, and both matter:

1. **omega alone mislabels r*.** In the IR case trade has the highest omega (0.867) but a
   4x clique lift, while alliances have omega 0.711 and a 570x lift -- the ranking by omega
   is the reverse of the ranking by discriminative power. `d4_provenance` therefore reports
   omega alongside a contrast and a lift, and `suspect_relation()` ranks on lift, not omega.

2. **A linear D1 probe badly understates the shortcut** (0.839 vs 0.979 on identical
   features) because the leak is a clique-indicator effect, not a linear one. The default
   probe is gradient boosting over densities *and* clique indicators.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Callable, Hashable, Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler

__all__ = ["LeakageAudit", "Group"]

_NO_TIME = "__static__"


@dataclass(frozen=True)
class Group:
    """A candidate group: a set of nodes at a time, with a binary label."""
    members: tuple
    label: int
    time: Hashable = _NO_TIME
    meta: dict = field(default_factory=dict, compare=False)

    def dyads(self):
        return combinations(sorted(self.members, key=repr), 2)

    @property
    def size(self):
        return len(self.members)


def _norm_pair(u, v):
    return (u, v) if repr(u) <= repr(v) else (v, u)


class LeakageAudit:
    """Computes D1-D4 for a `(graph, groups, labels)` triple.

    Parameters
    ----------
    edges : DataFrame with columns [relation, u, v] and optionally [time].
        Treated as undirected; duplicates and self-loops are dropped.
    groups : DataFrame with columns [members, label] and optionally [time, group_id].
        `members` holds an iterable of node ids (or a comma-separated string).
    """

    def __init__(self, edges: pd.DataFrame, groups: pd.DataFrame):
        # groups first: the node universe must include members that carry no edges at all,
        # otherwise an isolated member silently leaves the denominator and phi is inflated.
        # An isolated member's dyads are misses, not absences.
        self.groups = self._index_groups(groups)
        self._index_edges(edges)
        self._phi = None

    # ------------------------------------------------------------------ ingest
    def _index_edges(self, edges: pd.DataFrame):
        """Index edges as sorted int64 key arrays, one per (relation, time).

        Sets of Python tuples cost >100 bytes an edge, which is fine for a graph with tens of
        thousands of edges and fatal for one with millions (a STRING channel alone runs to
        seven figures). Packing each undirected dyad into one int64 and holding a sorted array
        costs 8 bytes and lets membership be tested for a whole group at once with
        `searchsorted`.
        """
        if "relation" not in edges.columns:
            raise ValueError("edges needs a 'relation' column")
        for c in ("u", "v"):
            if c not in edges.columns:
                raise ValueError(f"edges needs a '{c}' column")
        e = edges
        has_time = "time" in e.columns
        member_nodes = pd.Series(
            [m for g in getattr(self, "groups", []) for m in g.members], dtype=object)
        nodes = pd.unique(pd.concat([e["u"], e["v"], member_nodes], ignore_index=True))
        self._node_id = {n: i for i, n in enumerate(nodes)}
        self._n_nodes = len(nodes)

        ui = e["u"].map(self._node_id).to_numpy(np.int64)
        vi = e["v"].map(self._node_id).to_numpy(np.int64)
        keep = ui != vi
        ui, vi = ui[keep], vi[keep]
        lo, hi = np.minimum(ui, vi), np.maximum(ui, vi)
        keys = lo * np.int64(self._n_nodes) + hi

        rel = e["relation"].to_numpy()[keep]
        tim = (e["time"].to_numpy()[keep] if has_time
               else np.full(keys.shape, _NO_TIME, dtype=object))

        self._edge_keys = {}
        idx = pd.DataFrame({"rel": rel, "time": tim, "key": keys})
        for (r, t), g in idx.groupby(["rel", "time"], sort=False):
            self._edge_keys[(r, t)] = np.unique(g["key"].to_numpy(np.int64))
        self.relations = list(dict.fromkeys(e["relation"]))

    def _dyad_keys(self, members):
        """int64 keys for every dyad of `members`; unmapped nodes yield no key."""
        ids = [self._node_id[m] for m in members if m in self._node_id]
        if len(ids) < 2:
            return np.empty(0, np.int64), 0
        arr = np.array(sorted(ids), np.int64)
        i, j = np.triu_indices(len(arr), 1)
        return arr[i] * np.int64(self._n_nodes) + arr[j], len(arr)

    def _count_hits(self, keys, rel, t):
        arr = self._edge_keys.get((rel, t))
        if arr is None or not keys.size:
            return 0
        pos = np.searchsorted(arr, keys)
        pos = np.clip(pos, 0, arr.size - 1)
        return int((arr[pos] == keys).sum())

    @staticmethod
    def _index_groups(groups: pd.DataFrame) -> list[Group]:
        if "members" not in groups.columns or "label" not in groups.columns:
            raise ValueError("groups needs 'members' and 'label' columns")
        out = []
        for i, r in enumerate(groups.itertuples()):
            m = r.members
            if isinstance(m, str):
                m = [x.strip() for x in m.split(",") if x.strip()]
            m = tuple(m)
            if len(m) < 2:
                continue
            meta = {k: getattr(r, k) for k in groups.columns
                    if k not in ("members", "label", "time")}
            meta.setdefault("group_id", getattr(r, "group_id", i))
            out.append(Group(members=m, label=int(r.label),
                             time=getattr(r, "time", _NO_TIME), meta=meta))
        return out

    # ------------------------------------------------------------- core stats
    def densities(self) -> pd.DataFrame:
        """phi_r(S) = |Pi(S) ∩ E_t^r| / |Pi(S)| for every group and relation.

        Denominator is over dyads of the members that exist in the graph; a group whose
        members are entirely absent is dropped from the count rather than scored as zero,
        which would otherwise read as "no leakage" when it means "no data".
        """
        if self._phi is not None:
            return self._phi
        rows = []
        for i, g in enumerate(self.groups):
            keys, k_mapped = self._dyad_keys(g.members)
            row = {"idx": i, "label": g.label, "time": g.time, "size": g.size,
                   "size_in_graph": k_mapped}
            row.update(g.meta)                      # metadata usable for stratification
            row.setdefault("group_id", i)
            n = keys.size
            for rel in self.relations:
                row[f"phi_{rel}"] = (self._count_hits(keys, rel, g.time) / n) if n else np.nan
            rows.append(row)
        self._phi = pd.DataFrame(rows)
        return self._phi

    # ------------------------------------------------------------------- D4
    def d4_provenance(self, positive_label: int = 1,
                      negative_stratum: str | None = None) -> pd.DataFrame:
        """Provenance audit.

        omega_r is the manifesto's definition. It is NOT sufficient on its own: a dense
        relation scores a high omega with no discriminative power. `contrast` and `lift`
        are what identify r*.

        `negative_stratum` restricts the comparison group to one kind of negative, given as
        "column=value" against the group metadata (e.g. "neg_type=hard"). The contrast and
        lift depend strongly on which negatives they are measured against, so a reported
        lift is only interpretable alongside the stratum it was computed on.
        """
        phi = self.densities()
        pos = phi.label == positive_label
        neg = ~pos
        if negative_stratum:
            col, _, val = negative_stratum.partition("=")
            if col not in phi.columns:
                raise ValueError(f"group metadata has no column {col!r}; "
                                 f"available: {sorted(phi.columns)}")
            neg = neg & (phi[col].astype(str) == val)
            if not neg.any():
                raise ValueError(f"no negatives match {negative_stratum!r}")
        rows = []
        for rel in self.relations:
            c = phi[f"phi_{rel}"]
            omega = c[pos].mean()
            base = c[neg].mean()
            cl_pos = (c[pos] >= 1 - 1e-9).mean()
            cl_neg = (c[neg] >= 1 - 1e-9).mean()
            rows.append({
                "relation": rel,
                "omega_r": omega,
                "base_rate": base,
                "contrast": omega - base,
                "clique_rate_pos": cl_pos,
                "clique_rate_neg": cl_neg,
                # 0/0 is undefined, not infinite: a relation in which NEITHER positives nor
                # negatives ever form a clique carries no leak and must not sort to the top.
                "clique_lift": (np.nan if cl_pos == 0
                                else (cl_pos / cl_neg) if cl_neg > 0 else np.inf),
                # A raw lift is +inf whenever no negative ever forms a clique, which happens
                # routinely at high leakage and makes the statistic unusable downstream
                # (no correlation, no plotting, no calibration). The smoothed version applies
                # a Haldane-style 1/(2n) correction so it stays finite and ordered.
                "clique_lift_smoothed": ((cl_pos + 0.5 / max(pos.sum(), 1))
                                         / (cl_neg + 0.5 / max(neg.sum(), 1))),
                # The statistic that survives all three settings we have tested. A relation
                # that merely CORRELATES with the labels produces high density but rarely
                # exact cliques; a relation GENERATED from the label source makes positives
                # exact cliques, because the curation records every pairwise co-membership.
                # That distinction is what separates leakage from legitimate signal, and no
                # density-based statistic can make it -- see suspect_relations().
                "clique_contrast": cl_pos - cl_neg,
                "auc_phi_alone": (roc_auc_score(phi.label[pos | neg], c[pos | neg])
                                  if phi.label[pos | neg].nunique() > 1 else np.nan),
            })
        out = pd.DataFrame(rows).sort_values("clique_lift", ascending=False,
                                             ignore_index=True)
        out.attrs["negative_stratum"] = negative_stratum or "all negatives"
        return out

    def suspect_relations(self, negative_stratum: str | None = None,
                          min_clique_contrast: float = 0.05) -> pd.DataFrame:
        """Relations ranked as candidates for provenance review.

        **This is triage, not a verdict.** No statistic computed from the graph alone can
        separate leakage from legitimate signal: a relation that genuinely informs the labels
        and a relation generated from them both make positives denser than negatives. The
        verdict needs the written provenance declaration D4 asks for. What this ranking does
        is tell you which relations to check first.

        Ranking is on `clique_contrast` = P(phi=1 | positive) - P(phi=1 | negative), which is
        the only candidate that behaved in all three settings we have tested:

          * **omega alone** over-ranks dense relations -- in the IR benchmark trade has the
            highest omega and little discriminative power.
          * **clique lift** over-ranks sparse relations -- in the protein benchmark
            `experiments_transferred` tops it at 1707x while separating at only AUC 0.715,
            because its negatives essentially never form a clique so the ratio explodes off a
            tiny base.
          * **phi-alone AUC** cannot distinguish leakage from genuine signal at all: on the
            synthetic testbed at alpha = 0, where by construction there is no leak, every
            latent-similarity relation still clears an AUC threshold, because latent
            similarity is genuinely predictive of the labels.

        The clique rate is what differs. A merely correlated relation yields high density and
        few exact cliques; a relation generated from the label source makes positives exact
        cliques, because the curation records every pairwise co-membership.

        Returns the whole ranked table, not one name: leakage is frequently not confined to a
        single relation. In the protein benchmark three channels descend from the same
        literature and experiments that produced the labels.
        """
        d = self.d4_provenance(negative_stratum=negative_stratum)
        d = d.sort_values(["clique_contrast", "contrast"], ascending=False, ignore_index=True)
        d["flagged"] = d["clique_contrast"] >= min_clique_contrast
        return d

    def suspect_relation(self, negative_stratum: str | None = None) -> str:
        """Top-ranked suspect. Prefer `suspect_relations()` -- leakage is often not unique."""
        return str(self.suspect_relations(negative_stratum).iloc[0].relation)

    # ------------------------------------------------------------------- D1
    def d1_shortcut(self, train_mask=None, test_mask=None, probe: str = "gbm",
                    exclude_relations: Sequence[str] = (), random_state: int = 0) -> dict:
        """Shortcut sufficiency: how much of the task falls to group densities alone.

        With no masks, reports in-sample cross-fit-free numbers on the whole set; supply
        boolean masks to honour the benchmark's own split.
        """
        phi = self.densities()
        rels = [r for r in self.relations if r not in set(exclude_relations)]
        cols = [f"phi_{r}" for r in rels]
        X = phi[cols].copy()
        for r in rels:
            X[f"clique_{r}"] = (phi[f"phi_{r}"] >= 1 - 1e-9).astype(float)
        X["size"] = phi["size"]
        X["log_size"] = np.log(phi["size"])
        y = phi.label.values

        if train_mask is None:
            train_mask = np.ones(len(phi), bool)
        if test_mask is None:
            test_mask = train_mask
        train_mask = np.asarray(train_mask, bool)
        test_mask = np.asarray(test_mask, bool)

        Xtr, Xte = X[train_mask].values, X[test_mask].values
        ytr, yte = y[train_mask], y[test_mask]

        if probe == "linear":
            sc = StandardScaler().fit(Xtr)
            clf = LogisticRegression(max_iter=3000).fit(sc.transform(Xtr), ytr)
            p = clf.predict_proba(sc.transform(Xte))[:, 1]
        elif probe == "gbm":
            clf = GradientBoostingClassifier(random_state=random_state,
                                             n_estimators=300, max_depth=3).fit(Xtr, ytr)
            p = clf.predict_proba(Xte)[:, 1]
        else:
            raise ValueError(probe)

        return {"probe": probe, "features": list(X.columns),
                "n_train": int(train_mask.sum()), "n_test": int(test_mask.sum()),
                "auc_shortcut": float(roc_auc_score(yte, p)),
                "pr_auc_shortcut": float(average_precision_score(yte, p))}

    # ------------------------------------------------------------------- D3
    def perturbed_negatives(self, budget: int, universe: Callable | dict | Iterable,
                            n_per_positive: int = 2, seed: int = 0,
                            positive_label: int = 1) -> list[Group]:
        """Swap `budget` members of each positive for non-members -- D3's negative ladder.

        `universe` supplies candidate non-members: a callable `(time) -> iterable`, a dict
        keyed by time, or a flat iterable for static graphs.
        """
        rng = np.random.default_rng(seed)

        def cands(t):
            if callable(universe):
                return list(universe(t))
            if isinstance(universe, dict):
                return list(universe.get(t, []))
            return list(universe)

        out = []
        for g in self.groups:
            if g.label != positive_label:
                continue
            pool = [c for c in cands(g.time) if c not in set(g.members)]
            if len(pool) < budget or g.size <= budget:
                continue
            for _ in range(n_per_positive):
                drop = rng.choice(g.size, size=budget, replace=False)
                add = rng.choice(len(pool), size=budget, replace=False)
                new = [m for i, m in enumerate(g.members) if i not in set(drop.tolist())]
                new += [pool[i] for i in add]
                out.append(Group(members=tuple(sorted(new, key=repr)), label=0,
                                 time=g.time,
                                 meta={**g.meta, "budget": budget,
                                       "source_group": g.meta.get("group_id")}))
        return out

    def d3_curve(self, budgets: Sequence[int], universe, scorer: Callable | None = None,
                 n_per_positive: int = 2, seed: int = 0,
                 positive_label: int = 1) -> pd.DataFrame:
        """AUC against perturbation budget.

        `scorer(groups) -> array of scores` plugs in any model. If omitted, the D1 shortcut
        probe is used, which measures how fast the *shortcut* collapses -- the pure
        clique-violation signal.

        The reported statistic is the slope at b = 1: a shortcut learner falls off a cliff
        when a single member is substituted, a model with genuine group structure does not.
        """
        pos = [g for g in self.groups if g.label == positive_label]
        rows = []
        for b in budgets:
            negs = self.perturbed_negatives(b, universe, n_per_positive, seed, positive_label)
            if not negs:
                continue
            sub = pos + negs
            y = np.array([g.label for g in sub])
            if scorer is None:
                s = self._shortcut_scores(sub, seed)
            else:
                s = np.asarray(scorer(sub), dtype=float)
            rows.append({"budget": b, "n_pos": len(pos), "n_neg": len(negs),
                         "auc": float(roc_auc_score(y, s))})
        df = pd.DataFrame(rows)
        if len(df) >= 2:
            d = df.sort_values("budget")
            df.attrs["slope_at_1"] = float(
                (d.auc.iloc[1] - d.auc.iloc[0]) / (d.budget.iloc[1] - d.budget.iloc[0]))
        return df

    def _shortcut_scores(self, groups: list[Group], seed: int, n_splits: int = 5) -> np.ndarray:
        """Out-of-fold shortcut scores.

        Cross-fitted deliberately: scoring groups with a probe fitted on those same groups
        drives the D3 curve to ~1.0 everywhere and hides the very collapse the diagnostic
        exists to measure.
        """
        feats, y = [], []
        for g in groups:
            keys, _k = self._dyad_keys(g.members)
            n = keys.size
            row = []
            for rel in self.relations:
                d = (self._count_hits(keys, rel, g.time) / n) if n else 0.0
                row += [d, float(d >= 1 - 1e-9)]
            row += [g.size, np.log(g.size)]
            feats.append(row)
            y.append(g.label)
        X, y = np.array(feats), np.array(y)
        clf = GradientBoostingClassifier(random_state=seed, n_estimators=200, max_depth=3)
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        return cross_val_predict(clf, X, y, cv=cv, method="predict_proba")[:, 1]

    # ------------------------------------------------------------------- D2
    def d2_gap(self, fit_predict: Callable, target_relation: str | None = None,
               train_mask=None, test_mask=None) -> dict:
        """Leakage gap, both halves.

        `fit_predict(train_groups, test_groups, drop_relations, exclude_in_training)`
        must return scores for `test_groups`. Both halves are reported because they answer
        different questions: inference masking measures the fitted function's dependence on
        r*, train-time exclusion measures how recoverable r* is from the other relations.
        """
        r = target_relation or self.suspect_relation()
        n = len(self.groups)
        train_mask = np.ones(n, bool) if train_mask is None else np.asarray(train_mask, bool)
        test_mask = train_mask if test_mask is None else np.asarray(test_mask, bool)
        tr = [g for g, m in zip(self.groups, train_mask) if m]
        te = [g for g, m in zip(self.groups, test_mask) if m]
        y = np.array([g.label for g in te])

        auc_full = roc_auc_score(y, fit_predict(tr, te, (), False))
        auc_mask = roc_auc_score(y, fit_predict(tr, te, (r,), False))
        auc_excl = roc_auc_score(y, fit_predict(tr, te, (r,), True))
        return {"target_relation": r,
                "auc_full": float(auc_full),
                "auc_masked_at_inference": float(auc_mask),
                "auc_excluded_in_training": float(auc_excl),
                "delta_inference_mask": float(auc_full - auc_mask),
                "delta_train_exclusion": float(auc_full - auc_excl)}

    # ---------------------------------------------------------------- report
    def metric_triple(self, model_auc: float, train_mask=None, test_mask=None,
                      target_relation: str | None = None,
                      masked_auc: float | None = None) -> dict:
        """The (full, masked, shortcut) triple the protocol asks papers to report."""
        d1 = self.d1_shortcut(train_mask, test_mask)
        return {"auc_full": model_auc,
                "auc_masked": masked_auc,
                "auc_shortcut": d1["auc_shortcut"],
                "target_relation": target_relation or self.suspect_relation()}

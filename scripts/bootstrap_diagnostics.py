r"""Every headline diagnostic magnitude, with an interval around it.

This is a paper about a measuring instrument, and until this script existed not one of its headline
magnitudes carried an uncertainty. Table 3's contrasts, Table 4's contrast by size, the two steps
Section 6.3 compares, the PTA contrast in Section 6.2 and the lead time at which the pre-specified
rule declares the horizon closed were all point estimates. Table 4's largest entry, 0.5833, rests on
24 events and sits at the top of Figure 6 with nothing around it; the entry beside it rests on 47
(revision item 2.1).

The resampling unit is not negotiable and is already declared. Section 5.4 fixes it as the
**membership equivalence family**: two entities whose member sets coincide for a sustained period are
not independent observations, and the corpus holds 464 families over 562 entities, 43 of them with
more than one member. The task results already bootstrap over families; the diagnostics did not.
Corpus B has no equivalent, so its cluster is the **complex**, which keeps a positive and the
negatives generated from it in the same replicate. PTA's cluster is the **agreement**.

Architecture, because the naive version is unaffordable. Every statistic here is a mean, or a
threshold crossing of means, over rows that are expensive to compute and cheap to re-aggregate. So
each pass computes its row-level frame **once** -- one star density per candidate per relation per
lead time, one clique indicator per candidate per level -- and the bootstrap then resamples clusters
over the stored rows. Recomputing the graph statistics per replicate would multiply the cost of the
whole paper by the replicate count and change no number.

Six passes:

**A. Table 3.** The matched contrast per relation per lead time, its retention at eight periods, the
residual against the strongest anchor, and the lead time at which that residual first falls below
0.01 -- which is the five-period phantom Section 6.3 reports, and the quantity whose sampling
distribution decides whether "about five periods" is a measurement or a coin toss.

**B. Section 6.3's two steps.** Focal isolation's 0.9844 against the pooled relation's 0.1447 on the
same events, and the ratio between them, which the manuscript quotes as a factor of 6.8. A ratio of
two noisy quantities needs an interval more than either of them does.

**C. Table 4 and Figure 6.** The clique contrast by group size, corpus A at both declared levels and
corpus B at level 1, with the counts that make the small bins small.

**D. Section 6.2's PTA contrast.** The 0.1023 the instrument recovers against a width printed in the
source.

**E. The synthetic calibration.** Table 2 reports the rule landing on the target in 6 of 6 settings
from 90 accession events each. Resampling coalitions within each setting says how often it would
still land there, which is the difference between "the rule returns 6" and "the rule returns 6 in
most samples of this size".

**F. Section 6.3's declared-resolution width.** The one positive field measurement of a horizon in
corpus A, and the last headline magnitude to acquire an interval.

Intervals are percentile intervals from the empirical bootstrap distribution. No normal
approximation: several of these statistics are threshold crossings on integers, and a symmetric
interval around one of those would be a fiction.

    python scripts/bootstrap_diagnostics.py
    python scripts/bootstrap_diagnostics.py --replicates 200 --only A B     # a faster subset
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from penumbra.synthetic import SyntheticConfig, generate  # noqa: E402
from penumbra.umbra import NEVER_EVENT, HorizonAudit, delta_star  # noqa: E402
from vendor.cliquebait.diagnostics import LeakageAudit  # noqa: E402

LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"
RESULTS = ROOT / "results"
WS2 = ROOT.parent / "CLIQUEBAIT" / "data" / "ws2"

REGIME = (1965, 2014)
HORIZONS = range(0, 9)
RELATIONS = ["igo_comembership", "allies", "trades", "votes_with", "conflicts_with"]
R_STAR = "igo_comembership"
ANCHORS = ["trades", "votes_with", "conflicts_with"]
A_LEVELS = (1, 25)
BINS = [1, 3, 5, 10, 20, 80, 10_000]
N_NEG = 2
SEED = 0
THRESHOLD = 0.01
SYN_ANCHORS = ["r_current", "r_latent_1", "r_latent_2", "r_noise"]


def ci(samples, lo: float = 2.5, hi: float = 97.5) -> dict:
    """Percentile interval, with the count of usable replicates stated beside it."""
    a = np.asarray([s for s in samples if s is not None and s == s], float)
    if a.size == 0:
        return {"n_replicates": 0, "lo": None, "hi": None, "median": None}
    return {"n_replicates": int(a.size),
            "lo": round(float(np.percentile(a, lo)), 4),
            "hi": round(float(np.percentile(a, hi)), 4),
            "median": round(float(np.percentile(a, 50)), 4)}


def cluster_draws(clusters: np.ndarray, n_rep: int, rng) -> list[np.ndarray]:
    """`n_rep` resamples of the cluster labels, with replacement, at the observed cluster count."""
    uniq = np.unique(clusters)
    return [rng.choice(uniq, size=uniq.size, replace=True) for _ in range(n_rep)]


def _row_index(clusters: np.ndarray) -> dict:
    """cluster label -> the row positions it owns, so a replicate is a concatenate rather than a join."""
    order = np.argsort(clusters, kind="stable")
    sorted_c = clusters[order]
    edges = np.flatnonzero(np.r_[True, sorted_c[1:] != sorted_c[:-1]])
    starts = list(edges) + [len(sorted_c)]
    return {sorted_c[edges[i]]: order[starts[i]:starts[i + 1]] for i in range(len(edges))}


def resample(idx: dict, draw: np.ndarray) -> np.ndarray:
    return np.concatenate([idx[c] for c in draw if c in idx])


# --------------------------------------------------------------------------- shared corpus A load
def _corpus_a():
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    ev = pd.read_parquet(LEDGER / "events.parquet")
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    ev = ev.merge(ent[["entity_id", "entity_type", "family_id"]], on="entity_id", how="left")
    return mem, ev


class _Star:
    """The star statistic `run_u1_isolation` uses, over the packed index."""

    def __init__(self, audit: HorizonAudit):
        self.n, self.ix, self.keys = audit._n, audit._ix, audit._keys

    def __call__(self, cc: int, others: np.ndarray, year: int, relation: str) -> float:
        if cc not in self.ix:
            return float("nan")
        oi = np.array([self.ix[int(m)] for m in others if int(m) in self.ix], np.int64)
        if oi.size == 0:
            return float("nan")
        ci_ = self.ix[cc]
        k = np.minimum(ci_, oi) * np.int64(self.n) + np.maximum(ci_, oi)
        arr = self.keys.get((relation, year))
        if arr is None:
            return 0.0
        p = np.clip(np.searchsorted(arr, k), 0, arr.size - 1)
        return float((arr[p] == k).mean())


# --------------------------------------------------------------------------- A and B
def matched_rows() -> pd.DataFrame:
    """One row per (event, lead time, candidate): the star density in every relation, plus the focal
    record indicator. The frame Table 3 and Section 6.3's two steps are both aggregates of."""
    mem, ev = _corpus_a()
    frames = [pd.read_parquet(GRAPH / f"edges_{r}.parquet").assign(relation=r) for r in RELATIONS]
    audit = HorizonAudit(pd.concat(frames, ignore_index=True), mem, ev)
    star = _Star(audit)

    all_states = np.sort(mem.ccode.unique())
    ever = mem[mem.status == 1].groupby("entity_id").ccode.apply(set).to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()
             & ev.t_R.between(*REGIME) & (ev.entity_type == "organisation")]
    rng = np.random.default_rng(SEED)

    rows = []
    for r in acc.itertuples():
        cc, t_ev, eid = int(r.ccode), int(r.t_R), r.entity_id
        never = np.setdiff1d(all_states, np.fromiter(ever.get(eid, set()), np.int64))
        if never.size == 0:
            continue
        negs = rng.choice(never, size=min(N_NEG, never.size), replace=False)
        for d in HORIZONS:
            t = t_ev - d
            ms = audit._member_sets.get((eid, t))
            if ms is None:
                continue
            for who, label in [(cc, 1)] + [(int(n), 0) for n in negs]:
                others = np.array([m for m in ms if m != who], np.int64)
                if others.size == 0:
                    continue
                rows.append([r.family_id, d, label, float(who in ms)]
                            + [star(who, others, t, rel) for rel in RELATIONS])
    return pd.DataFrame(rows, columns=["family_id", "horizon", "label", "on_focal_record"]
                        + RELATIONS)


def _contrast_table(df: pd.DataFrame) -> pd.DataFrame:
    pos = df[df.label == 1].groupby("horizon")[RELATIONS].mean()
    neg = df[df.label == 0].groupby("horizon")[RELATIONS].mean()
    return pos - neg


def _crossing(con: pd.DataFrame) -> int | None:
    resid = con[R_STAR] - con[ANCHORS].max(axis=1)
    for h, v in resid.items():
        if v < THRESHOLD:
            return int(h)
    return None


def pass_ab(n_rep: int) -> dict:
    print("\nA/B. Table 3 and the two steps Section 6.3 compares")
    df = matched_rows()
    print(f"  {len(df):,} rows over {df.family_id.nunique()} families, "
          f"{int((df.label == 1).sum()):,} positives")

    point = _contrast_table(df)
    p = df[df.label == 1]
    focal_step = float(p.loc[p.horizon == 0, "on_focal_record"].mean()
                       - p.loc[p.horizon >= 1, "on_focal_record"].mean())
    pooled_step = float(p.loc[p.horizon == 0, R_STAR].mean()
                        - p.loc[p.horizon >= 1, R_STAR].mean())

    clusters = df.family_id.to_numpy()
    idx = _row_index(clusters)
    rng = np.random.default_rng(SEED)
    draws = cluster_draws(clusters, n_rep, rng)

    per_rel = {rel: {h: [] for h in HORIZONS} for rel in RELATIONS}
    retention, crossings, focal_s, pooled_s, ratios, residuals = (
        {rel: [] for rel in RELATIONS}, [], [], [], [], {h: [] for h in HORIZONS})
    for draw in draws:
        sub = df.iloc[resample(idx, draw)]
        if sub.label.nunique() < 2:
            continue
        con = _contrast_table(sub)
        for rel in RELATIONS:
            for h in HORIZONS:
                if h in con.index:
                    per_rel[rel][h].append(float(con[rel][h]))
            if 0 in con.index and 8 in con.index and abs(con[rel][0]) > 1e-9:
                retention[rel].append(float(con[rel][8] / con[rel][0]))
        r_ = con[R_STAR] - con[ANCHORS].max(axis=1)
        for h in HORIZONS:
            if h in r_.index:
                residuals[h].append(float(r_[h]))
        crossings.append(_crossing(con))
        sp = sub[sub.label == 1]
        f = float(sp.loc[sp.horizon == 0, "on_focal_record"].mean()
                  - sp.loc[sp.horizon >= 1, "on_focal_record"].mean())
        q = float(sp.loc[sp.horizon == 0, R_STAR].mean()
                  - sp.loc[sp.horizon >= 1, R_STAR].mean())
        focal_s.append(f)
        pooled_s.append(q)
        if abs(q) > 1e-9:
            ratios.append(f / q)

    fired = [c for c in crossings if c is not None]
    out = {
        "n_rows": int(len(df)), "n_families": int(df.family_id.nunique()),
        "n_positives": int((df.label == 1).sum()), "replicates": n_rep,
        "contrast": {rel: {int(h): {"point": round(float(point[rel][h]), 4),
                                    **ci(per_rel[rel][h])} for h in HORIZONS}
                     for rel in RELATIONS},
        "retention_at_8": {rel: {"point": round(float(point[rel][8] / point[rel][0]), 4),
                                 **ci(retention[rel])}
                           for rel in RELATIONS if abs(point[rel][0]) > 1e-9},
        "residual": {int(h): {"point": round(float(point[R_STAR][h]
                                                   - point[ANCHORS].max(axis=1)[h]), 4),
                              **ci(residuals[h])} for h in HORIZONS},
        "residual_crossing_lead_time": {
            "point": _crossing(point),
            "replicates_where_it_fired": len(fired),
            # Stored rather than left to subtraction: Figure 5 draws this count as a stub beside the
            # crossing histogram, and every value a figure carries has to have an artefact behind it.
            "replicates_where_it_never_fired": int(len(crossings) - len(fired)),
            "distribution": {int(k): int(v) for k, v in
                             pd.Series(fired).value_counts().sort_index().items()},
            **ci(fired)},
        "focal_step": {"point": round(focal_step, 4), **ci(focal_s)},
        "pooled_step": {"point": round(pooled_step, 4), **ci(pooled_s)},
        "focal_over_pooled": {"point": round(focal_step / pooled_step, 3), **ci(ratios)},
    }
    print(f"  {'relation':18s} {'D=0':>22s} {'D=8':>22s}")
    for rel in RELATIONS:
        c0, c8 = out["contrast"][rel][0], out["contrast"][rel][8]
        print(f"  {rel:18s} {c0['point']:.4f} [{c0['lo']:.4f}, {c0['hi']:.4f}]  "
              f"{c8['point']:.4f} [{c8['lo']:.4f}, {c8['hi']:.4f}]")
    rc = out["residual_crossing_lead_time"]
    print(f"  the residual first falls below {THRESHOLD} at lead time {rc['point']}; "
          f"across replicates {rc['lo']} to {rc['hi']} (median {rc['median']}), "
          f"fired in {rc['replicates_where_it_fired']} of {n_rep}")
    print(f"  distribution of that lead time: {rc['distribution']}")
    fs, ps, ro = out["focal_step"], out["pooled_step"], out["focal_over_pooled"]
    print(f"  focal step {fs['point']} [{fs['lo']}, {fs['hi']}]   "
          f"pooled step {ps['point']} [{ps['lo']}, {ps['hi']}]")
    print(f"  ratio {ro['point']} [{ro['lo']}, {ro['hi']}]  "
          f"-- the manuscript quotes this as a factor of 6.8")
    return out


# --------------------------------------------------------------------------- C
def clique_rows_a() -> pd.DataFrame:
    mem, ev = _corpus_a()
    cm = pd.read_parquet(GRAPH / f"edges_{R_STAR}.parquet").assign(relation=R_STAR)
    audit = HorizonAudit(cm, mem, ev)
    all_states = np.sort(mem.ccode.unique())
    ever = mem[mem.status == 1].groupby("entity_id").ccode.apply(set).to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna() & ev.t_R.between(*REGIME)]

    rows = []
    for k in A_LEVELS:
        rng = np.random.default_rng(SEED)
        for r in acc.itertuples():
            cc, t, eid = int(r.ccode), int(r.t_R), r.entity_id
            ms = audit._members.get((eid, t))
            if ms is None or len(ms) < 2:
                continue
            never = np.setdiff1d(all_states, np.fromiter(ever.get(eid, set()), np.int64))
            if never.size == 0:
                continue
            n = len(ms)
            negs = rng.choice(never, size=min(N_NEG, never.size), replace=False)
            for who, lab in [(cc, 1)] + [(int(x), 0) for x in negs]:
                grp = np.append(ms[ms != who], who)
                phi = audit.phi(grp, t, R_STAR, k)
                if not np.isnan(phi):
                    rows.append((r.family_id, k, n, lab, float(phi >= 1.0)))
    return pd.DataFrame(rows, columns=["cluster", "level", "n", "label", "clique"])


def clique_rows_b(threshold: int = 400) -> pd.DataFrame:
    g = pd.read_parquet(WS2 / f"groups_thr{threshold}.parquet")
    e = pd.read_parquet(WS2 / f"edges_thr{threshold}.parquet")
    phi = LeakageAudit(e, g).densities()
    d = phi[["phi_database", "label", "size", "neg_type", "group_id"]].rename(
        columns={"phi_database": "phi"}).dropna(subset=["phi"])
    d = d[(d.label == 1) | (d.neg_type == "random")]
    return pd.DataFrame({"cluster": d.group_id.to_numpy(), "level": 1,
                         "n": d["size"].to_numpy(), "label": d.label.to_numpy(),
                         "clique": (d.phi >= 1.0).astype(float).to_numpy()})


def _by_bin(d: pd.DataFrame) -> dict:
    d = d.assign(bin=pd.cut(d.n, BINS))
    out = {}
    for b, s in d.groupby("bin", observed=True):
        p, q = s[s.label == 1], s[s.label == 0]
        if not len(p) or not len(q):
            continue
        out[str(b)] = float(p.clique.mean() - q.clique.mean())
    return out


def pass_c(n_rep: int) -> dict:
    print("\nC. Table 4 and Figure 6: the clique contrast by group size")
    out = {}
    for name, frame in (("corpus_a", clique_rows_a()), ("corpus_b", clique_rows_b())):
        out[name] = {}
        for lvl, d in frame.groupby("level"):
            d = d.reset_index(drop=True)
            point = _by_bin(d)
            clusters = d.cluster.to_numpy()
            idx = _row_index(clusters)
            rng = np.random.default_rng(SEED)
            reps = {b: [] for b in point}
            for draw in cluster_draws(clusters, n_rep, rng):
                sub = d.iloc[resample(idx, draw)]
                tab = _by_bin(sub)
                for b in point:
                    if b in tab:
                        reps[b].append(tab[b])
            pos = d[d.label == 1]
            counts = {str(k): int(v) for k, v in
                      pos.assign(bin=pd.cut(pos.n, BINS)).groupby("bin", observed=True)
                      .size().items()}
            out[name][f"k={int(lvl)}"] = {
                b: {"point": round(point[b], 4), "n_pos": counts.get(b), **ci(reps[b])}
                for b in point}
            print(f"  {name}, k={int(lvl)}")
            print(f"    {'members':14s} {'n_pos':>6s} {'contrast':>9s} {'95% interval':>22s}")
            for b, v in out[name][f"k={int(lvl)}"].items():
                print(f"    {b:14s} {str(v['n_pos'] or '-'):>6s} {v['point']:>9.4f} "
                      f"[{v['lo']:.4f}, {v['hi']:.4f}]")
    return out


# --------------------------------------------------------------------------- D
def pass_d(n_rep: int) -> dict:
    """Section 6.2's PTA contrast, resampled over agreements."""
    print("\nD. Section 6.2: the PTA contrast between inside and outside the coded gap")
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_delta_star_desta import WINDOW, pta_relations  # noqa: E402

    sig, _force, events = pta_relations()
    idx_by_year: dict[int, set] = {}
    for r in sig.itertuples():
        idx_by_year.setdefault(int(r.year), set()).add((int(r.cow_i), int(r.cow_j)))

    rows = []
    for r in events.itertuples():
        if not r.members:
            continue
        for d in range(0, 9):
            t = r.force_year - d
            if t < WINDOW[0]:
                continue
            present = idx_by_year.get(t, set())
            hits = sum(1 for m in r.members
                       if (min(r.ccode, m), max(r.ccode, m)) in present)
            rows.append((r.Index, r.gap, d, hits / len(r.members), bool(d <= r.gap)))
    df = pd.DataFrame(rows, columns=["cluster", "gap", "horizon", "share_present", "inside_gap"])

    def contrast(d: pd.DataFrame) -> float:
        return float(d[d.inside_gap].share_present.mean() - d[~d.inside_gap].share_present.mean())

    point = contrast(df)
    clusters = df.cluster.to_numpy()
    idx = _row_index(clusters)
    rng = np.random.default_rng(SEED)
    reps = []
    for draw in cluster_draws(clusters, n_rep, rng):
        sub = df.iloc[resample(idx, draw)]
        if sub.inside_gap.nunique() < 2:
            continue
        reps.append(contrast(sub))
    # The ratio Figure 3 panel C reports as "a factor of ten". Its numerator is the focal record's
    # presence, which is exactly 1 by entailment -- the relation is dated from signature and the event
    # from entry into force -- so the ratio's uncertainty is entirely the denominator's, and inverting
    # the percentile interval is exact rather than approximate because the transform is monotone.
    ratios = [1.0 / r for r in reps if abs(r) > 1e-9]
    out = {"n_events": int(df.cluster.nunique()), "n_rows": int(len(df)),
           "contrast": {"point": round(point, 4), **ci(reps)},
           "focal_over_pooled": {"point": round(1.0 / point, 2), **ci(ratios)},
           "numerator_is_entailed": True}
    c, r_ = out["contrast"], out["focal_over_pooled"]
    print(f"  {out['n_events']} agreements, {out['n_rows']:,} event-lead-time pairs")
    print(f"  contrast {c['point']} [{c['lo']}, {c['hi']}]")
    print(f"  focal record over pooled relation {r_['point']} [{r_['lo']}, {r_['hi']}]  "
          f"-- the numerator is entailed, so this interval is the denominator's alone")
    return out


# --------------------------------------------------------------------------- E
def pass_e(n_rep: int) -> dict:
    """Table 2's calibration, resampled over coalitions within each setting.

    Table 2 says the rule lands on the target in 6 of 6 settings from 90 events each. The question a
    reviewer will ask is whether the rule would still land there in another sample of that size, and
    the answer is a distribution rather than a tick.
    """
    print("\nE. Table 2: the calibration, resampled over coalitions within each setting")
    out = {}
    for beta in (0, 1, 2, 3, 4, 5):
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            edges, events, membership, _g, meta = generate(1.0, beta, SyntheticConfig())
        audit = HorizonAudit(edges, membership, events)

        # The row-level frame: one phi per candidate per relation, per lead time, kept with the
        # coalition it belongs to so the resample is by coalition rather than by row.
        rows = []
        for h in HORIZONS:
            panel = audit.accession_panel(h, NEVER_EVENT, 4, SEED)
            if panel.empty or panel.label.nunique() < 2:
                continue
            for r in panel.itertuples():
                rec = {"cluster": r.entity_id, "horizon": h, "label": r.label}
                for rel in audit.relations:
                    rec[rel] = audit.phi_candidate(r.entity_id, r.year, r.ccode, rel, 1)
                rows.append(rec)
        df = pd.DataFrame(rows)
        rels = list(audit.relations)

        def curve_from(d: pd.DataFrame) -> pd.DataFrame:
            recs = []
            for h, g in d.groupby("horizon"):
                if g.label.nunique() < 2:
                    continue
                for rel in rels:
                    v = g[rel]
                    ok = v.notna()
                    y = g.label[ok]
                    if y.nunique() < 2:
                        continue
                    pos = v[ok & (g.label == 1)]
                    neg = v[ok & (g.label == 0)]
                    cp = float((pos >= 1 - 1e-9).mean())
                    cn = float((neg >= 1 - 1e-9).mean())
                    recs.append({"horizon": int(h), "relation": rel, "level": 1,
                                 "n_pos": int(len(pos)), "n_neg": int(len(neg)),
                                 "clique_contrast": cp - cn,
                                 # delta_star reads this field for the upper bound only, and the
                                 # lower bound is what Table 2 grades, so a rank statistic that is
                                 # cheap to recompute is enough here.
                                 "auc_phi_alone": 0.5})
            return pd.DataFrame(recs)

        point = delta_star(curve_from(df), "r_star", SYN_ANCHORS, level=1)["delta_star_lo"]
        clusters = df.cluster.to_numpy()
        idx = _row_index(clusters)
        rng = np.random.default_rng(SEED)
        reps = []
        for draw in cluster_draws(clusters, n_rep, rng):
            sub = df.iloc[resample(idx, draw)]
            c = curve_from(sub)
            if c.empty:
                continue
            reps.append(delta_star(c, "r_star", SYN_ANCHORS, level=1)["delta_star_lo"])
        fired = [r for r in reps if r is not None]
        on_target = sum(1 for r in fired if r == beta + 1)
        out[beta] = {"target": beta + 1, "point": point,
                     "replicates": len(reps), "fired": len(fired),
                     "on_target": on_target,
                     "share_on_target": round(on_target / max(len(reps), 1), 3),
                     "distribution": {int(k): int(v) for k, v in
                                      pd.Series(fired).value_counts().sort_index().items()},
                     **ci(fired)}
        o = out[beta]
        print(f"  beta={beta} target={beta + 1} point={point}  "
              f"on target in {o['on_target']}/{o['replicates']} replicates "
              f"({o['share_on_target'] * 100:.0f} percent), interval [{o['lo']}, {o['hi']}], "
              f"distribution {o['distribution']}")
    return out


# --------------------------------------------------------------------------- F
def pass_f(n_rep: int) -> dict:
    """Section 6.3's declared-resolution width, the one positive field measurement, with an interval.

    Everything else in Section 6.3 is either an entailment of the register's single date or a pooled
    contrast. The declared-resolution stratum's presence at one lead time is neither: the register
    states that its own pre-1965 dates are accurate only within five-year blocks, and this is the width
    that coding rule produces. It is the paper's only measured field horizon and it was the only
    headline magnitude still without an interval after the first bootstrap pass.

    Cheap, because focal isolation reads the membership register and no graph: a one-edge stub satisfies
    the audit's constructor and the statistic never touches it.
    """
    print("\nF. Section 6.3: the declared-resolution stratum's width")
    mem, ev = _corpus_a()
    stub = pd.DataFrame({"relation": ["_stub"], "year": [REGIME[0]], "cow_i": [2], "cow_j": [20],
                         "weight": [1]})
    audit = HorizonAudit(stub, mem, ev)
    first_mem = mem[mem.status == 1].groupby(["entity_id", "ccode"]).year.min().to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()]

    rows = []
    for r in acc.itertuples():
        cc, t_ev = int(r.ccode), int(r.t_R)
        fm = first_mem.get((r.entity_id, cc))
        # A prior spell puts the state on the record for reasons predating the event, so the trace at
        # long lead times is recurrence rather than back-dating; Section 6.3 conditions it away.
        first_entry = fm is None or fm >= t_ev - 1
        if not first_entry:
            continue
        for d in HORIZONS:
            ms = audit._member_sets.get((r.entity_id, t_ev - d))
            if ms is None:
                continue
            rows.append((r.family_id, r.dating_stratum, int(d), float(cc in ms)))
    df = pd.DataFrame(rows, columns=["cluster", "stratum", "horizon", "on_record"])

    out = {}
    for stratum in sorted(df.stratum.unique()):
        sub = df[df.stratum == stratum].reset_index(drop=True)
        at1 = sub[sub.horizon == 1]
        if at1.empty:
            continue
        point = float(at1.on_record.mean())
        idx = _row_index(at1.cluster.to_numpy())
        rng = np.random.default_rng(SEED)
        reps = []
        for draw in cluster_draws(at1.cluster.to_numpy(), n_rep, rng):
            s = at1.iloc[resample(idx, draw)]
            if len(s):
                reps.append(float(s.on_record.mean()))
        out[str(stratum)] = {"n_events_at_lead_time_1": int(len(at1)),
                            "n_clusters": int(at1.cluster.nunique()),
                            "presence_at_1": {"point": round(point, 4), **ci(reps)},
                            "max_beyond_1": round(float(sub[sub.horizon >= 2].on_record.max()), 4)}
        v = out[str(stratum)]["presence_at_1"]
        print(f"  {stratum:22s} n={len(at1):5d} over {at1.cluster.nunique():3d} families   "
              f"presence at one period {v['point']} [{v['lo']}, {v['hi']}]   "
              f"max beyond {out[str(stratum)]['max_beyond_1']}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=1000)
    ap.add_argument("--only", nargs="+", choices=list("ABCDEF"), default=list("ABCDEF"))
    ap.add_argument("--json", type=Path, default=RESULTS / "bootstrap_diagnostics.json")
    # Recomputing one pass should not silently delete the others. The row-level frames of passes A to C
    # take minutes to build, so a partial rerun is the normal case and a partial overwrite is the
    # failure D-32 records: an artefact that no longer holds what a claim cites.
    ap.add_argument("--merge", action="store_true",
                    help="update only the recomputed passes in an existing artefact")
    args = ap.parse_args()

    existing: dict = {}
    if args.merge and args.json.exists():
        existing = json.loads(args.json.read_text(encoding="utf-8"))

    payload: dict = {
        "replicates": args.replicates,
        "interval": "percentile, 2.5 to 97.5",
        "resampling_unit": {
            "corpus_a": "membership equivalence family, Section 5.4, 464 over 562 entities",
            "corpus_b": "the complex, which keeps a positive and its negatives together",
            "pta": "the agreement",
            "synthetic": "the coalition",
        },
        "why_percentile": ("several of these statistics are threshold crossings on integers, and a "
                           "symmetric interval around one of those would be a fiction"),
    }
    if "A" in args.only or "B" in args.only:
        payload["table_3_and_the_two_steps"] = pass_ab(args.replicates)
    if "C" in args.only:
        payload["clique_contrast_by_size"] = pass_c(args.replicates)
    if "D" in args.only:
        payload["pta_contrast"] = pass_d(args.replicates)
    if "E" in args.only:
        payload["synthetic_calibration"] = pass_e(args.replicates)
    if "F" in args.only:
        payload["declared_resolution_width"] = pass_f(args.replicates)

    if existing:
        merged = {k: v for k, v in existing.items() if k not in ("invocation", "corpus")}
        merged.update(payload)
        payload = merged
    write_result(args.json, payload, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

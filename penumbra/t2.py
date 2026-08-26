"""T2: termination as an entity-level competing-risks problem. Manifesto §4's other core task.

The unit is the **coalition**, at risk from its origin to termination or the end of the window.
§4 calls competing risks "essential and the substantive contribution of this task", and after reading
the coding rules the causes are the source's rather than the manifesto's (LEDGER.md §2.2):

    1  dissolution   103 events   dated by the ten-year plenary rule -> stratum 4
    2  replaced        32         exact
    3  absorbed        22         exact
    0  cause unknown   33         ATOP terminations; the codebook is unreachable (PROVENANCE §4)

ATOP's 33 enter through the likelihood's **cause-unknown** branch rather than being dropped or
assigned a cause. That branch was written and verified for exactly this: an event that certainly
happened whose cause the source cannot tell us contributes $S(t_L) - S(t_R)$, which is the sum over
causes, and pretending otherwise would either discard 17 % of the events or invent their causes.

Three things separate T2 from T1 and each changes what can be estimated.

**It is a small-sample problem.** 573 entities and about 190 events against T1's 93,450 dyads and
6,606 events. C8's bound is live: 22 absorption events support zero covariates at ten per parameter,
which is why P5 is tested on the collapsed dissolution-versus-superseded contrast that §11 already
prescribes.

**Most of it is rule-dated.** 103 of 157 coded terminations carry dates assigned from up to ten
years of subsequent data (§9.7). They stay in estimation and leave the rolling-origin evaluation,
because a date that consumed information through $t+10$ cannot score a forecast made at $t$.

**§5.3's focal-group problem is at its worst here.** A coalition that ends is a set of co-membership
edges that disappears, so the focal entity's own edges are the label. `graph.focal_excluded_weight`
implements the intervention; T2 is run both ways and the pair is the result, in the same way
CLIQUEBAIT's two halves of D2 are.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from penumbra.hazard import CAUSE_UNKNOWN, CENSORED, PeriodPanel

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"
NODES = (ROOT.parent / "CLIQUEBAIT" / "previous-work-code-base" / "coalition-gnn"
         / "data" / "canonical" / "nodes.parquet")

CAUSE_CODE = {"dissolution": 1, "replaced": 2, "absorbed": 3, "uncoded": CAUSE_UNKNOWN}
# C8: with 22 absorption events, the three-cause model supports no covariates. §11 prescribes the
# collapse and this is it, named rather than improvised at analysis time.
COLLAPSED = {"dissolution": 1, "replaced": 2, "absorbed": 2, "uncoded": CAUSE_UNKNOWN}

NODE_COLS = ["cinc", "polity2", "v2x_polyarchy", "log_e_gdppc", "log_e_pop", "log_milex"]
RELATIONS = ["igo_comembership", "allies", "trades", "votes_with", "conflicts_with"]


def build_panel(regime=(1965, 2014), collapse: bool = True, focal_excluded: bool = False,
                phi_level: int = 25):
    """Entity-period panel with cause-specific outcomes.

    `collapse` merges replaced and absorbed into "superseded", per C8. `focal_excluded` removes the
    focal coalition's own contribution to co-membership, which is §5.3's U3 intervention and matters
    more for T2 than for T1 because the disappearing edges *are* the termination.
    """
    lo, hi = regime
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    ev = pd.read_parquet(LEDGER / "events.parquet")
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    mem = mem[(mem.status == 1) & mem.year.between(lo, hi)]

    term = ev[ev.event_type == "termination"].set_index("entity_id")
    alive = mem.groupby("entity_id").year.agg(["min", "max"])
    keep = alive.index[(alive["max"] >= lo)]
    ent = ent[ent.entity_id.isin(keep)].reset_index(drop=True)

    mapping = COLLAPSED if collapse else CAUSE_CODE
    rows_ent, rows_year, rows_dur = [], [], []
    tL, tR, cause, strat, eid_list, entry = [], [], [], [], [], []
    for i, r in enumerate(ent.itertuples()):
        origin = max(int(r.origin), lo)
        last = min(int(r.exit_year), hi)
        if last < origin:
            continue
        eid_list.append(r.entity_id)
        j = len(eid_list) - 1

        # **Duration runs from founding, and observation begins later.** The first version set the
        # clock to zero at the regime start, so a coalition founded in 1900 and one founded in 1965 were
        # both duration 1 in 1965. Measured: 183 of 528 entities in the regime panel predate it, with a
        # median true age of 13 and a maximum of 150, and they carry 45.7 % of the coalition-years and
        # 39.1 % of the terminations. That misplaces the baseline for a third of the panel, and
        # `log_duration` is one of the two cross-cause sign reversals P5 is scored on -- section 9.1 names
        # left truncation and D-03 recorded that it "binds hard", so the concern was declared and the
        # implementation did not honour it (D-36).
        #
        # `PeriodPanel.entry` is the field for exactly this and was being passed zeros. Setting it to the
        # age at which observation starts makes the entity contribute only the periods it was observed
        # in, while the baseline is estimated on the true clock. For an entity founded at or after the
        # regime start the two clocks coincide and `entry` is 0, so the change is a no-op there.
        founded = int(r.founded) if pd.notna(r.founded) else origin
        founded = min(founded, origin)          # a founding after the origin would be a data error
        entry.append(origin - founded)          # last period BEFORE observation begins
        for y in range(origin, last + 1):
            rows_ent.append(j)
            rows_year.append(y)
            rows_dur.append(y - founded + 1)
        if r.entity_id in term.index and r.terminated and lo <= r.exit_year <= hi:
            t = term.loc[r.entity_id]
            c = mapping.get(str(t.cause), CAUSE_UNKNOWN)
            d = int(r.exit_year) - founded + 1
            tL.append(max(d - 1, origin - founded))
            tR.append(d)
            cause.append(c)
            strat.append(str(t.dating_stratum))
        else:
            tL.append(origin - founded)
            tR.append(last - founded + 1)
            cause.append(CENSORED)
            strat.append("censored")

    df = pd.DataFrame({"ent": rows_ent, "year": rows_year, "dur": rows_dur})

    # ---- entity-year covariates ----
    size = mem.groupby(["entity_id", "year"]).size().rename("size").reset_index()
    key = df.assign(entity_id=[eid_list[i] for i in df.ent])
    j = key.merge(size, on=["entity_id", "year"], how="left")
    sz = j["size"].fillna(0).to_numpy(float)

    nodes = pd.read_parquet(NODES)[["year", "cow_code"] + NODE_COLS]
    memn = mem.merge(nodes, left_on=["ccode", "year"], right_on=["cow_code", "year"], how="left")
    agg = memn.groupby(["entity_id", "year"])[NODE_COLS].agg(["mean", "std"])
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    j2 = key.merge(agg.reset_index(), on=["entity_id", "year"], how="left")

    # internal cohesion: the coalition's own members' density in each relation. For T2 this is the
    # group-level phi the manifesto's §5 statistics are about, computed on the coalition itself.
    from penumbra.graph import focal_excluded_weight
    # By name, not by glob. T2 was the least exposed of the three call sites -- its features are built by
    # looping over `RELATIONS`, so the PTA files a glob picked up were loaded and then ignored -- but
    # "harmless because something downstream filters it" is the property that stopped being true in
    # `run_u2.py`, where the same glob added four features to a shortcut probe (D-38, D-39).
    missing = [r for r in RELATIONS if not (GRAPH / f"edges_{r}.parquet").exists()]
    if missing:
        raise FileNotFoundError(f"declared relations with no edge file: {missing}")
    edges = pd.concat([pd.read_parquet(GRAPH / f"edges_{r}.parquet").assign(relation=r)
                       for r in RELATIONS], ignore_index=True)
    edges = edges[edges.year.between(lo, hi)]
    if focal_excluded:
        co = edges[edges.relation == "igo_comembership"]
        others = edges[edges.relation != "igo_comembership"]
    from penumbra.umbra import HorizonAudit
    audit = HorizonAudit(edges, mem, ev)
    phi_cols = {}
    for rel in RELATIONS:
        lvl = phi_level if rel == "igo_comembership" else 1
        vals = np.full(len(df), np.nan)
        for (e, y), idx in key.groupby(["entity_id", "year"], sort=False).indices.items():
            ms = audit._members.get((e, int(y)))
            if ms is None:
                continue
            v = audit.phi(ms, int(y), rel, lvl)
            if focal_excluded and rel == "igo_comembership":
                # Remove the focal coalition's own contribution: every dyad inside it shares this
                # organisation, so its weight drops by one and the edge vanishes at zero.
                v = audit.phi(ms, int(y), rel, lvl + 1)
            vals[idx] = v
        phi_cols[f"phi_{rel}"] = vals

    X = np.column_stack([sz, np.log1p(sz)]
                        + [j2[c].to_numpy(float) for c in agg.columns]
                        + [phi_cols[c] for c in phi_cols])
    names = (["size", "log_size"] + list(agg.columns) + list(phi_cols))
    miss = np.isnan(X)
    if miss.any():
        X = np.where(miss, np.nanmean(X, axis=0), X)
        col = miss.any(axis=0)
        X = np.column_stack([X, miss[:, col].astype(float)])
        names += [f"missing_{names[k]}" for k in np.nonzero(col)[0]]
    X = np.nan_to_num(X)
    sd = X.std(axis=0)
    X = (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0)

    n_causes = 2 if collapse else 3
    panel = PeriodPanel(entity=df.ent.to_numpy(), period=df.dur.to_numpy(), X=X,
                        entry=np.array(entry, dtype=int),
                        t_L=np.array(tL), t_R=np.array(tR), cause=np.array(cause))
    meta = {"entity_ids": eid_list, "year": df.year.to_numpy(), "feature_names": names,
            "dating_stratum": strat, "n_causes": n_causes, "collapse": collapse,
            "focal_excluded": focal_excluded, "regime": list(regime),
            "n_entities": len(eid_list), "n_rows": len(df),
            "events_by_cause": {int(c): int((np.array(cause) == c).sum())
                                for c in np.unique(cause) if c != CENSORED},
            "rule_assigned_events": int(sum(1 for s in strat if s == "rule_assigned")),
            }
    return panel, meta

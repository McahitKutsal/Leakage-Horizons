r"""U1 under focal isolation, across the whole corpus. SYNTHESIS section 6's first remaining measurement.

V10 established the operation on two sources. On DESTA, where the back-dating width is coded per
agreement, focal isolation recovers it exactly (contrast 1.000) where the pooled relation-level
density the manifesto specifies returns 0.102. This script runs it over **every** entity, which is the
version SYNTHESIS calls "the one remaining measurement that could move a non-identification".

Four measurements, in the order they have to be taken, because each one invalidates the reading of the
one before it.

**A. Focal-isolation presence by horizon.** Is the acceding state already on the focal entity's own
membership record $\Delta$ years before its coded accession? Under honest dating this is 1.0 at
$\Delta = 0$ and 0.0 beyond, and any excess is back-dating of exactly that width. Split by entity type
and by dating stratum, because section 9.7's `rule_assigned` and `declared_resolution` events have dates of
lower resolution than `exact` ones and there is no reason for them to behave alike.

**B. The same, conditioned on first-time entry.** A state that was a member before, left, and rejoined
is on the record at long horizons for a reason that is not back-dating, and *the confound rises with
the horizon* because reaching further back is more likely to land inside a prior spell. Measured: the
pooled `declared_resolution` curve decays 0.363 -> 0.257 -> 0.136 -> 0.073, which is the textbook shape
of a four-year penumbra and is almost entirely this confound -- that stratum's recurrence rate is 30.7 %
against `exact`'s 6.2 %, so the artefact loads onto exactly the stratum that appears to have a penumbra.
Conditioned on first-time entry the same curve is 0.142 at $\Delta = 1$ and **0.000 beyond**.

**C. The pooled relation on the same events**, so V10's comparison is made on one corpus rather than
across two sources. This is the number deciding whether V10's factor of ten is a property of DESTA or
of the diagnostic.

**D. The matched contrast for every relation, horizon by horizon.** The decisive one. Section 5.4 sets the
band from relations declared not to carry the label, so if those anchors show the same decaying
contrast as $r^\star$, the quantity D-13's rule extracts is a difference in homophily strength rather
than a trace of the event. They do.

The first run of measurement A did not produce any of the above. It produced a **corpus defect**:
alliance presence sat at 0.458 at $\Delta = 1$ against organisation's 0.013, which traced to ATOP coding
a member once per treaty *phase*, so a founder of a multi-phase treaty acquired a spurious accession
dated to the later phase. 221 of 481 alliance events (45.9 %) were that artefact and the 0.458 was
reading it back. Fixed in D-28, recorded as V11; the script is kept in the form that found it so the
check runs on every future rebuild.

    python scripts/run_u1_isolation.py            # A, B, C, D
    python scripts/run_u1_isolation.py --quick     # A and B only; skips loading 790k edges
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.umbra import HorizonAudit  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402

LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"
HORIZONS = range(0, 9)
# The primary regime: LEDGER.md section 6, the window over which the set of non-empty relations is
# constant. No pooled number may span a coverage break.
REGIME = (1965, 2014)
FULL = 1
# r* first, then the anchors of section 5.4. `conflicts_with` is the only one with no homophily content
# and it is the only one that comes out flat, which is what makes the comparison interpretable.
RELATIONS = ["igo_comembership", "allies", "trades", "votes_with", "conflicts_with"]
R_STAR = "igo_comembership"
ANCHORS = ["trades", "votes_with", "conflicts_with"]
N_NEG = 2          # per positive per horizon; declared, not tuned
SEED = 0


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    ev = pd.read_parquet(LEDGER / "events.parquet")
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    return mem, ev.merge(ent[["entity_id", "entity_type"]], on="entity_id", how="left")


def _stub() -> pd.DataFrame:
    """A one-edge relation so the audit constructor has a graph. Focal isolation reads membership only."""
    return pd.DataFrame({"relation": ["_stub"], "year": [REGIME[0]],
                         "cow_i": [2], "cow_j": [20], "weight": [1]})


# ---------------------------------------------------------------- A and B: focal isolation
def isolation_table(mem: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    """One row per (accession, horizon): is the state on the focal entity's own record, and is this
    its first entry? `first_entry` is what separates back-dating from a prior membership spell."""
    audit = HorizonAudit(_stub(), mem, ev)
    first_mem = mem[mem.status == FULL].groupby(["entity_id", "ccode"]).year.min().to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()]

    rows = []
    for r in acc.itertuples():
        cc, t_ev = int(r.ccode), int(r.t_R)
        fm = first_mem.get((r.entity_id, cc))
        # A prior spell means the record carries this state for reasons predating the event, so the
        # trace at long horizons is recurrence. t_ev - 1 rather than t_ev: the year before the coded
        # accession is already the first horizon at which back-dating would show.
        first_entry = fm is None or fm >= t_ev - 1
        for d in HORIZONS:
            ms = audit._member_sets.get((r.entity_id, t_ev - d))
            if ms is None:
                continue
            rows.append({"entity_id": r.entity_id, "ccode": cc, "horizon": int(d),
                         "on_focal_record": float(cc in ms), "first_entry": first_entry,
                         "entity_type": r.entity_type, "dating_stratum": r.dating_stratum,
                         "interval_width": int(r.t_R - r.t_L)})
    return pd.DataFrame(rows)


def summarise(tp: pd.DataFrame, by: str) -> dict:
    out = {}
    for key, g in tp.groupby(by, dropna=False):
        curve = g.groupby("horizon").on_focal_record.mean()
        beyond = curve[curve.index >= 1]
        out[str(key)] = {
            "n_events": int((g.horizon == 0).sum()),
            "curve": {int(h): round(float(v), 4) for h, v in curve.items()},
            "at_horizon_0": round(float(curve.get(0, np.nan)), 4),
            # A step function's mean is a width, not a presence, so the max matters more: one
            # non-zero horizon is enough to widen the penumbra.
            "max_beyond_0": round(float(beyond.max()), 4) if len(beyond) else None,
            "recurrence_share": round(float(1 - g.loc[g.horizon == 0, "first_entry"].mean()), 4),
        }
    return out


# ---------------------------------------------------------------- C and D: relation-level contrasts
class _Star:
    """Share of a candidate's dyads into a member set that a relation carries, via the packed index."""

    def __init__(self, audit: HorizonAudit):
        self.n, self.ix, self.keys = audit._n, audit._ix, audit._keys

    def __call__(self, cc: int, others: np.ndarray, year: int, relation: str) -> float:
        if cc not in self.ix:
            return float("nan")
        oi = np.array([self.ix[int(m)] for m in others if int(m) in self.ix], np.int64)
        if oi.size == 0:
            return float("nan")
        ci = self.ix[cc]
        k = np.minimum(ci, oi) * np.int64(self.n) + np.maximum(ci, oi)
        arr = self.keys.get((relation, year))
        if arr is None:
            return 0.0
        p = np.clip(np.searchsorted(arr, k), 0, arr.size - 1)
        return float((arr[p] == k).mean())


def matched_contrast(mem: pd.DataFrame, ev: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    r"""Positive minus never-event-negative star density, per relation per horizon.

    Negatives are drawn from the same (entity, year) as each positive, for the reason V0 records: drawn
    across entity-years instead, positive groups have a mean size of 66 against the negatives' 18 and
    the statistic measures group size. Matching holds the group fixed so only the candidate's own
    relationship to the members can differ.
    """
    frames = [pd.read_parquet(GRAPH / f"edges_{r}.parquet").assign(relation=r) for r in RELATIONS]
    audit = HorizonAudit(pd.concat(frames, ignore_index=True), mem, ev)
    star = _Star(audit)

    all_states = np.sort(mem.ccode.unique())
    ever = mem[mem.status == FULL].groupby("entity_id").ccode.apply(set).to_dict()
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
                rows.append([d, label, float(who in ms)]
                            + [star(who, others, t, rel) for rel in RELATIONS])

    df = pd.DataFrame(rows, columns=["horizon", "label", "on_focal_record"] + RELATIONS)
    pos = df[df.label == 1].groupby("horizon")[RELATIONS].mean()
    neg = df[df.label == 0].groupby("horizon")[RELATIONS].mean()
    con = (pos - neg)

    # V10's comparison at corpus scale, on **the same rows**: the focal entity's own record against the
    # pooled relation the manifesto specifies, for the same events at the same horizons. This section was
    # dropped when the script was restructured and V12 went on quoting its two numbers, which is the
    # defect D-35 exists to prevent, committed in the text written to report D-35.
    p = df[df.label == 1]
    focal_step = float(p.loc[p.horizon == 0, "on_focal_record"].mean()
                       - p.loc[p.horizon >= 1, "on_focal_record"].mean())
    pooled_step = float(p.loc[p.horizon == 0, R_STAR].mean()
                        - p.loc[p.horizon >= 1, R_STAR].mean())

    def pack(frame):
        return {rel: {int(h): round(float(v), 4) for h, v in frame[rel].items()} for rel in RELATIONS}

    # The gap between r* and the *strongest* anchor is what D-13's rule reads as leakage. Reported
    # per horizon so the horizon at which it vanishes is visible rather than asserted.
    best_anchor = con[ANCHORS].max(axis=1)
    residual = con[R_STAR] - best_anchor
    return df, {
        "n_rows": int(len(df)), "n_positives": int(df.label.sum()),
        "positive": pack(pos), "negative": pack(neg), "contrast": pack(con),
        "retention_at_8": {rel: round(float(con[rel].iloc[-1] / con[rel].iloc[0]), 4)
                           for rel in RELATIONS if abs(con[rel].iloc[0]) > 1e-9},
        "r_star_minus_best_anchor": {int(h): round(float(v), 4) for h, v in residual.items()},
        # The step each instrument shows from horizon 0 to the mean beyond it, same rows both times.
        "focal_step": round(focal_step, 4),
        "pooled_step": round(pooled_step, 4),
        "focal_by_horizon": {int(h): round(float(v), 4)
                             for h, v in p.groupby("horizon").on_focal_record.mean().items()},
        "pooled_by_horizon": {int(h): round(float(v), 4)
                              for h, v in p.groupby("horizon")[R_STAR].mean().items()},
        "first_horizon_residual_below_0_01": next(
            (int(h) for h, v in residual.items() if v < 0.01), None),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "u1_isolation.json")
    ap.add_argument("--quick", action="store_true", help="A and B only; skips the edge load")
    args = ap.parse_args()

    mem, ev = load()
    acc = ev[ev.event_type == "accession"]
    print(f"accessions: {len(acc)} total, {int(acc.t_R.between(*REGIME).sum())} in "
          f"{REGIME[0]}-{REGIME[1]}, by type {acc.entity_type.value_counts().to_dict()}")

    tp = isolation_table(mem, ev)
    print(f"{len(tp)} (event, horizon) pairs under focal isolation\n")

    out = {"regime": list(REGIME), "horizons": list(HORIZONS),
           "n_accessions": int(len(acc)),
           "n_accessions_in_regime": int(acc.t_R.between(*REGIME).sum())}

    for label, sub in (("A. all accessions", tp),
                       ("B. first-time entry only", tp[tp.first_entry])):
        print(f"--- {label} ---")
        for dim in ("entity_type", "dating_stratum"):
            s = summarise(sub, dim)
            key = f"{'all' if 'all' in label else 'first_entry'}_by_{dim}"
            out[key] = s
            for k, v in s.items():
                print(f"  {k:22s} n={v['n_events']:5d} at 0: {v['at_horizon_0']}  "
                      f"max beyond: {v['max_beyond_0']}  recurrence: {v['recurrence_share']}")
                print(f"    {v['curve']}")
        print()

    if args.quick:
        out["matched_contrast"] = {"skipped": True}
    else:
        print("--- C/D. matched contrast per relation (organisation accessions in regime) ---")
        _, mc = matched_contrast(mem, ev)
        out["matched_contrast"] = mc
        print(f"  {mc['n_rows']} rows, {mc['n_positives']} positives")
        print(f"  {'h':>2} " + " ".join(f"{r[:9]:>10s}" for r in RELATIONS))
        for h in HORIZONS:
            print(f"  {h:>2} " + " ".join(f"{mc['contrast'][r][h]:>10.4f}" for r in RELATIONS))
        print(f"  retention at 8: {mc['retention_at_8']}")
        print(f"  r* minus best anchor: {mc['r_star_minus_best_anchor']}")
        print(f"  first horizon where that residual < 0.01: "
              f"{mc['first_horizon_residual_below_0_01']}")
        print(f"  V10's comparison on the same rows -- step from horizon 0 to the mean beyond it:")
        print(f"    focal isolation {mc['focal_step']}   pooled relation {mc['pooled_step']}")
        print(f"    focal  by horizon: {mc['focal_by_horizon']}")
        print(f"    pooled by horizon: {mc['pooled_by_horizon']}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, out, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

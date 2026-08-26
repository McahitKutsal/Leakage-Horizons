r"""Can the two instruments ever both be measurements on the same events of corpus A? No, and here is why.

Section 6.5's comparison has a weakness an external read named exactly. Corpus A codes one date per
membership for 94 percent of its events, so focal isolation returns zero there **by entailment**, and
showing that the pooled statistic reports something the focal statistic cannot express is not the same
as showing that the pooled statistic is wrong. The manuscript records the entailment honestly in
Section 3.4 and in Table 1, and honesty about a weakness does not remove it.

The obvious repair is to find a stratum of corpus A where focal isolation *measures*, and compare the
two instruments there as two measurements. Exactly one stratum qualifies: the **declared-resolution**
stratum, whose dates the source itself states are accurate only to five-year blocks, and which
Section 6.5 reports at a presence of 0.1419 at one period. This script went looking for that comparison
and found that it does not exist, for a reason worth reporting rather than working around.

**The stratum lies entirely before the analysis window.** The register declares its reduced accuracy for
organisations founded before 1965, so every one of the 447 declared-resolution accessions carries a
coded year of 1965 or earlier, and the pooled statistic is computed on relations that Section 5.4
confines to 1965 onwards because that is the maximal window over which the set of non-empty relations
does not change. Reading the pooled statistic at lead times one to eight from an event in 1965 means
reading it in 1957 to 1964, inside the coverage break the window exists to exclude. So the two
instruments cannot both be measurements on the same events anywhere in corpus A: where focal isolation
measures, the pooled statistic is not computable without reintroducing a confound the design removed,
and where the pooled statistic is computable, focal isolation is entailed.

That is a sharper statement of the objection than the objection, and it is the reason the paper's
falsification of the pooled reading has to rest on evidence that does not involve focal isolation at
all: the anchor indistinguishability of Table 7, the crossing lead time's bootstrap interval, the
recurrence decomposition, and the trade register where the width is printed and n is 759.

What the script reports, so the claim is checkable rather than argued:

* the declared-resolution stratum's year distribution, and how much of it falls inside the window;
* both instruments on the exactly dated stratum inside the window, which is the case where focal
  isolation is entailed, so the reader can see what the comparison looks like when it is available;
* both instruments on the in-window remnant of the declared-resolution stratum, **flagged as
  coverage-contaminated**, because reporting the number and refusing to use it is more useful than
  omitting it.

    python scripts/run_both_instruments.py
    python scripts/run_both_instruments.py --replicates 400
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from penumbra.umbra import HorizonAudit  # noqa: E402

LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"
RESULTS = ROOT / "results"
REGIME = (1965, 2014)
HORIZONS = list(range(0, 9))
RELATIONS = ["igo_comembership", "allies", "trades", "votes_with", "conflicts_with"]
R_STAR = "igo_comembership"
ANCHORS = ["trades", "votes_with", "conflicts_with"]
THRESHOLD = 0.01          # Section 6.5's own threshold on the residual
N_NEG = 2
SEED = 0
FULL = 1


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
        if arr is None or arr.size == 0:
            return 0.0
        return float(np.isin(k, arr).mean())


def _first_below(series: dict, threshold: float) -> int | None:
    for h in sorted(series):
        if h >= 1 and series[h] < threshold:
            return int(h)
    return None


def stratum_windows() -> dict:
    r"""Where each dating stratum sits relative to the analysis window.

    This is the finding. `declared_resolution` is assigned by the register's own accuracy field for
    organisations founded before 1965, so the stratum cannot reach into the window, and the graph
    Section 5.4 declares cannot reach out of it.
    """
    ev = pd.read_parquet(LEDGER / "events.parquet")
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()]
    out = {}
    for stratum, g in acc.groupby("dating_stratum"):
        yr = g.t_R.astype(int)
        out[str(stratum)] = {
            "n_accessions": int(len(g)),
            "first_year": int(yr.min()), "last_year": int(yr.max()),
            "inside_the_window": int(yr.between(*REGIME).sum()),
            "share_inside_the_window": round(float(yr.between(*REGIME).mean()), 4),
            "lead_times_reachable_inside_the_window": int(max(0, int(yr.max()) - REGIME[0])),
        }
    return out


def build() -> pd.DataFrame:
    """One row per (event, lead time, candidate), tagged with the event's dating stratum."""
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    ev = pd.read_parquet(LEDGER / "events.parquet")
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    ev = ev.merge(ent[["entity_id", "entity_type", "family_id"]], on="entity_id", how="left")

    frames = [pd.read_parquet(GRAPH / f"edges_{r}.parquet").assign(relation=r) for r in RELATIONS]
    audit = HorizonAudit(pd.concat(frames, ignore_index=True), mem, ev)
    star = _Star(audit)

    all_states = np.sort(mem.ccode.unique())
    ever = mem[mem.status == FULL].groupby("entity_id").ccode.apply(set).to_dict()
    first_mem = mem[mem.status == FULL].groupby(["entity_id", "ccode"]).year.min().to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna() & ev.t_R.between(*REGIME)]
    rng = np.random.default_rng(SEED)

    rows = []
    for r in acc.itertuples():
        cc, t_ev, eid = int(r.ccode), int(r.t_R), r.entity_id
        # First entry only, which is what Section 6.5 conditions on: a prior spell puts the state on
        # the record for reasons that predate the event, and mechanism (i) is that confound.
        fm = first_mem.get((eid, cc))
        if not (fm is None or fm >= t_ev - 1):
            continue
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
                rows.append([r.dating_stratum, r.family_id, eid, t_ev, d, label,
                             float(who in ms), int(t < REGIME[0])]
                            + [star(who, others, t, rel) for rel in RELATIONS])
    return pd.DataFrame(rows, columns=["stratum", "family", "entity_id", "event_year", "horizon",
                                       "label", "on_focal_record", "before_window"] + RELATIONS)


def read_both(df: pd.DataFrame) -> dict:
    """Both instruments on one set of events: what each returns, and what each is."""
    pos, neg = df[df.label == 1], df[df.label == 0]
    focal = {int(h): round(float(v), 4)
             for h, v in pos.groupby("horizon").on_focal_record.mean().items()}
    con = (pos.groupby("horizon")[RELATIONS].mean() - neg.groupby("horizon")[RELATIONS].mean())
    best = con[ANCHORS].max(axis=1)
    residual = {int(h): float(v) for h, v in (con[R_STAR] - best).items()}
    pooled = {int(h): float(v) for h, v in con[R_STAR].items()}
    return {
        "n_events": int((pos.horizon == 0).sum()),
        "n_families": int(pos.family.nunique()),
        "share_of_rows_read_before_the_window": round(float(df.before_window.mean()), 4),
        "focal_curve": focal,
        "focal_estimate": _first_below(focal, 1e-9),
        "pooled_contrast": {k: round(v, 4) for k, v in pooled.items()},
        "residual": {k: round(v, 4) for k, v in residual.items()},
        "residual_rule_estimate": _first_below(residual, THRESHOLD),
        "unbanded_rule_estimate": _first_below(pooled, THRESHOLD),
        "contrast_by_relation": {rel: {int(h): round(float(v), 4) for h, v in con[rel].items()}
                                 for rel in RELATIONS},
    }


def interval(df: pd.DataFrame, n_rep: int) -> dict:
    """A family-level bootstrap on the three estimates."""
    fams = df.family.dropna().unique()
    rng = np.random.default_rng(SEED)
    focal, resid, unb = [], [], []
    for _ in range(n_rep):
        draw = rng.choice(fams, size=len(fams), replace=True)
        sub = pd.concat([df[df.family == f] for f in draw], ignore_index=True)
        r = read_both(sub)
        focal.append(9 if r["focal_estimate"] is None else r["focal_estimate"])
        resid.append(9 if r["residual_rule_estimate"] is None else r["residual_rule_estimate"])
        unb.append(9 if r["unbanded_rule_estimate"] is None else r["unbanded_rule_estimate"])

    def pack(v):
        a = np.asarray(v, float)
        return {"median": float(np.median(a)), "lo": float(np.percentile(a, 2.5)),
                "hi": float(np.percentile(a, 97.5)),
                "distribution": {int(k): int(c) for k, c in
                                 zip(*np.unique(a.astype(int), return_counts=True))}}
    return {"replicates": n_rep, "focal_isolation": pack(focal),
            "residual_rule": pack(resid), "unbanded_rule": pack(unb)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=400)
    ap.add_argument("--json", type=Path, default=RESULTS / "both_instruments.json")
    args = ap.parse_args()

    print("can the two instruments both be measurements on the same events of corpus A?\n")
    win = stratum_windows()
    for stratum, v in win.items():
        print(f"  {stratum:20s} {v['n_accessions']:5d} accessions, {v['first_year']} to "
              f"{v['last_year']}, {v['inside_the_window']} inside the window "
              f"({v['share_inside_the_window'] * 100:.1f} percent)")
    dr = win.get("declared_resolution", {})
    if dr:
        print(f"\n  the stratum where focal isolation measures ends at {dr['last_year']}, and the "
              f"window opens at {REGIME[0]}, so the deepest lead time the pooled statistic could be "
              f"read at inside the window is {dr['lead_times_reachable_inside_the_window']}")

    df = build()
    print(f"\n{len(df):,} (event, lead time, candidate) rows over "
          f"{df[df.label == 1].entity_id.nunique()} groups\n")

    out = {}
    for stratum in sorted(df.stratum.dropna().unique()):
        sub = df[df.stratum == stratum].reset_index(drop=True)
        r = read_both(sub)
        out[str(stratum)] = r
        flag = ("  COVERAGE CONTAMINATED" if r["share_of_rows_read_before_the_window"] > 0.05
                else "")
        print(f"  {stratum:20s} n={r['n_events']:5d} over {r['n_families']:3d} families, "
              f"{r['share_of_rows_read_before_the_window'] * 100:.0f} percent of rows read before "
              f"the window{flag}")
        print(f"    focal isolation      curve {[r['focal_curve'].get(i) for i in range(0, 4)]}"
              f"  -> estimate {r['focal_estimate']}")
        print(f"    pooled contrast      {[r['pooled_contrast'].get(i) for i in range(0, 9)]}")
        print(f"    residual on the band -> estimate {r['residual_rule_estimate']}"
              f"   unbanded -> {r['unbanded_rule_estimate']}")

    drf = df[df.stratum == "declared_resolution"].reset_index(drop=True)
    ci = interval(drf, args.replicates) if len(drf) else {}
    if ci:
        print(f"\n  the in-window remnant, {args.replicates} family-level replicates, reported and "
              f"not used")
        for name in ("focal_isolation", "residual_rule", "unbanded_rule"):
            v = ci[name]
            print(f"    {name:16s} median {v['median']:.0f}  interval [{v['lo']:.0f}, {v['hi']:.0f}]")

    payload = {
        "question": ("can the two instruments both be measurements on the same events of corpus A, "
                     "so that their disagreement falsifies the pooled reading rather than describing "
                     "what one instrument cannot express"),
        "answer": ("no, and not only because 94 percent of events are single dated. The one stratum "
                   "where focal isolation measures lies entirely before the analysis window, so the "
                   "pooled statistic is not computable on it without reintroducing the coverage break "
                   "Section 5.4 excludes by design"),
        "regime": list(REGIME), "horizons": HORIZONS, "threshold": THRESHOLD,
        "anchors": ANCHORS, "negatives_per_positive": N_NEG,
        "stratum_windows": win,
        "by_stratum": out,
        "in_window_remnant_interval": ci,
        "what_carries_the_falsification_instead": [
            "the anchor indistinguishability of Table 7, which needs no focal isolation",
            "the crossing lead time's bootstrap interval over the whole examined range",
            "the recurrence decomposition of the unconditioned four-period decay",
            "the trade register of Section 5.3, where the width is printed and n is 759",
        ],
    }
    write_result(args.json, payload, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

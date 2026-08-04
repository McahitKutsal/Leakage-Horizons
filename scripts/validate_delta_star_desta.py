"""Grade $\\Delta^\\star$ against an externally coded back-dating width. §6's unexecuted validation.

The synthetic testbed grades the estimator against a $\\beta$ we set. DESTA grades it against one the
**source** sets: an agreement signed at $s$ takes legal effect at $f$, so a relation built from
DESTA's signature-dated membership carries a dyad $f - s$ years before the event it belongs to. That
width is coded per agreement, which makes it the only real-data ground truth the programme has (§6).

Two tests, and the first exists because of V8's lesson. There, 336 accessions gave a clique contrast
whose standard error equalled the effect, and the pre-specified rule returned a $\\Delta^\\star$ that
was two noise-floor series crossing. DESTA supplies **192** accessions, fewer still, so a
band-crossing test would be weaker yet. But knowing $\\beta$ per event allows a direct measurement
that does not need the band at all:

**Test 1 — trace presence.** For each accession with gap $g$, is the signature-dated dyad present in
$G_t$ at horizon $\\Delta$? It must be for $\\Delta \\leq g$ and absent for $\\Delta > g$. This checks
the construction and measures back-dating directly, with one observation per (event, horizon) pair
rather than one per event.

**Test 2 — does the estimator recover it?** Run the pre-specified rule of D-13 with
$r^\\star = $ signature-dated PTA co-membership and see whether $\\Delta^\\star_{\\text{lo}}$ lands at
$g + 1$, as it did in 6 of 6 synthetic settings. Test 1 says what the answer should be; test 2 says
whether the instrument finds it.

    python scripts/validate_delta_star_desta.py
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.desta import treaties  # noqa: E402

WINDOW = (1946, 2014)


def pta_relations(window=WINDOW) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Two co-membership relations over the same agreements, dated differently.

    `signature` admits an agreement's dyads from the year it was signed; `force` from the year it
    took legal effect. They are identical in every other respect, so their difference **is** the
    back-dating, and its width is the source's own `gap`.
    """
    t = treaties(window)
    base = t[(t.entry_type == "base_treaty") & (t.n_members >= 2)]
    lo, hi = window
    rows_sig, rows_frc, ev = [], [], []
    for r in base.itertuples():
        f = r.force_year
        start_sig = int(r.sig_year)
        start_frc = int(f) if not pd.isna(f) else None
        for u, v in combinations(sorted(r.members), 2):
            a, b = (u, v) if u < v else (v, u)
            for y in range(max(start_sig, lo), hi + 1):
                rows_sig.append((y, a, b))
            if start_frc is not None:
                for y in range(max(start_frc, lo), hi + 1):
                    rows_frc.append((y, a, b))

    # Accession entries are the events: an acceding state's legal entry is its own force year.
    for r in t[t.entry_type == "accession"].itertuples():
        f = r.force_year
        if pd.isna(f) or not r.acceded:
            continue
        for cc in r.acceded:
            ev.append({"base_treaty": r.base_treaty, "ccode": int(cc),
                       "sig_year": int(r.sig_year), "force_year": int(f),
                       "gap": int(f) - int(r.sig_year),
                       "members": [m for m in r.members if m != cc]})

    def frame(rows):
        if not rows:
            return pd.DataFrame(columns=["year", "cow_i", "cow_j", "weight"])
        d = pd.DataFrame(rows, columns=["year", "cow_i", "cow_j"])
        return (d.groupby(["year", "cow_i", "cow_j"], as_index=False).size()
                .rename(columns={"size": "weight"}))

    return frame(rows_sig), frame(rows_frc), pd.DataFrame(ev)


def test_trace_presence(sig: pd.DataFrame, events: pd.DataFrame, horizons=range(0, 9)) -> dict:
    """Is the signature-dated dyad present Delta years before the event, as a function of Delta?

    Presence is measured on the acceding state's star into the existing members, which is the object
    U1's phi is built from. Split by whether the horizon falls inside the agreement's own coded gap.
    """
    idx = {}
    for r in sig.itertuples():
        idx.setdefault(int(r.year), set()).add((int(r.cow_i), int(r.cow_j)))

    rows = []
    for r in events.itertuples():
        if not r.members:
            continue
        for d in horizons:
            t = r.force_year - d
            if t < WINDOW[0]:
                continue
            present = idx.get(t, set())
            hits = sum(1 for m in r.members
                       if (min(r.ccode, m), max(r.ccode, m)) in present)
            rows.append({"gap": r.gap, "horizon": d,
                         "share_present": hits / len(r.members),
                         "inside_gap": bool(d <= r.gap)})
    df = pd.DataFrame(rows)
    if df.empty:
        return {"error": "no usable event-horizon pairs"}
    by_h = df.groupby("horizon").share_present.mean()
    inside = df[df.inside_gap].share_present.mean()
    outside = df[~df.inside_gap].share_present.mean()
    # The sharp prediction: presence is high inside the coded gap and collapses outside it.
    return {
        "n_pairs": int(len(df)), "n_events": int(events.shape[0]),
        "share_present_by_horizon": {int(k): round(float(v), 4) for k, v in by_h.items()},
        "mean_inside_gap": round(float(inside), 4),
        "mean_outside_gap": round(float(outside), 4),
        "contrast": round(float(inside - outside), 4),
        "by_gap": {int(g): {int(h): round(float(v), 4)
                            for h, v in s.groupby("horizon").share_present.mean().items()}
                   for g, s in df.groupby("gap") if g in (0, 1, 2, 3)},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "desta_delta_star.json")
    args = ap.parse_args()

    sig, frc, events = pta_relations()
    print(f"signature-dated relation: {len(sig)} edge-years")
    print(f"force-dated relation:     {len(frc)} edge-years")
    print(f"difference (back-dating): {len(sig) - len(frc)} edge-years")
    print(f"accession events with a coded force year: {len(events)}")
    if len(events):
        g = events.gap
        print(f"  their gaps: median {g.median()}  mean {g.mean():.2f}  "
              f"share >=1 {float((g >= 1).mean()):.3f}  share >=2 {float((g >= 2).mean()):.3f}")

    print("\n--- Test 1: is the trace present exactly inside the coded gap? ---")
    t1 = test_trace_presence(sig, events)
    if "error" in t1:
        print(f"  {t1['error']}")
    else:
        print(f"  {t1['n_pairs']} event-horizon pairs from {t1['n_events']} events")
        print(f"  share of member dyads present, by horizon: {t1['share_present_by_horizon']}")
        print(f"  inside the coded gap  {t1['mean_inside_gap']}")
        print(f"  outside the coded gap {t1['mean_outside_gap']}")
        print(f"  contrast              {t1['contrast']}")
        for gp, curve in t1["by_gap"].items():
            print(f"    agreements with gap={gp}: {curve}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps({
        "window": list(WINDOW),
        "n_edge_years_signature": int(len(sig)),
        "n_edge_years_force": int(len(frc)),
        "n_accession_events": int(len(events)),
        "event_gaps": ({"median": float(events.gap.median()),
                        "mean": round(float(events.gap.mean()), 3),
                        "distribution": {int(k): int(v)
                                         for k, v in events.gap.value_counts().sort_index().items()}}
                       if len(events) else {}),
        "test1_trace_presence": t1,
    }, indent=2, default=str))
    sig.to_parquet(ROOT / "data" / "graph" / "edges_pta_signature.parquet", index=False)
    frc.to_parquet(ROOT / "data" / "graph" / "edges_pta_force.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

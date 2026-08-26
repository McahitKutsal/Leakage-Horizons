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
from penumbra.provenance import write_result  # noqa: E402

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


def test_focal_only(events: pd.DataFrame, horizons=range(0, 9)) -> dict:
    r"""**Test 3 — focal isolation, and it is a construction check rather than a measurement.**

    V10 reports this as "the back-dating is real and exact": presence 1.00 for $\Delta \leq$ gap and 0.00
    beyond, at every gap, contrast 1.000. The table is right and the framing overstated it, which is
    what writing this function established and D-34 records.

    The focal relation admits the accession entry's dyads from its own `sig_year`; the event is dated at
    `force_year`; and `gap` **is** `force_year - sig_year`. So

        presence at horizon d  <=>  force_year - d >= sig_year  <=>  d <= gap

    with no data-dependent step anywhere. The step table cannot come out otherwise, and the marginal
    curve is the gap distribution restated -- `focal_only_by_horizon[d]` is the share of events with
    gap >= d. Asserted below rather than described, because a claim that something is entailed should
    fail loudly if it stops being entailed.

    What the check is worth is not nothing: a construction error, an off-by-one in the horizon, or a gap
    computed from the wrong pair of dates would all break it. It verifies the pipeline. It does **not**
    independently recover $\beta$, and the programme's evidence that the estimator recovers a known
    $\beta$ is C18's synthetic calibration, where the generator sets $\beta$ and the pre-specified rule
    of D-13 returns $\beta + 1$ in 6 of 6 settings.

    The informative half of V10 is Test 4's comparison: the same corpus, the pooled density the
    manifesto specifies, contrast 0.102.
    """
    rows = []
    for r in events.itertuples():
        if not r.members:
            continue
        for d in horizons:
            if r.force_year - d < WINDOW[0]:
                continue
            rows.append({"gap": r.gap, "horizon": d,
                         "present": float(d <= r.gap), "inside_gap": bool(d <= r.gap)})
    df = pd.DataFrame(rows)
    if df.empty:
        return {"error": "no usable event-horizon pairs"}

    by_h = df.groupby("horizon").present.mean()
    # The entailment, stated as a test. Both must hold exactly or the construction is wrong.
    assert df.loc[df.inside_gap, "present"].eq(1.0).all(), "presence not 1 inside the coded gap"
    assert df.loc[~df.inside_gap, "present"].eq(0.0).all(), "presence not 0 outside the coded gap"
    share_ge = {int(d): float((df[df.horizon == d].gap >= d).mean()) for d in by_h.index}
    entailed = all(abs(by_h[d] - share_ge[d]) < 1e-12 for d in by_h.index)

    return {
        "focal_only_by_horizon": {int(k): float(v) for k, v in by_h.items()},
        "inside": 1.0, "outside": 0.0, "contrast": 1.0,
        "share_with_gap_at_least_horizon": share_ge,
        "curve_equals_gap_distribution": bool(entailed),
        "is_construction_check_not_measurement": True,
        "note": ("Presence at horizon d is equivalent to d <= gap by construction, since the focal "
                 "relation is dated from sig_year, the event from force_year, and gap is their "
                 "difference. The step table verifies the pipeline; it does not recover beta "
                 "independently. See D-34 and C18."),
        "by_gap": {int(g): {int(h): float(v)
                            for h, v in s.groupby("horizon").present.mean().items()}
                   for g, s in df.groupby("gap") if g <= 4},
    }


def test_igo_focal_only(horizons=range(0, 9)) -> dict:
    r"""**Test 4's negative control** — the same isolation on COW IGO, through the library.

    Reported by V10 as $\beta = 0$ measured, "two corpora, one with an exact known penumbra and one with
    none, and the same instrument on both". The number is right; the inference is weaker than that
    sentence, for the reason V12 generalises. COW IGO records **one** date per membership, so focal
    isolation has no second date to measure against and a residual of zero is entailed by the source's
    structure rather than discovered in it. Focal isolation detects back-dating only where a source
    codes two dates. DESTA does; ATOP and COW IGO do not.

    The residual it *does* measure is recurrence, which is a real finding and is what V12 confirmed at
    corpus scale: presence beyond $\Delta = 0$ rises with the horizon, and conditioning on first entry
    removes it entirely.
    """
    from penumbra.umbra import HorizonAudit

    led = ROOT / "data" / "ledger"
    mem = pd.read_parquet(led / "membership.parquet")
    ev = pd.read_parquet(led / "events.parquet")
    stub = pd.DataFrame({"relation": ["_stub"], "year": [1965],
                         "cow_i": [2], "cow_j": [20], "weight": [1]})
    audit = HorizonAudit(stub, mem, ev)
    ent = pd.read_parquet(led / "entities.parquet")
    igo = set(ent.loc[ent.entity_type == "organisation", "entity_id"])
    tp = audit.trace_presence(ev[ev.entity_id.isin(igo)], horizons=horizons)
    by_h = tp.groupby("horizon").on_focal_record.mean()

    first = mem[mem.status == 1].groupby(["entity_id", "ccode"]).year.min().to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna() & ev.entity_id.isin(igo)]
    recur = sum(1 for r in acc.itertuples()
                if (first.get((r.entity_id, int(r.ccode))) or 10**9) < int(r.t_R) - 1)
    return {
        "library_by_horizon": {int(k): float(v) for k, v in by_h.items()},
        "horizon_ge1_mean": float(by_h[by_h.index >= 1].mean()),
        "beta_is_entailed_by_single_dating": True,
        "note": ("COW IGO records one date per membership, so a zero residual is entailed rather than "
                 "measured -- focal isolation needs a second coded date to have anything to detect. "
                 "The residual that IS measured is recurrence; see V12 and D-34."),
        "recurrence_cross_check": {
            "accession_events": int(len(acc)),
            "events_whose_state_was_a_member_before": int(recur),
            "share": round(recur / max(len(acc), 1), 4),
        },
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

    print("\n--- Test 3: focal isolation (construction check, see D-34) ---")
    t3 = test_focal_only(events)
    if "error" in t3:
        print(f"  {t3['error']}")
    else:
        print(f"  presence by horizon: {({k: round(v, 4) for k, v in t3['focal_only_by_horizon'].items()})}")
        print(f"  inside {t3['inside']}  outside {t3['outside']}  contrast {t3['contrast']}")
        print(f"  curve equals the gap distribution exactly: {t3['curve_equals_gap_distribution']}")
        print("  -> entailed by construction; the informative comparison is Test 1's pooled 0.102")
        for gp, curve in t3["by_gap"].items():
            print(f"    gap={gp}: {curve}")
    write_result(ROOT / "results" / "desta_focal_only.json", t3, indent=2)

    print("\n--- Test 4: the same isolation on COW IGO (negative control) ---")
    t4 = test_igo_focal_only()
    print(f"  presence by horizon: {({k: round(v, 4) for k, v in t4['library_by_horizon'].items()})}")
    print(f"  mean beyond horizon 0: {t4['horizon_ge1_mean']:.4f}")
    print(f"  recurrence cross-check: {t4['recurrence_cross_check']}")
    print("  -> beta = 0 is entailed by COW IGO coding one date; the residual is recurrence")
    write_result(ROOT / "results" / "igo_focal_only.json", t4, indent=2)

    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, {
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
    }, indent=2, default=str)
    sig.to_parquet(ROOT / "data" / "graph" / "edges_pta_signature.parquet", index=False)
    frc.to_parquet(ROOT / "data" / "graph" / "edges_pta_force.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

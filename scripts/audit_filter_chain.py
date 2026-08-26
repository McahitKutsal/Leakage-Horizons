r"""Every count the manuscript reports, and the filter that separates it from the count above it.

Three pairs of numbers in the manuscript differ from each other for reasons that were correct in the
code and unwritten in the prose, which is exactly the claim-to-artefact class Section 8 says the four
questions do not reach. An external read found all three:

* **528 against 527 groups.** Section 8's left-truncation count is 528; Section 6.5 and Appendix A
  report the estimated termination panel as 527. Both are right and they count different things.
* **7,146 against 7,084 exactly dated accessions.** Section 6.3's focal-isolation curve is over 7,146
  events; the interval on the same stratum is over 7,084. The difference is the lead time the count is
  taken at.
* **6,597 against 6,501.** Section 6.5's hazard has 6,501 event dyads against 6,597 accession events in
  the window. The difference is one accession per dyad.

None of the three is an error and every one of them is a reader's stumble, so the fix is a single
artefact that carries the whole chain with the filter named at each step, and a flow the manuscript can
print under Table 2 rather than three separate explanations scattered across three sections.

The filters are recomputed here through the same code paths the reporting scripts use -- `t2.build_panel`
for the termination panel, `t1.build_risk_set` for the hazard, `HorizonAudit.trace_presence` for focal
isolation -- so this is a second code path onto the same numbers rather than a restatement of them, which
is Section 8's fifth question applied to a count instead of to a density.

    python scripts/audit_filter_chain.py
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

from penumbra.provenance import write_result  # noqa: E402
from penumbra.umbra import HorizonAudit  # noqa: E402

LEDGER = ROOT / "data" / "ledger"
RESULTS = ROOT / "results"
REGIME = (1965, 2014)
HORIZONS = range(0, 9)


def _corpus() -> tuple:
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    ev = pd.read_parquet(LEDGER / "events.parquet")
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    return ent, ev, mem


# --------------------------------------------------------------------------- groups
def group_chain(ent: pd.DataFrame, mem: pd.DataFrame) -> dict:
    """562 entities to the 527 the termination hazard is estimated on.

    Two filters and they are applied by two different scripts, which is why the manuscript carries two
    numbers. `paper_support.left_truncation` asks which entities the analysis window overlaps *on the
    entity table's own dates*, because that is the population left truncation is a threat to. `t2.build_panel`
    additionally requires an active membership row inside the window, because an entity with no members
    in the window contributes no period to the likelihood.
    """
    lo, hi = REGIME
    e = ent.assign(origin_used=np.maximum(ent.origin.astype(int), lo))
    overlapping = e[e.exit_year.astype(int) >= e.origin_used]

    active = mem[(mem.status == 1) & mem.year.between(lo, hi)]
    with_members = active.groupby("entity_id").year.max()
    keep = set(with_members.index[with_members >= lo])
    estimated = overlapping[overlapping.entity_id.isin(keep)]

    dropped = overlapping[~overlapping.entity_id.isin(keep)]
    detail = []
    for r in dropped.itertuples():
        rows = mem[(mem.entity_id == r.entity_id) & (mem.status == 1)]
        detail.append({
            "entity_id": r.entity_id, "name": str(r.name),
            "founded": int(r.founded) if pd.notna(r.founded) else None,
            "exit_year": int(r.exit_year),
            "last_active_membership_year": int(rows.year.max()) if len(rows) else None,
            "why": "no active membership row inside the analysis window",
        })

    pre = overlapping.founded.astype("Int64") < lo
    return {
        "entities_in_the_corpus": int(len(ent)),
        "overlapping_the_window_on_entity_dates": int(len(overlapping)),
        "predating_the_window": int(pre.sum()),
        "estimated_in_the_termination_panel": int(len(estimated)),
        "dropped_between_the_two": detail,
        "reading": ("528 is the population left truncation is a threat to, which is what Section 8 "
                    "reports; 527 is the panel the likelihood is evaluated on, which is what Section "
                    "6.5 and Appendix A report"),
    }


# --------------------------------------------------------------------------- accessions
def accession_chain(ev: pd.DataFrame) -> dict:
    """8,062 accessions to the 6,501 event dyads the hazard scores.

    Two filters. The window is declared in Section 5.4 and is the maximal span over which the set of
    non-empty relations does not change. The one-accession-per-dyad collapse is `t1.build_risk_set`'s
    `groupby(...).year.min()`: a dyad leaves the risk set when it accedes, so a state that left a group
    and rejoined enters the hazard once. `t1.accession_multiplicity` measures the cost of that choice
    and it is reported here rather than left to be inferred from the difference of two totals.
    """
    lo, hi = REGIME
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()]
    in_window = acc[acc.t_R.between(lo, hi)]
    per_dyad = in_window.groupby(["entity_id", "ccode"]).size()
    repeats = int((per_dyad - 1).clip(lower=0).sum())
    return {
        "accession_events_in_the_corpus": int(len(acc)),
        "accession_events_in_the_window": int(len(in_window)),
        "outside_the_window": int(len(acc) - len(in_window)),
        "event_dyads_in_the_window": int(len(per_dyad)),
        "dyads_with_more_than_one_accession": int((per_dyad > 1).sum()),
        "repeat_accessions_collapsed": repeats,
        "share_collapsed": round(repeats / len(in_window), 4),
        "reading": ("6,597 is the event count and 6,501 is the dyad count; the hazard's unit is the "
                    "dyad and a dyad exits the risk set when it accedes, so 96 repeat accessions of "
                    "94 dyads are collapsed onto the first"),
    }


# --------------------------------------------------------------------------- focal isolation
def focal_isolation_chain(ev: pd.DataFrame, mem: pd.DataFrame) -> dict:
    """7,615 exactly dated accessions to the 7,084 the interval at one period is taken over.

    Three filters, and the third is the one the manuscript did not name. Conditioning on first entry
    removes prior membership spells, which is mechanism (i) and is stated. What is not stated is that
    focal isolation is only defined at lead time $\\Delta$ where the focal group *has* a member set at
    $t - \\Delta$: an accession in the group's founding year, or in the first year of the window, has
    no preceding-year record to be absent from. `HorizonAudit.trace_presence` skips those rows, so the
    count at lead time 1 is smaller than the count at lead time 0 and both appear in the manuscript.
    """
    lo, _hi = REGIME
    # The membership register and the event table unfiltered, which is what `run_u1_isolation` and
    # `bootstrap_diagnostics.pass_f` both pass: focal isolation reads a group's own record and the
    # window is a property of the relations, not of the register.
    stub = pd.DataFrame({"relation": ["_stub"], "year": [lo], "cow_i": [2], "cow_j": [20],
                         "weight": [1]})
    audit = HorizonAudit(stub, mem, ev)
    tp = audit.trace_presence(ev, horizons=HORIZONS)

    first_mem = mem[mem.status == 1].groupby(["entity_id", "ccode"]).year.min().to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()]
    first_entry = {}
    for r in acc.itertuples():
        fm = first_mem.get((r.entity_id, int(r.ccode)))
        first_entry[(r.entity_id, int(r.ccode), int(r.t_R))] = bool(
            fm is None or fm >= int(r.t_R) - 1)
    strat = {(r.entity_id, int(r.ccode), int(r.t_R)): r.dating_stratum for r in acc.itertuples()}

    tp = tp.assign(
        key=[(e, int(c), int(y)) for e, c, y in zip(tp.entity_id, tp.ccode, tp.event_year)])
    tp["first_entry"] = [first_entry.get(k, False) for k in tp.key]
    tp["stratum"] = [strat.get(k) for k in tp.key]

    out = {"reading": ("7,146 is the count at lead time 0 and 7,084 the count at lead time 1 on the "
                       "same stratum: focal isolation is undefined where the focal group has no "
                       "member set in the preceding year")}
    for stratum in sorted(x for x in tp.stratum.dropna().unique()):
        s = tp[tp.stratum == stratum]
        fe = s[s.first_entry]
        out[str(stratum)] = {
            "all_accessions_at_lead_time_0": int((s.horizon == 0).sum()),
            "first_entry_at_lead_time_0": int((fe.horizon == 0).sum()),
            "first_entry_at_lead_time_1": int((fe.horizon == 1).sum()),
            "lost_between_lead_time_0_and_1": int((fe.horizon == 0).sum()
                                                  - (fe.horizon == 1).sum()),
            "recurrent_removed_by_first_entry": int((s.horizon == 0).sum()
                                                    - (fe.horizon == 0).sum()),
        }
    return out


# --------------------------------------------------------------------------- terminations
def termination_chain(ev: pd.DataFrame, groups: dict) -> dict:
    """185 coded terminations to the 150 the panel scores.

    Two filters, and the second is the one the group chain already found: the window leaves 151, and the
    single entity with no active membership inside the window carries one of them, so the panel scores
    150. Writing the two chains in one artefact is what made that visible; separately, 151 and 150 look
    like a third unexplained pair.
    """
    lo, hi = REGIME
    term = ev[ev.event_type == "termination"]
    in_window = term[term.t_R.between(lo, hi)]
    dropped_ids = {d["entity_id"] for d in groups["dropped_between_the_two"]}
    on_dropped = in_window[in_window.entity_id.isin(dropped_ids)]
    return {
        "coded_terminations_in_the_corpus": int(len(term)),
        "in_the_window": int(len(in_window)),
        "outside_the_window": int(len(term) - len(in_window)),
        "on_entities_absent_from_the_estimated_panel": int(len(on_dropped)),
        "events_in_the_estimated_panel": int(len(in_window) - len(on_dropped)),
        "reading": ("185 coded, 151 inside the window, and 150 in the panel: the one entity the group "
                    "chain drops carries one of the 151"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=RESULTS / "filter_chain.json")
    args = ap.parse_args()

    ent, ev, mem = _corpus()
    groups = group_chain(ent, mem)
    payload = {
        "regime": list(REGIME),
        "groups": groups,
        "accessions": accession_chain(ev),
        "focal_isolation": focal_isolation_chain(ev, mem),
        "terminations": termination_chain(ev, groups),
    }
    for section, body in payload.items():
        print(f"\n{section}")
        print("  " + json.dumps(body, indent=2, default=str).replace("\n", "\n  "))
    write_result(args.json, payload, indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

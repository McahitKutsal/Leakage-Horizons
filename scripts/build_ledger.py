"""Build LEDGER and validate it before writing anything.

Validation is not a smoke test. Every check here corresponds to a way the corpus could be wrong
that would not show up as an error later -- it would show up as a plausible number. That is the
failure mode CLIQUEBAIT documents in the benchmark it audits, and the reason PROTOCOL section 1 puts
coverage verification against the materialised artefact rather than the documentation.

    python scripts/build_ledger.py                 # build, validate, write
    python scripts/build_ledger.py --dry-run       # build and validate only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.ledger import (BRACKETED, DECLARED, EXACT, RULE_ASSIGNED,  # noqa: E402
                             WINDOW_END, WINDOW_START, build)

OUT = ROOT / "data" / "ledger"


def validate(tabs: dict[str, pd.DataFrame]) -> list[str]:
    ent, ev, mem = tabs["entities"], tabs["events"], tabs["membership"]
    tabs = {k: v for k, v in tabs.items() if not k.startswith("_")}
    fail: list[str] = []

    def check(ok: bool, msg: str) -> None:
        if not ok:
            fail.append(msg)

    check(ent.entity_id.is_unique, "entity_id is not unique")
    check(ev.event_id.is_unique, "event_id is not unique")
    check(set(ev.entity_id) <= set(ent.entity_id), "events reference unknown entities")
    check(set(mem.entity_id) <= set(ent.entity_id), "membership references unknown entities")

    # Every entity must sit in exactly one family or the bootstrap silently drops it.
    check(ent.family_id.notna().all(), "entities with no family_id")
    check(len(tabs["families"]) == len(ent), "families table does not cover every entity once")

    # The interval convention: (t_L, t_R] with exact events at t_R = t_L + 1. A zero or negative
    # width contributes S(t_L) - S(t_R) <= 0 to the likelihood, which is not a probability.
    check((ev.t_R > ev.t_L).all(), "events with non-positive interval width")
    exact = ev[ev.dating_stratum == EXACT]
    check(((exact.t_R - exact.t_L) == 1).all(), "exact events whose width is not 1")

    # knowable_from >= t_R always, and strictly greater only for the rule-assigned stratum.
    check((ev.knowable_from >= ev.t_R).all(), "events knowable before they ended")
    ra = ev[ev.dating_stratum == RULE_ASSIGNED]
    check((ra.knowable_from > ra.t_R).all() if len(ra) else True,
          "rule-assigned events with no knowability lag")
    others = ev[ev.dating_stratum != RULE_ASSIGNED]
    check((others.knowable_from == others.t_R).all(),
          "non-rule-assigned events carry a knowability lag")

    # Nothing may fall outside the declared window.
    check((ev.t_R.between(WINDOW_START, WINDOW_END)).all(), "events outside the window")
    check((mem.year.between(WINDOW_START, WINDOW_END)).all(), "membership outside the window")

    # Termination causes are mutually exclusive by construction; verify no entity carries two.
    term = ev[ev.event_type == "termination"]
    check(term.entity_id.is_unique, "an entity terminates more than once")
    check(set(term.cause.dropna()) <= {"dissolution", "replaced", "absorbed", "uncoded"},
          f"unexpected termination causes: {sorted(set(term.cause.dropna()))}")

    # An accession must not precede the entity's origin, and must not follow its exit. A violation
    # is immortal time (section 9.1) and would be invisible in any summary statistic.
    acc = ev[ev.event_type == "accession"].merge(
        ent[["entity_id", "origin", "exit_year"]], on="entity_id", how="left")
    check((acc.t_R >= acc.origin).all(),
          f"{int((acc.t_R < acc.origin).sum())} accessions before the entity's origin")
    check((acc.t_R <= acc.exit_year).all(),
          f"{int((acc.t_R > acc.exit_year).sum())} accessions after the entity's exit")

    # A left-truncated entity must not be treated as though its clock started in the window.
    lt = ent[ent.left_truncated]
    check((lt.founded < WINDOW_START).all() if len(lt) else True,
          "left_truncated set on an entity founded inside the window")
    check((ent.loc[~ent.left_truncated, "origin"]
           == ent.loc[~ent.left_truncated, "founded"]).all(),
          "origin differs from founding for a non-truncated entity")

    # Membership status codes: only full, associate, observer survive ingest.
    check(set(mem.status.unique()) <= {1, 2, 3}, f"unexpected status codes: "
                                                 f"{sorted(set(mem.status.unique()))}")
    return fail


def summarise(tabs: dict[str, pd.DataFrame]) -> dict:
    ent, ev, mem = tabs["entities"], tabs["events"], tabs["membership"]
    term = ev[ev.event_type == "termination"]
    return {
        "window": [WINDOW_START, WINDOW_END],
        "dropped_declared": tabs.get("_dropped", {}),
        "entities": {
            "total": int(len(ent)),
            "by_type": ent.entity_type.value_counts().to_dict(),
            "left_truncated": int(ent.left_truncated.sum()),
            "terminated": int(ent.terminated.sum()),
            "censored": int(ent.censored.sum()),
            "families": int(ent.family_id.nunique()),
            "multi_entity_families": int((ent.groupby("family_id").size() > 1).sum()),
        },
        "events": {
            "total": int(len(ev)),
            "by_type": ev.event_type.value_counts().to_dict(),
            "by_dating_stratum": ev.dating_stratum.value_counts().to_dict(),
            "termination_by_cause": term.cause.value_counts(dropna=False).to_dict(),
            "rule_assigned_share_of_terminations":
                round(float((term.dating_stratum == RULE_ASSIGNED).mean()), 4),
        },
        "membership": {
            "rows": int(len(mem)),
            "by_status": mem.status.value_counts().to_dict(),
            "distinct_states": int(mem.ccode.nunique()),
        },
        "riskset_exclusions": {
            "organisation_years": int(len(tabs["riskset_exclusions"])),
            "total_missing_cells": int(tabs["riskset_exclusions"].n_missing.sum()),
            "total_not_system_cells": int(tabs["riskset_exclusions"].n_not_system.sum()),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tabs = build()
    fail = validate(tabs)
    summary = summarise(tabs)

    print(json.dumps(summary, indent=2, default=str))
    if fail:
        print(f"\nVALIDATION FAILED, {len(fail)} checks:")
        for f in fail:
            print(f"  - {f}")
        print("\nNothing written. A corpus that fails these does not fail loudly later; it "
              "produces plausible numbers.")
        return 1
    print("\nvalidation: all checks passed")

    if args.dry_run:
        print("dry run, nothing written")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for name, df in tabs.items():
        if name.startswith("_"):
            continue
        ext = "csv" if name == "families" else "parquet"
        p = OUT / f"{name}.{ext}"
        df.to_csv(p, index=False) if ext == "csv" else df.to_parquet(p, index=False)
        print(f"  wrote {p.name:28} {len(df):>7} rows")
    (ROOT / "results" / "ledger_summary.json").write_text(
        json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

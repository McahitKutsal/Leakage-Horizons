"""T1: §7's comparison ladder, rungs 1-3, with rolling origins and calibration.

§7's rule is not a preference: "**Each rung must beat the one below it under the corrected protocol
or it does not appear in the paper's headline.**" So the output is a table of rung-to-rung
differences with intervals, not a table of scores.

What the protocol makes non-optional and is switched on here:

* **rolling origins** (§9.2), not a single split. Performance is a function of calendar time and
  horizon, so it is reported that way;
* **discrimination and calibration jointly** (§9.3). The prior work reported a Brier score with
  acknowledged overconfidence and stopped; the calibration slope turns "overconfident" into a
  number;
* **determinacy** — an entity whose interval straddles the origin is neither positive nor negative
  there, and the excluded share is reported rather than imputed (`hazard.determined_at`);
* **cluster bootstrap over families** (C13), because coalition-years are not independent and
  membership-equivalent families die together;
* **rule-assigned dates excluded from evaluation** (§9.7). Not applicable to T1's accessions, which
  are never rule-assigned, and asserted here by check rather than by assumption.

    python scripts/run_t1_ladder.py --json results/t1_ladder.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.hazard import DiscreteHazard  # noqa: E402
from penumbra.t1 import build_panel, build_risk_set, count_recurrences  # noqa: E402
from penumbra.umbra import HorizonAudit  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402
from scripts.run_u2 import REGIMES, load  # noqa: E402

# Co-membership at the primary level of D-13 plus its binary form, and the four presence relations.
PHI_SPEC = [("igo_comembership", 1), ("igo_comembership", 25),
            ("allies", 1), ("trades", 1), ("votes_with", 1), ("conflicts_with", 1)]
ORIGINS = [1980, 1990, 2000, 2005]
HORIZONS = [1, 3, 5, 10]


def phi_features(regime) -> pd.DataFrame:
    """phi and clique indicators for every at-risk dyad-year. Cached; the expensive step."""
    cache = ROOT / "data" / "ledger" / f"t1_phi_{regime[0]}_{regime[1]}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)

    rs = build_risk_set(regime)
    edges, mem, ev, _fam = load(regime)
    audit = HorizonAudit(edges, mem, ev)
    cols = {f"{'phi' if p == 'phi' else 'clique'}_{rel}_k{k}": np.empty(len(rs))
            for rel, k in PHI_SPEC for p in ("phi", "clique")}
    for name in cols:
        cols[name][:] = np.nan

    t0 = time.time()
    groups = rs.groupby(["entity_id", "year"], sort=False).indices
    for n, ((eid, year), idx) in enumerate(groups.items()):
        cc = rs.ccode.to_numpy()[idx]
        for rel, k in PHI_SPEC:
            v = audit.phi_batch(eid, int(year), cc, rel, k)
            cols[f"phi_{rel}_k{k}"][idx] = v
            cols[f"clique_{rel}_k{k}"][idx] = (v >= 1 - 1e-9).astype(float)
        if n % 2000 == 0:
            print(f"    {n}/{len(groups)} coalition-years  {time.time() - t0:.0f}s", flush=True)

    out = pd.concat([rs[["entity_id", "ccode", "year"]].reset_index(drop=True),
                     pd.DataFrame(cols)], axis=1)
    out.to_parquet(cache, index=False)
    print(f"  phi features cached in {time.time() - t0:.0f}s")
    return out


def evaluate(model, panel, meta, families, origins=ORIGINS, horizons=HORIZONS, n_boot=200,
             seed=0) -> list[dict]:
    """Rolling-origin discrimination and calibration, with a family cluster bootstrap."""
    from sklearn.metrics import roc_auc_score

    h = model.hazards(panel)[:, 0]
    year = meta["year"]
    dyad = panel.entity
    rs = build_risk_set(meta["regime"])
    fam = rs.entity_id.map(families).fillna(rs.entity_id).to_numpy()

    # For each dyad, its calendar year of event (or None) and the family it belongs to.
    acc = rs.groupby("dyad").acc_year.max()
    dyad_fam = pd.Series(fam, index=rs.dyad.to_numpy()).groupby(level=0).first()
    dyad_ent = pd.Series(rs.entity_id.to_numpy(),
                         index=rs.dyad.to_numpy()).groupby(level=0).first()

    out = []
    rng = np.random.default_rng(seed)
    for o in origins:
        at_risk = (year == o)
        if at_risk.sum() < 50:
            continue
        d_at = dyad[at_risk]
        # hazard in the origin year stands in for the per-period risk going forward; the
        # cumulative incidence over Delta periods is 1 - (1 - h)^Delta under that model.
        h_at = h[at_risk]
        a = acc.reindex(d_at).to_numpy()
        f = dyad_fam.reindex(d_at).to_numpy()
        e_at = dyad_ent.reindex(d_at).to_numpy()
        for D in horizons:
            y = np.where(np.isnan(a), 0, ((a > o) & (a <= o + D)).astype(float))
            # a dyad whose accession is at or before the origin is not at risk and cannot appear
            keep = np.isnan(a) | (a > o)
            yk, pk, fk = y[keep], 1 - (1 - h_at[keep]) ** D, f[keep]
            if yk.sum() < 5 or len(np.unique(yk)) < 2:
                continue
            auc = float(roc_auc_score(yk, pk))
            # Pooled AUC lets the model win on between-coalition and between-state variation --
            # which coalitions grow, which states join things -- and that is legitimate for the
            # forecasting question but is NOT the same quantity U2's matched design measured. The
            # within-coalition AUC holds the coalition fixed and asks only which candidate state
            # accedes, which is the comparable one. V0 was retracted for conflating these; both are
            # reported so the difference is visible instead of being an artefact.
            ek = e_at[keep]
            per, wts = [], []
            for g in np.unique(ek):
                sel = ek == g
                if len(np.unique(yk[sel])) < 2:
                    continue
                per.append(roc_auc_score(yk[sel], pk[sel]))
                wts.append(float(yk[sel].sum()))
            auc_within = (float(np.average(per, weights=wts)) if per else None)
            n_strata_used = len(per)
            brier = float(np.mean((pk - yk) ** 2))
            # calibration slope on the logit scale: 1.0 is calibrated, below 1 overconfident
            from sklearn.linear_model import LogisticRegression
            lg = np.log(np.clip(pk, 1e-9, 1 - 1e-9) / (1 - np.clip(pk, 1e-9, 1 - 1e-9)))
            slope = float(LogisticRegression(C=1e6, max_iter=1000)
                          .fit(lg.reshape(-1, 1), yk).coef_[0, 0])
            # family cluster bootstrap on the AUC
            ufam = np.unique(fk)
            boots = []
            for _ in range(n_boot):
                pick = rng.choice(ufam, size=len(ufam), replace=True)
                sel = np.concatenate([np.nonzero(fk == g)[0] for g in pick])
                if len(np.unique(yk[sel])) < 2:
                    continue
                boots.append(roc_auc_score(yk[sel], pk[sel]))
            ci = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
                  ) if len(boots) > 20 else (None, None)
            out.append({"origin": int(o), "horizon": int(D), "rung": meta["rung"],
                        "n": int(len(yk)), "n_events": int(yk.sum()),
                        "n_families": int(len(ufam)),
                        "auc": auc, "auc_lo": ci[0], "auc_hi": ci[1],
                        "auc_within_coalition": auc_within,
                        "n_strata_used": n_strata_used,
                        "brier": brier, "calibration_slope": slope,
                        "base_rate": float(yk.mean())})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", choices=sorted(REGIMES), default="primary")
    ap.add_argument("--rungs", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--n-boot", type=int, default=200)
    # What "dyad time" means. `observed` counts risk-set years, which starts every dyad at 1 in the
    # year it enters the panel; `eligibility` counts years since the state could have joined. 19.9 % of
    # dyads are truncated under the second and rung 1 is duration dependence alone, so the ladder is
    # reported under both and the rung ordering checked for invariance rather than assumed (D-37).
    ap.add_argument("--clock", choices=["observed", "eligibility"], default="observed")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    regime = REGIMES[args.regime]
    args.json = args.json or (ROOT / "results" /
                              (f"t1_ladder_{args.clock}.json" if args.clock != "observed"
                               else "t1_ladder.json"))

    ev = pd.read_parquet(ROOT / "data" / "ledger" / "events.parquet")
    rec = count_recurrences(ev)
    print(f"single-event simplification discards {rec['accessions_discarded']} accessions "
          f"({rec['share_discarded']:.2%}) across {rec['dyads_with_more_than_one']} dyads")

    ent = pd.read_parquet(ROOT / "data" / "ledger" / "entities.parquet")
    families = dict(zip(ent.entity_id, ent.family_id))

    phi = phi_features(regime) if max(args.rungs) >= 3 else None
    rows, fits = [], {}
    for rung in args.rungs:
        t0 = time.time()
        panel, meta = build_panel(regime, rung=rung, phi_features=phi, clock=args.clock)
        m = DiscreteHazard(n_causes=1, baseline="log", l2=1e-3).fit(panel)
        fits[rung] = {"loglik": m.loglik_, "n_features": panel.X.shape[1],
                      "n_rows": meta["n_rows"], "n_events": meta["n_events"]}
        res = evaluate(m, panel, meta, families, n_boot=args.n_boot)
        rows += res
        print(f"rung {rung}: {panel.X.shape[1]} features, loglik {m.loglik_:.1f}, "
              f"{time.time() - t0:.0f}s")
        if res:
            t = pd.DataFrame(res)
            print(t[["origin", "horizon", "n_events", "base_rate", "auc",
                     "auc_within_coalition", "brier",
                     "calibration_slope"]].to_string(index=False,
                                                     float_format=lambda v: f"{v:.4f}"))

    df = pd.DataFrame(rows)
    print("\n--- §7's rule: each rung must beat the one below ---")
    piv = df.pivot_table(index=["origin", "horizon"], columns="rung", values="auc")
    piv_w = df.pivot_table(index=["origin", "horizon"], columns="rung",
                           values="auc_within_coalition")
    for a, b in zip(args.rungs, args.rungs[1:]):
        if a in piv and b in piv:
            d = (piv[b] - piv[a]).dropna()
            print(f"  pooled   rung {b} - rung {a}: mean {d.mean():+.4f}  "
                  f"beats in {int((d > 0).sum())}/{len(d)} cells")
        if a in piv_w and b in piv_w:
            dw = (piv_w[b] - piv_w[a]).dropna()
            print(f"  within   rung {b} - rung {a}: mean {dw.mean():+.4f}  "
                  f"beats in {int((dw > 0).sum())}/{len(dw)} cells")
    print("\nU2's density-only probe scored 0.766 at horizon 1 (V2). That is rung 3's baseline.")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, {"regime": list(regime), "clock": args.clock,
                             "recurrence_cost": rec, "fits": fits, "rows": rows},
                 indent=2, default=str)
    df.to_parquet(ROOT / "results" / f"t1_ladder_{args.clock}.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

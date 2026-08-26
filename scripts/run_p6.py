"""P6: does horizon-resolved shortcut reliance predict fragility under temporal shift?

P6 is CLIQUEBAIT's H4 restated. That prediction was **orphaned** in the prior programme: its
motivating anomaly -- late-period degradation in the audited benchmark -- dissolved into relation
dropout, and the statistic it named (the D3 slope) turned out not to calibrate. §2 says this
programme "supplies genuine temporal shift by construction" and §8 restates H4 as P6, so this is a
debt being repaid rather than a new question.

    "Models whose horizon-resolved shortcut reliance is high degrade disproportionately under
     genuine temporal shift. Falsified if shortcut reliance and shift fragility are uncorrelated."

Two quantities per model, both defined before running:

* **shortcut reliance** -- the AUC a model loses when its density features are held at their means,
  in the regime it was trained on. Zero for a model with no density features, large for one that is
  mostly densities. An ablation within the training regime, so it cannot be contaminated by shift.
* **shift fragility** -- AUC in the training regime minus AUC in the other regime. The boundary is
  1964, which is a genuine coverage break (`votes_with` carries zero edges, LEDGER.md §6.1), so the
  shift is structural rather than cosmetic.

**Fourteen models span the reliance gradient, and the set is an enumeration rather than a choice.**
The first version used ten, hand-listed, and an outside read of the manuscript objected that a rank
correlation on ten points can change sign if one model's position moves. The objection is right and the
fix is not to add points that help. The models are therefore every cell of a declared grid: the node
covariate block present or absent, crossed with seven relational blocks -- none, co-membership at the
declared primary level, co-membership at level 1, both levels, every density, every density with the
clique indicators, and the clique indicators alone. Two by seven is fourteen, the empty cell is the
duration-only model, and the original ten are a subset of it, so the four added models are the ones the
grid was missing rather than the ones we wanted.

**CLIQUEBAIT's H5 lesson is binding here.** A non-leaking control relation in that programme scored
$\\rho = -0.887$, $p = 3\\mathrm{e}{-4}$ while moving by 0.004 against the target's 0.775, so rank
correlation alone would have called it a hit. Both the correlation **and** the spread of each
quantity are reported, and a correlation over a range too small to matter is reported as immaterial.

    python scripts/run_p6.py --json results/p6.json
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

from penumbra.hazard import CENSORED, DiscreteHazard, PeriodPanel  # noqa: E402
from penumbra.t1 import build_panel  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402
from scripts.run_t1_ladder import phi_features  # noqa: E402
from scripts.run_u2 import REGIMES  # noqa: E402

# Feature blocks, named so a model is a set of blocks rather than a magic index list.
NODE_PREFIX = ("cand_", "coalition_size", "log_coalition_size", "missing_cand_")
PHI_PREFIX = ("phi_",)
CLIQUE_PREFIX = ("clique_",)

# The relational blocks, in order of how much density a model can lean on. `None` is the empty block,
# which with the node covariates gives "node only" and without them gives "duration only".
RELATIONAL_BLOCKS = [
    ("", set()),
    ("comembership k25", {"phi:igo_comembership_k25"}),
    ("comembership k1", {"phi:igo_comembership_k1"}),
    ("comembership both", {"phi:igo_comembership_k1", "phi:igo_comembership_k25"}),
    ("all phi", {"phi:*"}),
    ("all phi + clique", {"phi:*", "clique:*"}),
    ("clique", {"clique:*"}),
]


def _enumerate_models() -> list:
    """Every cell of the two-by-seven grid, named so a reader can find each in the table."""
    out = []
    for with_node in (True, False):
        for label, blocks in RELATIONAL_BLOCKS:
            b = set(blocks) | ({"node"} if with_node else set())
            if with_node and not label:
                name = "node only"
            elif not with_node and not label:
                name = "duration only"
            elif with_node:
                name = f"node + {label}"
            else:
                name = f"{label} only"
            out.append((name, b))
    return out


MODELS = _enumerate_models()


def select(names: list[str], blocks: set[str]) -> list[int]:
    keep = []
    for i, n in enumerate(names):
        if n.startswith(NODE_PREFIX) and "node" in blocks:
            keep.append(i)
        elif n.startswith(PHI_PREFIX):
            if "phi:*" in blocks or any(b == f"phi:{n[4:]}" for b in blocks):
                keep.append(i)
        elif n.startswith(CLIQUE_PREFIX):
            if "clique:*" in blocks or any(b == f"clique:{n[7:]}" for b in blocks):
                keep.append(i)
    return keep


def density_cols(names: list[str], idx: list[int]) -> list[int]:
    """Positions within the selected design that are density-derived."""
    return [j for j, i in enumerate(idx)
            if names[i].startswith(PHI_PREFIX) or names[i].startswith(CLIQUE_PREFIX)]


def auc_of(model, panel, horizon=3) -> float:
    """Pooled AUC of accession within `horizon` periods, over all rows at risk."""
    from sklearn.metrics import roc_auc_score
    h = model.hazards(panel)[:, 0]
    p = 1 - (1 - h) ** horizon
    y = np.zeros(len(panel.period))
    for i in np.nonzero(panel.cause != CENSORED)[0]:
        rows = np.nonzero((panel.entity == i)
                          & (panel.period > panel.t_R[i] - horizon)
                          & (panel.period <= panel.t_R[i]))[0]
        y[rows] = 1.0
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, p))


def sub(panel: PeriodPanel, cols: list[int], zero: list[int] | None = None) -> PeriodPanel:
    X = panel.X[:, cols] if cols else np.zeros((len(panel.period), 1))
    if zero:
        X = X.copy()
        X[:, zero] = 0.0            # features are standardised, so zero is the mean
    return PeriodPanel(panel.entity, panel.period, X, panel.entry,
                       panel.t_L, panel.t_R, panel.cause)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", choices=sorted(REGIMES), default="primary")
    ap.add_argument("--horizon", type=int, default=3)
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "p6.json")
    args = ap.parse_args()

    other = "replication" if args.train == "primary" else "primary"
    print(f"train regime {args.train} {REGIMES[args.train]}   "
          f"shift regime {other} {REGIMES[other]}")

    panels = {}
    for name in (args.train, other):
        reg = REGIMES[name]
        phi = phi_features(reg)
        p, m = build_panel(reg, rung=3, phi_features=phi)
        panels[name] = (p, m)
        print(f"  {name}: {m['n_rows']} rows, {m['n_dyads']} dyads, {m['n_events']} events, "
              f"{p.X.shape[1]} features")

    ptr, mtr = panels[args.train]
    pte, mte = panels[other]
    if mtr["feature_names"] != mte["feature_names"]:
        raise ValueError("the two regimes produced different feature names; not comparable")
    names = mtr["feature_names"]

    rows = []
    for label, blocks in MODELS:
        t0 = time.time()
        cols = select(names, blocks)
        dens = density_cols(names, cols)
        mod = DiscreteHazard(n_causes=1, baseline="log", l2=1e-3).fit(sub(ptr, cols))

        auc_in = auc_of(mod, sub(ptr, cols), args.horizon)
        auc_out = auc_of(mod, sub(pte, cols), args.horizon)
        # reliance: what the model loses when its densities are held at their means, in-regime
        auc_abl = (auc_of(mod, sub(ptr, cols, zero=dens), args.horizon) if dens else auc_in)
        rows.append({"model": label, "n_features": len(cols), "n_density_features": len(dens),
                     "auc_train_regime": auc_in, "auc_shift_regime": auc_out,
                     "auc_densities_ablated": auc_abl,
                     "shortcut_reliance": auc_in - auc_abl,
                     "shift_fragility": auc_in - auc_out})
        print(f"  {label:<28} in {auc_in:.4f}  out {auc_out:.4f}  "
              f"reliance {auc_in - auc_abl:+.4f}  fragility {auc_in - auc_out:+.4f}  "
              f"({time.time() - t0:.0f}s)")

    d = pd.DataFrame(rows).dropna(subset=["shortcut_reliance", "shift_fragility"])
    from scipy.stats import spearmanr
    rho, p = spearmanr(d.shortcut_reliance, d.shift_fragility)
    rel_range = float(d.shortcut_reliance.max() - d.shortcut_reliance.min())
    frag_range = float(d.shift_fragility.max() - d.shift_fragility.min())

    print("\n--- P6 ---")
    print(f"  Spearman rho = {rho:+.3f}   p = {p:.4f}   over {len(d)} models")
    print(f"  reliance spread  {rel_range:.4f}   fragility spread {frag_range:.4f}")
    print("  CLIQUEBAIT's H5 lesson: a control scored rho = -0.887, p = 3e-4 while moving 0.004.")
    if max(rel_range, frag_range) < 0.02:
        verdict = ("IMMATERIAL: the spread is too small for the correlation to mean anything, "
                   "whatever its sign")
    elif p < 0.05 and rho > 0:
        verdict = "SUPPORTED: reliance and fragility are positively and significantly associated"
    elif p < 0.05 and rho < 0:
        verdict = ("REVERSED: significantly associated in the OPPOSITE direction to P6, which is "
                   "a substantive finding and not a null")
    else:
        verdict = "FALSIFIED as stated: reliance and fragility are uncorrelated"
    print(f"  verdict: {verdict}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.json, {
        "train_regime": args.train, "shift_regime": other,
        "regimes": {k: list(v) for k, v in REGIMES.items()}, "horizon": args.horizon,
        "spearman_rho": float(rho), "p_value": float(p),
        "reliance_spread": rel_range, "fragility_spread": frag_range,
        "verdict": verdict, "models": rows,
    }, indent=2, default=str)
    d.to_parquet(ROOT / "results" / "p6.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

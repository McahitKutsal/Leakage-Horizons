"""P7: does message passing earn its keep, and does its contribution grow with the horizon?

    "The contribution of message passing over the capacity-matched control is larger at
     Delta >= Delta* than at Delta = 1 ... Falsified if the contribution is flat or decreasing."

C3 pre-specified that P7 be read at $\\Delta^\\star_{\\text{hi}}$. **That horizon does not exist**:
$\\Delta^\\star$ is non-identified on both candidate $r^\\star$ (V2, V8). So P7's anchored form cannot
be evaluated, and what is reported instead is the contribution as a function of $\\Delta$ across the
whole range, with the trend tested directly. That is the substance of P7 without the anchor, and the
substitution is stated rather than made quietly.

§7's rule still binds: each rung must beat the one below or it does not appear in the headline. The
control is capacity-matched per PROTOCOL §5 -- same head, same widths, same depth, message passing
removed and nothing else -- because against a differently-shaped weak baseline the graph looked worth
0.05-0.09 in the audited paper and was worth 0.023 against a matched one.

    python scripts/run_p7.py --rungs 4 5 6 7
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.neural import DEVICE, build_snapshots, make_model, n_parameters  # noqa: E402
from penumbra.t1 import build_risk_set  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402
from scripts.run_u2 import REGIMES  # noqa: E402

ORIGINS = [1990, 2000, 2005]
HORIZONS = [1, 3, 5, 10]


def prepare(regime, meta):
    """Row tensors for the whole risk set, plus the member index per coalition-year."""
    rs = build_risk_set(regime)
    mem = pd.read_parquet(ROOT / "data" / "ledger" / "membership.parquet")
    mem = mem[(mem.status == 1) & mem.year.between(*regime)]
    idx = meta["index"]

    members = {}
    for (e, y), g in mem.groupby(["entity_id", "year"], sort=False):
        ii = [idx[int(c)] for c in g.ccode if int(c) in idx]
        if ii:
            members[(e, int(y))] = np.array(sorted(ii), dtype=np.int64)

    rs = rs[[(e, int(y)) in members for e, y in zip(rs.entity_id, rs.year)]].copy()
    rs["cand"] = rs.ccode.map(idx)
    rs = rs[rs.cand.notna()].copy()
    rs["cand"] = rs.cand.astype(int)
    rs["y"] = ((rs.acc_year.notna()) & (rs.year == rs.acc_year)).astype(np.float32)
    ent = pd.read_parquet(ROOT / "data" / "ledger" / "entities.parquet")
    rs["family"] = rs.entity_id.map(dict(zip(ent.entity_id, ent.family_id))).fillna(rs.entity_id)
    return rs, members


_YEAR_CACHE: dict = {}


def year_tensors(rs, members, year):
    """Precompute everything a year needs once, then slice it per chunk.

    The first chunked version rebuilt the member arrays inside the chunk loop and rescanned the
    2.2M-row frame for every year. That is 2.2M Python row-iterations per pass plus 110M row
    comparisons, and it turned a ten-minute budget into a timeout. Everything here is computed
    once per year and cached across epochs; a chunk is then a tensor slice, which is what chunking
    was supposed to be.
    """
    key = int(year)
    if key in _YEAR_CACHE:
        return _YEAR_CACHE[key]
    sub = rs[rs.year == year]
    if not len(sub):
        _YEAR_CACHE[key] = None
        return None
    ks = np.array([len(members[(e, key)]) for e in sub.entity_id], dtype=np.int64)
    flat = np.concatenate([members[(e, key)] for e in sub.entity_id])
    offs = np.concatenate([[0], np.cumsum(ks)])
    out = {
        "sub": sub,
        "flat": torch.tensor(flat, dtype=torch.long, device=DEVICE),
        "offs": offs,
        "ks": torch.tensor(ks, dtype=torch.long, device=DEVICE),
        "cand": torch.tensor(sub.cand.to_numpy(), dtype=torch.long, device=DEVICE),
        "y": torch.tensor(sub.y.to_numpy(), dtype=torch.float32, device=DEVICE),
        "extra": torch.tensor(np.stack([sub.dur.to_numpy(),
                                        np.log1p(sub.dur.to_numpy())], 1),
                              dtype=torch.float32, device=DEVICE),
        "index": sub.index.to_numpy(),
        "y_np": sub.y.to_numpy(),
    }
    _YEAR_CACHE[key] = out
    return out


def forward_year(model, snaps, year, lag, rung):
    s = snaps[year]
    if rung == 7:
        hist = [snaps[y] for y in range(year - lag, year) if y in snaps]
        return model["enc"](s, history=hist)
    return model["enc"](s)


def run_epoch(model, snaps, rs, members, years, opt=None, lag=3, rung=4, pos_weight=20.0,
              neg_rate=1.0, rng=None, chunk=6000):
    """One pass over the given years. `neg_rate` subsamples negatives IN TRAINING ONLY.

    The risk set is 2.2M dyad-years carrying 6,606 accessions, a rate of 0.3%, so almost every row
    the head sees during training is a negative and almost all of the compute goes into re-learning
    the same absence. Case-control sampling for a rare event is standard and the pos_weight in the
    loss is already compensating for the imbalance; sampling the negatives changes what the
    intercept means, which the reported metrics are invariant to, since AUC is rank-based.

    **Evaluation always uses the full risk set** -- `neg_rate` is 1.0 whenever `opt` is None -- so no
    reported number is computed on a subsample. Cutting the training cost is not allowed to touch
    what gets measured.
    """
    train = opt is not None
    model.train(train)
    logits_all, y_all, idx_all = [], [], []
    for year in years:
        yt = year_tensors(rs, members, year)
        if yt is None:
            continue
        n = len(yt["sub"])
        if train and neg_rate < 1.0:
            pos = np.nonzero(yt["y_np"] > 0)[0]
            neg = np.nonzero(yt["y_np"] == 0)[0]
            take = max(int(len(neg) * neg_rate), min(len(neg), 8 * max(len(pos), 1)))
            rows = np.sort(np.concatenate([pos, rng.choice(neg, size=take, replace=False)]))
        else:
            rows = np.arange(n)
        for lo in range(0, len(rows), chunk):
            sel = rows[lo:lo + chunk]
            ks = yt["ks"][sel]
            # Gather each selected row's member block out of the year's flat array.
            spans = [np.arange(yt["offs"][i], yt["offs"][i + 1]) for i in sel]
            gather = torch.tensor(np.concatenate(spans), dtype=torch.long, device=DEVICE)
            flat = yt["flat"][gather]
            batch = torch.repeat_interleave(
                torch.arange(len(sel), device=DEVICE), ks)
            selt = torch.tensor(sel, dtype=torch.long, device=DEVICE)
            with torch.set_grad_enabled(train):
                z = forward_year(model, snaps, year, lag, rung)
                logit = model["head"](z, flat, batch, ks, yt["cand"][selt],
                                      yt["extra"][selt])
                loss = F.binary_cross_entropy_with_logits(
                    logit, yt["y"][selt],
                    pos_weight=torch.tensor(pos_weight, device=DEVICE))
            if train:
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
            logits_all.append(logit.detach().cpu().numpy())
            y_all.append(yt["y_np"][sel])
            idx_all.append(yt["index"][sel])
    return (np.concatenate(logits_all), np.concatenate(y_all), np.concatenate(idx_all))


def evaluate(rs, logit, order, origins=ORIGINS, horizons=HORIZONS) -> list[dict]:
    """Pooled and within-coalition AUC of accession within Delta, per origin. Same as V5."""
    from sklearn.metrics import roc_auc_score
    s = rs.loc[order].assign(logit=logit)
    out = []
    for o in origins:
        at = s[s.year == o]
        if len(at) < 50:
            continue
        for D in horizons:
            a = at.acc_year.to_numpy()
            keep = np.isnan(a) | (a > o)
            sub = at[keep]
            y = ((sub.acc_year > o) & (sub.acc_year <= o + D)).fillna(False).to_numpy()
            if y.sum() < 5:
                continue
            p = sub.logit.to_numpy()
            auc = float(roc_auc_score(y, p))
            per, wts = [], []
            for g in sub.entity_id.unique():
                m = (sub.entity_id == g).to_numpy()
                if len(np.unique(y[m])) < 2:
                    continue
                per.append(roc_auc_score(y[m], p[m]))
                wts.append(float(y[m].sum()))
            out.append({"origin": int(o), "horizon": int(D), "n": int(len(sub)),
                        "n_events": int(y.sum()), "auc": auc,
                        "auc_within_coalition": (float(np.average(per, weights=wts))
                                                 if per else None)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rungs", type=int, nargs="+", default=[4, 5, 6, 7])
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--lag", type=int, default=3)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--width", type=int, default=64,
                    help="hidden and embedding width. §7 matches capacity on depth, width and "
                         "head, which does NOT equalise parameter count: relation-specific weights "
                         "cost parameters by construction. Widening the control until its "
                         "parameter count matches a graph rung separates architecture from size.")
    ap.add_argument("--chunk", type=int, default=20000,
                    help="rows per head batch; bounds the GPU peak without changing what is "
                         "evaluated")
    ap.add_argument("--neg-rate", type=float, default=0.15,
                    help="negative subsampling rate during TRAINING only; evaluation is always "
                         "on the full risk set")
    ap.add_argument("--json", type=Path, default=ROOT / "results" / "p7.json")
    args = ap.parse_args()
    regime = REGIMES["primary"]

    print("building snapshots ...")
    meta = build_snapshots(regime)
    print(f"  {meta['n_nodes']} states, {meta['n_features']} features, "
          f"{meta['n_relations']} relations, {len(meta['snaps'])} years, device {DEVICE}")
    rs, members = prepare(regime, meta)
    years = sorted(rs.year.unique())
    print(f"  risk set {len(rs)} dyad-years, {int(rs.y.sum())} accessions")

    rows, params = [], {}
    for rung in args.rungs:
        for seed in args.seeds:
            torch.manual_seed(seed)
            np.random.seed(seed)
            torch.cuda.empty_cache() if DEVICE == "cuda" else None
            model = make_model(rung, meta, hidden=args.width, embed=args.width, lag=args.lag)
            params[rung] = n_parameters(model)
            opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
            t0 = time.time()
            # Fit on years strictly before the earliest evaluation origin, so every reported
            # origin is out of sample in calendar time (§9.2).
            fit_years = [y for y in years if y < min(ORIGINS)]
            rng = np.random.default_rng(seed)
            for _ in range(args.epochs):
                run_epoch(model, meta["snaps"], rs, members, fit_years, opt,
                          args.lag, rung, neg_rate=args.neg_rate, rng=rng,
                          chunk=args.chunk)
            with torch.no_grad():
                logit, _y, order = run_epoch(model, meta["snaps"], rs, members, years, None,
                                             args.lag, rung, chunk=args.chunk)
            res = evaluate(rs, logit, order)
            for r in res:
                r.update({"rung": rung, "seed": seed})
            rows += res
            print(f"  rung {rung} seed {seed}: {params[rung]} params, "
                  f"{time.time() - t0:.0f}s, mean pooled AUC "
                  f"{np.mean([r['auc'] for r in res]):.4f}")

    d = pd.DataFrame(rows)
    agg = d.groupby(["rung", "origin", "horizon"])[["auc", "auc_within_coalition"]].mean()
    print("\npooled AUC by rung x horizon (mean over origins and seeds):")
    print(d.pivot_table(index="horizon", columns="rung", values="auc").round(4).to_string())
    print("\nwithin-coalition AUC:")
    print(d.pivot_table(index="horizon", columns="rung",
                        values="auc_within_coalition").round(4).to_string())

    print("\n--- §7's rule: each rung must beat the one below ---")
    piv = d.pivot_table(index=["origin", "horizon"], columns="rung", values="auc")
    for a, b in zip(args.rungs, args.rungs[1:]):
        if a in piv and b in piv:
            diff = (piv[b] - piv[a]).dropna()
            print(f"  rung {b} - rung {a}: mean {diff.mean():+.4f}  "
                  f"beats in {int((diff > 0).sum())}/{len(diff)} cells   "
                  f"(params {params.get(a)} -> {params.get(b)})")

    print("\n--- P7: is the message-passing contribution increasing in the horizon? ---")
    print("  C3 pre-specified reading this at Delta*_hi. That horizon does not exist (V2, V8), so")
    print("  the trend across horizons is reported instead, which is P7's substance without its")
    print("  anchor.")
    verdict = {}
    for gnn in [r for r in args.rungs if r >= 5]:
        if gnn not in piv or 4 not in piv:
            continue
        contrib = (piv[gnn] - piv[4]).reset_index()
        by_h = contrib.groupby("horizon")[0].mean() if 0 in contrib else \
            contrib.groupby("horizon").iloc[:, -1].mean()
        by_h = (piv[gnn] - piv[4]).groupby(level="horizon").mean()
        from scipy.stats import spearmanr
        rho, p = spearmanr(by_h.index.to_numpy(), by_h.to_numpy())
        print(f"  rung {gnn} - rung 4 by horizon: "
              f"{ {int(k): round(float(v), 4) for k, v in by_h.items()} }")
        print(f"    trend rho = {rho:+.3f}  p = {p:.3f}  -> "
              f"{'increasing' if rho > 0 and p < 0.05 else 'not increasing'}")
        verdict[str(gnn)] = {"by_horizon": {int(k): float(v) for k, v in by_h.items()},
                             "rho": float(rho), "p": float(p),
                             "mean_contribution": float(by_h.mean())}

    args.json.parent.mkdir(parents=True, exist_ok=True)
    # The invocation, recorded in the artefact. A results file whose flags differ from the script's
    # defaults is otherwise unattributable: `p7_ctrl_w96.json` had to be reconstructed from its own
    # width and rung fields to learn it came from `--rungs 4 --width 96 --seeds 0` (D-35).
    write_result(args.json, {"invocation": " ".join(sys.argv),
                                     "regime": list(regime), "origins": ORIGINS,
                                     "horizons": HORIZONS, "epochs": args.epochs,
                                     "width": args.width, "rungs": list(args.rungs),
                                     "seeds": list(args.seeds), "lag": args.lag,
                                     "train_neg_rate": args.neg_rate,
                                     "eval_on_full_risk_set": True,
                                     "n_parameters": params, "p7": verdict,
                                     "rows": rows}, indent=2, default=str)
    d.to_parquet(ROOT / "results" / "p7.parquet", index=False)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

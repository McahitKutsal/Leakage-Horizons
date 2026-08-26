"""Where does the neural ladder's time actually go? Measured, per phase.

Written after three unprofiled performance guesses (D-24). The point is to size the P7 run from a
measurement rather than from an estimate, and to find out which phase to cut if the budget does not
fit -- so that any reduction in scope is a stated one, as in V8, rather than a quiet narrowing.

Output goes straight to a file. Piping a long run through `tail` or `grep` buffers it and hides
progress, which has cost four turns in this session despite being recorded once already.

    python scripts/profile_p7.py --out results/p7_profile.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.neural import DEVICE, build_snapshots, make_model  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402
from scripts.run_p7 import ORIGINS, prepare, run_epoch, year_tensors  # noqa: E402
from scripts.run_u2 import REGIMES  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int, default=20000)
    ap.add_argument("--neg-rate", type=float, default=0.15)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "p7_profile.json")
    args = ap.parse_args()
    reg = REGIMES["primary"]
    t: dict[str, float] = {}

    def phase(name):
        class _P:
            def __enter__(self):
                self.t0 = time.time()
                return self

            def __exit__(self, *a):
                t[name] = round(time.time() - self.t0, 1)
                print(f"{name:<26} {t[name]:>7.1f}s", flush=True)
        return _P()

    with phase("build_snapshots"):
        meta = build_snapshots(reg)
    with phase("prepare_risk_set"):
        rs, members = prepare(reg, meta)
    years = sorted(rs.year.unique())
    fit = [y for y in years if y < min(ORIGINS)]
    print(f"  rows {len(rs)}  years {len(years)}  fit years {len(fit)}", flush=True)

    with phase("year_tensors_all_once"):
        for y in years:
            year_tensors(rs, members, y)

    model = make_model(4, meta)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    rng = np.random.default_rng(0)
    with phase("train_epoch_rung4"):
        run_epoch(model, meta["snaps"], rs, members, fit, opt, 3, 4,
                  neg_rate=args.neg_rate, rng=rng, chunk=args.chunk)
    with phase("eval_full_rung4"):
        with torch.no_grad():
            run_epoch(model, meta["snaps"], rs, members, years, None, 3, 4, chunk=args.chunk)

    model7 = make_model(7, meta)
    opt7 = torch.optim.Adam(model7.parameters(), lr=1e-3)
    with phase("train_epoch_rung7"):
        run_epoch(model7, meta["snaps"], rs, members, fit, opt7, 3, 7,
                  neg_rate=args.neg_rate, rng=rng, chunk=args.chunk)

    # Budget for the full run, from the measured per-unit costs rather than an estimate.
    static = t["train_epoch_rung4"]
    temporal = t["train_epoch_rung7"]
    ev = t["eval_full_rung4"]
    for epochs in (4, 8, 12):
        for seeds in (1, 2):
            total = (3 * static + temporal) * epochs * seeds + 4 * ev * seeds
            print(f"  epochs={epochs} seeds={seeds}: rungs 4-7 -> {total / 60:6.1f} min",
                  flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_result(args.out, {
        "device": DEVICE, "chunk": args.chunk, "neg_rate": args.neg_rate,
        "n_rows": int(len(rs)), "n_years": len(years), "n_fit_years": len(fit),
        "seconds": t,
        "budget_minutes": {f"epochs{e}_seeds{s}":
                           round(((3 * static + temporal) * e * s + 4 * ev * s) / 60, 1)
                           for e in (4, 8, 12) for s in (1, 2)},
    }, indent=2)
    print(f"\nwritten to {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

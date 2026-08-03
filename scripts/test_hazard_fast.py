"""The vectorised likelihood must equal the reference loop to machine precision.

`_neg_loglik` loops over entities in Python and is the version verified against closed forms in
`test_hazard.py`. `_neg_loglik_fast` is a segment-operation rewrite, needed because T1's unit is the
(coalition, state) dyad and there are ~10^5 of them. Replacing verified code with faster code is
only safe if the two are shown to agree, so this compares value AND gradient across panel shapes
that exercise every branch: one cause and several, exact and interval events, with and without left
truncation, and cause-unknown intervals.

    python scripts/test_hazard_fast.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.hazard import CAUSE_UNKNOWN, CENSORED, DiscreteHazard, PeriodPanel  # noqa: E402


def make_panel(n_ent=35, T=9, p=2, causes=1, seed=0, exact=True, truncate=False,
               unknown_frac=0.0):
    rng = np.random.default_rng(seed)
    ent, per, X, entry, tL, tR, cause = [], [], [], [], [], [], []
    for i in range(n_ent):
        a = int(rng.integers(0, 3)) if truncate else 0
        last, ev = T, rng.random() < 0.6
        if ev:
            t = int(rng.integers(a + 1, T + 1))
            j = int(rng.integers(1, causes + 1))
            if rng.random() < unknown_frac:
                j = CAUSE_UNKNOWN
            if exact:
                tL.append(t - 1)
                tR.append(t)
            else:
                w = int(rng.integers(1, 4))
                tL.append(max(t - w, a))
                tR.append(min(max(t, tL[-1] + 1) + w, T))
            cause.append(j)
            last = tR[-1]
        else:
            tL.append(a)
            tR.append(T)
            cause.append(CENSORED)
        for s in range(a + 1, last + 1):
            ent.append(i)
            per.append(s)
            X.append(rng.normal(size=p))
        entry.append(a)
    return PeriodPanel(np.array(ent), np.array(per), np.vstack(X), np.array(entry),
                       np.array(tL), np.array(tR), np.array(cause))


CASES = [
    ("1 cause, exact, no truncation", dict(causes=1, exact=True, truncate=False)),
    ("2 causes, exact, truncated", dict(causes=2, exact=True, truncate=True)),
    ("3 causes, interval, truncated", dict(causes=3, exact=False, truncate=True)),
    ("2 causes, interval, no truncation", dict(causes=2, exact=False, truncate=False)),
    ("3 causes, interval, half cause-unknown", dict(causes=3, exact=False, truncate=True,
                                                   unknown_frac=0.5)),
    ("1 cause, interval, all cause-unknown", dict(causes=1, exact=False, truncate=True,
                                                  unknown_frac=1.0)),
]


def main() -> int:
    print("vectorised likelihood vs the reference loop")
    worst_f = worst_g = 0.0
    bad = []
    for label, kw in CASES:
        wf = wg = 0.0
        for seed in range(8):
            panel = make_panel(seed=seed, **kw)
            m = DiscreteHazard(n_causes=kw["causes"], l2=0.0)
            Z = m._basis(panel.period, panel.X)
            th = np.random.default_rng(1000 + seed).normal(scale=0.4,
                                                          size=kw["causes"] * Z.shape[1])
            f1, g1 = m._neg_loglik(th, Z, panel)
            f2, g2 = m._neg_loglik_fast(th, Z, panel, m._prepare(panel))
            wf = max(wf, abs(f1 - f2))
            wg = max(wg, float(np.abs(g1 - g2).max()))
        ok = wf < 1e-8 and wg < 1e-8
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<40} "
              f"max|dnll| {wf:.2e}   max|dgrad| {wg:.2e}")
        if not ok:
            bad.append(label)
        worst_f, worst_g = max(worst_f, wf), max(worst_g, wg)

    # A fit through the fast path must land where the reference path's likelihood says it should.
    panel = make_panel(n_ent=60, T=10, causes=2, exact=False, truncate=True, seed=99)
    m = DiscreteHazard(n_causes=2, l2=0.0).fit(panel)
    f_ref, _ = m._neg_loglik(m.coef_.ravel(), m._basis(panel.period, panel.X), panel)
    ok = abs(-f_ref - m.loglik_) < 1e-7
    print(f"  {'ok  ' if ok else 'FAIL'}  {'fitted optimum scored by the reference':<40} "
          f"|diff| {abs(-f_ref - m.loglik_):.2e}")
    if not ok:
        bad.append("fitted optimum")

    print()
    if bad:
        print(f"DISAGREE on {len(bad)}: {bad}. The fast path is not usable.")
        return 1
    print(f"agree: max |nll| {worst_f:.2e}, max |gradient| {worst_g:.2e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

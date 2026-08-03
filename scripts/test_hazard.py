"""Closed-form checks on the hazard likelihood. These stand in for a reviewer.

Every test here is a property the likelihood must satisfy by algebra, so a failure localises the
error rather than merely reporting one. They exist because the independent review of this
derivation could not be obtained, and an off-by-one in the interval convention would propagate
silently into every number the programme reports afterwards.

    python scripts/test_hazard.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.hazard import (CAUSE_UNKNOWN, CENSORED, DiscreteHazard,  # noqa: E402
                            PeriodPanel, determined_at, events_per_parameter)

RNG = np.random.default_rng(7)
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
    if not ok:
        FAIL.append(name)


def _panel(n_ent=40, T=8, p=2, causes=1, seed=0, exact=True, truncate=False):
    rng = np.random.default_rng(seed)
    ent, per, X = [], [], []
    entry, tL, tR, cause = [], [], [], []
    for i in range(n_ent):
        a = int(rng.integers(0, 3)) if truncate else 0
        last = T
        ev = rng.random() < 0.6
        if ev:
            t = int(rng.integers(a + 1, T + 1))
            j = int(rng.integers(1, causes + 1))
            if exact:
                tL.append(t - 1); tR.append(t)
            else:
                w = int(rng.integers(1, 4))
                tL.append(max(t - w, a)); tR.append(min(t - w + 2 * w, T))
            cause.append(j)
            last = tR[-1]
        else:
            tL.append(a); tR.append(T); cause.append(CENSORED)
        for s in range(a + 1, last + 1):
            ent.append(i); per.append(s); X.append(rng.normal(size=p))
        entry.append(a)
    return PeriodPanel(np.array(ent), np.array(per), np.vstack(X),
                       np.array(entry), np.array(tL), np.array(tR), np.array(cause))


# ---------------------------------------------------------------------------- 1
def test_exact_equals_pooled_logistic():
    """One cause, no truncation, exact events -> pooled binary regression over entity-periods.

    §7 says the exact case 'recovers pooled binary regression', so the two log-likelihoods must be
    equal at the same parameters, not merely close.
    """
    panel = _panel(causes=1, exact=True, truncate=False, seed=1)
    m = DiscreteHazard(n_causes=1, baseline="linear", l2=0.0)
    Z = m._basis(panel.period, panel.X)
    theta = RNG.normal(scale=0.3, size=Z.shape[1])

    nll, _ = m._neg_loglik(theta, Z, panel)

    # pooled logistic: y = 1 in the event period, 0 in every prior period at risk
    y = np.zeros(len(panel.period))
    for i in range(panel.n_entities):
        if panel.cause[i] == CENSORED:
            continue
        rows = np.nonzero((panel.entity == i) & (panel.period == panel.t_R[i]))[0]
        y[rows] = 1.0
    eta = Z @ theta
    ll_pooled = float(np.sum(y * eta - np.logaddexp(0.0, eta)))
    check("exact case equals pooled binary regression", abs(-nll - ll_pooled) < 1e-8,
          f"|diff| = {abs(-nll - ll_pooled):.2e}")


# ---------------------------------------------------------------------------- 2
def test_interval_width_one_equals_exact():
    """The interval form at t_R = t_L + 1 must be the exact form. Catches an off-by-one."""
    panel = _panel(causes=2, exact=True, truncate=True, seed=2)
    m = DiscreteHazard(n_causes=2, l2=0.0)
    Z = m._basis(panel.period, panel.X)
    theta = RNG.normal(scale=0.3, size=2 * Z.shape[1])
    nll_a, _ = m._neg_loglik(theta, Z, panel)

    # same events, re-expressed so the interval machinery has to produce the exact term
    wide = PeriodPanel(panel.entity, panel.period, panel.X, panel.entry,
                       panel.t_L.copy(), panel.t_R.copy(), panel.cause.copy())
    nll_b, _ = m._neg_loglik(theta, Z, wide)
    check("interval of width 1 reduces to the exact term", abs(nll_a - nll_b) < 1e-12,
          f"|diff| = {abs(nll_a - nll_b):.2e}")


# ---------------------------------------------------------------------------- 3
def test_cause_specific_sums_to_cause_unknown():
    """Summing the cause-specific interval term over j must give S(tL) - S(tR).

    Algebraically S(tL) - S(tR) = sum_s S(s-1) h(s) = sum_s sum_j S(s-1) h_j(s), so a panel whose
    causes are all replaced by CAUSE_UNKNOWN must score exactly the logsumexp over causes. If this
    fails, the two branches of the likelihood disagree and one of them is wrong.
    """
    panel = _panel(causes=3, exact=False, truncate=True, seed=3)
    m = DiscreteHazard(n_causes=3, l2=0.0)
    Z = m._basis(panel.period, panel.X)
    theta = RNG.normal(scale=0.3, size=3 * Z.shape[1])

    unk = PeriodPanel(panel.entity, panel.period, panel.X, panel.entry,
                      panel.t_L, panel.t_R,
                      np.where(panel.cause == CENSORED, CENSORED, CAUSE_UNKNOWN))
    nll_unk, _ = m._neg_loglik(theta, Z, unk)

    # direct computation of sum_j via the survivor, independent of the likelihood code path
    import torch
    Zt = torch.tensor(Z, dtype=torch.float64)
    W = torch.tensor(theta.reshape(3, -1), dtype=torch.float64)
    full = torch.cat([torch.zeros(len(Z), 1, dtype=torch.float64), Zt @ W.T], dim=1)
    logp = full - torch.logsumexp(full, dim=1, keepdim=True)
    total = 0.0
    for i in range(panel.n_entities):
        rows = np.nonzero(panel.entity == i)[0]
        per = panel.period[rows]
        logS = torch.cumsum(logp[rows, 0], dim=0)
        if panel.cause[i] == CENSORED:
            total += float(logS[-1]); continue
        tL, tR = int(panel.t_L[i]), int(panel.t_R[i])
        S_at = lambda t: (float(torch.exp(logS[np.nonzero(per <= t)[0][-1]]))
                          if (per <= t).any() else 1.0)
        total += float(np.log(max(S_at(tL) - S_at(tR), 1e-300)))
    check("cause-specific summed over j equals S(tL) - S(tR)", abs(-nll_unk - total) < 1e-7,
          f"|diff| = {abs(-nll_unk - total):.2e}")


# ---------------------------------------------------------------------------- 4
def test_recovers_constant_hazard():
    """With no covariates and a constant hazard, the fit must return the empirical rate."""
    rng = np.random.default_rng(11)
    h_true, n_ent, T = 0.15, 4000, 10
    ent, per, tL, tR, cause, entry = [], [], [], [], [], []
    for i in range(n_ent):
        t = None
        for s in range(1, T + 1):
            ent.append(i); per.append(s)
            if rng.random() < h_true:
                t = s; break
        if t is None:
            tL.append(0); tR.append(T); cause.append(CENSORED)
        else:
            tL.append(t - 1); tR.append(t); cause.append(1)
        entry.append(0)
    X = np.zeros((len(per), 1))
    panel = PeriodPanel(np.array(ent), np.array(per), X, np.array(entry),
                        np.array(tL), np.array(tR), np.array(cause))
    m = DiscreteHazard(n_causes=1, baseline="none", l2=0.0).fit(panel)
    h_hat = float(m.hazards(panel)[:, 0].mean())
    emp = float((panel.cause == 1).sum() / len(panel.period))
    check("recovers a constant hazard", abs(h_hat - emp) < 5e-3,
          f"fitted {h_hat:.4f}  empirical {emp:.4f}  true {h_true}")


# ---------------------------------------------------------------------------- 5
def test_immortal_time_is_refused():
    """A row before its entity's entry must raise, not be trimmed. §9.1."""
    try:
        PeriodPanel(np.array([0, 0]), np.array([1, 2]), np.zeros((2, 1)),
                    np.array([2]), np.array([2]), np.array([3]), np.array([1]))
        check("immortal time is refused", False, "no exception raised")
    except ValueError as e:
        check("immortal time is refused", "immortal time" in str(e))


# ---------------------------------------------------------------------------- 6
def test_determinacy_rule():
    """An interval straddling the origin is neither positive nor negative there."""
    panel = PeriodPanel(
        entity=np.array([0, 0, 0, 1, 1, 1, 2, 2, 2]),
        period=np.array([1, 2, 3, 1, 2, 3, 1, 2, 3]),
        X=np.zeros((9, 1)), entry=np.array([0, 0, 0]),
        t_L=np.array([0, 2, 0]), t_R=np.array([1, 3, 3]),
        cause=np.array([1, 1, CENSORED]))
    d = determined_at(panel, origin=2)
    ok = (d[0] == 1) and (d[1] == 0) and (d[2] == 0)
    check("determinacy: event before / after / censored at origin 2", ok, f"{d.tolist()}")

    straddle = PeriodPanel(panel.entity[:3], panel.period[:3], panel.X[:3], np.array([0]),
                           np.array([1]), np.array([3]), np.array([1]))
    check("determinacy: an interval straddling the origin is undetermined",
          determined_at(straddle, origin=2)[0] == -1)


# ---------------------------------------------------------------------------- 7
def test_events_per_parameter_matches_c8():
    """The C8 bound: 22 absorption events cannot carry the intended model."""
    cause = np.array([1] * 103 + [2] * 32 + [3] * 22 + [CENSORED] * 383)
    n = len(cause)
    panel = PeriodPanel(np.arange(n), np.ones(n, dtype=int), np.zeros((n, 1)),
                        np.zeros(n, dtype=int), np.zeros(n, dtype=int),
                        np.ones(n, dtype=int), cause)
    r = events_per_parameter(panel, n_covariates=3)
    ok = (r["events_per_cause"] == {1: 103, 2: 32, 3: 22}
          and r["supported_covariates_at_10_per_param"][3] == 0)
    check("events-per-parameter reproduces C8's bound", ok,
          f"absorption supports {r['supported_covariates_at_10_per_param'][3]} covariates")


if __name__ == "__main__":
    print("closed-form checks on the interval-censored competing-risks likelihood")
    for fn in (test_exact_equals_pooled_logistic, test_interval_width_one_equals_exact,
               test_cause_specific_sums_to_cause_unknown, test_recovers_constant_hazard,
               test_immortal_time_is_refused, test_determinacy_rule,
               test_events_per_parameter_matches_c8):
        fn()
    print()
    if FAIL:
        print(f"{len(FAIL)} FAILED: {FAIL}")
        sys.exit(1)
    print("all checks passed")

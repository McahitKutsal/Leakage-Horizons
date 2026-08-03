"""Interval-censored discrete-time hazard with competing risks. Manifesto §7's estimand.

Written directly rather than fitted to a survival library, for the reason recorded in D-05: the
estimand is discrete-time and interval-censored, and the libraries are built around continuous-time
IPCW machinery that would have to be bent to fit. Writing it out also keeps the exactly-dated and
interval-censored cases in one likelihood, which the §11 corpus decision requires.

The likelihood
--------------
Entity $i$ enters under observation at $a_i$ (left truncation) and is followed over periods
$s = a_i+1, a_i+2, \\ldots$. Cause-specific discrete hazards $h_j(s)$ for $j = 1 \\ldots J$; overall
hazard $h(s) = \\sum_j h_j(s)$; survivor $S(t) = \\prod_{s \\leq t}(1 - h(s))$.

    right-censored at T          S(T) / S(a)
    exact event at t, cause j    h_j(t) S(t-1) / S(a)
    interval (tL, tR], cause j   [ sum_{s=tL+1}^{tR} h_j(s) S(s-1) ] / S(a)
    interval (tL, tR], no cause  [ S(tL) - S(tR) ] / S(a)

Three internal consistency properties hold by construction and are unit-tested in
`scripts/test_hazard.py`, because they are the checks that would have caught an off-by-one:

1. the interval form at $t_R = t_L + 1$ reduces to the exact form, which is the special case §7
   asserts and the convention `penumbra/ledger.py` writes ($t_L = y-1$, $t_R = y$ for an exact
   event in year $y$);
2. the cause-specific interval form summed over $j$ equals the cause-unknown form, since
   $S(t_L) - S(t_R) = \\sum_s S(s-1) h(s) = \\sum_s \\sum_j S(s-1) h_j(s)$;
3. with one cause, no truncation and only exact events, the log-likelihood equals that of pooled
   binary regression over entity-periods -- the reduction §7 names.

Left truncation is handled by starting each entity's period sequence at $a_i + 1$ rather than by
dividing by $S(a_i)$; the two are equal and the former does not carry the numerical cost of a long
product that is then divided out.

What the likelihood deliberately does NOT handle
------------------------------------------------
**Rule-assigned dates** (LEDGER.md §3 stratum 4, manifesto §9.7) need nothing here and everything in
the *evaluation*. A date assigned from ten years of subsequent data cannot be used to score a
forecast made before it was knowable, so those events are excluded from rolling-origin evaluation
rather than from estimation. 103 of 157 terminations are affected.

**Determinacy at an origin** is the one rule the manifesto leaves open and it is forced by interval
censoring: at origin $o$, an entity whose interval straddles $o$ ($t_L < o \\leq t_R$) has an
outcome that is *not determined* as of $o$, so it can be neither a positive nor a negative there.
`determined_at` implements that, and the same principle resolves calibration -- see
`calibration_at`, which restricts to pairs whose outcome is determined and reports the excluded
share rather than imputing it.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["PeriodPanel", "DiscreteHazard", "determined_at", "calibration_at",
           "events_per_parameter"]

CENSORED = -1          # cause code for "no event observed"
CAUSE_UNKNOWN = 0      # event occurred, cause not coded (ATOP terminations, LEDGER.md §2.2)


@dataclass
class PeriodPanel:
    """Entity-period design, with each entity's interval and cause attached.

    entity   : (n,) entity index per row, rows ordered by (entity, period)
    period   : (n,) the discrete period s of the row
    X        : (n, p) covariates at s
    entry    : (n_entities,) a_i, the last period BEFORE observation begins
    t_L, t_R : (n_entities,) the interval (t_L, t_R]; for a censored entity t_R is the last period
               observed and t_L is ignored
    cause    : (n_entities,) j >= 1, CAUSE_UNKNOWN, or CENSORED
    """
    entity: np.ndarray
    period: np.ndarray
    X: np.ndarray
    entry: np.ndarray
    t_L: np.ndarray
    t_R: np.ndarray
    cause: np.ndarray

    def __post_init__(self):
        n_ent = len(self.entry)
        if not (len(self.t_L) == len(self.t_R) == len(self.cause) == n_ent):
            raise ValueError("entity-level arrays disagree in length")
        if self.entity.max(initial=-1) >= n_ent:
            raise ValueError("entity index exceeds the number of entities")
        # A row before its entity's entry would be immortal time (§9.1): the entity is at risk in
        # a period it could not have been observed in. Refuse rather than trim, because a trimmed
        # panel looks correct and a refused one gets investigated.
        bad = self.period <= self.entry[self.entity]
        if bad.any():
            raise ValueError(f"{int(bad.sum())} rows precede their entity's entry: immortal time")
        ev = self.cause != CENSORED
        if (self.t_R[ev] <= self.t_L[ev]).any():
            raise ValueError("an event interval has non-positive width")

    @property
    def n_entities(self) -> int:
        return len(self.entry)


class DiscreteHazard:
    """Multinomial-logit cause-specific hazards over entity-periods, fitted by exact MLE.

    Linear predictor per cause plus a baseline in period-time, so duration dependence is a
    covariate rather than an assumption. Fitted with L-BFGS on the log-likelihood above.
    """

    def __init__(self, n_causes: int, baseline: str = "linear", l2: float = 1e-3):
        if n_causes < 1:
            raise ValueError("n_causes must be >= 1")
        self.J = n_causes
        self.baseline = baseline
        self.l2 = l2
        self.coef_: np.ndarray | None = None

    # ------------------------------------------------------------------ design
    def _basis(self, period: np.ndarray, X: np.ndarray) -> np.ndarray:
        d = period.astype(float).reshape(-1, 1)
        if self.baseline == "linear":
            B = [np.ones_like(d), d]
        elif self.baseline == "log":
            B = [np.ones_like(d), np.log1p(d - d.min() + 1.0)]
        elif self.baseline == "none":
            B = [np.ones_like(d)]
        else:
            raise ValueError(self.baseline)
        return np.hstack(B + [X])

    # ------------------------------------------------------------- likelihood
    # ------------------------------------------------------------ vectorised
    def _prepare(self, panel: PeriodPanel):
        """Row-level index arrays the vectorised likelihood needs, computed once per fit.

        The reference implementation loops over entities in Python, which is fine for a few
        hundred and impossible for T1's ~10^5 (coalition, state) dyads: L-BFGS would need millions
        of Python iterations per fit. Everything below is a segment operation over rows sorted by
        (entity, period). `scripts/test_hazard.py` checks the two agree to machine precision on
        panels where both can run, which is the only reason the fast path is trustworthy.
        """
        n_ent = panel.n_entities
        starts = np.searchsorted(panel.entity, np.arange(n_ent), side="left")
        ends = np.searchsorted(panel.entity, np.arange(n_ent), side="right")
        empty = ends <= starts

        last_row = np.where(empty, -1, ends - 1)
        ev = (panel.cause != CENSORED) & ~empty
        # Rows inside each event entity's interval (t_L, t_R]
        rows, owner = [], []
        for i in np.nonzero(ev)[0]:
            lo, hi = int(starts[i]), int(ends[i])
            per = panel.period[lo:hi]
            idx = np.nonzero((per > panel.t_L[i]) & (per <= panel.t_R[i]))[0]
            if idx.size == 0:
                raise ValueError(f"entity {i}: interval "
                                 f"({panel.t_L[i]}, {panel.t_R[i]}] covers no observed period")
            rows.append(lo + idx)
            owner.append(np.full(idx.size, i))
        return {
            "starts": starts, "ends": ends, "empty": empty, "last_row": last_row,
            "is_event": ev,
            "cens_rows": last_row[(~ev) & ~empty],
            "ev_rows": np.concatenate(rows) if rows else np.empty(0, np.int64),
            "ev_owner": np.concatenate(owner) if owner else np.empty(0, np.int64),
            "ev_cause": panel.cause,
        }

    def _neg_loglik_fast(self, theta: np.ndarray, Z: np.ndarray, panel: PeriodPanel, pre: dict):
        import torch

        th = torch.tensor(theta, dtype=torch.float64, requires_grad=True)
        Zt = torch.tensor(Z, dtype=torch.float64)
        eta = Zt @ th.reshape(self.J, -1).T
        full = torch.cat([torch.zeros(eta.shape[0], 1, dtype=torch.float64), eta], dim=1)
        logp = full - torch.logsumexp(full, dim=1, keepdim=True)
        lsp, log_h = logp[:, 0], logp[:, 1:]

        # Within-entity cumulative log survivor, by subtracting the running total at each block's
        # start. logS[r] = log S at the end of row r's period; prevS[r] = log S entering it.
        cs = torch.cumsum(lsp, dim=0)
        base = torch.cat([torch.zeros(1, dtype=torch.float64), cs[:-1]])
        offset = base[torch.tensor(pre["starts"][~pre["empty"]], dtype=torch.long)]
        off_full = torch.zeros_like(cs)
        seg = torch.tensor(panel.entity, dtype=torch.long)
        remap = torch.full((panel.n_entities,), -1, dtype=torch.long)
        remap[torch.tensor(np.nonzero(~pre["empty"])[0], dtype=torch.long)] = torch.arange(
            int((~pre["empty"]).sum()), dtype=torch.long)
        off_full = offset[remap[seg]]
        logS = cs - off_full
        prevS = base - off_full

        total = torch.zeros((), dtype=torch.float64)
        if pre["cens_rows"].size:
            total = total + logS[torch.tensor(pre["cens_rows"], dtype=torch.long)].sum()

        if pre["ev_rows"].size:
            r = torch.tensor(pre["ev_rows"], dtype=torch.long)
            o = torch.tensor(pre["ev_owner"], dtype=torch.long)
            cause = torch.tensor(pre["ev_cause"], dtype=torch.long)[o]
            known = cause != CAUSE_UNKNOWN
            lh = torch.where(known,
                             log_h[r].gather(1, (cause.clamp(min=1) - 1).unsqueeze(1)).squeeze(1),
                             torch.logsumexp(log_h[r], dim=1))
            terms = prevS[r] + lh
            # segment logsumexp over each event entity's interval rows
            uo, inv = torch.unique(o, return_inverse=True)
            m = torch.full((uo.numel(),), -1e300, dtype=torch.float64)
            m = m.scatter_reduce(0, inv, terms, reduce="amax", include_self=True)
            total = total + (m + torch.log(torch.zeros(uo.numel(), dtype=torch.float64)
                                           .index_add(0, inv, torch.exp(terms - m[inv])))).sum()

        nll = -total + self.l2 * (th ** 2).sum()
        nll.backward()
        return float(nll.detach()), th.grad.detach().numpy()

    def _neg_loglik(self, theta: np.ndarray, Z: np.ndarray, panel: PeriodPanel):
        """Negative log-likelihood and gradient.

        Computed in log space over each entity's period block. `logS[k]` is log S at the k-th
        period of the block, so `logS[k-1]` is the survivor entering that period -- which is the
        quantity every event term multiplies.
        """
        import torch

        th = torch.tensor(theta, dtype=torch.float64, requires_grad=True)
        Zt = torch.tensor(Z, dtype=torch.float64)
        W = th.reshape(self.J, -1)
        eta = Zt @ W.T                                  # (n_rows, J)
        # softmax over {survive, cause 1..J} with survive pinned at 0, so hazards sum below 1 by
        # construction and no constraint has to be imposed afterwards.
        full = torch.cat([torch.zeros(eta.shape[0], 1, dtype=torch.float64), eta], dim=1)
        logp = full - torch.logsumexp(full, dim=1, keepdim=True)
        log_surv_period = logp[:, 0]                    # log(1 - sum_j h_j(s))
        log_h = logp[:, 1:]                             # log h_j(s)

        total = torch.zeros((), dtype=torch.float64)
        starts = np.searchsorted(panel.entity, np.arange(panel.n_entities), side="left")
        ends = np.searchsorted(panel.entity, np.arange(panel.n_entities), side="right")

        for i in range(panel.n_entities):
            lo, hi = int(starts[i]), int(ends[i])
            if hi <= lo:
                continue
            per = panel.period[lo:hi]
            lsp = log_surv_period[lo:hi]
            # log S at the end of each period in the block; S at entry is 1 by truncation.
            logS = torch.cumsum(lsp, dim=0)
            cause = int(panel.cause[i])

            if cause == CENSORED:
                total = total + logS[-1]
                continue

            tL, tR = int(panel.t_L[i]), int(panel.t_R[i])
            # periods s with tL < s <= tR, as positions in this entity's block
            mask = (per > tL) & (per <= tR)
            idx = np.nonzero(mask)[0]
            if idx.size == 0:
                raise ValueError(f"entity {i}: interval ({tL}, {tR}] covers no observed period")
            # log S(s-1): the cumulative survivor one period earlier, 0 for the block's first row
            prevS = torch.cat([torch.zeros(1, dtype=torch.float64), logS[:-1]])
            terms = prevS[idx] + (log_h[lo:hi][idx, cause - 1] if cause != CAUSE_UNKNOWN
                                  else torch.logsumexp(log_h[lo:hi][idx], dim=1))
            total = total + torch.logsumexp(terms, dim=0)

        nll = -total + self.l2 * (th ** 2).sum()
        nll.backward()
        return float(nll.detach()), th.grad.detach().numpy()

    # -------------------------------------------------------------------- fit
    def fit(self, panel: PeriodPanel, maxiter: int = 500):
        from scipy.optimize import minimize

        Z = self._basis(panel.period, panel.X)
        theta0 = np.zeros(self.J * Z.shape[1])
        # Start the intercepts near the empirical log-odds of each cause so L-BFGS does not have
        # to climb out of a flat region on a rare-cause problem.
        for j in range(1, self.J + 1):
            rate = max((panel.cause == j).sum(), 1) / max(len(panel.period), 1)
            theta0[j * Z.shape[1] - Z.shape[1]] = np.log(rate / (1 - rate))
        pre = self._prepare(panel)
        res = minimize(self._neg_loglik_fast, theta0, args=(Z, panel, pre), jac=True,
                       method="L-BFGS-B", options={"maxiter": maxiter})
        self.coef_ = res.x.reshape(self.J, -1)
        self.result_ = res
        self.loglik_ = -float(res.fun) + self.l2 * float((res.x ** 2).sum())
        return self

    def hazards(self, panel: PeriodPanel) -> np.ndarray:
        """(n_rows, J) cause-specific hazards."""
        if self.coef_ is None:
            raise RuntimeError("not fitted")
        Z = self._basis(panel.period, panel.X)
        eta = Z @ self.coef_.T
        e = np.exp(np.hstack([np.zeros((len(Z), 1)), eta]))
        return (e / e.sum(axis=1, keepdims=True))[:, 1:]

    def survivor(self, panel: PeriodPanel) -> np.ndarray:
        """(n_rows,) S(s) within each entity block, conditioned on entry."""
        h = self.hazards(panel).sum(axis=1)
        out = np.empty_like(h)
        starts = np.searchsorted(panel.entity, np.arange(panel.n_entities), side="left")
        ends = np.searchsorted(panel.entity, np.arange(panel.n_entities), side="right")
        for i in range(panel.n_entities):
            lo, hi = int(starts[i]), int(ends[i])
            out[lo:hi] = np.cumprod(1.0 - h[lo:hi])
        return out


# --------------------------------------------------------------- evaluation rules
def determined_at(panel: PeriodPanel, origin: int) -> np.ndarray:
    """Per entity: +1 event by `origin`, 0 no event by `origin`, -1 NOT DETERMINED.

    The rule the manifesto leaves open and interval censoring forces. At origin $o$ an entity whose
    interval straddles $o$ -- $t_L < o \\leq t_R$ -- has an outcome that is not yet determined: the
    source says the event happened somewhere in the interval and $o$ falls inside it. Such an entity
    is neither a positive nor a negative at that origin and belongs in neither. Scoring it either
    way invents information; dropping it silently hides how much was dropped, so the count is
    returned and callers report it.
    """
    out = np.zeros(panel.n_entities, dtype=np.int8)
    ev = panel.cause != CENSORED
    out[ev & (panel.t_R <= origin)] = 1
    out[ev & (panel.t_L >= origin)] = 0
    out[ev & (panel.t_L < origin) & (panel.t_R > origin)] = -1
    out[~ev] = np.where(panel.t_R[~ev] >= origin, 0, -1)
    return out


def calibration_at(pred_event_by: np.ndarray, panel: PeriodPanel, origin: int,
                   n_bins: int = 10) -> dict:
    """Calibration of P(event by `origin`) against the determined outcomes only.

    §9.3 makes calibration a primary metric rather than a companion, and interval censoring makes
    it awkward: the outcome is a set of periods, not a point, so the usual "observed indicator"
    does not exist for every entity. The resolution is the same one `determined_at` uses -- assess
    predictions only where the observable is determined, and report the share that was not.
    """
    det = determined_at(panel, origin)
    keep = det >= 0
    y = det[keep].astype(float)
    p = np.clip(np.asarray(pred_event_by, float)[keep], 1e-9, 1 - 1e-9)
    if y.size == 0 or len(np.unique(y)) < 2:
        return {"origin": origin, "n": int(y.size), "undetermined_share": float((~keep).mean()),
                "note": "not estimable at this origin"}

    # Calibration slope on the logit scale: 1.0 is calibrated, <1 overconfident. The prior work
    # reported a Brier score with acknowledged overconfidence and stopped there; §9.3 asks for the
    # slope precisely so that "overconfident" becomes a number.
    from sklearn.linear_model import LogisticRegression
    lr = LogisticRegression(fit_intercept=True, C=1e6, max_iter=1000)
    lr.fit(np.log(p / (1 - p)).reshape(-1, 1), y)

    edges = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    edges[0], edges[-1] = 0.0, 1.0
    b = np.clip(np.digitize(p, edges[1:-1]), 0, n_bins - 1)
    bins = [{"bin": int(k), "n": int((b == k).sum()),
             "mean_pred": float(p[b == k].mean()), "observed": float(y[b == k].mean())}
            for k in range(n_bins) if (b == k).any()]
    return {
        "origin": origin, "n": int(y.size),
        "undetermined_share": float((~keep).mean()),
        "brier": float(np.mean((p - y) ** 2)),
        "calibration_slope": float(lr.coef_[0, 0]),
        "calibration_intercept": float(lr.intercept_[0]),
        "bins": bins,
    }


def events_per_parameter(panel: PeriodPanel, n_covariates: int) -> dict:
    """Events per fitted parameter, per cause. C8's bound made explicit rather than assumed.

    The convention is ten events per parameter. With 22 absorption events the three-cause model
    supports two, which is why C8 tests P5 on the collapsed two-cause contrast instead.
    """
    per_cause = {int(j): int((panel.cause == j).sum()) for j in np.unique(panel.cause) if j >= 1}
    n_params = n_covariates + 2          # intercept and the period baseline
    return {
        "events_per_cause": per_cause,
        "parameters_per_cause": n_params,
        "events_per_parameter": {j: round(n / n_params, 2) for j, n in per_cause.items()},
        "supported_covariates_at_10_per_param": {j: max(n // 10 - 2, 0)
                                                 for j, n in per_cause.items()},
    }

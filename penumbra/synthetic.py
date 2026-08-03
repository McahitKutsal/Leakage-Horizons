"""WS3 for PENUMBRA: a synthetic event corpus with a known back-dating parameter $\\beta$.

CLIQUEBAIT's generator has a leakage coefficient $\\alpha$ and no time structure worth the name:
groups exist or do not at each step, and leakage is measured at zero lag. That is the setting the
D-series was calibrated in. PENUMBRA needs one more axis, because the quantity being calibrated is
a **horizon**.

    beta = how many steps before an event its administrative traces appear in r*.

The calibration target is therefore exact and stated in advance: **$\\Delta^\\star$ should recover
$\\beta$.** A leakage-horizon estimator that does not is broken, and there is no way to learn that
from real data, where $\\beta$ is what we are trying to measure.

Generative story
----------------
Nodes carry drifting latent positions. Coalitions form at a time with a latent-cohesive founding
membership, and states accede later. Labels come from latent cohesion and from nothing observed,
exactly as in the prior generator.

Leakage enters through **what r\\* believes the membership to be**: r\\*'s view is the true
membership shifted $\\beta$ steps earlier, so a state acceding at $t + \\beta$ is already inside
r\\*'s membership at $t$. That is the administrative story of section 1 rather than an abstraction of it --
an accession protocol signed and recorded before it takes effect.

    beta = 0 : r* reflects membership as it is. Zero-lag leakage, CLIQUEBAIT's regime.
    beta = 3 : an accession three steps away is already an edge. Delta* should come back 3.

Two design requirements, both inherited as hard constraints
----------------------------------------------------------
**Density invariance, now across both axes.** CLIQUEBAIT's FINDINGS section 8 records that without it
"every diagnostic would track alpha for reasons unrelated to leakage". The same holds for beta with
more force, because back-dating enlarges the pool of group-induced dyads: a naive generator would
make r* denser at higher beta and every horizon curve would move for that reason alone.
`verify_invariance` checks it on both axes.

**Clique completeness must not vary with beta.** This is the trap the prior design would have
walked into. If a fixed edge budget were split among all coalitions whose back-dating window is
open, then raising beta would open more windows, sample each coalition's dyads more sparsely, and
degrade the clique property -- confounding beta with completeness, when the clique property is
precisely what `clique_contrast` measures. So **alpha is defined as completeness**: each eligible
back-dated dyad is recorded with probability alpha, and the background is whatever the fixed budget
leaves. Density stays fixed, completeness stays alpha, and the two axes stay orthogonal.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

__all__ = ["SyntheticConfig", "generate", "verify_invariance"]


@dataclass
class SyntheticConfig:
    # Sized so that r*'s fixed edge budget covers the WORST-CASE year of back-dated eligible
    # dyads over the whole sweep, measured rather than guessed: the peak is 1,568 dyads at
    # beta <= 10, needing density 0.0788, so 0.09 leaves headroom. Sizing the budget once from
    # the worst case is what lets alpha = 1 actually mean complete recording while r*'s density
    # stays fixed. Letting the budget grow with beta instead would restore invariance on paper
    # and destroy it in fact.
    n_nodes: int = 200
    n_years: int = 40
    latent_dim: int = 8
    latent_drift: float = 0.04

    n_coalitions: int = 30
    size_min: int = 4
    size_max: int = 12
    # Accessions per coalition over its life. T1 carries the paper, so the generator has to
    # supply accession events rather than only formations.
    accessions_per_coalition: int = 3
    cohesion_quantile: float = 0.30

    n_latent_relations: int = 2      # genuinely predictive, no group mechanism at all
    include_noise_relation: bool = True
    # `r_current` records the SAME membership r* does, at the same completeness, but never
    # back-dates: beta = 0 by construction. It is the band's primary anchor, and the synthetic
    # testbed's main finding is that it has to be. Anchors without a group mechanism sit at a
    # clique rate of exactly zero, which makes the band far tighter than the residual a relation
    # that records the present honestly still shows -- so Delta*_lo overshoots and the penumbra
    # reads wider than it is. See PENUMBRA-OUTCOMES C17.
    include_current_relation: bool = True

    # r*'s density must be low enough that back-dated dyads can fill the budget at alpha = 1;
    # otherwise nominal alpha saturates and the top of the sweep is not the regime it claims.
    density_rstar: float = 0.09
    # The band's anchors must be DENSITY-MATCHED to r*. CLIQUEBAIT established that omega
    # over-ranks dense relations; the clique rate inherits that, so an r* at 0.09 against anchors
    # at 0.06 ranks top at every horizon on density alone and the sensitive bound never fires.
    # Measured: with the anchors at 0.06 the upper bound was unreachable at every beta.
    density_other: float = 0.09
    density_noise: float = 0.09

    negatives_per_positive: int = 3
    negative_budget: int = 2
    seed: int = 0


def _pairwise(Z: np.ndarray) -> np.ndarray:
    d2 = ((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(d2, np.inf)
    return np.sqrt(d2)


def _gumbel_topk(pairs: list, weights: np.ndarray, n: int, rng) -> list:
    """Weighted sampling without replacement, one pass."""
    n = min(n, len(pairs))
    if n <= 0:
        return []
    w = np.clip(np.asarray(weights, float), 1e-12, None)
    keys = np.log(w) + rng.gumbel(size=len(w))
    return [pairs[i] for i in np.argpartition(-keys, n - 1)[:n]]


def generate(alpha: float = 1.0, beta: int = 0, cfg: SyntheticConfig | None = None):
    """One synthetic corpus at completeness `alpha` and back-dating horizon `beta`.

    Returns `(edges, events, membership, groups, meta)`. `edges`, `events` and `membership` carry
    the same column names LEDGER uses, so UMBRA consumes synthetic and real corpora through one
    code path -- which is what the domain-generality claim in section 11 has to rest on.
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    if beta < 0:
        raise ValueError("beta must be >= 0")
    cfg = cfg or SyntheticConfig()
    rng = np.random.default_rng(cfg.seed)

    Z = rng.normal(size=(cfg.n_nodes, cfg.latent_dim))
    all_pairs = list(combinations(range(cfg.n_nodes), 2))
    n_pairs = len(all_pairs)
    pair_ix = {p: i for i, p in enumerate(all_pairs)}

    # ---- latent trajectory, and the distances every later step reads off it ----
    D: list[np.ndarray] = []
    for _ in range(cfg.n_years):
        Z = Z + cfg.latent_drift * rng.normal(size=Z.shape)
        D.append(_pairwise(Z))

    # ---- coalitions: formation time, founding members, accession schedule ----
    # A coalition forms at t_form with a latent-cohesive core and grows. Membership is TRUE
    # membership; what r* sees is this shifted beta steps earlier, built below.
    coalitions = []
    for c in range(cfg.n_coalitions):
        t_form = int(rng.integers(beta, max(beta + 1, cfg.n_years - 4)))
        k = int(rng.integers(cfg.size_min, cfg.size_max + 1))
        seed_node = int(rng.integers(cfg.n_nodes))
        order = np.argsort(D[t_form][seed_node])
        founders = sorted({seed_node, *(int(v) for v in order[:k - 1])})

        joins: list[tuple[int, int]] = []          # (ccode, year)
        pool = [v for v in order[k - 1:k - 1 + 4 * cfg.accessions_per_coalition]
                if v not in set(founders)]
        rng.shuffle(pool)
        for a in range(min(cfg.accessions_per_coalition, len(pool))):
            t_acc = t_form + 1 + int(rng.integers(0, max(1, cfg.n_years - t_form - 2)))
            if t_acc < cfg.n_years:
                joins.append((int(pool[a]), t_acc))
        coalitions.append({"entity_id": f"syn:{c}", "t_form": t_form,
                           "founders": founders, "joins": sorted(joins, key=lambda x: x[1])})

    def members_at(co: dict, t: int, shift: int = 0) -> list[int]:
        """True membership at t, or r*'s view when `shift` = beta.

        `shift` moves the calendar of the coalition earlier: a coalition forming at t_form is
        visible from t_form - shift, and a state acceding at t_acc is a member from t_acc - shift.
        That single displacement is the whole leakage mechanism.
        """
        if t < co["t_form"] - shift:
            return []
        return co["founders"] + [c for c, ta in co["joins"] if t >= ta - shift]

    # ---- membership and events, in LEDGER's schema ----
    mem_rows, ev_rows = [], []
    for co in coalitions:
        for t in range(cfg.n_years):
            for c in members_at(co, t):
                mem_rows.append((co["entity_id"], c, t, 1))
        ev_rows.append((co["entity_id"], "founding", pd.NA,
                        co["t_form"] - 1, co["t_form"], "exact", co["t_form"]))
        for c, ta in co["joins"]:
            ev_rows.append((co["entity_id"], "accession", c, ta - 1, ta, "exact", ta))

    membership = pd.DataFrame(mem_rows, columns=["entity_id", "ccode", "year", "status"])
    events = pd.DataFrame(ev_rows, columns=["entity_id", "event_type", "ccode",
                                            "t_L", "t_R", "dating_stratum", "knowable_from"])

    # ---- relations ----
    rel_names = ["r_star"] + [f"r_latent_{i+1}" for i in range(cfg.n_latent_relations)]
    if cfg.include_current_relation:
        rel_names.append("r_current")
    if cfg.include_noise_relation:
        rel_names.append("r_noise")

    edge_rows = []
    meta = {"alpha": alpha, "beta": beta,
            "density": {r: [] for r in rel_names},
            "rstar_group_edges": [], "rstar_total": [],
            "eligible_backdated_dyads": [], "completeness_realised": []}

    for t in range(cfg.n_years):
        sim_w = np.array([1.0 / (1e-6 + D[t][u, v] ** 2) for u, v in all_pairs])

        # r*'s eligible dyads: those induced by the BACK-DATED membership. r_current's are the
        # same construction at shift 0, which is what makes it a like-for-like anchor.
        def _eligible(shift: int) -> list:
            out = set()
            for co in coalitions:
                ms = members_at(co, t, shift=shift)
                for u, v in combinations(sorted(ms), 2):
                    out.add((u, v))
            return sorted(out)

        eligible = _eligible(beta)
        eligible_now = _eligible(0)
        meta["eligible_backdated_dyads"].append(len(eligible))

        budget = int(round(cfg.density_rstar * n_pairs))

        def _compose(elig: list) -> list:
            """Group edges at completeness alpha, plus similarity background to a fixed budget."""
            ng = int(round(alpha * len(elig)))
            ge = ([elig[i] for i in rng.choice(len(elig), size=min(ng, len(elig)),
                                               replace=False)] if ng else [])
            tk = set(ge)
            ix = [i for i, pp in enumerate(all_pairs) if pp not in tk]
            return list(ge) + list(_gumbel_topk([all_pairs[i] for i in ix], sim_w[ix],
                                                budget - len(ge), rng))

        # alpha is COMPLETENESS, not budget share: each eligible dyad is recorded with
        # probability alpha. This is what keeps the clique property independent of beta.
        n_group = int(round(alpha * len(eligible)))
        if n_group > budget:
            warnings.warn(
                f"t={t}: back-dated dyads at alpha={alpha:.2f}, beta={beta} need {n_group} of a "
                f"{budget} budget, so r*'s density cannot be held fixed. Lower alpha, lower "
                f"n_coalitions, or raise density_rstar -- otherwise beta and density move "
                f"together and the calibration measures the wrong thing.",
                RuntimeWarning, stacklevel=2)
            n_group = budget
        group_edges = ([eligible[i] for i in rng.choice(len(eligible), size=n_group,
                                                        replace=False)] if n_group else [])
        taken = set(group_edges)
        rest_ix = [i for i, p in enumerate(all_pairs) if p not in taken]
        bg = _gumbel_topk([all_pairs[i] for i in rest_ix], sim_w[rest_ix],
                          budget - len(group_edges), rng)
        rstar = list(group_edges) + list(bg)
        meta["rstar_group_edges"].append(len(group_edges))
        meta["rstar_total"].append(len(rstar))
        meta["completeness_realised"].append(
            len(group_edges) / len(eligible) if eligible else np.nan)

        for rel in rel_names:
            if rel == "r_star":
                edges = rstar
            elif rel == "r_current":
                edges = _compose(eligible_now)
            elif rel == "r_noise":
                b = int(round(cfg.density_noise * n_pairs))
                edges = [all_pairs[i] for i in rng.choice(n_pairs, size=b, replace=False)]
            else:
                b = int(round(cfg.density_other * n_pairs))
                edges = _gumbel_topk(all_pairs, sim_w, b, rng)
            meta["density"][rel].append(len(edges) / n_pairs)
            for u, v in edges:
                edge_rows.append((rel, t, u, v, 1))

    edges = pd.DataFrame(edge_rows, columns=["relation", "year", "cow_i", "cow_j", "weight"])

    # ---- candidate groups with negatives, for the D-series probes ----
    group_rows = []
    for co in coalitions:
        for t in range(cfg.n_years):
            ms = members_at(co, t)
            if len(ms) < 2:
                continue
            group_rows.append({"members": ms, "label": 1, "time": t,
                               "group_id": co["entity_id"], "neg_type": ""})
            pool = [x for x in range(cfg.n_nodes) if x not in set(ms)]
            b = min(cfg.negative_budget, len(ms) - 2)
            for _ in range(cfg.negatives_per_positive):
                if b < 1:
                    continue
                drop = set(rng.choice(len(ms), size=b, replace=False).tolist())
                new = [m for i, m in enumerate(ms) if i not in drop]
                new += [pool[i] for i in rng.choice(len(pool), size=b, replace=False)]
                group_rows.append({"members": sorted(new), "label": 0, "time": t,
                                   "group_id": co["entity_id"], "neg_type": "hard"})
    groups = pd.DataFrame(group_rows)

    meta["density_rstar_mean"] = float(np.mean(meta["density"]["r_star"]))
    meta["completeness_mean"] = float(np.nanmean(meta["completeness_realised"]))
    meta["completeness_shortfall"] = float(alpha - meta["completeness_mean"])
    meta["n_positives"] = int((groups.label == 1).sum())
    meta["n_negatives"] = int((groups.label == 0).sum())
    meta["n_accessions"] = int((events.event_type == "accession").sum())
    return edges, events, membership, groups, meta


def verify_invariance(alphas, betas, cfg: SyntheticConfig | None = None) -> pd.DataFrame:
    """r*'s density must not move with alpha OR with beta. Without this nothing calibrates.

    The beta axis is the new one and the more dangerous: back-dating enlarges the pool of
    group-induced dyads, so a generator that added group edges on top of a background would make
    r* denser at longer horizons, and every horizon curve would slope for that reason alone.
    """
    rows = []
    for a in alphas:
        for b in betas:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                _e, _ev, _m, _g, meta = generate(a, b, cfg)
                warned = any(issubclass(x.category, RuntimeWarning) for x in w)
            rows.append({
                "alpha": a, "beta": b,
                "density_rstar": round(meta["density_rstar_mean"], 6),
                "density_latent_1": round(float(np.mean(meta["density"]["r_latent_1"])), 6),
                "completeness": round(meta["completeness_mean"], 4),
                "shortfall": round(meta["completeness_shortfall"], 4),
                "eligible_mean": int(np.mean(meta["eligible_backdated_dyads"])),
                "budget_exceeded": warned,
                "n_pos": meta["n_positives"], "n_acc": meta["n_accessions"],
            })
    return pd.DataFrame(rows)

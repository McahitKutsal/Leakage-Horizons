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

__all__ = ["SyntheticConfig", "generate", "verify_invariance",
           "ParametricConfig", "generate_parametric"]


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


# =============================================================================================
# The parametric generator: homophily, heterogeneous back-dating, and dating noise.
# =============================================================================================
#
# `generate` above is left byte-identical on purpose. Table 2 of the manuscript -- the only evidence
# that the estimator recovers a known width -- is computed by it, and a refactor that moved those six
# numbers while claiming to add a feature is the defect class D-35 exists to prevent. Everything below
# is a second generator that shares the module's helpers and nothing else.
#
# It exists because the paper's deepest claim was argued rather than measured. Section 6.3 holds that a
# trace of the event and a persistent similarity between candidate and members enter a pooled contrast
# identically, so no such contrast can separate them. `generate` cannot exhibit that: its homophily is
# fixed -- the background is always drawn by latent proximity and the acceding entities are always the
# group's nearest non-members -- so there is no axis along which the confusion can be shown to grow.
# Three axes are added here, each answering a specific objection (revision items 2.2, 2.3, 2.10).
#
# **Homophily h.** The exponent on latent similarity in every sampling weight. At h = 0 the background
# is a uniform random sample and the acceding entity is a uniform random non-member, so positives and
# negatives differ only through the event; at h = 1 similarity enters linearly; above that it
# concentrates. Ground truth beta is set independently of h, so the bias of each instrument becomes a
# measurable function of h rather than an argument about it.
#
# **A heterogeneous back-dating width.** `generate`'s beta is a sharp step: every event appears exactly
# beta periods early, which is a regime the estimator can hardly fail in. Real back-dating is spread --
# the PTA register's own coded gaps have median 1, mean 1.71 and a tail to 9 -- so `beta_pmf` draws a
# width per event. That makes "the true horizon" a decision rather than a number, and the decision is
# reported: meta["beta_quantiles"] carries the distribution the lower bound is graded against.
#
# **Dating noise.** A share of events whose *coded* date is displaced from the true one, the register
# being wrong rather than early. This is the synthetic counterpart of corpus A's declared-resolution
# stratum, where a coding rule locates pre-1965 dates only within five-year blocks and focal isolation
# consequently reads 0.1419 at one period.
#
# **Whether the anchors share the latent space.** The switch that decides whether mechanism (h) fires.
# Shared, the anchors carry the same homophily as the target relation and the reference band subtracts
# nearly all of it, which is corpus A. Drawn from an independent latent trajectory, they carry none of
# it and the band subtracts nothing, which is corpus B. Both regimes come out of one generator, so the
# difference between the two field corpora becomes a setting rather than a conjecture.


@dataclass
class ParametricConfig(SyntheticConfig):
    """`SyntheticConfig` plus the three axes `generate` holds fixed.

    Defaults sit at the qualitative position of the legacy generator -- homophily on, anchors sharing
    the latent space, a sharp width, no dating noise -- but they do **not** reproduce its numbers and
    are not meant to. The legacy path is a different sequence of draws and stays the reference for
    Table 2.
    """

    # Exponent on latent similarity. 0 = none, 1 = linear, above 1 = concentrated. Applied to the edge
    # background, to the founding membership and to the pool acceding entities are drawn from, because
    # the argument is about all three: homophily makes positives denser than negatives whether it acts
    # on who joins or on who is tied to whom.
    homophily: float = 1.0
    # **The functional form homophily takes, because a result that holds for one kernel is a result
    # about that kernel.** An external read objected that "an exponent on latent similarity" is a single
    # parametrisation carrying the paper's two most important findings. These three are not
    # reparametrisations of each other: `power` is an unbounded power law on inverse squared distance,
    # `logistic` is a bounded kernel that saturates rather than diverging as distance goes to zero, and
    # `block` abandons the continuous kernel entirely for discrete latent communities, where two nodes
    # are similar if they share a block and not otherwise. All three reduce to a uniform weight at
    # h = 0, which is what keeps the negative control a negative control in each of them.
    homophily_form: str = "power"
    n_blocks: int = 8
    # Corpus A analogue when True, corpus B analogue when False.
    anchors_share_latent_space: bool = True
    # ((width, weight), ...) over back-dating widths, or None for the sharp width `beta` supplies.
    beta_pmf: tuple | None = None
    # Share of accession events whose coded date is displaced by `date_noise_shift` from the truth.
    date_noise: float = 0.0
    date_noise_shift: int = 1

    # **Co-back-dating: the curator who touches more than one register at a time.**
    #
    # Section 3.3 asserts that the focal group's own edges are the only place administrative back-dating
    # can live, "a curator's decision to date a membership from signature rather than operation affects
    # that group's record and nothing else". That is true of the focal *event* and false of the target
    # *relation*. If the acceding entity and a sitting member are co-members of some other group Y, the
    # dyad they carry in r* is Y's, and if Y's record is back-dated that dyad is an administrative trace
    # that focal isolation never reads, because it is not on the focal group's record.
    #
    # For the trace to be correlated with the label the entity's entry into Y has to be near its entry
    # into the focal group, which is what accession waves are: expansion rounds, post-independence
    # batches, bloc changes. `co_backdating` is the share of accession events that arrive in such a wave,
    # each one adding an entry of the same entity into another group that already overlaps the focal one,
    # dated by the same curatorial convention and therefore back-dated by its own draw from the same
    # width law. At 0 the generator is exactly the one Table 3 and Table 4 were computed on.
    co_backdating: float = 0.0
    # How many members the partner group must share with the focal group at the event period, so the
    # co-back-dated dyad actually lands inside the focal group's star rather than somewhere harmless.
    co_backdating_overlap: int = 1
    # **The partner register's own convention.** ((width, weight), ...) or None to reuse the focal law.
    #
    # This is the axis the mechanism turns on, and the first version of the experiment missed it. Under
    # a single convention the partner record is back-dated by the same width as the focal one, so every
    # dyad it puts into r* early is one the focal record already carries and focal isolation loses
    # nothing: co-back-dating is harmless when every curator works to one rule. It stops being harmless
    # when conventions differ across groups, which is corpus A exactly -- 7,615 exactly dated events
    # against 447 the source dates only to a five-year block. Giving the partner its own width law is
    # what makes the two regimes separable, and reporting both is what turns the objection into a
    # measurement instead of a refutation or a confirmation chosen by a default.
    co_backdating_beta_pmf: tuple | None = None
    seed: int = 0


def _weighted_choice(rng, candidates: np.ndarray, weights: np.ndarray, n: int) -> np.ndarray:
    """`n` distinct draws from `candidates` with probability proportional to `weights`.

    Gumbel top-k rather than a normalised probability vector, for the same reason `_gumbel_topk` uses
    it: one pass, and it degenerates cleanly to a uniform sample when every weight is equal -- which
    is exactly the h = 0 case the negative control needs.
    """
    n = int(min(n, candidates.size))
    if n <= 0:
        return np.empty(0, candidates.dtype)
    keys = np.log(np.clip(np.asarray(weights, float), 1e-300, None)) + rng.gumbel(
        size=candidates.size)
    return candidates[np.argpartition(-keys, n - 1)[:n]]


def generate_parametric(beta: int = 0, alpha: float = 1.0,
                        cfg: ParametricConfig | None = None):
    r"""One synthetic corpus with homophily, an optional width distribution, and dating noise.

    Returns `(edges, events, membership, groups, meta, membership_recorded)` in LEDGER's column names,
    so `HorizonAudit` consumes any of the frames unchanged. The sixth element is what `generate` has no
    equivalent of and what focal isolation needs, so it is worth its own paragraph.

    **Two registers, because the two instruments read different objects.** `membership` is the honest
    register: an entity is a member from the period it truly joined. U1 has to be built on that one,
    since the risk set is "states not already members" and a back-dated register would drop exactly the
    leaking rows as ineligible -- the candidate is already a member there, so it is not at risk, and
    the horizons the leak lives at would be empty. `membership_recorded` is the register a curator
    wrote: every event appears `beta` periods early, which is the PTA situation exactly, a relation
    dated from signature against an event dated from entry into force. Focal isolation reads that one.
    Giving both makes the two instruments comparable on one corpus with one known truth, which is what
    Sections 6.2 and 6.3 compare across two field sources and cannot compare within either.

    The leakage mechanism is unchanged in kind: $r^\star$'s view of the membership is the truth moved
    earlier. What changes is that the displacement is per event rather than per corpus, that the
    similarity structure has a strength, and that the coded date can be wrong.

    Ground truth is carried in `meta`:

    * `beta_per_event` -- the width actually applied to each accession, so any quantile of the true
      distribution can be taken afterwards rather than being fixed here;
    * `beta_quantiles` -- max, 0.9, 0.75 and median, because under a spread width "the horizon" is a
      choice and the manuscript has to name which one the lower bound is graded against;
    * `coded_minus_true` -- the dating-noise displacement, which is the only thing focal isolation can
      see when the register is wrong rather than early.
    """
    cfg = cfg or ParametricConfig()
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    if beta < 0:
        raise ValueError("beta must be >= 0")
    if cfg.homophily < 0:
        raise ValueError("homophily must be >= 0")
    rng = np.random.default_rng(cfg.seed)
    h = float(cfg.homophily)

    all_pairs = list(combinations(range(cfg.n_nodes), 2))
    n_pairs = len(all_pairs)
    pair_arr = np.arange(n_pairs)

    # ---- two latent trajectories: the one the group mechanism lives in, and an independent one ----
    Z = rng.normal(size=(cfg.n_nodes, cfg.latent_dim))
    Z2 = rng.normal(size=(cfg.n_nodes, cfg.latent_dim))
    D: list[np.ndarray] = []
    D2: list[np.ndarray] = []
    for _ in range(cfg.n_years):
        Z = Z + cfg.latent_drift * rng.normal(size=Z.shape)
        Z2 = Z2 + cfg.latent_drift * rng.normal(size=Z2.shape)
        D.append(_pairwise(Z))
        D2.append(_pairwise(Z2))

    # Similarity as a *weight* rather than as an ordering, so h can turn it off. At h = 0 every pair
    # weighs 1 and every draw below is uniform, which is what makes the h = 0, beta = 0 cell a genuine
    # negative control rather than a low-homophily one.
    form = cfg.homophily_form
    if form not in ("power", "logistic", "block"):
        raise ValueError(f"unknown homophily_form: {form!r}")
    # Block membership is drawn once and is a property of the corpus rather than of a period, which is
    # what makes it a different mechanism from a distance kernel rather than a transform of one.
    blocks = rng.integers(0, cfg.n_blocks, size=cfg.n_nodes) if form == "block" else None

    def _kernel(d: np.ndarray) -> np.ndarray:
        """Pairwise similarity weight from a distance matrix, under the declared form."""
        if h == 0.0:
            return np.ones(n_pairs)
        if form == "power":
            s = np.array([1.0 / (1e-6 + d[u, v] ** 2) for u, v in all_pairs])
            return s if h == 1.0 else s ** h
        if form == "logistic":
            # Bounded in (0, 1] and centred on the median distance, so raising h concentrates the
            # weight on close pairs without letting any single pair's weight diverge.
            raw = np.array([d[u, v] for u, v in all_pairs])
            fin = raw[np.isfinite(raw)]
            mid = float(np.median(fin))
            scale = float(np.std(fin)) or 1.0
            return 1.0 / (1.0 + np.exp(h * (raw - mid) / scale))
        # block: within-block pairs are weighted up by h, everything else weighs 1. No distance enters.
        same = np.array([1.0 if blocks[u] == blocks[v] else 0.0 for u, v in all_pairs])
        return 1.0 + h * same * float(cfg.n_blocks)

    def sim(dist: np.ndarray) -> np.ndarray:
        return _kernel(dist)

    def _node_weights(dist_row: np.ndarray, node: int, others: np.ndarray) -> np.ndarray:
        """The same three forms, for a single node against a candidate set."""
        if h == 0.0:
            return np.ones(others.size)
        if form == "power":
            return (1.0 / (1e-6 + dist_row[others] ** 2)) ** h
        if form == "logistic":
            # `_pairwise` puts inf on the diagonal, so a row's median and spread have to be taken over
            # the finite entries or every logistic weight comes back nan.
            finite = dist_row[np.isfinite(dist_row)]
            mid = float(np.median(finite))
            scale = float(np.std(finite)) or 1.0
            return 1.0 / (1.0 + np.exp(h * (dist_row[others] - mid) / scale))
        return 1.0 + h * (blocks[others] == blocks[node]).astype(float) * float(cfg.n_blocks)

    def _set_weights(dist: np.ndarray, members: list, pool: np.ndarray) -> np.ndarray:
        """Mean similarity from each pool entity to a member set, under the declared form."""
        if h == 0.0:
            return np.ones(pool.size)
        if form == "power":
            return np.array([np.mean(1.0 / (1e-6 + dist[v, members] ** 2)) for v in pool]) ** h
        if form == "logistic":
            flat = dist[np.ix_(pool, members)]
            flat = flat[np.isfinite(flat)]
            mid, scale = float(np.median(flat)), float(np.std(flat)) or 1.0
            return np.array([np.mean(1.0 / (1.0 + np.exp(h * (dist[v, members] - mid) / scale)))
                             for v in pool])
        mem_blocks = blocks[members]
        return np.array([1.0 + h * float(np.mean(blocks[v] == mem_blocks)) * float(cfg.n_blocks)
                         for v in pool])

    # ---- the width distribution ----
    pmf = cfg.beta_pmf
    if pmf is not None:
        widths = np.array([int(w) for w, _p in pmf])
        probs = np.array([float(p) for _w, p in pmf], float)
        probs = probs / probs.sum()

    def draw_beta() -> int:
        return int(beta) if pmf is None else int(rng.choice(widths, p=probs))

    co_pmf = cfg.co_backdating_beta_pmf
    if co_pmf is not None:
        co_widths = np.array([int(w) for w, _p in co_pmf])
        co_probs = np.array([float(pp) for _w, pp in co_pmf], float)
        co_probs = co_probs / co_probs.sum()

    def draw_partner_beta() -> int:
        """The partner register's width. Its own law when one is declared, the focal law otherwise."""
        if co_pmf is None:
            return draw_beta()
        return int(rng.choice(co_widths, p=co_probs))

    # ---- coalitions ----
    coalitions = []
    max_width = int(beta if pmf is None else widths.max())
    if co_pmf is not None and cfg.co_backdating > 0:
        # `beta_form` bounds how early a group's recorded view can begin, so a partner convention wider
        # than the focal one has to widen it or the co-back-dated dyads are silently clipped.
        max_width = max(max_width, int(co_widths.max()))
    for c in range(cfg.n_coalitions):
        t_form = int(rng.integers(max_width, max(max_width + 1, cfg.n_years - 4)))
        k = int(rng.integers(cfg.size_min, cfg.size_max + 1))
        seed_node = int(rng.integers(cfg.n_nodes))

        # Founding membership drawn with weight proportional to similarity-to-seed raised to h. At
        # h = 0 this is a uniform random set, so a coalition is not a latent cluster at all.
        others = np.array([v for v in range(cfg.n_nodes) if v != seed_node])
        w_seed = _node_weights(D[t_form][seed_node], seed_node, others)
        founders = sorted({seed_node, *(int(v) for v in
                                        _weighted_choice(rng, others, w_seed, k - 1))})

        pool_src = np.array([v for v in range(cfg.n_nodes) if v not in set(founders)])
        # The acceding entities. Weighted by mean similarity to the founding membership, which is the
        # homophily channel the identification argument is actually about: at h > 0 a joiner is close
        # to the members before it joins, for reasons that are not the event.
        prox = _set_weights(D[t_form], founders, pool_src)
        pool = _weighted_choice(rng, pool_src, prox,
                                min(4 * cfg.accessions_per_coalition, pool_src.size))
        rng.shuffle(pool)

        joins = []
        for a in range(min(cfg.accessions_per_coalition, pool.size)):
            t_acc = t_form + 1 + int(rng.integers(0, max(1, cfg.n_years - t_form - 2)))
            if t_acc >= cfg.n_years:
                continue
            b_e = draw_beta()
            # The register's date, which may be wrong. The true membership start is `t_acc`; the coded
            # event date is what a forecaster is told, and focal isolation is read against it.
            shift = (cfg.date_noise_shift
                     if (cfg.date_noise > 0 and rng.random() < cfg.date_noise) else 0)
            joins.append({"ccode": int(pool[a]), "t_true": t_acc,
                          "t_coded": int(np.clip(t_acc + shift, 0, cfg.n_years - 1)),
                          "beta": b_e, "coded_minus_true": int(shift)})
        coalitions.append({"entity_id": f"syn:{c}", "t_form": t_form, "beta_form": max_width,
                           "founders": founders, "joins": sorted(joins, key=lambda x: x["t_true"])})

    def members_true(co: dict, t: int) -> list:
        if t < co["t_form"]:
            return []
        return co["founders"] + [j["ccode"] for j in co["joins"] if t >= j["t_true"]]

    def members_rstar(co: dict, t: int) -> list:
        """What r-star believes the membership to be: every event moved earlier by its own width."""
        if t < co["t_form"] - co["beta_form"]:
            return []
        return co["founders"] + [j["ccode"] for j in co["joins"]
                                 if t >= j["t_true"] - j["beta"]]

    # ---- co-back-dating: the same entity entering a second, overlapping group in the same period ----
    #
    # Every join added here is an ordinary accession event with an ordinary width. What makes it the
    # test of Section 3.3's "and nothing else" is *where* it lands: inside a group that already shares
    # members with the focal one, at the focal event's own period. The dyads it back-dates therefore run
    # from the acceding entity into the focal group's sitting members, and they are administrative
    # traces of the focal event that live on another group's record. Focal isolation cannot read them,
    # by construction, because it reads one record.
    n_co = 0
    if cfg.co_backdating > 0:
        focal_events = [(ci, jx) for ci, co in enumerate(coalitions)
                        for jx in range(len(co["joins"]))]
        rng.shuffle(focal_events)
        take = int(round(cfg.co_backdating * len(focal_events)))
        for ci, jx in focal_events[:take]:
            co = coalitions[ci]
            j = co["joins"][jx]
            v, t = j["ccode"], j["t_true"]
            focal_ms = set(members_true(co, t))
            # The entity must not belong to the partner group on any other footing. Adding it to a
            # group it joins anyway would give the same entity two entries into one group, which is a
            # prior membership spell and therefore mechanism (i) rather than this one; the first version
            # of this block allowed it and inflated the focal record's own reach to ten periods.
            partners = [k for k, cy in enumerate(coalitions)
                        if k != ci and cy["t_form"] <= t
                        and v not in (set(cy["founders"])
                                      | {int(x["ccode"]) for x in cy["joins"]})
                        and len(set(members_true(cy, t)) & focal_ms) >= cfg.co_backdating_overlap]
            if not partners:
                continue
            cy = coalitions[int(rng.choice(partners))]
            shift = (cfg.date_noise_shift
                     if (cfg.date_noise > 0 and rng.random() < cfg.date_noise) else 0)
            cy["joins"].append({"ccode": int(v), "t_true": int(t),
                                "t_coded": int(np.clip(t + shift, 0, cfg.n_years - 1)),
                                "beta": draw_partner_beta(), "coded_minus_true": int(shift),
                                "co_backdated_with": co["entity_id"]})
            cy["joins"].sort(key=lambda x: x["t_true"])
            n_co += 1

    # ---- the two membership registers, and the events, in LEDGER's schema ----
    mem_rows, rec_rows, ev_rows = [], [], []
    for co in coalitions:
        for t in range(cfg.n_years):
            for c in members_true(co, t):
                mem_rows.append((co["entity_id"], c, t, 1))
            for c in members_rstar(co, t):
                rec_rows.append((co["entity_id"], c, t, 1))
        ev_rows.append((co["entity_id"], "founding", pd.NA,
                        co["t_form"] - 1, co["t_form"], "exact", co["t_form"]))
        for j in co["joins"]:
            stratum = "exact" if j["coded_minus_true"] == 0 else "declared_resolution"
            ev_rows.append((co["entity_id"], "accession", j["ccode"],
                            j["t_coded"] - 1, j["t_coded"], stratum, j["t_coded"]))

    membership = pd.DataFrame(mem_rows, columns=["entity_id", "ccode", "year", "status"])
    membership_recorded = pd.DataFrame(rec_rows, columns=["entity_id", "ccode", "year", "status"])
    events = pd.DataFrame(ev_rows, columns=["entity_id", "event_type", "ccode",
                                            "t_L", "t_R", "dating_stratum", "knowable_from"])

    # ---- ground truth: how far the trace of an event reaches, and whose record carries it ----
    def _admin_reach(max_lead: int = 12) -> list:
        r"""Per focal accession event, the reach of the administrative trace, split by record.

        Two widths per event, both defined the way focal isolation's rule reads a curve -- the largest
        lead time of one or more at which a trace is present, and zero if none is -- so that a corpus
        maximum plus one is directly comparable with what the estimators report.

        * `focal_record_reach` is what focal isolation identifies: the acceding entity is on the focal
          group's own recorded register that many periods before its coded date. Under the generator's
          construction this is the event's own width.
        * `off_focal_reach` is what Section 3.3 says cannot exist. A dyad from the acceding entity into
          a sitting member of the focal group, carried by *another* group's recorded register, absent
          from every honest register at that period, and absent from the focal group's own recorded
          register too, so no reading of the focal record can recover it.
        * `co_backdated_reach` is the part of the second that the focal event *caused*: only the partner
          entries this event's own wave added are counted. The distinction is the whole difficulty. Any
          group's back-dating of any membership puts administrative dyads into r* at arbitrary lead
          times, and an entity that joined some other group nine periods ago carries one at lead eleven
          for reasons that have nothing to do with the focal event. Calling that a leakage horizon of
          eleven would be the error this paper is about. So the horizon reported against an estimator is
          `max(focal_record_reach, co_backdated_reach)`, which counts only traces the event produced,
          and `off_focal_reach` is reported separately and against matched negatives, because a level
          positives and negatives share is not a trace of anything.

        `off_focal_reach` is therefore also computed for negatives: entities that never accede to the
        focal group, on the same group at the same period. The difference between the two is the only
        part of the ambient off-focal administrative content a diagnostic could read as a trace.
        """
        true_sets = [[set(members_true(co, t)) for t in range(cfg.n_years)] for co in coalitions]
        rec_sets = [[set(members_rstar(co, t)) for t in range(cfg.n_years)] for co in coalitions]
        honest = []
        for t in range(cfg.n_years):
            s = set()
            for ci in range(len(coalitions)):
                ms = sorted(true_sets[ci][t])
                s.update(combinations(ms, 2))
            honest.append(s)

        # Which partner entries each focal event's own wave added, so the caused part is separable from
        # the ambient part. Keyed by (focal group, entity, period), which identifies a focal event.
        caused: dict = {}
        for cy, cyo in enumerate(coalitions):
            for jj in cyo["joins"]:
                owner = jj.get("co_backdated_with")
                if owner is not None:
                    caused.setdefault((owner, int(jj["ccode"]), int(jj["t_true"])), set()).add(cy)

        nrng = np.random.default_rng(cfg.seed + 977)

        def _off_reach(ci: int, v: int, t: int, only) -> int:
            """Largest lead time at which another group's record carries an administrative dyad from
            `v` into the focal group's sitting members. `only` restricts the search to given groups."""
            out = 0
            search = range(len(coalitions)) if only is None else only
            for d in range(1, max_lead + 1):
                s = t - d
                if s < 0:
                    break
                members = true_sets[ci][s]
                if not members:
                    continue
                focal_rec = rec_sets[ci][s]
                for cy in search:
                    if cy == ci or v not in rec_sets[cy][s] or v in true_sets[cy][s]:
                        continue
                    for u in rec_sets[cy][s] & members:
                        if (min(u, v), max(u, v)) in honest[s]:
                            continue
                        if v in focal_rec and u in focal_rec:
                            continue
                        out = max(out, d)
                        break
            return out

        rows = []
        for ci, co in enumerate(coalitions):
            ever = set(co["founders"]) | {int(x["ccode"]) for x in co["joins"]}
            pool = [x for x in range(cfg.n_nodes) if x not in ever]
            for j in co["joins"]:
                v, t = int(j["ccode"]), int(j["t_true"])
                is_focal = "co_backdated_with" not in j
                focal_reach = 0
                for d in range(1, max_lead + 1):
                    if t - d < 0:
                        break
                    if not true_sets[ci][t - d]:
                        continue
                    if v in rec_sets[ci][t - d]:
                        focal_reach = max(focal_reach, d)
                row = {"entity_id": co["entity_id"], "ccode": v, "t_true": t,
                       "beta": int(j["beta"]), "is_focal_event": bool(is_focal),
                       "focal_record_reach": int(focal_reach)}
                if is_focal:
                    # The off-focal parts are meaningful only for an event the grid declares, because
                    # the partner entries exist to contaminate those and not each other.
                    off_reach = _off_reach(ci, v, t, None)
                    co_reach = _off_reach(ci, v, t, caused.get((co["entity_id"], v, t), set()))
                    neg = (nrng.choice(pool, size=min(4, len(pool)), replace=False)
                           if pool else np.empty(0, int))
                    row.update({
                        "off_focal_reach": int(off_reach),
                        "co_backdated_reach": int(co_reach),
                        "off_focal_reach_negatives": [int(_off_reach(ci, int(x), t, None))
                                                      for x in neg],
                        "administrative_reach": int(max(focal_reach, co_reach))})
                rows.append(row)
        return rows

    reach = _admin_reach()

    # ---- relations ----
    rel_names = ["r_star"] + [f"r_latent_{i + 1}" for i in range(cfg.n_latent_relations)]
    if cfg.include_current_relation:
        rel_names.append("r_current")
    if cfg.include_noise_relation:
        rel_names.append("r_noise")

    edge_rows = []
    meta = {"alpha": alpha, "beta": beta, "homophily": h, "homophily_form": form,
            "anchors_share_latent_space": bool(cfg.anchors_share_latent_space),
            "beta_pmf": cfg.beta_pmf, "date_noise": cfg.date_noise,
            "density": {r: [] for r in rel_names},
            "eligible_backdated_dyads": [],
            "completeness_realised": []}

    budget = int(round(cfg.density_rstar * n_pairs))
    for t in range(cfg.n_years):
        w_group = sim(D[t])
        w_anchor = sim(D[t] if cfg.anchors_share_latent_space else D2[t])

        def _eligible(view) -> list:
            out = set()
            for co in coalitions:
                ms = view(co, t)
                for u, v in combinations(sorted(ms), 2):
                    out.add((u, v))
            return sorted(out)

        eligible = _eligible(members_rstar)
        eligible_now = _eligible(members_true)
        # Recorded so the edge budget's headroom is a measured quantity rather than a claim in a
        # comment. If back-dating ever pushes the peak above the budget, r*'s density stops being
        # invariant and every horizon curve slopes for that reason alone; the count is what says
        # whether it did (D-45's lesson applied to a constant).
        meta["eligible_backdated_dyads"].append(len(eligible))

        def _compose(elig: list, weights: np.ndarray):
            """Group dyads at completeness alpha, plus a homophily background to a fixed budget."""
            n_group = int(round(alpha * len(elig)))
            if n_group > budget:
                warnings.warn(
                    f"t={t}: group dyads at alpha={alpha:.2f} need {n_group} of a {budget} budget, "
                    f"so r*'s density cannot be held fixed",
                    RuntimeWarning, stacklevel=2)
                n_group = budget
            ge = ([elig[i] for i in rng.choice(len(elig), size=n_group, replace=False)]
                  if n_group else [])
            taken = set(ge)
            rest = np.array([i for i in pair_arr if all_pairs[i] not in taken])
            bg = _weighted_choice(rng, rest, weights[rest], budget - len(ge))
            return list(ge) + [all_pairs[i] for i in bg], len(ge)

        rstar, n_group = _compose(eligible, w_group)
        meta["completeness_realised"].append(n_group / len(eligible) if eligible else np.nan)

        for rel in rel_names:
            if rel == "r_star":
                edges = rstar
            elif rel == "r_current":
                edges, _ = _compose(eligible_now, w_group)
            elif rel == "r_noise":
                b = int(round(cfg.density_noise * n_pairs))
                edges = [all_pairs[i] for i in rng.choice(n_pairs, size=b, replace=False)]
            else:
                b = int(round(cfg.density_other * n_pairs))
                edges = [all_pairs[i] for i in _weighted_choice(rng, pair_arr, w_anchor, b)]
            meta["density"][rel].append(len(edges) / n_pairs)
            for u, v in edges:
                edge_rows.append((rel, t, u, v, 1))

    edges = pd.DataFrame(edge_rows, columns=["relation", "year", "cow_i", "cow_j", "weight"])

    # ---- candidate groups with negatives, for the density-only probes ----
    group_rows = []
    for co in coalitions:
        for t in range(cfg.n_years):
            ms = members_true(co, t)
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

    betas = np.array([j["beta"] for co in coalitions for j in co["joins"]], float)
    noise = np.array([j["coded_minus_true"] for co in coalitions for j in co["joins"]], float)
    meta["density_rstar_mean"] = float(np.mean(meta["density"]["r_star"]))
    meta["density_rstar_range"] = float(np.ptp(meta["density"]["r_star"]))
    meta["completeness_mean"] = float(np.nanmean(meta["completeness_realised"]))
    meta["n_positives"] = int((groups.label == 1).sum())
    meta["n_negatives"] = int((groups.label == 0).sum())
    meta["n_accessions"] = int((events.event_type == "accession").sum())
    meta["beta_per_event"] = betas.astype(int).tolist()
    meta["beta_quantiles"] = {
        "max": int(betas.max()) if betas.size else None,
        "q90": float(np.quantile(betas, 0.90)) if betas.size else None,
        "q75": float(np.quantile(betas, 0.75)) if betas.size else None,
        "median": float(np.median(betas)) if betas.size else None,
        "mean": float(betas.mean()) if betas.size else None,
    }
    meta["coded_minus_true"] = {
        "share_displaced": float((noise != 0).mean()) if noise.size else 0.0,
        "shift": cfg.date_noise_shift}
    meta["n_pairs"] = int(n_pairs)
    meta["edge_budget"] = int(budget)
    meta["peak_eligible_backdated_dyads"] = int(max(meta["eligible_backdated_dyads"]))
    meta["budget_headroom"] = int(budget - max(meta["eligible_backdated_dyads"]))
    meta["n_rows_true_register"] = int(len(membership))
    meta["n_rows_recorded_register"] = int(len(membership_recorded))
    partner_widths = [int(j["beta"]) for co in coalitions for j in co["joins"]
                      if "co_backdated_with" in j]
    focal_rows = [r for r in reach if r["is_focal_event"]]
    meta["co_backdating"] = {
        "share_requested": float(cfg.co_backdating),
        "overlap_required": int(cfg.co_backdating_overlap),
        "partner_width_law": ("the focal law" if cfg.co_backdating_beta_pmf is None
                              else cfg.co_backdating_beta_pmf),
        "events_added": int(n_co),
        "partner_width_max": int(max(partner_widths)) if partner_widths else None,
        "partner_width_mean": (round(float(np.mean(partner_widths)), 3)
                               if partner_widths else None),
        "focal_events_graded": int(len(focal_rows)),
        "events_on_the_register": int(len(reach)),
        "per_event": reach,
    }
    if focal_rows:
        f = max(r["focal_record_reach"] for r in focal_rows)
        # **Two readings of focal isolation, and the difference is a recommendation.** Section 10 tells
        # a practitioner to measure back-dating on the focal group's own record. Read that way the
        # instrument sees the focal group's convention and nothing else, which is `f` below. Applied the
        # way the pipeline applies it -- to every group's own record, over every event on the register
        # -- it sees every convention the corpus contains, which is `f_all`. Under one convention the
        # two coincide. Under mixed conventions they do not, and the second is the one to use.
        f_all = max(r["focal_record_reach"] for r in reach)
        cz = max(r["co_backdated_reach"] for r in focal_rows)
        amb = max(r["off_focal_reach"] for r in focal_rows)
        neg = [x for r in focal_rows for x in r["off_focal_reach_negatives"]]
        meta["co_backdating"].update({
            "focal_record_horizon": int(f + 1),
            "focal_record_horizon_every_register": int(f_all + 1),
            "co_backdated_horizon": int(cz + 1),
            "administrative_horizon": int(max(f, cz) + 1),
            "ambient_off_focal_horizon": int(amb + 1),
            "share_of_events_with_a_caused_off_focal_trace": round(
                float(np.mean([r["co_backdated_reach"] > 0 for r in focal_rows])), 4),
            "share_where_the_caused_trace_exceeds_the_focal_record": round(
                float(np.mean([r["co_backdated_reach"] > r["focal_record_reach"]
                               for r in focal_rows])), 4),
            "ambient_mean_reach_positives": round(
                float(np.mean([r["off_focal_reach"] for r in focal_rows])), 4),
            "ambient_mean_reach_negatives": round(
                float(np.mean(neg)) if neg else float("nan"), 4),
            "ambient_share_positives": round(
                float(np.mean([r["off_focal_reach"] > 0 for r in focal_rows])), 4),
            "ambient_share_negatives": round(
                float(np.mean([x > 0 for x in neg])) if neg else float("nan"), 4),
        })
    return edges, events, membership, groups, meta, membership_recorded

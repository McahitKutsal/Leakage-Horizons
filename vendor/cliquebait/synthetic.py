"""
WS3 — synthetic testbed with a known leakage coefficient alpha.

Because alpha is known, this is the only setting where the diagnostics can be *calibrated*
rather than merely computed, which is why the manifesto puts the methodological weight here.

Generative story
----------------
Each node has a latent position z_i. Group labels come from LATENT cohesion, never from any
observed relation:

    y(S) = 1  iff  S is a latent-cohesive set (a latent-space neighbourhood)

so a positive group is genuinely learnable from node features and from relations that reflect
latent similarity. Leakage is then injected into one privileged relation r*:

    alpha = 0 : r* is generated purely from latent similarity, exactly like the other
                relations. It carries real signal but no privileged information about labels.
    alpha = 1 : every edge of r* comes from the dyads induced by positive groups. Positive
                groups are cliques in r*; the task collapses to clique detection.

Design requirement: **r*'s expected density is held constant across alpha.** If density rose
with alpha, every diagnostic would move with alpha for a reason that has nothing to do with
leakage, and the calibration would be worthless. The generator therefore allocates a fixed
edge budget between group-induced dyads and latent-similarity dyads according to alpha,
rather than adding group edges on top of a fixed background. `verify_density_invariance()`
checks this held.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

__all__ = ["SyntheticConfig", "generate", "verify_density_invariance"]


@dataclass
class SyntheticConfig:
    n_nodes: int = 200
    n_times: int = 20
    latent_dim: int = 8
    n_features: int = 10
    feature_noise: float = 0.35

    n_groups_per_time: int = 12          # positive groups drawn per time step
    group_size_min: int = 4
    group_size_max: int = 20
    cohesion_quantile: float = 0.25      # a group is "cohesive" if its mean pairwise latent
                                         # distance is under this quantile of random subsets

    n_latent_relations: int = 2          # relations reflecting latent similarity
    include_noise_relation: bool = True  # a relation with no signal at all
    # r*'s density must be low enough that the dyads induced by positive groups can fill the
    # whole budget at alpha = 1; otherwise nominal alpha saturates below 1 and the top of the
    # sweep is not the regime it claims to be. `generate` reports the realised share and
    # warns when it falls short of alpha.
    density_rstar: float = 0.035
    density_other: float = 0.06
    density_noise: float = 0.06

    negatives_per_positive: int = 3
    negative_budget: int = 2             # members swapped to build a hard negative
    random_negative_frac: float = 0.34   # share of negatives that are unconstrained subsets

    latent_drift: float = 0.05           # per-step drift of latent positions
    seed: int = 0


def _pairwise_dist(Z):
    d2 = ((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(d2, np.inf)
    return np.sqrt(d2)


def _sample_dyads_by_weight(pairs, weights, n, rng):
    """Sample n distinct dyads without replacement, proportional to weights."""
    n = min(n, len(pairs))
    if n <= 0:
        return []
    w = np.asarray(weights, dtype=float)
    w = np.clip(w, 1e-12, None)
    # Gumbel top-k: weighted sampling without replacement in one pass
    keys = np.log(w) + rng.gumbel(size=len(w))
    idx = np.argpartition(-keys, n - 1)[:n]
    return [pairs[i] for i in idx]


def generate(alpha: float, cfg: SyntheticConfig | None = None):
    """Build one synthetic benchmark at leakage coefficient `alpha`.

    Returns (edges, groups, universe) in the format `LeakageAudit` consumes, plus a `meta`
    dict recording realised densities so the invariance can be audited.
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    cfg = cfg or SyntheticConfig()
    rng = np.random.default_rng(cfg.seed)

    Z0 = rng.normal(size=(cfg.n_nodes, cfg.latent_dim))
    W = rng.normal(size=(cfg.latent_dim, cfg.n_features))

    all_pairs = list(combinations(range(cfg.n_nodes), 2))
    pair_pos = {p: i for i, p in enumerate(all_pairs)}
    n_pairs = len(all_pairs)

    rel_names = ["r_star"] + [f"r_latent_{i+1}" for i in range(cfg.n_latent_relations)]
    if cfg.include_noise_relation:
        rel_names.append("r_noise")

    edge_rows, group_rows, feat_rows = [], [], []
    universe = {}
    meta = {"alpha": alpha, "realised_density": {r: [] for r in rel_names},
            "rstar_edges_from_groups": [], "rstar_edges_total": []}

    Z = Z0.copy()
    for t in range(cfg.n_times):
        Z = Z + cfg.latent_drift * rng.normal(size=Z.shape)
        D = _pairwise_dist(Z)
        universe[t] = list(range(cfg.n_nodes))

        X = Z @ W + cfg.feature_noise * rng.normal(size=(cfg.n_nodes, cfg.n_features))
        for i in range(cfg.n_nodes):
            feat_rows.append({"time": t, "node": i,
                              **{f"x{j}": X[i, j] for j in range(cfg.n_features)}})

        # ---- latent-cohesive positive groups (labels depend on Z only) ----
        dvals = D[np.triu_indices(cfg.n_nodes, 1)]
        thresh = np.quantile(dvals, cfg.cohesion_quantile)
        positives = []
        for _ in range(cfg.n_groups_per_time):
            k = int(rng.integers(cfg.group_size_min, cfg.group_size_max + 1))
            seed_node = int(rng.integers(cfg.n_nodes))
            order = np.argsort(D[seed_node])
            members = [seed_node] + [int(v) for v in order[:k - 1]]
            members = sorted(set(members))
            if len(members) < cfg.group_size_min:
                continue
            md = np.mean([D[u, v] for u, v in combinations(members, 2)])
            if md <= thresh:                      # cohesive under the latent process
                positives.append(tuple(members))
        positives = list(dict.fromkeys(positives))

        induced = set()
        for S in positives:
            for u, v in combinations(S, 2):
                induced.add((u, v))
        induced = sorted(induced)

        # ---- relations ----
        sim_w = np.array([1.0 / (1e-6 + D[u, v] ** 2) for u, v in all_pairs])

        for rel in rel_names:
            if rel == "r_star":
                budget = int(round(cfg.density_rstar * n_pairs))
                n_grp = int(round(alpha * budget))
                n_grp = min(n_grp, len(induced))
                grp_edges = ([induced[i] for i in
                              rng.choice(len(induced), size=n_grp, replace=False)]
                             if n_grp else [])
                taken = set(grp_edges)
                rest_idx = [i for i, p in enumerate(all_pairs) if p not in taken]
                rest_pairs = [all_pairs[i] for i in rest_idx]
                rest_w = sim_w[rest_idx]
                bg = _sample_dyads_by_weight(rest_pairs, rest_w, budget - len(grp_edges), rng)
                edges = list(grp_edges) + list(bg)
                meta["rstar_edges_from_groups"].append(len(grp_edges))
                meta["rstar_edges_total"].append(len(edges))
            elif rel == "r_noise":
                budget = int(round(cfg.density_noise * n_pairs))
                sel = rng.choice(n_pairs, size=budget, replace=False)
                edges = [all_pairs[i] for i in sel]
            else:
                budget = int(round(cfg.density_other * n_pairs))
                edges = _sample_dyads_by_weight(all_pairs, sim_w, budget, rng)

            meta["realised_density"][rel].append(len(edges) / n_pairs)
            for u, v in edges:
                edge_rows.append({"relation": rel, "time": t, "u": u, "v": v})

        # ---- groups: positives plus perturbed and random negatives ----
        for S in positives:
            group_rows.append({"members": list(S), "label": 1, "time": t,
                               "group_id": f"t{t}_g{hash(S) % 10**6}", "neg_type": ""})
            n_hard = int(round(cfg.negatives_per_positive * (1 - cfg.random_negative_frac)))
            n_rand = cfg.negatives_per_positive - n_hard
            pool = [x for x in range(cfg.n_nodes) if x not in set(S)]
            for _ in range(n_hard):
                b = min(cfg.negative_budget, len(S) - 2)
                if b < 1:
                    continue
                drop = set(rng.choice(len(S), size=b, replace=False).tolist())
                add = rng.choice(len(pool), size=b, replace=False)
                new = [m for i, m in enumerate(S) if i not in drop]
                new += [pool[i] for i in add]
                group_rows.append({"members": sorted(new), "label": 0, "time": t,
                                   "group_id": f"t{t}_hard", "neg_type": "hard"})
            for _ in range(n_rand):
                new = rng.choice(cfg.n_nodes, size=len(S), replace=False)
                group_rows.append({"members": sorted(int(x) for x in new), "label": 0,
                                   "time": t, "group_id": f"t{t}_rand",
                                   "neg_type": "random"})

    edges = pd.DataFrame(edge_rows)
    groups = pd.DataFrame(group_rows)
    features = pd.DataFrame(feat_rows)
    meta["n_positives"] = int((groups.label == 1).sum())
    meta["n_negatives"] = int((groups.label == 0).sum())
    meta["alpha_realised"] = (
        float(np.mean(np.array(meta["rstar_edges_from_groups"])
                      / np.maximum(np.array(meta["rstar_edges_total"]), 1))))
    meta["mean_rstar_group_share"] = meta["alpha_realised"]
    shortfall = alpha - meta["alpha_realised"]
    meta["alpha_shortfall"] = float(shortfall)
    if shortfall > 0.02:
        import warnings
        warnings.warn(
            f"nominal alpha={alpha:.2f} but only {meta['alpha_realised']:.2f} realised: the "
            f"dyads induced by positive groups cannot fill r*'s edge budget. Lower "
            f"density_rstar or raise n_groups_per_time, otherwise the top of the sweep is "
            f"not the regime it claims to be.", RuntimeWarning, stacklevel=2)
    return edges, groups, features, universe, meta


def verify_density_invariance(alphas, cfg: SyntheticConfig | None = None) -> pd.DataFrame:
    """Confirm r*'s density does not move with alpha -- the calibration depends on it."""
    rows = []
    for a in alphas:
        _e, _g, _f, _u, meta = generate(a, cfg)
        rows.append({"alpha": a,
                     "density_rstar": float(np.mean(meta["realised_density"]["r_star"])),
                     "density_latent_1": float(np.mean(meta["realised_density"]["r_latent_1"])),
                     "alpha_realised": meta["alpha_realised"],
                     "shortfall": meta["alpha_shortfall"],
                     "n_pos": meta["n_positives"], "n_neg": meta["n_negatives"]})
    return pd.DataFrame(rows)

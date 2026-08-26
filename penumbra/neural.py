"""§7's ladder, rungs 4-7: the capacity-matched control and the encoders that must beat it.

    4  graph-free MLP at matched depth, width and readout  -- message passing removed, nothing else
    5  homogeneous encoder (GraphSAGE)
    6  heterogeneous encoder (RGCN)
    7  temporal encoder over $G_{\\leq t}$ rather than $G_t$ alone

§7 calls rung 7 "the only architectural novelty this programme is entitled to propose", and
PROTOCOL §5 makes the control **capacity-matched** rather than a differently-shaped weak baseline:
against the audited paper's DeepSets (0.906) and MLP (0.901) the graph looked worth 0.05-0.09;
against a matched control (0.970) it was worth 0.023. Every encoder here therefore shares the head,
the hidden width, the embedding width and the depth, and differs in exactly one respect.

Why this can be trained as binary classification. T1's accessions are all **exactly dated**, so the
interval-censored likelihood reduces to pooled binary regression over dyad-periods -- the reduction
§7 asserts and `scripts/test_hazard.py` verifies to 2.8e-14. The neural rungs are therefore fitted
on the same estimand as rungs 1-3 rather than on a separate objective, which is what makes the
ladder a ladder.

The graph is small -- at most 202 states and about 14k co-membership edges in a year -- so one
encoder pass per year covers every dyad in it. The cost is entirely in the head over 2.2M
dyad-years, which is what the GPU is for.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "graph"
NODES = (ROOT.parent / "CLIQUEBAIT" / "previous-work-code-base" / "coalition-gnn"
         / "data" / "canonical" / "nodes.parquet")

NODE_COLS = ["cinc", "polity2", "v2x_polyarchy", "v2x_libdem", "v2x_partipdem",
             "log_e_gdppc", "log_e_pop", "log_tpop", "log_milex", "log_milper"]
RELATIONS = ["igo_comembership", "allies", "trades", "votes_with", "conflicts_with"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ----------------------------------------------------------------------- snapshots
def build_snapshots(regime=(1965, 2014)) -> dict:
    """One graph per year over a fixed state index, with node covariates.

    A fixed index across years matters: an encoder that saw a different node ordering each year
    would be learning the ordering. States absent in a year keep their row, carry mean-imputed
    covariates and an absence flag, and hold no edges.
    """
    lo, hi = regime
    # **The relations are named, not globbed.** This read `GRAPH.glob("edges_*.parquet")`, so when
    # `validate_delta_star_desta.py` wrote `edges_pta_signature.parquet` and `edges_pta_force.parquet`
    # into the same directory for V10, they were silently pulled in. `RELATIONS` has five entries, so
    # `relation.map(rel_ix)` returned NaN for the PTA rows, `np.stack` cast NaN into an int64 edge-type
    # tensor, and RGCNConv died on a device-side CUDA assert -- an error with no visible connection to
    # its cause, two indirections and a device boundary away. V9's P7 run predates those files, so the
    # glob was latently broken from the moment V10 was measured and nothing said so (D-38).
    missing = [r for r in RELATIONS if not (GRAPH / f"edges_{r}.parquet").exists()]
    if missing:
        raise FileNotFoundError(f"declared relations with no edge file: {missing}")
    edges = pd.concat([pd.read_parquet(GRAPH / f"edges_{r}.parquet").assign(relation=r)
                       for r in RELATIONS], ignore_index=True)
    edges = edges[edges.year.between(lo, hi)]
    nodes = pd.read_parquet(NODES)
    nodes = nodes[nodes.year.between(lo, hi)]

    codes = sorted(set(edges.cow_i) | set(edges.cow_j) | set(nodes.cow_code))
    idx = {int(c): i for i, c in enumerate(codes)}
    n = len(codes)

    X = nodes.pivot_table(index="year", columns="cow_code", values=NODE_COLS)
    mu = nodes[NODE_COLS].mean()
    sd = nodes[NODE_COLS].std().replace(0, 1.0)

    rel_ix = {r: i for i, r in enumerate(RELATIONS)}
    snaps = {}
    for year in range(lo, hi + 1):
        feats = np.zeros((n, len(NODE_COLS)), dtype=np.float32)
        present = np.zeros((n, 1), dtype=np.float32)
        sub = nodes[nodes.year == year]
        for r in sub.itertuples():
            i = idx.get(int(r.cow_code))
            if i is None:
                continue
            present[i, 0] = 1.0
            for k, c in enumerate(NODE_COLS):
                v = getattr(r, c)
                feats[i, k] = 0.0 if pd.isna(v) else (v - mu[c]) / sd[c]
        e = edges[edges.year == year]
        if len(e):
            ui = e.cow_i.map(idx).to_numpy()
            vi = e.cow_j.map(idx).to_numpy()
            et = e.relation.map(rel_ix).to_numpy()
            # Refuse an unmapped endpoint or relation instead of casting NaN to int64. The cast is what
            # turned a naming mismatch into a CUDA assert, and a NaN in an index array is the one kind
            # of bad value that produces no error at the point it is created (D-38).
            for arr, what in ((ui, "cow_i"), (vi, "cow_j"), (et, "relation")):
                bad = pd.isna(arr).sum()
                if bad:
                    raise ValueError(f"{year}: {bad} edge rows with an unmapped {what}")
            ui, vi, et = ui.astype(np.int64), vi.astype(np.int64), et.astype(np.int64)
            ei = np.concatenate([np.stack([ui, vi]), np.stack([vi, ui])], axis=1)
            et = np.concatenate([et, et])
        else:
            ei = np.zeros((2, 0), dtype=np.int64)
            et = np.zeros(0, dtype=np.int64)
        snaps[year] = {
            "x": torch.tensor(np.hstack([feats, present]), device=DEVICE),
            "edge_index": torch.tensor(ei, dtype=torch.long, device=DEVICE),
            "edge_type": torch.tensor(et, dtype=torch.long, device=DEVICE),
        }
    return {"snaps": snaps, "index": idx, "n_nodes": n,
            "n_features": len(NODE_COLS) + 1, "n_relations": len(RELATIONS)}


# ------------------------------------------------------------------------ encoders
class MLPEnc(nn.Module):
    """Rung 4. Identical depth, width and normalisation to the graph encoders, no message passing.

    This is the control PROTOCOL §5 requires: it differs from rungs 5-7 in exactly one respect, so
    the difference measures message passing rather than architecture shape.
    """

    def __init__(self, fin, hid, out, dropout=0.2):
        super().__init__()
        self.l1, self.l2 = nn.Linear(fin, hid), nn.Linear(hid, out)
        self.n1, self.n2 = nn.LayerNorm(hid), nn.LayerNorm(out)
        self.d = dropout

    def forward(self, s):
        h = F.dropout(F.relu(self.n1(self.l1(s["x"]))), p=self.d, training=self.training)
        return self.n2(self.l2(h))


class SAGEEnc(nn.Module):
    """Rung 5, homogeneous: relations collapsed to one edge set."""

    def __init__(self, fin, hid, out, dropout=0.2):
        super().__init__()
        from torch_geometric.nn import SAGEConv
        self.c1, self.c2 = SAGEConv(fin, hid), SAGEConv(hid, out)
        self.n1, self.n2 = nn.LayerNorm(hid), nn.LayerNorm(out)
        self.d = dropout

    def forward(self, s):
        h = F.dropout(F.relu(self.n1(self.c1(s["x"], s["edge_index"]))), p=self.d,
                      training=self.training)
        return self.n2(self.c2(h, s["edge_index"]))


class RGCNEnc(nn.Module):
    """Rung 6, heterogeneous: relation-specific weights.

    CLIQUEBAIT's H2 found the heterogeneous advantage reverses under target-relation exclusion
    (+0.0129 to -0.0127 under rich pooling), so this rung is at genuine risk and is expected to be.
    """

    def __init__(self, fin, hid, out, nrel, dropout=0.2):
        super().__init__()
        from torch_geometric.nn import RGCNConv
        self.c1, self.c2 = RGCNConv(fin, hid, nrel), RGCNConv(hid, out, nrel)
        self.n1, self.n2 = nn.LayerNorm(hid), nn.LayerNorm(out)
        self.d = dropout

    def forward(self, s):
        h = self.c1(s["x"], s["edge_index"], s["edge_type"])
        h = F.dropout(F.relu(self.n1(h)), p=self.d, training=self.training)
        return self.n2(self.c2(h, s["edge_index"], s["edge_type"]))


class TemporalEnc(nn.Module):
    """Rung 7, over $G_{\\leq t}$: a GRU across the current and previous `lag` snapshots.

    §7 calls this the only architectural novelty the programme is entitled to propose, and commits
    in advance to reporting a negative result if it does not beat the static encoder. Capacity is
    matched by giving the static rungs the same hidden and embedding widths; the GRU adds
    parameters, which is stated rather than hidden -- a temporal encoder that wins only by being
    larger has not shown that history matters.
    """

    def __init__(self, fin, hid, out, nrel, lag=3, dropout=0.2):
        super().__init__()
        self.base = RGCNEnc(fin, hid, out, nrel, dropout)
        self.gru = nn.GRU(out, out, batch_first=True)
        self.norm = nn.LayerNorm(out)
        self.lag = lag

    def forward(self, s, history=None):
        cur = self.base(s)
        if not history:
            return cur
        seq = torch.stack([self.base(h) for h in history] + [cur], dim=1)
        out, _ = self.gru(seq)
        return self.norm(out[:, -1])


# ---------------------------------------------------------------------------- head
class AccessionHead(nn.Module):
    """Rich pooling of the coalition, concatenated with the candidate. Shared by every rung.

    Pooling is mean/std/max/min per CLIQUEBAIT, whose H3 found the pooling gain real but *not*
    leakage-mediated once measured on a headroom-normalised scale. Using the same head everywhere is
    what makes the rung differences attributable to the encoder.
    """

    def __init__(self, embed, extra=2, hidden=128, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4 * embed + embed + extra, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden // 2), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden // 2, 1))

    def forward(self, z, member_flat, member_batch, n_members, cand_idx, extra):
        from torch_geometric.utils import scatter
        zm = z[member_flat]
        B = n_members.shape[0]
        mean = scatter(zm, member_batch, dim=0, dim_size=B, reduce="mean")
        msq = scatter(zm * zm, member_batch, dim=0, dim_size=B, reduce="mean")
        kf = n_members.float().clamp(min=1).unsqueeze(1)
        corr = torch.where(kf > 1, kf / (kf - 1), torch.zeros_like(kf))
        std = ((msq - mean * mean) * corr).clamp(min=0).add(1e-6).sqrt()
        mx = scatter(zm, member_batch, dim=0, dim_size=B, reduce="max")
        mn = scatter(zm, member_batch, dim=0, dim_size=B, reduce="min")
        return self.net(torch.cat([mean, std, mx, mn, z[cand_idx], extra], dim=1)).squeeze(1)


def make_model(rung: int, meta: dict, hidden=64, embed=64, lag=3):
    fin, nrel = meta["n_features"], meta["n_relations"]
    if rung == 4:
        enc = MLPEnc(fin, hidden, embed)
    elif rung == 5:
        enc = SAGEEnc(fin, hidden, embed)
    elif rung == 6:
        enc = RGCNEnc(fin, hidden, embed, nrel)
    elif rung == 7:
        enc = TemporalEnc(fin, hidden, embed, nrel, lag=lag)
    else:
        raise ValueError(f"rung {rung} is not a neural rung")
    return nn.ModuleDict({"enc": enc, "head": AccessionHead(embed)}).to(DEVICE)


def n_parameters(model) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

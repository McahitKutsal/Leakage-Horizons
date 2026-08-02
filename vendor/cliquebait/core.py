"""
Local reproduction of the previous work's model, plus relation masking for D2.

Mirrors 10_revision_experiments.ipynb (the notebook that produced the published revision
numbers): year-batched trainer, vectorised rich pooling, one optimiser step per training
year. The headline configuration there is

    GraphModel(encoder='rgcn', nrel=4, pooling='rich', use_bilinear=True, use_multitask=True)
    train_model(..., staged=False)          # single Adam, lr 1e-3, weight_decay 1e-3
    seeds [42, 1, 2, 3, 4], 150 epochs, patience 25, random-15% val from <=2009

and it reports test ROC-AUC 0.957 +- 0.006. Reproducing that on the original snapshots is
the acceptance test for this module.

What is added here: `mask_relations` on the encode path, so a fitted model can be evaluated
with relation r* removed at inference time -- the D2 leakage gap.
"""
from __future__ import annotations

import random
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import (average_precision_score, precision_recall_curve,
                             roc_auc_score)
from torch_geometric.nn import RGCNConv, SAGEConv, GATConv
from torch_geometric.utils import scatter

ROOT = Path(__file__).resolve().parents[1]
PREV = ROOT / "previous-work-code-base" / "coalition-gnn" / "data"

EDGE_TYPES = ["allies", "trades", "votes_with", "conflicts_with"]
NUM_RELATIONS = len(EDGE_TYPES)
REL_INDEX = {r: i for i, r in enumerate(EDGE_TYPES)}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

POS_WEIGHT, LABEL_SMOOTH, WEIGHT_DECAY = 2.5, 0.1, 1e-3
LAMBDA_DUR = LAMBDA_COH = 0.3


def set_seed(s: int) -> None:
    torch.manual_seed(s)
    np.random.seed(s)
    random.seed(s)


# --------------------------------------------------------------------------- data
def load_snapshots(snap_dir: Path, start=1946, end=2016, device=DEVICE) -> dict:
    snaps = {}
    for year in range(start, end + 1):
        p = Path(snap_dir) / f"graph_{year}.pt"
        if not p.exists():
            continue
        d = torch.load(p, weights_only=False)
        x = d["country"].x
        cow = d["country"].cow_code.numpy()
        ei_list, et_list = [], []
        for ri, rn in enumerate(EDGE_TYPES):
            key = ("country", rn, "country")
            if key in d.edge_types:
                ei = d[key].edge_index
                ei_list.append(ei)
                et_list.append(torch.full((ei.shape[1],), ri, dtype=torch.long))
        if ei_list:
            ei, et = torch.cat(ei_list, 1), torch.cat(et_list)
        else:
            ei = torch.zeros((2, 0), dtype=torch.long)
            et = torch.zeros(0, dtype=torch.long)
        xm = d["country"].x_mask if "x_mask" in d["country"] else torch.ones_like(x)
        snaps[year] = {"x": x.to(device), "x_mask": xm.to(device),
                       "edge_index": ei.to(device), "edge_type": et.to(device),
                       "cow_codes": cow,
                       "code_to_idx": {int(c): i for i, c in enumerate(cow)},
                       "year": year}
    return snaps


def mask_relations(snap: dict, drop: list[str] | list[int]) -> dict:
    """Inference-time removal of one or more relations. Returns a view; no copy of x."""
    idx = {REL_INDEX[r] if isinstance(r, str) else int(r) for r in drop}
    if not idx:
        return snap
    keep = ~torch.isin(snap["edge_type"],
                       torch.tensor(sorted(idx), device=snap["edge_type"].device))
    return {**snap,
            "edge_index": snap["edge_index"][:, keep],
            "edge_type": snap["edge_type"][keep]}


def build_samples(df: pd.DataFrame, label: int, snaps: dict) -> list[dict]:
    out = []
    for r in df.itertuples():
        y = int(r.year)
        if y not in snaps:
            continue
        c2i = snaps[y]["code_to_idx"]
        valid = [m for m in (int(x) for x in r.members_str.split(",")) if m in c2i]
        if len(valid) < 2:
            continue
        out.append({"year": y, "members": valid,
                    "member_idx": [c2i[m] for m in valid], "label": label,
                    "coalition_id": getattr(r, "coalition_id",
                                            getattr(r, "source_coalition_id", "")),
                    "neg_type": getattr(r, "neg_type", None),
                    "type": getattr(r, "type", None),
                    "duration": float(getattr(r, "total_duration", 0) or 0) if label else 0.0,
                    "cohesion": float(getattr(r, "internal_vote_agreement", 0) or 0)
                    if label else 0.0})
    return out


def load_samples(snaps: dict, coal_dir: Path | None = None):
    coal_dir = Path(coal_dir) if coal_dir else PREV / "coalitions"
    pos = build_samples(pd.read_parquet(coal_dir / "positive_samples.parquet"), 1, snaps)
    neg = build_samples(pd.read_parquet(coal_dir / "negative_samples.parquet"), 0, snaps)
    return pos, neg


def make_splits(pos, neg, seed=42, val_frac=0.15, val_end=2009, test_years=None):
    """Temporal test, random val from the pre-test pool -- the previous work's protocol."""
    allr = pos + neg
    if test_years is None:
        test = [s for s in allr if s["year"] > val_end]
    else:
        test = [s for s in allr if s["year"] in set(test_years)]
    pre = [s for s in allr if s["year"] <= val_end]
    rng = np.random.default_rng(seed)
    idx = np.arange(len(pre))
    rng.shuffle(idx)
    vs = set(idx[:int(val_frac * len(pre))].tolist())
    train = [pre[i] for i in range(len(pre)) if i not in vs]
    val = [pre[i] for i in range(len(pre)) if i in vs]
    return train, val, test


# -------------------------------------------------------------------------- model
class RGCNEncoder(nn.Module):
    def __init__(self, fin, h, out, nrel, dropout=0.3):
        super().__init__()
        self.conv1, self.conv2 = RGCNConv(fin, h, nrel), RGCNConv(h, out, nrel)
        self.norm1, self.norm2 = nn.LayerNorm(h), nn.LayerNorm(out)
        self.d = dropout

    def forward(self, snap):
        h = self.conv1(snap["x"], snap["edge_index"], snap["edge_type"])
        h = F.dropout(F.relu(self.norm1(h)), p=self.d, training=self.training)
        return self.norm2(self.conv2(h, snap["edge_index"], snap["edge_type"]))


class SAGEEnc(nn.Module):
    def __init__(self, fin, h, out, dropout=0.3):
        super().__init__()
        self.c1, self.c2 = SAGEConv(fin, h), SAGEConv(h, out)
        self.n1, self.n2 = nn.LayerNorm(h), nn.LayerNorm(out)
        self.d = dropout

    def forward(self, snap):
        h = self.c1(snap["x"], snap["edge_index"])
        h = F.dropout(F.relu(self.n1(h)), p=self.d, training=self.training)
        return self.n2(self.c2(h, snap["edge_index"]))


class GATEnc(nn.Module):
    def __init__(self, fin, h, out, heads=4, dropout=0.3):
        super().__init__()
        self.c1 = GATConv(fin, h // heads, heads=heads, dropout=dropout)
        self.c2 = GATConv(h, out, heads=1, dropout=dropout)
        self.n1, self.n2 = nn.LayerNorm(h), nn.LayerNorm(out)
        self.d = dropout

    def forward(self, snap):
        h = self.c1(snap["x"], snap["edge_index"])
        h = F.dropout(F.relu(self.n1(h)), p=self.d, training=self.training)
        return self.n2(self.c2(h, snap["edge_index"]))


class MLPEnc(nn.Module):
    """Graph-free control: identical depth, width and head, but no message passing.

    This is the right floor for "what does the graph contribute at all", because it differs
    from the graph encoders in exactly one respect. It is not the paper's DeepSets baseline
    (which uses its own phi/rho), so numbers are not directly comparable to that row.
    """

    def __init__(self, fin, h, out, dropout=0.3):
        super().__init__()
        self.l1, self.l2 = nn.Linear(fin, h), nn.Linear(h, out)
        self.n1, self.n2 = nn.LayerNorm(h), nn.LayerNorm(out)
        self.d = dropout

    def forward(self, snap):
        h = F.dropout(F.relu(self.n1(self.l1(snap["x"]))), p=self.d, training=self.training)
        return self.n2(self.l2(h))


class CoalitionHead(nn.Module):
    def __init__(self, embed_dim, raw_dim, pooling="rich", use_bilinear=True,
                 use_multitask=True, hidden=128, dropout=0.3):
        super().__init__()
        self.pooling, self.use_bilinear = pooling, use_bilinear
        self.use_multitask = use_multitask
        mult = 4 if pooling == "rich" else 1
        pool_dim = mult * (embed_dim + raw_dim) + 1 + (1 if use_bilinear else 0)
        self.W_pair = (nn.Parameter(torch.randn(embed_dim, embed_dim) * 0.01)
                       if use_bilinear else None)
        self.validity = nn.Sequential(
            nn.Linear(pool_dim, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden // 2), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden // 2, 1))
        if use_multitask:
            mt = mult * embed_dim + 1
            self.dur = nn.Sequential(nn.Linear(mt, hidden), nn.ReLU(),
                                     nn.Linear(hidden, 1), nn.Softplus())
            self.coh = nn.Sequential(nn.Linear(mt, hidden), nn.ReLU(),
                                     nn.Linear(hidden, 1), nn.Sigmoid())

    def forward_batch(self, z_all, raw_all, member_lists=None, flat=None, batch=None, ks=None):
        dev = z_all.device
        if flat is None:
            ks = torch.tensor([len(m) for m in member_lists], device=dev)
            flat = torch.cat([torch.as_tensor(m, dtype=torch.long, device=dev)
                              for m in member_lists])
            batch = torch.repeat_interleave(torch.arange(len(member_lists), device=dev), ks)
        B = ks.shape[0]
        zm, rawm = z_all[flat], raw_all[flat]

        def pool(feat):
            mean = scatter(feat, batch, dim=0, dim_size=B, reduce="mean")
            if self.pooling == "mean":
                return mean
            msq = scatter(feat * feat, batch, dim=0, dim_size=B, reduce="mean")
            kf = ks.float().clamp(min=1).unsqueeze(1)
            corr = torch.where(kf > 1, kf / (kf - 1), torch.zeros_like(kf))
            std = ((msq - mean * mean) * corr).clamp(min=0).add(1e-6).sqrt()
            mx = scatter(feat, batch, dim=0, dim_size=B, reduce="max")
            mn = scatter(feat, batch, dim=0, dim_size=B, reduce="min")
            return torch.cat([mean, std, mx, mn], dim=1)

        zp, rp = pool(zm), pool(rawm)
        parts = [zp, rp, (ks.float() / 20.0).unsqueeze(1)]
        if self.use_bilinear:
            sumz = scatter(zm, batch, dim=0, dim_size=B, reduce="sum")
            full = (sumz @ self.W_pair * sumz).sum(1)
            diag = scatter((zm @ self.W_pair * zm).sum(1), batch, dim=0, dim_size=B, reduce="sum")
            denom = (ks * (ks - 1)).float().clamp(min=1)
            parts.append(torch.where(ks >= 2, (full - diag) / denom,
                                     torch.zeros_like(full)).unsqueeze(1))
        v = self.validity(torch.cat(parts, dim=1)).squeeze(1)
        dur = coh = None
        if self.use_multitask:
            mt = torch.cat([zp, (ks.float() / 20.0).unsqueeze(1)], dim=1)
            dur, coh = self.dur(mt).squeeze(1), self.coh(mt).squeeze(1)
        return v, dur, coh


class GraphModel(nn.Module):
    def __init__(self, num_features, encoder="rgcn", nrel=NUM_RELATIONS, pooling="rich",
                 use_bilinear=True, use_multitask=True, hidden=128, embed=128, dropout=0.3):
        super().__init__()
        if encoder == "rgcn":
            self.encoder = RGCNEncoder(num_features, hidden, embed, nrel, dropout)
        elif encoder == "sage":
            self.encoder = SAGEEnc(num_features, hidden, embed, dropout)
        elif encoder == "gat":
            self.encoder = GATEnc(num_features, hidden, embed, dropout=dropout)
        elif encoder == "mlp":
            self.encoder = MLPEnc(num_features, hidden, embed, dropout)
        else:
            raise ValueError(encoder)
        self.encoder_kind = encoder
        self.uses_graph = encoder != "mlp"
        self.head = CoalitionHead(embed, num_features, pooling, use_bilinear,
                                  use_multitask, hidden, dropout)

    def encode(self, snap):
        return self.encoder(snap)


# ------------------------------------------------------------------------ training
def _metrics(probs, labels):
    if len(np.unique(labels)) < 2:
        return np.nan, np.nan, np.nan
    p, r, _ = precision_recall_curve(labels, probs)
    return (roc_auc_score(labels, probs), average_precision_score(labels, probs),
            float((2 * p * r / (p + r + 1e-10)).max()))


def _precompute_year(samples):
    by = defaultdict(list)
    for s in samples:
        by[s["year"]].append(s)
    pre = {}
    for y, grp in by.items():
        ks = torch.tensor([len(s["member_idx"]) for s in grp], device=DEVICE)
        flat = torch.cat([torch.tensor(s["member_idx"], dtype=torch.long, device=DEVICE)
                          for s in grp])
        batch = torch.repeat_interleave(torch.arange(len(grp), device=DEVICE), ks)
        labs = torch.tensor([float(s["label"]) for s in grp], device=DEVICE)
        posmask = labs > 0.5
        dtgt = torch.tensor([np.log1p(s["duration"]) for s in grp],
                            device=DEVICE, dtype=torch.float32)
        cohv = torch.tensor([s["cohesion"] for s in grp], device=DEVICE, dtype=torch.float32)
        pre[y] = {"grp": grp, "ks": ks, "flat": flat, "batch": batch, "labs": labs,
                  "posmask": posmask, "dtgt": dtgt, "cohv": cohv,
                  "cohmask": posmask & (cohv > 0)}
    return pre


@torch.no_grad()
def evaluate(model, samples, snaps, drop_relations=None):
    """drop_relations: list of relation names removed at INFERENCE only -- this is D2."""
    model.eval()
    logits = [None] * len(samples)
    labels = np.array([s["label"] for s in samples])
    by = defaultdict(list)
    for i, s in enumerate(samples):
        by[s["year"]].append((i, s))
    for y, items in by.items():
        snap = mask_relations(snaps[y], drop_relations) if drop_relations else snaps[y]
        z = model.encode(snap)
        v, _, _ = model.head.forward_batch(
            z, snap["x"], member_lists=[s["member_idx"] for _, s in items])
        for (i, _), val in zip(items, v):
            logits[i] = val.item()
    probs = 1 / (1 + np.exp(-np.array(logits)))
    auc, pr, f1 = _metrics(probs, labels)
    return {"AUC": auc, "PR_AUC": pr, "F1": f1}, probs, labels


def train_model(model, train, val, snaps, seed=42, staged=False, epochs=150,
                patience=25, lr=1e-3, enc_lr=1e-4, verbose=False):
    set_seed(seed)
    model.to(DEVICE)
    if staged:
        opt = torch.optim.Adam([{"params": model.encoder.parameters(), "lr": enc_lr},
                                {"params": model.head.parameters(), "lr": lr}],
                               weight_decay=WEIGHT_DECAY)
    else:
        opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    pw = torch.tensor(POS_WEIGHT, device=DEVICE)
    pre = _precompute_year(train)
    years = list(pre.keys())
    best_auc, best_state, patc = -1.0, None, 0

    for ep in range(epochs):
        model.train()
        random.shuffle(years)
        for y in years:
            p = pre[y]
            opt.zero_grad()
            z = model.encode(snaps[y])
            v, dur, coh = model.head.forward_batch(z, snaps[y]["x"], flat=p["flat"],
                                                   batch=p["batch"], ks=p["ks"])
            tgt = p["labs"] * (1 - LABEL_SMOOTH) + 0.5 * LABEL_SMOOTH
            w = torch.where(p["labs"] > 0.5, pw, torch.ones_like(p["labs"]))
            loss = F.binary_cross_entropy_with_logits(v, tgt, weight=w)
            if dur is not None and p["posmask"].any():
                loss = loss + LAMBDA_DUR * F.mse_loss(dur[p["posmask"]], p["dtgt"][p["posmask"]])
                if p["cohmask"].any():
                    loss = loss + LAMBDA_COH * F.mse_loss(coh[p["cohmask"]], p["cohv"][p["cohmask"]])
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        sch.step()
        vm, _, _ = evaluate(model, val, snaps)
        if vm["AUC"] is not None and vm["AUC"] > best_auc:
            best_auc, patc = vm["AUC"], 0
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            patc += 1
        if verbose and ep % 10 == 0:
            print(f"    ep{ep:3d} valAUC={vm['AUC']:.4f}")
        if patc >= patience:
            break
    if best_state:
        model.load_state_dict(best_state)
    return model, best_auc


def mean_std(xs):
    a = np.array([x for x in xs if x is not None and not np.isnan(x)], dtype=float)
    if not len(a):
        return {"mean": None, "std": None, "n": 0}
    return {"mean": round(float(a.mean()), 4), "std": round(float(a.std()), 4),
            "n": int(len(a)), "vals": [round(float(v), 4) for v in a]}

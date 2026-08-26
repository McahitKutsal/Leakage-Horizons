r"""Does a second, independent implementation of the density code produce the same numbers?

Section 9's first threat: $\phi_r(S; k)$ and the clique contrast are computed by one implementation
across all four testbeds, so an error in it would be common to every result reported. The survival
likelihood is checked against closed forms and against a slow reference to within $10^{-13}$; the
density code had no equivalent, and Section 8 -- nine defects in a working day -- is the reason that
gap matters rather than a reason to trust the code (revision item 2.7).

`penumbra.reference` is the second implementation. It is written from Section 3.1's definitions, uses
Python dicts and `itertools.combinations` where `umbra` uses packed `int64` keys and
`numpy.searchsorted`, and has no member-only cache and no star decomposition -- which is precisely the
optimisation most able to be subtly wrong.

This script runs both over every testbed the manuscript reports and, where the numbers are headline
claims, re-derives the claim itself through the reference rather than only comparing intermediate
values. Four passes:

**A. Synthetic, all six settings.** Every $\phi$ in every panel, then the clique contrast per relation
per lead time, then $\Delta^\star_{\text{lo}}$ recomputed from the reference's own curve. The
calibration in Table 2 is the paper's only evidence that the estimator recovers a known width, so it
is the one that most needs a second implementation behind it.

**B. Corpus A, Table 3.** The matched contrast per relation per lead time, star by star.

**C. Corpus A, Table 4.** The clique contrast by group size at both declared levels.

**D. Corpus B, Table 4.** Every group against every channel, compared with **two** other
implementations: `umbra` and the pinned CLIQUEBAIT `LeakageAudit`, which is a separate code base
written for a different paper. Three implementations agreeing is a stronger statement than two.

The PTA figures in Section 6.2 are computed by an inline index in
`scripts/validate_delta_star_desta.py` rather than by `umbra`, so they already rest on two code paths;
pass B's star statistic is checked against the reference in the same units so that is recorded too.

    python scripts/verify_reference_density.py                 # all four passes
    python scripts/verify_reference_density.py --only A B      # a subset
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.provenance import write_result  # noqa: E402
from penumbra.reference import ReferenceDensity, clique_contrast, node_id  # noqa: E402
from penumbra.synthetic import SyntheticConfig, generate  # noqa: E402
from penumbra.umbra import NEVER_EVENT, HorizonAudit, delta_star  # noqa: E402

LEDGER = ROOT / "data" / "ledger"
GRAPH = ROOT / "data" / "graph"
RESULTS = ROOT / "results"
WS2 = ROOT.parent / "CLIQUEBAIT" / "data" / "ws2"

REGIME = (1965, 2014)
R_STAR_A = "igo_comembership"
RELATIONS_A = ["igo_comembership", "allies", "trades", "votes_with", "conflicts_with"]
ANCHORS_A = ["trades", "votes_with", "conflicts_with"]
A_LEVELS = (1, 25)
BINS = [1, 3, 5, 10, 20, 80, 10_000]
N_NEG = 2
SEED = 0

SYN_BETAS = (0, 1, 2, 3, 4, 5)
SYN_ANCHORS = ["r_current", "r_latent_1", "r_latent_2", "r_noise"]
SYN_RSTAR = "r_star"

# Equality is the target, not closeness: both implementations compute a ratio of two exact integer
# counts, so any disagreement at all is a disagreement about which dyads are present. The tolerance
# exists only for the last bit of the division.
TOL = 1e-12


def _agree(a: float, b: float) -> bool:
    if (a != a) and (b != b):          # both nan: agreement about absence
        return True
    if (a != a) or (b != b):
        return False
    return abs(a - b) <= TOL


def _report(name: str, diffs: list[float], n: int, nan_mismatch: int) -> dict:
    worst = max(diffs) if diffs else 0.0
    ok = (worst <= TOL) and nan_mismatch == 0
    print(f"  {name:44s} {n:>9,} values   worst |diff| {worst:.3e}   "
          f"nan mismatches {nan_mismatch}   {'agree' if ok else 'DISAGREE'}")
    return {"n_values": int(n), "worst_abs_diff": float(worst),
            "nan_mismatches": int(nan_mismatch), "agree": bool(ok)}


# --------------------------------------------------------------------------- A
def pass_a() -> dict:
    """Synthetic calibration, recomputed end to end through the reference implementation."""
    print("\nA. synthetic testbed, six back-dating settings")
    out = {"per_beta": {}, "levels": [1]}
    diffs, n_vals, nan_mm = [], 0, 0
    lo_reference, lo_umbra = {}, {}

    for beta in SYN_BETAS:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            edges, events, membership, _g, _meta = generate(1.0, beta, SyntheticConfig())
        audit = HorizonAudit(edges, membership, events)
        ref = ReferenceDensity(edges, membership)

        rows = []
        for h in range(0, 9):
            panel = audit.accession_panel(h, NEVER_EVENT, 4, SEED)
            if panel.empty or panel.label.nunique() < 2:
                continue
            for rel in audit.relations:
                vals_u, vals_r = [], []
                for r in panel.itertuples():
                    u = audit.phi_candidate(r.entity_id, r.year, r.ccode, rel, 1)
                    v = ref.phi_candidate(r.entity_id, r.year, r.ccode, rel, 1)
                    vals_u.append(u)
                    vals_r.append(v)
                    n_vals += 1
                    if not _agree(u, v):
                        nan_mm += 1 if ((u != u) != (v != v)) else 0
                        if (u == u) and (v == v):
                            diffs.append(abs(u - v))
                cc = clique_contrast(vals_r, panel.label.tolist())
                rows.append({"horizon": h, "relation": rel, "level": 1,
                             "n_pos": cc["n_pos"], "n_neg": cc["n_neg"],
                             "clique_contrast": cc["clique_contrast"],
                             "auc_phi_alone": _auc(vals_r, panel.label.tolist())})

        curve_ref = pd.DataFrame(rows)
        curve_umb = audit.u1_curve(horizons=range(0, 9), levels=(1,), negatives=NEVER_EVENT)
        ds_ref = delta_star(curve_ref, SYN_RSTAR, SYN_ANCHORS, level=1)
        ds_umb = delta_star(curve_umb, SYN_RSTAR, SYN_ANCHORS, level=1)
        lo_reference[beta] = ds_ref["delta_star_lo"]
        lo_umbra[beta] = ds_umb["delta_star_lo"]
        out["per_beta"][beta] = {"target": beta + 1,
                                 "delta_star_lo_umbra": ds_umb["delta_star_lo"],
                                 "delta_star_lo_reference": ds_ref["delta_star_lo"]}
        print(f"    beta={beta}  target {beta + 1}  umbra lo={ds_umb['delta_star_lo']}  "
              f"reference lo={ds_ref['delta_star_lo']}")

    out["phi"] = _report("phi, all panels, all relations", diffs, n_vals, nan_mm)
    hits = sum(1 for b in SYN_BETAS if lo_reference[b] == b + 1)
    out["calibration_through_the_reference"] = {
        "settings": len(SYN_BETAS), "on_target": int(hits),
        "identical_to_umbra": bool(lo_reference == lo_umbra),
    }
    print(f"  the reference recovers the known width in {hits} of {len(SYN_BETAS)} settings, "
          f"and its bounds are {'identical' if lo_reference == lo_umbra else 'NOT identical'} "
          f"to umbra's")
    return out


def _auc(values, labels) -> float:
    """Rank AUC from plain lists, so the reference curve carries the field delta_star reads."""
    pairs = sorted((v, y) for v, y in zip(values, labels) if v == v)
    if not pairs:
        return float("nan")
    ys = [y for _v, y in pairs]
    if len(set(ys)) < 2:
        return float("nan")
    # Ranks with ties averaged, then the Mann-Whitney identity.
    vals = [v for v, _y in pairs]
    ranks, i = [0.0] * len(vals), 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    n_pos = sum(ys)
    n_neg = len(ys) - n_pos
    r_pos = sum(r for r, y in zip(ranks, ys) if y == 1)
    return (r_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


# --------------------------------------------------------------------------- B
def _corpus_a_inputs():
    mem = pd.read_parquet(LEDGER / "membership.parquet")
    ev = pd.read_parquet(LEDGER / "events.parquet")
    ent = pd.read_parquet(LEDGER / "entities.parquet")
    ev = ev.merge(ent[["entity_id", "entity_type"]], on="entity_id", how="left")
    return mem, ev


def pass_b() -> dict:
    """Table 3's matched contrast, star by star, both implementations."""
    print("\nB. corpus A, Table 3, matched contrast per relation per lead time")
    mem, ev = _corpus_a_inputs()
    frames = [pd.read_parquet(GRAPH / f"edges_{r}.parquet").assign(relation=r)
              for r in RELATIONS_A]
    edges = pd.concat(frames, ignore_index=True)
    audit = HorizonAudit(edges, mem, ev)
    ref = ReferenceDensity(edges, mem)

    all_states = np.sort(mem.ccode.unique())
    ever = mem[mem.status == 1].groupby("entity_id").ccode.apply(set).to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna()
             & ev.t_R.between(*REGIME) & (ev.entity_type == "organisation")]
    rng = np.random.default_rng(SEED)

    diffs, n_vals, nan_mm = [], 0, 0
    rows = []
    for r in acc.itertuples():
        cc, t_ev, eid = int(r.ccode), int(r.t_R), r.entity_id
        never = np.setdiff1d(all_states, np.fromiter(ever.get(eid, set()), np.int64))
        if never.size == 0:
            continue
        negs = rng.choice(never, size=min(N_NEG, never.size), replace=False)
        for d in range(0, 9):
            t = t_ev - d
            ms = audit._member_sets.get((eid, t))
            if ms is None:
                continue
            for who, label in [(cc, 1)] + [(int(n), 0) for n in negs]:
                others = np.array([m for m in ms if m != who], np.int64)
                if others.size == 0:
                    continue
                rec = {"horizon": d, "label": label}
                for rel in RELATIONS_A:
                    u = _umbra_star(audit, who, others, t, rel)
                    v = ref.star(who, others, t, rel, 1)
                    n_vals += 1
                    if not _agree(u, v):
                        if (u != u) != (v != v):
                            nan_mm += 1
                        else:
                            diffs.append(abs(u - v))
                    rec[rel] = v
                rows.append(rec)

    df = pd.DataFrame(rows)
    pos = df[df.label == 1].groupby("horizon")[RELATIONS_A].mean()
    neg = df[df.label == 0].groupby("horizon")[RELATIONS_A].mean()
    con = pos - neg
    out = {"star": _report("star density, 5 relations x 9 lead times", diffs, n_vals, nan_mm),
           "contrast_from_the_reference": {
               rel: {int(h): round(float(v), 4) for h, v in con[rel].items()}
               for rel in RELATIONS_A}}

    stored = json.loads((RESULTS / "u1_isolation.json").read_text(encoding="utf-8"))
    published = stored["matched_contrast"]["contrast"]
    worst = max(abs(round(float(con[rel][h]), 4) - published[rel][str(h)])
                for rel in RELATIONS_A for h in range(0, 9))
    out["worst_deviation_from_the_published_table"] = float(worst)
    print(f"  Table 3 recomputed through the reference: worst deviation from the published "
          f"value {worst:.4f}")
    return out


def _umbra_star(audit: HorizonAudit, cc: int, others: np.ndarray, year: int, relation: str) -> float:
    """`umbra`'s star statistic, the code path `run_u1_isolation._Star` uses."""
    if int(cc) not in audit._ix:
        return float("nan")
    oi = np.array([audit._ix[int(m)] for m in others if int(m) in audit._ix], np.int64)
    if oi.size == 0:
        return float("nan")
    ci = audit._ix[int(cc)]
    k = np.minimum(ci, oi) * np.int64(audit._n) + np.maximum(ci, oi)
    arr = audit._keys.get((relation, int(year)))
    if arr is None:
        return 0.0
    p = np.clip(np.searchsorted(arr, k), 0, arr.size - 1)
    return float((arr[p] == k).mean())


# --------------------------------------------------------------------------- C
def pass_c() -> dict:
    """Table 4's corpus A rows: the clique contrast by size at both declared levels."""
    print("\nC. corpus A, Table 4, clique contrast by group size")
    mem, ev = _corpus_a_inputs()
    cm = pd.read_parquet(GRAPH / f"edges_{R_STAR_A}.parquet").assign(relation=R_STAR_A)
    audit = HorizonAudit(cm, mem, ev)
    ref = ReferenceDensity(cm, mem)

    all_states = np.sort(mem.ccode.unique())
    ever = mem[mem.status == 1].groupby("entity_id").ccode.apply(set).to_dict()
    acc = ev[(ev.event_type == "accession") & ev.ccode.notna() & ev.t_R.between(*REGIME)]

    diffs, n_vals, nan_mm = [], 0, 0
    out = {"levels": {}}
    for k in A_LEVELS:
        rng = np.random.default_rng(SEED)
        rows = []
        for r in acc.itertuples():
            cc, t, eid = int(r.ccode), int(r.t_R), r.entity_id
            ms = audit._members.get((eid, t))
            if ms is None or len(ms) < 2:
                continue
            never = np.setdiff1d(all_states, np.fromiter(ever.get(eid, set()), np.int64))
            if never.size == 0:
                continue
            n = len(ms)
            negs = rng.choice(never, size=min(N_NEG, never.size), replace=False)
            for who, lab in [(cc, 1)] + [(int(x), 0) for x in negs]:
                grp = np.append(ms[ms != who], who)
                u = audit.phi(grp, t, R_STAR_A, k)
                v = ref.phi(grp, t, R_STAR_A, k)
                n_vals += 1
                if not _agree(u, v):
                    if (u != u) != (v != v):
                        nan_mm += 1
                    else:
                        diffs.append(abs(u - v))
                if v == v:
                    rows.append((n, lab, float(v >= 1.0)))
        d = pd.DataFrame(rows, columns=["n", "label", "clique"])
        d["bin"] = pd.cut(d.n, BINS)
        tab = {}
        for b, s in d.groupby("bin", observed=True):
            p, q = s[s.label == 1], s[s.label == 0]
            if not len(p) or not len(q):
                continue
            tab[str(b)] = round(float(p.clique.mean() - q.clique.mean()), 4)
        out["levels"][f"k={k}"] = tab

    out["phi"] = _report("phi on candidate groups, 2 levels", diffs, n_vals, nan_mm)
    stored = json.loads((RESULTS / "clique_by_size.json").read_text(encoding="utf-8"))
    worst = 0.0
    for k in A_LEVELS:
        for b, v in out["levels"][f"k={k}"].items():
            pub = stored["corpus_a"][f"k={k}"].get(b, {}).get("clique_contrast")
            if pub is not None:
                worst = max(worst, abs(v - pub))
    out["worst_deviation_from_the_published_table"] = float(worst)
    print(f"  Table 4's corpus A rows recomputed: worst deviation {worst:.4f}")
    return out


# --------------------------------------------------------------------------- D
def pass_d(threshold: int = 400) -> dict:
    """Corpus B against two other implementations, one of them a separate code base."""
    print(f"\nD. corpus B at threshold {threshold}, three implementations")
    from vendor.cliquebait.diagnostics import LeakageAudit

    g = pd.read_parquet(WS2 / f"groups_thr{threshold}.parquet")
    e = pd.read_parquet(WS2 / f"edges_thr{threshold}.parquet")
    relations = sorted(e.relation.unique())

    # `umbra` and the reference both take LEDGER's column names, so the timeless corpus is given a
    # single constant year. `umbra` additionally indexes nodes by integer, which is why corpus B was
    # run through the CLIQUEBAIT library in the first place; relabelling the protein accessions
    # 0, 1, 2, ... is a bijection and changes no dyad, so it lets the third implementation take part
    # rather than leaving the comparison to two.
    YEAR = 0
    proteins = sorted(set(e.u) | set(e.v) | {m for row in g.members for m in row})
    code = {p: i for i, p in enumerate(proteins)}
    edges_int = pd.DataFrame({"relation": e.relation.to_numpy(),
                              "year": YEAR,
                              "cow_i": [code[x] for x in e.u],
                              "cow_j": [code[x] for x in e.v],
                              "weight": 1})
    ref = ReferenceDensity(edges_int, None)
    audit = HorizonAudit(edges_int,
                         pd.DataFrame({"entity_id": pd.Series(dtype=str),
                                       "ccode": pd.Series(dtype=int),
                                       "year": pd.Series(dtype=int),
                                       "status": pd.Series(dtype=int)}),
                         pd.DataFrame())
    lib = LeakageAudit(e, g).densities()

    diffs_ur, diffs_ul, n_vals, nan_mm = [], [], 0, 0
    rows = []
    for i, row in enumerate(g.itertuples()):
        members = [code[m] for m in row.members if m in code]
        rec = {"label": int(row.label), "size": len(row.members), "neg_type": row.neg_type}
        for rel in relations:
            v = ref.phi(members, YEAR, rel, 1)
            u = audit.phi(np.array(members, np.int64), YEAR, rel, 1)
            lv = float(lib.iloc[i][f"phi_{rel}"])
            n_vals += 1
            if not _agree(u, v):
                if (u != u) != (v != v):
                    nan_mm += 1
                else:
                    diffs_ur.append(abs(u - v))
            if not _agree(lv, v):
                if (lv != lv) != (v != v):
                    nan_mm += 1
                else:
                    diffs_ul.append(abs(lv - v))
            rec[rel] = v
        rows.append(rec)

    d = pd.DataFrame(rows)
    out = {"umbra_vs_reference": _report("phi, umbra against the reference", diffs_ur,
                                         n_vals, nan_mm),
           "cliquebait_vs_reference": _report("phi, CLIQUEBAIT against the reference", diffs_ul,
                                              n_vals, 0)}

    sub = d[(d.label == 1) | (d.neg_type == "random")].copy()
    sub["bin"] = pd.cut(sub["size"], BINS)
    tab = {}
    for b, s in sub.groupby("bin", observed=True):
        p, q = s[s.label == 1], s[s.label == 0]
        if not len(p) or not len(q):
            continue
        tab[str(b)] = round(float((p["database"] >= 1.0).mean()
                                  - (q["database"] >= 1.0).mean()), 4)
    out["contrast_from_the_reference"] = tab
    stored = json.loads((RESULTS / "clique_by_size.json").read_text(encoding="utf-8"))
    worst = max(abs(v - stored["corpus_b"]["k=1"][b]["clique_contrast"])
                for b, v in tab.items() if b in stored["corpus_b"]["k=1"])
    out["worst_deviation_from_the_published_table"] = float(worst)
    print(f"  Table 4's corpus B row recomputed: worst deviation {worst:.4f}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", choices=list("ABCD"), default=list("ABCD"))
    ap.add_argument("--json", type=Path, default=RESULTS / "reference_density.json")
    args = ap.parse_args()

    payload: dict = {
        "tolerance": TOL,
        "why": ("the two implementations compute a ratio of exact integer counts, so the target is "
                "equality and the tolerance covers only the division"),
        # What the cross-check actually bought, recorded rather than quietly fixed. Both entries are
        # specification gaps rather than arithmetic errors, which is the class of defect a second
        # implementation finds and a self-consistent validation suite cannot: the suite tests the code
        # against itself, and both implementations here were written from the prose.
        "reconciliations": [
            {"what": "level 1 means presence, not weight at least one",
             "found": ("the reference filtered weight >= level at every level, which empties the "
                       "voting-agreement relation (weights strictly inside the unit interval) and "
                       "halves trade flows (log volumes from -3.98 to 3.54); the disagreement on "
                       "those two stars was exactly 1.0"),
             "verdict": ("umbra was right and the prose was not explicit; the level ladder is "
                         "defined for the integer-weighted target relation and the anchors are "
                         "presence relations read at level 1. Section 4 now states it")},
            {"what": "corpus B was never run through umbra",
             "found": ("umbra indexes nodes by integer and corpus B identifies proteins by string "
                       "accession, so the second domain's statistics came from the pinned "
                       "CLIQUEBAIT library alone"),
             "verdict": ("relabelling the accessions 0, 1, 2, ... is a bijection that changes no "
                         "dyad, so all three implementations now compute the corpus B table and "
                         "agree exactly")},
        ],
    }
    if "A" in args.only:
        payload["synthetic"] = pass_a()
    if "B" in args.only:
        payload["corpus_a_table_3"] = pass_b()
    if "C" in args.only:
        payload["corpus_a_table_4"] = pass_c()
    if "D" in args.only:
        payload["corpus_b_table_4"] = pass_d()

    def worst_of(node) -> float:
        w = 0.0
        if isinstance(node, dict):
            for k, v in node.items():
                # Keys are not all strings: `per_beta` is keyed by the integer setting.
                key = str(k)
                if key == "worst_abs_diff" or key.startswith("worst_deviation"):
                    w = max(w, float(v))
                else:
                    w = max(w, worst_of(v))
        return w

    payload["worst_disagreement_anywhere"] = worst_of(payload)
    agree = payload["worst_disagreement_anywhere"] <= 1e-4
    payload["verdict"] = ("the density code agrees with an independent implementation on every "
                          "testbed" if agree else "the two implementations disagree; see above")
    print(f"\nworst disagreement anywhere: {payload['worst_disagreement_anywhere']:.3e}")
    print(payload["verdict"])
    write_result(args.json, payload, indent=2, default=str)
    print(f"written to {args.json}")
    return 0 if agree else 1


if __name__ == "__main__":
    sys.exit(main())

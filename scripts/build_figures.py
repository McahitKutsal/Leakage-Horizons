r"""Draw the manuscript's figures from `results/`, so no series can disagree with its artefact.

Every figure below was previously drawn by hand with the numbers typed in from the artefacts. Two of
the four defects an external read found in D-46 were in those drawings and neither was reachable by any
checker we had: `check_paper.py` compares text against artefacts, and a diagram is neither. Drawing
them from the artefacts removes the second copy.

Each function carries the specification the manuscript used to hold in a blockquote, because that text
is a drawing brief rather than manuscript content and this is where a drawing brief belongs.

    python scripts/build_figures.py             # all eight
    python scripts/build_figures.py --only 2 3  # a subset, while iterating
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from penumbra.figures import INK, SERIES, direct_label, panel, save, use_house_style  # noqa: E402
from penumbra.provenance import write_result  # noqa: E402

RESULTS = ROOT / "results"
FIGURES = ROOT / "paper" / "Figures"


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


# ============================================================================ Figure 1
def figure_1(fig_dir: Path) -> dict:
    r"""The diagnostic suite, and the two questions it separates.

    *Purpose.* A reader should leave this figure knowing three things without consulting the caption:
    that the provenance declaration is an input rather than an afterthought, that the suite produces an
    estimate and a measurement which are different objects, and that one of the four components was
    absent from the original design.

    *Layout.* Three tiers separated by two full-width rules, with the tier names in the left margin:
    DECLARE, COMPUTE, REPORT. The only element crossing the first rule is the arrow from the provenance
    card, and that is the visual claim.

    *Greyscale.* The accent appears twice, on the provenance card border and on the focal isolation
    box, and it never carries meaning alone: the provenance card also has the heavier border and the
    focal isolation box also has a marginal flag, so both survive printing in one ink.

    Schematic, no data. Drawn here rather than by hand so the whole set shares one type and one
    palette.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrow, FancyBboxPatch

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def card(x, y, w, h, title, body, *, accent=False, heavy=False, fill="white"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                    facecolor=fill,
                                    edgecolor=INK["accent"] if accent else INK["data_tertiary"],
                                    linewidth=1.6 if heavy else 0.8, zorder=3))
        ax.annotate(title, (x + w / 2, y + h - 3.4), ha="center", va="top",
                    color=INK["data_primary"], fontsize=7.6, zorder=4)
        if body:
            ax.annotate(body, (x + w / 2, y + h - 8.6), ha="center", va="top",
                        color=INK["data_tertiary"], fontsize=6.4, zorder=4)

    for y, name in ((88, "DECLARE"), (52, "COMPUTE"), (14, "REPORT")):
        ax.annotate(name, (1.5, y), rotation=90, ha="center", va="center", fontsize=7.0,
                    color=INK["data_tertiary"])
    for y in (72.5, 31.0):
        ax.plot([6, 100], [y, y], color=INK["grid"], lw=0.9, zorder=1)

    # ---- DECLARE ----
    card(8, 76, 26, 21, "Event corpus",
         "each event carries an interval\n" + r"$(t_L, t_R]$ and a dating stratum")
    card(38, 76, 26, 21, "Observation graph",
         "$m$ relations over one node set,\none of them the target $r^\\star$")
    card(68, 76, 30, 21, "Provenance declaration",
         "which relation is $r^\\star$,\nwhich are anchors,\nwhich are ineligible",
         accent=True, heavy=True)

    ax.add_patch(FancyArrow(83, 75.4, 0, -13.0, width=0.35, head_width=1.8, head_length=2.2,
                            length_includes_head=True, color=INK["accent"], zorder=5))
    # The claim the arrow makes is checkable for corpus A and not for corpus B, and Section 6.6
    # says so, so the arrow says so too rather than promising more than the artefact supports.
    ax.annotate("declared in writing before any\nstatistic; timestamped for corpus A",
                (80.6, 68.6), ha="right",
                va="center", color=INK["accent"], fontsize=6.4, zorder=5)

    # ---- COMPUTE ----
    comp = [(8, "U1", "at what lead time does\n$r^\\star$ re-enter the band?", False),
            (30, "U2", "how much discrimination\nsurvives with densities alone?", False),
            (52, "U3", "how much does a fitted\nmodel lose without $r^\\star$?", False),
            (74, "Focal isolation", "is the member on the group's\nown record before it joined?", True)]
    for x, title, body, flag in comp:
        card(x, 38, 20, 20, title, body, accent=flag,
             fill=INK["fill_light"] if flag else "white")
        if flag:
            ax.annotate("absent from the\noriginal specification",
                        (x + 10, 37.0), ha="center", va="top", color=INK["accent"], fontsize=6.0,
                        zorder=4)

    # ---- REPORT ----
    ax.add_patch(FancyBboxPatch((10, 6), 34, 19, boxstyle="round,pad=0.6,rounding_size=3.0",
                                facecolor="white", edgecolor=INK["data_tertiary"], lw=0.8,
                                zorder=3))
    ax.annotate(r"$\hat{\Delta}^\star$, a conservative estimate", (27, 20.5), ha="center",
                color=INK["data_primary"], fontsize=7.6, zorder=4)
    ax.annotate("a model dependent estimate,\nand the interval's upper end\nis not identified",
                (27, 16.0), ha="center", va="top", color=INK["data_tertiary"], fontsize=6.4,
                zorder=4)
    ax.add_patch(plt.Rectangle((58, 6), 34, 19, facecolor="white",
                               edgecolor=INK["data_tertiary"], lw=0.8, zorder=3))
    ax.annotate("measured back-dating width", (75, 20.5), ha="center",
                color=INK["data_primary"], fontsize=7.6, zorder=4)
    ax.annotate("a measurement: needs a source\nthat codes two dates", (75, 16.0), ha="center",
                va="top", color=INK["data_tertiary"], fontsize=6.4, zorder=4)

    ax.plot([51, 51], [7, 24], color=INK["guide"], lw=0.9, ls=(0, (3, 2)), zorder=2)
    ax.annotate("different objects,\noften confused", (51, 15.5), ha="center", va="center",
                color=INK["annotation"], fontsize=6.2, zorder=5,
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none"))

    for x0 in (18, 40, 62):
        ax.add_patch(FancyArrow(x0, 37.4, 0, -11.0, width=0.16, head_width=1.2, head_length=1.8,
                                length_includes_head=True, color=INK["data_tertiary"], zorder=2))
    ax.add_patch(FancyArrow(90.5, 37.4, 0, -11.0, width=0.16, head_width=1.2, head_length=1.8,
                            length_includes_head=True, color=INK["accent"], zorder=2))

    return {"stem": "figure-1", "paths": [str(p.name) for p in save(fig, fig_dir, "figure-1")]}


# ============================================================================ Figure 2
def figure_2(fig_dir: Path) -> dict:
    r"""How the lower bound is formed, and that it lands on the target six times out of six.

    *Purpose.* The summary scatter alone shows only that the estimator is right. The point of this
    figure is to show *why*, so a reader can see the estimate being formed and judge it, and then see
    the interval's upper end failing to form at all.

    *Layout.* Six small multiples, one per setting of the back-dating parameter, sharing axes: lead
    time 1 to 8 horizontally, clique contrast 0 to 1 vertically. In each cell the contrast for r-star
    is a heavy line with filled markers and the anchor band a light ribbon along the bottom. The first
    lead time at which the contrast falls inside the ribbon carries a dotted vertical and a filled
    triangle on the axis, with the estimate printed beside it. The visual result is a cliff that moves
    one step right per cell, which is the whole calibration argument in one view: the estimator is
    reading the width of the plateau.

    *Right column.* The six estimates against the truth, with the line y = x + 1 through all six
    points and whiskers from the family bootstrap, which extend upward only. Beneath it a row of six
    cells for the interval's upper end as specified, filled where it exists and hatched where it does not.
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    cal = load("delta_star_calibration.json")
    boot = load("bootstrap_diagnostics.json")["synthetic_calibration"]
    ub = load("upper_bound_audit.json")["synthetic"]

    runs = {r["beta"]: r for r in cal["results"] if r["stratum"] == "never_event"}
    betas = sorted(runs)

    fig = plt.figure(figsize=(7.4, 3.6))
    gs = GridSpec(2, 4, figure=fig, width_ratios=[1, 1, 1, 1.30],
                  wspace=0.34, hspace=0.78)

    for i, b in enumerate(betas):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        det = runs[b]["detail"]
        h = [d["horizon"] for d in det]
        contrast = [d["clique_contrast"] for d in det]
        band = [d["band_clique_contrast"] for d in det]

        ax.fill_between(h, 0, band, color=INK["band"], lw=0, zorder=1)
        ax.plot(h, contrast, **SERIES["target"], zorder=3, clip_on=False)

        lo = runs[b]["delta_star_lo"]
        if lo is not None:
            ax.axvline(lo, color=INK["guide"], lw=0.8, ls=(0, (1.5, 1.5)), zorder=2)
            ax.plot([lo], [0], marker="^", ms=5, color=INK["data_primary"],
                    clip_on=False, zorder=4)
            ax.annotate(rf"$\hat{{\Delta}}^\star={lo}$", (lo + 0.25, 0.62),
                        color=INK["data_secondary"], fontsize=7.2)

        panel(ax, title=rf"$\beta = {b}$", grid="none")
        ax.set_xlim(0.6, 8.4)
        ax.set_ylim(0, 1.06)
        ax.set_xticks([1, 3, 5, 8])
        ax.set_yticks([0, 0.5, 1])
        if i % 3 == 0:
            ax.set_ylabel("clique contrast")
        if i // 3 == 1:
            ax.set_xlabel(r"lead time $\Delta$")

        if b == 0:                      # the two series are named once, here, and nowhere else
            ax.annotate(r"contrast for $r^\star$", xy=(4.0, 0.017), xytext=(2.3, 0.44),
                        color=INK["data_primary"], fontsize=7.0,
                        arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"],
                                        shrinkA=1, shrinkB=2))
            ax.annotate("anchor band", xy=(6.8, 0.058), xytext=(4.9, 0.24),
                        color=INK["data_tertiary"], fontsize=7.0,
                        arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"],
                                        shrinkA=1, shrinkB=2))

    # ---- the summary scatter, with the resampling whiskers ----
    ax = fig.add_subplot(gs[0, 3])
    pts = [(b, runs[b]["delta_star_lo"]) for b in betas]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    hi = [boot[str(b)]["hi"] - runs[b]["delta_star_lo"] for b in betas]
    ax.plot([-0.4, 5.4], [0.6, 6.4], color=INK["guide"], lw=0.9, ls=(0, (4, 2)), zorder=1)
    ax.errorbar(xs, ys, yerr=[[0] * len(xs), hi], fmt="o", ms=4.2,
                color=INK["data_primary"], ecolor=INK["data_secondary"],
                elinewidth=1.0, capsize=2.2, capthick=0.8, zorder=3)
    # The setting where only two replicates in three land on the target gets the heavier whisker.
    worst = min(betas, key=lambda b: boot[str(b)]["share_on_target"])
    ax.errorbar([worst], [runs[worst]["delta_star_lo"]],
                yerr=[[0], [boot[str(worst)]["hi"] - runs[worst]["delta_star_lo"]]],
                fmt="none", ecolor=INK["data_primary"], elinewidth=2.0, capsize=3.0,
                capthick=1.4, zorder=4)
    direct_label(ax, 4.55, 7.55, "target", color=INK["guide"], size=7.0)
    ax.annotate(f"{boot[str(worst)]['share_on_target'] * 100:.0f} percent"
                "\non target",
                xy=(worst - 0.10, runs[worst]["delta_star_lo"] + 1.1), xytext=(1.25, 7.2),
                color=INK["data_secondary"], fontsize=6.6, ha="center", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"],
                                shrinkA=2, shrinkB=3))
    panel(ax, title="estimate against truth", grid="none")
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(0, 8.6)
    ax.set_xticks(betas)
    ax.set_yticks([0, 2, 4, 6, 8])
    ax.set_xlabel(r"true $\beta$")
    ax.set_ylabel(r"$\hat{\Delta}^\star$")

    # ---- the upper bound, one cell per setting ----
    # A row of six cells needs a sixth of the height its grid cell offers, and taking the rest leaves a
    # field of white that reads as a missing panel. Repositioned to the top of the cell instead.
    ax = fig.add_subplot(gs[1, 3])
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.50, box.width, box.height * 0.30])
    fired = set(ub["pre_specified_rule_fires_at_beta"])
    for i, b in enumerate(betas):
        on = b in fired
        ax.add_patch(plt.Rectangle((i + 0.08, 0.12), 0.84, 0.76,
                                   facecolor=INK["data_secondary"] if on else "white",
                                   edgecolor=INK["data_tertiary"], lw=0.7,
                                   hatch=None if on else "///"))
        ax.annotate(str(b), (i + 0.5, -0.06), ha="center", va="top",
                    color=INK["axis"], fontsize=7.0, annotation_clip=False)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 1.0)
    ax.axis("off")
    ax.annotate("the interval's upper end as specified", (0.0, 1.30), xycoords="axes fraction",
                color=INK["data_secondary"], fontsize=7.6, annotation_clip=False)
    ax.annotate(r"true $\beta$", (0.5, -0.52), xycoords="axes fraction", ha="center", va="top",
                color=INK["axis"], fontsize=7.0, annotation_clip=False)
    ax.annotate(f"exists in {ub['pre_specified_rule_fires_in']} of {ub['settings']};"
                " hatched is unreachable", (0.5, -1.05), xycoords="axes fraction",
                ha="center", va="top", color=INK["data_tertiary"], fontsize=6.8,
                annotation_clip=False)

    return {"stem": "figure-2", "paths": [str(p.name) for p in save(fig, fig_dir, "figure-2")]}


# ============================================================================ Figure 3
def figure_3(fig_dir: Path) -> dict:
    r"""Where the administrative trace lives, and which reading of the record finds it.

    *Purpose.* Section 3.3's claim that a group's own record is the only place back-dating can live is
    true under one dating convention and false under mixed ones, and the figure has to make both halves
    visible at once or it argues only one side. Panel A is the shortfall against the truth, by wave
    share, for the two readings of focal isolation in each convention regime: four series, of which the
    two "one convention" series lie exactly on zero and have to be drawn so a reader can see that they
    are on it rather than missing. Panel B is the control, the ambient off-focal reach for positives
    against matched negatives, which is the measurement that says the ambient content is not a trace.
    """
    import matplotlib.pyplot as plt

    cb = load("co_backdating.json")
    summ = cb["summary"]

    def series(law, field):
        pts = []
        for key, body in summ.items():
            if key.startswith(law + ","):
                share = float(key.split("=")[1])
                pts.append((share, body[field]))
        return sorted(pts)

    fig, (ax, axb) = plt.subplots(1, 2, figsize=(7.0, 2.9),
                                  gridspec_kw={"width_ratios": [1.55, 1]})

    for law, field, style, name in (
            ("mixed", "mean_gap_focal_group_only", "target", "mixed conventions,\nfocal record only"),
            ("mixed", "mean_gap_every_register", "anchor_a", "mixed conventions,\nevery register"),
            ("one", "mean_gap_focal_group_only", "flat", "one convention,\neither reading")):
        pts = series(law, field)
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        ax.plot(xs, ys, **SERIES[style], zorder=3)
        direct_label(ax, xs[-1] + 0.012, ys[-1], name, color=SERIES[style]["color"], size=6.2)
    ax.axhline(0, color=INK["guide"], lw=0.8, zorder=2)
    panel(ax, title="A. shortfall against the administrative horizon, by wave share", grid="y")
    ax.set_xlabel("share of events arriving in a curatorial wave")
    ax.set_ylabel("periods missed")
    ax.set_xlim(-0.03, 0.72)
    ax.set_ylim(-2.0, 3.4)
    ax.set_xticks([0, 0.1, 0.25, 0.5])
    ax.set_yticks([-1, 0, 1, 2, 3])

    amb = cb["ambient_off_focal"]
    labels = ["mean reach", "share carrying one"]
    pos = [amb["mean_reach_positives"], amb["share_positives"]]
    neg = [amb["mean_reach_negatives"], amb["share_negatives"]]
    x = np.arange(len(labels))
    w = 0.34
    axb.bar(x - w / 2, pos, w, color=SERIES["target"]["color"], zorder=3, label="positives")
    axb.bar(x + w / 2, neg, w, color=SERIES["anchor_a"]["color"], zorder=3,
            label="matched negatives")
    for xi, (a, b) in enumerate(zip(pos, neg)):
        axb.text(xi - w / 2, a + 0.04, f"{a:.2f}", ha="center", size=6.0, color=INK["data_primary"])
        axb.text(xi + w / 2, b + 0.04, f"{b:.2f}", ha="center", size=6.0, color=INK["data_primary"])
    panel(axb, title="B. ambient off-focal content: the same for both classes", grid="y")
    axb.set_xticks(x)
    axb.set_xticklabels(labels, size=6.4)
    axb.set_ylim(0, 1.32)
    axb.set_ylabel("periods, or share")
    axb.legend(frameon=False, fontsize=6.0, loc="upper right")

    fig.tight_layout()
    return {"stem": "figure-3", "paths": [str(p.name) for p in save(fig, fig_dir, "figure-3")]}

# ============================================================================ Figure 4
def figure_4(fig_dir: Path) -> dict:
    r"""A width printed in the source, and an instrument that recovers a tenth of it.

    *Purpose.* The paper's central comparison, and it should be legible in five seconds: a clean
    staircase on the left, a nearly flat line in the middle, and a quantified gap between them.

    *Panel A.* Five step functions, one per coded gap width, **all at exactly 1.0** until their gap and
    0.0 after. The hand-drawn version staggered them so they would not overplot, and on an axis running
    0 to 1 that stagger read as presence declining from 1.00 to 0.86 as the gap widens, which is a
    decline the data do not contain (D-46). Nothing is lost by removing it: the five lines differ in
    where they drop, not in how high they run.

    *Panel B.* The pooled relation as the suite specifies it, with the four per-gap curves behind it so
    a reader can see that even agreements with a coded gap of three stay high. Two dashed references at
    the means inside and outside the coded gap, with the contrast bracketed between them.

    *Panel C.* The same quantity both ways, on this register. The focal record's 1.000 is entailed by
    the two coded dates and the pooled 0.1023 is measured, and the panel says which is which, because
    Section 3.4 turns on that distinction.

    *Style.* Panels A and B keep identical vertical scale and height. Any rescaling of B to make its
    decline look steeper would invert the figure's meaning.
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    focal = load("desta_focal_only.json")["by_gap"]
    pta = load("desta_delta_star.json")["test1_trace_presence"]
    ratio = load("bootstrap_diagnostics.json")["pta_contrast"]

    fig = plt.figure(figsize=(7.4, 3.0))
    gs = GridSpec(1, 3, figure=fig, width_ratios=[4, 4, 2.6], wspace=0.34)

    # ---- A, the agreement's own record ----
    # The five curves are identical until each drops, so drawing five overlapping plateaus wastes the
    # panel and invites the offset that D-46 records. One plateau, five risers, each named at its own
    # riser: the reader sees that the height is shared and only the drop moves.
    axa = fig.add_subplot(gs[0, 0])
    gaps = sorted(int(g) for g in focal)
    for g in gaps:
        curve = focal[str(g)]
        h = sorted(int(k) for k in curve)
        y = [curve[str(k)] for k in h]
        axa.step(h, y, where="post", color=INK["data_primary"], lw=1.5, zorder=3)
        # Named at the corner where the line leaves the plateau, alternating height so five labels
        # one unit apart do not touch.
        axa.annotate(f"gap {g}", (g + 1.06, 0.92 if g % 2 == 0 else 0.84),
                     ha="left", va="center", color=INK["data_secondary"], fontsize=6.2, zorder=4)
    axa.axhline(1.0, color=INK["guide"], lw=0.8, ls=(0, (3, 2)), zorder=2)
    axa.annotate("presence is exactly 1 inside the coded gap, at every gap",
                 (0.05, 1.045), color=INK["guide"], fontsize=6.6)
    axa.annotate("drops at its own\ncoded width",
                 xy=(5.04, 0.42), xytext=(5.45, 0.60), color=INK["data_secondary"], fontsize=6.6,
                 arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"], shrinkB=3))
    panel(axa, title="A   the agreement's own record, entailed", grid="none")
    axa.set_ylabel("share of member pairs already present")
    axa.set_xlabel(r"lead time $\Delta$")
    axa.set_xlim(-0.2, 8.2)
    axa.set_ylim(0, 1.13)
    axa.set_xticks(range(0, 9, 2))
    axa.set_yticks([0, 0.25, 0.5, 0.75, 1.0])

    # ---- B, the pooled relation ----
    axb = fig.add_subplot(gs[0, 1], sharey=axa)
    h = sorted(int(k) for k in pta["share_present_by_horizon"])
    pooled = [pta["share_present_by_horizon"][str(k)] for k in h]
    # The per-gap curves are a fan behind the pooled line: only the widest is named, because it is the
    # one the text calls out and five right-edge labels collide at this size.
    for g, curve in sorted(pta["by_gap"].items(), key=lambda kv: int(kv[0])):
        axb.plot(h, [curve[str(k)] for k in h], color=INK["data_tertiary"], lw=0.7,
                 ls=(0, (2.5, 1.6)), zorder=2)
    widest = max(pta["by_gap"], key=lambda g: int(g))
    axb.annotate(f"agreements with a coded gap of {widest}",
                 (0.15, pta["by_gap"][widest][str(h[0])] + 0.022),
                 color=INK["data_tertiary"], fontsize=6.4)
    axb.plot(h, pooled, color=INK["data_primary"], lw=2.0, marker="o", ms=3.4, zorder=4)
    for level, name in ((pta["mean_inside_gap"], "mean inside"),
                        (pta["mean_outside_gap"], "mean outside")):
        axb.axhline(level, color=INK["annotation"], lw=0.8, ls=(0, (4, 2)), zorder=3)
        axb.annotate(name, (8.15, level), color=INK["annotation"], fontsize=6.2, va="center",
                     annotation_clip=False)
    axb.annotate("", xy=(1.4, pta["mean_inside_gap"]), xytext=(1.4, pta["mean_outside_gap"]),
                 arrowprops=dict(arrowstyle="<->", lw=0.9, color=INK["annotation"]))
    # The measure sits over a fan of curves, so it carries its own ground rather than relying on a gap.
    axb.annotate(f"contrast {pta['contrast']:.3f}",
                 (1.58, (pta["mean_inside_gap"] + pta["mean_outside_gap"]) / 2),
                 color=INK["annotation"], fontsize=6.8, va="center", zorder=6,
                 bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none"))
    panel(axb, title="B   the pooled relation, measured", grid="none")
    axb.set_xlabel(r"lead time $\Delta$")
    axb.set_xlim(-0.2, 8.2)
    axb.set_xticks(range(0, 9, 2))
    plt.setp(axb.get_yticklabels(), visible=False)

    # The sentence that makes the comparison a finding rather than two plots.
    axa.annotate("same agreements, same events, same lead times",
                 (1.06, 1.20), xycoords="axes fraction", ha="center",
                 color=INK["data_secondary"], fontsize=7.4, annotation_clip=False)

    # ---- C, the same quantity both ways ----
    axc = fig.add_subplot(gs[0, 2])
    point, clo, chi = (ratio["contrast"]["point"], ratio["contrast"]["lo"],
                       ratio["contrast"]["hi"])
    axc.barh([1], [1.0], height=0.34, color=INK["data_secondary"], zorder=3)
    axc.barh([0], [point], height=0.34, color=INK["data_primary"],
             xerr=[[point - clo], [chi - point]],
             error_kw=dict(ecolor=INK["annotation"], elinewidth=1.0, capsize=2.6), zorder=3)
    axc.annotate("focal record, 1.000\nentailed by two coded dates", (0.0, 1.28),
                 color=INK["data_secondary"], fontsize=6.6, va="bottom")
    axc.annotate(f"pooled relation, {point:.4f}\nmeasured, interval {clo:.4f} to {chi:.4f}",
                 (0.0, 0.28), color=INK["data_secondary"], fontsize=6.6, va="bottom")
    # The ratio is the panel's point, so it gets the space between the two bars rather than a corner.
    axc.annotate("", xy=(1.0, 0.62), xytext=(point, 0.62),
                 arrowprops=dict(arrowstyle="<->", lw=0.9, color=INK["annotation"]))
    axc.annotate(f"{ratio['focal_over_pooled']['point']:.1f}, interval "
                 f"{ratio['focal_over_pooled']['lo']:.1f} to {ratio['focal_over_pooled']['hi']:.1f}",
                 (0.56, 0.70), color=INK["annotation"], fontsize=6.8, ha="center", va="bottom")
    panel(axc, title="C   both ways, trade register", grid="none")
    axc.set_xlim(0, 1.10)
    axc.set_ylim(-0.45, 1.85)
    axc.set_yticks([])
    axc.set_xticks([0, 0.5, 1.0])
    axc.set_xlabel("share of member pairs")
    axc.annotate("the focal agreement contributes\n13,966 of 204,747 edge-years, 6.8 percent",
                 (0.5, -0.30), xycoords="axes fraction", ha="center", va="top",
                 color=INK["data_tertiary"], fontsize=6.4, annotation_clip=False)

    return {"stem": "figure-4", "paths": [str(p.name) for p in save(fig, fig_dir, "figure-4")]}


# ============================================================================ Figure 5
def figure_5(fig_dir: Path) -> dict:
    r"""A four-period horizon that is entirely recurrence.

    *Purpose.* To show a confound being removed. The reader should see a textbook decaying curve, then
    the same events with the confound conditioned away, and be able to tell from the figure alone which
    stratum the artefact loaded onto.

    *Layout.* Two panels stacked on identical vertical scales, because the collapse from upper to lower
    is the finding and rescaling would manufacture or hide it. A narrow right-hand column carries the
    recurrence rate of each stratum in the same two line styles as the series, so the correspondence
    needs no explanation.
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    iso = load("u1_isolation.json")
    width = load("bootstrap_diagnostics.json")["declared_resolution_width"]
    styles = {"declared_resolution": dict(color=INK["data_primary"], lw=1.7, marker="o", ms=3.8,
                                          markerfacecolor=INK["data_primary"]),
              "exact": dict(color=INK["data_tertiary"], lw=1.0, ls=(0, (4, 2)), marker="o", ms=3.4,
                            markerfacecolor="white")}
    label = {"declared_resolution": "declared resolution", "exact": "exactly dated"}

    fig = plt.figure(figsize=(7.4, 4.0))
    gs = GridSpec(2, 2, figure=fig, width_ratios=[4.4, 1], height_ratios=[1, 1],
                  wspace=0.22, hspace=0.34)

    for row, (key, title) in enumerate((("all_by_dating_stratum", "as computed, all accessions"),
                                        ("first_entry_by_dating_stratum",
                                         "conditioned on first entry"))):
        ax = fig.add_subplot(gs[row, 0])
        for stratum, st in styles.items():
            node = iso[key][stratum]
            h = sorted(int(k) for k in node["curve"])
            y = [node["curve"][str(k)] for k in h]
            ax.plot(h, y, **st, zorder=3)
            # Named once, in the upper panel, where the two series are still apart. At the right end
            # they sit on top of each other and run into the recurrence column beside them.
            if row == 0:
                direct_label(ax, 1.18, y[1] + 0.055,
                             f"{label[stratum]}, n = {node['n_events']:,}",
                             color=st["color"], size=6.6)
        panel(ax, title=title, grid="y")
        ax.set_ylim(0, 1.06)
        ax.set_xlim(-0.25, 8.25)
        ax.set_xticks(range(0, 9))
        ax.set_yticks([0, 0.5, 1.0])
        ax.set_ylabel("share already on the record")
        if row == 1:
            ax.set_xlabel(r"lead time $\Delta$")
        if row == 0:
            ax.annotate("reads as a four-period horizon with a floor",
                        xy=(3.0, 0.16), xytext=(3.4, 0.52), color=INK["annotation"], fontsize=7.0,
                        arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"], shrinkB=3))
        else:
            w = width["declared_resolution"]["presence_at_1"]
            ax.errorbar([1], [w["point"]], yerr=[[w["point"] - w["lo"]], [w["hi"] - w["point"]]],
                        fmt="none", ecolor=INK["annotation"], elinewidth=1.0, capsize=2.4, zorder=4)
            ax.annotate(f"{w['point']:.4f} [{w['lo']:.4f}, {w['hi']:.4f}]\n"
                        f"the register's own five-year block resolution, "
                        f"{width['declared_resolution']['n_events_at_lead_time_1']} events",
                        xy=(1.12, w["hi"]), xytext=(2.1, 0.62), color=INK["data_secondary"],
                        fontsize=6.8,
                        arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"], shrinkB=3))
            ax.annotate("nothing beyond one period, in either stratum", (4.4, 0.10),
                        color=INK["data_tertiary"], fontsize=6.8)

    # ---- the recurrence rates, in the line styles of the series ----
    ax = fig.add_subplot(gs[:, 1])
    rates = [(s, iso["all_by_dating_stratum"][s]["recurrence_share"]) for s in styles]
    for i, (stratum, share) in enumerate(rates):
        ax.barh([i], [share * 100], height=0.30, facecolor=styles[stratum]["color"],
                edgecolor="none", alpha=0.85 if stratum == "declared_resolution" else 0.55,
                zorder=3)
        ax.annotate(f"{share * 100:.2f} percent", (share * 100 + 1.4, i),
                    color=INK["data_secondary"], fontsize=6.8, va="center")
        ax.annotate(label[stratum], (0.0, i + 0.26), color=INK["data_tertiary"], fontsize=6.6)
    panel(ax, title="share whose state\nwas a member before", grid="none")
    ax.set_xlim(0, 42)
    ax.set_ylim(-0.55, 1.75)
    ax.set_yticks([])
    ax.set_xticks([0, 20, 40])
    ax.set_xlabel("percent")
    ax.annotate("the confound loads on the stratum\nthat appeared to have a horizon",
                (0.5, -0.30), xycoords="axes fraction", ha="center", va="top",
                color=INK["data_tertiary"], fontsize=6.4, annotation_clip=False)

    return {"stem": "figure-5", "paths": [str(p.name) for p in save(fig, fig_dir, "figure-5")]}


# ============================================================================ Figure 6
def figure_6(fig_dir: Path) -> dict:
    r"""Relations that cannot record the event decay like the one that can.

    *Purpose.* The paper's deepest negative result. A reader should see that the target relation's
    decay is unremarkable against relations incapable of carrying the label, that the reference band
    therefore subtracts almost all of it, and that the group's own record says the trace is gone after
    one period.

    *Bands.* The target relation and trade flows carry their family-bootstrap intervals, because the
    claim is that the two are not separated at the far end and a claim of that form cannot be read off
    point estimates.

    *Lower panel.* The residual the pre-specified rule reads, with the strip below it showing where
    that rule lands across 1,000 resamples. The arrow above is a mode, not a measurement, and the strip
    is what says so.
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    boot = load("bootstrap_diagnostics.json")["table_3_and_the_two_steps"]
    iso = load("u1_isolation.json")["matched_contrast"]

    order = [("igo_comembership", "co-membership, the target relation", "target", True),
             ("trades", "trade flows   anchor", "anchor_a", True),
             ("votes_with", "voting agreement   anchor", "anchor_b", False),
             ("allies", "alliance ties", "other", False),
             ("conflicts_with", "militarised disputes   anchor", "flat", False)]

    fig = plt.figure(figsize=(7.4, 4.4))
    gs = GridSpec(3, 1, figure=fig, height_ratios=[2.5, 1.05, 0.42], hspace=0.42)

    ax = fig.add_subplot(gs[0])
    h = list(range(0, 9))
    # The target relation and its strongest anchor end within three thousandths of each other, which is
    # the panel's point and also means their right-edge labels would sit on top of one another.
    nudge = {"igo_comembership": 0.016, "trades": -0.016}
    for rel, name, style, banded in order:
        pts = [boot["contrast"][rel][str(k)] for k in h]
        y = [p["point"] for p in pts]
        if banded:
            ax.fill_between(h, [p["lo"] for p in pts], [p["hi"] for p in pts],
                            color=INK["band"], alpha=0.55, lw=0, zorder=1)
        ax.plot(h, y, **SERIES[style], zorder=3)
        direct_label(ax, 8.16, y[-1] + nudge.get(rel, 0.0), name,
                     color=SERIES[style]["color"], size=6.6)
    ax.annotate("the two are no longer separated here",
                xy=(6.6, 0.155), xytext=(4.0, 0.256), color=INK["annotation"], fontsize=6.8,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"], shrinkB=3))
    ax.annotate("the only relation with no homophily,\nand the only flat one",
                xy=(3.0, 0.006), xytext=(1.15, 0.048), color=INK["data_tertiary"], fontsize=6.6,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"], shrinkB=3))
    panel(ax, title="matched density contrast by relation", grid="y")
    ax.set_xlim(-0.2, 8.2)
    ax.set_ylim(0, 0.40)
    ax.set_xticks(h)
    ax.set_ylabel("matched contrast")

    # ---- residual, and where the rule lands under resampling ----
    axr = fig.add_subplot(gs[1], sharex=ax)
    resid = [iso["r_star_minus_best_anchor"][str(k)] for k in h]
    axr.bar(h, resid, width=0.56, color=INK["data_secondary"], zorder=3)
    axr.axhline(0.01, color=INK["annotation"], lw=0.9, ls=(0, (4, 2)), zorder=4)
    axr.axhspan(0, 0.01, color=INK["fill_light"], zorder=1)
    cross = boot["residual_crossing_lead_time"]
    axr.annotate(r"the pre-specified rule returns $\hat{\Delta}^\star$ here",
                 xy=(cross["point"], resid[cross["point"]] + 0.002),
                 xytext=(cross["point"] + 0.35, 0.044),
                 color=INK["data_primary"], fontsize=6.8,
                 arrowprops=dict(arrowstyle="->", lw=0.8, color=INK["data_primary"], shrinkB=2))
    # The marker sits at the foot of the tallest bar, so it needs its own ground to be visible.
    axr.plot([1], [0], marker="s", ms=5.4, color=INK["data_primary"],
             markeredgecolor="white", markeredgewidth=1.1, clip_on=False, zorder=6)
    axr.annotate("focal isolation: the group's own\nrecord already carries nothing",
                 xy=(1.06, 0.0015), xytext=(1.95, 0.049), color=INK["data_primary"], fontsize=6.6,
                 arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"], shrinkB=3))
    panel(axr, title="target relation minus the strongest anchor", grid="none")
    axr.set_ylim(0, 0.076)
    axr.set_yticks([0, 0.03, 0.06])
    axr.set_ylabel("residual")

    axs = fig.add_subplot(gs[2], sharex=ax)
    dist = {int(k): v for k, v in cross["distribution"].items()}
    axs.bar(list(dist), list(dist.values()), width=0.56, color=INK["data_tertiary"], zorder=3)
    for k, v in dist.items():
        axs.annotate(str(v), (k, v + 8), ha="center", color=INK["data_tertiary"], fontsize=6.0)
    panel(axs, title="where the rule lands under resampling", grid="none")
    axs.set_ylim(0, 330)
    axs.set_yticks([])
    axs.set_xlabel(r"lead time $\Delta$")
    axs.spines["left"].set_visible(False)
    axs.annotate(f"never crossed inside eight in "
                 f"{cross['replicates_where_it_never_fired']} of {1000:,}",
                 (8.15, 120), color=INK["data_tertiary"], fontsize=6.6, va="center",
                 annotation_clip=False)

    return {"stem": "figure-6", "paths": [str(p.name) for p in save(fig, fig_dir, "figure-6")]}


# ============================================================================ Figure 7
def figure_7(fig_dir: Path) -> dict:
    r"""The same shape in two domains, read at two levels, and a reversal when the relation saturates.

    *Purpose.* To show that the size dependence of the clique statistic is a property of the statistic
    rather than of either corpus, and that it inverts at a level where the relation is saturated. What
    the figure must **not** suggest is that the two corpora trace one function: they are read at
    different levels and their heights are not comparable, so the comparison is of shape.

    *Whiskers.* Not decoration. The smallest corpus A bin rests on 24 events and its interval overlaps
    the next bin's, so a reader must be able to see that the apparent peak at the left is unresolved.
    The structural zeros at the right come through resampling as exact zeros with zero-width intervals,
    which is drawn as a flat cap rather than omitted.
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    boot = load("bootstrap_diagnostics.json")["clique_contrast_by_size"]
    bins = ["(1, 3]", "(3, 5]", "(5, 10]", "(10, 20]", "(20, 80]", "(80, 10000]"]
    names = ["2 to 3", "4 to 5", "6 to 10", "11 to 20", "21 to 80", "81 and above"]
    series = [("corpus_b", "k=1", "target", "corpus B, protein complexes, $k = 1$"),
              ("corpus_a", "k=25", "anchor_a", "corpus A, coalitions, $k = 25$"),
              ("corpus_a", "k=1", "anchor_b", "corpus A at $k = 1$")]

    fig = plt.figure(figsize=(7.4, 4.1))
    gs = GridSpec(2, 1, figure=fig, height_ratios=[3.1, 1], hspace=0.16)
    ax = fig.add_subplot(gs[0])
    x = np.arange(len(bins))
    ax.axvspan(4.5, 5.5, color=INK["fill_light"], zorder=0)
    ax.annotate("structurally zero: a clique needs all "
                r"$\binom{n}{2}$ pairs", (4.66, 0.30), rotation=90, ha="center", va="center",
                color=INK["data_tertiary"], fontsize=6.6, zorder=2)
    for corp, lvl, style, name in series:
        node = boot[corp][lvl]
        y = [node[b]["point"] for b in bins]
        lo = [node[b]["point"] - node[b]["lo"] for b in bins]
        hi = [node[b]["hi"] - node[b]["point"] for b in bins]
        ax.errorbar(x, y, yerr=[lo, hi], **SERIES[style], ecolor=SERIES[style]["color"],
                    elinewidth=0.9, capsize=2.2, capthick=0.8, zorder=3)
        ax.plot([], [], **SERIES[style], label=name)
    ax.annotate("same corpus, same statistic, saturated level:\nthe dependence inverts",
                xy=(4.75, 0.478), xytext=(2.45, 0.66), color=INK["annotation"], fontsize=6.8,
                arrowprops=dict(arrowstyle="->", lw=0.7, color=INK["annotation"],
                                connectionstyle="arc3,rad=-0.25", shrinkB=4))
    panel(ax, grid="y")
    ax.set_ylim(0, 0.87)
    ax.set_xlim(-0.45, 5.5)
    ax.set_xticks(x)
    ax.tick_params(labelbottom=False)
    ax.set_ylabel("clique contrast")
    ax.legend(loc="upper left", handlelength=2.6, borderaxespad=0.2, labelspacing=0.35)

    # ---- counts per bin, two opposing wedges on one log scale ----
    axc = fig.add_subplot(gs[1], sharex=ax)
    for i, (corp, lvl, style, _n) in enumerate(series[:2]):
        node = boot[corp][lvl]
        counts = [node[b]["n_pos"] or 0 for b in bins]
        off = -0.19 if i == 0 else 0.19
        axc.bar(x + off, counts, width=0.34, color=SERIES[style]["color"],
                alpha=0.85 if i == 0 else 0.6, zorder=3)
        for xi, c in zip(x, counts):
            axc.annotate(f"{c:,}", (xi + off, c * 1.35), ha="center", color=INK["data_tertiary"],
                         fontsize=5.6, va="bottom")
    axc.set_yscale("log")
    panel(axc, grid="none")
    axc.set_ylim(1, 60_000)
    axc.set_yticks([])
    axc.spines["left"].set_visible(False)
    axc.set_xticks(x)
    axc.set_xticklabels(names)
    axc.set_xlabel("members in the group the event enters")
    axc.annotate("positive groups per bin, log scale: corpus B dark, corpus A light",
                 (0.0, 1.10), xycoords="axes fraction", color=INK["data_tertiary"], fontsize=6.4)

    return {"stem": "figure-7", "paths": [str(p.name) for p in save(fig, fig_dir, "figure-7")]}


# ============================================================================ Figure 8
def sd_pad(sd: float) -> float:
    """Vertical clearance for a label beside an error bar whose half-length is `sd`."""
    return sd * 0.15


def figure_8(fig_dir: Path) -> dict:
    r"""Message passing against a capacity-matched control, with the seed spread that settled it.

    *Purpose.* To show simultaneously that the graph-free control is saturated in capacity, that two of
    the three message passing encoders sit above it and one sits below, and that the margins have to be
    read against the seed spread. That last is why the figure exists: at two seeds one margin read as
    0.0009 and at four the homogeneous encoder read as a tie.

    Drawn at **ten** seeds. The four-seed run is kept in the artefacts and in Table 10, because the
    change between them is a result rather than a superseded draft, and the figure shows the count it is
    drawn at on its axis label so a reader cannot mistake one for the other.
    """
    import matplotlib.pyplot as plt

    agg = load("paper_support.json")["architecture_by_seed_count"]["ten_seeds"]
    params = {k: v for k, v in load("p7_s10.json")["n_parameters"].items()}
    ctrl_p = load("p7_ctrl_w128_s10.json")["n_parameters"]["4"]
    ctrl96_p = load("p7_ctrl_w96_s10.json")["n_parameters"]["4"]

    controls = [(int(params["4"]), agg["rung4_mean_auc"], agg["rung4_sd_over_seeds"], "width 64"),
                (int(ctrl96_p), agg["mlp_w96_mean_auc"], agg["mlp_w96_sd_over_seeds"], "width 96"),
                (int(ctrl_p), agg["mlp_w128_mean_auc"], agg["mlp_w128_sd_over_seeds"], "width 128")]
    encoders = [(int(params["5"]), agg["rung5_mean_auc"], agg["rung5_sd_over_seeds"],
                 "homogeneous message passing"),
                (int(params["6"]), agg["rung6_mean_auc"], agg["rung6_sd_over_seeds"],
                 "relation specific"),
                (int(params["7"]), agg["rung7_mean_auc"], agg["rung7_sd_over_seeds"], "temporal")]

    # The contribution by lead time was an inset and it sat on top of the encoder it describes. A short
    # panel underneath costs the same space and hides nothing.
    from matplotlib.gridspec import GridSpec
    fig = plt.figure(figsize=(7.0, 4.3))
    gs = GridSpec(2, 1, figure=fig, height_ratios=[2.5, 1], hspace=0.42)
    ax = fig.add_subplot(gs[0])
    lo, hi = agg["rung4_mean_auc"], agg["mlp_w96_mean_auc"]
    ax.axhspan(min(lo, hi), max(lo, hi), color=INK["fill_light"], zorder=0)
    ax.annotate(f"graph-free capacity curve: doubling the\nparameters buys "
                f"{agg['width_64_to_128']:.4f}", (117_500, 0.8455),
                ha="right", va="bottom", color=INK["data_tertiary"], fontsize=6.6)

    cx = [c[0] for c in controls]
    cy = [c[1] for c in controls]
    ax.errorbar(cx, cy, yerr=[c[2] for c in controls], fmt="s", ms=4.6,
                markerfacecolor="white", color=INK["data_tertiary"], ecolor=INK["data_tertiary"],
                elinewidth=0.9, capsize=2.4, ls=(0, (4, 2)), lw=0.9, zorder=3)
    for x, y, _sd, name in controls:
        direct_label(ax, x, y - 0.0034, name, color=INK["data_tertiary"], size=6.4, ha="center")

    for x, y, sd, name in encoders:
        heavy = name == "relation specific"
        ax.errorbar([x], [y], yerr=[sd], fmt="o", ms=5.2, color=INK["data_primary"],
                    ecolor=INK["data_primary"], elinewidth=2.0 if heavy else 1.0,
                    capsize=3.0 if heavy else 2.4, capthick=1.4 if heavy else 0.8, zorder=4)
        # The homogeneous encoder sits below the control band and its label would land on the
        # width-64 control's; it goes to the left of the point instead.
        if name.startswith("homogeneous"):
            direct_label(ax, x - 1200, y, "homogeneous", color=INK["data_primary"], size=6.8,
                         ha="right")
        else:
            direct_label(ax, x, y + sd + 0.0018, name, color=INK["data_primary"], size=6.8,
                         ha="center")

    for (cxi, cyi), (exi, eyi, margin, label) in zip(
            [(controls[1][0], controls[1][1]), (controls[2][0], controls[2][1])],
            [(encoders[1][0], encoders[1][1],
              agg["relation_specific_vs_w96"]["margin"],
              f"{agg['relation_specific_vs_w96']['sigma']:.1f} SE"),
             (encoders[2][0], encoders[2][1],
              agg["temporal_vs_w128"]["margin"],
              f"{agg['temporal_vs_w128']['sigma']:.0f} SE")]):
        ax.annotate("", xy=(exi, eyi), xytext=(exi, cyi),
                    arrowprops=dict(arrowstyle="<->", lw=0.8, color=INK["annotation"]))
        ax.annotate(f"+{margin:.4f}, {label}", (exi + 1700, (eyi + cyi) / 2 + 0.0012),
                    color=INK["annotation"], fontsize=6.8, va="center")

    hom = agg["homogeneous_vs_w64"]
    ax.annotate(f"worse than its width-64 control: {hom['margin']:+.4f},\n"
                f"{abs(hom['sigma']):.1f} SE, losing {hom['cells'] - hom['cells_won']} "
                f"of {hom['cells']} cells",
                (encoders[0][0] + 2200, encoders[0][1] - sd_pad(encoders[0][2])),
                ha="left", va="center", color=INK["data_secondary"], fontsize=6.6)
    ax.annotate("at four seeds the margin above read as 0.0121\nand the one below as a tie",
                xy=(encoders[1][0] - 700, encoders[1][1] + encoders[1][2] * 0.6),
                xytext=(50_600, 0.8875), color=INK["data_secondary"], fontsize=6.6,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=INK["guide"], shrinkB=3))

    panel(ax, grid="y")
    ax.set_xlim(48_000, 118_000)
    ax.set_ylim(0.842, 0.893)
    ax.set_xlabel("parameters")
    ax.set_ylabel("mean pooled AUC over ten seeds")
    ax.set_xticks([50_000, 70_000, 90_000, 110_000])
    ax.set_xticklabels(["50,000", "70,000", "90,000", "110,000"])

    # ---- the contribution over the graph-free control, by lead time ----
    rows = pd.DataFrame(load("p7_s10.json")["rows"])
    means = rows.groupby(["rung", "horizon"]).auc.mean().unstack()
    axi = fig.add_subplot(gs[1])
    lead = list(means.columns)
    for rung, style, name in ((7, "target", "temporal"), (6, "anchor_a", "relation specific"),
                              (5, "flat", "homogeneous")):
        gain = (means.loc[rung] - means.loc[4]).tolist()
        axi.plot(lead, gain, **SERIES[style], zorder=3)
        direct_label(axi, lead[-1] + 0.28, gain[-1], name, color=SERIES[style]["color"], size=6.4)
    axi.axhline(0, color=INK["guide"], lw=0.7)
    panel(axi, title="contribution over the graph-free control, by lead time: largest at the "
                     "shortest, and negative throughout for the homogeneous encoder", grid="y")
    axi.set_xlim(0.5, 10.5)
    axi.set_ylim(-0.015, 0.030)
    axi.set_xticks(lead)
    axi.set_yticks([-0.01, 0, 0.01, 0.02, 0.03])
    axi.set_xlabel("lead time, periods")
    axi.set_ylabel("gain")

    return {"stem": "figure-8", "paths": [str(p.name) for p in save(fig, fig_dir, "figure-8")]}


BUILDERS = {1: figure_1, 2: figure_2, 3: figure_3, 4: figure_4, 5: figure_5,
            6: figure_6, 7: figure_7, 8: figure_8}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, nargs="+", default=sorted(BUILDERS))
    ap.add_argument("--json", type=Path, default=RESULTS / "figures.json")
    args = ap.parse_args()

    use_house_style()
    FIGURES.mkdir(parents=True, exist_ok=True)
    built = {}
    for n in args.only:
        if n not in BUILDERS:
            print(f"  skip  figure {n}: no builder yet")
            continue
        built[n] = BUILDERS[n](FIGURES)
        print(f"  figure {n}: {', '.join(built[n]['paths'])}")

    write_result(args.json, {"figures": built,
                             "note": ("drawn from results/ by scripts/build_figures.py; the series in "
                                      "a figure and the series in an artefact are now one object")},
                 indent=2, default=str)
    print(f"\nwritten to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

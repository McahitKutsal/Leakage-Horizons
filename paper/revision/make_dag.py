"""Figure 1: what the leakage horizon is, and what it is not.

Draws the decomposition of Section 4.3 as a graph, so that each of the four terms of
kappa = tau + lambda + eta + rho corresponds to one path into the target relation.
Label positions are computed from the drawn curves rather than placed by hand.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

fig, ax = plt.subplots(figsize=(9.8, 5.6))
ax.set_xlim(0.0, 9.9)
ax.set_ylim(-0.80, 5.80)
ax.axis("off")

NODE = dict(boxstyle="round,pad=0.34", linewidth=1.3, edgecolor="#1a1a1a",
            facecolor="white")
SHADED = dict(boxstyle="round,pad=0.34", linewidth=1.5, edgecolor="#1a1a1a",
              facecolor="#cfcfcf")
RULE = dict(boxstyle="round,pad=0.28", linewidth=1.1, edgecolor="#4d4d4d",
            facecolor="#f4f4f4")

nodes = {
    "U":  (1.15, 4.55, "Latent\nsimilarity", NODE, 10),
    "Y":  (1.15, 2.70, "Accession event\nat $t+\\Delta$", NODE, 10),
    "P":  (1.15, 0.85, "Prior\nmembership spell", NODE, 10),
    "Df": (4.95, 4.05, "focal register's\ndating rule", RULE, 8.6),
    "Do": (4.95, 1.35, "other registers'\ndating rules", RULE, 8.6),
    "R":  (8.45, 2.70, "Target relation\nat origin $t$", NODE, 10),
    "S":  (3.05, 0.60, "Comparison stratum", SHADED, 9.4),
}
pos = {}
for key, (x, y, label, style, fs) in nodes.items():
    ax.text(x, y, label, ha="center", va="center", fontsize=fs, bbox=style,
            zorder=4, linespacing=1.35)
    pos[key] = (x, y)


def rot90(v):
    """Perpendicular in the orientation matplotlib's arc3 uses for a positive rad."""
    return (v[1], -v[0])


def arrow(a, b, dashed=False, rad=0.0, lw=1.45, shrink=27):
    """Draw an arrow and return the midpoint of the curve it traces."""
    p0, p2 = pos[a], pos[b]
    d = (p2[0] - p0[0], p2[1] - p0[1])
    perp = rot90(d)
    ctrl = (0.5 * (p0[0] + p2[0]) + rad * perp[0],
            0.5 * (p0[1] + p2[1]) + rad * perp[1])
    ax.add_patch(FancyArrowPatch(
        p0, p2, arrowstyle="-|>", mutation_scale=15, linewidth=lw,
        color="#1a1a1a", linestyle=(0, (5.5, 3.2)) if dashed else "solid",
        connectionstyle=f"arc3,rad={rad}", shrinkA=shrink, shrinkB=shrink,
        zorder=2))
    return (0.25 * p0[0] + 0.5 * ctrl[0] + 0.25 * p2[0],
            0.25 * p0[1] + 0.5 * ctrl[1] + 0.25 * p2[1])


def label(xy, text, dx=0.0, dy=0.0, fs=11):
    ax.text(xy[0] + dx, xy[1] + dy, text, ha="center", va="center", fontsize=fs,
            zorder=5, bbox=dict(boxstyle="square,pad=0.18", facecolor="white",
                                edgecolor="none"))


# the event and its two generative causes
arrow("U", "Y")
arrow("P", "Y")

# the dating rules write the event into the relation at earlier valid times
arrow("Y", "Df", dashed=True, shrink=24)
m_tau = arrow("Df", "R", dashed=True, shrink=24)
arrow("Y", "Do", dashed=True, shrink=24)
m_lam = arrow("Do", "R", dashed=True, shrink=24)

# homophily and recurrence reach the relation without passing through the event
m_eta = arrow("U", "R", rad=-0.418)
m_rho = arrow("P", "R", rad=0.514)

# the stratum is selected on outcomes after the origin
arrow("Y", "S", shrink=24)

label(m_tau, r"$\tau$   trace on the focal record", dx=0.15, dy=0.42)
label(m_lam, r"$\lambda$   trace on other records", dx=0.15, dy=-0.42)
label(m_eta, r"$\eta$   homophily", dy=0.06)
label(m_rho, r"$\rho$   recurrence", dy=0.02)

ax.text(3.05, 0.14, "conditioned on", ha="center", va="center", fontsize=8.6,
        style="italic", color="#3d3d3d", zorder=5)
ax.text(9.05, 1.45, "what a pooled\ncontrast reads", ha="center", va="center",
        fontsize=8.6, style="italic", color="#3d3d3d", linespacing=1.3)
ax.text(9.72, 5.42, "dashed: the register's dating rule", ha="right",
        va="center", fontsize=8.6, color="#3d3d3d")

fig.tight_layout(pad=0.3)
fig.savefig("figures/figure-dag.png", dpi=300, facecolor="white")
print("wrote figures/figure-dag.png")

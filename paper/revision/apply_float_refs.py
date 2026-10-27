"""Every float a journal prints has to be pointed at from the running text.
These edits add the pointers the rewrite dropped. Each must match exactly once."""
import pathlib
import sys

HERE = pathlib.Path(__file__).parent / "sections"

EDITS = [
    ("06-design.md",
     "We call what it does a **scope test** for that reason. Calling it a "
     "replication would promise otherwise.",
     "We call what it does a **scope test** for that reason. Calling it a "
     "replication would promise otherwise. Table 2 states the two corpora side "
     "by side."),

    ("07a-results-synthetic.md",
     "The estimate lands on the target in **6 of 6** settings. The resampling "
     "column is what a point estimate hides.",
     "The estimate lands on the target in **6 of 6** settings, and Figure 3 "
     "shows the six estimates against the target line. The resampling column is "
     "what a point estimate hides."),

    ("07b-results-field.md",
     "Calling that a leakage horizon of eleven would be the error this paper is "
     "about.",
     "Calling that a leakage horizon of eleven would be the error this paper is "
     "about. Table 5 reports the sweep."),
    ("07b-results-field.md",
     "**Reading every register closes most of it, and that is the "
     "recommendation.** Graded against the administrative horizon,",
     "**Reading every register closes most of it, and that is the "
     "recommendation.** Figure 4 puts the two readings against the truth in "
     "both regimes. Graded against the administrative horizon,"),
    ("07b-results-field.md",
     "Agreements with a coded gap of three periods still show 91 percent "
     "presence eight periods out.",
     "Agreements with a coded gap of three periods still show 91 percent "
     "presence eight periods out. Figure 5 puts the two measurements side by "
     "side."),
    ("07b-results-field.md",
     "It is a density and not a clique rate.",
     "It is a density and not a clique rate, and Figure 7 plots the full "
     "curves."),
    ("07b-results-field.md",
     "which is also the stratum whose dates are least precise.",
     "which is also the stratum whose dates are least precise. Figure 6 shows "
     "the same events before and after conditioning."),

    ("07c-results-scope-task.md",
     "Corpus A is read at $k = 25$ because at $k = 1$ its target relation has "
     "density 0.9954 and the statistic is degenerate there. Corpus B is read at "
     "$k = 1$ because its channels are binary.",
     "Corpus A is read at $k = 25$ because at $k = 1$ its target relation has "
     "density 0.9954 and the statistic is degenerate there. Corpus B is read at "
     "$k = 1$ because its channels are binary. They are two decreasing "
     "functions read at two levels, not one function traced twice, which is "
     "what Figure 8 draws."),
    ("07c-results-scope-task.md",
     "Table 9 gives the architectural comparison: four encoders over the same "
     "risk set with parameter-matched graph-free controls, at ten seeds and at "
     "four.",
     "Table 9 gives the architectural comparison, and Figure 9 plots it against "
     "parameter count: four encoders over the same risk set with "
     "parameter-matched graph-free controls, at ten seeds and at four."),
]


def main():
    by_file = {}
    for name, old, new in EDITS:
        by_file.setdefault(name, []).append((old, new))

    problems, already = [], []
    for name, edits in by_file.items():
        path = HERE / name
        text = path.read_text(encoding="utf-8")
        for old, new in edits:
            if text.count(old) == 1:
                text = text.replace(old, new)
            elif text.count(old) == 0 and text.count(new) == 1:
                already.append(name)
            else:
                problems.append(f"{name}: {text.count(old)} matches for "
                                f"{old[:60]!r}")
        path.write_text(text, encoding="utf-8")

    if problems:
        print("EDITS NOT APPLIED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print(f"{len(EDITS) - len(already)} float references added, "
          f"{len(already)} already in place")


if __name__ == "__main__":
    main()

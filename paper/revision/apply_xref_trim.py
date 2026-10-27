"""Drop cross-references a reader does not need to follow. The reviewer's
complaint was that the manuscript sends you elsewhere to finish a sentence;
each edit below makes the sentence stand on its own."""
import pathlib
import sys

HERE = pathlib.Path(__file__).parent / "sections"

EDITS = [
    ("02-what-this-is.md",
     "This is a decomposition of sources, not an algebraic identity, and "
     "Section 4.3 gives each term a section.",
     "This is a decomposition of sources, not an algebraic identity."),
    ("05-suite.md",
     "report a linear probe alongside a non-linear one. Section 8 gives the "
     "reason:",
     "report a linear probe alongside a non-linear one. The reason:"),
    ("07a-results-synthetic.md",
     "Read as the conservative estimate of Section 4.2, the same number",
     "Read as a conservative estimate under that asymmetry, the same number"),
    ("07a-results-synthetic.md",
     "All four estimators of Section 7.2, including the pre-specified rule, "
     "return the correct value of 1.",
     "All four estimators, including the pre-specified rule, return the correct "
     "value of 1."),
    ("07b-results-field.md",
     "The mechanism does not switch on with similarity, which is why "
     "Section 4.3 gives it its own term.",
     "The mechanism does not switch on with similarity, which is why it carries "
     "its own term in the decomposition."),
    ("07b-results-field.md",
     "Overshooting is the direction the loss of Section 4.2 prefers.",
     "Overshooting is the direction the asymmetric loss prefers."),
    ("07b-results-field.md",
     "For 94 percent of the corpus that zero is an entailment, as Section 4.5 "
     "records.",
     "For 94 percent of the corpus that zero is an entailment and not a "
     "measurement."),
    ("07b-results-field.md",
     "the coding rule that locates an event inside such a block is exactly the "
     "curatorial decision Section 1 describes:",
     "the coding rule that locates an event inside such a block is exactly the "
     "curatorial decision this paper is about:"),
    ("07c-results-scope-task.md",
     "and Section 6.5's check that the negatives are not edge-excluded is the "
     "statement that does.",
     "and the check that the negatives are not edge-excluded is the statement "
     "that does."),
    ("08-misreports.md",
     "since it follows from the registers rather than from either corpus, and "
     "it is the term $\\lambda$ in Section 4.3.",
     "since it follows from the registers and not from either corpus, and it is "
     "the term $\\lambda$ of the decomposition."),
    ("10-limitations.md",
     "We have since written a second implementation from the Section 4 "
     "definitions, sharing nothing with the first:",
     "We have since written a second implementation from the definitions, "
     "sharing nothing with the first:"),
    ("06-design.md",
     "and focal isolation reads that one. This is Section 6.3's situation "
     "exactly,",
     "and focal isolation reads that one. This is the trade register's "
     "situation exactly,"),
    ("13-backmatter.md",
     "including the objection that became Section 7.3 and the terminology of "
     "the horizon itself.",
     "including the objection that became the off-focal experiment and the "
     "terminology of the horizon itself."),
    ("13-backmatter.md",
     "including the second implementation of the density code in Section 10, "
     "was performed by an author who had written the code being audited, which "
     "is why Section 10 states that threat at the level of the author group.",
     "including the second implementation of the density code, was performed by "
     "an author who had written the code being audited, which is why Section 10 "
     "states that threat at the level of the author group."),
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
                                f"{old[:55]!r}")
        path.write_text(text, encoding="utf-8")
    if problems:
        print("EDITS NOT APPLIED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print(f"{len(EDITS) - len(already)} cross-references trimmed, "
          f"{len(already)} already in place")


if __name__ == "__main__":
    main()

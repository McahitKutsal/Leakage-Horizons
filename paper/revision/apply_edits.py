"""Targeted prose edits. Each must match exactly once or the script fails,
so an edit that no longer applies is reported instead of silently skipped."""
import pathlib
import sys

HERE = pathlib.Path(__file__).parent / "sections"

EDITS = [
    # one wrong cross-reference: the consequence of the left truncation is
    # reported with the coalition corpus result, not with its description
    ("02-what-this-is.md",
     "a consequence that is central to Section 6.4 rather than incidental:",
     "a consequence that is central to Section 7.5 and not incidental:"),

    # de-tic: "rather than" used as a rhetorical operator rather than a comparison
    ("00-front.md",
     "We measure both conditions rather than assume them,",
     "We measure both conditions instead of assuming them,"),
    ("02-what-this-is.md",
     "we think it is the useful thing this paper has to say rather than an "
     "objection to it.",
     "we think it is the useful thing this paper has to say, not an objection "
     "to it."),
    ("06-design.md",
     "because the edge budget is a fixed integer count of dyads rather than a "
     "sampled quantity,",
     "because the edge budget is a fixed integer count of dyads and not a "
     "sampled quantity,"),
    ("06-design.md",
     "would make part of the reported contrast structural rather than measured, "
     "and it is verifiable rather than asserted:",
     "would make part of the reported contrast structural instead of measured. "
     "The claim is checkable:"),
    ("07a-results-synthetic.md",
     "a lower bound that comes back above the quantity it bounds is wrong "
     "rather than cautious.",
     "a lower bound that comes back above the quantity it bounds is wrong, not "
     "cautious."),
    ("07a-results-synthetic.md",
     "which makes it a property of the two statistics rather than of a sample.",
     "which makes it a property of the two statistics and not of a sample."),
    ("07a-results-synthetic.md",
     "The clique estimate at $h = 3$ is 0.97 over five seeds rather than exactly "
     "1.00.",
     "The clique estimate at $h = 3$ is 0.97 over five seeds, not exactly 1.00."),
    ("07b-results-field.md",
     "This is corpus A's situation rather than a contrivance:",
     "This is corpus A's situation, not a contrivance:"),
    ("07b-results-field.md",
     "It verifies the pipeline rather than recovering the width independently, "
     "and Table 1 records it as such.",
     "It verifies the pipeline; it does not recover the width independently, "
     "and Table 1 records it as such."),
    ("09-one-date.md",
     "a reason to report the width for a subpopulation rather than to abandon it.",
     "a reason to report the width for a subpopulation, not to abandon it."),
    ("10-limitations.md",
     "its absence is a limitation of this paper rather than a claim about the "
     "literature.",
     "its absence is a limitation of this paper and not a claim about the "
     "literature."),

    # drop cross-references a reader does not need to follow
    ("04-formulation.md",
     "The level $k$ matters because a weighted relation can be near-saturated as "
     "a binary relation while still discriminating at higher weights, and "
     "Section 7.5 shows this is the case for co-membership.",
     "The level $k$ matters because a weighted relation can be near-saturated as "
     "a binary relation while still discriminating at higher weights, which is "
     "the case for co-membership."),
    ("04-formulation.md",
     "We therefore fix a set of **anchor** relations by reading what each source "
     "records, before computing anything, and take the band from them. "
     "Section 7.6 tests whether that reading is any good.",
     "We therefore fix a set of **anchor** relations by reading what each source "
     "records, before computing anything, and take the band from them."),
    # the matched density contrast is Table 6 in this manuscript, not Table 7
    ("07a-results-synthetic.md",
     "militarised disputes, flat at 0.004 at every lead time in Table 7.",
     "militarised disputes, flat at 0.004 at every lead time in Table 6."),
    ("07b-results-field.md",
     "Table 7 reports the matched contrast by relation and lead time on 52,305 "
     "positives,",
     "Table 6 reports the matched contrast by relation and lead time on 52,305 "
     "positives,"),
    ("08-misreports.md",
     "Section 7.2 shows the clique statistic surviving strong homophily at "
     "density 0.12, failing to fire at all at 0.50 and overshooting at 0.90, so "
     "**saturation is the condition under which homophily breaks it**.",
     "The clique statistic survives strong homophily at density 0.12, fails to "
     "fire at all at 0.50 and overshoots at 0.90, so **saturation is the "
     "condition under which homophily breaks it**."),
]


def main():
    by_file = {}
    for name, old, new in EDITS:
        by_file.setdefault(name, []).append((old, new))

    problems = []
    applied_already = []
    for name, edits in by_file.items():
        path = HERE / name
        text = path.read_text(encoding="utf-8")
        for old, new in edits:
            hits = text.count(old)
            if hits == 1:
                text = text.replace(old, new)
            elif hits == 0 and text.count(new) == 1:
                applied_already.append(name)      # re-run, nothing to do
            else:
                problems.append(f"{name}: {hits} matches for {old[:60]!r}")
        path.write_text(text, encoding="utf-8")

    if problems:
        print("EDITS NOT APPLIED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print(f"{len(EDITS) - len(applied_already)} edits applied, "
          f"{len(applied_already)} already in place, "
          f"{len(by_file)} files")


if __name__ == "__main__":
    main()

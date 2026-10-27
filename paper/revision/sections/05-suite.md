## 5. The diagnostic suite

The suite has four components, and Figure 2 gives the pipeline.

**U1, the horizon curve.** For each lead time $\Delta$ in a declared range, compute the clique contrast for $r^{\star}$ and for every anchor, on both comparison strata, at every level $k$ of the declared ladder. The estimate $\widehat{\Delta}^{\star}$ is the smallest $\Delta$ at which the contrast for $r^{\star}$ falls inside the anchor band. A second statistic was specified alongside it to close the interval from above, namely the smallest $\Delta$ at which $r^{\star}$ both loses top rank and has its single-feature discrimination fall inside the band; Section 7.1 reports that it is not identified. We keep the definition in print because a rule that failed is evidence about the design.

**U2, the lead-time-resolved shortcut probe.** Fit a probe at each lead time using only relational densities and clique indicators, with no learned representation, cross-fitted with folds grouped on the resampling unit, and report the discrimination curve together with its decay. Report a linear probe alongside a non-linear one, because a decay present at every capacity including linear is not a capacity artefact, and without the linear comparison the question cannot be answered at all.

**U3, the exclusion contrast.** Refit with $r^{\star}$ excluded and report the change, which measures how much of a fitted model's discrimination depends on the target relation. That is a different quantity from how much of the target relation's density is event-related.

**Focal isolation.** For each event, ask whether the acceding entity is already on the focal group's own record $\Delta$ periods before the coded event date. Under honest dating this is 1 at $\Delta = 0$ and 0 beyond, so any excess is back-dating of exactly that width. Applied to a corpus it is run over every group's own record and not only over the group whose event is being audited, for a reason Section 7.3 measures.

Three conventions govern how a weighted relation is read. The ladder applies to $r^{\star}$ only, which is read at level 1 and at a declared primary level, because co-membership's weight is a count of shared organisations. The anchors are read as presence relations, since their weights are not counts: trade flows carry log volumes from $-3.98$ to $3.54$ and voting agreement lies strictly inside the unit interval. And "level 1" means presence, not weight at least one, since a literal threshold at weight one would empty the voting relation and discard half of trade flows. We state the third because a second implementation written from our prose read it literally and disagreed with the original by exactly 1.0 on those two relations. The original was right and the prose was silent.

[FIGURE 1]

**Figure 2.** The diagnostic suite, and the two questions it separates. Schematic, no data.

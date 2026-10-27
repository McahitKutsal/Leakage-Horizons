## 4. Problem formulation

### 4.1 Corpus and notation

A **group corpus** is a set of entities $c \in C$, each with a membership set $S_{c}(t) \subseteq V$ varying over discrete time $t$, together with a set of **events**. An accession event is a triple $(c,v,t)$ recording that $v$ joined $c$ at $t$. Because registers record dates at varying resolution, each event carries an interval $(t_{L},t_{R}]$ and a **dating stratum**, an exactly dated event being the case $t_{R} = t_{L} + 1$.

An **observation graph** $G_{t} = (V,E_{t}^{r_{1}},\ldots,E_{t}^{r_{m}})$ carries $m$ relations over one node set. One is designated $r^{\star}$, the **target relation**: the relation through which the event would leak if it leaks at all. For accession to an organisation it is co-membership, under which two entities share an edge when they belong to a common organisation in that year. Note that $r^{\star}$ is built from the register that supplies the labels. This is deliberate: it leaks by construction, and the question is how far back.

For a group $S$ and relation $r$, write $\Pi(S)$ for the unordered pairs of members and define the **group density**

$$\phi_{r}(S;k) = \frac{\text{number of pairs } (u,v) \in \Pi(S) \text{ with } w_{r}(u,v) \geq k}{|\Pi(S)|},$$

where $w_{r}$ is the edge weight, so that at $k = 1$ it is the share of member pairs connected in $r$. The level $k$ matters because a weighted relation can be near-saturated as a binary relation while still discriminating at higher weights, which is the case for co-membership.

### 4.2 The leakage horizon

Fix a lead time $\Delta \geq 0$; a forecaster at origin $t$ predicting events at $t + \Delta$ sees $G_{t}$. Define the **clique contrast**

$$\kappa_{r}(\Delta) = P\big( \phi_{r}(S) = 1 \mid \text{positive} \big) - P\big( \phi_{r}(S) = 1 \mid \text{negative} \big),$$

where a positive is a candidate acceding at $t + \Delta$ and a negative is drawn from the comparison stratum declared in Section 2.3. The **leakage horizon** $\Delta^{\star}$ is the smallest $\Delta$ at which $r^{\star}$ is statistically indistinguishable from relations declared not to carry the event.

The reference band comes from documentary grounds and not from the graph, since no statistic computed from the graph separates leakage from legitimate signal: a relation that genuinely informs the label and a relation generated from it both make positives denser than negatives. We therefore fix a set of **anchor** relations by reading what each source records, before computing anything, and take the band from them.

What kind of estimate the rule produces has to be stated, because the obvious name promises something else. We specified the horizon as an interval, bracketed below by the clique statistic and above by rank position and single-feature discrimination. Section 7.1 reports that the bracket does not hold, and we withdraw it. What survives is one number whose errors run one way: against a width a generator sets it never falls below the target, and it exceeds it by one or two periods in a third of resamples at the widest setting. That is not the behaviour of a lower bound. Calling it conservative is defensible only once the loss is written down. Treating a contaminated relation as clean corrupts every number computed downstream and is not detectable from those numbers, whereas treating a clean relation as contaminated costs lead times and therefore sample size. Under that asymmetry an estimator whose errors run upward is the safe one; under a symmetric loss it would not be. We write $\widehat{\Delta}^{\star}$ for what the rule returns and call it a **conservative horizon estimate**.

### 4.3 Two operations on the focal group

Two interventions on $r^{\star}$ are available, and they are opposites. **Focal exclusion** removes $E^{r^{\star}} \cap \Pi(S_{c})$, the focal group's own contribution, so that the group's own edges cannot stand in for the label when a model is estimated; any leakage-aware pipeline needs it. **Focal isolation** keeps only those edges and discards the rest, because the group's own edges are where administrative back-dating of the group's own event lives: a curator's decision to date a membership from signature rather than from operation is a decision about that group's record.

Whether it touches that group's record *alone* is what the operation's freedom from homophily rests on. The claim holds of the focal **event** and does not transfer to the target **relation**. If the acceding entity and a sitting member are co-members of some other group, the dyad they carry in $r^{\star}$ belongs to that group's record, and if that record is back-dated the dyad is an administrative trace no reading of the focal register reaches. For such a trace to correlate with the label, the entity's entry into the other group must fall near its entry into the focal one, which is what accession waves are. Section 7.3 makes the wave a controlled parameter and measures what it costs.

### 4.4 Measured, and entailed by the register

A zero can arise in two ways that mean opposite things. A statistic returns zero because the quantity it looks for is absent, which is a measurement; it also returns zero because the register cannot express the quantity, in which case the zero follows from the construction. Focal isolation identifies a back-dating width **if and only if the register dates the relation and the event from separate fields.** Where it does, as in Section 6.3's trade register, the presence curve is the width. Where the register codes one date per membership and derives the event from a transition in that same field, the curve is 1 at $\Delta = 0$ and 0 beyond **by construction**. The coalition corpus is of the second kind for 94 percent of its events, and Section 9 says what to do about that.

Table 1 records which side of the line each headline quantity sits on. Entailments are not weaker results; they are results about the register rather than about the corpus.

| Quantity | Section | Status |
|---|---|---|
| Estimate recovers $\beta + 1$ in 6 of 6 settings | 7.1 | **measurement** against a width the generator sets |
| False-positive rate at zero homophily and zero width | 7.1 | **measurement**, the negative control |
| Identification slope of each estimator on the true width | 7.2 | **measurement** against a width the generator sets |
| Off-focal reach under one dating convention | 7.3 | **measurement**, and it is zero |
| Off-focal reach under mixed conventions | 7.3 | **measurement** against a width the generator sets |
| Trade register back-dated increment, 6.8 percent of the relation | 6.3 | **measurement**, both dates coded |
| Trade register focal record, presence 1 inside the coded gap | 7.4 | **entailment**, reported as a pipeline validation |
| Trade register pooled contrast, 0.1023 | 7.4 | **measurement** |
| Coalition exactly dated stratum, 1.000 falling to 0.000 | 7.5 | **entailment**, one coded date per membership |
| Coalition declared-resolution stratum, 0.1419 at one period | 7.5 | **measurement**, the register's own block resolution |
| Coalition pooled contrast, 0.3114 falling to 0.1490 | 7.5 | **measurement** |
| Clique contrast 0.0000 above eighty members | 7.6 | **measurement** with a combinatorial ceiling |
| The interval's upper end is not identified | 7.1 | **measurement** about the definition, not about a corpus |

**Table 1.** Every headline quantity, and whether it is a measurement or an entailment of the register's construction.

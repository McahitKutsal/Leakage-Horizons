## 6. Experimental design

We use four testbeds: two ground-truth settings in which the width is known independently of the diagnostic, and two field corpora in which it is not.

### 6.1 Declaration protocol

Every choice that could have been made after seeing a result was fixed in writing beforehand: the target relation and anchor set for each corpus, the level ladder, the comparison strata, the resampling unit, the covariate set and the lead times. Where a pre-specified rule returned a result we then judged uninterpretable, we report the rule's output together with the reason for rejecting it.

The declaration is released as a separate citable artefact, of which one half is timestamped and the other is not. The coalition corpus's declaration was committed to version control before any data was materialised, amended twice within a day and frozen, and it contains the two predictions that corpus went on to falsify. The protein corpus's channel assignment lives in an analysis script's docstring that was not committed before it was run, so the repository cannot corroborate that the reading preceded the statistic; Section 7.6 states the consequence where the result appears. Depositing the artefact now fixes its text, but it does not make a later timestamp evidence about an earlier order.

### 6.2 Synthetic testbed

A generator produces a group corpus with two controlled parameters: **completeness** $\alpha$, the share of the target relation's edges present, and **back-dating** $\beta$, the number of periods before the event at which the focal group's edges appear. Each setting has 200 nodes and 90 accession events, and completeness tracks $\alpha$ to within 0.0004.

A calibration testbed has to get one thing right. The density of $r^{\star}$ must not move with the parameter being calibrated, or the estimator is graded against a relation that grew denser instead of a width that grew wider. Here the density is *exactly* invariant, one value across every cell, because the edge budget is a fixed integer count of dyads and not a sampled quantity, and the invariance is checked before any estimator is graded. The tempting alternative is worse than doing nothing: letting the budget grow with $\beta$ restores invariance on paper and destroys it in fact, since back-dating enlarges the pool of group-induced dyads and a growing budget holds the nominal density fixed while the group-induced share rises with the parameter. The budget is therefore sized once, from the measured worst case over the whole sweep, which peaks at 1,794 eligible dyads of 19,900 pairs.

Two registers are emitted rather than one, because the two instruments read different objects. The *honest* register records an entity as a member from the period it truly joined, and U1 must be built on that one: the risk set is states not already members, so a back-dated register would drop exactly the leaking rows as ineligible. The *recorded* register is what a curator wrote, with every event appearing $\beta$ periods early, and focal isolation reads that one. This reproduces the trade register's situation exactly, and it is what lets the two instruments be compared against one known truth.

A second generator adds the axes the first holds fixed, the first being left untouched so the calibration cannot move. It adds homophily strength $h$, an exponent on latent similarity in every sampling weight, so that at $h = 0$ positives and negatives differ only through the event; a per-event width redrawn from the trade register's coded gap distribution; dating noise, a share of events whose *coded* date is displaced from the true one, making the register wrong rather than early; a switch for whether the anchors share the latent space, so that one setting reproduces the coalition corpus and the other the protein corpus; and a curatorial wave, under which a share of accession events arrive with the acceding entity also entered into a second group that already overlaps the focal one, the second register being back-dated by its own law. The generator records, per event, which record carries the trace and how far it reaches, so the two are separable rather than inferred.

### 6.3 A field register that codes the width

The DESTA register of preferential trade agreements (Dür et al., 2014) codes, for each agreement and each acceding party, both a signature year $s$ and an entry-into-force year $f$, so a graph built from signature-dated membership carries a dyad exactly $f - s$ periods before the legal event. **The width is printed in the source.**

Over the observation window there are 759 accession entries with a coded force year, with gap median 1, mean 1.71, and 39.4 percent at two or more periods. The signature-dated relation has 204,747 edge-years against the force-dated relation's 190,781, a difference of 13,966 edge-years or 6.8 percent. The convention adds dyad-years rather than moving them: 13,967 dyad-years appear only in the signature-dated relation and exactly one appears only in the force-dated one. This 6.8 percent is a property of this register and is not carried to the coalition corpus.

### 6.4 Field corpus A: international coalitions

The primary corpus comprises 562 entities, 490 intergovernmental organisations and 72 multilateral treaties, over 1946 to 2014. It carries 10,328 events, of which 8,062 are accessions, and membership occupies 505,400 entity-year rows over 202 states. Events fall in three dating strata: 9,581 exact; 646 **declared resolution**, where the source states its own dates are accurate only within five years; and 101 **rule assigned**, where the coding rule computes a date from up to a decade of subsequent data.

The observation graph carries five relations: co-membership; alliance ties from a treaty obligations register (Leeds et al., 2002); trade flows; voting agreement in the United Nations General Assembly derived from dynamic ideal points (Bailey et al., 2017); and militarised disputes (Palmer et al., 2022). Analysis is confined to 1965 to 2014 for the reason given in Section 2.3. Resampling uses **membership equivalence families** rather than entities, because two entities whose member sets coincide for a sustained period are not independent observations; the corpus contains 464 families, of which 43 hold more than one entity.

### 6.5 Field corpus B: protein complexes

The scope-test corpus comprises 2,540 curated protein complexes against 2,540 random and 5,080 hard negatives over 19,486 proteins, with a ten-channel interaction network as the relations. It was chosen for one property: its group size distribution is the inverse of corpus A's. Median complex size is 3, with 0.16 percent of positives above eighty members, against corpus A's 41.1 percent.

The target relation is the channel importing the curated complex registers, which is the label source itself. Two further channels were declared **contaminated and therefore ineligible as anchors** before any statistic was computed, since one aggregates text-mined co-occurrence from papers that describe complexes and one aggregates experimental evidence including co-immunoprecipitation. The five remaining channels were declared anchors: messenger RNA co-expression, two transferred variants, gene fusion events, phylogenetic co-occurrence, and sequence homology. None can record a curator's decision that a set of proteins forms a complex.

The negative construction matters because the level of every contrast depends on it. Each positive complex generates three negatives, two *hard* and one *random*. A random negative is $k$ proteins drawn uniformly without replacement from the universe of proteins carrying at least one channel edge, where $k$ is the positive's size, so it is size-matched by construction; a hard negative keeps the positive's members with $b = \min(2,k-2)$ of them dropped and $b$ proteins substituted. **No existing edge is excluded and no collision with a real complex is checked**, since the alternative would make part of the reported contrast structural instead of measured. The claim is checkable: had edges been avoided, the negatives' mean density in the target relation would be zero, and it is 0.00132 against the relation's own density of 0.00115.

Corpus B has no time axis, so it cannot reproduce a single result about lead time, and lead time is what a leakage horizon is measured in. We call what it does a **scope test** for that reason. Table 2 states the two corpora side by side.

| | **Corpus A, coalitions** | **Corpus B, protein complexes** |
|---|---|---|
| Groups | 562 entities | 2,540 complexes |
| Nodes | 202 states | 19,486 proteins |
| Positive events | 8,062 accessions | 2,540 complexes |
| Negatives | declared strata, subsampled | 2,540 random, 5,080 hard |
| Relations | 5 | 10 |
| Time axis | 1946 to 2014, annual | none |
| Median size of the group an event enters | 60 | 3 |
| Share above 80 members | 41.1 percent of events | 0.16 percent of complexes |
| Target relation density | 0.9954 | 0.001153 |
| Highest relation density | 0.9954 | 0.001887 |

**Table 2.** The two field corpora. The size distributions are inverses of each other, which is why corpus B is the scope test.

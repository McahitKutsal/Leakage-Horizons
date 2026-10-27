## 1. Introduction

A group membership forecaster takes a set of candidate entities, a group, and a body of relational data, and asks whether a candidate will join. Recommender systems predict community joins from social graphs, computational biology predicts protein complex membership from interaction networks, and political forecasting predicts accession to international organisations from trade, alliance and voting networks. What these share is that both the relational data and the labels come from curated registers, compiled by people recording events after the fact.

### 1.1 A failure that a correct temporal split does not catch

Consider a forecaster that predicts, for each state and each intergovernmental organisation, whether the state will accede within the next year. Its labels come from a membership register, and so does its most informative feature: co-membership, under which two states are tied when they belong to a common organisation.

Registers date their contents by conventions of their own, and those conventions are documented rather than hidden. The Correlates of War membership register states that some of its dates are accurate only to a five-year block, and that organisations founded before its exact-dating era are coded by rule. Wherever a register dates a membership from the signing of a founding convention rather than from the year the organisation began operating, the co-membership edge enters the feature graph before the accession it encodes.

A strict temporal split leaves this untouched. The split itself is honest, since no row after the prediction origin is used, yet the features are contaminated anyway because the contamination sits inside the register and not across the boundary. What a practitioner needs to know is therefore not whether such contamination exists but how far back it reaches. A system forecasting one year ahead may be entirely compromised while the same system forecasting five years ahead is not.

### 1.2 The standard audit gives the wrong answer

The leakage literature supplies checklists and taxonomies, and where it implies an estimator the estimator is pooled: compare the relational density of positives against that of negatives at increasing lead times, and declare the horizon closed once the difference becomes indistinguishable from relations that cannot carry the event. Applied to our coalition corpus, that procedure reports contamination still present eight years before accession.

It is not there, and the corpus supplies two independent reasons for saying so. The first is a control the design already contains. Trade flows cannot record an accession to an intergovernmental organisation, yet at eight years their matched contrast is 0.1463, with a 95 percent interval of 0.1161 to 0.1755, against the target relation's 0.1490, interval 0.1160 to 0.1768. A relation built from the label source and a relation that cannot record the label are indistinguishable at the far end of the range the audit examines. What the decaying curve measures is not a trace of the event but similarity: states that accede to a group are genuinely more like its members than never-joiners are, and were so a decade earlier. That similarity is the signal a forecaster should be using. The second reason is the register's own record, which, read on the focal group alone and conditioned on first-time entry, carries a trace at one year and nothing beyond it.

A practitioner following the pooled recipe would therefore discard eight years of training data to remove a contamination at most one year wide. That is the cost this paper is about, and it runs both ways: the instrument that invents a horizon where none exists will also miss one where it is real.

### 1.3 Two settings in which the width is observed rather than assumed

An objection arrives at this point, and it is the right one. If the true horizon is unknown, then any claim that an instrument over- or under-reports rests on assumptions the data cannot test. We therefore grade the instrument in two settings where the width is not assumed at all.

The first is a register that codes it twice. The DESTA preferential trade agreement register records both a signature year and an entry-into-force year for each agreement and acceding party, so a graph built from signature-dated membership carries a dyad exactly the difference of the two before the legal event. Over 759 accession entries the width is printed in the source. Graded against it the pooled reading fails, because the back-dated dyads amount to 6.8 percent of the relation and a density over the whole relation is a weighted average in which the quantity of interest carries weight 0.068. The second setting is a generator that sets the width, with the target relation's density held exactly invariant across every cell, so an estimator is graded against a width that moved and not against a relation that grew denser. There the pre-specified rule recovers the width in six settings of six and never falls below it under resampling.

Neither setting involves an assumption about an unobserved population. Both are widths we can see, and a framework capable only of confirming itself would not have produced the DESTA failure.

### 1.4 Contributions

1. We define the leakage horizon over a multi-relational temporal graph and give a four-component diagnostic suite that estimates it. The fourth component, focal isolation, reads the focal group's own record, and we show the design cannot do without it.

2. We calibrate the suite in the two settings above, where the width is observed. The generator is where the instrument works; the trade register is where the pooled reading is falsified against a width we can see.

3. We turn the identification failure from an argument into a measurement. As homophily concentrates, the pooled statistic loses all dependence on the true width, and widening the examined range turns a slope of zero into a slope of about minus one. We reproduce the collapse under three similarity kernels sharing no functional form and show that our coalition corpus lies inside the regime in which two of the three break the statistic.

4. We measure, rather than argue, the two conditions focal isolation needs: it identifies a width only where the register dates the relation and the event from separate fields, and it is complete only where every register feeding the target relation dates by one convention.

5. Because most registers code one date per membership, Section 9 sets out five procedures that remain available when focal isolation is silent by construction.

Section 2 states what this problem is and distinguishes it from three problems it resembles, since the distinction decides what evidence can settle it.

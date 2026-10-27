## S4. From the register to each reported count

Several counts in the main text differ for reasons that are correct and that a reader cannot reconstruct without being told. Each arrow below is a filter and every filter is named. The whole chain is recomputed by a script that reaches each count through the same code path the reporting script uses, so this is a second reading of the numbers and not a restatement of them.

**Groups.**

| Step | Count | Where it is reported |
|---|---|---|
| Entities in the register | 562 | Section 6.4 |
| Observation interval overlaps 1965 to 2014 | 528 | the population left truncation threatens |
| An active membership row inside the window | 527 | the panel the termination hazard is estimated on, Table S1 |

**Terminations.**

| Step | Count | Where it is reported |
|---|---|---|
| Coded terminations, whole register | 185 | Section 6.4 |
| Inside the window | 151 | |
| On a group in the estimated panel | 150 | Table S1 |

The one group that separates 528 from 527 has no active membership row inside the window, and it carries one of the 151 coded terminations. That is why the panel scores 150 and not 151.

**Accession events.**

| Step | Count | Where it is reported |
|---|---|---|
| Accession events, whole register | 8,062 | Section 6.4 |
| Inside the window | 6,597 | Table 7 and Figure 8 |
| One accession per dyad | 6,501 | Table 8; 96 repeat accessions of 94 dyads are collapsed onto the first, 1.5 percent |

A dyad leaves the risk set when it accedes, which is why the dyad and not the event is the unit of the accession task.

**Exactly dated accessions, for focal isolation.**

| Step | Count | Where it is reported |
|---|---|---|
| Exactly dated accessions, whole register | 7,615 | Section 6.4 |
| First entry, which removes prior membership spells | 7,146 | the count at lead time zero, Section 7.5 |
| The focal group has a member set in the preceding period | 7,084 | the count at lead time one, over which that stratum's interval is taken |

The 62 events that separate 7,146 from 7,084 are accessions in a group's founding period, where there is no earlier record for the entity to be absent from. Focal isolation is defined at lead time one only where the focal group has a member set in the preceding period.

**Declared-resolution accessions.**

| Step | Count | Where it is reported |
|---|---|---|
| Declared-resolution accessions | 447 | Section 6.4 |
| First entry | 310 | the stratum's measurement of 0.1419, Section 7.5 |

None of the 310 is lost at lead time one.

## S5. Software

The corpus construction, the diagnostic suite, the survival estimators, the synthetic generators and every analysis script are released at the repository named in the main text's data and code availability statement, under the MIT licence. Every stored result carries the command that produced it and a three-integer fingerprint of the corpus version it was computed on, and a consistency checker compares every registered number against the artefacts. The second, independent implementation of the density code is released alongside the first, together with the cross-check that compares them, because a claim that two implementations agree is only checkable if both are available.

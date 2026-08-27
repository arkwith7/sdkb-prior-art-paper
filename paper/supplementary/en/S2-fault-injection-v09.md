# S2. The four adjudications of the fault injection and CQ pass rates by generation (full text of v0.9 §6.5–§6.6)

> **This is a move, not a deletion.** Under PLAN-033 §3.2, H1 (discriminative power of the gate) is
> demoted in the v2.0 manuscript to **the design (§4.9) plus one paragraph of holdout confirmation
> (§6.5)**. The four adjudications that led to the verdict (H1 → H1′ → H1″ → H1‴) and the table of
> CQ pass rates by generation are preserved here in full. **Not a character was altered** — hiding
> the order of re-adjudication would make it indistinguishable from p-hacking, and exposing that
> order is why this record exists. Source: §6.5–§6.6 of the canonical manuscript at commit
> `f3127f5`.
>
> This is the English rendering of the Korean audit record
> [S2-fault-injection-v09.md](../S2-fault-injection-v09.md), which remains the record of the
> original wording. No verdict and no measured value differs between them.

---

## 6.5 Fault-injection result table

12 fault types × strengths of 1/5/10% × 3 repeats = **108 instances** were run on the development
split, together with 18 sound deltas as the false-positive denominator (all code-generated ·
`make faults` · canonical table `paper/tables/fault_matrix.md`). Each cell is the detection rate of
that layer.

| Fault | Expected layer | L0 | L1 | L2 | L3 | Leakage | T1 | T2 | T3 | First detecting layer | Undetected |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Freshness and integrity | L0 | **1.00** | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | L0 | 0/9 |
| Structure (required property missing) | L1 | 0.00 | **1.00** | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | L1 | 0/9 |
| Logic (cycle, type contradiction) | L2 | 0.00 | 0.11 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — | 8/9 |
| Function (CQ path deleted) | L3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — | 9/9 |
| Semantic-alignment error | T1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — | 9/9 |
| Hierarchy flattening | T1 (+L3) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — | 9/9 |
| Judgment-context substitution | T1 · T2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — | 9/9 |
| Metadata deletion | T1 (weak) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — | 9/9 |
| Temporal leakage | L0 / leakage audit | 0.00 | 0.00 | 0.00 | 0.00 | **1.00** | 0.00 | 0.00 | 0.00 | Leakage | 0/9 |
| qrel edge leakage | Leakage audit | 0.00 | 0.00 | 0.00 | 0.00 | **1.00** | 0.00 | 0.00 | 0.00 | Leakage | 0/9 |
| **Synonym mis-merge (cross-task)** | T3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.67 | 0.00 | 0.00 | **0.00** | Leakage | 3/9 |
| **Shared-hierarchy inversion (cross-task)** | T3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** | — | 9/9 |

**H1 was rejected.** Of the three decision criteria, only the false-positive rate was met.

- **Detection of cross-task faults by T3 alone: 0/18.** T3 detected neither cross-task fault in any
  instance.
- **McNemar (paired by fault, L0–L3 detection vs T-gate detection): b=19, c=0, p<.0001 (exact
  binomial).** Significant, but **in the direction opposite to the hypothesis**. The T-gate caught
  nothing that formal validation missed, whereas formal validation alone caught 19.
- **False-positive rate 0/18 = 0%** (meets the ≤5% criterion). Neither kind of sound delta — a
  subset of an actual merge delta, and a meaning-preserving enrichment — was rejected at any layer.

The cause is identified at three layers, and all three lie in **the resolution of the resource the
gate stands on** rather than in the gate **design**.

1. **L2 has no detection surface.** The SDKB T-Box contains **not one** `owl:disjointWith` or
   cardinality constraint (measured). An injected type contradiction is not a logical contradiction.
   Even the single detection came from L1, not L2.
2. **L3 and T3 are existence checks.** **26 of the 28 CQs carry `expect-min: 1`**, so they ask only
   whether any result row exists. A fault must drive a CQ **to 0 rows** to fire, so a local fault at
   1–10% strength passes in principle.
3. **The margin of T1 is wide.** T1 compares the faulted P1 against the sound B3, so a fault must
   consume the entire ontology gain (+0.042) and exceed \(\varepsilon=0.02\) on top of it. Under a
   10% semantic-alignment error the measured gain fell only from +0.042 to +0.032.

### 6.5.1 Diagnosis — what would have been caught with finer-grained CQs (T3′ · exploratory)

To separate whether cause 2 above is a limit of the gate structure or of CQ resolution, we computed
a proxy indicator T3′ that looks at **a drop in the number of CQ result rows** rather than at
pass/fail. This diagnosis was preregistered **before the fault results were seen** (PLAN-020 §5-1)
and does not enter the gate verdict.

| Fault | T3 detection | **T3′ row-count drop** | Cross-task CQs that dropped |
|---|---:|---:|---|
| Structure (required property missing) | 0/9 | **9/9** | CQ02, CQ04, CQ05 |
| Function (CQ path deleted) | 0/9 | **9/9** | CQ01–CQ07, CQ12, CQ15, CQ21 |
| Semantic-alignment error | 0/9 | **9/9** | CQ02, CQ03, CQ06 |
| Hierarchy flattening | 0/9 | **9/9** | CQ21 |
| Metadata deletion | 0/9 | **9/9** | CQ05, CQ08, CQ13 |
| Temporal leakage | 0/9 | **4/9** | CQ03, CQ06 |
| **Synonym mis-merge (cross-task)** | 0/9 | **6/9** | **CQ18 (expert matching), CQ23** |
| **Shared-hierarchy inversion (cross-task)** | 0/9 | 0/9 | — |
| Two kinds of sound delta (false-positive denominator) | 0/18 | **0/18** | — |

**Fault detection 55/108, false alarms on sound deltas 0/18.** With the same CQ suite, the same
faults and the same strengths, changing only the decision resolution detects more than half. The
cross-task synonym mis-merge in particular drives the response row count of the **expert-matching CQ
(CQ18)** down in 6/9 — the path posited in §4.10 does exist, and the binary pass decision of the
current CQs was swallowing it. The cause of the T3 failure is therefore not the cross-task condition
itself but **that a CQ asks about existence and not about distribution**. The remedy is the CQ
refinement of Appendix F, and this table is the first quantitative evidence for its expected effect.
Re-running after refinement is registered as W4b (§11).

**Shared-hierarchy inversion is not caught even by T3′.** Inverting the direction of
`hasSubprocess` preserves the row count of CQ21, because the hierarchy query does not check
direction. This is a separate deficit that CQ refinement alone does not close; a directionality
constraint must be stated in SHACL or in the CQ.

**A specificity problem in the leakage audit (an unfavorable result).** The synonym mis-merge was
detected at the leakage layer at a rate of 0.67, and this is not real leakage. Merging concepts
raises the probability that the concept set of a query contains the concept set of a ground-truth
document, which pushes indicator G-3 (copied concept pairs of the ground truth) past its baseline.
G-3 was designed to catch temporal and qrel leakage but **is not specific to leakage**. The verdict
of this layer should be read with weight on G-1 (whether a document was placed in a concept slot;
specificity confirmed).

### 6.5.2 Carrying out the remedy — the CQ decision was refined and adjudicated again (v2 · H1′)

The diagnosis of §6.5.1 identified a remedy, and Appendix F had announced that remedy ("re-run after
CQ refinement") **before** the fault injection. This section is the result of actually carrying it
out. The decision rule was frozen before results were seen (PLAN-021), and the rule itself is as
follows.

\[
\text{pass}_{v2}(i) = \underbrace{[\,\text{rows}_i \ge \text{expect-min}_i\,]}_{\text{v1 existence check}} \wedge \neg\,\text{regress}_i,\qquad
\text{regress}_i =
\begin{cases}
\text{rows}_i < (1-\tau)\,\text{base}_i & (\text{monotone: up})\\
\text{rows}_i > (1+\tau)\,\text{base}_i & (\text{monotone: down})
\end{cases}
\]

\(\tau=0.05\) is the primary value, and the entire frozen grid \(\tau \in \{0, 0.05, 0.10\}\) is
reported. **The assignment of CQs to suites (pa 5 · em 6 · tf 5 · core 12) did not change** — what
changed is the decision rule, not the assignment, and the denominator of T3 remains {em, tf, core}.

**Why polarity (`# monotone:`) was declared on all 28.** CQ03 (uncovered process steps) and CQ06
(concepts with no recent filing) are **gap-finding queries**, for which fewer result rows means
better coverage. Judging "fewer rows = regression" without polarity would trip the gate on a
legitimate enrichment. This correction has a price, stated before execution: the 4/9 detections that
temporal leakage earned in §6.5.1 all came through CQ03 and CQ06, and they disappear in v2.

**The faults were not re-injected.** Only the decision rule changed, so the 126 isolated fault
graphs were read and adjudicated again, and L0, L1, L2, leakage, T1 and T2 inherited the stored
values of the same instances. This makes the comparison paired on the same instances and the
McNemar test legitimate. The only new injection is the nine N03 sound deltas that enlarge the
false-positive denominator.

| Decision criterion | v1 (preregistered) | **v2 (τ=0.05)** |
|---|---:|---:|
| T3 detection (108 fault instances) | 0/108 | **34/108** |
| L3 detection | 0/108 | **34/108** |
| Undetected fault families | 8/12 | **5/12** |
| T3 detection of cross-task faults | 0/18 | **6/18** |
| **Detection of cross-task faults by T3 alone** | 0/18 | **0/18** |
| McNemar (L0–L3 vs T-gate) | b=19, c=0, p<.0001 | **b=14, c=0, p=.0001** |
| False positives (27 sound deltas) | 0/18 | **1/27 = 3.7%** |

**The diagnosis that decision resolution was the cause is confirmed.** T3 recovered from 0 to
34/108, and the newly detected fault families are six: structure, logic, function, hierarchy
flattening, metadata, and synonym mis-merge. **The logical-contradiction fault in particular is
detected 9/9** — L2 (HermiT) is still 0, and the observation of §6.5 that the T-Box carries no
`owl:disjointWith` stands, yet the same fault leaves a trace in the CQ distribution. Injecting a
cycle raises the row count of the gap-finding queries, and the `down` polarity catches that increase
as a regression; the measurement shows that polarity declaration works in both directions. The
cross-task synonym mis-merge is likewise detected 6/9 through the expert-matching CQ (CQ18), as
announced.

**H1′ is nevertheless rejected. And the reason for the rejection differs from v1 — that is the
substance of this section.**

**Instances where T3 fires and L3 does not number 0 at all three values of \(\tau\)** (verified
across all 135 instances). This is not chance but a consequence of the layer definitions. L3 looks
at a drop in the **number of CQs passing across all suites (pa included)**, and T3 looks at a drop in
the pass rate of its subset {em, tf, core}. If any cross-task CQ regresses, the overall pass count
falls with it, so **`L3 ⊇ T3` holds structurally**. The decision form of H1, "a cross-task fault is
detected **by T3 alone**", therefore cannot be met however finely the CQ suites are refined.

**What was rejected is not the usefulness of T3 but the design of the decision criterion of H1.**
This did not surface in the v1 measurement (0/108), because neither layer caught anything and the
containment was invisible. Narrowing L3 to the focal-task suite would immediately produce detections
by T3 alone, but that would be changing the definition of a decision layer after seeing the result,
so it is not done here. It is registered for the next preregistration, and only the observation and
its implication are recorded here. The practical implication is clear: **in a layered defence the
value of T3 lies not in "does it catch something alone" but in "what does it point to".** T3 states
which task's specification regressed, whereas L3 states only the total.

**An unfavorable measurement — v2 blocks a legitimate duplicate merge.** To enlarge the
false-positive denominator we added a sound delta N03 (merging fully duplicate individuals, whose
triple sets excluding the IRI are identical on both outgoing and incoming edges). This is a
legitimate change that real curation performs, and no layer should reject it. Yet 1/9 were rejected
at \(\tau=0.05\) and 3/9 at \(\tau=0\) (CQ17, the material–problem–expert query, and CQ12, the
problem–process–equipment–expert query). Merging duplicate individuals removes the combination rows
that passed through them — those rows were spurious rows created by the duplication, so no
information is lost — and a decision that looks only at row counts reads that as a regression.
**v2 cannot distinguish the reason rows fell.** This is a principled limit of a distribution check,
and the remedy is not to raise \(\tau\) (detection power collapses) but to declare deduplication as
a delta type and exempt it.

| \(\tau\) | T3 detection | L3 detection | False positives | Detection by T3 alone |
|---:|---:|---:|---:|---:|
| 0.00 | **55/108** | 64/108 | 3/27 (11.1%) | 0/18 |
| **0.05 (primary)** | 34/108 | 34/108 | 1/27 (3.7%) | 0/18 |
| 0.10 | 18/108 | 20/108 | 1/27 (3.7%) | 0/18 |

**Detection power and false positives are in direct conflict.** \(\tau=0\) reproduces exactly the
55/108 of the T3′ diagnosis in §6.5.1 but exceeds the preregistered 5% false-positive criterion,
while \(\tau=0.10\) keeps false positives low at the cost of detection falling to 18. That the
frozen primary value 0.05 lies between them is the result of a prior choice and not of post-hoc
optimization, and all three grid values are reported so that this can be verified.

**Shared-hierarchy inversion is not detected by v2 either.** As §6.5.1 identified, the absence of a
directionality constraint is a separate deficit unrelated to decision resolution, and it must be
closed by SHACL directionality and acyclicity constraints (not executed).

**The status of this section.** v2 was designed **after** seeing the T3′ diagnosis (55/108). The
expected effect was measured first and the rule was then changed to match, and the same data were
adjudicated again. This is therefore not confirmatory evidence but **a post-hoc redesign test
(H1′)**, and the rejection of the preregistered H1 is not retroactively altered (Table 7.1).
Confirmation of v2 must be carried out on new data in the next generation of deltas.

### 6.5.3 The layer definitions were separated and adjudicated again (L3 ⊥ T3 · H1″)

The deficit identified by §6.5.2 was not decision resolution but **the layer definition**. This
section reports the result of correcting that definition and thereby making H1 testable for the
first time. The revised rule was frozen before execution (PLAN-022 · commit `44f8022`, separate
from the result commit).

**The revision.** The detection surface of L3 is narrowed to **the focal-task suite (pa)**. T3 was
not altered by one character — there is a single manipulated variable.

$$\text{old}: \ L3=\{pa,em,tf,core\}(28) \supseteq T3=\{em,tf,core\}(23) \qquad \text{new}: \ L3=\{pa\}(5) \perp T3=\{em,tf,core\}(23)$$

**That this revision does not weaken the gate must be established first.** The union of the two sets
remains all 28 CQs after the revision and the acceptance rule is a product (§4.9), so a failure
anywhere is a rejection regardless of which layer owns it. What changes is not detection power but
**attribution**. Rather than asserting this, we checked it per instance: **violations of
`L3_all ⟺ L3_pa ∨ T3` are 0 across all 144 instances**, at all three values of τ (Table 6.5c). There
is no case in which a delta rejected before the revision is accepted after it. For the same reason
`make cq` in CI keeps its exit code as the product over all 28 and only displays the layer
attribution — narrowing the exit code to pa as well would turn a cross-task CQ failure of
`mini_graph` into a pass and break this invariant.

**The revision is also the semantically correct one.** T3 is by definition "non-regression of
**cross**-task CQs", and regression of the focal task is handled statistically by T1 (§4.9). By the
same logic, **functional** validation of the focal task belongs to L3. That L3 counted all suites in
the old definition is a residue of the definition that preceded the T-gate.

**Results.** Without re-injecting faults, the 135 isolated instances plus 9 new ones (N03A, below)
were re-adjudicated, 144 in total (57.5 seconds).

| Decision criterion | Old attribution (§6.5.2) | **New attribution (L3 ⊥ T3)** |
|---|---:|---:|
| Violations of the detection-power invariant | — | **0/144** |
| L3 detection (117 fault instances) | 43/117 | **11/117** |
| T3 detection | 43/117 | **43/117** (unchanged) |
| T3 detection of cross-task faults | 6/18 | **6/18** |
| **Detection of cross-task faults by T3 alone** | 0/18 (impossible by definition) | **5/18** |
| McNemar (L0–L3 vs T-gate) | b=14, c=0 | **b=14, c=27, p=.0609** |
| False positives (27 sound deltas) | 1/27 = 3.7% | **0/27 = 0%** |

**All three conditions of H1″ are met** — (i) detection by T3 alone 5/18 > 0; (ii) the McNemar
direction favors the T-gate (c=27 > b=14, whereas the H1 measurement had c=0, the exact opposite);
(iii) false positives 0/27 < 5% (across the whole τ grid). That is, **when the layers are made
disjoint, the T-gate does catch regressions that the formal layers miss.** The status of this result
is nevertheless restricted below.

**A remedy included with it — exemption for deduplication.** In response to the unfavorable
measurement of §6.5.2 (a legitimate duplicate merge rejected at 11.1% when τ=0), we made the delta
declare its type and made **the data verify that declaration**. Only when `delta_type=dedup` and the
outgoing and incoming edge signatures of every removed individual are exactly those of the retained
individual is **the distribution check alone** exempted (the existence check is not exempted — a
duplicate merge cannot drive a CQ to 0 rows). The point is that no person judges legitimacy. The
result is **0/27** false positives, and 0 across the whole τ grid. Exemptions are logged and their
count is reported in Table 6.6.

**We measured the hole the exemption opens (N03A).** The exemption is per delta, so declaring
`dedup` and hiding a non-identical pair inside it could slip past the distribution check. We
injected that scenario as a fault (merging same-class pairs with mismatched signatures, 9
instances). Automatic verification **refused the exemption in 9/9**, and the faults, returned to
ordinary delta status, were **detected 9/9**. This fault begins with N in its name but is a fault
and is not counted in the false-positive denominator — merging individuals with different signatures
does destroy information.

**Four unfavorable measurements.**

1. **Shared-hierarchy inversion (F12) is caught by no layer — 0/9, with not one CQ regressing.** Of
   the two cross-task fault families, T3 catches only the synonym mis-merge, and the 5/18 of H1″
   comes entirely from there. The absence of a directionality constraint is a deficit independent of
   decision resolution and layer definition, and must be closed by SHACL directionality and
   acyclicity constraints (not executed).
2. **At τ=0.10 detection by T3 alone collapses to 0/18.** The conclusion holds at only two of the
   three frozen grid values (0 and 0.05). The primary value 0.05 was chosen in advance, but the
   sensitivity of the conclusion to τ must be read alongside it.
3. **The additional discriminative power of T3 is not specific to cross-task faults.** Decomposing
   the instances detected by T3 alone gives logical contradiction 8/9, hierarchy flattening 6/9, CQ
   path deletion 4/9 and metadata deletion 3/9, so **non-cross-task faults are the majority**. Much
   of what T3 additionally catches arises not because a fault is cross-task but because **the five
   pa-suite CQs are insensitive**. This confounding is not resolved while claim-level decomposition
   of the prior-art CQs remains unexecuted.
4. **L3 detection of the focal-task-targeting fault (F04) weakened from 6 to 2.** This was announced
   before the revision. Deleting `skos:prefLabel` touches only CQ16 (material incompatibility) in
   the pa suite; the rest went through cross-task CQs. As L3 narrows, the resolution of the pa CQs
   must carry that narrower surface.

**The status of this section — a third adjudication.** H1 (v1) → H1′ (v2) → H1″ (layer separation)
**adjudicate the same fault data three times**, and what prompted the idea of separating the layers
was the result of §6.5.2. The two arguments above (invariance of the union is arithmetic; the
division of roles is a citation of §4.9) are independent of the result, but concealing that order
would make this indistinguishable from p-hacking. H1″ is therefore **exploratory**, and the
rejections of the preregistered H1 and H1′ are not retroactively altered (Table 7.1). What this
result does in the paper is not to confirm but to serve as **the design rationale of the revised
gate**; confirmation must be carried out on new data in the next generation of deltas.

### 6.5.4 Confirmation on holdout faults (H1‴)

The conclusion of §6.5.3 was **exploratory**, because it was the third adjudication of the same
fault data. This section reports its replication on fault instances that had never been adjudicated,
**without altering the decision rule by a single character**. There is no manipulated variable; only
the data changed. The preregistration was frozen before execution (PLAN-025 v2 · commit `a474126`,
separate from the result commit; the decision rule, the stopping rule, the expected results and the
narrative path in case of rejection are all contained in that commit).

**Composition of the holdout — two axes.** (i) **Replication**: the existing cross-task fault
families (F11 synonym mis-merge, F12 shared-hierarchy inversion) are injected afresh at new repeats
rep ∈ {3,4,5}. Because the seed is `sha256(fault, strength, repeat)`, a different rep gives a
different fault graph, and a regression test enforces that these do not overlap the rep ∈ {0,1,2} of
the first round. (ii) **Generalization**: **three new cross-task fault families** were designed —
hub concentration of expert-competence edges (F13 · four predicates pooled, N=1,283), relocation of
expert-case to failure-mode links (F14 · N=105), and inversion of the supply relation in the value
chain (F15 · two predicates pooled, N=46). 27 sound deltas (N01–N03 × 3 strengths × rep {3,4,5})
form the false-positive denominator. In total **72 instances** (injection 1,241 s · re-adjudication
31 s · development split only; the confirmatory split was not opened).

**Cross-task character is secured by construction, not by the result.** The cross-task fault
families of the first round were labeled by the **expectation** that they would be harmless to
retrieval and touch only another task. The three new families replace that expectation with a
verifiable property: the manipulated predicates have an **empty intersection** with the 20
predicates referenced by the focal-task (pa) suite CQs, and that list is extracted statically from
`queries/cq/*.rq` rather than from a document, with a test enforcing it. All three **preserve the
edge count** (they either change objects within the same type signature or invert direction only),
and every manipulated predicate exists in the upstream SDKB. We also declared the detectability at
L0–L2 before execution: the 14 files of the snapshot contain **0** `owl:disjointWith`, so L2 cannot
in principle catch a direction inversion, and `providedBy` and `madeBy` carry no SHACL constraint at
all. Discovering this afterwards would be an excuse rather than a finding.

**Results.**

| Decision condition (preregistration §3.4) | Measurement | Verdict |
|---|---:|:--:|
| (i) Detection of cross-task faults by T3 alone ≥ 1 | **12/45** (T3 detection 16/45 · L3 detection 2/45) | Met |
| (ii) One-sided McNemar (L3 vs T3 · direction prespecified) | b=0 · c=14 · **p=.0001** (exact test) | Met |
| (iii) False-positive rate ≤ 5% | **0/27 = 0%** | Met |
| **H1‴** | | **Supported** |

By fault family, F13 is 6/9 (all by T3 alone; 0/3 at 1% strength and 3/3 at each of 5% and 10% —
monotone), F11 is 6/9 (2/9 by T3 alone), F14 2/9, F15 2/9 (both at 10% only, all by T3 alone), and
F12 0/9. The cross-task CQ that regressed points to a different place in each family — F13→CQ11
(process and skill experts), F11→CQ18 (patents by skill), F14→CQ28 (patent–failure mode–expert),
F15→CQ13 (value-chain vendor portfolio). T3 therefore states not "something broke" but **which
specification of which task broke**.

**We compare against the expectations written in advance** (we had committed not to revise them if
they missed). Five of five held: F13 and F14 are caught at T3 (em); F15 is caught more readily than
F12; false positives 0–1; the proportion detected by T3 alone is at the level of the first round
(first round 5/18 = 27.8% vs holdout 12/45 = 26.7%); and at low strength F14 may be asymptomatic
because only one edge is relocated (measured 0/3). That an expectation held is not evidence in
itself, but it is grounds for saying that the decision rule was not tuned to two particular faults.

**Four unfavorable measurements — what this result does not confirm.**

1. **It is rejected at τ=0.10.** Across the three frozen grid values, detection by T3 alone is 17/45
   (τ=0), 12/45 (τ=0.05) and **4/45** (τ=0.10), and the McNemar at τ=0.10 gives p=.3438. **The same
   direction of fragility** as in §6.5.3 reproduced in the holdout: the conclusion depends on the
   prior choice of τ=0.05 as primary. That the primary value was not chosen after seeing results is
   all this experiment can defend, and the fact that the threshold of a distribution check governs
   the gate conclusion remains.
2. **Shared-hierarchy inversion (F12) is again 0/9.** Not one CQ regressed in the new repeats either.
   The new fault on the same axis (F15, direction inversion) was caught 2/9, however, so the deficit
   narrows from "direction inversion is asymptomatic in principle" to a query-level problem: **CQ21
   reads `hasSubprocess` without fixing direction**. The remedy is a SHACL directionality constraint
   and fixing the direction in CQ21 (neither executed).
3. **It does not answer the question of specificity.** All 12 instances detected by T3 alone in this
   holdout are cross-task faults, but that is **because non-cross-task faults (F01–F10) were not
   placed in the denominator** (they do not enter the decision rule and were not re-injected;
   prespecified in §3.3 of the plan). The unfavorable measurement 3 of §6.5.3 — that non-cross-task
   faults make up much of the additional discriminative power of T3 — is not refuted by this
   experiment and stands.
4. **Only 70% of the intended manipulation of F13 actually moves.** Preserving the edge count forces
   a rewiring to be skipped when its result coincides with an existing triple (RDF is a set, so
   remove-plus-add erases an edge). Measured collision skips by strength are 4/13, 21/64 and 38/128.
   The alternative (allowing collisions) would change the character of the fault from "distribution
   distortion" to "deletion" and move its target layer, so it was not taken. The detection rate of
   F13 includes this truncation.

**The status of this section — confirmation, but within the scope of the preregistration.** H1‴
confirms one proposition: **in a T-gate whose layers are defined disjointly, T3 catches cross-task
regressions that focal-task monitoring (L0–L3, T1, T2, the leakage audit) lets through** — on 45
faults never adjudicated before, under a prespecified one-sided test, with zero false positives.
What it does not confirm is the **completeness** of the gate (F12 is still caught by no one) and the
**specificity** of T3 (point 3 above), and the τ sensitivity of the conclusion also stands. The
rejections of H1 and H1′ and the exploratory status of H1″ are not retroactively altered
(Table 7.1).

## 6.6 CQ pass rates by generation

The pass rates of the three CQ suites are published per enrichment generation so that the history of
T3 and any gate-induced drift can be verified.

| Enrichment generation | Decision rule | CQ-PA | CQ-EM | CQ-TF | CQ-CORE | Claim layer (measurement) | T3 verdict | Waivers |
|---|---|---:|---:|---:|---:|---:|---|---:|
| g0 | — (reference generation) | 0.800 (4/5) | 1.000 (6/6) | 1.000 (5/5) | 1.000 (12/12) | — (not measured) | — (reference) | — |
| graph_v1 | v2 (τ=0.05) | 1.000 (5/5) | 1.000 (6/6) | 1.000 (5/5) | 1.000 (12/12) | — (not measured) | **accepted** (0 drop) vs g0 | 0 |
| g0_cq31 | — (reference generation) | 0.800 (4/5) | 1.000 (6/6) | 1.000 (5/5) | 1.000 (12/12) | 1.000 (3/3) | — (reference) | — |
| graph_v1_cq31 | v2 (τ=0.05) | 1.000 (5/5) | 1.000 (6/6) | 1.000 (5/5) | 1.000 (12/12) | 1.000 (3/3) | **accepted** (0 drop) vs g0_cq31 | 0 |

**Cumulative waivers: 0.** This table is generated, **verdicts included**, from the artifacts
`make cq-freeze` leaves for each generation (`data/cq_generations/`), into
`paper/tables/cq_generations.md`. The actual graph generations are **only two**, the reference
generation g0 and the merged generation graph_v1, so **there is not yet a history worth calling a
trend** — we do not create generations to fill a table. The two rows below (`*_cq31`) are not new
graphs but **the same two graphs frozen again after the claim CQs were incorporated (the 31-question
regime)** (§9.7). The earlier two rows were not overwritten because a change in the CQ set changes
the meaning of a pass rate, and erasing them retroactively would remove the historicity that is the
reason this table exists.

**The verdict column of the table is filled by code (corrected 2026-07-28).** In an earlier edition
(the v0.9 draft) the second row of this table was written by hand without a generation artifact, and
the generator was printing a placeholder in the T3 column of non-reference generations — **a manual
entry and a violation of our own discipline in §11**. The correction has two parts. First, the
`graph_v1` generation was actually frozen with `--against g0` so that the verdict lives inside the
artifact. Second, **the generator now raises an exception rather than printing a placeholder when it
meets a non-reference generation without a verdict** — as long as a placeholder is tolerated the
same violation recurs in the next generation — and this contract is pinned by a regression test
(`tests/test_tgate.py::test_table_refuses_placeholder_verdict`). On re-adjudication the hand-written
"accepted (0 drop)" turned out to match the actual result, but **a number without a source is a
defect regardless of whether it happens to match**.

**Three things must be read together.** First, **CQ-PA moves from 0.800 in the reference generation
to 1.000 in graph_v1.** The FTO claim-readiness query (CQ27), which did not respond on G0, responds
for the first time through the claimText axis of G1 (371,267 items, §3.2). This column is the
denominator of L3, not of T3 (§4.9 as revised), and because there are only five focal-task CQs, the
response of a single query is an amplitude of 0.2 — that insensitivity is why claim-level
decomposition remains a prerequisite (§3.1.6, §9.7). Second, **the decision rule is a premise of any
comparison between generations.** v1 (existence check) and v2 (existence ∧ distribution check,
§6.5.2) can give different pass rates for the same graph, so generations may be compared only under
the same rule, which is why the rule version is a column of the table. **The reference generation has
no rule** — regression against itself is 0 by definition, so both rules agree, and that cell is
marked "reference generation". The `graph_v1` row, by contrast, is **a generation merged under the
v1 rule and adjudicated retroactively under v2** (a retroactive move toward the stricter rule, so the
acceptance conclusion is not weakened). Third, **the claim-layer column is a measurement, not a
gate** (§9.7 · PLAN-023 §1) — CQ29–31 query the sidecar and are constant terms unresponsive to the
graph under test, so they are not placed in the denominators of L3 and T3. Had they been, three
always-passing checks would have diluted the pa failure (0.800 → 0.875) and weakened the gate.
Fourth, **the history of deduplication exemptions is also reported by this table** (§6.5.3) — the
same discipline as waivers, since a silent exemption makes the gate ornamental. To date the number
of exemptions used outside the fault-injection experiments is 0.

---


---

## S2.1 The hypothesis verdict table of canonical v0.9 §6.3 (full text, before abridgment)

## 6.3 Hypothesis verdict table

| Hypothesis | Prespecified support criterion | Observation | Verdict |
|---|---|---|---|
| **H1** (discriminative power of the gate) | Paired fault detection rate higher than L0–L3 with McNemar \(p<.05\), false-positive rate on sound deltas ≤5%; the cross-task fault families (synonym mis-merge, hierarchy inversion) pass L0–L3, T1 and T2 and are detected at T3 alone | Detection of cross-task faults by T3 alone **0/18** · McNemar b=19 · c=0 · p<.0001 (**direction opposite to the hypothesis**) · false-positive rate **0/18 = 0%** | **Rejected** (§6.5, §6.5.1) |
| **H1′** (re-adjudication after refinement · **post-hoc redesign, not confirmatory**) | The same criteria re-adjudicated under CQ decision v2 (existence ∧ distribution check, τ=0.05 frozen in advance) | T3 detection recovered from 0/108 to **34/108** (cross-task faults 6/18), yet **detection by T3 alone 0/18** · McNemar b=14 · c=0 · p=.0001 (direction unchanged) · false positives **1/27 = 3.7%** | **Rejected — but for a different reason.** `L3 ⊇ T3` holds by the layer definitions, making detection by T3 alone impossible by definition (§6.5.2). What was rejected is not the usefulness of T3 but the design of the decision criterion |
| **H1″** (re-adjudication after layer separation · **post-hoc redesign, not confirmatory**) | Narrow L3 to the focal-task suite (pa) so that it is **disjoint** from T3, then re-adjudicate the same criteria. Invariance of detection power (`L3_all ⟺ L3_pa ∨ T3`) is a precondition | Violations of the detection-power invariant **0/144** · detection of cross-task faults **by T3 alone 5/18** · McNemar b=14 · **c=27** · p=.0609 (**direction reversed in favor of the T-gate**) · false positives **0/27 = 0%** (deduplication exemption introduced) | **Supported — but exploratory and heavily restricted.** A third adjudication of the same data (§6.5.3). The 5/18 are all synonym mis-merges and hierarchy inversion is 0/9 · detection by T3 alone is 0/18 at τ=0.10 · most detections by T3 alone are non-cross-task faults (low specificity) |
| **H1‴** (holdout confirmation · **decision rule unchanged, data new**) | With the layer-separated definition frozen, on 45 cross-task faults **never adjudicated before** (replication of F11 and F12 × rep {3,4,5}, 18, plus the new cross-task families F13, F14, F15, 27): (i) detection by T3 alone ≥1, (ii) one-sided McNemar (direction prespecified in favor of T3) \(p<.05\), (iii) false-positive rate ≤5%. All preregistered (PLAN-025 v2 · `a474126`) | Stopping-rule violations 0 · detection of cross-task faults **by T3 alone 12/45** · one-sided McNemar b=0 · **c=14** · **p=.0001** · false positives **0/27 = 0%** · axis A replication 2/18 (p=.0625) · axis B generalization **10/27** (p=.0010) | **Supported — confirmatory.** The three preregistered conditions are met (§6.5.4). But **rejected at τ=0.10** (alone 4/45, p=.3438) · F12 is again 0/9 · with no non-cross-task faults in the denominator, **specificity is not tested** |
| **H2** (acceptance safety) | The lower bound of the 95% CI on \(\Delta Recall@100\) > \(-0.02\) **and** the maximum drop in the prespecified major subgroups < 0.05 | Confirmatory split (198 q · frozen delta P1 vs B3 · `make tgate SPLIT=test`): **T1** family R@100 0.4315 → 0.4849, Δ+0.0534, 95% CI [+0.0145, +0.0926] → LB95 **+0.0145 > −0.02**. **T2** no drop on any of the three axes (maximum drops −0.0140 pos_lang, −0.0584 proc_group, −0.0310 rejection, all below δ=0.05). **T3** 0 drop on em, tf and core. **Accept(ΔG)=1** | **Supported** — but what was tested is **the acceptance safety of one frozen delta**, not the discriminative power of the gate (that is H1, §6.5). The process-family axis rests on thin evidence, as it has **only one** trusted subgroup with n≥20 |
| **H3** (hybrid effect) | P0 or P1 improves on B3 in both R@100 and nDCG@20 (significant after correction), and the improvement in the low-overlap subgroup exceeds that in the high-overlap subgroup | test (198 q · family R@100): P1 Δ+0.0534, 95% CI [+0.0145, +0.0926], p=0.008 (significant); concepts alone Δ+0.0584, p=0.002. The prespecified primary P0★ (concept+ipc) gives Δ+0.0319, p=0.181 (not significant — the IPC weight overfits dev). **nDCG@20 does not improve**: P1 Δ−0.0176 (p=0.227), P0★ Δ−0.0395 (p=0.029, a significant deterioration). **The low-overlap clause is contradicted**: under the F11 frozen threshold (dev Q1=0.0079), low Δ−0.0586 (n=27, p=0.448) < high Δ+0.0711 (n=171, p=0.000) | **Partly supported — confined to the primary outcome** (R@100 improves on P1 · **the nDCG clause is not met** · the primary P0★ is not significant · the low-overlap clause is contradicted) |
| **H4** (layer contribution) | The removal loss of A4/A5 exceeds that of A1 and of bibliographic removal | test: the removal loss of A4 (−ClaimFeature) +0.0070 and of A5 (−rejection ground) 0.0 do not significantly exceed that of A1 (−CPC/IPC) +0.0025 (all n.s. under Holm m=8). The ClaimFeature layer makes no independent contribution | **Rejected** |
| **H5** (specificity — negative control) | The \(\Delta R@100\) of A8 (removal of the expert-matching layers) is not significant | test: removal loss of A8 ΔR@100 +0.0316, 95% CI [+0.0105, +0.0560], p=0.002 (the only one significant under Holm) — **retrieval significantly degraded** | **Rejected → cross-task entanglement observed** (the negative control framing is abandoned; the need for T3 is strengthened; §7.3) |

**Two honest reports concerning H2.** First, the delta used in the verdict is the single ΔG
(P1 vs B3) frozen when the T-gate was introduced. **The prespecified primary retrieval system P0★
was put through the same gate** (`tgate_report_test_p0star.json`), and the result is likewise
acceptance, but **the margin is thin**: T1 LB95 is **−0.0139**, only just above the margin of −0.02,
and T2 shows **an actual drop (+0.0118)** in the subgroup whose positives include a foreign language
(it passes because it is below δ=0.05). Non-inferiority is not superiority, so this acceptance does
not contradict the failure of P0★ to reach superiority (§6.2, p=0.181). To avoid putting only a
favorable delta through the gate, we froze the decision to report both verdicts together before
results were seen (PLAN-024 §1). Second, **the trusted subgroups of T2 are thin.** In the
confirmatory split of 198 queries, the subgroups exceeding `n≥20` number two on the language axis,
two on the rejection-ground axis and **one** on the process-family axis. The safety of the process
family is in effect the observation of a single subgroup, and we do not claim from it that process
families in general are safe.

Apart from the confirmatory hypotheses, the following three items are reported as exploratory
analysis and are not included in the claims of the conclusion.

| Exploratory analysis | Observation | Value |
|---|---|---|
| Operational efficiency | Reduction in the number of candidates reviewed, or in review cost, at the same R@100 | **Not performed** — Candidate Reduction was not computed. Stage cost was measured (rerank p95 ≈ 30 ms · Table 6.2e) |
| Signal by rejection type | Explanatory power of single-reference coverage for novelty and of set coverage for inventive step | **Not testable** — the resource contains 0 rejections on novelty alone (of 1,000 records, all 14 novelty citations co-occur with inventive step; n=3 in the confirmatory split). §6.4, §8.1 |
| Semantic reachability | Relation between the semantic-reachability subgroup and the size of the hybrid effect | **Not performed** — no stratification by reachability resolution was carried out. On the proxy axis of lexical overlap, **the gain concentrates in the high-overlap subgroup** (§6.4) |

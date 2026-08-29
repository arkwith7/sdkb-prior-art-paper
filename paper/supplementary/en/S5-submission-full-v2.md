# S5 · Cited material from the pre-abridgment full text (English)

> **What this file is.** The manuscript cites S5 in 25 places for material that was moved out of the
> body during abridgment. This file carries **those cited items in English**, so that a reader of
> the English manuscript can reach every piece of evidence it points to.
>
> **What this file is not.** It is not a translation of the whole Korean S5. That file
> ([S5-submission-full-v2.md](../S5-submission-full-v2.md)) carries the same cited material in
> Korean, together with the exploratory re-readings and the verdict records that the manuscript
> cites only in Korean; where a section below states that further material exists, it is there.
> The unabridged pre-excerpt edition, from which both files were cut, is kept as the complete
> original at
> [paper/archive/S5-submission-full-v2-pre-excerpt.md](../../archive/S5-submission-full-v2-pre-excerpt.md). Nothing here is created: every
> value and every verdict is carried over from that record, and a machine check
> (`make supplementary-check-en`) verifies that the measured values of the two files agree.
>
> **Where each citation lands.** §2.4 → §1 · §3.3 → §2 · §5.3 → §3 · §4.3 → §4 · §4.5 → §5 and §10 ·
> §4.4 and §5.4.2 → §6 · §5.4.1 → §7 and §8 · §5.4.3 → §9 · §6.3 → §11 and §13 · §6.4 → §12, §14
> and §15 · §3.5.1 and §6.4 (transfer) → §16.

---

## 1. Position relative to prior work

Cited from §2.4 of the manuscript.

| Research strand | Gap that remains | What this study adds |
|---|---|---|
| Patent text retrieval | No explicit domain semantics and no validation of graph evolution | Couples the semiconductor ontology hierarchy into candidate generation and reranking |
| Citation and KG retrieval | Query-citation leakage and the problem of controlling change | Masks the query edges and separates by time and family |
| Cross-lingual patent retrieval | The channels are limited to translation and multilingual embeddings | Sets the language-neutral concept IRI as a third channel and decomposes recall by the language of the ground truth (exploratory · §9) |
| Ontology validation | Does not guarantee ranking quality or freedom from cross-task regression | A three-condition T-gate and a non-inferiority merge rule |
| Downstream evaluation of KGs | Stops at post-hoc comparison and is not an acceptance gate | Converted into a pre-release acceptance gate |
| Task-based ontology evaluation (Porzel & Malaka, 2004; Brank et al., 2005) | Used as a **criterion for choosing** among ontologies, not as a **condition for accepting a change** to one | Uses the same task performance as a term in the pre-merge acceptance rule |
| The practice of using resource quality indicators as a **proxy** for utility (coverage, link completeness, concept density) | Misalignment is reported only at the level of correlation (Chiu et al., 2016; Heist et al., 2023); **a controlled case and a decision taken on it** are rare | The measurement in which a 2.4-fold improvement of resource indicators produced a retrieval drop in two arms with documents and settings fixed and only the resource replaced, and the rejection verdict on it |
| Domain ontology datasets | Confuse multi-task representation with single-task performance | States the three task views, the asymmetric validation, and T3 monitoring |

Rather than claiming primacy, the contribution is placed in this combination and in the
experimental design.

---

## 2. The reachability ladder — definitions per level and derivation

Cited from §3.3 of the manuscript.

How far the ground-truth resource **reaches into the graph** varies greatly with the resolution at
which it is viewed.

| Resolution | Definition | Reachability |
|---|---|---:|
| Node reachability | The distinct targets of `hasPriorArtExaminer` exist as graph nodes | 2,211/2,321 = 95.3% |
| Process ∪ Device semantic reachability | The cited document connects through a process or device concept | 54.6% |
| + Material semantic reachability | Material concepts added to the above relations | 63.4% |
| + all semantic links | Domain semantic relations such as competence, failure and equipment added | 70.5% |
| + CPC/IPC classification reachability | Classification codes added to the semantic links | 95.3% |
| ClaimFeature reachability | On the sample with a judgment link, prior art connects at the feature level | 402/584 = 68.8% |

Examiner citations number 2,534 in all, of which 30 are non-patent literature. 2,321 is the number
of **distinct patents** that `hasPriorArtExaminer` points to. **2,534, 2,321, 2,211 and 584 are
different denominators and are never mixed into a single "number of positives".**

The difference is itself a measurement problem. Reporting only the high values at the node and
classification levels **inflates semantic retrieval readiness**. Conversely, treating the 68.8% of
ClaimFeature as a property of all 1,000 queries **generalizes from a rich subset to the whole**. The
study therefore uses, as the basic unit of resource reporting, a **reachability ladder** — a table
that records level by level how far the resource reaches — rather than a single number.

**The ladder stands differently in different languages.** Rebuilding the same ladder by document
language exposes the gap in readiness (artifact `paper/tables/ir_crosslingual_test.md` §2). The
proportion of candidate documents holding a concept link is 99.2% for Korean, against 69.6% for
English and **0% for Japanese**. Concepts per document, counted on the examiner-cited ground-truth
nodes, is 2.32 for Korean against 1.51 for English. Only classification (IPC) coverage is the same
at 100% in all three languages. The text resource itself is not homogeneous either: the median body
length of English positives is 1,103 characters and of Japanese 117, which is effectively
bibliographic information. That is, a "language-neutral concept IRI" is a property of the T-Box
level, and **at the A-Box level fewer concepts are attached to non-Korean documents.** This asymmetry
is the premise for interpreting the cross-lingual recall results of §9 and identifies the next target
for concept enrichment.

**The commands that reproduce the ladder** are in the Korean record; the qrel grades that feed it
are three (grade 2, a `PriorArtJudgment` linking a specific claim to a specific prior document with
the novelty or inventive-step ground identified; grade 1, a patent-level `hasPriorArtExaminer`
relation only; unobserved, no examiner citation relation, which is **not** fixed as a negative).
**Grade 2 does not mean legally more relevant than grade 1** — the grade states only how fine the
evidence observed in this data is.

---

## 3. The three task views in the T-Box

Cited from §5.3 of the manuscript.

The TTL files of the repository contain, for expert matching, `Problem`, `RootCause`,
`FailureMode`, `Mitigation`, `Skill`, `Expert`, `ExpertCase` and the equipment, material and company
classes with their relations. For prior-art search they contain the patent status classes, `Claim`,
`ClaimFeature`, `PriorArtJudgment`, `Rejection`, `ClassificationSymbol` and `NoveltyScore`, together
with the examiner and applicant citation relations and the claim-judgment relation. For technology
foresight they contain `TechnologyNode`, `Scenario`, `STEEPVEFactor`, `RealOption`, TRL and RBV, and
the `filingDate` time axis. The scope of the three tasks is therefore **a dataset property
observable in the current T-Box**, not a future design.

In functional validation G0 passes 27/28 of the CQs and G1 and G2 pass 28/28. That result means the
existence of a query path and a non-empty response; it does not mean that expert-matching accuracy,
prior-art relevance ranking or foresight accuracy have all been validated. With that limit stated,
the paper adds quantitative evaluation based on T1 and T2 to the prior-art-search view alone and
connects the other two views through the regression monitoring of T3.

**The claim-feature resource.** A separate claim-feature resource holds 586,567 Claims, 1,289,512
ClaimFeatures, 483,394 `dependsOnClaim` relations and 635 PriorArtJudgments. Feature-level
reachability on the judgment-linked sample is 402/584, or 68.8%. This shows that claim-level
evaluation is feasible but does not say that all 1,000 rejected patents carry the same completeness.

**CQ10 and the difference from retrieval relevance.** CQ10 of v0.7 reports that candidates rose from
8 to 90 under `plasma_etch` with a pre-2015 condition. That is an observation about candidate
generation and the expansion of process links. How many of the 90 candidates are known examiner
citations, at what rank they sit, and whether the uncited candidates are actually relevant were not
measured. CQ10 is therefore diagnostic material showing the need for the T-gate, not evidence of
retrieval performance.

**Cross-task CQ pass rates.** On deltas the gate accepted, the pass rate of the other tasks' CQs did
not fall and **cumulative waivers are 0**. Because the actual graph generations are **only two**,
the reference generation and the merged generation, **there is not yet a history worth calling a
trend**, and we do not create generations to fill a table. The table and the per-generation
artifacts are in [S2](S2-fault-injection-v09.md).

> **A correction in how to read this.** The variation in CQ pass rates observed between G0, G1 and
> G2 is **not the result of the ontology improving**. The T-Box of the three graphs is identical
> (103 classes · 97/81 predicates · delta 0), so the variation comes entirely from **the A-Box being
> populated** — a CQ that returned nothing on G0 comes to respond through the 371,267 claimText
> items of G1, for instance. The numbers of this section must therefore **not be read as evidence of
> generation safety.** What this section shows is one fact, that the other tasks' CQs did not regress
> on the deltas the gate accepted; the proposition "the ontology is safe as it evolves" was not
> tested in this paper, as §6.4 of the manuscript states.

---

## 4. Comparison systems and the proposed ranking function

Cited from §4.3 of the manuscript.

| ID | System | Evidence used | Purpose |
|---|---|---|---|
| B0 | BM25-Claim | Claim vocabulary | Minimal baseline |
| B1 | BM25-Fielded | Title, abstract, claims | Effect of fields |
| B2 | Dense | Document embedding | Semantic-similarity baseline |
| B3 | Text Hybrid | BM25 + Dense (RRF) | **Strongest text baseline** |
| B4 | CPC/IPC | Classification overlap and distance | Effect of the classification signal alone |
| B5 | Ontology-only | Concept paths over process, device, material, equipment and failure | Effect of explicit semantics alone |
| P0 | Text+Ontology | B3 + concept overlap and paths | Core proposed system |
| P1 | +ClaimFeature | P0 + feature coverage | Fine-grained claim semantics |
| P2 | +Ground-aware | P1 + rejection-ground compatibility, within the oracle-free scope | Legal context |

**Practice correspondence and reproduction path of each configuration** — the ranking files come in
three sets per split, `dev`, `test` and `test_b`.

| Configuration | Corresponding stage in practice | Input text | Code module and entry point | Output ranking file |
|---|---|---|---|---|
| **B0** BM25-Claim | Keyword search | Query `claims_independent` · document `text_main` | `retrieval/bm25.py::search` (nori dictionary tokenization) | `sys_B0_bm25_*.txt` |
| **B2** Dense | Semantic search | Same | `retrieval/dense.py::search` (Titan v2 · FAISS flat) | `sys_B2_dense_*.txt` |
| **B3** Text Hybrid | Fusion of the two results | Rank fusion, so it does not read text directly | `retrieval/hybrid.py::rrf` | `sys_B3_rrf_*.txt` |
| **B4** Classification alone | Bibliographic-condition search | Classification symbols | `retrieval/systems.py::build_b4` | `sys_B4_ipc_*.txt` |
| **B5** Concepts alone | No counterpart — the path this study proposes | Concept links | `retrieval/systems.py::build_b5` | `sys_B5_concept_*.txt` |
| **P0★** Text+Ontology | Prioritizing candidates for review | The B3 candidate pool and concepts | `retrieval/systems.py::rerank_p0` | `sys_P0star_*.txt` |
| **P1** +ClaimFeature | Same | The above inputs plus claim features | `analysis/ontology_eval.py::rerank_p1` | `sys_P1_*.txt` |

Each ranking file is scored by `analysis/metrics.py` to become the performance table of §5.4 of the
manuscript, and the ablation and subgroup results derive from the same files.

**Unimplemented configurations.** B1 (BM25-Fielded) and P2 (+Ground-aware) were designed but not
implemented, so no ranking or metric was ever produced for them. They were not excluded because
their results were unfavorable; no value exists to report.

**Why the check is on identity of rankings rather than on file hashes.** A hybrid ranking file is
not byte-reproducible even for identical inputs, so the integrity of the control is verified by
comparing the rankings themselves.

**As-built record of the dense baseline.** B2 is **Titan Embed v2**. The patent-specific encoders
considered at design time (PatentSBERTa, PaECTER) are English-only with short inputs and could not
take Korean long-form queries and documents (2,255 characters) without truncation. The model was
fixed before the development set was opened and was not changed after seeing test results. A
multilingual long-document encoder, which is subject to neither constraint, was added
exploratorily under a separate preregistration after the confirmatory verdicts, and its selection
was carried out on the development split alone.

**The proposed ranking function.** The score of a candidate patent \(d\) is

\[
\begin{aligned}
S(q,d) =\;& w_b\widetilde{BM25}(q,d)
+w_e\widetilde{\cos(e_q,e_d)} \\
&+w_c\,ConceptOverlap(q,d)
+w_h\,PathSim(q,d)\\
&+w_f\,FeatureCoverage(q,d)
+w_r\,GroundCompatibility(q,d)
\end{aligned}
\]

with each term normalized to [0,1] per query.

- \(ConceptOverlap\): weighted Jaccard over process, device, material, equipment and failure concepts
- \(PathSim\): semantic similarity based on the shortest ontology path or on information content
- \(FeatureCoverage\): the proportion of the features of the query's independent claims that the
  candidate covers
- \(GroundCompatibility\): compatibility between the rejection-ground context and the feature
  composition

The weights \(w\) are chosen by a prior grid **on the development set alone**. Optimization using
the test qrel is prohibited. For explanation, each result records not only the final score but also
the per-term contributions and the concepts and features that matched.

**The reranking ceiling.** The proposed systems reorder the top 1,000 of the text baseline and do
not enlarge the candidate set, and the counts behind that ceiling are in the Korean record
(Appendix B of S5, exploratory descriptive statistics).

---

## 5. Metrics and statistics

Cited from §4.5 of the manuscript.

**The primary outcome is family-level Recall@100** — how many known related documents entered the
top 100. In practice an examiner or searcher does not look only at the first few hits but scans to a
fixed depth, so "did it omit anything within that depth" comes before "did it put the best at the
very top". Filings of the same invention in other jurisdictions (a patent family) are counted once
to remove duplication.

\[
Recall@K(q)=\frac{|Rel(q)\cap TopK(q)|}{|Rel(q)|}
\]

The auxiliary metrics are as follows.

- Recall@50, Recall@500
- Success@K: the proportion of queries that found **at least one** related document
- MRR@K: **at what rank the first related document appeared** (mean reciprocal rank)
- nDCG (normalized discounted cumulative gain)@20: on the subset with a graded qrel
- bpref: an indicator that is **less disturbed when the ground truth is incomplete** (Buckley &
  Voorhees, 2004)
- Candidate Reduction: **how far the candidates to be reviewed were reduced** while holding recall
  at the same level
- Median and p95 latency per query, graph-feature generation time, index size and memory use

Precision is not used as a primary outcome. Measuring precision would require **fixing every uncited
document as "not relevant"**, and our ground truth holds only what an examiner actually saw, so that
assumption does not hold. Precision is reported only as an auxiliary value on a sample judged
directly by experts.

**As-built conventions (fixed after execution).** The constructed qrel is entirely grade 1, so the
"subset with a graded qrel" does not exist. Rather than generating grades after the fact, the two
metrics are computed under the following conventions, which are stated in the tables. (i) **nDCG@20
is computed with binary gain.** (ii) **bpref treats retrieved non-positive documents as
non-relevant** — classical bpref requires a judged non-relevant set, which is empty under a
positive-only qrel, making the value always 1 and the indicator vacuous. Both conventions apply
identically to every comparison system, so the validity of comparison between systems is preserved.
Graded evaluation is a follow-up task once the expert judgments of §5.13 of the Korean record are
obtained.

**Readout metrics one layer below (Appendix A · exploratory layer A → confirmatory layer B).** All
of the above belong to the retrieval layer. To see whether the gain of the retrieval layer carries
into the generation layer, four metrics are kept separately — **citation accuracy** (the proportion
of the document identifiers an answer gives as evidence that are in the sealed ground truth),
**hallucination rate** (the proportion of identifiers given that are not in the context),
**evidence-sentence match** (whether a quoted sentence appears verbatim in the source) and the
**proportion of insufficient-evidence declarations**. Neither a person nor another model takes part
in the scoring: all four are **identifier and string comparisons** and therefore deterministic.
Their status differs by layer: in layer A all four are exploratory, whereas in layer B **only
citation accuracy (overall) and the hallucination rate** are the confirmatory metrics used in the
frozen T4 verdict, and the other two are reported only (Appendix A.2). **In neither case are they
placed in the same table as the retrieval results** — they are not retrieval-layer metrics. One
piece of context is carried in the same table: **the mean number of citations per query.** The
denominator of citation accuracy is not the number of queries but **all identifiers cited**, and
citing less raises accuracy by itself, so without the denominator these four cannot be read
(Appendix A).

**Statistical analysis.**

- When comparing systems, they are **paired over the same queries** and resampled 10,000 times
  (paired bootstrap) to give 95% confidence intervals — query difficulty varies, and without
  pairing a difference in difficulty masquerades as a difference in performance.
- A paired randomization test is used as an auxiliary check on Recall@K differences.
- When comparing detection rates between layers, McNemar's test is used, **paired on the same fault
  instance**.
- Because removing one layer at a time involves multiple comparisons, the **Holm correction** filters
  out results that look significant by chance.
- Effect size is reported as the mean difference together with Cliff's delta or the per-query
  win/loss/tie proportions.
- The conditional effect of H3 is estimated as a system × overlap-group interaction on groups split
  by lexical-overlap quartile or by a prior threshold.
- Subgroup results **carry the number of queries and the number of positives**, and no conclusion is
  drawn when the sample is small.

**The lexical-overlap groups.** "Low lexical overlap" was not defined after seeing results. A
character n-gram or morpheme-based Jaccard is computed between the query claims and the claims and
abstract of the qrel documents after stop-word removal, and the lower quartile of the development
distribution is frozen as low overlap. A sensitivity analysis over other tokenizations is provided.

**Freezing record.** The query score is the character 3-gram Jaccard averaged over the known
positive documents of that query, and Q1 = **0.0079** of the distribution over the 197 development
queries was frozen as the low-overlap boundary (median 0.0211, Q3 0.0347). The threshold is pinned
in a file and is not recomputed on re-execution (`data/processed/ir/overlap_threshold.json`); the
same value was applied unchanged to the confirmatory split, dividing it into low 27 and high 171.
This score is an **analysis-only stratification label** and is not fed into the ranking function.

---

## 6. Ablation conditions and the full subgroup and ablation table

Cited from §4.4 and §5.4.2 of the manuscript.

**The eight preregistered ablation conditions.** One layer at a time is removed to measure its
contribution.

| Experiment | Layer removed | Claim under test |
|---|---|---|
| A1 | CPC/IPC | Dependence on classification |
| A2 | Process and device | Core domain concepts |
| A3 | Material, equipment and failure | Adjacent semantic axes |
| A4 | ClaimFeature | Claim features |
| A5 | Rejection ground and judgment | Legal context |
| A6 | Hierarchy paths, keeping only concept overlap | Contribution of the relational structure |
| A7 | All ontology features | Regression to the text-only baseline |
| **A8** | **The expert-matching-only layers (`Skill`, `ExpertCase`, `Mitigation`)** | **Negative control — specificity of the ablation effect (H5)** |

**How to read them.** The more performance falls when a layer is removed, the more that layer
contributed. The prediction of H4 was that the loss from removing A4 and A5 (claim features and
rejection grounds) should exceed the loss from removing A1 (classification codes) or the
bibliographic information. **A8 is different in kind** — it was chosen to be theoretically unrelated
to retrieval, so removing it should leave performance unchanged (H5). We do not assume that every
layer contributes. If the loss from A4 and A5 is small, we examine whether the features were
extracted poorly, whether the sample is skewed, or whether they overlap with other features. And
**if removing A8 markedly degrades performance**, the control framing itself is abandoned and the
result is reported as an observation that the tasks are entangled (§11 below).

**The full table** (test, 198 queries · family R@100 · query-level paired bootstrap 10,000 with seed
20260726 · artifact `paper/tables/ir_subgroup_test.md`).

| Subgroup / removed layer | Queries | qrels | Text Hybrid R@100 | Proposed R@100 | Difference | 95% CI |
|---|---:|---:|---:|---:|---:|---|
| Inventive step only (Art. 29(2)) | 70 | 182 | 0.3802 | 0.4112 | +0.0310 | [−0.0479, +0.1107] (p=0.440) |
| Novelty + inventive step (Art. 29(1) and (2)) ⚠ | 3 | 5 | 0.3333 | 0.3333 | +0.0000 | (n<20 · no firm conclusion) |
| No structured rejection-ground label | 125 | 292 | 0.4627 | 0.5299 | +0.0672 | [+0.0256, +0.1104] (p=0.002) |
| **Low lexical overlap** | 27 | 59 | 0.1975 | 0.1389 | **−0.0586** | [−0.2099, +0.0741] (p=0.448) |
| **High lexical overlap** | 171 | 420 | 0.4685 | 0.5396 | **+0.0711** | [+0.0330, +0.1104] (p<.001) |
| Positives entirely Korean | 98 | 207 | 0.6023 | 0.6959 | +0.0936 | [+0.0295, +0.1579] (p=0.004) |
| Positives include a foreign language | 100 | 272 | 0.2642 | 0.2782 | +0.0140 | [−0.0313, +0.0578] (p=0.518) |
| Process family: process | 181 | 432 | 0.4426 | 0.5010 | +0.0584 | [+0.0161, +0.1006] (p=0.006) |
| Process family: device ⚠ | 13 | 36 | 0.3590 | 0.3846 | +0.0256 | (n<20 · no firm conclusion) |
| −CPC/IPC (A1) | 198 | 479 | — | 0.4824 | +0.0025 | [−0.0259, +0.0300] (p=0.844) |
| −Process and device (A2) | 198 | 479 | — | 0.4997 | −0.0147 | [−0.0396, +0.0101] (p=0.253) |
| −Material, equipment and failure (A3) | 198 | 479 | — | 0.4930 | −0.0081 | [−0.0271, +0.0076] (p=0.392) |
| −ClaimFeature (A4) | 198 | 479 | — | 0.4779 | +0.0070 | [−0.0038, +0.0215] (p=0.271) |
| −Rejection ground (A5) | 198 | 479 | — | 0.4849 | +0.0000 | (structurally 0 under oracle-free) |
| −Hierarchy paths (A6) | 198 | 479 | — | 0.4849 | +0.0000 | (selected weight w_h=0 → structurally 0) |
| −All ontology features (A7 = text only) | 198 | 479 | — | 0.4315 | +0.0534 | [+0.0145, +0.0926] (p=0.008 · n.s. after Holm) |
| **−Expert layer (A8, negative control)** | 198 | 479 | — | 0.4534 | **+0.0316** | **[+0.0105, +0.0560]** (p=0.002 · significant under Holm) |

> **How to read the rows.** Subgroup rows: `Text Hybrid` = B3, `Proposed` = P1, `Difference` =
> P1 − B3 (positive = the proposal leads). Ablation rows: `Proposed R@100` is the value after
> removing that layer from P1 (full 0.4849), and `Difference` is the **removal loss**
> (full − ablated · positive = the layer contributes). Only A8 (the negative control) is significant
> under Holm (m=8) → H5 rejected and task entanglement observed. Subgroups marked ⚠ have n<20 and
> carry no firm conclusion.
>
> **A resource limit on the rejection-ground axis (important).** Of the 1,000 upstream records, 400
> cite inventive step (Art. 29(2)) and 14 cite novelty (Art. 29(1)), **rejections on novelty alone
> number 0** (all 14 co-occur with inventive step), and 600 carry no structured label. The
> anticipated contrast between novelty and inventive step is therefore **not testable on this
> resource**, and the co-occurrence row in the table is descriptive statistics at n=3. The vendor TTL
> snapshot also folds the `§1×n|§2×m` string into a single `Rejection_Inventiveness` and loses the
> novelty axis, so the labels were taken from a snapshot derived from the upstream original
> (`data/external/sdkb/rejection_basis.csv`). These labels are used **for subgroup decomposition
> only** and are not inputs to the ranking function.
>
> **The interpretation of the two cross-lingual rows is in §9.** The Δ of +0.0140 (p=0.518) in the
> "positives include a foreign language" subgroup does not mean that the ontology is powerless at a
> language barrier. Decomposed by ground-truth document, most positives in that subgroup **enter no
> system's candidate set at all** — a Korean query under BM25 recovers 0/128 English positives. The
> per-query Δ is computed over the few recoverable Korean positives, so this row must not be read as
> "cross-lingual performance".

**Two cautions in reading the ablation table.** First, the removal losses of A2 and A3 are
**negative** — removing the process-and-device axis or the material-equipment-failure axis raises
the primary outcome slightly (both n.s.). The picture in which each concept axis contributes
independently is not supported by the data; the gain comes not from a sum of axes but from a single
combined signal, concept overlap. Second, the +0.0534 of A7 (all ontology features removed) is **the
same number** as the P1-against-B3 difference in the performance table, because it is a comparison
of the same two rankings. In the performance table it is the preregistered primary comparison and is
reported uncorrected at p=0.008; here it is one member of a family of eight ablations and is
reported as n.s. after the Holm correction (m=8). Two verdicts on the same number are not a
contradiction but **a consequence of different comparison families**, and neither was chosen after
seeing the result.

**Figure — contribution by layer (A1–A8) with the Holm correction.** A positive value means
performance fell when that layer was removed, that is, a contribution. Only the negative control A8
is significant after correction. File `paper/figures/ir_ablation.svg`.

**Figure — P1 − B3 by subgroup.** The point is the difference and the bar the 95% confidence
interval; subgroups with n<20 are drawn in grey. File `paper/figures/ir_subgroup.svg`.

---

## 7. Retrieval performance — all rows of the two confirmatory splits

Cited from §5.4.1 of the manuscript.

> **The two panels appear in one table but are neither pooled nor averaged.** Panel A is the first
> confirmatory split (198 queries · 479 qrels) and panel B the non-overlapping second split (198
> queries · 503 qrels). The query set and the ground-truth set differ, and **each verdict stands
> under its own preregistration** — they are placed side by side only so that whether the same
> structure appeared twice can be seen on one screen. The values of panel A are also **observations
> on the pre-correction resource snapshot** and are not recomputed on the later corpus: while the
> second split was being built, the body text of 8 candidate documents changed, and recomputing
> without knowing how far those 8 move the values would be a new experiment rather than a
> re-measurement.

Every number is the output of
`python -m sdkb_paper.analysis.results_table --split {dev,test}` with no manual entry (artifacts
`paper/tables/ir_performance_test.md` and `paper/tables/ir_performance_test_b.md`). The conditions
are identical across all systems and both panels: after the F10 candidate mask (time validity, with
self and same-family excluded), truncation at the top 1,000, fold-then-cut at the family level, and
a macro average over queries with at least one known positive. **The primary outcome is
family-level Recall@100**, and each split was unsealed once at the moment of final comparison and
evaluated without reselection. The decision rule, margin, weights and retrieval settings of panel B
were inherited unchanged from panel A and are pinned in the pre-unsealing commit (`67568c8`).

**Retrieval performance on the two confirmatory splits (2 panels).** The baseline is the Text Hybrid
(B3) of each panel; Δ, CI, *p* and win/loss/tie come from a query-level paired bootstrap with 10,000
resamples. The last two rows of each panel are exploratory baselines under a separate
preregistration and do not enter the confirmatory verdicts.

| | System | R@100 | Δ vs B3 | 95% CI | *p* | Win/loss/tie | Δ nDCG@20 | *p* |
|---|---|---:|---:|---|---:|---|---:|---:|
| **A** | BM25-Claim (B0) | 0.4126 | −0.0189 | [−0.0535, +0.0152] | .279 | 15/22/161 | — | — |
| **A** | Dense (B2 · Titan v2) | 0.3031 | −0.1285 | [−0.1691, −0.0895] | <.001 | 6/57/135 | — | — |
| **A** | **Text Hybrid (B3 = B0⊕B2 RRF)** | **0.4315** | — | — | — | — | — | — |
| **A** | CPC/IPC only (B4) | 0.1860 | −0.2455 | [−0.3018, −0.1895] | <.001 | 14/89/95 | — | — |
| **A** | Ontology-only (B5) | 0.1800 | −0.2515 | [−0.3163, −0.1863] | <.001 | 25/96/77 | — | — |
| **A** | Text+Ontology (P0★ · prespecified primary) | 0.4635 | +0.0319 | [−0.0139, +0.0785] | **.181** | 41/22/135 | **−0.0395** | **.029** |
| **A** | **+ClaimFeature (P1)** | **0.4849** | **+0.0534** | **[+0.0145, +0.0926]** | **.008** | 37/11/150 | −0.0176 | .227 |
| **A** | Multilingual fusion baseline (B★ · exploratory) | 0.4505 | +0.0190 | [−0.0116, +0.0495] | .222 | 24/15/159 | +0.0043 | .714 |
| **A** | Bibliographic-condition baseline (B10 · exploratory) | 0.3988 | −0.0327 | [−0.0693, +0.0039] | .076 | 14/25/159 | **−0.0328** | **.012** |
| **B** | BM25-Claim (B0) | 0.3254 | −0.0848 | [−0.1229, −0.0489] | <.001 | 9/40/149 | −0.0240 | .028 |
| **B** | Dense (B2 · Titan v2) | 0.3646 | −0.0456 | [−0.0831, −0.0090] | .016 | 17/32/149 | −0.0513 | <.001 |
| **B** | **Text Hybrid (B3 = B0⊕B2 RRF)** | **0.4102** | — | — | — | — | — | — |
| **B** | CPC/IPC only (B4) | 0.3012 | −0.1090 | [−0.1745, −0.0458] | .001 | 35/73/90 | −0.0763 | <.001 |
| **B** | Ontology-only (B5) | 0.1470 | −0.2633 | [−0.3249, −0.2012] | <.001 | 20/104/74 | −0.1756 | <.001 |
| **B** | Text+Ontology (P0★ · prespecified primary) | 0.4344 | +0.0242 | [−0.0084, +0.0574] | **.147** | 25/18/155 | −0.0218 | .210 |
| **B** | **+ClaimFeature (P1)** | **0.4445** | **+0.0343** | **[+0.0094, +0.0615]** | **.004** | 19/9/170 | −0.0136 | .390 |
| **B** | Multilingual fusion baseline (B★ · exploratory) | 0.3809 | −0.0293 | [−0.0647, +0.0064] | .101 | 16/24/158 | +0.0049 | .641 |
| **B** | Bibliographic-condition baseline (B10 · exploratory) | 0.4155 | +0.0053 | [−0.0453, +0.0553] | .844 | 34/38/126 | +0.0009 | .942 |

The Δ nDCG@20 cells are empty for the four baseline rows of panel A (B0, B2, B4, B5) **because those
values were not reported** — in the first split the auxiliary-metric comparison was computed only
for the two preregistered proposed configurations (P0★ and P1). The blanks are not filled in
afterwards.

---

## 9. Cross-lingual decomposition and operational efficiency

Cited from §5.4.3 of the manuscript. Every value here is exploratory descriptive statistics on
frozen runs and frozen settings; it is neither a new retrieval nor a preregistered confirmatory
test.

**Why a per-query average cannot answer the cross-lingual question.** The subgroup table of §6
reports that the gain of the proposal is not significant on queries whose positives include a
foreign language (Δ +0.0140, *p* = .518). Whether the cause is a lack of language neutrality in the
ontology, the absence of query and document translation, or a deficit in the resource itself is not
separable from a per-query average, because the average is diluted by the Korean positives (of the
479 positives in the confirmatory split, 340 are Korean, 128 English and 11 Japanese). Recall is
therefore decomposed by **micro-aggregation over ground-truth documents**; every number is the
output of `python -m sdkb_paper.analysis.lang_recall --split test` (artifact
`paper/tables/ir_crosslingual_test.md`).

**Operational efficiency — the gain on the primary outcome barely carries into the number of
documents reviewed.** What the gain on R@100 (+0.0534) means in practice was converted into the unit
of **documents reviewed**. There are four metrics: **Effort@Recall**, the minimum review depth at
which a query first reaches a target recall; **Candidate Reduction**, by what percentage that depth
fell against the baseline; and the recall-by-depth curve and the number of additional documents
found per query. The unit is the same family (distinct inventions) as the primary outcome, and the
review-depth cap is fixed at 500. The full table is `paper/tables/ir_effort_test.md` and the curve
is `paper/figures/ir_effort_curve.svg`.

| System | To the first related document (median) | To half the positives (median) | Full-recall attainment |
|---|---:|---:|---:|
| Text Hybrid (B3) | 21.0 | 65.0 | 38.4% |
| Text+Ontology (P0★) | 23.5 | 70.5 | 41.9% |
| **+ClaimFeature (P1)** | **19.0** | **59.5** | 40.9% |

**The medians fall, but the benefit disappears once queries are paired.** The median Candidate
Reduction, comparing the review depth of the two systems directly on the same query, is **0.0%**,
and the win/tie/loss counts are 62/16/64, essentially even (at the half-positives target, over the
142 queries that both reached). The number of additional documents found per query also has a median
of 0: at K=100, 37 queries gained documents against 11 that lost them, for a total of +28. The gain
of §7 above is therefore **not the result of improving every query a little but a shift of the mean
produced by some queries only**. This observation runs in the same direction as the concentration of
the gain in the high-overlap subgroup.

**One structural point stated in advance.** Without a cap on review depth, the proportion of queries
that fail to reach the target recall is **identical** across the three systems (half the positives
26.8%, full recall 55.1%), because the proposed systems reorder the candidate pool of B3 without
enlarging it. The only benefit available here is in principle **"finding the same things at a
shallower depth"** and never **"finding more"** — the limit of reranking diagnosed in §6.2 of the
manuscript appears in the same shape in the operational metrics.

**Three boundaries in reading this.** (i) Queries that failed to reach the target recall **were not
discarded**. Discarding them would remove the hard queries and inflate the benefit, so unreached
queries were conservatively imputed at cap+1, only medians were reported, and the truncation
proportion is carried in the table. (ii) **The median for full recall (R=1.0) is not reported**,
because more than half (over 55%) are unreached and the median would be determined by the imputed
value; only the attainment rate is given in its place. (iii) These values are **exploratory
descriptive statistics**. The confirmatory split was already unsealed, so no superiority is claimed
again here and these values do not enter the conclusions or the contributions. They are also
statements about the **number** of documents reviewed and **do not translate into a percentage
saving of search time or cost**, because per-document review time was not measured.

---

## 8. Robustness of the comparison under incomplete ground truth

Cited from §5.4.1 of the manuscript (the two checks of §4.5).

> **This section does not stand in for expert relevance judgment.** It asks one question — **does
> the conclusion of the paired comparison depend on the relevance of the unjudged documents?** No new
> retrieval was run, and no metric, bootstrap procedure or verdict changed. The command is
> `python -m sdkb_paper.analysis.judgment_robustness` and the output is
> `data/processed/ir/judgment_robustness.json`.

**The input runs are `runsets/O_pre_linker/`, not `runs/`.** The `runs/` on disk are artifacts of a
later resource generation in which the R@100 of P1 is 0.4556, and computing with those would measure
the robustness of **a different comparison than the one the manuscript reports**. The single
selection criterion was *"does it reproduce the numbers of the performance table"*, and the
reproduction agrees to four decimal places (panel A Δ +0.0534 · LB +0.0145 · panel B Δ +0.0343 ·
LB +0.0094).

**A · Exogeneity of the ground-truth set (an argument, not a number).** The standard mechanism by
which incomplete ground truth biases a comparison is pool bias: if the ground truth is built from
the top results of the systems being compared, a system that did not contribute to the pool is
structurally disadvantaged. The ground truth of this benchmark is **examiner citations**, generated
before and independently of any system in this study. The path by which a deficit could correlate
with a configuration therefore narrows to one: when the configurations raise **different kinds** of
document to the top and the examiner's propensity to cite differs by kind. B below measures that
residual path.

**B · Composition of the unjudged set in the top 100.** Four axes were fixed in advance (language,
publication year, CPC/IPC main class, concepts per document). **The binary "holds a concept link"
variable has no contrast because 98.5 % of candidates hold one, so it was redefined as the
distribution of concept counts** (approved 2026-08-17), and **CPC is empty on 97.2 % of candidates
and was replaced by IPC on the same axis**. Missing years are not discarded but counted as an
`unknown` category.

| Split | Configuration | n | Language (ko/en/ja) | Median year (unknown share) | Two most frequent main classes | Concepts Q1/median/Q3 |
|---|---|---|---|---|---|---|
| A (test) | B3 | 19,610 | .997 / .002 / .001 | 2017 (.232) | **H10 .332** · C23 .242 | 3 / 5 / 7 |
| A (test) | P1 | 19,582 | .996 / .004 / .000 | 2018 (.284) | **C23 .320** · H10 .270 | 3 / 5 / 7 |
| A (test) | P0★ | 19,589 | .995 / .005 / — | 2018 (.303) | C23 .347 · H10 .249 | 4 / 5 / 8 |
| B (test_b) | B3 | 19,606 | .990 / .008 / .002 | 2014 (.353) | H10 .342 · C23 .153 | 2 / 4 / 6 |
| B (test_b) | P1 | 19,595 | .992 / .007 / .001 | 2014 (.350) | H10 .360 · C23 .160 | 2 / 4 / 6 |
| B (test_b) | P0★ | 19,600 | .992 / .007 / .001 | 2014 (.350) | H10 .370 · C23 .158 | 2 / 4 / 6 |

**The result is split, and we record it as such.** On the language, year and concept-count axes the
composition of the two configurations is similar. **The classification axis differs in panel A** —
the unjudged set of B3 is most frequently semiconductor devices (H10) and that of P1 surface
treatment (C23). In panel B that difference disappears. **Following the interpretation rule fixed in
advance**, the classification axis **remains a residual threat**. No test is attached — these are
descriptive statistics, and attaching a test would create a new confirmatory claim. **No existing
verdict is revised on this observation.**

**C · The verdict-overturning threshold n\*.** Only **unjudged families** that appear in the top 100
of the weaker configuration and not in the top 100 of the stronger one are added as positives. Each
addition raises the positive count by one and is recovered only by the weaker configuration, so the
paired difference falls monotonically. The placement is the greedy one that lowers the difference
fastest.

| Split | Δ (P1−B3) | LB₉₅ | U (adversarially addable candidates) | n\* (point estimate) | n\* (LB₉₅) | n\*/U | Queries used |
|---|---|---|---|---|---|---|---|
| A (test) | +0.0534 | +0.0145 | 7,242 (mean 36.6 · queries with U=0: 0) | **17** | **4** | .0023 / .0006 | 17 / 4 |
| B (test_b) | +0.0343 | +0.0094 | 3,669 (mean 18.5 · queries with U=0: 2) | **10** | **3** | .0027 / .0008 | 10 / 3 |

**The threshold is small — this is the unfavorable result of the section and it is carried as it
stands.** In both splits the point estimate reaches 0 with **fewer than 0.3 % of the adversarially
addable candidates**, and the lower bound of the confidence interval reaches 0 with **fewer than
0.1 %**. **The mechanism is in the denominator**: about 24 % of queries have only one ground-truth
family (A .237 · B .232) and the median number of positives is **2**, so on such a query a single
adversarial addition cancels that query's recall difference entirely.

**The assumptions are not hidden.** (i) An added family is counted in the same unit as the existing
positives. (ii) The adversarial placement is **the worst case** and not an estimate of the real
distribution — that unjudged documents have no reason to favor one configuration is the exogeneity
argument of A above. (iii) The greedy placement is **optimal for the point estimate** but may not be
optimal for the CI lower bound, so `n*(LB₉₅)` is **read as an upper bound**. (iv) No pass mark is
placed on n\* — placing a threshold would create a new verdict.

**The one permitted conclusion was fixed in advance.** *"The conclusion is vulnerable to the
composition of a small number of unjudged documents, and this is not resolved without sampled
judgment."* What this vulnerability threatens is **the significance of the paired difference**; the
gate verdicts, the design principles and the observation of cross-layer metric misalignment do not
depend on this threshold.

**The second check, widening the ground truth by an exogenous label,** merged the examiner citations
of foreign counterparts and the difference was maintained (+0.0534 → +0.0593 · *p* = .008 → .003).
The full text of both checks is in the Korean record.

---

## 10. Reproducibility control, sealing and unsealing

Cited from §4.5 of the manuscript.

- Data, ontology, shapes, CQs, index and model versions are pinned by hash.
- Random seeds and the package lockfile are published (including the split, bootstrap and
  hard-negative sampling).
- The lists of training, development and test identifiers are stored.
- Whether any forbidden edge remains after qrel masking is checked automatically
  (`validate/leakage_check.py` · `make leakage`). The check has four layers: corpus features;
  runtime feature resources (the concept axis and the claim-feature sidecar); residue of the
  candidate mask (F10) in the top 100 of the produced run; and the qrel hash and seal state. The
  development-split measurement is 0 violations across all seven system runs.
- Before the test is unsealed, the research questions, primary outcome, thresholds and exclusion
  criteria are frozen in a timestamped document.
- Consistency with the triple signature of the 105,588 generation is verified automatically
  (`check_signatures.py`).
- Where redistribution of full text is restricted, the source API queries, the preprocessing code,
  and the document identifiers and checksums are provided.
- The results of the three modes (oracle-free / citation-assisted / GT-assisted) are stored
  separately.

**We state the two places where this control is not complete (added 2026-08-02, measured).**
Reproducibility must be a check result rather than a claim, so the holes the check revealed are
recorded as they are.

- **The frozen snapshot alone cannot reproduce the concept links.** The snapshot contains the
  concept dictionary (Tier-1 vocabulary, 482 keys) and 14 TTL files, but **it does not contain the
  alias dictionary (Tier-2, 235 keys)** through which a substantial share of the actual links
  passes. Rebuilding the A-Box concept links from the snapshot alone therefore does not match the
  graph in link count or link set. From the standpoint of provenance integrity the current snapshot
  is **incomplete**, and the fix is to include the mapping assets in the release artifacts and
  register their hashes in `PROVENANCE.json`. The numbers of this paper were produced from links
  that exist in the graph, so the verdicts are unaffected.
- **Byte-level reproducibility of the hybrid run file is broken.** Even with byte-identical input
  runs, the sha256 of the RRF fusion output differs between executions. The cause is that the fusion
  function iterates over query identifiers as a set, so **the order in which query blocks are written
  varies between processes**, while **the rankings themselves are identical** (content comparison
  after sorting agrees). The verdicts are therefore not contaminated; what is broken is the
  hash-based reproducibility check. The fix is to fix the write order by sorting, and until then
  this artifact alone is **verified by content equivalence rather than by hash**.

---

## 11. Task entanglement — where the negative control broke (H5)

Cited from §6.3 of the manuscript.

> **The observation of this section is one of the three misalignments, and three boundaries are
> attached to it.** The verdict (H5 rejected) is definite, but **the cause is not separated** (see
> (a) and (b) below), it is the result of one unsealing of a confirmatory split, and it is
> conditional on the module arrangement of this release. We therefore do not use this observation as
> the most general conclusion of the paper.

Removing the expert-matching-only layers (the `Skill` axis), designed to be theoretically unrelated
to retrieval and used as the negative control, **significantly degraded retrieval** (removal loss
+0.0316, 95% CI [+0.0105, +0.0560], p=0.002; the only ablation of the eight significant after the
Holm correction). As stated in advance, the result is read in one of two ways — establishing
specificity or observing coupling — and what was observed is the latter.

This is not the result of a faulty experimental design but direct evidence that **tasks sharing one
vocabulary do not separate cleanly in statistical terms**. A delta aimed at the expert-matching view
can quietly damage the query paths of prior-art search, and that damage is visible neither in formal
validation (L0–L3) nor in the performance checks of the gate task (T1, T2). An ablation study of a
multi-task ontology should therefore include a negative control on a layer unrelated to the gate
task, and this is where the paper's grounds come from for a cross-task non-regression condition
being needed **independently** of formal validation and single-task performance.

We do not, however, overstate it. What was observed is the fact that **the tasks do influence one
another**, and **by what path** they do so is not answered by this experiment.

**There are three candidate paths, and two of them were measured on the resource side (added
2026-08-02).** A resource audit after unsealing measured two more ordinary mechanisms that explain
the same observation, and they are recorded as such.

- **(a) The module boundaries do not coincide with the task boundaries.** `sdkb-core.ttl` holds 56
  classes and 44 ObjectProperties, and **the entire expert-matching vocabulary** (`Expert`,
  `ExpertCase`, `Skill`, `Problem`, `RootCause`, `Mitigation`, `FailureMode`) is inside it; because
  the `patent` and `foresight` modules `owl:imports` the core, **every task inherits it
  unconditionally**. Of the three tasks, only `sdkb-patent.ttl` is cleanly separated. That is, **the
  layer designed as a negative control was in fact part of the shared core.**
- **(b) The expert alias dictionary was applied unchanged to patent prose.** The alias dictionary
  that creates concept links is originally a bridge attaching expert profiles and SME problem tags
  to nodes, yet the same dictionary is used on patent body text. As a result `chamber` links to
  `skill:chamber_conditioning`, `gas` to `skill:gas_chemistry` and `plasma` to
  `skill:plasma_diagnostics` — a **category error** in which "a patent that mentions a chamber"
  becomes "a document holding the chamber-conditioning **competence**". 98.9% of the task-axis links
  pass through this route, and five surface forms create 80.3% of the Skill-axis links. If so, what
  A8 removed may not be "the expert-matching layer" but **a bundle of labels wrongly attached to
  high-frequency nouns in patent prose**.

If (a) and (b) hold, the −0.0316 of A8 is **not a property whereby an ontology couples tasks but an
artifact of the module arrangement and dictionary reuse of this release**. Which it is has never
been separated by this paper, so it remains **undistinguished**. **The conclusion of this section is
unchanged under any of the three candidates**, however — the fact that neither formal validation
(L0–L3) nor the performance checks of the gate task (T1, T2) saw this drop is the same, so the
grounds for a cross-task condition being independently necessary stand. What changes is **the size
of the claim**. We do not extend this observation into a property of ontologies in general, that "a
shared T-Box cannot separate tasks". Each candidate leaves a testable prediction — for (a), whether
the sign of A8 holds after task-specific vocabulary is separated out of the core; for (b), whether
A8 loses significance after a patent-specific alias profile lowers the share of Skill-axis links —
and both are to be measured under a new preregistration.

**And in the second confirmatory split this observation was not reproduced — stated first.**
Repeating the same ablation on a non-overlapping query set gave a removal loss for A8 of **exactly
0.0000**. We neither average the two values nor retract either. **The result split across two
samples** is the accurate statement, and the reason for the split is itself undistinguished: the
significant degradation in the first split may have been chance, or the queries of the second split
may have held effectively no Skill-axis concepts, so that **there was nothing to remove**. If the
latter, the 0 is not "no effect" but "not measurable", and **this table cannot separate the two**.
The way to separate them is to decompose and compare the per-query, per-axis concept coverage of the
two splits, and the specification is in §14 below.

**This split does not demolish the grounds for the cross-task condition — but it moves their
weight.** The claim that the cross-task non-regression condition (T3) is independently necessary
rested on two grounds. One split here, and **the other stands** — the observation that when faults
were deliberately injected, formal validation and the retrieval performance check both missed them
and **T3 alone caught 12 of 45 holdout instances** (one-sided *p* = .0001). The design-principle
table records its grounds in the same order: the fault-injection result comes first, and the
negative control follows **with the split stated**.

---

## 12. Conclusion rules — what may and may not be said with these results

Cited from §6.4 of the manuscript. Frozen before unsealing and carried here verbatim.

A negative result is not a failure but an output that identifies the next direction of improvement.
The negative results of this study are measurements and number three — the conditional prediction
contradicted (the gain concentrates in high overlap), the absence of layer contribution, and no
improvement in top-of-ranking precision. These three are not unrelated failures but point to a
single structure, and that structure sets the next priorities: **(a)** ontology-based candidate
generation and query expansion to open the reranking ceiling, **(b)** a separate ranking objective
aimed at top-of-ranking precision, and **(c)** cross-lingual recall. (a) and (c) are two faces of
the same constraint.

| Observation | Permitted conclusion | Forbidden conclusion |
|---|---|---|
| The proposed system is significantly better than the strongest text baseline | Improves deep recall of **known positives** on this benchmark | Finds every legally relevant piece of prior art better |
| The gain is confined to a particular subgroup | Conditional complementary value | Improves retrieval in general |
| The feature effect exists only on a subset | Local value of fine-grained semantics and a coverage constraint | The same effect on all queries |
| Removing the negative control degrades retrieval | An observation of cross-task dependency, and the necessity of a cross-task condition | A failure of the ablation design · identification of a causal mechanism |
| The hybrid is worse | No retrieval gain under the current mapping and scope | Ontologies are inherently useless for patent retrieval |
| A reduction in documents reviewed (Effort@Recall) | The same recall with **fewer documents reviewed** | An X% saving of search time or cost · replacing a patent attorney's review |
| Performance falls after resource indicators improve | Misalignment between layers · the necessity of a performance condition | That ontology enrichment is itself useless · identification of the cause (resource vs scoring function undistinguished) |
| The retrieval metric (Recall@100) improves | Improved **deep recall** of known positives | **The RAG answers got better · generation performance improved** — a retrieval metric does not stand in for generation performance |
| Citation accuracy is higher on one arm | The **evidence identifiers given match the sealed ground truth more often**, recorded together with the possibility that the arm was more cautious | Superiority of answer quality · a significant improvement at the generation layer (no such test was registered) |
| Hallucination rate and evidence-sentence match | The **range within which the evidence given can be trusted** | Replacing or automating a patent attorney's review · settling evidence localization without human verification |

**The last two rows are the whole of the conclusion rule for the layer below.** The second readout of
the transfer experiment is confirmatory but **the verdict is a failure**, so no number in its table
is used as grounds for "improved". The sentence that may be used is **"we could not confirm
transfer"** and not *"it does not transfer"* — the point estimate in fact favored the proposed arm,
and what broke was not the value but the width of the interval.

---

## 14. Competing explanations — what was not separated, given as the specification of the experiment that would separate it

Cited from §6.4 of the manuscript.

The observation that retrieval fell although the resource improved 2.4-fold admits five competing
explanations, and **this experiment did not separate them**. Rather than passing this off in a
single sentence of limitations, it is carried as a table — because what the promotion criterion
requires is not "we excluded them" but **"we state that we did not exclude them"**.

| Competing explanation | Prediction | The experiment that would separate it | Current state |
|---|---|---|---|
| **Resource deficit** — the vocabulary and resolution are still insufficient | Expanding the vocabulary to the 10³ scale improves it | Re-measure on the same pipeline after vocabulary expansion | **Not performed** |
| **Scoring function** — the overlap score is an unweighted Jaccard and ignores document frequency | Adding per-concept df weighting improves it | Re-measure with a ranking function that consumes concept metadata (df, depth, hypernym) | **Not performed** — this is a new method, not a re-measurement |
| **Candidate pool** — the reranking ceiling | Introducing ontology-based candidate generation improves it | Add a candidate-generation arm | **Outside the design** |
| **Language** — there is no query translation | Translating the query improves cross-lingual recall | Re-measure with the query side alone translated | **Not implemented** |
| **Module boundaries** — the concept hierarchy has only 11 triples, so the weight of the hierarchy term is structurally 0 | Making the hierarchy substantive makes the hierarchy term visible | Re-measure after assigning a multi-level `skos:broader` taxonomy | **Not performed** |

**Two further things this paper did not separate are carried in the same form.**

| Competing explanation | Prediction | The experiment that would separate it | Current state |
|---|---|---|---|
| **The split between the two confirmatory splits on the negative control (A8)** — (i) the significant degradation in layer A was chance; (ii) the queries of layer B held no concepts on the expert-layer axis, so there was nothing to remove | If (ii), the coverage of that axis in the layer-B queries is close to 0 | Decompose and compare the per-query, per-axis concept coverage of the two splits | **Not performed** — the second split cannot separate "failure to reproduce" from "nothing to measure" |
| **The cause of the transfer verdict failure (T4)** — (i) the retrieval gain does not carry to the generation layer; (ii) the sample was too small to show non-inferiority | If (ii), the lower bound moves inside the margin as the sample grows | Re-adjudicate with the same instrument on more queries (a new preregistration) | **Not performed** — the lower bound missed the margin by 0.0005, a knife-edge failure, so both explanations remain alive (§16) |

**This table is an output.** "We did not identify the cause" is a limitation, but **being able to
specify what to measure in order to separate them** is a result. None of the five changes the
conclusion of this paper — even if all five were true, **"resource indicators alone cannot authorize
acceptance"** still stands. What the competing explanations bear on is not the necessity of the
acceptance rule but **the direction of improvement**.

---

## 15. Qualitative typology of failures — produced, and placed in an appendix

Cited from §6.4 of the manuscript.

**A first distinction: this is not the expert relevance judgment.** What §5.13 of the Korean record
designed is a **relevance judgment** asking *"is a highly ranked candidate absent from the ground
truth actually a false positive"*, and it remains **not performed**. The work in this section does
not judge relevance; it **classifies by observed features** why a document already fixed as a
positive was pushed down. Only the coding protocol (blinding, independent coding, reporting κ, and
an appendix if κ<0.4) is taken over from §5.13.

**Coders and the decision rule fixed in advance.** The type list F1–F7, the coding sheet, the sample
and the prompt were frozen in a commit before coding began. There are three coders — **two different
models run locally coded the whole set** (492 calls across the two splits) and **one person coded a
sample of 40 pairs**. The person coded before seeing the models' output. The decision rule was also
fixed before results were seen: **if the agreement (κ) between the person and the models' consensus
is 0.4 or above the result goes in the main text, and below it goes to an appendix.**

**The instrument failed.** The self-consistency of the two models is 1.000 and 1.000 (0.982 on one
split), effectively perfect, yet **the agreement between the two models is only κ = 0.146 and
0.142**. That combination is not noise but **systematic bias** — the labels reflect **the habits of a
model** rather than properties of the case. One model in fact placed 77–90% of its labels in F1 and
the other 57–65% in F3. **The decisive evidence is F5**: there are 21 places where the mechanical
decomposition identified the IPC term as the leading term of the inversion, and **the two models used
F5 zero times across both splits**. The models did not use in their judgment a decomposition that
came with a Korean summary attached.

**The person saw that place.** Of the 40 pairs, **F5 is the most frequent at 19**. All 40 carry a
label and a supporting sentence, all 40 supporting sentences differ, and they cite the decomposition
values together with the technical substance. And **it is not transcription** — had the person
simply read off the leading term identified by the machine and stamped the most frequent label, the
hit rate would be 0.650, so **35% is not explained by the leading term** (18 concept-led cases split
across four categories).

**Distribution of the 40 human-coded pairs** (both splits combined; the full text and the per-split
decomposition are in the Korean record).

| Type | Meaning | Count |
|---|---|---:|
| **F5 classification density** | Many documents share the IPC class, so the classification term did not discriminate | **19** |
| **F3 ground-truth resource deficit** | The demoted positive has no concepts, or shares none with the query | **12** |

Because κ fell below the criterion fixed in advance, this typology is reported in the appendix and
**no claim in the paper rests on it**.

---

## 16. Appendix A — the transfer experiment (RQ5 · one T4 verdict)

Cited from §3.5.1 and §6.4 of the manuscript.

> **This paper does not propose a RAG method.** The generation side (model, prompt, number of
> context documents, temperature, seed) was fixed to the character, and the only thing changed is
> **which retrieval arm's top documents are inserted**. This is therefore not a new benchmark but
> **a second readout of the same benchmark**.
>
> **Two layers are reported.** The readout on the first confirmatory split (layer A) is
> **exploratory**, and its purpose was to freeze the instrument. The readout on the second
> confirmatory split (layer B) is **confirmatory**: the decision rule and the non-inferiority margin
> were frozen **before results were seen** and one verdict was issued. **Layer-A values are not used
> as grounds for the layer-B verdict.**

The controlled resource substitution is a record of resource-layer indicators and retrieval-layer
performance diverging. What, then, one layer further down — **does a retrieval-layer indicator
represent the value of the generation layer?** The question matters because of the acceptance rule.
T1 blocks or passes a release on one retrieval metric (Recall@100). If that metric does not
represent how it is used in practice, that is, the quality of the stage that answers with evidence
attached, then the acceptance condition itself must be reconsidered.

**The design spends everything on holding the variables to one.** Each layer uses the same queries,
the same sealed ground truth and the same leakage control, and takes the **top 10** documents from
an already frozen retrieval result file as context. Scoring involves neither a person nor another
model: it is **identifier comparison** — a machine checks whether the documents an answer cites are
in the sealed ground truth. The temperature is 0, yet each configuration is still run **three times**
and the between-run variation is reported. There were 1,188 calls in each layer and 0 API failures.
**The instrument signature is identical across the two layers** — the prompt sha256, the model ID,
the number of context documents, the temperature and the maximum generation length are the same, and
the only differences are the split and the retrieval result set.

**We first confirmed that the two arms really insert different documents.** If the top 10 of the two
arms were nearly identical, passing non-inferiority would be evidence that **the arms were similar**
rather than evidence of transfer. In layer B the mean Jaccard similarity of the top 10 is 0.2334
(median 0.1765), 91% of queries are below 0.5, and the sets are identical on 3 of 200 queries. Layer
A is at the same level (mean 0.1755). **The discriminative power is intact.**

**The margin was frozen before results were seen.** The primary metric is **citation accuracy
(overall)** — its scoring is deterministic (identifier comparison, no judge model) and **the two arms
stand on the same query set**. The auxiliary conditional accuracy counts only queries that actually
have evidence, and **that query set itself differs by arm**, so the two arms would not stand on the
same sample. The non-inferiority margin is **ε_T4 = 0.02**, inherited unchanged from T1, because
inventing a new number would make its source the results. The threshold on the hallucination side is
**η = 0.01**, half of that, since hallucination has asymmetric cost and cannot be traded against an
accuracy gain on equal terms. The decision rule is
`T4 = (lower bound of the CI on Δ citation accuracy > −0.02) ∧ (upper bound of the CI on Δ
hallucination rate < +0.01)` with Δ = P1 − B3. The rule is pinned in a pre-unsealing commit, and the
margins are fixed as constants in code that a caller cannot change.

> **The denominator moves with the arm — one sentence of the preregistration's rationale is
> corrected here (2026-08-10).** The denominator of citation accuracy (overall) is not the number of
> queries but **all identifiers cited** (`src/sdkb_paper/rag/score.py`, `rag/t4.py`), and because the
> two arms cite a different number per query, **the denominator differs by arm** (layer A: P1 2.2929
> against B3 2.4949; layer B: Δ −0.0707). The preregistration's stated reason for choosing this
> metric, *"the denominator is the full query set and therefore does not move"*, was inaccurate.
> **Only the rationale is corrected; the primary metric, the decision rule and the margin stand** —
> and the preregistration document is not retroactively edited. That the denominator moves was
> already recorded **as a competing explanation**, which is why the mean number of citations per
> query is carried alongside as the context of the denominator.
>
> **For the same reason one condition attaches to inheriting the margin.** The ε of T1 is a margin
> on Recall@100 **averaged per query**, whereas ε_T4 is a margin on a ratio computed over **pooled
> citation identifiers**. The two share the range of the scale ([0,1]) but **differ in sampling
> unit** — the inheritance is to be read as far as "the same ratio scale" and does not mean "the same
> substantive difference". Being a frozen threshold, it was applied unchanged.

**The T4 verdict (layer B · 198 queries paired · bootstrap 10,000).** Artifact
`paper/tables/rag_t4_verdict_test_b.md`.

| Metric | B3 | P1 | Δ | 95% CI | *p* | Condition |
|---|---:|---:|---:|---|---:|---|
| **Citation accuracy (overall)** | 0.2477 | 0.2713 | **+0.0236** | **[−0.0205, +0.0673]** | .292 | **Not met — the lower bound −0.0205 ≤ −0.02** |
| **Hallucination rate** | 0.0091 | 0.0032 | −0.0059 | [−0.0186, +0.0059] | .393 | Met — the upper bound +0.0059 < +0.01 |
| Citation accuracy (conditional) · reported only | 0.5655 | 0.5811 | +0.0156 | [−0.0696, +0.1007] | .728 | — |
| Evidence-sentence match · reported only | 0.8278 | 0.7739 | **−0.0539** | [−0.1118, +0.0039] | .068 | — |

The bootstrap **recomputes** the ratio on each resampled query set, so its definition matches the
point estimate, and the number of resamples whose denominator became 0 was **0**. **Between-run
variation is reported separately** — at temperature 0 the between-run standard deviation of the two
metrics used in the verdict is 0.0000, and the only quantities that moved are the evidence-sentence
match (0.0017, 0.0017) and the proportion of insufficient-evidence declarations (0.0058, 0.0077).
**A standard deviation near 0 means the model is deterministic, not that a difference is
significant.**

**T4 failed. But the shape of the failure must be read exactly.** Of the two conditions the
hallucination rate passed and the citation-accuracy condition broke, and **the point estimate favors
P1** (+0.0236). What broke is not the value but the width of the interval — with 198 queries and
about 330 cited identifiers the confidence interval widened to ±0.044 and its left end passed the
margin by **0.0005**. The sentence that may be used is therefore not *"it was worse at the generation
layer"* but **"we could not show with this sample that performance does not fall"**. **The margin was
not changed** — moving a frozen threshold for the sake of 0.0005 is exactly the post-hoc adjustment
this paper forbids, and **regret is not a reason**.

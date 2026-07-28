# Validation-Gated Evolution of Multi-Task Engineering Ontologies: Evidence from Semiconductor Prior-Art Retrieval

**Running title:** Validation-gated evolution of engineering ontologies  
**Article type:** Research paper  
**Authors:** [Omitted for review]  
**Corresponding author:** [To be completed in the title page]

> **Editorial status.** This document is an AEI-oriented submission draft. The manuscript text ends after the declarations and references. The Korean completion checklist and the proposed supplementary-material map at the end are editorial notes and must be removed from the submitted manuscript.

## Highlights

- A validation gate protects multiple tasks sharing an engineering ontology.
- SDKB integrates expert matching, prior-art search, and technology foresight.
- Ontology reranking improves deep recall, but not top-rank ordering quality.
- Holdout fault injection confirms the value of cross-task non-regression.
- Same-pipeline old-versus-new testing is required for update approval.

## Abstract

Domain ontologies that support multiple engineering tasks evolve as new evidence and application views are added. Conventional validation verifies structural consistency but does not establish that an ontology update preserves downstream performance or sibling-task functionality. We present SDKB, a task-extensible semiconductor ontology dataset supporting expert matching, prior-art retrieval, and technology foresight, and a validation-gated evolution method. The method combines freshness, SHACL, logical, and competency-question checks with task-level non-inferiority, subgroup safety, and cross-task non-regression. Prior-art retrieval is the primary empirical task because 1,000 rejected applications and 2,534 examiner citations provide positive-only weak relevance judgments. In a sealed test of 198 queries, a secondary ontology-plus-claim-feature configuration improved family Recall@100 by 0.0534 over the strongest text hybrid (95% CI 0.0145–0.0926; *p* = .008), whereas the prespecified primary configuration was not significant and nDCG@20 did not improve. Fault injection initially rejected the preregistered discrimination hypothesis. After separating overlapping validation surfaces and freezing the revised rule, a holdout of 45 unseen cross-task faults confirmed 12 T3-only detections (one-sided McNemar *p* = .0001) with 0/27 false positives. Removing an expert-matching layer also degraded retrieval, indicating empirical cross-task dependency. The results support cross-task non-regression as a complement to structural and single-task validation, while limiting retrieval claims to deep recall. Same-pipeline old-versus-new ontology testing remains necessary to establish version-level approval safety.

**Keywords:** engineering ontology; ontology evolution; knowledge graph validation; competency question; prior-art retrieval; semiconductor; non-regression testing; fault injection

## Nomenclature

| Symbol or term | Meaning |
|---|---|
| AEI | *Engineering Applications of Artificial Intelligence* |
| CQ | Competency question |
| G0, G1, G2 | SDKB graph generations or resource layers |
| L0–L3 | Freshness/integrity, structural, logical, and functional validation |
| O, O′ | Baseline and candidate ontology versions |
| qrel | Query–relevance judgment |
| R@K | Recall at rank cutoff K |
| T1 | Same-pipeline task non-inferiority condition |
| T2 | Prespecified subgroup-safety condition |
| T3 | Cross-task CQ non-regression condition |
| T-gate | Product of T1, T2, and T3 task-level conditions |

# 1. Introduction

Engineering ontologies rarely remain static. New processes, materials, equipment, regulations, patents, and organizational knowledge are continuously added, while existing concepts are merged, split, or repositioned. A technically valid graph update can nevertheless alter application behavior. A synonym merge may preserve RDF syntax but collapse a distinction needed for expert matching. A hierarchy change intended to improve prior-art retrieval may break a technology-foresight query. An update can even improve average retrieval performance while degrading a safety-relevant subgroup.

This problem is more acute when several applications share one T-Box. In such a setting, validating a change only against the task that motivated it is insufficient. Structural validation asks whether the graph is well formed; logical validation asks whether it is consistent under the axioms that have actually been declared; functional validation asks whether expected query paths remain executable. None of these questions is identical to whether the update preserves empirical task performance or the functionality of sibling tasks.

This paper studies that gap through SDKB, a task-extensible semiconductor domain ontology dataset. SDKB represents semiconductor processes, devices, materials, equipment, failures, capabilities, patents, firms, and technology-strategy relations. Three application views share its core vocabulary: expert matching, prior-art retrieval, and technology foresight. Prior-art retrieval is used as the primary empirical task because examiner-cited references associated with rejected applications provide an institutionally anchored, although incomplete, evaluation signal. The other two views are not assigned unobserved performance claims; they are protected through task-specific competency questions.

The central proposal is a validation-gated evolution process. A candidate ontology version must pass four conventional layers—freshness and integrity (L0), structural constraints (L1), logical consistency (L2), and primary-task functional tests (L3)—and three task-level conditions: non-inferiority under an unchanged application pipeline (T1), subgroup safety (T2), and cross-task non-regression (T3). The separation between an unchanged pipeline evaluated with two ontology versions and two different retrieval systems is essential. A comparison between a text baseline and an ontology-enhanced system measures search utility; it does not, by itself, demonstrate that an ontology update is safe.

The study addresses four research questions.

**RQ1.** What validation evidence is required to approve an update to a multi-task engineering ontology?

**RQ2.** Does explicit semiconductor-domain knowledge add retrieval utility beyond a strong text-hybrid baseline under leakage-controlled evaluation?

**RQ3.** Can cross-task CQ non-regression detect failures that primary-task and formal checks do not localize?

**RQ4.** Do ostensibly task-specific ontology layers behave independently when they share a T-Box?

The corresponding hypotheses are deliberately bounded.

- **H1:** A cross-task condition detects at least one cross-task fault missed by the primary-task functional layer, with a prespecified directional test and a false-positive rate no greater than 5%. The original layer definition made this hypothesis untestable because L3 contained the T3 query surface; the revised, disjoint definition is therefore evaluated first exploratorily and then on untouched holdout faults.
- **H2:** For a candidate ontology update, the lower bound of the 95% confidence interval for same-pipeline family Recall@100 exceeds the non-inferiority margin of −0.02, all prespecified subgroup drops remain below 0.05, and no sibling-task CQ suite regresses. This hypothesis requires the same retrieval pipeline to be evaluated with O and O′.
- **H3:** Ontology-enhanced retrieval improves family Recall@100 and nDCG@20 over the strongest text hybrid, with a larger effect for low-overlap queries.
- **H4:** Claim-feature and rejection-ground components contribute more than classification or bibliographic controls.
- **H5:** Removing the expert-matching-only layer has no retrieval effect and therefore functions as a negative control.

This work makes four contributions.

First, it provides a validation architecture for the evolution of multi-task engineering ontologies. The architecture distinguishes graph correctness, application utility, update safety, and cross-task regression rather than collapsing them into one quality label.

Second, it reports SDKB as a semiconductor knowledge infrastructure with three application views and a reachability ladder that separates node-level, semantic-relation, and claim-feature coverage. This avoids treating the existence of a schema as evidence of instance completeness.

Third, it evaluates the detection behavior of the gate using controlled fault injection. The preregistered test failed, the cause was traced to overlapping validation surfaces, and the revised rule was frozen before a holdout set of previously unseen cross-task faults was executed. This chronology is retained because the failure and redesign are part of the engineering evidence.

Fourth, it reports bounded retrieval findings. An ontology-plus-claim-feature configuration improves deep recall, but the prespecified primary configuration is not statistically significant, top-rank ordering quality does not improve, and the expected advantage on low-overlap queries is absent. The paper therefore does not claim that an ontology generically improves prior-art search.

# 2. Background and related work

## 2.1 Engineering ontologies and domain knowledge infrastructures

Ontology engineering has long emphasized explicit conceptualization, competency questions, and evaluation against intended use (Gruber, 1993; Grüninger and Fox, 1995). Recent engineering ontologies extend this logic to interoperable materials and manufacturing data. The PMD Core Ontology targets semantic interoperability across materials-science workflows (Bayerlein et al., 2024), while MDS-Onto connects materials-domain and applied data-science concepts (Rajamohan et al., 2025). A recent review classified 65 manufacturing ontologies and highlighted continuing fragmentation in scope, reuse, and evaluation (Sapel et al., 2025).

SemicONTO is the closest semiconductor-specific academic comparator. Its initial version models semiconductor experiments and demonstrates the ontology through four competency questions (Li et al., 2024). SDKB differs in purpose and evidence. It spans patent, firm, capability, process, device, material, equipment, failure, and technology-strategy relations; exposes three task views on a shared core; and treats downstream and cross-task non-regression as release criteria. The comparison is not intended to establish superiority—SemicONTO and SDKB address different levels of the semiconductor information lifecycle—but to locate the present work within the small body of explicit semiconductor ontology research.

| Resource or framework | Main scope | Validation emphasis | Relation to this work |
|---|---|---|---|
| LOT (Poveda-Villalón et al., 2022) | Industrial ontology-engineering lifecycle | Requirements, implementation, publication, maintenance | Process foundation; no task-level update gate |
| PMDco (Bayerlein et al., 2024) | Materials-science interoperability | Semantic integration and reuse | Adjacent engineering domain |
| SemicONTO (Li et al., 2024) | Semiconductor experiments | Four competency questions in an initial ontology | Closest domain comparator |
| MDS-Onto (Rajamohan et al., 2025) | Materials and applied data science | Cross-domain semantic integration | Demonstrates multi-domain reuse |
| SDKB (this work) | Semiconductor knowledge infrastructure | L0–L3 plus T1–T3, fault injection, downstream retrieval | Multi-task update validation |

## 2.2 Ontology evolution and test-driven validation

Ontology-change research distinguishes additions, removals, refinements, and composite operations, and examines their effects on consistency and dependent artifacts (Flouris et al., 2008). Linked-data quality frameworks similarly cover accessibility, intrinsic quality, contextual fitness, and representational issues (Zaveri et al., 2016). SHACL makes many structural expectations executable, while test-driven linked-data methods turn quality requirements into repeatable checks (Kontokostas et al., 2014; W3C, 2017).

These approaches are necessary but not sufficient for a multi-task engineering resource. A reasoner can detect only contradictions supported by declared axioms. A CQ existence test can pass when one valid row survives despite a substantial distributional regression. A downstream evaluation can miss damage to tasks that were not measured. KGrEaT advances downstream-task evaluation of knowledge graphs (Heist et al., 2023), but version approval additionally requires a paired old-versus-new design and an explicit policy for subgroup and sibling-task regressions.

The present framework treats quality as layered evidence rather than a single score. It also treats the gate as software that must itself be tested. Controlled fault injection is used to estimate detection coverage, false positives, and sensitivity to decision thresholds.

## 2.3 Prior-art retrieval and weak relevance judgments

Patent retrieval differs from general web search because queries are long, vocabulary changes over time, patent families duplicate evidence, and recall is operationally important (Lupu and Hanbury, 2013; Shalaby and Zadrozny, 2019). Classification codes, citation networks, claim-matching datasets, dense representations, and claim-level modeling can complement lexical retrieval (Mahdabi and Crestani, 2014; Risch et al., 2020; Krestel et al., 2021; Bekamiri et al., 2024; Ghosh et al., 2024). Knowledge-graph methods are especially relevant when technological distance makes surface similarity unreliable (Siddharth et al., 2022).

Examiner citations are useful but incomplete. They reflect search and examination processes rather than exhaustive relevance judgments, and examiner-added and applicant-supplied citations have different interpretations (Alcácer and Gittelman, 2006; Alcácer et al., 2009). Accordingly, the 2,534 citations in this study are described as **positive-only, examiner-anchored weak relevance judgments**, not expert-labeled ground truth. Uncited documents are not assumed to be irrelevant. This choice motivates family Recall@100 as the primary metric and limits precision claims until independent expert judgments are available.

Cross-language patent search is an additional challenge, particularly for Korean queries with English or Japanese prior art (Choi, 2009; Magdy and Jones, 2014; Piroi and Hanbury, 2019). Language-neutral concept identifiers may help, but the present architecture reranks a text-derived candidate pool and cannot recover documents absent from that pool. Cross-language results are therefore exploratory diagnostics rather than a main contribution.

## 2.4 Research gap

The literature provides strong methods for ontology construction, formal and structural validation, downstream knowledge-graph evaluation, and patent retrieval. Competency-question datasets also make parts of functional evaluation reproducible (Potoniec et al., 2020). What remains underdeveloped is a version-approval method for an engineering ontology shared by several applications. Such a method must answer three distinct questions:

1. **Search utility:** does an ontology-enhanced system outperform a text system?
2. **Evolution safety:** does the same system preserve performance when O is replaced by O′?
3. **Gate detection power:** does the validation stack detect known failures without rejecting valid changes?

The experiments and claims in the remainder of the paper maintain this separation.

# 3. SDKB: resource scope and task views

## 3.1 Shared core and application views

SDKB is organized around a shared semiconductor core and three application views. The core represents processes, subprocesses, devices, materials, equipment, defects and failure modes, firms, patents, classifications, and value-chain relationships. Each view adds task-facing relations without creating a separate ontology.

The **expert-matching view** connects problems, processes, equipment, skills, expert cases, and mitigations. In the present paper it is validated through T-Box inspection and expert-matching CQs; no ranking-performance claim is made.

The **prior-art view** connects applications, claims, cited patents, classifications, rejection grounds, domain concepts, and claim features. It is the primary empirical view because its examiner citations support reproducible, albeit weak and incomplete, retrieval evaluation.

The **technology-foresight view** connects firms, technologies, patent portfolios, process capabilities, value-chain positions, and temporal observations. It is treated as a reuse and non-regression view rather than as a quantitatively validated forecasting system.

This asymmetric validation is intentional. Requiring identical empirical evidence for all three views would either overstate evidence for expert matching and foresight or discard their value as protected reuse cases.

## 3.2 Graph genealogy and resource layers

The current resource consists of three graph generations or layers and a claim-feature sidecar.

| Layer | Triples | Principal contents | Role in this study |
|---|---:|---|---|
| G0 | 105,588 | 1,000 rejected applications, 3,034 cited-patent nodes, examiner-citation and rejection schema | Benchmark anchor and baseline graph |
| G1 | 924,814 | 24,179 patents from major semiconductor firms; 371,267 claim texts | Domain-enrichment and candidate changes |
| G2 | 490,529 | 12,339 patents from 188 KSIA firms; 161,184 claim texts | External-corpus reuse and transfer analysis |
| Claim-feature sidecar | 11,605,931 | 586,567 claims; 1,289,512 claim features; 483,394 dependency edges; 635 prior-art judgments | Fine-grained claim analysis |

The sidecar is reported separately because its scale and storage mechanism differ from G0–G2. Its schema is part of SDKB, but its instances must not be silently counted as G0 content. The release pipeline records source signatures and provenance for the benchmark generation and checks them in continuous integration.

## 3.3 Retrieval anchor and the reachability ladder

The resource contains 2,534 examiner citations, including 30 non-patent-literature references. The predicate linking applications to examiner prior art has 2,321 unique patent targets, of which 2,211 are directly reachable as graph nodes. These counts have different denominators and are not interchangeable.

Resource readiness is therefore reported through a reachability ladder:

1. **Citation level:** 2,534 observed citation events.
2. **Unique patent-target level:** 2,321 unique patent targets.
3. **Graph-node level:** 2,211 directly reachable patent targets, or 95.3%.
4. **Semantic-relation level:** domain concept and relation coverage, which is lower than node reachability.
5. **Claim-feature level:** 402 of 584 judgment-linked instances are feature-reachable, or 68.8%.

The ladder prevents two common overclaims. High graph-node reachability does not imply complete semantic modeling, and rich claim-feature coverage in a selected judgment subset does not imply equal coverage for all 1,000 applications.

## 3.4 Provenance, licensing, and release separation

Each distributable artifact is associated with a source and license manifest. Public ontology schema, shapes, CQs, code, identifiers, and derived statistics are separated from patent texts that cannot be redistributed under the collection terms. KIPRIS-derived source material is reconstructed by authorized users rather than republished as an unrestricted corpus. This release separation is part of the engineering design, not an afterthought: FAIR-oriented reproducibility concerns procedures, hashes, identifiers, and derived evidence as well as raw-file availability (Wilkinson et al., 2016).

# 4. Validation-gated evolution method

## 4.1 Three evidence tracks

The proposed evidence architecture has three tracks that share data but answer different questions.

1. **Resource and graph validation:** L0–L3 establish freshness, structural compliance, logical behavior, and primary-task functional behavior.
2. **Application evaluation:** retrieval systems are compared on a frozen benchmark to estimate search utility.
3. **Update approval:** one fixed application pipeline is run with O and O′, followed by T1–T3.

The distinction controls the interpretation of every result. In particular,

\[
\Delta R_{\text{utility}} = R(P1) - R(B3)
\]

compares systems and estimates retrieval utility, whereas

\[
\Delta R_{\Delta G} = R(P,O') - R(P,O)
\]

holds the pipeline \(P\) fixed and estimates the performance effect of replacing ontology version \(O\) with \(O'\). Only the second quantity can enter T1 for version approval.

## 4.2 L0–L3 validation layers

The conventional validation stack is defined as follows.

- **L0—freshness and integrity:** verifies input hashes, generation manifests, timestamps, graph signatures, and leakage masks.
- **L1—structural validation:** executes SHACL constraints for required properties, datatypes, controlled identifiers, and declared cardinalities.
- **L2—logical validation:** executes a reasoner over the axioms present in the T-Box and tests cycles or contradictions covered by those axioms.
- **L3—primary-task functional validation:** executes the CQs assigned to the prior-art suite and detects existence or distributional regressions.

L2 is only as strong as its axiom surface. In the audited version, the absence of `owl:disjointWith`, functional-property, and cardinality axioms makes L2 a weak layer. The method retains it for architectural completeness but does not treat a pass as strong evidence of semantic consistency.

The initial CQ rule required only a minimum result count, usually one. Fault injection showed that this rule was insensitive to partial damage. The revised rule retains the existence condition and adds a polarity-aware distribution check:

\[
\operatorname{pass}_{v2}(i)=
[\operatorname{rows}_i\ge \operatorname{min}_i]\wedge
\neg\operatorname{regress}_i,
\]

where

\[
\operatorname{regress}_i=
\begin{cases}
\operatorname{rows}'_i < (1-\tau)\operatorname{rows}_i,&\text{for monotone-up CQs},\\
\operatorname{rows}'_i > (1+\tau)\operatorname{rows}_i,&\text{for monotone-down CQs}.
\end{cases}
\]

The primary tolerance is \(\tau=0.05\); \(\tau\in\{0,0.05,0.10\}\) is reported as a frozen sensitivity grid.

## 4.3 T1–T3 task gate

For a candidate delta \(\Delta G:O\rightarrow O'\), approval is defined as

\[
\begin{aligned}
\operatorname{Accept}(\Delta G)=&
\prod_{\ell=0}^{3}\mathbb{1}[L_\ell=\operatorname{pass}]\\
&\cdot \mathbb{1}[LB_{95\%}(\Delta R_{\Delta G,100})>-\epsilon]\\
&\cdot \mathbb{1}[\max_s \operatorname{Drop}_s<\delta]\\
&\cdot \mathbb{1}[\forall f\in\{EM,TF,CORE\}:Q_f(O')\ge Q_f(O)].
\end{aligned}
\]

T1 is a non-inferiority condition with \(\epsilon=0.02\). Its null states that replacing O with O′ reduces family Recall@100 by at least 0.02 under the same retrieval pipeline. T2 prevents a favorable mean from hiding a drop of 0.05 or more in a prespecified subgroup with adequate sample size. T3 requires non-regression in expert-matching, technology-foresight, and shared-core CQ suites.

L3 and T3 must have disjoint reporting surfaces. L3 covers the primary-task CQ suite; T3 covers the other task suites and the shared core. Their union still covers all CQs, so attribution changes without weakening the total pass condition. The implementation verifies the invariant

\[
L3_{\text{all}}\Longleftrightarrow L3_{\text{primary}}\lor T3
\]

for every evaluated delta.

## 4.4 Benchmark construction

The benchmark starts from 1,000 rejected Korean patent applications and 2,534 examiner-cited references. Citation edges associated with each query are masked before feature generation. Candidate documents must predate the query's relevant cutoff. Self matches and members of the query's patent family are excluded, and documents are folded to the family level before the rank cutoff is applied.

Queries are split by time and family into development and sealed test sets. The development split contains 197 queries. The test split contains 198 queries and 479 positive qrels and was opened once for the reported confirmatory comparison. Only queries with at least one known positive are macro-averaged.

The benchmark does not provide exhaustive negatives. Recall is computed against the observed positive set:

\[
R@K(q)=\frac{|Rel^+(q)\cap TopK(q)|}{|Rel^+(q)|}.
\]

Family Recall@100 is the primary metric because it corresponds to whether known prior art enters a feasible review depth. Recall@50, Recall@500, Success@100, MRR@500, and binary-gain nDCG@20 are secondary. Nonstandard bpref values are excluded from the main paper because positive-only judgments do not provide the judged-nonrelevant set required by the classical definition.

## 4.5 Retrieval systems

Only implemented systems with reported outputs are included.

| ID | System | Evidence |
|---|---|---|
| B0 | BM25-Claim | Claim text |
| B2 | Dense | Titan v2 embeddings |
| B3 | Text Hybrid | Reciprocal-rank fusion of B0 and B2 |
| B4 | CPC/IPC only | Classification overlap and distance |
| B5 | Ontology only | Semiconductor concepts and paths |
| P0★ | Text + Ontology | B3 reranked by concept overlap and IPC; prespecified primary |
| P1 | + ClaimFeature | P0 plus claim-feature coverage; secondary configuration |

For candidate document \(d\) and query \(q\), the proposed score is

\[
\begin{aligned}
S(q,d)=&w_b\widetilde{\operatorname{BM25}}(q,d)
+w_e\widetilde{\cos(e_q,e_d)}\\
&+w_c\operatorname{ConceptOverlap}(q,d)
+w_h\operatorname{PathSim}(q,d)
+w_f\operatorname{FeatureCoverage}(q,d).
\end{aligned}
\]

All feature values are normalized within a query. Weights are selected on the development split and frozen before test evaluation. The ontology-enhanced systems rerank the top 1,000 candidates from the text pipeline; they do not expand the candidate pool. This architecture is consequential for low-overlap and cross-language queries.

The current dense component is a general embedding baseline. A publicly reproducible patent-specific dense baseline must be added before submission to distinguish ontology effects from a weak dense component. PatentSBERTa and PaECTER are appropriate candidates, subject to language support and licensing.

## 4.6 Subgroups and ablation

The low-overlap threshold is the first quartile of the development distribution of mean character-trigram Jaccard similarity between a query claim and its known positives. The frozen value is 0.0079, producing 27 low-overlap and 171 higher-overlap test queries. Other prespecified subgroup axes include rejection-ground availability, process or device group, and the language of observed positives. Groups with fewer than 20 queries are descriptive only.

Eight ablations remove CPC/IPC, process/device concepts, material/equipment/failure concepts, ClaimFeature, rejection ground, hierarchy path, all ontology features, and the expert-matching-only layer. The last ablation is a negative control: it was expected to have no retrieval effect. Family-wise inference across the eight ablations uses Holm correction.

## 4.7 Fault injection and confirmatory chronology

The first fault-injection campaign contains 12 types at 1%, 5%, and 10% intensity with three repetitions, for 108 instances, plus valid deltas for estimating false positives. Fault types target integrity, structure, logic, CQ paths, semantic alignment, hierarchy, judgment context, metadata, temporal leakage, qrel leakage, synonym over-merging, and cross-task hierarchy reversal.

The original H1 expected cross-task faults to be detected only by T3. That prediction failed. The CQ decision rule was then made distribution-sensitive, but a second analysis showed a set-inclusion defect: L3 evaluated all task suites and therefore necessarily subsumed T3. The layers were redefined as disjoint while preserving total CQ coverage. Because these changes were informed by the first data, their results are exploratory.

The revised definition was then frozen and evaluated on 72 untouched instances: 45 cross-task faults and 27 valid deltas. The 45 faults comprise new repetitions of two earlier cross-task types and three new families—expert-skill hub concentration, expert-case/failure-mode reassignment, and value-chain direction reversal. For the new families, the manipulated predicates are statically verified to be disjoint from predicates used by the primary-task CQ suite. No decision rule was changed after the holdout was generated.

## 4.8 Statistical analysis

System comparisons use query-level paired bootstrap confidence intervals with 10,000 resamples and paired randomization tests. The main retrieval comparison is P0★ versus B3; P1 is clearly labeled secondary. Ablations use Holm correction. Fault detection uses paired McNemar tests at the instance level, with direction specified before the holdout run. Effect estimates are accompanied by query-level win/loss/tie counts where available. No result is converted from exploratory to confirmatory merely because it is statistically significant.

# 5. Results

## 5.1 Resource audit

The audit confirmed that vocabulary and relations for all three task views exist in the T-Box. It also confirmed that the graph has substantially different coverage at different semantic resolutions. Direct graph-node reachability for unique cited-patent targets is 95.3%, whereas claim-feature reachability in the judgment-linked subset is 68.8%. Thus, the resource can support broad patent-level navigation without implying complete feature-level evidence.

Thirty-one CQs are executable: 28 are assigned to the gate suites and three query the claim sidecar as measurements. The latter return 5,917, 3,117, and 4,906 rows for prior-art judgments at claim level, independent-claim features, and dependent-claim structure, respectively. Because the sidecar is not part of G0, these three measurements do not retrospectively strengthen the G0 gate.

L2 provides limited assurance in the current release. Faults involving type contradiction and hierarchy cycles frequently remain logically satisfiable because the required disjointness, cardinality, functional-property, or acyclicity axioms are absent. This is an observed validation-surface limitation, not evidence that the injected faults are harmless.

## 5.2 Prior-art retrieval utility

Table 2 reports the sealed test results. All values use the same temporal and family masks and a candidate cutoff of 1,000.

**Table 2. Retrieval results on the sealed test split (198 queries, 479 qrels).**

| System | R@50 | R@100 | R@500 | Success@100 | MRR@500 | nDCG@20 |
|---|---:|---:|---:|---:|---:|---:|
| BM25-Claim (B0) | 0.3535 | 0.4126 | 0.5590 | 0.6414 | 0.2426 | 0.2028 |
| Dense (B2, Titan v2) | 0.2532 | 0.3031 | 0.4566 | 0.4949 | 0.1483 | 0.1188 |
| **Text Hybrid (B3)** | 0.3901 | 0.4315 | 0.6100 | 0.6515 | **0.2531** | **0.2059** |
| CPC/IPC only (B4) | 0.1455 | 0.1860 | 0.3229 | 0.3232 | 0.0620 | 0.0506 |
| Ontology only (B5) | 0.1327 | 0.1800 | 0.3684 | 0.3283 | 0.0485 | 0.0420 |
| Text + Ontology (P0★) | 0.3892 | 0.4635 | 0.6264 | 0.6717 | 0.1909 | 0.1664 |
| **+ ClaimFeature (P1)** | **0.3979** | **0.4849** | **0.6252** | **0.7020** | 0.2276 | 0.1883 |

The prespecified primary configuration P0★ improves family Recall@100 by 0.0319 over B3, but the confidence interval includes zero (95% CI −0.0139 to 0.0785; *p* = .181). The secondary P1 configuration improves Recall@100 by 0.0534 (95% CI 0.0145–0.0926; *p* = .008), with 37 query-level wins, 11 losses, and 150 ties.

The result does not extend to top-rank ordering. Relative to B3, P0★ reduces nDCG@20 by 0.0395 (95% CI −0.0769 to −0.0041; *p* = .029), and P1 changes nDCG@20 by −0.0176 (*p* = .227). MRR shows the same non-improving direction. The ontology component therefore adds known positives within a review depth of 100 but does not improve the ordering of the first 20 results.

The concept-only and classification-only arms are much weaker than the text hybrid. Explicit knowledge is useful here as a reranking signal, not as an independent replacement for lexical and dense retrieval. This conclusion is architecture-specific because ontology evidence cannot introduce a document that is absent from the top-1,000 text candidates.

## 5.3 Subgroup behavior

The prespecified low-overlap prediction is contradicted. On 27 low-overlap queries, P1 changes Recall@100 by −0.0586 relative to B3 (95% CI −0.2099 to 0.0741; *p* = .448). On the other 171 queries, it improves Recall@100 by 0.0711 (95% CI 0.0330–0.1104; *p* < .001). The gap is consistent with a reranking ceiling: when a text pipeline fails to recruit a candidate, later ontology scoring cannot recover it.

The process subgroup, the only adequately sized prespecified process/device group, improves by 0.0584 (*n* = 181; 95% CI 0.0161–0.1006; *p* = .006). Queries whose observed positives are all Korean improve by 0.0936 (*n* = 98; *p* = .004), whereas queries with at least one foreign-language positive improve by 0.0140 (*n* = 100; *p* = .518). These are qrel-conditioned descriptive analyses and must not be read as complete subgroup-safety evidence for an ontology update.

The rejection-ground comparison is underpowered and incomplete. The source contains 400 applications marked for inventive-step rejection and 14 marked for both novelty and inventive step, but no novelty-only rejection. Six hundred applications lack a structured rejection label. Novelty-specific versus inventive-step-specific performance is therefore not testable with this benchmark.

## 5.4 Component ablation and cross-task dependency

**Table 3. Ablation from P1 on family Recall@100. Positive loss means that removing the layer harms P1.**

| Removed layer | Ablated R@100 | Removal loss | Inference |
|---|---:|---:|---|
| CPC/IPC | 0.4824 | +0.0025 | Not significant |
| Process and device | 0.4997 | −0.0147 | Not significant |
| Material, equipment, and failure | 0.4930 | −0.0081 | Not significant |
| ClaimFeature | 0.4779 | +0.0070 | Not significant |
| Rejection ground | 0.4849 | 0.0000 | Structurally inactive in oracle-free mode |
| Hierarchy path | 0.4849 | 0.0000 | Selected weight was zero |
| All ontology features | 0.4315 | +0.0534 | *p* = .008; not significant after Holm across ablations |
| **Expert-matching layer** | **0.4534** | **+0.0316** | **95% CI 0.0105–0.0560; Holm-significant** |

H4 is rejected. Neither ClaimFeature nor rejection-ground evidence shows the expected independent contribution. The observed retrieval gain behaves mainly as a combined concept-overlap signal rather than as the sum of interpretable contributions from each modeled layer.

H5 is also rejected. Removing the expert-matching layer—designed as a negative control—reduces Recall@100 by 0.0316 (*p* = .002), the only ablation that remains significant after Holm correction. This should not be interpreted as a causal estimate of expert knowledge. It is evidence that the task views are empirically dependent in the implemented graph and scoring pipeline. Concepts or paths thought to be exclusive to one view can affect another through shared T-Box structure, feature extraction, or graph connectivity. The failed negative control therefore supplies a practical argument for T3.

## 5.5 Fault-injection results

The preregistered H1 is rejected. Under the original existence-only CQ rule, T3 detects none of the 18 cross-task faults. Across all 108 faults, the formal stack detects 19 instances that the task gate misses, whereas the task gate detects none missed by the formal stack; the McNemar direction is opposite to the hypothesis (*p* < .0001). The false-positive rate is 0/18.

Two engineering defects explain the result. First, 26 of 28 CQs merely required at least one result row, making local damage invisible. Second, L3 counted all task suites and therefore subsumed T3. A distribution-sensitive CQ rule raises T3 detection to 34/108 at \(\tau=0.05\), but T3-only detection remains impossible until the layer surfaces are separated.

After L3 was restricted to the primary-task suite and T3 retained the expert-matching, foresight, and core suites, total CQ coverage remained unchanged: the coverage invariant held for all 144 evaluated instances. Reanalysis of the original data produced 5/18 T3-only cross-task detections and 0/27 false positives. This result is exploratory because the rule was revised after inspecting the first experiment.

The frozen rule was subsequently evaluated on untouched holdout instances. Table 4 reports the confirmatory result.

**Table 4. Holdout evaluation of the revised, disjoint T3 rule.**

| Prespecified condition | Result | Verdict |
|---|---:|---|
| At least one T3-only detection among cross-task faults | 12/45 | Pass |
| One-sided McNemar, T3 over L3 | *b* = 0, *c* = 14, *p* = .0001 | Pass |
| False-positive rate no greater than 5% | 0/27 | Pass |

Detection varies by fault family. Expert-skill hub concentration is detected in 6/9 cases, synonym over-merging in 6/9, expert-case/failure-mode reassignment in 2/9, and value-chain direction reversal in 2/9. A subprocess-direction reversal remains undetected in 0/9 cases because the relevant CQ does not fix direction and no structural directionality constraint exists.

The result is threshold-sensitive. T3-only detections are 17/45 at \(\tau=0\), 12/45 at the prespecified \(\tau=0.05\), and 4/45 at \(\tau=0.10\); at 0.10, the directional test is not significant (*p* = .3438). The holdout also does not establish specificity against non-cross-task faults because such faults were not included in its fault denominator. H1 is therefore supported only for the frozen 0.05 rule, the tested cross-task fault distribution, and the stated false-positive controls.

## 5.6 Cross-language diagnostic

Across the development and test splits, BM25 retrieves none of 334 English positive documents for Korean queries. On English positives, the ontology-only arm retrieves 14/128 in the test split, compared with 6/128 for the text hybrid; the same ordering occurs in development. The final reranker does not retain this advantage because its candidate set is inherited from the text hybrid.

This observation identifies a future design direction—ontology-based candidate generation or union-of-arms retrieval—but is not a confirmatory cross-language result. The pool of foreign-language positives is selected and highly biased, the denominator is positive-only, and the frozen architecture did not test concept-based candidate expansion.

## 5.7 Hypothesis summary

| Hypothesis | Result | Interpretation |
|---|---|---|
| H1, original | Rejected | Existence-only CQs and overlapping L3/T3 surfaces prevent the predicted discrimination |
| H1, revised holdout | Supported within scope | 12/45 T3-only detections; *p* = .0001; 0/27 false positives; threshold-sensitive |
| H2, version approval safety | **Not yet assessed** | Requires the same pipeline under O and O′; P1 versus B3 cannot supply this evidence |
| H3, hybrid retrieval | Partially supported | Secondary P1 improves R@100; primary P0★ is nonsignificant; nDCG and low-overlap conditions fail |
| H4, ClaimFeature and rejection-ground specificity | Rejected | Independent contributions are not supported |
| H5, expert-layer negative control | Rejected | Removal harms retrieval, indicating cross-task dependency |

# 6. Discussion

## 6.1 From ontology validity to update safety

The principal contribution is not a new retrieval score but a distinction among kinds of evidence. A graph can be syntactically valid, structurally compliant, and logically satisfiable while still being unsafe for an application. Conversely, a system-level improvement can result from changing the pipeline rather than from a safe ontology update. Approval of O′ therefore requires a paired, same-pipeline comparison with O.

This distinction changes how ontology evolution should be reported. “The ontology-enhanced system outperformed the text baseline” is a utility statement. “The candidate ontology version is non-inferior to the baseline version” is an update-safety statement. “The gate detects a controlled regression” is a test-system statement. Conflating them can allow an improved model to hide a damaging graph change or allow a useful ontology to be credited for an unrelated model change.

## 6.2 Why cross-task non-regression is independent

The holdout experiment shows that a disjoint cross-task CQ layer can reveal changes that the primary-task CQ layer does not attribute. Its value is not merely another aggregate pass/fail indicator. T3 identifies which sibling-task specification regressed and can therefore route a failed update to the relevant owner.

The expert-layer ablation provides complementary evidence. A layer designed to be irrelevant to retrieval was not empirically isolated. Because several views share concepts and paths, local changes may have nonlocal effects. The result justifies cross-task protection, but it also cautions against strong language such as “causal task entanglement.” The ablation does not identify whether the mechanism is semantic dependency, feature-extraction coupling, or graph-connectivity change.

## 6.3 Retrieval utility is bounded to deep recall

The strongest positive retrieval result is an increase in family Recall@100 for a secondary configuration. Three boundaries are important.

First, the prespecified primary configuration does not reach significance. Reporting P1 as a secondary result avoids replacing the primary system after observing the test set.

Second, nDCG@20 and MRR do not improve. The system recruits more known positives by rank 100 but does not order the head of the list more effectively. This may still be useful for recall-oriented patent review, but it is not a general ranking improvement.

Third, the effect is concentrated in higher-overlap queries. The architecture reranks rather than expands the candidate set; it cannot solve the very cases in which the text system retrieves no useful candidates. Future work should test concept-based query expansion or a union of text and ontology candidate generators under a new preregistered protocol.

## 6.4 Negative results as engineering evidence

Several null or adverse results improve the design. The failure of the original H1 exposed an existence-only CQ weakness. The second failure exposed set inclusion between validation layers. The undetected subprocess-direction reversal identifies a missing directional constraint. The ClaimFeature ablation prevents an unsupported fine-grained semantic claim. The low-overlap result reveals the ceiling of reranking.

Such results are particularly valuable for AEI's engineering orientation because they identify failure modes and design conditions. The revised gate is more credible because the manuscript retains the sequence of failure, diagnosis, revision, and untouched holdout confirmation.

## 6.5 Practical release policy

A practical ontology release can use the following decision policy:

1. reject stale, unsigned, or leakage-contaminated artifacts at L0;
2. reject declared structural and logical violations at L1–L2;
3. reject primary-task CQ regressions at L3;
4. run the same frozen application pipeline with O and O′;
5. reject non-inferior-mean but unsafe-subgroup changes at T2;
6. reject sibling-task or core-CQ regressions at T3;
7. record waivers only for machine-verifiable delta types, such as exact duplicate removal;
8. publish the gate report with the ontology release.

A failure should initiate diagnosis, not imply that the entire change is worthless. Splitting, repairing, or conditionally releasing a delta may be preferable to permanent rejection.

# 7. Threats to validity

## 7.1 Construct validity

Examiner citations are incomplete positives, not exhaustive relevance judgments. Family Recall@100 measures recovery of observed citations, not legal relevance, novelty, inventive step, or examiner effort. Binary nDCG is additionally limited because all qrels have the same gain. Independent expert assessment of unseen candidates is required before precision, legal utility, or review-cost claims are made.

The retrieval architecture measures ontology reranking over a text candidate pool. It does not estimate the maximum value of ontology-based retrieval or candidate generation. The cross-language diagnostic is particularly affected.

## 7.2 Internal validity

The test split was opened once, but P1 is a secondary configuration and must remain labeled as such. Several gate revisions were informed by the initial fault results. Only the final holdout is confirmatory for the revised rule. The chronology and all adverse intermediate outcomes are therefore reported.

The expert-layer ablation shows dependency but does not isolate the mechanism. A graph perturbation can affect several derived features at once. Additional mediation tests or feature-lineage tracing would be required for causal interpretation.

## 7.3 Statistical conclusion validity

The test set contains 198 queries, but many subgroup samples are much smaller. Only groups meeting the prespecified minimum should block a release. Multiple ablations are Holm-corrected. The revised T3 result depends on the prespecified \(\tau=0.05\) and fails at 0.10; a threshold chosen for another deployment requires new calibration.

The positive-only qrels create many ties and prevent conventional precision estimation. Values derived by treating unjudged documents as nonrelevant are not used as principal evidence.

## 7.4 External validity

The evidence comes from one semiconductor ontology, one Korean patent setting, and two realized graph generations. There is no basis for claiming a longitudinal trend or universal threshold. Replication is needed in other engineering domains, ontology sizes, and application portfolios.

The holdout contains cross-task faults and valid deltas but no new non-cross-task fault families. It confirms incremental cross-task detection, not full gate completeness or cross-task specificity.

## 7.5 Resource and reproducibility validity

KIPRIS collection conditions limit unrestricted redistribution of source texts. Reproduction therefore depends on public schema, identifiers, provenance, hashes, rebuilding scripts, and permitted derived artifacts. The immutable release DOI, commit hash, final license matrix, and exact graph counts must be frozen before submission.

The L2 layer is under-specified in the current T-Box. Passing it should not be interpreted as strong logical assurance until disjointness, cardinality, functional-property, and directionality constraints are modeled and tested.

# 8. Data and code availability

The development repository is available at [https://github.com/arkwith7/sdkb-prior-art-paper](https://github.com/arkwith7/sdkb-prior-art-paper). The version of record will cite an immutable release DOI and commit. The reproducibility package is intended to include the distributable SDKB schema and metadata, provenance and license manifests, SHACL shapes, task-assigned CQs, graph-count reports, temporal and family splitting code, citation-edge masking and leakage tests, retrieval configurations, fault generators, gate reports, and machine-readable result tables.

Patent texts or other source material that cannot be redistributed will be replaced by authorized reconstruction instructions, stable identifiers, hashes, and derived statistics. Availability statements will distinguish public artifacts from access-controlled source data.

# 9. Conclusions

This paper presents a validation-gated approach to the evolution of SDKB, a multi-task semiconductor ontology dataset supporting expert matching, prior-art retrieval, and technology foresight. The approach combines graph-integrity, structural, logical, and primary-task functional checks with same-pipeline non-inferiority, subgroup safety, and cross-task CQ non-regression.

The empirical evidence supports two bounded conclusions. First, ontology and claim-feature reranking can improve deep recovery of examiner-cited patent families: a secondary configuration increases family Recall@100 by 0.0534 over the strongest text hybrid. The prespecified primary configuration is not significant, top-rank ordering does not improve, and the predicted low-overlap benefit is absent. Second, after overlapping validation surfaces were separated and the rule was frozen, T3 detects 12 of 45 previously unseen cross-task faults missed by the primary-task CQ layer, with no false positives among 27 valid deltas. A failed expert-layer negative control further indicates that shared ontology views are empirically dependent.

These findings support cross-task non-regression as a necessary complement to formal and single-task validation. They do not yet demonstrate that a specific ontology version is safe to approve. That claim requires the same retrieval pipeline to be executed with the old and candidate ontologies and evaluated under T1–T3. Keeping that requirement explicit is the central methodological boundary of the paper.

# Declarations

## CRediT authorship contribution statement

[To be completed for each author before submission.]

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper. [Confirm before submission.]

## Funding

[Insert funder names, grant numbers, and the funders' roles, or state that the research received no specific grant.]

## Ethical and legal considerations

The study evaluates information-retrieval and ontology-validation methods using patent records and derived metadata. It does not involve human participants. Any expert-judgment study added before submission must receive the applicable institutional determination and informed-consent treatment.

## Declaration of generative AI and AI-assisted technologies

Generative AI was used to assist manuscript restructuring and language drafting. The authors remain responsible for the research questions, experimental design, data, code, statistical analyses, citations, and verification of every claim. Generative AI did not perform legal patentability assessment or replace expert judgment.

# References

Alcácer, J., & Gittelman, M. (2006). Patent citations as a measure of knowledge flows: The influence of examiner citations. *The Review of Economics and Statistics, 88*(4), 774–779. https://doi.org/10.1162/rest.88.4.774

Alcácer, J., Gittelman, M., & Sampat, B. (2009). Applicant and examiner citations in U.S. patents: An overview and analysis. *Research Policy, 38*(2), 415–427. https://doi.org/10.1016/j.respol.2008.12.001

Bayerlein, B., Schilling, M., Birkholz, H., Jung, M., Waitelonis, J., Mädler, L., & Sack, H. (2024). PMD Core Ontology: Achieving semantic interoperability in materials science. *Materials & Design, 237*, 112603. https://doi.org/10.1016/j.matdes.2023.112603

Bekamiri, H., Hain, D. S., & Jurowetzki, R. (2024). PatentSBERTa: A deep NLP based hybrid model for patent distance and classification using augmented SBERT. *Technological Forecasting and Social Change, 206*, 123536. https://doi.org/10.1016/j.techfore.2024.123536

Choi, Y. (2009). Korean to English Patent Automatic Translation (K2E-PAT) and cross lingual retrieval on KIPRIS. *World Patent Information, 31*(2), 135–136. https://doi.org/10.1016/j.wpi.2008.09.005

Flouris, G., Manakanatas, D., Kondylakis, H., Plexousakis, D., & Antoniou, G. (2008). Ontology change: Classification and survey. *The Knowledge Engineering Review, 23*(2), 117–152. https://doi.org/10.1017/S0269888908001367

Ghosh, M., Rose, M. E., Erhardt, S., Buunk, E., & Harhoff, D. (2024). PaECTER: Patent-level representation learning using citation-informed transformers. *arXiv*. https://doi.org/10.48550/arXiv.2402.19411

Gruber, T. R. (1993). A translation approach to portable ontology specifications. *Knowledge Acquisition, 5*(2), 199–220. https://doi.org/10.1006/knac.1993.1008

Grüninger, M., & Fox, M. S. (1995). Methodology for the design and evaluation of ontologies. In *Proceedings of the IJCAI-95 Workshop on Basic Ontological Issues in Knowledge Sharing*.

Heist, N., Hertling, S., & Paulheim, H. (2023). KGrEaT: A framework to evaluate knowledge graphs via downstream tasks. In *Proceedings of the 32nd ACM International Conference on Information and Knowledge Management* (pp. 3938–3942). https://doi.org/10.1145/3583780.3615241

Kontokostas, D., Westphal, P., Auer, S., Hellmann, S., Lehmann, J., Cornelissen, R., & Zaveri, A. (2014). Test-driven evaluation of linked data quality. In *Proceedings of the 23rd International Conference on World Wide Web* (pp. 747–758). https://doi.org/10.1145/2566486.2568002

Krestel, R., Chikkamath, R., Hewel, C., & Risch, J. (2021). A survey on deep learning for patent analysis. *World Patent Information, 65*, 102035. https://doi.org/10.1016/j.wpi.2021.102035

Li, H., Wang, C., & Lambrix, P. (2024). Initial development of an ontology for the semiconductor domain—SemicONTO. In *Proceedings of the First International Workshop on Semantic Materials Science* (CEUR Workshop Proceedings, Vol. 3760, pp. 120–127). https://ceur-ws.org/Vol-3760/paper12.pdf

Lupu, M., & Hanbury, A. (2013). Patent retrieval. *Foundations and Trends in Information Retrieval, 7*(1), 1–97. https://doi.org/10.1561/1500000027

Magdy, W., & Jones, G. J. F. (2014). Studying machine translation technologies for large-data CLIR tasks: A patent prior-art search case study. *Information Retrieval, 17*(5–6), 492–519. https://doi.org/10.1007/s10791-013-9231-6

Mahdabi, P., & Crestani, F. (2014). Query-driven mining of citation networks for patent citation retrieval and recommendation. In *Proceedings of the 23rd ACM International Conference on Information and Knowledge Management* (pp. 1659–1668). https://doi.org/10.1145/2661829.2661899

Piroi, F., & Hanbury, A. (2019). Multilingual patent text retrieval evaluation: CLEF–IP. In *Information Retrieval Evaluation in a Changing World* (pp. 365–387). Springer. https://doi.org/10.1007/978-3-030-22948-1_15

Potoniec, J., Wiśniewski, D., Ławrynowicz, A., & Keet, C. M. (2020). Dataset of ontology competency questions to SPARQL-OWL queries translations. *Data in Brief, 29*, 105098. https://doi.org/10.1016/j.dib.2019.105098

Poveda-Villalón, M., Fernández-Izquierdo, A., Fernández-López, M., & García-Castro, R. (2022). LOT: An industrial oriented ontology engineering framework. *Engineering Applications of Artificial Intelligence, 111*, 104755. https://doi.org/10.1016/j.engappai.2022.104755

Rajamohan, B. P., Bradley, A. C. H., Tran, V. D., et al. (2025). Materials Data Science Ontology (MDS-Onto): Unifying domain knowledge in materials and applied data science. *Scientific Data, 12*, 628. https://doi.org/10.1038/s41597-025-04938-5

Risch, J., Alder, N., Hewel, C., & Krestel, R. (2020). PatentMatch: A dataset for matching patent claims and prior art. *arXiv*. https://doi.org/10.48550/arXiv.2012.13919

Sapel, P., Molinas Comet, L., Dimitriadis, I., Hopmann, C., & Decker, S. (2025). A review and classification of manufacturing ontologies. *Journal of Intelligent Manufacturing, 36*, 3669–3693. https://doi.org/10.1007/s10845-024-02425-z

Shalaby, W., & Zadrozny, W. (2019). Patent retrieval: A literature review. *Knowledge and Information Systems, 61*, 631–660. https://doi.org/10.1007/s10115-018-1322-7

Siddharth, L., Li, Y., & Luo, J. (2022). Retrieving technologically distant patents using a knowledge graph approach. *Journal of Engineering Design, 33*(8–9), 670–683. https://doi.org/10.1080/09544828.2022.2144714

W3C. (2017). *Shapes Constraint Language (SHACL)*. W3C Recommendation. https://www.w3.org/TR/shacl/

Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data, 3*, 160018. https://doi.org/10.1038/sdata.2016.18

Zaveri, A., Rula, A., Maurino, A., Pietrobon, R., Lehmann, J., & Auer, S. (2016). Quality assessment for linked data: A survey. *Semantic Web, 7*(1), 63–93. https://doi.org/10.3233/SW-150175

---

# 투고 전 필수 완료 항목 — 제출 본문에서 제외

아래 항목 중 1–4는 심사 대응력이 아니라 **주장의 성립 여부**에 직접 영향을 주므로 완료 전 투고를 권하지 않는다.

- [ ] **O 대 O′ 동일 파이프라인 실험:** P1 또는 최종 동결 파이프라인을 기존 온톨로지 O와 후보 온톨로지 O′에 동일하게 실행한다. \(\Delta R_{\Delta G}\)의 paired bootstrap CI, T2 하위집단 최대 하락, T3 CQ 비회귀를 산출한다. 이 결과가 없으면 H2와 “update approval safety”는 계속 미검정으로 남겨야 한다.
- [ ] **독립 전문가 판정:** 최소 50개 질의에서 시스템이 새로 회수한 미판정 후보를 표본화하고, 두 명 이상의 전문가가 관련성·검토 필요성·판정 시간을 독립 평가한다. 합의도와 adjudication 절차를 보고한다. 실시하지 못하면 precision, review-cost reduction, legal relevance 주장을 추가하지 않는다.
- [ ] **특허 특화 dense 기준선:** PatentSBERTa 또는 PaECTER 등 공개 재현 가능한 특허 기준선을 개발셋에서 고정하고 test에 1회 적용한다. 현재 Titan v2만으로는 “강한 특허 의미검색 기준선”이라는 표현을 쓰지 않는다.
- [ ] **불변 릴리스 고정:** DOI, commit hash, 실행 환경, 랜덤 시드, 그래프별 자동 계수, CQ 결과, 라이선스 매트릭스를 한 릴리스로 고정한다.
- [ ] **숫자 정합성 자동 검사:** ClaimFeature 1,289,512, `dependsOnClaim` 483,394, sidecar 11,605,931을 정본으로 삼거나 자동 계수 결과에 맞춰 전 문서·표·코드를 일괄 수정한다.
- [ ] **L2 범위 결정:** disjointness·cardinality·functional·directionality 제약을 실제로 추가하고 재실행하거나, 현행 L2가 약한 탐지면임을 본문처럼 유지한다. 미실행 제약을 완료된 것으로 서술하지 않는다.
- [ ] **F12 방향성 결손 처리:** `hasSubprocess` 방향 고정 CQ/SHACL을 추가하는 경우 기존 holdout 결과와 분리해 “후속 수정”으로 보고한다.
- [ ] **도표 생성:** Fig. 1 검증 구조, Fig. 2 Recall@100 및 nDCG 차이, Fig. 3 ablation, Fig. 4 fault-detection chronology를 코드에서 재생성하고 번호·캡션·본문 호출 순서를 맞춘다.
- [ ] **인용 전수 확인:** 저자명, 연도, 권·호, 페이지, DOI를 원문과 대조하고 Elsevier 양식으로 변환한다.
- [ ] **데이터 권리 문구 검토:** KIPRIS 원문·메타데이터·식별자의 재배포 가능 범위를 이용 조건과 기관 승인에 맞게 법률·행정적으로 재확인한다.
- [ ] **저자·기관·기여·연구비·이해상충 입력:** 익명 심사본과 title page를 분리한다.
- [ ] **영문 교정:** 의미를 바꾸지 않는 범위에서 전문 교정을 시행하고, 교정 후 수치·가설 판정·표 호출을 다시 자동 검사한다.
- [ ] **AEI 최신 투고 규정 확인:** 초록 제한, highlights 파일, graphical abstract 선택 여부, double-anonymous 파일 구성, 데이터 정책, AI 사용 고지 문구를 제출 당일 Guide for Authors와 대조한다.

# 보충자료 구성안 — 별도 파일로 분리

| 파일 | 권장 내용 |
|---|---|
| Supplement S1 | 사전등록 시점, commit, test 개봉 기록, H1→H1′→H1″→H1‴ 연대기 |
| Supplement S2 | 108개 최초 결함 및 72개 holdout 인스턴스의 전체 fault matrix |
| Supplement S3 | \(\tau\in\{0,0.05,0.10\}\) 민감도, 검출–위양성 trade-off |
| Supplement S4 | 전체 시스템의 query-level bootstrap CI, 승/패/동, subgroup 세부표 |
| Supplement S5 | 31개 CQ의 task suite, polarity, minimum rows, baseline rows, sidecar 여부 |
| Supplement S6 | 데이터 계보, provenance, 라이선스, 재구축 절차, 해시와 자동 계수 |
| Supplement S7 | 교차언어 문서 단위 진단과 후보-pool 편향 분석 |
| Supplement S8 | 전문가 판정 프로토콜·양식·합의도·review-time 결과(실시 후) |

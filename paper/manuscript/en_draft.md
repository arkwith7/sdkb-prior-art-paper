# A Task-Aware Release Gate for Shared Engineering Ontologies with Multiple Task Views: A Design Science Study in Semiconductor Prior-Art Retrieval

## Abstract

Engineering ontologies keep changing after release. Whether a change passing structural and logical checks preserves task performance is a question resource-level evaluation leaves open. When tasks share a vocabulary, a change approved on one task's score can break another's query paths. Following design science research, we present two artifacts and an evaluation environment. SDKB (Semiconductor Domain Knowledge Base) carries expert matching, prior-art search and foresight as task views on one shared schema (T-Box). A task-aware release gate adds three conditions to four formal validation layers (L0–L3): retrieval non-inferiority (T1), subgroup non-regression guardrail (T2), and non-regression of other tasks' competency questions (T3). A multi-layer benchmark evaluates both in four episodes: a representation audit (SHACL, 31 competency questions); holdout fault injection on 45 unjudged faults; a controlled resource swap with documents, code and settings frozen; and a leakage-controlled retrieval comparison over two non-overlapping splits of 198 queries, anchored on examiner citations for 1,000 rejected patents. In the swap, a change raising concepts per document 2.4-fold and passing every formal layer reduced retrieval (family Recall@100 −0.0293, 95% CI [−0.0542, −0.0053]); T1 rejected it. T3 alone detected 12 of 45 cross-task faults, with no false alarms in 27. The pre-registered composite prediction held in neither split: deep recall improved in both (+0.0534, +0.0343), while the pre-specified primary configuration and nDCG@20 did not. We derive four core and two scope design principles, and state the limits: one domain, one refusal of undistinguished cause, no expert relevance judgments, and queries confined to patents in the graph.

**Keywords:** semiconductor domain ontology dataset; ontology evolution; task-aware release gate; cross-task non-regression; proxy-metric mismatch; prior-art retrieval; design science research

## Nomenclature

Abbreviations are given in full at first use and abbreviated thereafter. The names of gates and
metrics (L0–L3, T1–T4, Recall@100, nDCG@20) are used verbatim throughout: replacing them with
paraphrases would change what they refer to.

| Abbreviation | Expansion |
|---|---|
| A-Box | assertional box — the instance layer of an ontology (§3.1) |
| CQ | competency question — a question the ontology must be able to answer (§3.1) |
| DSR | design science research (§1) |
| EP1–EP4 | the four evaluation episodes (§4, §5) |
| DP1–DP6 | the design principles derived in §6.4 |
| IPC / CPC | International / Cooperative Patent Classification |
| KIPRIS | Korea Intellectual Property Rights Information Service |
| L0–L3 | the four formal validation layers: freshness, structure, logic, function (§3.4) |
| nDCG@20 | normalized discounted cumulative gain at rank 20 |
| Recall@100 | recall at retrieval depth 100, computed at patent-family level |
| RRF | reciprocal rank fusion |
| SHACL | Shapes Constraint Language |
| SPARQL | SPARQL Protocol and RDF Query Language |
| T-Box | terminological box — the schema layer of an ontology (§3.1) |
| T1–T4 | the task conditions of the release gate (§3.5) |

---

# 1. Introduction

The arrival of large language models (LLMs) and retrieval-augmented generation (RAG) in engineering
practice has widened, not narrowed, the role of explicit knowledge representation (Lewis et al.,
2020; Pan et al., 2024). What constrains a model that generates something untrue is not a larger
model but a verifiable knowledge structure. Engineering informatics has pursued the same line,
integrating design assets and processes into knowledge graphs (Bharadwaj & Starly, 2022). The demand
is strongest in domains such as semiconductors, where process, device, material, equipment and
organization are densely coupled: the same physical phenomenon is named differently depending on
context, so retrieval that relies on string matching leaves connections unreached.

Semiconductor knowledge is not used by a single task. An equipment defect must be traced from a
failure mode through root causes to the people and skills that address it. Patent analysis must run
from claims through their limitations to a prior-art judgement, and technology planning must connect
technology nodes to scenarios and investment options. These three are not separate repositories but
different uses of the same knowledge, sharing a vocabulary of processes, devices, materials,
equipment and organizations. **SDKB** (Semiconductor Domain Knowledge Base) is a semiconductor
domain ontology dataset that grew by admitting these three requirements in turn.

**Task-extensible**, here, does not mean that one ontology performs equally well on every task. It
means that classes, relations, constraints, competency questions (CQs) and instances (the A-Box) can
be added for each task while the shared schema (T-Box) and the identifiers are preserved — and that
those additions do not damage the existing structure. What an ontology can *represent* and how far
its performance has been *verified* must therefore be stated separately.

Among the three tasks, prior-art retrieval sits at the front end of research and development and is
also amenable to quantitative measurement. Pre-filing novelty and inventive-step judgements and
search reports depend on it, and the documents an examiner actually cited supply an external
scoring standard. Relevant prior art, however, may describe the same invention in different terms
and at a different level of abstraction. Semantic connections that cross vocabulary boundaries are
therefore required, and that is precisely why an ontology is coupled to this task. Yet patent
retrieval research and ontology quality validation have developed with little reference to each
other (§2), and passing the ontology-side checks does not guarantee retrieval performance.

This mismatch takes two forms. First, a change can pass all four conventional layers of ontology
change validation — freshness, structure, logic and function (L0–L3) — and still degrade retrieval
on a sealed evaluation set. We call this **task-semantic regression**. Second, when one vocabulary
supports three tasks, a change that favours one task can damage another task's query paths. Merging
two similar concepts to raise recall, for instance, degrades the ability to discriminate `Skill` in
expert matching. We call this **cross-task regression**.

Both arise from one cause. Whoever edits an ontology usually observes resource-side indicators: the
growth of the vocabulary, the number of concepts per document, the number of links repaired. By
**resource** we mean the dataset in its state before it enters an application — the T-Box, the A-Box
and the document-to-concept links. Evaluation, however, has three layers — resource, retrieval and
generation (§2.3) — and whether an indicator at one layer represents performance at the next cannot
be known before it is measured.

The question this study raises is therefore a single one. When an ontology dataset that represents
three tasks grows, does it preserve the performance of the primary task without damaging the
function of the others — and how can that be established *before* release?

We address the question as design science research (DSR; Hevner et al., 2004; Gregor & Hevner,
2013). What we ask is not whether a hypothesis is accepted, but how the artifacts were designed and
evaluated and what transferable design knowledge follows.

- **RQ1** — How can one design an ontology dataset that represents three tasks on a single shared
  T-Box while remaining extensible per task? (§3 · EP1)
- **RQ2** — How can one design a gate that evaluates, before release, whether a formally valid
  change damages downstream task performance or the function of the other tasks? (§3 · EP2 · EP3)
- **RQ3** — What utility, failure boundaries and cross-layer indicator mismatches are observed in
  evaluating the artifacts, and what transferable design principles follow? (EP3 · EP4 · §6)

The contribution is threefold. The first is the **artifact**: SDKB, an ontology dataset that
connects three semiconductor knowledge tasks through common identifiers and a shared T-Box and
supplies per-task views, competency questions and validation assets. The second is the **method**: a
release gate (T-gate) that adds to formal validity the non-inferiority of the primary task, subgroup
safety, and preservation of cross-task function as conditions of release approval, together with an
evaluation of its discriminating power by holdout fault injection and by an actual resource swap.
The third is **design knowledge**: a controlled swap in which a change that improved the resource
indicators and passed every formal check nevertheless degraded retrieval, and from that observation
the transferable principles of layered validation and approval one layer down.

The weight of the latter two contributions lies less in the design itself than in the measurements
that show the design to be necessary. Retrieval utility is therefore reported only with its
boundaries stated, and the evaluation of whether retrieval gains transfer to the generation layer is
not presented as a separate contribution. The deficits in validation strength and generalizability
are set out as a specification in §6.5.

The remainder is organized as follows. Section 2 states the research gap; Section 3 the artifacts
and the design and evaluation procedure; Section 4 the evaluation design. Section 5 reports the four
episodes, and Section 6 the design principles, limitations and conclusion.

![Figure 1. Study overview — two artifacts and one evaluation environment, the release approval procedure, and what the four episodes measure.](../../figures/concept_overview.svg)

**Figure 1.** Study overview. The top band is artifact A1, a resource placing three task views on one shared T-Box; the middle band is artifact A2, the release gate that reviews a resource change before it ships; the bottom band is evaluation environment E1, the four episodes and what each measures. The middle band reads left to right, and a failed stage stops the ones behind it. T4, shown dashed, is not part of the approval rule (§3.5.1).

The full text of abridged sections, the appendices and the auxiliary tables are reproduced verbatim
in the supplementary material [S5](../../supplementary/S5-submission-full-v2.md).

---

# 2. Background and research gap

This section reviews four strands in turn: the unit of evaluation and the nature of ground truth in
prior-art retrieval (§2.1); how ontology quality validation came to rest on post-hoc comparison
(§2.2); the proxy validity of resource-side indicators (§2.3); and the position of this study
(§2.4). Taken together they leave one gap. For an ontology that supports several tasks at once,
there is no procedure that decides, before release, whether a change may be accepted.

**Table 1. Position relative to prior work — the contribution is the combination and the experimental design, not primacy.**

|Research strand|Representative work|Remaining gap|What this study adds|
|---|---|---|---|
|Patent prior-art retrieval and the use of graphs| Lupu & Hanbury (2013); Krestel et al. (2021); Mahdabi & Crestani (2014); Siddharth et al. (2022) |The graph serves as an input representation for performance; controlling change in the graph itself is not addressed|On top of query-citation masking and time/family separation, retrieval performance becomes an approval condition for resource change, and the **performance ceiling** of that coupling is reported|
|Ontology quality and evolution validation| Kontokostas et al. (2014); Keet & Ławrynowicz (2016); W3C (2017); Zablith et al. (2015) |Asks only whether a change damages the ontology, not whether it damages a task|A 3-condition task gate and a non-inferiority merge rule on top of formal validation|
|Task-based and downstream evaluation| Porzel & Malaka (2004); Brank et al. (2005); Heist et al. (2023) |Used as a **criterion** for comparing and selecting ontologies, or as a post-hoc comparison once construction is finished|The same task performance becomes a term in the approval rule applied **before** release|
|The practice of treating resource indicators as proxies for utility| Strathern (1997); Chiu et al. (2016); Thomas & Uminsky (2020) |The mismatch is reported at the level of correlation; **a controlled case and a decision taken on it** are rare|Controlled confirmation in two conditions differing only in the resource bundle, and an **approval verdict** (§5.3)|
|Semantic representation, validation and application in engineering informatics| Schönfelder & König (2025); Kosse et al. (2025); Speiser et al. (2026); Solihin et al. (2015); Pauwels et al. (2024) |Standardized representation, structural conformance and application performance are shown; **a rule for approving change** is not addressed|Judges **whether a change may be accepted** rather than whether the resource is usable, and reports an actual review (§5.3)|
|Cross-domain use of a shared graph| Johansen et al. (2025) |Stops at **observing** influence between domains|Enforces the same influence as an approval condition — **cross-task non-regression**|

# Cover letter — Advanced Engineering Informatics

To the Editors of *Advanced Engineering Informatics*

Dear Editors,

We submit **"A Task-Aware Release Gate for Shared Engineering Ontologies with Multiple Task Views:
A Design Science Study in Semiconductor Prior-Art Retrieval"** for consideration as a full research
paper.

**The problem.** Engineering ontologies do not stop changing once released; they change whenever the
products, processes and equipment they describe change. Current practice admits a change when it
passes structural and logical validation. That test is silent on the question a maintainer actually
faces — whether the change preserves the performance of the tasks the ontology serves — and the
silence is costly when several tasks share one vocabulary, because a change justified by one task's
score can break another task's query paths.

**What we contribute.** Following design science research, we present two artifacts and an
evaluation environment, and we report what evaluating them taught us. SDKB is a semiconductor domain
ontology dataset that carries expert matching, prior-art search and technology foresight as task
views on one shared T-Box. The task-aware release gate adds three conditions to four layers of
formal validation: retrieval non-inferiority, a subgroup non-regression guardrail, and
non-regression of the other tasks' competency questions. The benchmark measures both over 1,000 rejected Korean patents with
examiner citations as partial ground truth, under leakage control, on two non-overlapping
confirmatory splits.

**The central finding is negative, and that is why we think it matters.** In a controlled swap where
documents, code and settings were frozen and only the resource bundle was replaced, a change that
raised concepts per document 2.4-fold and passed every formal layer *reduced* retrieval (family
Recall@100 −0.0293, 95% CI [−0.0542, −0.0053]). The retrieval condition refused it. A widely held
assumption — that improving an ontology's internal quality improves the tasks built on it — did not
hold, and the refusal is the artifact doing its job. We report the boundary of the positive results
with the same care: deep recall improved on both splits, but the pre-registered composite prediction
held in neither, and the pre-specified primary configuration did not reach significance.

**Fit with the journal.** The paper is squarely in the journal's territory: explicit knowledge
representation in OWL, SHACL and SPARQL; a knowledge-intensive engineering task; and an evaluation
that is quantitative, pre-registered and adversarial toward its own hypotheses. It speaks to a
question every shared engineering ontology eventually faces — how to decide what may be released.

**Openness.** The dataset, the evaluation harness, the frozen thresholds, the split and
relevance-judgment identifiers, the fault-injection specifications and the figure-generating code
are public under a DOI, with per-file SHA-256 for all published assets. Patent full text is not
redistributable under the source database's academic-use terms; identifiers and a refetch procedure
are provided instead, and the resulting limits on independent reproduction are stated explicitly
rather than glossed.

**What we do not claim.** We do not propose a retrieval or generation method, we do not claim
performance for the two non-retrieval task views, and we do not claim the gate has been shown to
keep approved changes safe — that comparison did not become possible within this study, and we say
so. The pre-registrations, including the ones whose predictions failed, are cited and reported in
full.

The manuscript is original, is not under consideration elsewhere, and all authors have approved this
submission. We have no competing interests to declare. We would be glad to suggest reviewers with
expertise in ontology evolution, knowledge-graph evaluation, or patent information retrieval should
that be useful.

Thank you for your consideration.

Sincerely,

HyoungSik Park
Graduate School of Management of Technology, Sungkyunkwan University
richphs@skku.edu

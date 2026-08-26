# Cover letter — Results in Engineering

To the Editors of *Results in Engineering*

Dear Editors,

We submit **"A Task-Aware Release Gate for Evolving Shared Engineering Ontologies: Evidence from
Semiconductor Prior-Art Retrieval"** for consideration as a full research
paper.

**The problem.** Engineering ontologies do not stop changing once released; they change whenever the
products, processes and equipment they describe change. Current practice admits a change when it
passes structural and logical validation. That test is silent on the question a maintainer actually
faces, namely whether the change preserves the performance of the tasks the ontology serves. That
silence is costly when several tasks share one vocabulary. A change justified by one task's score
can disrupt another task's query paths.

**What we contribute.** Following design science research, we present two artifacts and an
evaluation environment, and we report what evaluating them taught us. SDKB is a semiconductor domain
ontology dataset that carries expert matching, prior-art search and technology foresight as task
views on one shared T-Box. The task-aware release gate adds three conditions to four layers of
formal validation: retrieval non-inferiority, a subgroup non-regression guardrail, and
non-regression of the other tasks' competency questions. The benchmark measures both over 1,000 rejected Korean patents with
examiner citations as partial ground truth, under leakage control, on two non-overlapping
confirmatory splits.

**The central finding is negative, and that is why we think it matters.** We froze documents, code
and settings and replaced only the resource bundle. In that controlled swap a change that raised
concepts per document 2.4-fold and passed every formal layer *reduced* retrieval (family Recall@100
−0.0293, 95% CI [−0.0542, −0.0053]). The retrieval condition refused it. A widely held assumption,
that improving an ontology's internal quality improves the tasks built on it, did not hold, and the
refusal is the artifact doing its job. We report the boundary of the positive results with the same
care. Deep recall improved on both splits, but the preregistered composite prediction held in
neither, and the prespecified configuration did not reach significance.

**Fit with the journal.** The paper reports new knowledge that is useful to engineering practice.
It addresses an operational problem rather than an ontology-theoretic one: how a semiconductor
knowledge base decides what may be released. It contributes a release procedure that runs in a
continuous integration pipeline, a controlled before-and-after experiment on a real change, and the
measurement of a failure the procedure blocked. Every shared engineering ontology eventually faces
that question.

**Openness.** The dataset, the evaluation harness, the frozen thresholds, the split and
relevance-judgment identifiers, the fault-injection specifications and the figure-generating code
are public under a DOI. Per-file SHA-256 is published for all released assets. Patent full text is
not redistributable under the source database's academic-use terms, so identifiers and a refetch
procedure are provided instead. The resulting limits on independent reproduction are stated
explicitly rather than glossed.

**What we do not claim.** We do not propose a retrieval or generation method, and we do not claim
performance for the two non-retrieval task views. Nor do we claim the gate has been shown to keep
approved changes safe. That comparison did not become possible within this study, and we say so. The
pre-registrations, including the ones whose predictions failed, are cited and reported in full.

The manuscript is original, is not under consideration elsewhere, and all authors have approved this
submission. We have no competing interests to declare. We would be glad to suggest reviewers with
expertise in ontology evolution, knowledge-graph evaluation, or patent information retrieval should
that be useful.

Thank you for your consideration.

Sincerely,

HyoungSik Park
Graduate School of Management of Technology, Sungkyunkwan University
richphs@skku.edu

# S1 · Preregistered freeze list and reproduction material

> The preregistered freeze list, the artifacts and procedures needed for reproduction, and the
> methodological caveats cited by §4 and §5 of the manuscript. Items whose freeze is on record
> carry the preregistration document and the commit hash.

>
> This is the English rendering of the Korean original
> [S1-appendices-v09.md](../S1-appendices-v09.md), which remains the record of the original wording.
> No verdict and no measured value differs between them.

> **On the `§` references in this file.** The text below was carried over from the v0.9 working
> canonical manuscript, so its `§` numbers are that edition's section numbers and differ from those
> of the current manuscript. The working canonical manuscript is
> [논문_v0_9_SDKB_통합초안.md](../../archive/논문_v0_9_SDKB_통합초안.md).

---

# Appendix A. Preregistered freeze list

Items frozen before the results were seen. Where a preregistration document and a commit hash are
on record, that evidence is given with the item.

- Freeze the data version and the commit hash
- Verify the exact denominators for patents, families and NPL (distinguishing 2,534 / 2,321 /
      2,211 / 584)
- Freeze the training, development and test periods and identifiers
- Pass the masking test for the query citation and judgment edges
- Confirm 0 future-information features
- Freeze the primary dense model and the tokenization rule
- Freeze the primary outcome Recall@100 and the auxiliary metrics
- Freeze \(\epsilon\), \(\delta\) and the minimum subgroup size
- Freeze the definition of low overlap
- Freeze the CQ suite partition (CQ-PA / CQ-EM / CQ-TF / CQ-CORE) and its version
- **Freeze the assignment of detection surfaces to L3 and T3** (L3 = pa · T3 = em·tf·core ·
      disjoint ∧ union complete) — PLAN-022 · commit `44f8022`
- **Freeze the CQ decision-rule version and \(\tau\)** (v2 = existence ∧ distribution ·
      polarity `# monotone:` on all 28 · τ=0.05 · grid {0, 0.05, 0.10}) — PLAN-021
- **Freeze the delta types and the exemption rule** (`generic` / `dedup` · only the distribution
      check is exempted, and only on passing automatic verification) — PLAN-022
- Freeze the fault-injection types, strengths and repeat counts (including the cross-task fault
      families)
- Freeze the sampling design and rating scale for expert judgment
- Record access rights to the test qrel and the date of unsealing
- Verify consistency with the triple signature of the 105,588 generation
- Fix the random seeds (split, bootstrap, hard-negative sampling)

# Appendix B. Software artifacts and the reproduction procedure


## B-1. Directory structure

```
/ontology
  tbox.ttl                  # shared core + three task views
  sdkb-patent.ttl           # prior-art-search module
  shapes/                   # SHACL shapes
/queries/cq  CQ01–CQ31.rq             # suite in the file header `# suite:` · query target in `# target:` (as-built)
                                      #   pa   = CQ09·10·16·26·27      (prior-art search · focal task · target=graph)
                                      #   pa   = CQ29·30·31            (claim layer · target=sidecar · measurement, not a gate §9.7)
                                      #   em   = CQ11·12·17·18·20·28   (expert matching)
                                      #   tf   = CQ02·03·04·05·06      (technology foresight)
                                      #   core = CQ01·07·08·13·14·15·19·21·22·23·24·25 (shared)
/data      G0-Core, G1, G2, claim-feature sidecar
/data/cq_generations  cq_<generation>.json  # per-generation suite pass-rate artifact + waiver log (Table 6.6)
/qrels     dev/, test-sealed/        # test is hash-pinned with an access log
/splits    family_time/
/baselines bm25/, dense/, hybrid/, cpc_overlap/, ontology/
/src/sdkb_paper/analysis   metrics.py, bootstrap.py, subgroup.py, ablation.py, lang_recall.py
/src/sdkb_paper/validate   shacl_gate.py, reasoner_gate.py, cq_runner.py, vocab_coverage.py,
                           leakage_check.py, t1_noninferiority.py, t2_subgroup.py,
                           t3_cross_task_cq.py, t_gate.py
/faults    inject_faults.py           # includes the cross-task fault families (not implemented)
/ci        quality-gate.yml
/scripts   split_by_family_time.py, check_signatures.py
```

The suite assignment is recorded in the CQ file header (`# suite:`), and the runner halts with an
error if a label is missing or outside the permitted values — a denominator that changes silently
makes T3 vacuous. The assignment was **frozen before the T-gate was run** (PLAN-019 §4.1).

## B-2. CI quality-gate wiring

The gate is layered on top of the existing `sig-check` target. Failure at any stage exits non-zero
and blocks the merge. **What the public repository CI actually runs, however, reaches L0–L3, lint,
tests and signature consistency** — retrieval artifacts (corpus, index, runs) are not committed
under the KIPRIS non-redistribution terms, so T1 and T2 are run with `make gate` in an environment
holding the full-text data and their verdict reports are left as artifacts. T3 needs only the graph
and therefore reproduces without the data.

```make
# Makefile (as-built) — one `make gate` runs L0 → T3 fail-fast
gate: gate-graph leakage tgate
gate-graph: l0 validate reason cq vocab      # L0 freshness and integrity / L1 SHACL / L2 HermiT / L3 CQ
leakage:  python -m sdkb_paper.validate.leakage_check --split dev
tgate:    python -m sdkb_paper.validate.t_gate --split dev --baseline g0   # T1 + T2 + T3
cq-freeze: python -m sdkb_paper.validate.t3_cross_task_cq <graph> --freeze <generation>
sig-check: python scripts/check_signatures.py

# Fault injection (§4.10, §6.5 · H1) — an experiment measuring the discriminative power of the gate. Not a standing CI target.
faults-baseline: python -m sdkb_paper.analysis.faults --baseline   # seal the canonical artifacts + baseline
faults-fc:       python -m sdkb_paper.analysis.faults --fc-cache   # FC component once + verify P1 reproduction
faults:          python -m sdkb_paper.analysis.faults --reps 3 --workers 10

# Re-adjudication after decision refinement (§6.5.2) — faults are not re-injected. Only sound deltas are added.
faults-n03:      python -m sdkb_paper.analysis.faults --n03        # 9 full-duplicate merges
faults-rejudge:  python -m sdkb_paper.analysis.faults --rejudge    # re-adjudicate the isolated copies, v1 vs v2 × τ
```

**The decision rule is a frozen value, not an argument.** `config.CQ_TAU=0.05` and
`config.CQ_TAU_GRID=(0, 0.05, 0.10)` live in the code, and the canonical source of polarity is the
`# monotone:` header of each `.rq`. If a label is missing or outside the permitted values the runner
**stops with an error** — a silent default would misjudge a legitimate improvement on a gap-finding
query as a regression (§6.5.2).

**The CQ execution engine (as-built).** `cq_runner` executes SPARQL through pyoxigraph. In-memory
rdflib takes 150 seconds for the 28 CQs on G₀ (23 MB) and cannot carry 108 fault-injection
instances. The switch was made **only after confirming that the per-CQ result row counts of the two
engines agree on 28/28** (`--verify-engines`, 0 mismatches), and `--engine rdflib` can revert at any
time. After the switch it takes 2.4 seconds — the cost barrier to a standing CI gate is gone.

**Contamination isolation for fault injection.** Fault injection damages the graph on purpose, so an
artifact leaking into the canonical path would silently contaminate the entire study.
`validate/quarantine.py` prevents this physically. (i) Before the experiment, the sha256 of every
canonical artifact is sealed and the target graph is physically copied into a separate directory.
(ii) Fault artifacts are never written outside `data/quarantine/<run>/<label>/`, and each directory
carries a contamination stamp recording the fault specification, the seed and the commit.
(iii) Entry points that read a canonical path throw immediately on detecting a contaminated path or
stamp, and the runner re-verifies the canonical hashes **at every instance**, halting at that point
if a single byte differs. (iv) At the end of a batch the isolated copies are locked read-only and an
audit ledger remains. Quarantined artifacts are not committed to the repository.

ε and δ are not command-line arguments but are frozen in the code as `config.T_EPSILON=0.02` and
`config.T_DELTA=0.05` — if the margin could be changed at call time it would not be a
preregistration. `t_gate.py` computes the acceptance rule as a **product**, exits non-zero if any
term is 0, and leaves the verdict and its grounds in `tgate_report.json`.

`t3_cross_task_cq.py` stores the per-task pass rates of the previous canonical state as a generation
artifact (`data/cq_generations/cq_<generation>.json`), compares the current values against it, and
exits non-zero on a drop. A suite that disappears entirely is treated as a pass rate of 0, which
blocks the workaround of "deleting CQs to pass". A waiver is permitted only through an explicit
token in the commit message (`T3-WAIVER:`), and its count is logged
(`data/cq_generations/waiver_log.jsonl`) and reported in the paper (Table 6.6).

## B-3. Items an independent re-run must check

Items an independent re-execution has to check against.

- Verify the triple signature of the 105,588 generation (`check_signatures.py`)
- Licence manifest (matching the curation source table of §3.2)
- Fix the random seeds (split, bootstrap, hard-negative sampling)
- Pin the hash of `g:qrels-test` and record the moment of unsealing
- Confirm the metadata-only distribution scope (KIPRIS terms)
- Store the results of the three modes (oracle-free / citation-assisted / GT-assisted)
      separately
- Record the correspondence between the CQ suite version and the fault-injection experiment
      version (decision rule v1/v2 · the rule column of Table 6.6 · Table 6.5v2)
- Integrity of the canonical hashes before and after fault injection (`data/PRISTINE.json` ·
      quarantine ledger)
- Result of the CQ engine comparison (oxigraph ↔ rdflib, 28/28 agreement)
- Reproduction of the frozen P1 run from the FC cache (top-100, 197/197)

# Appendix C. Caveats

- **The CQ decision was refined, but claim-level decomposition was not carried out.** Strengthening
  the existence check into a distribution check was carried out on 2026-07-28 (decision v2 ·
  §6.5.2), and T3 detection recovered from 0/108 to 34/108. The **claim-level decomposition** of the
  prior-art CQs remains unexecuted and, more importantly, refinement did not revive
  H1′ — because the cause lies not in decision resolution but in **the detection surfaces of L3 and
  T3 overlapping**. A layer definition cannot be changed after seeing a result, so the separation was
  carried over to the next preregistration.
- **The distribution check misjudges a legitimate deduplication as a regression (measured
  2026-07-28).** Merging fully duplicate individuals (sound delta N03) was rejected 1/9 at τ=0.05
  and 3/9 at τ=0 (§6.5.2). A decision that looks only at row counts cannot distinguish the
  disappearance of the spurious combination rows the duplication created. Raising τ collapses
  detection from 55 to 18, so the remedy is a delta-type declaration rather than a margin adjustment
  (not executed).
- **L2 (the reasoning gate) has almost no detection surface (measured 2026-07-28).** The SDKB T-Box
  contains **not one** `owl:disjointWith`, cardinality constraint or functional property. An
  injected logical fault is not a contradiction under OWL semantics, so HermiT reports consistency.
  Of nine fault injections, L2 detected 0 and L1 caught 1 (§6.5). Of the four formal validation
  layers, L2 is in effect an empty layer on the current resource.
- **The effective sensitivity of T1 is low (measured 2026-07-28).** T1 compares the faulted P1
  against the sound B3, so a fault must consume the entire ontology gain (+0.042) and exceed
  \(\varepsilon=0.02\) on top of it. Under a 10% concept-alignment error the gain fell only to
  +0.032 and T1 passed (§6.5). Resetting the margin would change the preregistration and requires a
  separate procedure.
- **The leakage indicator G-3 is not specific to leakage (measured 2026-07-28).** A concept-merge
  fault raised G-3 and was detected at the leakage layer at a rate of 0.67, which is not real leakage
  (§6.5). G-1 (whether a document was placed in a concept slot) has confirmed specificity.
- **A limit of the false-positive denominator in fault injection.** The sound delta N01 (a subset of
  an actual merge delta) is **structurally vacuous with respect to T1 and T2**, because its triples
  are already in G₁ and the union view does not change. False positives at the performance layer
  were measured only through N02 (meaning-preserving enrichment). Holding out unreleased real
  enrichment would be a stronger design, and the absence of such a holdout is a constraint of the
  current resource.
- **Two metric conventions differ from what §5.1 of the manuscript announced.** Because the qrel is
  entirely grade 1, nDCG@20 was computed with **binary gain** and bpref under the
  **retrieved-as-judged** convention (noted in §5.1 and §6.2). The bpref values are **a record of a
  past execution and are excluded from the current analysis** (status notice in
  [S5](S5-submission-full-v2.md) §5). Graded evaluation is conditional on first obtaining the expert
  judgments of §5.5.
- **The retrieval pipeline is frozen for single-language query processing (measured and updated
  2026-07-28).** With no translation layer, cross-lingual recall depends on only two channels, the
  multilingual embedding and the language-neutral concept IRI. The result is measured and reported
  in §6.2f, decomposed by ground-truth language (lexical retrieval recovers 0/334 English positives;
  the final system recovers 5% of non-Korean positives). Improvement experiments with translation,
  concept enrichment or candidate generation as factors would change the F8 and F13 freezes and are
  therefore possible only under **a separate preregistration** (§9.1 · PLAN-019).


---

## Appendix · Resource specification moved from §3.2 and §3.3 of the manuscript (PLAN-086 §7.3)

### The full set of predicates on the rejected-patent axis

The rejected-patent axis consists of `hasPriorArtExaminer` (examiner citation · **the relation
removed from the retrieval graph under leakage control**), `rejectedFor` (rejection ground),
`hasClaim`/`dependsOnClaim`, `hasFeature`/`featureConcept`,
`hasJudgment`/`aboutClaim`/`overPriorArt`/`onGround`, and `hasPriorArtApplicant` (applicant
citation, held separately from the examiner citation).

### Definitions of the four denominators

Examiner citations number 2,534 in total, of which 30 are non-patent literature. 2,321 is the number
of distinct patents designated by `hasPriorArtExaminer`. 2,211 is the number of ground-truth items
that reach the graph at node level, and 584 is the size of the sample carrying a judgment link. The
four are different denominators and are not mixed as one ground-truth count.

### Decision rules for the two relevance grades

Grade 2 applies when a judgment links a specific claim to a prior document and the rejection ground
is identified. Grade 1 applies when only a patent-level citation relation is confirmed; the absence
of a citation relation is treated as unobserved rather than confirmed negative. Grade 2 does not
imply a legally deeper relevance. The 30 non-patent-literature items are excluded from the
denominator of the main evaluation and reported separately.

### The five-way release separation that blocks ground-truth inflow

The five are the publishable core, the development and validation qrel, the test judgments sealed
until evaluation (hash-pinned, with an access log), derived features generated independently of the
qrel, and provenance. Pinning does not constrain improvement in later versions.

## S1-A · Classification and uses of the 31 competency questions

> Moved from manuscript §3.4. [Return to manuscript §3.4](../../manuscript/en_source.md#34-task-level-acceptance-after-formal-validation)

| Category | Count | Use | G0 pass |
|---|---:|---|---:|
| L3 focal-task suite (pa) | 5 | Functional validation of the prior-art task | 4/5 |
| T3 suites (em 6 · tf 5 · core 12) | 23 | Non-regression of other tasks and the shared core | 23/23 |
| **Gate-observed subtotal** | **28** | Denominator of the acceptance rule | **27/28** |
| Sidecar claim queries (CQ29–31) | 3 | Claim-level measurement only · not included in the rule | 3/3 |
| **Full representation audit** | **31** | Denominator of the EP1 representation audit | **30/31** |

# S1. Appendices A–H removed from canonical v0.9 (preserved in full)

> **This file is a move, not a deletion.** Under PLAN-033 §4.2, the appendices of the v2.0
> manuscript retain **only the abridged Appendix B (the claim–evidence matrix)**, and the rest
> (A, C–H) are moved here and published as supplementary material. The content is **exactly as cut
> from canonical v0.9, with not a character altered** — altering it would break the purpose of
> preservation, an honest record of the state before correction (`CLAUDE.md`, the canonical-return
> clause). Source commit: `paper/archive/논문_v0_9_SDKB_통합초안.md` at `f3127f5`. Because an abridged
> Appendix B remains in the manuscript, **the full text before abridgment** is carried here as well.
>
> This is the English rendering of the Korean audit record
> [S1-appendices-v09.md](../S1-appendices-v09.md), which remains the record of the original wording.
> No verdict and no measured value differs between them.

---

# Appendix A. Preregistration checklist

- [ ] Freeze the data version and the commit hash
- [ ] Verify the exact denominators for patents, families and NPL (distinguishing 2,534 / 2,321 /
      2,211 / 584)
- [ ] Freeze the training, development and test periods and identifiers
- [ ] Pass the masking test for the query citation and judgment edges
- [ ] Confirm 0 future-information features
- [ ] Freeze the primary dense model and the tokenization rule
- [ ] Freeze the primary outcome Recall@100 and the auxiliary metrics
- [ ] Freeze \(\epsilon\), \(\delta\) and the minimum subgroup size
- [ ] Freeze the definition of low overlap
- [ ] Freeze the CQ suite partition (CQ-PA / CQ-EM / CQ-TF / CQ-CORE) and its version
- [x] **Freeze the assignment of detection surfaces to L3 and T3** (L3 = pa · T3 = em·tf·core ·
      disjoint ∧ union complete) — PLAN-022 · commit `44f8022`
- [x] **Freeze the CQ decision-rule version and \(\tau\)** (v2 = existence ∧ distribution ·
      polarity `# monotone:` on all 28 · τ=0.05 · grid {0, 0.05, 0.10}) — PLAN-021
- [x] **Freeze the delta types and the exemption rule** (`generic` / `dedup` · only the distribution
      check is exempted, and only on passing automatic verification) — PLAN-022
- [ ] Freeze the fault-injection types, strengths and repeat counts (including the cross-task fault
      families)
- [ ] Freeze the sampling design and rating scale for expert judgment
- [ ] Record access rights to the test qrel and the date of unsealing
- [ ] Verify consistency with the triple signature of the 105,588 generation
- [ ] Fix the random seeds (split, bootstrap, hard-negative sampling)

# Appendix B. Claim–evidence matrix of the paper

| Claim | Kind of evidence | Current state | What the final manuscript needs |
|---|---|---|---|
| The shared T-Box contains the vocabularies of expert matching, prior-art search and technology foresight | TTL classes and properties, and the CQ matrix | Confirmed | Frozen commit, automatic counts |
| The representability of the three tasks is validated | SHACL and CQ execution | Partly confirmed | Per-view CQ and shape results with denominators |
| The performance of all three tasks is validated | Task-specific external ground-truth evaluation | Not claimed | Independent follow-up evaluation |
| G0 contains retrieval resources based on rejected patents | Graph counts and schema | Confirmed | Release hash |
| Node reachability 95.3% | Counts of distinct targets and existing nodes | Confirmed | Reproduction command |
| Semantic reachability 54.6–70.5% | Path counts per relation set | Confirmed | Denominators, SPARQL |
| CQ10 candidates 8→90 | CQ execution result | Confirmed in v0.7 | Query and graph version |
| The T-gate additionally detects semantic faults (H1) | Fault injection | **Rejected** (108 dev instances) | Detection rate, false-positive rate, McNemar (§6.5) |
| **Cross-task faults are detected at T3 alone (H1)** | Cross-task targeted fault injection | **Rejected** — detection by T3 alone 0/18 | Per-layer detection matrix, McNemar (§6.5) |
| An accepted delta is non-inferior and subgroup-safe (H2) | Paired retrieval evaluation | **Supported** — confirmatory split, Accept(ΔG)=1 (§6.3) | \(\Delta R@100\), 95% CI |
| The hybrid improves on the text baseline (H3) | System comparison | **Partly supported — confined to the primary outcome** (confirmatory split · the nDCG clause is not met) (§6.2, §6.3) | R@K, nDCG, corrected p |
| The effect is larger on low-overlap queries (H3, conditional) | Prespecified subgroup analysis | **Contradicted** — the gain concentrates in high overlap (§6.4, §7.3) | Interaction, effect size |
| ClaimFeature and rejection-ground contributions are large (H4) | Ablation | **Rejected** — neither layer contributes independently (§6.3, §6.4) | Per-layer removal loss |
| **The negative control has no effect (H5)** | A8 ablation | **Rejected → cross-task entanglement observed** (§6.3, §7.6) | \(\Delta R@100\), CI (or an entanglement report) |
| Some highly ranked uncited candidates are relevant | Expert judgment on a sample | Not performed | Judgment distribution, \(\kappa\) |
| **A history of CQ pass rates without regression across generations** | Table 6.6 | **Two generations accumulated** (g0, graph_v1 · verdicts generated by code) | Generation and waiver log (a trend only after generations accumulate) |

# Appendix C. Structural migration from v0.7 and the two v0.8 drafts into v0.9

| Source element | Location in v0.9 | Principle applied |
|---|---|---|
| L0–L3 gate (v0.7) | §2.3, §4 | Preserved as is, with the three-condition T-gate added |
| Expert-matching T-Box (v0.7) | §3.1.1, §6.1.1, §8.3 | Restored as representational scope; no ranking performance claimed; scope separated |
| Prior-art-search T-Box (v0.7) | §3.1.2, §3.3–3.7 | Promoted to the primary quantitatively validated view |
| Technology-foresight T-Box and former H2 (v0.7) | §3.1.3, §8.4 | Kept as representational scope and a secondary use case; excluded from the primary hypotheses |
| Former H1 on process coverage (v0.7) | §3.2, resource lineage | Excluded from the retrieval hypotheses; kept as validity of resource formation |
| CQ10 8→90 (v0.7) | §6.1.4 | Confined to evidence about candidate generation |
| Examiner citations 2,534 (v0.7) | §3.3–3.5 | Redefined as a positive-only weak qrel |
| Task-extensible framing and task-semantic regression (v0.8.1) | §1.1–1.2, §2.4 | Adopted as the skeleton |
| L0–L3 + T-gate structure and acceptance rule (v0.8.1) | §4.1, §4.9 | Adopted and extended with condition T3 |
| Reachability ladder and multiple denominators (v0.8.1) | §3.4, §6.1.3 | Adopted |
| Claim-feature sidecar scope separation (v0.8.1) | §3.2, §6.1.5 | Adopted |
| System of expected findings and rejection conditions (v0.8.1) | §7 | Adopted, with the cross-task and negative-control claims (B, F) added |
| Argument on overfitting a single-task gate (validation-gate edition §1.1) | §1.3 | Promoted to core concept 2 |
| Cross-task CQ non-regression S5 (validation-gate edition) | T3 (§4.1, §4.9, §6.6) | Repositioned to fit the L0–L3 + T structure |
| Negative control H3c (validation-gate edition) | H5, A8 (§5.4, §7.6) | Adopted, including the two-sided interpretation rule |
| Overfitting-targeted fault families d and e (validation-gate edition) | Last two rows of the fault table in §4.10, H1 | Adopted |
| Threat of gate-induced drift (validation-gate edition §7.4) | §9.6 | Adopted |
| Expert-matching scope separation (validation-gate edition §8.1) | §8.3 | Adopted (stated only as out of scope, with no mention of an external paper) |
| Unresolved CQ arithmetic and refinement (validation-gate edition A-0) | §3.1.6, §9.7, Appendix D | Stated as a prerequisite |
| AEI review risk table (validation-gate edition Appendix D) | Appendix G | Adopted and updated |
| Software engineering and CI wiring (validation-gate edition Appendix B) | Appendix E | Adopted, reflecting the three T-gate conditions |
| Decision thresholds (validation-gate edition Appendix C) | Appendix F | Adopted and extended |
| The term 'IP-R&D' (earlier edition) | Throughout | Replaced by 'patent-based R&D'; expressions of primacy excluded |

# Appendix D. Execution priority roadmap

## D-0. Prerequisites (before the manuscript is fixed)

1. **Fixing the CQ suites and refining the decision (completed 2026-07-28).** All 28 CQs were
   assigned to the four suites by the file header `# suite:` and frozen before the T-gate was run
   (Appendix E-1 · PLAN-019 §3.2). The assignment of CQ13, 14, 19 and 21 to CQ-CORE was applied at
   the same time. Refinement had two directions. (i) Claim-level decomposition of the prior-art CQs,
   answering the objection that "only the smallest fragment is evaluated" (**not executed**).
   (ii) **Strengthening the existence check into a distribution check** — the direction directly
   supported by the T3′ measurement, and **carried out on 2026-07-28** (decision v2 · polarity
   `# monotone:` declared on all 28 · τ=0.05 frozen in advance · §6.5.2). On re-running, T3
   detection recovered from 0/108 to 34/108, yet H1′ was still rejected, and the cause turned out to
   be **not the decision resolution but the containment between layer definitions (L3 ⊇ T3)**. Two
   of the remaining three were then closed on the same day: **separating the detection surfaces of
   L3 and T3** (new preregistration PLAN-022 · §6.5.3 · H1″ supported after detection-power
   invariance was confirmed) and **exempting the deduplication delta type** (automatic verification ·
   false positives 1/27 → 0/27, with the hole opened by the exemption measured through an
   exemption-abuse fault). **The remaining item (i), claim-level decomposition of the prior-art CQs,
   was also carried out that day** (PLAN-023 · CQ29, 30 and 31 created · §9.7). Because the claim
   layer lives in the sidecar rather than in G0, however, it was incorporated **as a measurement and
   not as a gate**, so the fault sensitivity of L3 did not rise — that limit is stated in §9.7.
2. **Confirming the conclusion about discriminative power (completed 2026-07-28).** What remained
   after (ii) was that **every verdict obtained was post hoc** — H1 rejected → H1′ rejected → H1″
   supported is a third adjudication of the same fault data. This was closed with new data: with the
   layer definitions and the decision rule frozen (no manipulated variable), **72 instances that had
   never been adjudicated** were preregistered and injected (PLAN-025 v2 · `a474126` · 18 on the
   replication axis + 27 across three new cross-task fault families + 27 sound deltas). The result
   is **H1‴ supported**, and the decision rule, the stopping rule and the expected results were
   fixed before execution (§6.5.4). What remains is the sensitivity at τ=0.10 and the **untested
   specificity** (non-cross-task faults were not placed in the holdout denominator).
3. **Fixing the primary dense model and tokenization.** To be fixed before the development set is
   unsealed, after reviewing Korean patent performance and licensing.

## D-1. Data infrastructure (highest priority)

- Split G0-Core and the sealed `g:qrels-test` by time and patent family → `split_by_family_time.py`
- Automatic checking of leakage items → `leakage_check.py`
- **Entry threshold:** produce Recall@100 on a leakage-free BM25 baseline. **Do not fix the abstract
  or the contribution statement before this number exists.**

## D-2. Core experiments

- Nine comparison systems (B0–B5, P0–P2) × metrics, with the three modes stored separately →
  `run_eval.py`
- The full fault families × the seven gate layers (L0–L3, T1–T3) detection matrix (including the
  cross-task families)
- Ablation experiments A1–A8 (including the negative control), and separation of novelty from
  inventive step
- Accumulation of per-generation CQ pass-rate artifacts (Table 6.6)

## D-3. Fixing and submitting the manuscript

- Fix the abstract, the RQs and the contribution statement once the numbers exist
- **Expression discipline:** "ground truth" → "examiner-validated weak ground truth" / "IP-R&D" →
  "patent-based R&D" / no expressions of primacy
- Check the unresolved bibliography entries (at the end of the appendix references) against the
  originals

# Appendix E. Software engineering artifacts

*(Where the target journal places software engineering as a standalone topic out of scope, this
appendix is isolated as reproducibility material and the main text concentrates on knowledge
representation, validation methodology and evaluation design.)*

## E-1. Directory structure

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
/faults    inject_faults.py           # includes the cross-task fault families (not implemented — Appendix D-2)
/ci        quality-gate.yml
/scripts   split_by_family_time.py, check_signatures.py
```

The suite assignment is recorded in the CQ file header (`# suite:`), and the runner halts with an
error if a label is missing or outside the permitted values — a denominator that changes silently
makes T3 vacuous. The assignment was **frozen before the T-gate was run** (PLAN-019 §4.1).

## E-2. CI quality-gate wiring

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

# W4b re-adjudication after decision refinement (§6.5.2) — faults are not re-injected. Only sound deltas are added.
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

## E-3. Reproducibility checklist

- [ ] Verify the triple signature of the 105,588 generation (`check_signatures.py`)
- [ ] Licence manifest (matching the curation source table of §3.2)
- [ ] Fix the random seeds (split, bootstrap, hard-negative sampling)
- [ ] Pin the hash of `g:qrels-test` and record the moment of unsealing
- [ ] Confirm the metadata-only distribution scope (KIPRIS terms)
- [ ] Store the results of the three modes (oracle-free / citation-assisted / GT-assisted)
      separately
- [x] Record the correspondence between the CQ suite version and the fault-injection experiment
      version (decision rule v1/v2 · the rule column of Table 6.6 · Table 6.5v2)
- [ ] Integrity of the canonical hashes before and after fault injection (`data/PRISTINE.json` ·
      quarantine ledger)
- [ ] Result of the CQ engine comparison (oxigraph ↔ rdflib, 28/28 agreement)
- [ ] Reproduction of the frozen P1 run from the FC cache (top-100, 197/197)

# Appendix F. Decision thresholds (triggers for a change of direction)

| Observation | Response |
|---|---|
| The hybrid **fails even non-inferiority** on Recall@100 against the strongest text baseline | Do not claim the overall effect of H3; move the centre of gravity of the paper to the validation-gate methodology (RQ1) and reposition retrieval as supporting evidence |
| The graded-qrel sample is insufficient for testing | Demote nDCG to a high-quality subset only, and make patent-level Recall the primary outcome |
| Cohen's κ < 0.4 on expert re-evaluation | Exclude the reclassification of uncited top results from the main text; keep it as a sensitivity analysis in an appendix |
| **H5 fails** (A8 significantly degrades retrieval) | Abandon the negative-control frame and switch to "cross-task entanglement observed" — promote it to direct evidence for the necessity of T3 (§7.6) |
| **T3 fails to detect the cross-task fault families** | The cross-task CQ suite is too loose → re-run after CQ refinement and report the suite version history — **triggered and completed 2026-07-28** (decision v2 · §6.5.2 · a rule-version column in Table 6.6) |
| **Detection by T3 alone is still 0 after refinement** | Suspect **the containment between layer definitions** rather than the decision resolution → a new preregistration separating the detection surfaces of L3 and T3. Do not change a layer definition after seeing the result — **triggered and completed 2026-07-28** (re-adjudicated after freezing PLAN-022 · §6.5.3 · H1″ supported) |
| **Risk that layer separation weakens the gate** | Before redefining, check the invariant `L3_all ⟺ L3_pa ∨ T3` per instance — if the union is all CQs and the acceptance rule is a product, only attribution changes. If even one violation appears, do not use the result — **checked 2026-07-28 · violations 0/144** (§6.5.3) |
| **A legitimate delta is caught by the distribution check** (deduplication) | Do not raise \(\tau\) (detection power collapses) → exempt the distribution check only when the delta declares its type and **the data verify that declaration** (the existence check remains). Measure the hole the exemption opens by injecting it as a fault — **carried out 2026-07-28, false positives 1/27 → 0/27 · the abuse fault refused 9/9** (§6.5.3) |
| **Every verdict obtained is post hoc** (H1 rejected → H1′ rejected → H1″ supported is a third adjudication of the same data) | Do not fix the rule again — each fix accumulates post-hoc character. With the layer definitions and the decision rule frozen, replicate on **fault instances never adjudicated before**, and preregister the decision rule, the stopping rule and the expected results before execution. Secure cross-task character by **construction** rather than by result (manipulated predicates ∩ focal-task CQ predicates = ∅, enforced by a test over a static extraction) — **triggered and completed 2026-07-28** (PLAN-025 v2 frozen at `a474126` → 72 holdout instances · §6.5.4 · **H1‴ supported** · the rejection at τ=0.10 and the untested specificity reported as they stand) |
| The distribution of queries and rejection grounds in the most recent 20% test window is insufficient | Switch to a five-fold rolling-origin auxiliary analysis preserving time order (§4.3) |
| A subgroup sample falls below the minimum size | Exclude that subgroup from the T2 blocking rule and report the observation only |

# Appendix G. Review risks at the target journal and responses (against AEI)

AEI (Advanced Engineering Informatics, Elsevier) states knowledge-representation formalisms and
reasoning techniques in scope and requires the generality and scalability of a method to be
validated both qualitatively and quantitatively, while stating that a paper addressing only
software engineering issues is out of scope. `[Re-confirm the official scope and metrics on the
Elsevier page before submission]`

| Risk | Response |
|---|---|
| **Novelty** — Siddharth, PaECTER and the IPRally Graph Transformer have taken KG + retrieval | Foreground the reversal of direction: not "improve retrieval with a KG" but "control the evolution of a KG by retrieval while monitoring cross-task effects". Name recent comparators such as PatenTEB (2025). Avoid claims of primacy |
| **The scope exclusion of SW issues** | **Isolate** the gate implementation and CI wiring **in Appendix E**. Keep the main text on knowledge representation, validation methodology and evaluation design |
| **The objection that a multi-task ontology is validated by a single-task evaluation** | State the depth-asymmetry design in §1.3, plus the T3 cross-task condition, the per-generation trend of Table 6.6, and the acknowledged limit in §9.6 |
| **The low share of gate-task CQs (4/28)** | The CQ refinement prerequisite of Appendix D-0 — decision refinement was carried out (§6.5.2); claim-level decomposition was not |
| **Claiming the independence of T3 while detection by T3 alone is 0** | Do not hide it — establish by measurement that detection by T3 alone is impossible because `L3 ⊇ T3` by the layer definitions (§6.5.2), and narrow the claim to the weak form (the only layer that **points to the location** of a regression). The strong form was then restored by a new preregistration separating the layers (§6.5.3) and by **holdout confirmation** (§6.5.4 · detection by T3 alone 12/45 · one-sided p=.0001), with the untested specificity and the rejection at τ=0.10 stated in the same section |
| **Weak ground truth** | The positive-only terminology, bpref, and blinded two-rater expert re-evaluation with κ |
| **Numbers not produced** | C2 (§6.2–6.4) and C3 (§6.5–6.6) are produced under leakage control — one unsealing, no reselection. H1 is rejected, H1″ is exploratory support, **H1‴ is confirmed on the holdout**, and **H2 is supported on the confirmatory split**; the discriminative power of the gate (H1) and the acceptance safety of a delta (H2) must be read as distinct |
| **Why lead with P1 when the primary system is not significant** | We do not lead with it — the prespecified P0★ (p=.181) is reported as primary and the advantage of P1 is described as a secondary observation (§6.2, §6.3). No post-hoc substitution was made |
| **Is it not only R@100 that improved** | Yes — nDCG@20, MRR and bpref did not improve, and they are carried as they stand in Table 6.2c. The scope of the claim was explicitly narrowed to "deep recall" (§6.3, §8.5) |
| **Is this not a single-language pipeline for multilingual patent retrieval** | Yes — this is not hidden but measured and reported in §6.2f, decomposed by ground-truth language (lexical retrieval recovers 0/334 English positives). The same table also shows the cross-lingual comparative advantage of the ontology-only arm (2.3× the hybrid on English), which specifies the follow-up design. Translation and concept-enrichment experiments lie outside the frozen design and are separated into their own preregistration (§9.1) |
| **Salami-slicing** (overlap with the expert-matching study) | Scope separation is stated in §8.3 — expert matching is used only as a T3 input and as the negative control, with no performance or methodological claim |

# Appendix H. Caveats

- **The CQ decision was refined, but claim-level decomposition was not carried out.** Strengthening
  the existence check into a distribution check was carried out on 2026-07-28 (decision v2 ·
  §6.5.2), and T3 detection recovered from 0/108 to 34/108. The **claim-level decomposition** of the
  prior-art CQs remains unexecuted (Appendix D-0) and, more importantly, refinement did not revive
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
- **Current state of the quantitative results (third update, 2026-07-28).** Tables 6.2 (and
  6.2b–6.2e), 6.3 and 6.4 and Figures 2–5 are **filled with measurements** — all code-generated,
  with no manual entry (`make tables && make figures`). **The T-gate (T1, T2, T3) and the leakage
  audit now exist in code and run on both the development and confirmatory splits** (`make gate` ·
  Appendix E-2). **Table 6.5 (fault injection) is likewise filled with measurements** — 12 fault
  types × 3 strengths × 3 repeats = 108 instances plus 18 sound deltas, on the development split,
  with 0 errors (`make faults`). The result is that **H1 was rejected** (§6.5). The re-adjudication
  carrying out the announced remedy (refinement of the CQ decision) was also produced (Table 6.5v2 ·
  `make faults-rejudge` · with 9 N03 sound deltas added), and **H1′ was likewise rejected, but for a
  different reason** (§6.5.2). **Table 6.6 (CQ pass rates by generation) is filled to the two
  accumulated generations, and on 2026-07-28 one manual entry was found in this table and
  corrected** — the second row had been written by hand without a generation artifact and the
  generator was printing a placeholder in the verdict column. The `graph_v1` generation was actually
  frozen so that code fills the verdict, and the contract was changed so that the generator blocks a
  generation without a verdict by raising an exception (§6.6). With only a reference generation and a
  merged generation, this is not yet a trend, and we do not create generations to fill a table.
  **H2 (acceptance safety) was adjudicated on the confirmatory split on 2026-07-28** (§6.3 ·
  Accept(ΔG)=1 · re-adjudicating the frozen run without new retrieval). What had previously stood in
  this place, "no performance claim about H2 is stated", was there **because the frozen-test-set
  verdict the preregistration required did not exist**, and not substituting the development-split
  verdict for it was that discipline.
- **Two metric conventions differ from what §5.1 of the manuscript announced.** Because the qrel is
  entirely grade 1, nDCG@20 was computed with **binary gain** and bpref under the
  **retrieved-as-judged** convention (noted in §5.1 and §6.2). Graded evaluation is conditional on
  first obtaining the expert judgments of §5.5.
- **The retrieval pipeline is frozen for single-language query processing (measured and updated
  2026-07-28).** With no translation layer, cross-lingual recall depends on only two channels, the
  multilingual embedding and the language-neutral concept IRI. The result is measured and reported
  in §6.2f, decomposed by ground-truth language (lexical retrieval recovers 0/334 English positives;
  the final system recovers 5% of non-Korean positives). Improvement experiments with translation,
  concept enrichment or candidate generation as factors would change the F8 and F13 freezes and are
  therefore possible only under **a separate preregistration** (§9.1 · PLAN-019).
- **Bibliography needs re-checking.** The unresolved entries marked at the end of the references
  (PatenTEB, the CLEF-IP overview, IPRally, Keet & Khan, Potoniec et al.) require comparison against
  the originals before submission.
- **SemiKong is an arXiv preprint (not peer-reviewed).** Process-hierarchy labels are to be finalized
  against the original (Process Group/Module/Unit).
- **Journal metrics conflict.** The IF and CiteScore of the target journal differ by aggregator and
  by year, so the official page must be re-checked before submission.
- **The T-Box vocabulary and asset numbers precede comparison against a frozen repository commit.**
  They are to be replaced by automatic counts in the final manuscript (§3.1.5).

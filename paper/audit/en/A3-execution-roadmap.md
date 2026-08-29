> Audit record — migrated from S1 Appendix D. Kept verbatim as recorded; not revised to the
> current verdict phrasing. The current verdicts are held by paper/verdicts.yaml.

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


---

## Work-status items migrated from S1 Appendix H

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
- **Bibliography needs re-checking.** The unresolved entries marked at the end of the references
  (PatenTEB, the CLEF-IP overview, IPRally, Keet & Khan, Potoniec et al.) require comparison against
  the originals before submission.
- **SemiKong is an arXiv preprint (not peer-reviewed).** Process-hierarchy labels are to be finalized
  against the original (Process Group/Module/Unit).
- **Journal metrics conflict.** The IF and CiteScore of the target journal differ by aggregator and
  by year, so the official page must be re-checked before submission.
- **The T-Box vocabulary and asset numbers precede comparison against a frozen repository commit.**
  They are to be replaced by automatic counts in the final manuscript (§3.1.5).

> Audit record — migrated from S1 Appendix F. Kept verbatim as recorded; not revised to the
> current verdict phrasing. The current verdicts are held by paper/verdicts.yaml.

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


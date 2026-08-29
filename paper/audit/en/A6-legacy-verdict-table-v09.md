> Audit record — migrated from S2 §S2.1. Kept verbatim as recorded; not revised to the
> current verdict phrasing. The current verdicts are held by paper/verdicts.yaml.

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

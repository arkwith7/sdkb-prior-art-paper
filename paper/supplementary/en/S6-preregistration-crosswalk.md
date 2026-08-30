# S6 · Preregistration crosswalk

> The names this manuscript gives to its evaluation checks ↔ the labels used in the preregistration
> documents ↔ the documents themselves. A paper reporting preregistered results must let readers
> verify the correspondence between its claims and the registered outcomes; this table is that
> correspondence.
> This is the English rendering of the Korean original
> [S6-preregistration-crosswalk.md](../S6-preregistration-crosswalk.md); the Korean file remains
> the record of the original wording, and no verdict or measured value differs between them.

The manuscript names its evaluation checks in words; the preregistration documents use hypothesis
labels. The table below joins the two.

## 1. Confirmatory evaluation checks

| Name in the manuscript | Preregistration label | Research-question label | Preregistration document | Status |
|---|---|---|---|---|
| **Retrieval-utility check** | `H3` | `RQ2` | PLAN-031 (first confirmatory split) · PLAN-047 (second confirmatory split) | Confirmatory |
| **Layer-specificity check** | `H5` | `RQ3` · `RQ4` | PLAN-031 · PLAN-047 | Confirmatory |
| **Transfer check** | `T4` (no hypothesis label) | `RQ5` | PLAN-038 (instrument frozen) · PLAN-047 (confirmatory readout) | One confirmatory readout · not part of the acceptance rule |

`RQ4` (layer independence) has no separate check: **the result of the layer-specificity check
answers it**, exactly as designed at the time of preregistration.

## 2. Checks demoted from confirmatory — verdict unchanged, only the place of reporting moved

| Preregistration label | Content | Place in the manuscript | Verdict |
|---|---|---|---|
| `H1` | Discriminative power of the gate | §4.4 design · §5.4 holdout confirmation | Supported within the holdout scope |
| `H2` | Acceptance safety | §6.4 | **Not tested on the resource of this paper** · later rejected in one actual test under a separate preregistration (PLAN-035) |
| `H4` | Layer contribution | Rows A4 and A5 of the ablation table in §5.3.2 | Rejected |

**Demotion is not deletion.** The verdict records remain under their original labels in the working
canonical manuscript [논문_v0_9_SDKB_통합초안.md](../../archive/논문_v0_9_SDKB_통합초안.md) §1.4a and in
[paper/verdicts.yaml](../../verdicts.yaml).

## 3. Design research questions

| Manuscript | Working canonical manuscript and PLANs | Note |
|---|---|---|
| `RQ1` | `DRQ1` | Representing three tasks on one shared T-Box |
| `RQ2` | `DRQ2` | Design of the change-acceptance gate |
| `RQ3` | `DRQ3′` | Utility, failure boundaries, cross-layer metric misalignment (former `DRQ3` + `DRQ4` merged; `DRQ4` is retired and not reused) |

> ⚠ **The `RQ2` and `RQ3` of §1 (preregistration research questions) are not the `RQ2` and `RQ3`
> of §3 (design research questions of the manuscript).** Only the latter appear in the manuscript;
> the labels of §1 are used inside this table alone.

## 4. Design principles `DP` ↔ Lessons ①②③ — recording where a label went

The manuscript reports seven design principles (`DP1`–`DP7`) as
**three lessons** (**Lessons ①②③**) and **two follow-up hypotheses**. The evidence is one
qualifying resource delta and one port case, so a general proposition resting on a single case is
not called an established principle. This is a change in where they are reported and what they are
called, not a retraction. **No verdict, measured value or grade differs.** The table below records
where each label went and how it is graded.

**There are five promotion conditions, fixed before the results were seen.** (1) the evidence is
the output of executed code; (2) competing explanations are excluded, or their non-exclusion is
stated; (3) the principle is stated in a form transferable beyond this artifact — if the sentence
carries "in SDKB" it is an observation, not a principle; (4) it is refutable, with the observation
that would weaken it stated alongside; (5) it is not derived after the fact, with the design time
and the confirmation time each recorded.

There are three grades. **Designed in advance, empirically supported** applies where all five hold
and the design time precedes the confirmation time; **empirically supported** applies where all
five hold but confirmation came first; **proposition** applies where at least one is unmet. The
evidence and the weakening condition of each principle are stated in §6.3 of the manuscript.

| Working canonical manuscript and PLANs | Place in the manuscript | Name | Grade |
|---|---|---|---|
| `DP2` Acceptance one layer below | §6.3 | **Lesson ①** | Designed in advance, empirically supported |
| `DP3` Cross-task monitoring | §6.3 | **Lesson ②** | Designed in advance, empirically supported |
| `DP5` Separation of candidate generation | §6.3 | **Lesson ③** | Empirically supported |
| `DP1` Layered validation | §6.1 | Absorbed into the prose; no label | Empirically supported |
| `DP4` Controlled resource substitution | Opening of §4 | Absorbed as a methodological requirement of the evaluation design; no label | Empirically supported |
| `DP6` Verification of transfer | §6.3 | **Follow-up hypothesis** | Proposition |
| `DP7` Port-layer separation | §6.3 | **Follow-up hypothesis** | Empirically supported |

> The design-principle tables in [S5](S5-submission-full-v2.md) §3.3, §7.7 and §7.8 belong to the
> generation that had **two grades** and **do not carry `DP7`**. The current grading is held by the
> table above.

**The lesson names are used inside the manuscript only.** The working canonical manuscript, the
PLANs, the defect ledger and `verdicts.yaml` keep the `DP` labels. What must hold is traceability,
not identity of symbols.

## 5. Names that did not change

`L0`–`L3` (four formal validation layers) · `T1`–`T4` (task conditions) · `EP1`–`EP5` (evaluation
episodes) · `A1`–`A8` (ablation conditions) · `B0`–`B5` and `P0`–`P2` (comparison systems).

> The lessons are named with the enclosed numerals **①②③**. A label beginning with `L` denotes
> exactly one thing in this paper: a formal validation layer, `L0`–`L3`.

`T1`–`T4` remain because they are not legacy notation. They are the names of the components of the
artifact this paper proposes, the T-gate.

## 6. Freezing points and sealing of the preregistrations

The items each preregistration froze before results were seen — non-inferiority margin ε=0.02,
subgroup margin δ=0.05, primary outcome family-level Recall@100, the time and family split
boundaries, the low-overlap boundary 0.0079, and the generation-layer margins ε_T4=0.02 and
η=0.01 — together with the sealed qrel hashes and the access ledger, are in §4.5 of the manuscript
and in the pre-abridgment full text [S5](S5-submission-full-v2.md).

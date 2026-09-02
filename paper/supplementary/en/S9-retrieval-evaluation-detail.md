# S9 · Details of the retrieval-layer evaluation — premises for reading the verdicts, the scope of the ablations, and the cross-lingual diagnosis

> Details of the retrieval-layer evaluation cited by §5.3 of the manuscript. The manuscript carries
> the verdicts of the two preregistered checks and their direct evidence; the premises needed to
> read those verdicts and the full exploratory diagnosis are kept here.
> **All values match the manuscript; nothing is newly computed in this file.**
> This is the English rendering of the Korean record
> [S9-retrieval-evaluation-detail.md](../S9-retrieval-evaluation-detail.md).

## 1. Three premises for reading the two verdicts

First, because the ground truth is partial, the two checks of §4.5 were carried out. The difference
persisted after merging examiner citations from corresponding foreign filings (+0.0534 → +0.0593 ·
*p* = .008 → .003). However, the minimum adversarial addition that would bring the lower confidence
bound to 0 is 4 items in panel A and 3 in panel B, so the residual vulnerability can be removed only
by sample adjudication (§6.4). Second, the queries of panel B carry sparse ontology signal (2.909
versus 1.105 concepts per document), so the attenuation of the effect is consistent in direction
with that property, and the property is described in the preregistration document written before
unsealing. Third, five conditions for describing an effect as established were fixed before
unsealing. One is met — the lower bound of the effect-size confidence interval exceeds 0 — and
replication across two non-overlapping splits is partially met. Significance in the prespecified
primary configuration is not met, sign stability across the sensitivity grid was not executed, and
the leakage audit returned 0. No condition was changed after the results were seen (full text and
the unsealing history are in S5).

## 2. The scope of the claims the ablations support

The proposed configuration does not expand the candidate pool (§4.3), so the ablation results must
be read as layer contributions within that pool. That most ablations are non-significant admits two
explanations — absence of layer contribution and pressure from the re-ranking ceiling — and the two
are not distinguished. The rejection-ground axis also carries a resource limitation: among the 1,000
upstream source records, novelty-only rejections number 0, so the anticipated contrast between
novelty and inventive step cannot be tested on this resource. In the second confirmatory split, A8
is again exactly 0.0000, and the gains were observed on queries whose vocabulary already overlaps
(+0.0461 · *p* = .008) and on queries whose ground truth is entirely Korean (+0.1019 · *p* = .005).
The ontology as a whole therefore contributes, but which axis produces that contribution was not
distinguished.

## 3. Cross-lingual diagnosis — three relative advantages of the concept path

The same diagnosis shows three relative advantages of the concept path. The Ontology-only
configuration recovers English ground truth at 0.109 (14/128), the highest of all configurations
(Text Hybrid 0.047 · lexical-only 0.000). The Japanese recall of 0 follows from a concept-link
coverage of 0.0% and is therefore not a failure of ranking. Adding the 45 items the concept-only
configuration recovers from outside the pool to the 289/479 (60.3%) of ground truth the text
baseline's candidate pool contains raises the ceiling to 334/479 (69.7%). However, the
foreign-language subpool is sparse in distractors, so the cross-lingual gain is structurally
overestimated (ground-truth proportion 72.5% in English versus 3.3% in Korean). In the second
confirmatory split, the classification-only configuration outperforms the Ontology-only
configuration. The single statement these values support is therefore that the concept path reaches
different documents from the text path; superiority of the concept path is not supported by them.

## 4. Three gaps specific to the retrieval-layer evaluation

Of the gap table in §6.4 of the manuscript, the three that concern only the retrieval-layer
evaluation are placed here. **Wording, values, and item numbers are identical to the source table** —
renumbering them would break the correspondence with the manuscript.

| | Gap | Current state (where reported) | Measurement that resolves it |
|---|---|---|---|
| ⑥ | Mismatch between query language and ground-truth language | Queries are entirely Korean and 41% of known positives are non-Korean (§6.4) | Add a query-side translation configuration and re-measure recall decomposed by language |
| ⑦ | Absence of a strong multilingual baseline | **Partially resolved** — a multilingual fusion baseline was added and baseline strength did not change significantly (§4.3 · Table 5). Because both encoders share a backbone family, **family diversity is not achieved** | Re-evaluation including an encoder from a different family |
| ⑧ | Expert relevance judgments not carried out | The protocol was frozen but no judgments were made (§4.4). Vulnerability is quantified as the minimum number of judgment flips and **partially reduced** by merging exogenous labels (§5.3.1) | Two-rater blinded independent judgment of a **targeted sample** of top-ranked uncited candidates, with κ reported |

## S9-T1 · Complete subgroup and ablation results

> Moved from manuscript §5.3.2. [Return to manuscript §5.3.2](../../manuscript/en_source.md#532-subgroups-and-ablation)

| Group/removed layer | Queries | qrel | Text Hybrid R@100 | Proposed R@100 | Difference | 95% CI |
|---|---:|---:|---:|---:|---:|---|
| **low lexical overlap** | 27 | 59 | 0.1975 | 0.1389 | **−0.0586** | [−0.2099,+0.0741] (p=0.448) |
| **high lexical overlap** | 171 | 420 | 0.4685 | 0.5396 | **+0.0711** | [+0.0330,+0.1104] (p<.001) |
| positives entirely Korean | 98 | 207 | 0.6023 | 0.6959 | +0.0936 | [+0.0295,+0.1579] (p=0.004) |
| positives include another language | 100 | 272 | 0.2642 | 0.2782 | +0.0140 | [−0.0313,+0.0578] (p=0.518) |
| **−Expert layer (A8, negative control)** | 198 | 479 | — | 0.4534 | **+0.0316** | **[+0.0105,+0.0560]** (p=0.002 · significant after Holm) |

Of all 17 rows, the twelve not shown above remain in the frozen full version in S5. In the second
confirmatory split, the same removal of the expert-matching-only layer was 0.0000 and was not reproduced.

## S9-T2 · Exploratory baselines and original-sample summary

> Moved from manuscript Table 6. [Return to manuscript §5.3.1](../../manuscript/en_source.md#531-retrieval-performance-and-the-verdicts-of-the-confirmatory-checks)

The multilingual-fusion and bibliographic-condition baselines do not enter the confirmatory verdict.
Their split-level values and the original-sample win/loss/tie summary remain in the full two-panel
retrieval table in S5. Manuscript Table 6 retains only Text Hybrid, Text+Ontology, and +ClaimFeature,
the three configurations directly used in the verdict.

## 5. The layer-contribution check — verdicts on the twelve ablation rows

Details of the layer-contribution check summarised in §5.3.2 of the manuscript. **Values are
identical to Table 6 of the manuscript.**

The prediction that the removal loss of the claim-feature and rejection-ground layers would exceed
the removal loss of the classification signal did not hold. The configuration with all ontology
features removed (A7) produces rankings identical to the text-only baseline. The contribution of the
ontology as a whole is therefore stated not by a separate ablation row but by the comparison across
configurations in Table 5 of the manuscript. Of the 17 ablation rows, the twelve not carried in the
manuscript are in S5.

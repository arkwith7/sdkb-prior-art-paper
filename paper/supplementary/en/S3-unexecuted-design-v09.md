# S3 — Options designed but not executed · full text of the abridged §4 (v0.9)

> **Why this file exists.** In stage 2 of PLAN-033, §4 (the methodology of the task-based
> validation gate) was reduced from 6,960 to 5,459 characters, and what was cut is carried here
> **without a single character altered**. Most of what was cut is an **option that was designed but
> not executed in this study** — that it was not executed is itself a reportable fact, so it is not
> deleted (`CLAUDE.md` §1-1, §8). §4.2 and §4.8 of the manuscript point to this file.
>
> No verdict and no number is created here. Every sentence below was carried over verbatim from an
> earlier edition of manuscript v0.9.
>
> This is the English rendering of the Korean audit record
> [S3-unexecuted-design-v09.md](../S3-unexecuted-design-v09.md), which remains the record of the
> original wording.

---

## S3.1 §4.2 as written — three query representations (comparison not run)

> The manuscript retains only "four query representations were prepared in the corpus, but the
> comparison between representations was not run". The design text follows.

## 4.2 The unit of an evaluation query

The unit of a query in the main analysis is one rejected patent. Each query uses the independent
claims by preference; where identification of the independent claims is incomplete, an auxiliary
query is generated that uses claim 1 together with the title and abstract. On the subset with a
claim-level judgment link, the pair `(rejected patent, independent claim)` is used as the query
unit.

Query representations are divided into the following three kinds to check robustness.

1. **Claim-only:** the independent claims, or claim 1
2. **Claim+Abstract:** the claims together with the abstract
3. **Fielded:** title, abstract and claims indexed as separate fields and combined by weight

The main analysis uses Claim-only. Title and abstract are summary expressions of the application
and can make retrieval easier, but they can also move away from the legal unit of claim relevance,
so they are reported as a separate result.

---

## S3.2 §4.3 as written — the rolling-origin auxiliary analysis (not executed)

> The manuscript retains only the as-built split (600/200/200, boundaries 2016-11-21 and
> 2021-07-21). The five-fold rolling-origin auxiliary analysis in the last paragraph below **was
> not executed**.

## 4.3 The time and family split

A random document split can mix the same family and later information into training and test. This
study uses the following principles.

- Sort the query patents by priority date or filing date.
- Assign the oldest 60% to training, the next 20% to development, and the most recent 20% to test.
- Every document of the same DOCDB family belongs to a single split.
- Impose a group constraint so that the family of a rejected patent and the families of its qrel are
  not reused directly as training positives in another split.
- The resulting split is **600 training / 200 development / 200 test**, with boundaries
  **2016-11-21** (training–development) and **2021-07-21** (development–test). 959 distinct
  families do not overlap between splits. Queries with at least one known positive number 197 in
  development and 198 in test. The boundaries and the seed were frozen in code before the test qrel
  was unsealed (the evidence is left as a commit hash), and the test qrel was sealed in a separate
  file until the moment of final comparison (479 edges over 198 queries).

The 60/20/20 division is an initial rule. Should the query count and the distribution of rejection
grounds in the most recent 20% prove insufficient for statistical analysis, a five-fold
rolling-origin evaluation preserving time order is used as an auxiliary analysis. In no case is a
split boundary changed after seeing test performance.

---

## S3.3 §4.5.2–4.5.3 as written — citation-assisted and GT-assisted

> The manuscript reduced each of the two modes to a single sentence. The results of both modes are
> stored apart from the main conclusions and are not used for performance claims.

### 4.5.2 The citation-assisted auxiliary system

The citation edges of the query itself are removed, while the citation network of other patents
published before the query date may be used. This is the setting in which a real retrieval service
exploits the historical citation structure available to it, and it is reported as a separate result.

### 4.5.3 The GT-assisted ceiling

Feature overlap or rejection grounds extracted by treating the examiner judgment as ground truth
(GT) are permitted as query features. This setting is not a deployable primary system but "the
ceiling obtainable when complete semantic alignment is possible". It is reported apart from the
main conclusions and is not used for performance claims.

This three-mode design is consistent with the evaluation precedent of CLEF-IP and of Mahdabi &
Crestani (2014), in which the citations of the query patent are removed and then used as relevance
judgments.

---

## S3.4 §4.6 as written — choice of the dense baseline (description at design time)

> The manuscript replaced this with the as-built choice (Titan Embed v2). What follows is **the
> description at design time**; the actual choice differed because of constraints on handling long
> Korean documents.

## 4.6 Comparison systems

| ID | System | Evidence used | Purpose |
|---|---|---|---|
| B0 | BM25-Claim | Claim vocabulary | Minimal strong baseline |
| B1 | BM25-Fielded | Title, abstract, claims | Effect of fields |
| B2 | Dense | Patent-specific embedding | Semantic-similarity baseline |
| B3 | Text Hybrid | BM25 + Dense, RRF or normalized sum | Strongest text baseline |
| B4 | CPC/IPC | Classification overlap and distance | Effect of the classification signal alone |
| B5 | Ontology-only | Concept paths over process, device, material, equipment and failure | Effect of explicit semantics alone |
| P0 | Text+Ontology | B3 + concept overlap and paths | Core proposed system |
| P1 | +ClaimFeature | P0 + feature coverage | Fine-grained claim semantics |
| P2 | +Ground-aware | P1 + rejection-ground compatibility, within the oracle-free scope | Legal context |

The dense baseline uses a patent-specific encoder that can be reproduced publicly. The minimum
candidates are PatentSBERTa or PaECTER; Korean patent performance and licensing are reviewed and one
primary model is fixed before the development set is unsealed. Where multilingual representation is
weak, a multilingual embedding is added as an auxiliary baseline, but the model is not selected on
the basis of test results.

---

## S3.5 §4.8 as written — four auxiliary metrics separating novelty from inventive step (not computed)

> The manuscript retains only the fact that the two kinds of judgment differ and that "four
> auxiliary metrics were designed but not computed". The four metrics below **were not computed in
> this study**.

## 4.8 Separating novelty from inventive step

A novelty judgment concerns, in principle, whether a single prior document discloses every
essential feature of a claim. An inventive-step judgment, by contrast, may involve the combination
of several documents and the perspective of a person skilled in the art. Document-level recall
alone cannot fully describe both kinds.

The following auxiliary metrics are therefore used.

- **Single-reference Feature Coverage:** the maximum proportion of the query features that a single
  document covers
- **Set Recall@K:** how far the set of top-K documents covers the examiner-cited families
- **Set Feature Coverage@K:** the proportion of the query features covered by the union of the
  top-K documents
- **Minimum Evidence Set:** the smallest number of documents that reaches a target feature-coverage
  rate

For rejection grounds other than novelty and inventive step (insufficient description, clarity and
so on), the degree of direct relevance to prior-art search is stated explicitly, and where the
sample is too small the analysis is reported as exploratory only.

---

## S3.6 §4.10 as written — the 12 fault families and their expected detecting layer

> The manuscript retains, in prose, only the composition of the 12 families and the two cross-task
> faults. The full correspondence table follows.

| Fault family | Example injection | Expected detecting layer |
|---|---|---|
| Freshness and integrity | Artifact from an earlier version, input hash mismatch | L0 |
| Structure | Removal of a required date, wrong datatype, cardinality violation | L1 |
| Logic | Simultaneous assignment of mutually exclusive types, cyclic hierarchy | L2 |
| Function | Deletion of a required CQ path | L3 |
| Semantic alignment | Substituting `plasma_etch` for an unrelated process, random rewiring of `overlappingFeature` | T1 |
| Hierarchy semantics | Flattening a process sub-hierarchy into a single parent node | T1, partly L3 |
| Judgment context | Substituting novelty ↔ inventive-step grounds, shuffling `RejectionType` labels | T1 · T2 |
| Metadata deletion | Removing CPC or applicant | T1 (weak signal) |
| Temporal leakage | Inserting CPC or concept links created after the query date | L0 or the leakage audit |
| qrel leakage | Restoring the ground-truth citation edges of the query into the retrieval features | Leakage audit |
| **Synonym mis-merge (cross-task)** | Forced merging of similar `Skill` / `Material` concepts — possibly harmless or even favorable to retrieval | **T3** (CQ-EM collapses) |
| **Shared-hierarchy inversion (cross-task)** | Inverting the parent–child relation of `Process` / `SubProcess` | **T3** (CQ-TF · CQ-EM), partly L3 |

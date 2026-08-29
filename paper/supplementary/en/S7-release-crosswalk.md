# S7 · Paper–release crosswalk

> The numbers this paper reports ↔ the numbers the public release shows ↔ the **resource
> generation** each belongs to ↔ the **reproduction grade** of each asset. The paper reports the
> frozen generation on which the experiments actually ran, whereas the release distributes the
> current generation reflecting later upstream corrections, so the two may differ. This is the
> English rendering of the Korean original
> [S7-release-crosswalk.md](../S7-release-crosswalk.md), which remains the record of the original
> wording.
>
> **No verdict and no measured value changes here.** This table does not correct a value; it states
> **which generation a value belongs to**.

§6.5 of the paper directs the reader to check against the release and its hashes. Four places
diverge — the count of vocabulary properties, the size of the claim-feature layer, the competency
question pass rate, and the graph triple signature — and the tables below resolve all four by
naming the generation each value belongs to.

## 1. Resource generations — where each value came from

| Generation | Upstream commit | Date | G₀ triples | What it produced |
|---|---|---|---|---|
| **Generation of §6 of the paper (arm O)** | `d578bf3` | 2026-07-23 | **105,588** | **Every retrieval number** in §5 and §6 · EP1 representation audit · EP2 fault injection · EP4 |
| **EP3 arm O′** | `2839afb` | 2026-08-01 | **105,713** | The post-substitution arm of the controlled resource substitution in EP3 (CR-007 applied, +125) |
| Former snapshot | `0a7ff15` | 2026-08-15 | 119,251 | ditto |
| **Current snapshot** | `013854b` | 2026-08-25 | **120,147** | `data/external/sdkb/` of this repository · **produces none of the numbers in the paper** |
| **Public release `v1.1.1-paper`** | `b8495b2` | 2026-08-21 | (public tree · A-Box emptied) | The edition archived by Zenodo `10.5281/zenodo.22046508` · **the edition this paper cites** |
| Former release `v1.1-paper` | `754fb78` | 2026-08-20 | ditto | Zenodo `10.5281/zenodo.22030396` · not cited, for reasons R1 and R2 below |

**Freezing evidence.** The snapshot signature of the paper's generation is in the signature history
of the repository. The per-file sha256 of arm O′ of EP3 is in the signature list of preregistration
document PLAN-040 (18 files). The source commit and
freshness record of the current snapshot are in `data/external/sdkb/PROVENANCE.json`, and the
per-file sha256 of every release asset is in the release's **`provenance/PROVENANCE.json`**
(323 assets at tag time · `release.upstream_commit = 754fb78`).

## 2. Correspondence of the numbers — four pairs

| Item | Value in the paper (location) | Generation | Value in the release | Generation | Source of the difference |
|---|---|---|---|---|---|
| `owl:ObjectProperty` | **97** (§3.2 · 97 → 98 in §5.3) | 105,588 / 105,713 | **99** | Current | CR-007 declared `skos:broader`, +1; a later upstream correction added another |
| `owl:DatatypeProperty` | **81** (§3.2) | 105,588 | **85** | Current | Later upstream correction |
| `owl:Class` | **103** (§3.2) | 105,588 | **103** (84 named + 19 blank nodes) | Current | **Identical** — only the way of counting is reported differently |
| Claim-feature sidecar | **11,605,931** triples (§3.2) | 105,588 | **11,770,236** | Current | More material to decompose after re-retrieval of the full text |

**The release values come from the T-Box module table and the A-Box layer table of the public
`README.md`; they were not transcribed by hand.** That the paper's values do belong to the stated
generation is confirmed by the frozen signatures in this repository.

## 3. Competency-question pass rate — **the denominators differ**

| | Paper | Release (fresh clone) | Release (after `refetch-fulltext`) |
|---|---|---|---|
| Full audit | **30/31** | 14/31 = 0.452 | **27/31 = 0.871** |
| Observed by the gate | 27/28 | — | 1.000 on each of `em`, `tf` and `core` |

**Do not subtract one from the other.** The paper's 30/31 was measured on an **internal G₀ loaded
with the claim-feature sidecar**, which counts CQ29–31 as 3/3 passed. The release's 27/31 was
measured on a **public reproduction that cannot build the sidecar**, which counts the same three as
failures. The four unrecovered questions are **CQ27, CQ29, CQ30 and CQ31**, all of which require
the sidecar layer. Because the decomposition input of the sidecar is KIPRIS full text and that text
may not be redistributed, **these four are not recovered even with an issued key**.

## 4. Reproduction grades — three levels

| Grade | Meaning | Assets | Measured basis |
|---|---|---|---|
| **ⓐ Full reproduction** | Identical output from public files alone | Shared T-Box · SHACL shapes · the CQ suites and their execution results · the requirements matrix · regulatory instances · the expert-matching A-Box · all frozen thresholds · the gate and leakage-check rules · the fault-injection specification · the source artifacts of the result tables · the figure-generation code · the evaluation harness (`benchmark/`) | Direct comparison against the per-file sha256 in the release's `provenance/PROVENANCE.json` |
| **ⓑ Approximate reproduction after re-collection by identifier** | Nearly identical output once full text is re-retrieved with a KIPRIS key | Patent A-Box · cited prior art · the confirmatory-split queries | Patent A-Box **33,934 against 33,931 = 0.009 %** difference · CQ **27/31** · the difference arises from where the abstract is read (the `astrtCont` field of the search response against the bibliographic query) |
| **ⓒ Auditable only** | Cannot be regenerated; only the frozen artifacts can be compared | The claim-feature layer (sidecar) · the questions that depend on it, **CQ27 and CQ29–31** · the company-confidential layer (only a de-identified perturbed copy exists) | The decomposition input is full text and may not be redistributed |

**We do not conceal that grade ⓒ exists.** The two deficits stated in §6.5 of the paper — that the
frozen snapshot alone cannot reproduce the concept links of the generation used in the text, and
that byte-level reproducibility of the hybrid fusion artifact is not established — are of the same
grade, and the details are in [S5](S5-submission-full-v2.md).

## 5. Rules for citing these numbers

1. **Do not cite a value without stating its generation.** `owl:ObjectProperty 97` is the value of
   the paper's generation and `99` is the value of the current generation. Both are correct.
2. **Do not update the paper's numbers to the release values.** Doing so would be *changing the
   conditions after seeing the results*; measurement on a new generation
   is **a new experiment under a new preregistration**.
3. **Do not cite the release values as expectations for the paper.** The same reason applies.
4. The reference for comparing release assets is the **version DOI**; to denote the dataset in
   general, use the concept DOI `10.5281/zenodo.22030395`.

## 6. Release deficits and their removal (2026-08-21)

| | What | Status |
|---|---|---|
| R1 | The `README.md` shipped in tag `v1.1-paper` calls itself `SDKB v1.0`, and the BibTeX title of the same edition also says `SDKB v1.0` | **Removed** — reissued as `v1.1.1-paper` |
| R2 | The `CITATION.cff` of the same edition has no DOI field (only `version: "1.1.0"`) | **Removed** — same reissue |
| R3 | The path of `PROVENANCE.json` is `provenance/` rather than the repository root | Removed — §6.5 of the paper states the path |

R1 and R2 close only by re-tagging, because what Zenodo archives is **the tree at tag time**, so a
correction committed after the tag does not enter the archive. On 2026-08-21 the metadata was
corrected upstream at `b8495b2`, `v1.1.1-paper` was issued, and the new version DOI
`10.5281/zenodo.22046508` was assigned. **Verified by downloading the archive**: line 21 of
`README.md` reads `# SDKB — Semiconductor Domain Knowledge Base`; the BibTeX carries
`version = {1.1.1}`; and `CITATION.cff` carries `version: "1.1.1"` and
`doi: 10.5281/zenodo.22030395`.

The mechanism behind R1 and R2 is that a tagged tree cannot state its own version DOI. That number
is assigned when the release is issued, so a tag can only carry the preceding number. The concept
DOI is stable and enumerates every version, so a tagged tree states that one.

**Asset invariance was confirmed by hash.** Of the 324 public assets, the ones whose hash moved are
the five metadata files (`README.md`, `README.ko.md`, `CITATION.cff`, `.zenodo.json`,
`CHANGELOG.md`) and the three reports the release build regenerates; the difference in the latter is
per-query wall-clock seconds and the generation timestamp. The ontology, data, code and evaluation
assets are **identical byte for byte**, and the CQ result is likewise 14/31. No asset was added or
removed.

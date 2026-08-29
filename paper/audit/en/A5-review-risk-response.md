> Audit record — migrated from S1 Appendix G. Kept verbatim as recorded; not revised to the
> current verdict phrasing. The current verdicts are held by paper/verdicts.yaml.

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


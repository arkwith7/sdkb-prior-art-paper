# 선행연구 공백과 연구질문 검토 (제안본 PLAN-093 · 2026-10-17)

> **확인 방법.** Crossref 레코드(DOI·권호·쪽)로 서지를 확인했다. 초록은 Semantic Scholar·OpenAlex·IDEAS·
> arXiv 초록면 또는 출판사·저장소 레코드의 검색 요약에서 읽었다. Elsevier·Springer 출판사 페이지는 접근 거부(403)여서
> 열지 못했고, 그 항목은 Crossref 레코드를 서지 확인으로 삼았다. **전문(full text)은 한 편도 읽지 않았다.**
> 초록 확인 여부를 항목마다 적는다. 참고문헌 목록(`paper/assembly/references.md`)에는 아직 넣지 않았다.
>
> **2026-10-17 개정(PLAN-095).** 흐름 F(특허 의미 검색) · G(추론형 LLM·Agent 기반 특허 과제) · H(이론)와 **비교표 §4′** 를 추가했다.
> **같은 날 2차:** F1·G1–G4·H1 여섯 편을 [TM-LITERATURE-FULLTEXT](TM-LITERATURE-FULLTEXT.md) 에서 전문 검토했다 — **서지 6/6 · 전문 4/6 · 초록만 2/6**(SEARCHFORMER · FOPNet 접근 거부).
> 아래 F·G·H 행의 "확인" 열과 §4′ 의 "확인 수준" 열은 그 기록을 따른다. 서지 확인은 내용 확인이 아니다.
>
> **신규성은 확정하지 않는다.** 아래 공백은 *"확인한 출처 범위에서"* 의 관측이며, §6 에 확인하지 못한 범위를 적는다.

## A. 신준석 교수 연구 — 실제 내용과 이 연구의 연결

교수의 선호를 추정하지 않고, **확인한 초록의 내용**만 연결 근거로 쓴다.

| # | 서지 | 확인 | 내용(초록 기준) | 이 연구와의 연결 |
|---|---|---|---|---|
| A1 | Lee, C., Kang, B., & Shin, J. (2015). Novelty-focused patent mapping for technology opportunity analysis. *TFSC*, 90(B), 355–365. doi:10.1016/j.techfore.2014.05.010 | 초록 | 특허 공백 대신 텍스트 마이닝 + 국소 이상치 계수로 특허별 신규성 점수를 매겨 지도화(LED 열관리) | **발굴 단계** 방법. 후보의 신규성을 순위화하나 기존 개시 근거와 대조하는 단계는 다루지 않는다 |
| A2 | Lee, J., Kim, C., & Shin, J. (2017). Technology opportunity discovery to R&D planning: Key technological performance analysis. *TFSC*, 119, 53–63. doi:10.1016/j.techfore.2017.03.011 | 초록 | 넓게 정의된 기회를 상세 R&D 계획으로 전환 · 성능 격차·성능 구조·R&D 실현 가능성·**기술 대안** 분석 · 전문가 노력 절감 보고 | **가장 가까운 앵커.** "발굴 이후" 단계를 다루고 기술 대안까지 간다. 이 연구는 그 다음, 곧 대안별 **기존 개시·차별성 근거**의 확보를 다룬다 |
| A3 | Lee, Y., Kim, S. Y., Song, I., Park, Y., & Shin, J. (2014). Technology opportunity identification customized to the technological capability of SMEs through two-stage patent analysis. *Scientometrics*, 100(1), 227–244. doi:10.1007/s11192-013-1216-0 | 초록 | 전문가 구축 속성·응용 표와 키워드 대조 → 행위–대상(SAO 류) 분석 반복 · 자원 제약 중소기업 | **자원 제약**을 명시적으로 다루나 발굴 쪽 |
| A4 | Shin, J., & Lee, H. (2013). Low-risk opportunity recognition from mature technologies for SMEs. *JETM*, 30(4), 402–418. doi:10.1016/j.jengtecman.2013.09.002 | 검색 요약 | 기술 복잡도·시장 적합성·성숙도·조직 적합의 4단계 저위험 기회 선별 · 반도체 장비 사례 | 위험 관점의 선별 · 기존 기술 근거 확인은 단계에 없음 · **반도체 장비 도메인 공유** |
| A5 | Hwang, S., & Shin, J. (2019). Extending technological trajectories to latest technological changes by overcoming time lags. *TFSC*, 143, 142–153. doi:10.1016/j.techfore.2019.04.013 | 초록 | 최신 논문을 특허 주경로에 연결해 공개·인용 지연 보정 | 인용 기반 근거의 **시점 지연** — 이 연구의 시점 마스크·노출 이력 설계와 같은 문제의식 |
| A6 | Kim, J., & Shin, J. (2018). Mapping extended technological trajectories. *Scientometrics*, 116(3), 1439–1459. doi:10.1007/s11192-018-2834-3 | 서지만 | — | 특허 인용 궤적 기반 기술 인텔리전스(초록 미확인) |
| A7 | (공저) Lee, B., Shin, J. 외 (2020). 공진화 분석 기반 기술 인텔리전스: 반도체 패키지 공정 사례. Korea Society for Innovation Management & Economics 발행 학술지(국문 학술지명 미확인) 28(4), 63–93. doi:10.14386/sime.2020.28.4.63 | 서지만 · **제1저자 미확인** | — | 반도체 + 기술 인텔리전스. **인용 전 서지 재확인 필요** |
| A8 | Han & Shin (2014) *Technovation* 34(9) · Shin, Lee & Park (2006) *Scientometrics* 69 | 제목만 | — | 배경 후보 |
| — | Cho & Shin (2022) *IEEE Access* 10 · Cho, Bae, Byun & Shin (2025) *PLOS ONE* 20 | 초록 | 전기차 시장 진입 자원 조합(RBV·TOE) | **연결 약함** — 특허·기회 검증 연구가 아니다. 본문 인용 불필요. 아카이브 초안이 인용한 근거를 재확인 없이 쓰지 않는다 |

**연결의 형태(초안).** 신준석 교수 연구 축의 A1–A3 은 특허 기반 기술기회의 **발굴·구체화**를 다룬다. 이 연구는
그 산출물(기술 대안 후보)을 입력으로 받는 **다음 단계**, 곧 제한된 검토 자원에서 후보의 기존 개시 근거를 확보하는
문제를 다룬다. 이 연결은 내용상의 위치 관계이며, 교수의 관심이나 평가를 추정한 것이 아니다.

## B. 기술 인텔리전스·기술기회 분석의 기반

| # | 서지 | 확인 | 쓰임 |
|---|---|---|---|
| B1 | Lichtenthaler, E. (2003). Third generation management of technology intelligence processes. *R&D Management*, 33(4), 361–375. doi:10.1111/1467-9310.00304 | 초록 | TI 과정 안에 검증 단계를 배치하는 틀 |
| B2 | Lichtenthaler, E. (2004). Technology intelligence processes in leading European and North American multinationals. *R&D Management*, 34(2), 121–135. doi:10.1111/j.1467-9310.2004.00328.x | 초록 | 누가 어떤 자원으로 검증하는가 |
| B3 | Kerr, C., Mortara, L., Phaal, R., & Probert, D. (2006). A conceptual model for technology intelligence. *IJTIP*, 2(1), 73. doi:10.1504/ijtip.2006.010511 | 초록 | mine/trawl/target/scan — 검증은 의사결정 수요가 주도하는 **target** 방식에 대응(이 대응은 해석) |
| B4 | Savioz, P. (2004). *Technology Intelligence*. Palgrave Macmillan. doi:10.1057/9781403948212 | 서지 | 중소기업 자원 제약 아래의 TI |
| B5 | Mortara, L. 외 (2009). *IJTM*, 48(1), 115. doi:10.1504/ijtm.2009.024603 | 서지만 | 실무 사례 |
| B6 | Porter, A. L., & Cunningham, S. W. (2004). *Tech Mining*. Wiley. doi:10.1002/0471698466 | 서지만 | 기반 |
| B7 | Porter, A. L., & Detampel, M. J. (1995). Technology opportunities analysis. *TFSC*, 49(3), 237–255. doi:10.1016/0040-1625(95)00022-3 | 목록 요약 | TOA 기원 |
| B8 | Yoon, B., & Park, Y. (2005). A systematic approach for identifying technology opportunities: Keyword-based morphology analysis. *TFSC*, 72(2), 145–160. doi:10.1016/j.techfore.2004.08.011 | 서지만 | 형태분석 기반 발굴 |
| B9 | Lee, S., Yoon, B., & Park, Y. (2009). An approach to discovering new technology opportunities: Keyword-based patent map approach. *Technovation*, 29(6–7), 481–497. doi:10.1016/j.technovation.2008.10.006 | 초록 | 공백의 검증이 **중요도·추세** 검정이지 기존 개시 검정이 아님 |
| B10 | Abbas, A., Zhang, L., & Khan, S. U. (2014). A literature review on the state-of-the-art in patent analysis. *WPI*, 37, 3–13. doi:10.1016/j.wpi.2013.12.006 | 서지만 | 리뷰 |
| **B11** | Park, S., Kim, G., & Lee, S. (2026). Evaluating the value of LLMs in patent-based technology intelligence: Toward increasing efficiency and reducing expert dependency. *TFSC*, 222, 124375. doi:10.1016/j.techfore.2025.124375 | Crossref·OpenAlex **서지만 · 초록 미열람(폐쇄 접근)** | **가장 가까운 기술경영 게재 선례**(제목상 "전문가 의존 감소" · 검색 요약상 특허 질의 작성 과제 포함). 전문 검토 전에는 차별을 확정하지 않는다 — 투고 전 필수 확인 |
| B12 | Jiang, P., Arena, A. P., Sorce, S., & Atherton, M. (2026). Large language models in the patent lifecycle: A systematic review. *WPI*, 87, 102506. doi:10.1016/j.wpi.2026.102506 | OpenAlex **초록 확인** | PRISMA · 129편(2018–2026초) · 심사·소추 단계 34편 · RAG 지배 · "사람 감독이 필요한 보조 도구" — 공백 4 의 전수 확인 대체물로 쓸 수 있는 후보(전문 미열람) |

## C. 선행기술 검색 평가 · 심사관 인용 정답의 한계 · 전문 검색 · LLM 질의

| # | 서지 | 확인 | 쓰임 |
|---|---|---|---|
| C1 | Lupu, M., & Hanbury, A. (2013). Patent Retrieval. *FnTIR*, 7(1), 1–97. doi:10.1561/1500000027 | 초록 | 특허 검색의 사용자·과정 모형 |
| C2 | Shalaby, W., & Zadrozny, W. (2019). Patent retrieval: a literature review. *KAIS*, 61(2), 631–660. doi:10.1007/s10115-018-1322-7 | 초록 | 자동 검색 회수가 "평균 수준" — 상호작용적 접근의 필요 |
| C3 | Krestel, R. 외 (2021). A survey on deep learning for patent analysis. *WPI*, 65, 102035. doi:10.1016/j.wpi.2021.102035 | 초록 | 방법 배경 |
| C4 | Piroi, F., & Zenz, V. (2011). Evaluating IR in the IP domain: The CLEF-IP campaign. In *Current Challenges in Patent IR*, 87–108. doi:10.1007/978-3-642-19231-9_4 · Piroi 외 (2011) CLEF-IP 2011, CEUR-WS 1177 | 레코드 | 인용 기반 정답이 표준 평가 관행 |
| C5 | Fujii, A., Iwayama, M., & Kando, N. (2004). The patent retrieval task in the fourth NTCIR workshop. *SIGIR 2004*, 560–561. doi:10.1145/1008992.1009120 | 초록 | 무효 자료 검색 과제 |
| C6 | Magdy, W., & Jones, G. J. F. (2010). Examining the robustness of evaluation metrics for patent retrieval with incomplete relevance judgements. *CLEF 2010 LNCS*, 82–93. doi:10.1007/978-3-642-15998-5_10 | 서지만 · **결론 미확인** | 불완전 정답의 지표 강건성 — 인용 전 본문 확인 필요 |
| C7 | Lupu, M., Piroi, F., & Hanbury, A. (2010). Aspects and analysis of patent test collections. *PaIR '10*, 17–22. doi:10.1145/1871888.1871892 | 서지만 | 시험 집합 |
| C8 | Helmers, L. 외 (2019). Automating the search for a patent's prior art with a full text similarity search. *PLOS ONE*, 14(3), e0212103. doi:10.1371/journal.pone.0212103 | 검색 요약 | 심사관 인용 라벨의 잡음·불완전 |
| C9 | Alcácer, J., & Gittelman, M. (2006). Patent citations as a measure of knowledge flows: The influence of examiner citations. *REStat*, 88(4), 774–779. doi:10.1162/rest.88.4.774 | 초록 | 미국 특허 인용의 약 2/3 가 심사관 삽입 |
| C10 | Criscuolo, P., & Verspagen, B. (2008). Does it matter where patent citations come from? *Research Policy*, 37(10), 1892–1908. doi:10.1016/j.respol.2008.07.011 | 초록 | 인용 출처(발명자·심사관)의 차이 |
| C11 | Russell-Rose, T., Chamberlain, J., & Azzopardi, L. (2018). Information retrieval in the workplace. *IP&M*, 54(6), 1042–1057. doi:10.1016/j.ipm.2018.07.003 | 초록 | 전문 검색자의 Boolean 관행 |
| C12 | Wang, S., Scells, H., Koopman, B., & Zuccon, G. (2023). Can ChatGPT write a good Boolean query for systematic review literature search? *SIGIR '23*, 1426–1436. doi:10.1145/3539618.3591703 | 초록(일부) | LLM Boolean 질의 생성 — **체계적 문헌고찰 영역** |
| C13 | Scells, H. 외 (2020). Automatic Boolean query formulation for systematic review literature search. *WWW 2020*, 1071–1081. doi:10.1145/3366423.3380185 | 서지 | 자동 질의 구성 |

## D. 심사 기록·거절 논거의 재사용

| # | 서지 | 확인 | 쓰임 |
|---|---|---|---|
| D1 | Lu, Q., Myers, A. F., & Beliveau, S. (2017). USPTO patent prosecution research data: Unlocking office action traits. USPTO Economic Working Paper 2017-10. doi:10.2139/ssrn.3024621 | USPTO 페이지 | 거절 근거·대상 청구항·인용 선행기술을 담은 OA 데이터(440만 건) |
| D2 | Risch, J., Alder, N., Hewel, C., & Krestel, R. (2020). PatentMatch. arXiv:2012.13919 | 초록 | 청구항–인용 문헌 구절 쌍(EPO 조사 범주) — **요소 수준** 판단 재사용 |
| D3 | Parikh, A., & Dori-Hacohen, S. (2024). ClaimCompare. arXiv:2407.12193 | 초록 | OA 기반 신규성 파괴 쌍 |
| D4 | Ikoma, H., & Mitamura, T. (2025). Can AI examine novelty of patents? arXiv:2502.06316 | 초록 | 실제 심사 사례 기반 신규성 판정 |
| D5 | Lim, H. 외 (2025). PANORAMA: A dataset and benchmarks capturing decision trails and rationales in patent examination. arXiv:2510.24774 | 초록 · 게재처 미확인 | **가장 가까운 선행.** 심사 판단 궤적·논거를 과제로 분해 · LLM 은 선행기술 검색·위치 찾기는 비교적 잘하고 신규성·진보성 판단은 약함. 틀은 **심사 자동화 벤치마크**이지 기술 인텔리전스가 아니다. **→ G1 로 재분류 · 서지 확정(NeurIPS 2025 D&B) · 비교표 §4′** |

## E. 설계과학 방법론

Hevner, March, Park & Ram (2004) *MISQ* 28(1), 75–106, doi:10.2307/25148625 · Peffers 외 (2007) *JMIS* 24(3), 45–77,
doi:10.2753/mis0742-1222240302 · Gregor & Hevner (2013) *MISQ* 37(2), 337–355, doi:10.25300/misq/2013/37.2.01.
→ 방법론 장에만 둔다. 기여 유형은 Gregor & Hevner 의 틀에서 **개선(improvement)** 후보로 서술하되, 기술경영 측 기여는 발견과 적용 조건으로 쓴다.

## F. 특허 의미 검색 — "키워드를 넘어서는 것" 자체는 신규성이 아니다

| # | 서지 | 확인 | 내용(초록 기준) | 이 연구가 구분해야 할 것 |
|---|---|---|---|---|
| F1 | Vowinckel, K., & Hähnke, V. D. (2023). SEARCHFORMER: Semantic patent embeddings by siamese transformers for prior art search. *World Patent Information*, 73, 102192. doi:10.1016/j.wpi.2023.102192 | Crossref · **초록만 · 전문 접근 거부** · 2차 3편(FULLTEXT §4) | EPO 조사보고서의 청구항–인용 쌍으로 미세조정한 특허 전용 Sentence-BERT. 한정된 평가 집합(2,014쌍)에서 BM25·범용 모델을 유의하게 상회(α=.01). 전체 코퍼스 검색은 계산 제약으로 미수행 · 모델·데이터 비공개 | 의미 임베딩 + BM25 결합은 이미 있다. 이 연구의 A⓪(혼합 검색)은 **그 수준의 기준선**이며 기여가 아니다 |

## G. 추론형 LLM · Agent 기반 특허 과제 — 서로 다른 부분을 다룬다

| # | 서지 | 확인 | 내용(초록 기준) | 이 연구가 구분해야 할 것 |
|---|---|---|---|---|
| G1 | Lim, H., Nam, S., Na, S., Cho, J. Y., Yang, J. Y., Shin, H., Lee, Y., Kim, J., Lee, M., & Hong, H. (2025). PANORAMA: A dataset and benchmarks capturing decision trails and rationales in patent examination. *NeurIPS 2025 Datasets & Benchmarks*. arXiv:2510.24774 | **전문 확인**(arXiv v1 · FULLTEXT §1) · NeurIPS 게재 확인 | 미국 심사 기록 8,143건 · 과제 셋(PAR4PC 선행기술 검색 → PI4PC 구절 위치 → 신규성·진보성 판단). **PAR4PC 는 후보 8개 중 복수 선택(객관식 · 정확도)** · 2,896 인스턴스 · LLM 12종(추론형 QwQ-32B · EXAONE-Deep-32B 는 CoT 로만) · GPT-4o 최고 51.04% · HF 공개 | **가장 가까운 선행.** 그러나 평가는 "주어진 후보 8개에서 고르기"다. 검색식을 만들어 **대규모 후보에서 제한된 검토량 안에 발견**하는 평가와 다르다 — 이것이 차별화 지점 |
| G2 | Zheng, G., An, T., Zuo, Y., Wang, S., & Zhai, Y. (2026). From LLMs to AI agents: a systematic benchmark for SAO structure extraction in patent analytics. *Scientific Reports*, 16, 19036. doi:10.1038/s41598-026-49727-1 | **전문 확인**(Europe PMC JATS · FULLTEXT §3) | 단일 LLM(GPT-4o · Gemini 1.5 Pro · Claude 3.5 Sonnet) 대 성찰·수정 루프 Agent. Agent 가 F1 을 올리나(최고 89.58%) 비용이 **40–60배**(문장당 11k–15k 토큰) | **정보 추출 성능과 선행기술 발견 성능을 구분한다.** 비용 보고 형식(토큰·호출)은 참고 |
| G3 | Yoo, Xu, & Cao (2026). PatentMind: A multi-aspect reasoning graph for patent similarity evaluation. *Findings of ACL 2026*, 14947–14964. doi:10.18653/v1/2026.findings-acl.735 · arXiv:2505.19347 | **전문 확인**(arXiv v3 · 게재본 미대조 · FULLTEXT §2) | 기술특징·적용분야·청구범위를 분리한 추론 기반 유사성 평가 · 전문가 판정과 r=0.938 · 임베딩 대비 계산 비용 큼(2차 인용) | **주어진 특허쌍의 평가**와 **대규모 후보에서의 발견**을 구분한다 |
| G4 | Wang, N., Wan, Z., Zhao, H., Wang, C., & Wang, Y. (2026). FOPNet: A comprehensive functional semantic knowledge graph for deep technical analysis in patents. *World Patent Information*, 84, 102427. doi:10.1016/j.wpi.2026.102427 | Crossref · **초록만(간접) · 전문 접근 거부**(FULLTEXT §5) | 기능–대상–속성 삼중항을 특허 지식그래프에 연결 · USPTO 심사 결정·PTAB 기반 유사성 벤치마크 공개 · 키워드 대비 +43%(초록 주장) | **온톨로지·지식그래프와 LLM 의 결합 자체를 신규성으로 제시하지 않는다.** 이 연구의 질문은 "결합" 이 아니라 "판단 지식의 제공이 Agent 의 검색 행동을 바꾸는가" 다 |

## H. 이론적 출발점

| # | 서지 | 확인 | 쓰임 |
|---|---|---|---|
| H1 | Zollo, M., & Winter, S. G. (2002). Deliberate learning and the evolution of dynamic capabilities. *Organization Science*, 13(3), 339–351. doi:10.1287/orsc.13.3.339.2780 | **전문 확인**(수락원고 · 출판본 쪽수 미대응 · FULLTEXT §6) | 경험 축적 · 지식 명료화 · 지식 체계화의 구분. **검증 가능한 작은 기제**(명시화된 판단 지식 → 검색 루틴 변화 · 과제 조건별 효용)만 가져온다. **동적역량 향상은 주장하지 않는다**(PLAN-095 §3) |

## 4′. 비교표 — 입력 · 실행 · 후보 범위 · 추론 설정 · 외부 지식 · 비용 · 전문가 · 공개

"초록만으로 판단한 칸은 **미확인**" 이 규칙이다. 빈 칸이 아니라 미확인이라고 적는다.

| 연구 | 입력 자료 | 실제 검색 실행 | 후보 범위 | 모델 추론 설정 | 외부 지식 | 비용 통제 | 전문가 평가 | 공개 코드·데이터 | 확인 수준 |
|---|---|---|---|---|---|---|---|---|---|
| F1 SEARCHFORMER | 청구항 텍스트 | **없음** — 후보 집합 내 bi-encoder 순위(focal 당 음성 197–955 · 2차) | 2,014쌍 · 전체 코퍼스 아님 | 해당 없음(인코더) | 없음 | 미확인 | 미확인 | **모델·데이터 비공개** | 초록만 + 2차 |
| G1 PANORAMA | 출원 제목·초록·청구항 전체 + 후보 8(각 제목·초록·청구항 · 평균 16,060 토큰) | **없음**(객관식 복수 선택 · 단일 호출) | 8(gold/silver/negative · negative 는 같은 class 타 출원의 인용) | zero-shot/CoT 프롬프트 · **추론형 2종도 CoT 프롬프트로만** · temp 0 | 없음 | **없음** | 파싱 검증 7인만(산출물 평가 없음) | HF + GitHub + 프롬프트 | **전문** |
| G2 SAO Agent | 특허 문장 14,537(영어 72건) | **없음**(추출) | 해당 없음 | 반성–정련 루프 ≤3회 · **도구 호출 없음** · 네이티브 추론 모델 없음 · temp 0 | 없음 | **$0.0024–0.0038 → Agent $0.09–0.16/문장 · 40–60배**(Table 6) | 주석 5인만 | 데이터 요청 시 · 코드 없음 | **전문** |
| G3 PatentMind | 특허쌍 500(제목·초록·청구항 + IPC) | **없음**(쌍 점수) | 2 | 고정 8호출 프롬프트 DAG · **Agent 아님** · 추론 모델은 백본 교체만 · temp 0.2 | IPC 코드만 | **20–30초 · ≈$0.003/쌍** | 주석 4인(κ 0.588) | "accept 후" · URL 없음 | **전문** |
| G4 FOPNet | 미확인 | 미확인(쌍/후보 랭킹 추정) | 미확인 | 선택적 LLM 재순위만 | **F-O-P 기능 의미 KG(임베딩에 내장)** | 미확인 | 미확인 | 벤치마크 공개 선언 · 코드 미확인 | 초록만(간접) |
| C12 Wang et al. 2023 | 체계적 고찰 주제 | **Boolean 실행** | 문헌 DB | ChatGPT 프롬프트 | 없음 | 미확인 | 미확인 | 미확인 | 초록 일부 |
| **이 연구(PLAN-094 · 미실행)** | 청구항·초록 | **Boolean 실행(KIPRIS) + 혼합 순위 A⓪** | 대규모 후보 · 검토 200 | **동결된 추론 설정 · Agent 루프(턴 24 · 호출 12)** | **심사 판단 지식(표 / 온톨로지 도구)** | **호출·토큰·USD·지연·실패율** | **선택(EXPERT-CASE-PROTOCOL)** | 집계·식별자·프롬프트 sha 공개 예정 | 설계 |

이 표가 보여 주는 공백은 한 줄이다 — **실제 검색을 실행하고 · 대규모 후보에서 · 제한된 검토량 아래 · 추론 설정을 통제한
Agent 에 · 외부 판단 지식을 더한** 조건을 함께 갖춘 연구는 확인한 범위에 없다. 각 요소는 따로 존재한다 — 선택(G1) · 쌍 평가(G3) ·
추출 루프(G2) · 임베딩 순위(F1) · KG 보강 임베딩(G4). **경쟁 설명과 재판정은 FULLTEXT §7** — 특히 PANORAMA 의 가이드라인 CoT 가
자유 CoT 보다 낮았다는 관측은 "판단 지식 제공이 효과가 없을 수 있다" 는 선행 음성 신호이고, F1·G4 전문에 예산 통제가 있을 가능성은
배제하지 못했다.

## 5. 공백 (확인한 출처 범위에서)

1. **기술기회 분석은 발굴·계획 단계에서 끝난다.** A1–A4·B7–B9 의 검증 단계는 중요도·추세·실현 가능성·적합성을 본다.
   후보 대안의 **기존 개시·차별성 근거 확보**를 별도 과제로 다룬 것은 확인한 범위에서 보이지 않았다.
2. **선행기술 검색 연구는 심사관 인용을 정답으로만 쓴다.** C4–C8 은 정답으로 쓰고 그 불완전성을 논한다.
   그 판단 지식을 **심사 밖의 사용자(R&D·기술 인텔리전스 담당)의 입력**으로 재사용한 것은 확인한 범위에서 보이지 않았다.
3. **OA·심사 논거 데이터셋은 심사 자동화를 겨냥한다.** D1–D5 는 거절 논거를 기계가 쓸 수 있게 만들지만, 기술
   인텔리전스·제한된 검토 자원과 연결하거나 재사용이 **언제 통하고 언제 실패하는지**를 진술하지 않았다(확인 범위).
4. **추론·도구 사용이 가능한 AI 의 선행기술조사에서, 과거 전문가 판단을 명시적 지식으로 제공하는 것이 어떤 검색 행동을
   바꾸고 어느 조건에서 추가적인 조사 가치를 만드는지에 대한 통제된 증거가 없다**(확인 범위 · §4′). LLM 질의 생성은 체계적
   문헌고찰에서 평가됐고(C12–C13), 특허 쪽의 Agent·추론형 연구(G1–G4)는 **후보 선택 · 추출 · 쌍 평가**를 다룬다 — 검색식을
   만들어 제한된 검토량 안에서 발견하는 평가가 아니다. 이 공백은 세 질문으로 좁힌다: **추가 가치**(강한 Agent + 판단 지식 =
   같은 예산에서 근거 확보 개선?) · **작동 기제**(요소 분해 · 대체 표현 · 관점 확장 · 검색식 수정 중 무엇?) · **적용 조건**(어떤
   질의에서 도움이 되고 어떤 질의에서 비용·잡음만 느는가 · 표 대 온톨로지).

## 6. 확인하지 못한 범위 (신규성 주장 금지의 근거)

Google Scholar·Scopus·WoS 전수 검색 · Elsevier·Springer 원문 · **국내 문헌(KCI·RISS)과 신준석 교수 국문 논문 전체** ·
KIPO·EPO 내부 AI 검색 도구와 상용 특허 분석 업체 자료 · 모든 논문의 전문 · C6·C7·B5·B6·A6·B8·B10 의 결론 ·
D2–D4 의 학술지 게재처 · 특허 선행기술 조사 전용 LLM 질의 생성 연구 · **Agent·추론형 LLM 특허 연구의 전수**(G1–G4 는 조언이 든 것만 확인) · F1·G1–G4·H1 의 전문.
→ 투고 전에 **국내 문헌과 특허 전용 LLM 검색 연구**를 한 번 더 확인한다.

## 7. 연구질문 검토와 수정안

| 출발안 | 검토 | 수정안 |
|---|---|---|
| RQ1 심사 기록에서 재사용할 수 있는 판단 지식은 무엇이며, 개별 사건의 판단과 어떻게 구분하는가? | 공백 3 에 대응. 근거는 상류 논증층(블록·논거 범위 · FAIL 보존 · 하류 미소비) | 유지. 답의 형태를 "구분 기준과 그 **검증 범위**"로 한정 |
| RQ2 그 지식은 제한된 검토량에서 알려진 심사 근거의 확보·복원을 개선하는가? | 공백 2·4 에 대응. "개선"은 비교 기준이 없으면 요소 분해 지침의 효과와 섞인다 | **"같은 검토량에서, 요소 분해 지침만 준 경우와 구분되는 근거 확보 차이를 만드는가?"** (PLAN-094 주 대비) |
| RQ3 효과가 발생하거나 실패하는 조건은 무엇인가? | 공백 3 에 대응. 기존 결과(EP3 · 미검색 89%)로 일부 답할 수 있음 | 유지. 조건 축을 사전 지정: 정답 언어 · 요소 수 · 부분 개시 · 지식 표현 형식(표 대 온톨로지) · 형식 검증 통과 여부 |

### 7.1 v2 (2026-10-17 · PLAN-095 §2)

중심 문장: *"추론형 LLM 과 검색 도구를 쓰는 AI Agent 가 선행기술조사를 수행하는 조건에서, 과거 특허 심사 판단 지식을
어떻게 구조화하고 제공해야 제한된 조사 자원 안에서 기술대안 검토에 필요한 근거 확보를 개선하며, 어떤 조건에서 효과와
한계를 보이는가?"*

| 좌표 | 질문 | 공백 | 증거 자리 |
|---|---|---|---|
| RQ-0 (구 RQ1) | 재사용 가능한 판단 지식과 개별 사건 판단의 구분 | 3 | 상류 논증층 · 하류 소비 0 |
| RQ-A 추가 가치 | 강한 Agent 에 판단 지식을 더하면 같은 예산에서 근거 확보가 개선되는가 | 4 | PLAN-094 A④−A② · 참조 A②−A⓪ |
| RQ-B 작동 기제 | 요소 분해 · 대체 표현 · 관점 확장 · 검색식 수정 중 무엇을 통해 | 4 | PLAN-094 §3.4′ 코딩 · κ |
| RQ-C 적용 조건 | 어떤 질의에서 도움·잡음 · 제공 방식(표 대 온톨로지) 차이 | 3·4 | PLAN-094 하위집단 · A④−A③ |

설계 문서 밖(파생본 본문)에서는 영문자 좌표 대신 서술형 또는 `RQ1`–`RQ3` 을 쓴다(CLAUDE.md §0.9-2).

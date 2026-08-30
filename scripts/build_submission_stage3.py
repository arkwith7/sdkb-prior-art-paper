#!/usr/bin/env python3
"""scripts/build_submission_stage3.py — 3단계(재조준·축약) 파생본을 **기계로** 조립한다.

용법:  python scripts/build_submission_stage3.py [--check]
종료:  0 = 성공(또는 --check 정합) · 1 = 불일치 · 2 = 앵커 소실·중복

왜 스크립트인가 (PLAN-048 3단계 · CLAUDE.md §1-1·§2.3)
- 3단계는 **문장을 새로 쓰는 단계**다. 그러나 **표의 수치는 새로 쓰는 대상이 아니다** —
  손으로 옮겨 적으면 오탈자가 곧 조작이 된다(§1-1 "수치는 실행된 코드의 출력"). 그래서
  산문은 사람이 쓰고(`paper/manuscript/stage3_source.md`), **표는 축약 전 전문에서 문자
  단위로 복사**한다. 이 파일이 그 경계를 강제한다.
- 복사 원본은 **조립 입력 층**(`paper/assembly/`)이다. 표는 `frozen-tables.md`, 서지는
  `references.md` 에 있으며 둘 다 축약 이전 파생본에서 기계로 떼어 온 사본이다. 조립 입력은
  독자에게 나가는 자료가 아니므로, 보충자료를 정리해도 조립이 흔들리지 않는다.
- 앵커가 없거나 둘 이상이면 **조용히 넘어가지 않고 실패**한다(rc 2). 표가 소리 없이
  빠지거나 엉뚱한 표가 실리는 사고를 구조적으로 막기 위해서다.

산문 소스에 쓰는 지시자는 둘뿐이다.
    {{COPY:<앵커 문자열>|table}}     앵커 행 다음에 오는 마크다운 표 블록을 그대로 넣는다
    {{COPY:<앵커>|table|keep:A;B}}   같은 표에서 **머리글과 지정한 행만** 골라 넣는다
    {{COPY:<앵커>|table|from:X.md}}  동결본 대신 paper/tables/X.md(생성기 산출)에서 가져온다
    (from: 은 keep: 보다 앞에 쓴다 — keep 의 행 앵커에는 `|` 가 들어간다)
    {{BIB}}                          참고문헌 목록을 그대로 넣되, 아래 BIB_FIXES 만 교체한다

**행 선별(keep)도 옮겨 적기가 아니라 복사다 (PLAN-053 §2.3).** 본문 표에서 주장을 지지 않는
행을 내릴 때(표 8 = 17행 → 5행), 남길 행을 손으로 다시 타자하면 이 파일의 존재 이유가 사라진다.
그래서 남길 행을 **앵커로 지목**하고 원문 행을 그대로 가져온다. 앵커가 정확히 한 행에 걸리지
않으면 실패한다(rc 2). 내린 행은 삭제가 아니라 이관이며 전문은 동결본에 그대로 남는다.

**표 안의 문구도 규약을 따라야 한다 — 그러나 표를 다시 타자하지는 않는다(CELL_FIXES).**
치환은 **나가는 표에만** 건다(2026-08-29). 동결본 전체에 걸면 복사되지 않는 표까지 고치게 되어,
고친 문장은 어디에도 나가지 않고 앵커 유지 의무만 남는다 — 실측 21건 중 16건이 그러하였고,
그 열여섯이 동결본의 절 일곱을 붙잡아 보충자료를 정리할 수 없게 만들었다. 복사되는 표 어디에도
걸리지 않는 치환이 남아 있으면 조립이 멈춘다.
절 번호가 바뀌거나(§4.9 → §4.5) §0.8 문구 사전이 늘면 표 셀도 따라가야 하는데, 그 이유로
표를 손으로 옮겨 적으면 이 파일의 존재 이유가 사라진다. 그래서 셀 치환은 **앵커가 정확히
한 번 매치되는 목록으로만** 허용하고, **수치가 하나라도 달라지면 실패**시킨다(rc 2).
수치를 정말 바꿔야 하면 사유를 적어 명시적으로 예외 처리하며, 그 사유는 빌드 로그에 남는다.

**서지 확정도 손이 아니라 목록으로 한다.** 3단계는 플레이스홀더 6건을 없애는 단계인데(D2),
목록 전체를 다시 타자하면 어느 줄이 왜 바뀌었는지 보이지 않는다. 그래서 **바뀐 줄만** 아래
BIB_FIXES 에 적고, 각 항목이 원문에서 정확히 한 번 매치되지 않으면 실패한다(rc 2).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROSE = Path("paper/manuscript/stage3_source.md")
# 복사 원본 — **조립 입력 층**(2026-08-29 · 사용자 승인). 구판은 축약 이전 파생본
# `paper/supplementary/S5-submission-full-v2.md` 를 직접 읽었고, 그래서 S5 하나가 두 임무를
# 졌다 — 독자에게 근거를 보이는 일과 조립기에 표를 빌려주는 일이다. 두 임무는 서로를 붙잡아,
# 조립을 위해 남긴 자리가 보충자료의 정리를 막고 보충자료의 교정이 조립을 멈췄다(실제 2회).
# 자리를 나누면 그 결합이 사라진다. **표의 내용은 한 글자도 바뀌지 않았다** — 분리 전후의
# 조립 산출물이 바이트 단위로 동일함을 확인하였다.
FROZEN = Path("paper/assembly/frozen-tables.md")
BIB_SRC = Path("paper/assembly/references.md")
TARGET = Path("paper/submission/manuscript.md")

DIRECTIVE = re.compile(
    r"\{\{COPY:(?P<anchor>[^|}]+)\|(?P<mode>table)"
    # from: 이 keep: 보다 앞이다 — keep 의 행 앵커에는 `|` 가 들어가므로 뒤에 와야 한다.
    r"(?:\|from:(?P<src>[^|}]+))?"
    r"(?:\|keep:(?P<keep>[^}]+))?\}\}"
)

# `from:` 로 지목할 수 있는 두 번째 복사 원본 — **생성기가 만든 표**다(PLAN-060 B3).
# 왜 필요한가: S5 는 2단계 산출물의 동결 사본이므로 그 뒤에 새로 계산한 표는 그 안에 없다.
# 그렇다고 산문 소스에 손으로 적으면 이 파일의 존재 이유가 사라진다(§1-1). 그래서 원본을
# 하나 더 허용하되, **디렉터리를 paper/tables/ 로 못박아** 아무 파일이나 끌어오지 못하게 한다.
# 이 원본에는 CELL_FIXES 와 절 재번호를 적용하지 않는다 — 생성 시점에 이미 최종 번호다.
GENERATED_DIR = Path("paper/tables")

BIB_START = "# 참고문헌"
BIB_END = "[미확정 서지"          # 이 행부터는 싣지 않는다 — 미확정 목록의 두 항목은 본문 미인용이다.

# (원문에서 찾을 조각, 그 행을 대신할 내용) · 내용이 None 이면 그 행을 지운다.
# 근거는 전부 2026-08-12 원문·출판사 페이지 대조다(PLAN-048 3단계 서지 확정).
BIB_FIXES: list[tuple[str, str | None]] = [
    (
        "Brank, J., Grobelnik, M., & Mladenić, D. (2005).",
        "Brank, J., Grobelnik, M., & Mladenić, D. (2005). A survey of ontology evaluation techniques. "
        "In *Proceedings of the Conference on Data Mining and Data Warehouses (SiKDD 2005)* (pp. 166–170). "
        "Ljubljana, Slovenia. https://aile3.ijs.si/dunja/SiKDD2005/Papers/BrankEvaluationSiKDD2005.pdf",
    ),
    (
        "Daniell, S., Buzhinsky, I., & Björkqvist, S. (2025).",
        "Daniell, K., Buzhinsky, I., & Björkqvist, S. (2025). Efficient patent searching using graph "
        "transformers. In *Proceedings of the PatentSemTech Workshop at SIGIR 2025*. "
        "https://doi.org/10.48550/arXiv.2508.10496",
    ),
    (
        "Faruqui, M., Tsvetkov, Y., Rastogi, P., & Dyer, C. (2016).",
        "Faruqui, M., Tsvetkov, Y., Rastogi, P., & Dyer, C. (2016). Problems with evaluation of word "
        "embeddings using word similarity tasks. In *Proceedings of the 1st Workshop on Evaluating "
        "Vector-Space Representations for NLP (RepEval)* (pp. 30–35). https://aclanthology.org/W16-2506/",
    ),
    (
        "Kontokostas, D., Westphal, P.,",
        "Keet, C. M., & Ławrynowicz, A. (2016). Test-driven development of ontologies. In *The Semantic "
        "Web: Latest Advances and New Domains (ESWC 2016)* (LNCS Vol. 9678, pp. 642–657). Springer. "
        "https://doi.org/10.1007/978-3-319-34129-3_39\n\n"
        "Kontokostas, D., Westphal, P., Auer, S., Hellmann, S., Lehmann, J., Cornelissen, R., & Zaveri, A. "
        "(2014). Test-driven evaluation of linked data quality. In *Proceedings of the 23rd International "
        "Conference on World Wide Web* (pp. 747–758). https://doi.org/10.1145/2566486.2568002",
    ),
    # 동결 원문에서 이 항목만 알파벳 순서를 벗어나 Piroi 뒤에 있었다. 자리를 옮겨야 하므로
    # 여기서는 지우고, 교정한 서지를 BIB_INSERTS 에서 Piroi 앞에 넣는다(2026-08-16).
    ("Pauwels, P., van den Bersselaar, R., & Verhelst, J. (2024).", None),
    (
        "Porzel, R., & Malaka, R. (2004).",
        "Porzel, R., & Malaka, R. (2004). A task-based approach for ontology evaluation. In *Proceedings "
        "of the ECAI-2004 Workshop on Ontology Learning and Population*. Valencia, Spain.",
    ),
    # TDD 계열의 대표 서지는 데이터셋 논문이 아니라 방법 논문이다 — 위에서 Keet & Ławrynowicz 로
    # 갈음했으므로 이 항목은 뺀다(본문 인용도 함께 바뀌었다).
    ("Potoniec, J., Wiśniewski, D.,", None),
    (
        "Solihin, W., Eastman, C., & Lee, Y.-C. (2015).",
        "Solihin, W., Eastman, C., & Lee, Y.-C. (2015). Toward robust and quantifiable automated IFC "
        "quality validation. *Advanced Engineering Informatics, 29*(3), 739–756. "
        "https://doi.org/10.1016/j.aei.2015.07.006",
    ),
]

# 3단계에서 새로 인용한 문헌(설계과학연구 프레임 · §3). 알파벳 순서 자리에 끼워 넣는다.
BIB_INSERTS: list[tuple[str, str]] = [
    (
        # Gruber 앞이다 — "Gregor" < "Gruber" < "Grüninger"(2026-08-16 교정).
        "Gruber, T. R. (1993).",
        "Gregor, S., & Hevner, A. R. (2013). Positioning and presenting design science research for "
        "maximum impact. *MIS Quarterly, 37*(2), 337–355. https://doi.org/10.25300/MISQ/2013/37.2.01",
    ),
    (
        "Hogan, A., Blomqvist, E.,",
        "Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems "
        "research. *MIS Quarterly, 28*(1), 75–105. https://doi.org/10.2307/25148625",
    ),
    (
        "W3C. (2017).",
        "Venable, J., Pries-Heje, J., & Baskerville, R. (2016). FEDS: A framework for evaluation in design "
        "science research. *European Journal of Information Systems, 25*(1), 77–89. "
        "https://doi.org/10.1057/ejis.2014.36",
    ),
    # 1·2장 재구성(2026-08-16)에서 새로 인용한 문헌 — AI 시대의 명시적 지식 표현(§1),
    # 공학 정보학의 지식그래프(§1·§2.2), 측정 이론의 대리지표 논의(§2.3).
    (
        "Brank, J., Grobelnik,",
        "Bharadwaj, A. G., & Starly, B. (2022). Knowledge graph construction for product designs from "
        "large CAD model repositories. *Advanced Engineering Informatics, 53*, 101680. "
        "https://doi.org/10.1016/j.aei.2022.101680",
    ),
    (
        "Lupu, M., & Hanbury",
        "Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., et al. (2020). Retrieval-augmented "
        "generation for knowledge-intensive NLP tasks. In *Advances in Neural Information Processing "
        "Systems 33* (pp. 9459–9474).",
    ),
    (
        "Piroi, F., & Hanbury",
        "Manheim, D., & Garrabrant, S. (2018). Categorizing variants of Goodhart's law. *arXiv*. "
        "https://doi.org/10.48550/arXiv.1803.04585",
    ),
    (
        "Piroi, F., & Hanbury",
        "Pan, S., Luo, L., Wang, Y., Chen, C., Wang, J., & Wu, X. (2024). Unifying large language models "
        "and knowledge graphs: A roadmap. *IEEE Transactions on Knowledge and Data Engineering, 36*(7), "
        "3580–3599. https://doi.org/10.1109/TKDE.2024.3352100",
    ),
    (
        "Thomas, R., & Uminsky",
        "Strathern, M. (1997). 'Improving ratings': Audit in the British University system. *European "
        "Review, 5*(3), 305–321. "
        "https://doi.org/10.1002/(SICI)1234-981X(199707)5:3<305::AID-EURO184>3.0.CO;2-4",
    ),
    # §2 문헌 보강(2026-08-16) — 공학 지식의 공유·진화(§2.2). 서지는 출판사 페이지 대조.
    (
        "Daniell, K., Buzhinsky,",
        "Chungoora, N., Young, R. I. M., Gunendran, G., Palmer, C., Usman, Z., Anjum, N. A., "
        "Cutting-Decelle, A.-F., Harding, J. A., & Case, K. (2013). A model-driven ontology approach for "
        "manufacturing system interoperability and knowledge sharing. *Computers in Industry, 64*(4), "
        "392–401. https://doi.org/10.1016/j.compind.2013.01.003",
    ),
    (
        "Pan, S., Luo, L.,",
        "Noy, N. F., & Klein, M. (2004). Ontology evolution: Not the same as schema evolution. *Knowledge "
        "and Information Systems, 6*(4), 428–440. https://doi.org/10.1007/s10115-003-0137-2",
    ),
    (
        "Zaveri, A., Rula,",
        "Zablith, F., Antoniou, G., d'Aquin, M., Flouris, G., Kondylakis, H., Motta, E., Plexousakis, D., "
        "& Sabou, M. (2015). Ontology evolution: A process-centric survey. *The Knowledge Engineering "
        "Review, 30*(1), 45–75. https://doi.org/10.1017/S0269888913000349",
    ),
    # 공학 정보학 문헌 보강(2026-08-17) — 인접 최근 연구와의 포지셔닝(§2.2·§2.3·§2.4·§3).
    # 서지는 Crossref 등록 메타데이터 대조다(저자·권·논문번호·DOI).
    (
        "Kontokostas, D., Westphal, P.,",
        "Johansen, K. W., Schultz, C., & Teizer, J. (2025). Knowledge graph exploitation to enhance the "
        "usability of risk assessment in construction safety planning. *Advanced Engineering Informatics, "
        "65*, 103305. https://doi.org/10.1016/j.aei.2025.103305",
    ),
    (
        "Krestel, R., Chikkamath,",
        "Kosse, S., Hagedorn, P., & König, M. (2025). Semantic digital twins in construction: Developing a "
        "modular system reference architecture based on information containers. *Advanced Engineering "
        "Informatics, 67*, 103483. https://doi.org/10.1016/j.aei.2025.103483",
    ),
    (
        "Shalaby, W., & Zadrozny",
        "Schönfelder, P., & König, M. (2025). Ontology-based reasoning in automatic floor plan analysis. "
        "*Advanced Engineering Informatics, 68*, 103761. https://doi.org/10.1016/j.aei.2025.103761",
    ),
    (
        "Strathern, M. (1997).",
        "Speiser, K., Maciocci, G., Boukamp, F., & Teizer, J. (2026). Agentic system for construction "
        "safety risk assessments using large language models and knowledge graphs. *Advanced Engineering "
        "Informatics, 74*, 104681. https://doi.org/10.1016/j.aei.2026.104681",
    ),
    # 위 BIB_FIXES 에서 지운 Pauwels 를 알파벳 자리(Pan·Piroi 사이)에 다시 넣는다.
    (
        "Piroi, F., & Hanbury",
        "Pauwels, P., Van Den Bersselaar, E., & Verhelst, L. (2024). Validation of technical requirements "
        "for a BIM model using semantic web technologies. *Advanced Engineering Informatics, 60*, 102426. "
        "https://doi.org/10.1016/j.aei.2024.102426",
    ),
    # 신규성 경계 보강(2026-08-21 · PLAN-063 트랙 2) — 변경된 KG 자체의 품질 지표, CQ 의 자동
    # 시험화, 통합 파이프라인 벤치마크. 셋 다 §2.2 에서 본 연구와 대비된다. 서지는 Crossref ·
    # arXiv · CEUR 볼륨 페이지 대조다. 아래 셋은 앞의 Hevner·Noy 삽입 뒤에 와야 앵커가 산다.
    (
        "Bekamiri, H., Hain,",
        "Bakker, R. M., & de Boer, M. H. T. (2026). Dynamic knowledge graph evaluation: Semantic and "
        "syntactic metrics for evaluating changes. *Data & Knowledge Engineering, 164*, 102611. "
        "https://doi.org/10.1016/j.datak.2026.102611",
    ),
    (
        "Hogan, A., Blomqvist, E.,",
        "Hofer, M., & Rahm, E. (2026). Evaluation of pipelines for data integration into knowledge "
        "graphs. *arXiv*. https://doi.org/10.48550/arXiv.2605.22304",
    ),
    (
        "Noy, N. F., & Klein, M. (2004).",
        "Mynarz, J., Haniková, K., & Svátek, V. (2023). Test-driven knowledge graph construction. In "
        "*Proceedings of the 4th International Workshop on Knowledge Graph Construction (KGCW 2023) "
        "co-located with ESWC 2023* (CEUR Workshop Proceedings, Vol. 3471). "
        "https://ceur-ws.org/Vol-3471/paper4.pdf",
    ),
]


# ── 표 셀 치환 (2026-08-13) ─────────────────────────────────────────────────
# (앵커, 치환할 행 전체, 수치 변경 사유 · None 이면 수치 불변을 강제한다)
# 왜 필요한가 — 2단계에서 장 구성을 접으며 §4.8·§4.9·§4.9.1 이 §4.4·§4.5·§4.5.1 이 됐는데
# 표 안의 참조는 동결본을 그대로 복사하느라 옛 번호로 남았다(submission-check D9). 명칭
# 규칙(§0.8 SYSTEM_LABELS·SEAL)도 같은 이유로 표에만 남는다.
NUMERIC = re.compile(r"\d+(?:[.,]\d+)*")
SECTION_TOKEN = re.compile(r"§\s?\d+(?:\.\d+)*")


def measurements(text: str) -> list[str]:
    """수치 토큰 — 단, 절 번호는 뺀다(§4.9 → §4.5 는 재번호이지 수치 변경이 아니다)."""
    return NUMERIC.findall(SECTION_TOKEN.sub("§", text))

CELL_FIXES: list[tuple[str, str, str | None]] = [
    # **사문 16건을 뺐다 (2026-08-29 · 사용자 승인).** 뺀 것은 §1.4a 평가 점검 표 4행 ·
    # §4.9 승인식 표 5행 · §7.7·§7.8 설계원리 표 5행 · §4.1 세 태스크 뷰 1행 · §4.4 도달성 1행
    # 이다. **판정도 수치도 바뀌지 않는다** — 이 열여섯은 복사되지 않는 표를 고치고 있었으므로
    # 산출물에 한 글자도 내보낸 적이 없다(실측: 치환 결과 문자열이 파생본에 0건). 같은 규율은
    # 이제 원본 쪽에서 선다 — `make verdicts` 가 supplementary 까지 보기 때문이다.
    # 절제 표의 `p=0.000` — 0 이 아닌 값을 0 으로 적은 자리다. 부트스트랩 10,000 회의
    # 분해능은 0.0001 이므로 산출기가 낼 수 있는 가장 작은 값이 `0.000` 으로 반올림된 것이며,
    # **참값이 0 이라는 뜻이 아니다.** 통계 보고 관례대로 `p<.001` 로 적는다. 같은 표의 다른
    # p 값은 그대로 둔다 — 반올림으로 0 이 되지 않았기 때문이다.
    (
        "| **high lexical overlap** | 171 | 420 | 0.4685 | 0.5396 |",
        "| **high lexical overlap** | 171 | 420 | 0.4685 | 0.5396 | **+0.0711** | "
        "[+0.0330,+0.1104] (p<.001) |",
        "p=0.000 은 반올림 표기이고 참값은 0 이 아니다 — 통계 보고 관례에 따라 p<.001 로 적는다",
    ),
    # EP4 행 — "1회 개봉" 단정 대신 열람 원장을 밝힌다(§0.8 SEAL).
    (
        "| **EP4** | **검색 효용과 경계** |",
        "| **EP4** | **검색 이득의 범위와 경계** | 온톨로지 보강이 강한 텍스트 기준선을 "
        "**개선하는가, 어디까지인가** | 봉인 분할에 대한 사전등록된 확증 평가 — 모든 접근을 "
        "열람 원장에 기록 (비중복 확증 분할 둘) | 확증 + 탐색적 진단 | §6.4 |\n"
        # EP5 행 신설 (2026-08-22 · PLAN-064 A-5). 동결본은 에피소드 넷까지만 담고 있으므로
        # 다섯째 행은 여기서 붙인다 — 산문 소스에 표를 다시 타자하지 않기 위해서다.
        "| **EP5** | **이식 판정** | 형식 층과 교차 태스크 층이 **자원을 바꾸어도 동일하게 "
        "작동하는가** | 별도 사전등록 아래 홀드아웃 결함 21건과 실제 릴리스 계보 10판정 "
        "(승인식은 완성되지 않는다 · T1·T2 미이식) | 별도 사전등록 아래의 판정 | §6.5 |",
        "\"1회\" 를 뺀 자리에 회수 단정이 남지 않는다(§0.3 조건 ⑤). 그리고 EP5 행이 늘면서 "
        "그 행의 수치(21·10)가 새로 들어간다 — 출처는 SPEC-010 §8 판정 기록이다. 명칭은 "
        "\"효용\" 에서 \"이득의 범위\" 로 내린다(PLAN-081 §6-③) — 수치는 불변이다",
    ),
    # ── 문체 규격 v2 · T6 (2026-08-16) ────────────────────────────────────────
    # 규격 v1 은 산문만 검사했으므로 **표 셀의 구어·은유·축약형이 통째로 남아 있었다**.
    # v2 의 T6·T7 이 표 셀을 검사 대상에 넣었고, 그래서 여기서 고친다. 아래 치환은
    # **어체만** 바꾼다 — 판정·예측·수치는 한 글자도 움직이지 않는다.
    (
        "| **EP2** | **게이트 판별력** |",
        "| **EP2** | **게이트 판별력** | 의도적으로 주입한 결함을 게이트가 **검출하는가**, "
        "정상 변경을 **거부하지는 않는가** | 아직 판정한 적 없는 홀드아웃 결함 · 사전 지정한 "
        "세 조건 | 게이트 판별력에 대한 홀드아웃 산출물 평가 (확증 점검 목록에는 포함되지 않는다 · §5.7) | §6.2 |",
        None,
    ),
    (
        "| **EP3** | **통제된 자원 교체** |",
        "| **EP3** | **통제된 자원 교체** | 문서집합·설정을 고정하고 **자원만 교체하였을 때** "
        "게이트의 판정은 무엇인가 | 사전등록된 승인식(T1·T2·T3)의 적용 | 별도 사전등록 아래의 "
        "판정 | §6.3 |",
        None,
    ),
    ("| B0·B2·B3 텍스트 · B4 분류 |",
     "| B0·B2·B3 텍스트 · B4 분류 | 불변 | 불변 | 0 (텍스트를 변경하지 않았으므로) |", None),
]

# 2·4단계 재구성으로 바뀐 절 번호. 표 안의 참조에만 적용한다 — 산문은 사람이 소스에서 고친다.
SECTION_RENUMBER = [
    ("§4.9.1", "§4.5.1"),
    ("§4.8–4.9", "§4.4–4.5"),
    ("§4.9", "§4.5"),
    ("§4.8", "§4.4"),
    ("§5.12", "§5.6"),
]

# ── 집중도 재구성(PLAN-053)의 장 구성 재편: 8장 → 6장 ──────────────────────────
# 표 셀의 절 참조도 함께 움직여야 한다 — 그러지 않으면 D9(존재하지 않는 절 참조)로 죽은
# 링크가 된다. **표를 다시 타자하지 않기 위해** 셀 하나하나를 CELL_FIXES 로 적는 대신,
# 복사되는 표 행 전체에 이 사상을 한 번에 적용한다. 사상은 동시 치환이며(가장 긴 토큰부터
# 매칭) 연쇄 치환이 일어나지 않는다. 절 번호는 수치가 아니므로(measurements 가 § 토큰을
# 제거한다) 이 치환은 수치 불변 검사를 흔들지 않는다.
CHAPTER_REMAP: dict[str, str] = {
    # 3장(DSR) 흡수 · 4장 산출물 → 3장
    "§4.5.1": "§3.5.1", "§4.4–4.5": "§3.4–3.5",
    "§4.5": "§3.5", "§4.4": "§3.4", "§4.3": "§3.3", "§4.2": "§3.2", "§4.1": "§3.1",
    # 5장 평가 설계 → 4장 (7절 → 5절)
    "§5.7": "§4.5", "§5.6": "§4.4", "§5.5": "§4.5", "§5.4": "§4.4",
    "§5.3": "§4.3", "§5.2": "§4.2", "§5.1": "§4.1",
    # 6장 결과 → 5장 (3단 제목 6개 → 3개) — EP4 의 하위 절은 파생본 §5.3.x 다(아래 참조).
    "§6.4.1": "§5.3.1", "§6.4.2": "§5.3.1", "§6.4.3": "§5.3.2", "§6.4.4": "§5.3.3",
    "§6.4.5": "§5.3.3", "§6.4.6": "§5.3.1",
    # §6.5 는 동결본에 없던 토큰이다 — A-5 가 신설한 EP5 결과 절(파생본 §5.5)을 표 셀에서
    # 가리키기 위해 동결본 번호 체계의 다음 자리를 빌린다(2026-08-22 · PLAN-064 A-5).
    "§6.5": "§5.5",
    # 5장 절 순서 — **소스의 실제 제목 순서를 따른다**(2026-08-30 교정 · 아래 경위).
    # 동결본 번호(에피소드 순) → 파생본 번호(발견의 무게 순):
    #   §6.1 EP1 표현 감사 → §5.1 · §6.2 EP2 게이트 판별력 → §5.4
    #   §6.3 EP3 자원 교체 → §5.2 · §6.4 EP4 검색 이득 → §5.3 · §6.5 EP5 이식 → §5.5
    #
    # **왜 고치는가 — 이 사상은 두 세대 낡아 있었고 표 3 의 다섯 행 중 넷이 죽은 절을**
    # **가리켰다.** 구판 주석은 *"EP3 이 §5.1, EP1 이 §5.3"* 이라 적었고 그 값은
    # PLAN-081 재편 당시의 순서다. 그 뒤 산문 소스가 §5 를 다시 배열하여
    # `stage3_source.md`·`en_source.md` 모두 **§5.1 이 EP1** 이 되었으나(§5 서두의
    # *"§5.1 first confirms that the artifact does carry the three tasks"* 가 그 순서를
    # 명시한다) 이 사상표는 따라오지 않았다. §5 는 서사 순서와 절 번호를 **일부러**
    # 어긋나게 둔 장이므로 표 3 이 유일한 길잡이이고, 그것이 틀리면 독자는 다섯
    # 에피소드를 서로 다른 논문으로 읽는다. **판정·수치는 하나도 바뀌지 않는다** —
    # 바뀐 것은 각 에피소드의 결과가 실린 자리를 가리키는 포인터뿐이다.
    #
    # **재발 방지:** 산문 소스의 §5 절 순서를 바꾸면 이 표를 함께 고친다. 조립기의 수치
    # 불변 검사는 절 번호를 수치로 세지 않으므로 이 어긋남을 잡아 주지 않는다.
    "§6.4": "§5.3", "§6.3": "§5.2", "§6.2": "§5.4", "§6.1": "§5.1",
    # 7장 논의 + 8장 한계·결론 → 6장
    # 6장 재편 (2026-08-26 · PLAN-081 §2 이동 대장) — 설계원리 절이 교훈 절(§6.3)이 되고
    # 한계는 §6.4, 가용성은 §6.5, 결론은 독립 장 §7 이 되었다. 대응의 오른쪽만 옮겼다.
    "§7.10": "§6.4", "§7.1": "§6.1", "§7.2": "§6.2", "§7.3": "§6.3", "§7.4": "§3.6",
    "§7.5": "§6.1", "§7.6": "§6.4", "§7.7": "§6.3", "§7.8": "§6.3", "§7.9": "§6.4",
    "§8.1.1": "§6.4", "§8.1.2": "§6.4", "§8.1": "§6.4", "§8.2": "§6.4", "§8.3": "§6.4",
    "§8.4": "§6.4", "§8.5": "§6.4", "§8.6": "§6.5", "§8.7": "§6.4", "§8.8": "§7",
}
CHAPTER_TOKEN = re.compile(
    "|".join(re.escape(k) for k in sorted(CHAPTER_REMAP, key=len, reverse=True))
)


def remap_sections(text: str) -> str:
    return CHAPTER_TOKEN.sub(lambda m: CHAPTER_REMAP[m.group(0)], text)


def apply_cell_fixes(rows: list[str], used: dict[str, int]) -> list[str]:
    """**복사된 표 행**을 고친다. 앵커가 그 표 안에 두 번 있거나 수치가 바뀌면 실패한다.

    **범위를 표로 좁힌 이유 (2026-08-29 · 사용자 승인).** 구판은 동결본 **전체**에 치환을 걸고
    앵커마다 파일 안에서 정확히 1건을 요구했다. 그 결과 두 가지가 생겼다. ① 복사되지 않는 절의
    표까지 치환 대상이 되어, 고친 문장이 **어디에도 나가지 않은 채** 앵커 유지 의무만 남았다 —
    실측 21건 중 **16건이 그런 사문(死文)이었다.** ② 그 16건이 동결본의 절 일곱을 붙잡아 두어,
    보충자료를 정리하면 조립이 멈췄다. 치환은 **나가는 표에만** 걸어야 그 둘이 함께 사라진다.
    """
    out = list(rows)
    for probe, new, reason in CELL_FIXES:
        hits = [k for k, line in enumerate(out) if probe in line]
        if not hits:
            continue
        if len(hits) > 1:
            fail(f"셀 치환 앵커가 한 표 안에서 {len(hits)}건 — {probe!r}")
        k = hits[0]
        old = out[k]
        text = old if new is None else new
        for a, b in SECTION_RENUMBER:
            text = text.replace(a, b)
        if text == old:
            fail(f"셀 치환이 아무것도 바꾸지 않았다 — {probe!r} (규칙이 이미 반영됐으면 목록에서 뺀다)")
        if measurements(old) != measurements(text):
            if reason is None:
                fail(
                    f"셀 치환이 수치를 바꿨다 — {probe!r}\n"
                    f"  이전: {measurements(old)}\n  이후: {measurements(text)}"
                )
            print(f"셀 치환 · 수치 변경 허용 — {probe!r}: {reason}")
        out[k] = text
        used[probe] = used.get(probe, 0) + 1
    return out


def fail(msg: str) -> None:
    print(f"실패: {msg}", file=sys.stderr)
    raise SystemExit(2)


def select_rows(rows: list[str], keep: str, anchor: str) -> list[str]:
    """머리글 두 행 + `keep` 이 지목한 행만 남긴다 (원문 순서 유지)."""
    head, body = rows[:2], rows[2:]
    picked: list[int] = []
    for probe in [p.strip() for p in keep.split(";") if p.strip()]:
        hits = [i for i, row in enumerate(body) if probe in row]
        if len(hits) != 1:
            fail(f"행 선별 앵커가 {len(hits)}건 — {probe!r} (표: {anchor!r})")
        picked.append(hits[0])
    kept = [body[i] for i in sorted(set(picked))]
    if len(kept) != len(picked):
        fail(f"행 선별 앵커가 같은 행을 두 번 지목했다 — {anchor!r}")
    print(f"행 선별 · {anchor!r}: {len(body)}행 → {len(kept)}행 (나머지는 동결본에 잔류)")
    return head + kept


def read_generated(name: str) -> list[str]:
    """생성기 산출 표를 읽는다 — paper/tables/ 밖은 거부한다."""
    path = (GENERATED_DIR / name.strip()).resolve()
    if GENERATED_DIR.resolve() not in path.parents:
        fail(f"생성 표는 {GENERATED_DIR}/ 안에서만 읽는다 — {name!r}")
    if not path.exists():
        fail(f"생성 표 부재 — {path} (생성기를 먼저 돌린다)")
    return path.read_text(encoding="utf-8").split("\n")


def extract_table(
    lines: list[str],
    anchor: str,
    keep: str | None = None,
    remap: bool = True,
    fixes_used: dict[str, int] | None = None,
) -> str:
    hits = [i for i, line in enumerate(lines) if anchor in line]
    if not hits:
        fail(f"앵커 소실 — {anchor!r}")
    if len(hits) > 1:
        fail(f"앵커 중복 {len(hits)}건 — {anchor!r} (더 긴 앵커로 특정할 것)")
    i = hits[0]
    # 앵커 행 이후 첫 표 행까지 내려간 뒤, 표가 끝나는 곳까지 담는다.
    j = i
    while j < len(lines) and not lines[j].lstrip().startswith("|"):
        j += 1
        if j - i > 6:
            fail(f"앵커 뒤 6행 안에 표가 없다 — {anchor!r}")
    k = j
    while k < len(lines) and lines[k].lstrip().startswith("|"):
        k += 1
    if k - j < 3:
        fail(f"표가 너무 짧다({k - j}행) — {anchor!r}")
    rows = lines[j:k]
    if fixes_used is not None:
        rows = apply_cell_fixes(rows, fixes_used)
    if keep is not None:
        rows = select_rows(rows, keep, anchor)
    out = [remap_sections(row) for row in rows] if remap else list(rows)
    for before, after in zip(rows, out):
        if measurements(before) != measurements(after):
            fail(f"절 재번호가 수치를 바꿨다 — {anchor!r}\n  {before}\n  {after}")
    return "\n".join(out)


def extract_bib(lines: list[str]) -> str:
    starts = [i for i, line in enumerate(lines) if line.strip() == BIB_START]
    if len(starts) != 1:
        fail(f"참고문헌 표제가 {len(starts)}건 — 하나여야 한다")
    i = starts[0] + 1
    ends = [k for k in range(i, len(lines)) if BIB_END in lines[k]]
    if not ends:
        fail(f"참고문헌 종료 표지 소실 — {BIB_END!r}")
    body = lines[i:ends[0]]

    def apply(spec: list[tuple[str, str | None]], insert: bool) -> None:
        for probe, text in spec:
            hits = [k for k, line in enumerate(body) if probe in line]
            if len(hits) != 1:
                fail(f"서지 교체 앵커가 {len(hits)}건 — {probe!r}")
            k = hits[0]
            if text is None:
                del body[k]
                while k < len(body) and body[k].strip() == "":
                    del body[k]
                    break
            elif insert:
                body.insert(k, "")
                body.insert(k, text)
            else:
                body[k] = text

    apply(BIB_FIXES, insert=False)
    apply(BIB_INSERTS, insert=True)
    print(f"서지: 교체 {len(BIB_FIXES)}건 · 신규 {len(BIB_INSERTS)}건 · 플레이스홀더 목록 제외")
    return "\n".join(body).strip() + "\n"


def build() -> str:
    if not PROSE.exists():
        fail(f"산문 소스 부재 — {PROSE}")
    if not FROZEN.exists():
        fail(f"복사 원본 부재 — {FROZEN}")
    if not BIB_SRC.exists():
        fail(f"서지 원본 부재 — {BIB_SRC}")
    frozen = FROZEN.read_text(encoding="utf-8").split("\n")
    prose = PROSE.read_text(encoding="utf-8")

    used: list[str] = []
    fixes_used: dict[str, int] = {}   # 동결본은 디스크에서 불변 — 나가는 표만 고친다

    def sub(match: re.Match[str]) -> str:
        anchor = match.group("anchor").strip()
        used.append(anchor)
        src = match.group("src")
        if src is None:
            return extract_table(frozen, anchor, match.group("keep"), fixes_used=fixes_used)
        return extract_table(read_generated(src), anchor, match.group("keep"), remap=False)

    out = DIRECTIVE.sub(sub, prose)
    if "{{BIB}}" not in out:
        fail("{{BIB}} 지시자가 없다 — 참고문헌이 빠진 원고는 만들지 않는다")
    out = out.replace("{{BIB}}", extract_bib(BIB_SRC.read_text(encoding="utf-8").split("\n")))
    if "{{COPY" in out:
        fail("해석되지 않은 지시자가 남았다 — 문법은 {{COPY:앵커|table}} 이다")
    unused = [probe for probe, _new, _r in CELL_FIXES if probe not in fixes_used]
    if unused:
        fail(
            "복사되는 표 어디에도 걸리지 않은 셀 치환이 있다 — 사문이므로 목록에서 뺀다:\n  "
            + "\n  ".join(repr(p) for p in unused)
        )
    print(f"셀 치환 {len(CELL_FIXES)}건 · 복사한 표 {len(used)}개 · 원본 {FROZEN}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="다시 조립해 현재 파생본과 대조만 한다")
    args = ap.parse_args()

    built = build()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != built:
            print("불일치: 파생본이 산문 소스 + 동결 표와 다르다 (재생성 필요)", file=sys.stderr)
            return 1
        print("정합: 파생본 = 산문 소스 + 동결 표")
        return 0
    TARGET.write_text(built, encoding="utf-8")
    print(f"생성: {TARGET} ({len(built):,}자)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

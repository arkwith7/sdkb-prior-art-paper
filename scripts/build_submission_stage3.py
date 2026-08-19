#!/usr/bin/env python3
"""scripts/build_submission_stage3.py — 3단계(재조준·축약) 파생본을 **기계로** 조립한다.

용법:  python scripts/build_submission_stage3.py [--check]
종료:  0 = 성공(또는 --check 정합) · 1 = 불일치 · 2 = 앵커 소실·중복

왜 스크립트인가 (PLAN-048 3단계 · CLAUDE.md §1-1·§2.3)
- 3단계는 **문장을 새로 쓰는 단계**다. 그러나 **표의 수치는 새로 쓰는 대상이 아니다** —
  손으로 옮겨 적으면 오탈자가 곧 조작이 된다(§1-1 "수치는 실행된 코드의 출력"). 그래서
  산문은 사람이 쓰고(`paper/manuscript/stage3_source.md`), **표는 축약 전 전문에서 문자
  단위로 복사**한다. 이 파일이 그 경계를 강제한다.
- 복사 원본은 **축약 전 파생본 전문**(`paper/supplementary/S5-submission-full-v2.md`)이다.
  S5 는 2단계 산출물의 동결 사본이므로 3단계 편집이 원본을 움직이지 못한다.
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
FROZEN = Path("paper/supplementary/S5-submission-full-v2.md")
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
    # AEI 문헌 보강(2026-08-17) — 투고처에 게재된 최근 연구와의 포지셔닝(§2.2·§2.3·§2.4·§3).
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
    # EP4 행 — "1회 개봉" 단정 대신 열람 원장을 밝힌다(§0.8 SEAL).
    (
        "| **EP4** | **검색 효용과 경계** |",
        "| **EP4** | **검색 효용과 경계** | 온톨로지 보강이 강한 텍스트 기준선을 "
        "**개선하는가, 어디까지인가** | 봉인 분할에 대한 사전등록된 확증 평가 — 모든 접근을 "
        "열람 원장에 기록 (비중복 확증 분할 둘) | 확증 + 탐색적 진단 | §6.4 |",
        "\"1회\" 를 뺀 자리에 회수 단정이 남지 않는다 — 개봉 횟수는 원장이 말한다(§0.3 조건 ⑤)",
    ),
    # 자원 교체 표 — P1 은 사전 지정 주 구성이 아니라 **교체 대상 구성**이다(§0.8 SYSTEM_LABELS).
    (
        "| **P1 (주 시스템)** |",
        "| **P1 (교체 대상 구성)** | 0.4849 | 0.4556 | **−0.0293** · 95% CI [−0.0542, −0.0053] |",
        None,
    ),
    # 평가 점검 표 머리글 — 두 칸은 합성 판정이 아니라 **사전등록별 기록**임을 열 이름이 말하게
    # 한다. 그리고 §0.9 에 따라 첫 칸을 사전등록 라벨에서 **서술형 호칭**으로 바꾼다.
    (
        "| 연구질문 | 점검 (라벨) |",
        "| 평가 점검 | 지위 | 결과를 보기 전에 동결한 예측 | 사전등록별 판정 기록 · "
        "첫 확증 분할(A) | 사전등록별 판정 기록 · 두 번째 확증 분할(B) | 근거 |",
        None,
    ),
    # ── §0.9 라벨 정책: 파생본 본문에 사전등록 라벨을 쓰지 않는다 ──────────────────────
    # 세 행 모두 **판정·예측·수치는 원문 그대로**이고 바뀌는 것은 첫 두 칸의 호칭뿐이다.
    # 라벨의 숫자(RQ2·H3·RQ3·H5·RQ5·T4)가 빠지므로 수치 토큰 검사가 걸린다 — 사유를 적는다.
    # 대응표는 paper/supplementary/S6-preregistration-crosswalk.md.
    (
        "| **RQ2** 검색 유용성 |",
        "| **점검 1 · 검색 유용성** | 확증 | 온톨로지 보강 검색은 최강 텍스트 기준선보다 "
        "**Recall@100 과 nDCG@20 이 모두** 높고, 그 개선폭은 질의–정답의 어휘 중첩이 **낮은** "
        "집단에서 더 크다 | **부분 지지 — 주 지표에 한정** (R@100 은 P1 에서 유의 개선 · nDCG "
        "조항 미충족 · 사전 지정 주 구성 비유의 · 저중첩 조건 반증) | **미지지** (R@100 은 "
        "개선되나 nDCG 조항이 깨졌다 · 주 구성 비유의) | §6.4.1 (패널 A · B) |",
        "라벨 숫자 2·3(RQ2·H3)만 빠진다 — 예측·판정·측정값은 원문과 동일하다(§0.9 규칙 2)",
    ),
    (
        "| **RQ3** 계층 특이성 |",
        "| **점검 2 · 계층 특이성** | 확증 | 게이트 태스크와 무관한 전문가 매칭 전용 계층"
        "(`Skill`·`ExpertCase`·`Mitigation`)의 제거는 검색 성능을 **유의하게 바꾸지 않는다** | "
        "**기각 → 교차 태스크 의존성 관측** (제거가 검색을 유의하게 악화) | **재현되지 않음 — "
        "판정 불가** (같은 절제의 값이 0.0000 · \"영향 없음\"과 \"뺄 것이 없음\"을 가르지 "
        "못한다) | §6.4.3 · §6.4.6 · §7.3 |",
        "라벨 숫자 3·5(RQ3·H5)만 빠진다 — 예측·판정·측정값은 원문과 동일하다(§0.9 규칙 2)",
    ),
    (
        "| **RQ5** 전달 |",
        "| **점검 3 · 전달** | 확증 판독 (게이트 조건 T4) | 검색 구성만 교체하고 생성기를 고정하였을 때 "
        "**인용 정확도가 떨어지지 않고 환각률이 오르지 않는다**(마진 동결) | *(탐색적 판독 — "
        "계측기 동결이 목적 · 판정 없음)* | **판정 1회 = 실패 — 전달을 확증하지 못했다** "
        "(점추정은 제안 구성이 앞서나 신뢰구간 하한이 마진보다 낮았다 · 원인 미구분) | "
        "[S5](../supplementary/S5-submission-full-v2.md) 부록 A |",
        "라벨 숫자 5(RQ5)만 빠지고 T4 는 게이트 이름이라 남는다 — 판정·측정값은 원문과 동일하다",
    ),
    # DP4 근거 셀에 남은 마지막 사전등록 라벨 — §0.9 규칙 2.
    (
        "| **DP4** | **통제된 자원 교체**",
        "| **DP4** | **통제된 자원 교체** — 문서집합·모델·가중치를 고정하고 **자원 번들만 교체**해야 "
        "온톨로지 중심 자원 변경의 효과가 판별된다 | §6.5 — T-Box 가 한 번도 바뀌지 않아 승인 안전성을 "
        "**원리적으로 측정할 수 없었다** · 두 조건이 처음 성립한 뒤에야 판정이 나왔다 · "
        "**성립 사례는 1건** | 확인이 먼저 | 2026-08-01 | **경험적 지지** "
        "(확인 선행 · 방법론적 요구사항) |",
        "라벨 숫자 2(H2)가 빠지고 사례 수 1 이 늘어난다 — 근거와 시점은 원문과 동일하다"
        "(§0.9 규칙 2 · §0.6 3단계 등급)",
    ),
    # DP2·DP3 등급 — §0.6 이 3단계로 개정되며(2026-08-19 · PLAN-060) "확립" 이 갈렸다.
    # 설계 시점이 확인 시점보다 앞선 둘만 **사전 설계 · 실증 지지**다. 근거·시점·수치는 불변이고
    # 바뀌는 것은 등급의 이름뿐이다. §4.9 는 SECTION_RENUMBER 가 §4.5 로 옮긴다.
    (
        "| **DP2** |",
        "| **DP2** | **한 층 아래 승인** — 자원 변경은 자원 지표가 아니라 **다음 사용 층의 "
        "비회귀 결과**로 승인한다 | §6.3 — 형식 검증 L0–L3 를 **전부 통과한** 델타를 성능 조건 "
        "T1 이 거부(Accept = 0) | **§4.9 설계 시점** | 2026-08-01 | **사전 설계 · 실증 지지** |",
        None,
    ),
    (
        "| **DP3** |",
        "| **DP3** | **교차 태스크 감시** — 공유 T-Box 에서는 **주 태스크 성능만으로** 변경을 "
        "승인하지 않는다 | §6.2 — 교차 결함을 T3 만 단독 검출(12/45 · 단측 *p*=.0001) · "
        "§6.4.3 — 음성 대조군(A8) 제거가 검색 성능을 0.0316 저하시켰고(제거 손실 +0.0316), 다만 "
        "**§6.4.6 두 번째 분할에서는 0.0000 으로 갈렸다** | **§4.9 설계 시점**(T3) | 2026-07 | "
        "**사전 설계 · 실증 지지** — 근거는 결함주입 T3 단독 검출이 진다. A8 근거는 **두 표본에서 "
        "갈렸음을 그대로 적는다**(경쟁 설명 §7.9) |",
        "부호 표기 통일 — 같은 값을 표 9 캡션의 제거 손실 정의(full − ablated · 양수 = 계층 기여)와"
        " 같은 부호로 적는다. 측정값은 0.0316 그대로다(§1-1 · PLAN-062 F1)",
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
    ("| 항 | 말로 풀면 | 어긋나면 |", "| 항 | 조건의 내용 | 미충족 시의 처리 |", None),
    (
        "| L0–L3 | 최신인가 ·",
        "| L0–L3 | 최신 상태인가 · 구조 제약을 충족하는가 · 논리적 모순이 없는가 · 필수 "
        "역량질문에 응답하는가 | 즉시 거부 |",
        None,
    ),
    (
        "| **T1** | 바꾼 뒤에도",
        "| **T1** | 변경 이후에도 **검색 성능이 저하되지 않았는가** | 허용 폭 \\(\\epsilon\\) 을 "
        "초과하여 저하되면 거부 |",
        None,
    ),
    (
        "| **T2** | 전체 평균은 괜찮아도",
        "| **T2** | 전체 평균과 별개로 **특정 하위집단만 저하되지 않았는가** | 한 집단이라도 "
        "\\(\\delta\\) 이상 저하되면 거부 |",
        None,
    ),
    (
        "| **T3** | **다른 갈래**가",
        "| **T3** | **다른 태스크**가 응답하던 역량질문에 여전히 응답하는가 | 통과율이 하나라도 "
        "저하되면 거부 |",
        None,
    ),
    # DP1 근거 셀 — P1 을 "주 시스템"이라 부르는 것은 §0.8 SYSTEM_LABELS 위반이다.
    (
        "| **DP1** | **층별 검증**",
        "| **DP1** | **층별 검증** — 온톨로지 내부 품질과 하류 태스크 성능은 **별도 층에서** "
        "평가한다 | §6.3 — 문서당 개념 1.545 → 3.779(2.4배)인데 교체 대상 구성(P1)의 "
        "Recall@100 은 −0.0293 · **성립한 자원 델타는 1건** | 확인이 먼저 | 2026-08-01 | "
        "**경험적 지지** (확인 선행) |",
        "구성 명칭 P1 과 델타 건수 1 이 늘어난다 — 측정값은 원문과 동일하다"
        "(§0.8 SYSTEM_LABELS · §0.6 3단계 등급)",
    ),
    (
        "| **DP6** |",
        "| **DP6** | **전달 검증** — 검색 지표의 개선을 검토 효율이나 생성 답변 품질로 "
        "**자동 일반화하지 않는다** | §6.4.5 — Recall@100 이 +0.0534 인데 Candidate Reduction "
        "중앙값 **0.0 %** · 부록 A — 검색 층에서 유의하게 개선된 팔이 **생성 층 비열등 판정을 "
        "통과하지 못하였다**(T4 실패 · 하한 −0.0205 대 마진 −0.02) | §4.9.1(T4 설계) | "
        "2026-08-09 (확증 판정 1회) | **제안** |",
        None,
    ),
    # 5장 절 병합(14 → 7)에 따른 §5.12 → §5.6. 앵커는 이 행에서만 나오는 클래스 목록으로 잡는다.
    ("| 전문가 매칭 | `Problem`·`RootCause`", None, None),
    # ── 용어 교정 (2026-08-16) ────────────────────────────────────────────────
    # "해상도"는 이 원고에서 네 가지 뜻으로 쓰이던 은유였다(자원 계량 · 도달성의 관찰 수준 ·
    # 매칭 단위 · CQ 검사 세밀도). 뜻마다 다른 용어로 갈랐고, 이 표의 열 이름은 그중
    # **도달성의 관찰 수준**이다(§4.3 에서 정의한다).
    ("| 해상도 | 정의 | 도달성 |", "| 관찰 수준 | 정의 | 도달성 |", None),
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
    # 6장 결과 → 5장 (3단 제목 6개 → 3개)
    "§6.4.1": "§5.4.1", "§6.4.2": "§5.4.1", "§6.4.3": "§5.4.2", "§6.4.4": "§5.4.3",
    "§6.4.5": "§5.4.3", "§6.4.6": "§5.4.1",
    "§6.4": "§5.4", "§6.3": "§5.3", "§6.2": "§5.2", "§6.1": "§5.1",
    # 7장 논의 + 8장 한계·결론 → 6장
    "§7.10": "§6.5", "§7.1": "§6.1", "§7.2": "§6.2", "§7.3": "§6.3", "§7.4": "§6.4",
    "§7.5": "§6.1", "§7.6": "§6.5", "§7.7": "§6.4", "§7.8": "§6.4", "§7.9": "§6.5",
    "§8.1.1": "§6.5", "§8.1.2": "§6.5", "§8.1": "§6.5", "§8.2": "§6.5", "§8.3": "§6.5",
    "§8.4": "§6.5", "§8.5": "§6.5", "§8.6": "§6.6", "§8.7": "§6.5", "§8.8": "§6.7",
}
CHAPTER_TOKEN = re.compile(
    "|".join(re.escape(k) for k in sorted(CHAPTER_REMAP, key=len, reverse=True))
)


def remap_sections(text: str) -> str:
    return CHAPTER_TOKEN.sub(lambda m: CHAPTER_REMAP[m.group(0)], text)


def apply_cell_fixes(lines: list[str]) -> None:
    """동결본 행을 제자리에서 고친다. 앵커가 1건이 아니거나 수치가 바뀌면 실패한다."""
    for probe, new, reason in CELL_FIXES:
        hits = [k for k, line in enumerate(lines) if probe in line]
        if len(hits) != 1:
            fail(f"셀 치환 앵커가 {len(hits)}건 — {probe!r}")
        k = hits[0]
        old = lines[k]
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
        lines[k] = text
    print(f"셀 치환 {len(CELL_FIXES)}건 (수치 불변 검사 통과)")


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
    lines: list[str], anchor: str, keep: str | None = None, remap: bool = True
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
    frozen = FROZEN.read_text(encoding="utf-8").split("\n")
    apply_cell_fixes(frozen)         # 동결본은 디스크에서 불변 — 메모리 사본만 고친다
    prose = PROSE.read_text(encoding="utf-8")

    used: list[str] = []

    def sub(match: re.Match[str]) -> str:
        anchor = match.group("anchor").strip()
        used.append(anchor)
        src = match.group("src")
        if src is None:
            return extract_table(frozen, anchor, match.group("keep"))
        return extract_table(read_generated(src), anchor, match.group("keep"), remap=False)

    out = DIRECTIVE.sub(sub, prose)
    if "{{BIB}}" not in out:
        fail("{{BIB}} 지시자가 없다 — 참고문헌이 빠진 원고는 만들지 않는다")
    out = out.replace("{{BIB}}", extract_bib(frozen))
    if "{{COPY" in out:
        fail("해석되지 않은 지시자가 남았다 — 문법은 {{COPY:앵커|table}} 이다")
    print(f"복사한 표 {len(used)}개 · 원본 {FROZEN}")
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
